from datetime import datetime, timezone
import io
import time
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pymongo.errors import PyMongoError
from reportlab.pdfbase.pdfmetrics import stringWidth

from trialmatch.services.db import patients_collection, trials_collection
from trialmatch.services.clinicaltrials_gov_import import (
    extract_trial_input_list,
    normalize_trial_record,
)
from trialmatch.services.patient_processor import build_patient_profile_from_json
from trialmatch.services.matching_orchestrator import (
    run_matching_for_patient,
    latest_matches_for_patient,
)
from trialmatch.services.auth import require_auth
from trialmatch.config import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


app = Flask(__name__)
CORS(app)


def _error_response(message: str, status: int):
    return jsonify({"error": {"message": message, "status": status}}), status


@app.errorhandler(PyMongoError)
def handle_mongo_error(exc: PyMongoError):
    """Return a clean JSON 500 instead of a raw Python traceback for DB errors."""
    return _error_response(f"Database error: {exc}", 500)


@app.post("/api/patients_upload")
@require_auth(require_admin=False)
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
@require_auth(require_admin=False)
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
@require_auth(require_admin=False)
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
@require_auth(require_admin=False)
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
@require_auth(require_admin=True)
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
@require_auth(require_admin=True)
def trials_upload():
    """
    Upload clinical trials into MongoDB.

    Accepts a JSON array of studies, or ``{ "trials": [...] }`` / ``{ "studies": [...] }``.

    Each item may be ClinicalTrials.gov v2 (``protocolSection``) or a legacy flat row
    (``nct_id``, ``brief_title``, ``criteria``, optional ``overall_status``).
    """
    payload = request.get_json(force=True, silent=True)
    trial_items = extract_trial_input_list(payload)
    if not trial_items:
        return _error_response(
            "Expected a non-empty JSON array of studies, or an object with a non-empty "
            "`trials` or `studies` list.",
            400,
        )

    coll = trials_collection()
    upserted = 0
    skipped = 0
    for item in trial_items:
        doc = normalize_trial_record(item)
        if not doc:
            skipped += 1
            continue
        coll.update_one({"nct_id": doc["nct_id"]}, {"$set": doc}, upsert=True)
        upserted += 1

    if upserted == 0:
        return _error_response(
            "No valid trials could be imported. For ClinicalTrials.gov JSON, each study needs "
            "protocolSection.identificationModule.nctId and protocolSection.eligibilityModule."
            "eligibilityCriteria. Legacy rows need nct_id, brief_title, and criteria.",
            400,
        )

    return jsonify({"upserted": upserted, "skipped": skipped})


@app.get("/api/patient_report_pdf")
@require_auth(require_admin=False)
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

    def wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> List[str]:
        """
        Word-wrap text for ReportLab canvas drawString.
        """
        raw = (text or "").strip()
        if not raw:
            return [""]

        lines: List[str] = []
        for paragraph in raw.splitlines() or [""]:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if stringWidth(candidate, font_name, font_size) <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def unique_items(items: Any) -> List[str]:
        out: List[str] = []
        seen = set()
        for raw in items or []:
            value = str(raw or "").strip()
            if not value:
                continue
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(value)
        return out

    def draw_wrapped_line(text: str, font_name: str, font_size: int, x: float, max_width: float):
        nonlocal y
        p.setFont(font_name, font_size)
        for line in wrap_text(text, font_name, font_size, max_width):
            if y < 72:
                p.showPage()
                y = height - 72
                p.setFont(font_name, font_size)
            p.drawString(x, y, line)
            y -= 12

    def draw_bulleted_section(title: str, items: List[str], preview_limit: int):
        nonlocal y
        p.setFont("Helvetica-Bold", 11)
        p.drawString(72, y, f"{title} ({len(items)})")
        y -= 16
        if not items:
            draw_wrapped_line("None parsed", "Helvetica", 10, 72, width - 144)
            y -= 8
            return

        shown = items[:preview_limit]
        p.setFont("Helvetica", 10)
        for item in shown:
            draw_wrapped_line(f"- {item}", "Helvetica", 10, 72, width - 144)
            y -= 1
        if len(items) > preview_limit:
            draw_wrapped_line(
                f"(+{len(items) - preview_limit} more in source profile)",
                "Helvetica-Oblique",
                9,
                72,
                width - 144,
            )
        y -= 10

    p.setFont("Helvetica", 10)
    created_at = match_doc.get("created_at", "")
    mode = match_doc.get("mode", "")
    p.drawString(72, y, f"Mode: {mode}    Generated at: {created_at}")
    y -= 24

    conditions = unique_items(profile.get("conditions"))
    medications = unique_items(profile.get("medications"))
    draw_bulleted_section("Conditions", conditions, preview_limit=12)
    draw_bulleted_section("Medications", medications, preview_limit=10)

    p.setFont("Helvetica-Bold", 11)
    p.drawString(72, y, "Summary narrative")
    y -= 16
    raw_summary = str(profile.get("text_summary") or "").strip()
    if raw_summary:
        sentences = [s.strip() for s in raw_summary.split(". ") if s.strip()]
        summary_preview = ". ".join(sentences[:6]).strip()
        if summary_preview and not summary_preview.endswith("."):
            summary_preview += "."
        if len(sentences) > 6:
            summary_preview += f" (+{len(sentences) - 6} more sentences)"
        draw_wrapped_line(summary_preview, "Helvetica", 10, 72, width - 144)
    else:
        draw_wrapped_line("No summary available.", "Helvetica", 10, 72, width - 144)
    y -= 12

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
        title_lines = wrap_text(str(trial.get("title", "")), "Helvetica", 9, 290)
        required_height = max(14, len(title_lines) * 11) + 2
        if y - required_height < 72:
            p.showPage()
            y = height - 72
            p.setFont("Helvetica-Bold", 9)
            p.drawString(72, y, "NCT ID")
            p.drawString(200, y, "Title")
            p.drawString(500, y, "Score")
            y -= 14
            p.setFont("Helvetica", 9)

        nct_id = str(trial.get("nct_id", ""))
        score = f"{trial.get('score', 0):.1f}"

        p.drawString(72, y, nct_id)
        p.drawString(500, y, score)
        for i, line in enumerate(title_lines):
            p.drawString(200, y - (i * 11), line)
        y -= max(14, len(title_lines) * 11) + 2

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

