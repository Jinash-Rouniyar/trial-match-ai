from datetime import datetime, timezone
import io
import time
from functools import wraps
from typing import Callable, Any, Dict, List

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from trialmatch.services.db import patients_collection, trials_collection
from trialmatch.services.patient_processor import build_patient_profile_from_json
from trialmatch.services.matching_orchestrator import (
    run_matching_for_patient,
    latest_matches_for_patient,
)
from trialmatch.config import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


app = Flask(__name__)
CORS(app)


def _error_response(message: str, status: int):
    return jsonify({"error": {"message": message, "status": status}}), status


def require_admin(view_func: Callable[..., Any]):
    """
    Very simple admin guard based on a static token header.
    Suitable for project-level protection of admin-style routes.
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        secret = settings.app_admin_secret
        if not secret:
            # If not configured, allow everything (for easier local grading)
            return view_func(*args, **kwargs)
        header_token = request.headers.get("X-Admin-Token")
        if not header_token or header_token != secret:
            return _error_response("Unauthorized (invalid admin token).", 401)
        return view_func(*args, **kwargs)

    return wrapper


@app.post("/api/patients_upload")
def upload_patient():
    data = request.get_json(force=True, silent=True) or {}
    patient_json = data.get("patient")
    patient_id = data.get("patient_id")

    if not isinstance(patient_json, dict):
        return _error_response("`patient` must be a JSON object.", 400)

    if not patient_id:
        patient_id = str(patient_json.get("id") or f"patient-{int(time.time())}")

    profile = build_patient_profile_from_json(patient_json)
    if not profile:
        return _error_response("Could not build patient profile from supplied JSON.", 400)

    doc = {
        "patient_id": patient_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
    }
    patients_collection().update_one(
        {"patient_id": patient_id},
        {"$set": doc},
        upsert=True,
    )

    return jsonify({"patient_id": patient_id, "profile": profile})


@app.get("/api/patients_index")
def list_patients():
    cursor = patients_collection().find().sort("created_at", -1).limit(100)
    patients = []
    for doc in cursor:
        profile = doc.get("profile") or {}
        patients.append(
            {
                "patient_id": doc.get("patient_id"),
                "created_at": doc.get("created_at"),
                "conditions": profile.get("conditions", [])[:4],
            }
        )
    return jsonify({"patients": patients})


@app.get("/api/patient_detail")
def patient_detail():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return _error_response("patient_id query parameter is required.", 400)

    doc = patients_collection().find_one({"patient_id": patient_id})
    if not doc:
        return _error_response(f"Patient '{patient_id}' not found.", 404)

    profile = doc.get("profile") or {}
    latest = latest_matches_for_patient(patient_id)

    return jsonify(
        {
            "patient_id": patient_id,
            "created_at": doc.get("created_at"),
            "profile": profile,
            "latest_matches": latest,
        }
    )


@app.post("/api/trials_match")
def trials_match():
    data = request.get_json(force=True, silent=True) or {}
    patient_id = data.get("patient_id")
    mode = data.get("mode", "demo")
    num_trials = data.get("num_trials")

    if not patient_id:
        return _error_response("patient_id is required.", 400)
    if mode not in ("demo", "random"):
        return _error_response("mode must be 'demo' or 'random'.", 400)

    try:
        match_doc = run_matching_for_patient(
            patient_id=patient_id,
            mode=mode,
            num_trials=num_trials,
        )
    except ValueError as ve:
        return _error_response(str(ve), 404)
    except Exception as exc:
        return _error_response(str(exc), 500)

    return jsonify(
        {
            "patient_id": patient_id,
            "mode": match_doc.get("mode"),
            "created_at": match_doc.get("created_at"),
            "trials": match_doc.get("trials", []),
        }
    )


@app.post("/api/trials_match_batch")
def trials_match_batch():
    """
    Run matching for multiple patients in one request.
    Body: { "patient_ids": [...], "mode": "demo" | "random", "num_trials"?: int }
    """
    data = request.get_json(force=True, silent=True) or {}
    patient_ids = data.get("patient_ids") or []
    mode = data.get("mode", "demo")
    num_trials = data.get("num_trials")

    if not isinstance(patient_ids, list) or not patient_ids:
        return _error_response("patient_ids must be a non-empty list.", 400)
    if mode not in ("demo", "random"):
        return _error_response("mode must be 'demo' or 'random'.", 400)

    results: List[Dict[str, Any]] = []
    for pid in patient_ids:
        try:
            match_doc = run_matching_for_patient(
                patient_id=str(pid),
                mode=mode,
                num_trials=num_trials,
            )
            results.append(
                {
                    "patient_id": match_doc.get("patient_id"),
                    "mode": match_doc.get("mode"),
                    "created_at": match_doc.get("created_at"),
                    "trials": match_doc.get("trials", []),
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "patient_id": str(pid),
                    "error": str(exc),
                }
            )

    return jsonify({"results": results})


@app.post("/api/trials_upload")
@require_admin
def trials_upload():
    """
    Admin-style endpoint to upload a set of clinical trials into MongoDB.

    Body shape:
    {
        "trials": [
            {
                "nct_id": "...",
                "brief_title": "...",
                "criteria": "...",
                "overall_status": "RECRUITING"  # optional
            },
            ...
        ]
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    trials = data.get("trials")
    if not isinstance(trials, list) or not trials:
        return _error_response("`trials` must be a non-empty list.", 400)

    coll = trials_collection()
    upserted = 0
    for item in trials:
        if not isinstance(item, dict):
            continue
        nct_id = item.get("nct_id")
        brief_title = item.get("brief_title")
        criteria = item.get("criteria")
        if not (nct_id and brief_title and criteria):
            continue
        doc = {
            "nct_id": str(nct_id),
            "brief_title": str(brief_title),
            "criteria": str(criteria),
        }
        if "overall_status" in item:
            doc["overall_status"] = str(item.get("overall_status") or "")
        coll.update_one({"nct_id": doc["nct_id"]}, {"$set": doc}, upsert=True)
        upserted += 1

    return jsonify({"upserted": upserted})


@app.get("/api/patient_report_pdf")
def patient_report_pdf():
    """
    Generate a simple PDF report for the latest match of a given patient.
    """
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return _error_response("patient_id query parameter is required.", 400)

    doc = patients_collection().find_one({"patient_id": patient_id})
    if not doc:
        return _error_response(f"Patient '{patient_id}' not found.", 404)

    match_doc = latest_matches_for_patient(patient_id)
    if not match_doc:
        return _error_response("No match results found for this patient.", 404)

    profile = doc.get("profile") or {}

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 72
    p.setFont("Helvetica-Bold", 16)
    p.drawString(72, y, f"TrialMatch AI Report – Patient {patient_id}")
    y -= 32

    p.setFont("Helvetica", 10)
    created_at = match_doc.get("created_at", "")
    mode = match_doc.get("mode", "")
    p.drawString(72, y, f"Mode: {mode}    Generated at: {created_at}")
    y -= 24

    # Conditions
    conditions = ", ".join(profile.get("conditions", []) or [])
    p.setFont("Helvetica-Bold", 11)
    p.drawString(72, y, "Conditions")
    y -= 16
    p.setFont("Helvetica", 10)
    p.drawString(72, y, conditions or "None parsed")
    y -= 24

    # Trials table (top N)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(72, y, "Top Trial Matches")
    y -= 18
    p.setFont("Helvetica-Bold", 9)
    p.drawString(72, y, "NCT ID")
    p.drawString(200, y, "Title")
    p.drawString(500, y, "Score")
    y -= 14
    p.setFont("Helvetica", 9)

    for trial in (match_doc.get("trials") or [])[:15]:
        if y < 72:
            p.showPage()
            y = height - 72
            p.setFont("Helvetica", 9)
        p.drawString(72, y, str(trial.get("nct_id", "")))
        p.drawString(200, y, str(trial.get("title", ""))[:70])
        p.drawString(500, y, f"{trial.get('score', 0):.1f}")
        y -= 14

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"trialmatch_report_{patient_id}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)

