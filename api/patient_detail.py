from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse

from trialmatch.services.db import patients_collection
from trialmatch.services.matching_orchestrator import latest_matches_for_patient


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, body: dict):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        # Expect path like /api/patient_detail?patient_id=...
        query = urlparse(self.path).query
        params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
        patient_id = params.get("patient_id")

        if not patient_id:
            self._send_json(400, {"error": "patient_id query parameter is required"})
            return

        doc = patients_collection().find_one({"patient_id": patient_id})
        if not doc:
            self._send_json(404, {"error": f"Patient '{patient_id}' not found"})
            return

        profile = doc.get("profile") or {}
        latest_matches = latest_matches_for_patient(patient_id)

        self._send_json(
            200,
            {
                "patient_id": patient_id,
                "created_at": doc.get("created_at"),
                "profile": profile,
                "latest_matches": latest_matches,
            },
        )

