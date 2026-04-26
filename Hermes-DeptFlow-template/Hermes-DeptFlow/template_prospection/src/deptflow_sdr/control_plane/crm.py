from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from deptflow_sdr.control_plane.registry import Registry


CRM_HEADERS = ["Nom", "LinkedIn", "Score", "Tier", "Statut", "Message", "Prochaine action"]


class GoogleSheetsSync:
    """Build and optionally push CRM rows to Google Sheets."""

    def __init__(self, registry: Registry):
        self.registry = registry

    def build_rows(self, profile_id: str) -> list[list[Any]]:
        rows: list[list[Any]] = [CRM_HEADERS]
        for lead in self.registry.list_leads(profile_id):
            rows.append(
                [
                    lead["full_name"],
                    lead["linkedin_url"],
                    lead["score_total"],
                    lead["tier"],
                    lead["status"],
                    lead.get("message_body") or "",
                    self._next_action(lead["status"]),
                ]
            )
        return rows

    def sync_with_access_token(self, profile_id: str, spreadsheet_id: str, access_token: str, sheet_name: str) -> int:
        rows = self.build_rows(profile_id)
        url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
            f"{urllib.parse.quote(sheet_name)}!A1:append?valueInputOption=USER_ENTERED"
        )
        request = urllib.request.Request(
            url,
            data=json.dumps({"values": rows}).encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
        self.registry.record_crm_sync(profile_id, "google_sheets", "completed", max(0, len(rows) - 1))
        return max(0, len(rows) - 1)

    def sync_with_service_account_json(
        self,
        profile_id: str,
        spreadsheet_id: str,
        service_account_json: str,
        sheet_name: str = "Leads",
    ) -> int:
        try:
            from google.oauth2 import service_account  # type: ignore
            from google.auth.transport.requests import Request  # type: ignore
        except Exception as exc:
            raise RuntimeError("google-auth is required for Google Sheets service account sync") from exc

        info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        credentials.refresh(Request())
        return self.sync_with_access_token(profile_id, spreadsheet_id, credentials.token, sheet_name)

    def export_csv(self, profile_id: str, path: Path) -> Path:
        rows = self.build_rows(profile_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [",".join(self._csv_cell(cell) for cell in row) for row in rows]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.registry.record_crm_sync(profile_id, str(path), "completed", max(0, len(rows) - 1))
        return path

    def _next_action(self, status: str) -> str:
        if status == "connection_ready":
            return "Envoyer demande de connexion"
        if status == "approved":
            return "Prêt pour go-live"
        if status == "connected":
            return "Préparer relance DM"
        return "Revue humaine"

    def _csv_cell(self, value: Any) -> str:
        text = str(value).replace('"', '""')
        return f'"{text}"'
