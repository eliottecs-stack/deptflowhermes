from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from deptflow_sdr.config import Settings
from deptflow_sdr.domain.models import Lead, LeadScore, PreparedMessage


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class LocalStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.data_dir = settings.data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def existing_lead_keys(self) -> list[str]:
        path = self.data_dir / "leads.jsonl"
        if not path.exists():
            return []
        keys: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get("lead", {}).get("linkedin_url") or record.get("lead_key")
            if key:
                keys.append(str(key).strip().lower().rstrip("/"))
        return keys

    def save_lead(self, lead: Lead, score: LeadScore, message: Optional[PreparedMessage] = None) -> None:
        _append_jsonl(
            self.data_dir / "leads.jsonl",
            {
                "lead_key": lead.key(),
                "lead": asdict(lead),
                "score": score.to_dict(),
                "message": asdict(message) if message else None,
            },
        )

    def save_run(self, run: Dict[str, Any]) -> None:
        _append_jsonl(self.data_dir / "daily_runs.jsonl", run)


class SupabaseStore:
    """Minimal Supabase REST writer.

    If Supabase is unavailable, the workflow should use LocalStore instead.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = settings.supabase_url.rstrip("/")
        self.key = settings.supabase_service_key

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }

    def _post(self, table: str, rows: list[dict[str, Any]]) -> None:
        url = f"{self.base}/rest/v1/{table}?on_conflict=lead_key"
        request = urllib.request.Request(
            url=url,
            data=json.dumps(rows).encode("utf-8"),
            method="POST",
            headers=self._headers(),
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()

    def existing_lead_keys(self) -> list[str]:
        # Keep it simple and avoid pulling the entire table in MVP.
        return []

    def save_lead(self, lead: Lead, score: LeadScore, message: Optional[PreparedMessage] = None) -> None:
        self._post(
            "deptflow_leads",
            [{
                "lead_key": lead.key(),
                "linkedin_url": lead.linkedin_url,
                "full_name": lead.full_name,
                "headline": lead.headline,
                "company_name": lead.company_name,
                "location": lead.location,
                "score_total": score.total,
                "tier": score.tier,
                "qualified": score.qualified,
                "score_json": score.to_dict(),
                "message_body": message.body if message else None,
                "raw_json": lead.raw,
            }],
        )

    def save_run(self, run: Dict[str, Any]) -> None:
        url = f"{self.base}/rest/v1/deptflow_runs"
        request = urllib.request.Request(
            url=url,
            data=json.dumps([run]).encode("utf-8"),
            method="POST",
            headers=self._headers(),
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()


def make_store(settings: Settings):
    if settings.has_supabase:
        return SupabaseStore(settings)
    return LocalStore(settings)
