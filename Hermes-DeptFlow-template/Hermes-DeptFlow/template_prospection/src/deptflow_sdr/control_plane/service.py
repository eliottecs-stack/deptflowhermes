from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from deptflow_sdr.control_plane.gates import GoLiveGate
from deptflow_sdr.control_plane.registry import Registry
from deptflow_sdr.workflows.daily_prospecting import DailyProspectingWorkflow


@dataclass
class ConnectionOutcome:
    sent: int
    skipped: int
    errors: list[str] = field(default_factory=list)


class ControlPlaneService:
    """High-level use cases exposed by the dashboard."""

    def __init__(self, registry: Registry):
        self.registry = registry
        self.gate = GoLiveGate(registry)

    def send_connection_requests(self, profile_id: str, bereach_client: Any, max_count: int) -> ConnectionOutcome:
        gate = self.gate.evaluate(profile_id)
        if not gate.allowed:
            raise RuntimeError("Go-live bloqué: " + "; ".join(gate.reasons))

        profile = self.registry.get_profile(profile_id)
        leads = self.registry.list_leads(profile_id, status="connection_ready")
        local_limit = max(0, int(profile.get("daily_connection_limit", 0)))
        remote_limit = self._remaining_connections(bereach_client.get_limits())
        budget = min(max(0, int(max_count)), local_limit, remote_limit, len(leads))

        sent = 0
        errors: list[str] = []
        for lead in leads[:budget]:
            try:
                bereach_client.connect_profile(lead["linkedin_url"])
            except Exception as exc:
                errors.append(f"{lead['linkedin_url']}: {exc}")
                continue

            self.registry.upsert_lead(
                profile_id,
                lead_key=lead["lead_key"],
                full_name=lead["full_name"],
                linkedin_url=lead["linkedin_url"],
                score_total=lead["score_total"],
                tier=lead["tier"],
                status="connected",
                message_body=lead.get("message_body"),
            )
            sent += 1

        client_id = str(profile["client_id"])
        if sent:
            self.registry.record_quota_event(client_id, "linkedin_connection", used=sent, limit=local_limit)
        return ConnectionOutcome(sent=sent, skipped=max(0, len(leads) - sent), errors=errors)

    def run_dry_run(self, profile_id: str, profile_path: Path, limit: int = 5) -> dict[str, Any]:
        workflow = DailyProspectingWorkflow(profile_path, dry_run=True)
        result = workflow.run(limit=limit)
        self.registry.record_run(profile_id, dry_run=True, status="completed", summary=result)
        self._import_local_leads(profile_id, profile_path)
        return result

    def _remaining_connections(self, limits: dict[str, Any]) -> int:
        candidates = [
            limits.get("connectionRequests", {}),
            limits.get("connection_requests", {}),
            limits.get("connections", {}),
        ]
        for candidate in candidates:
            if isinstance(candidate, dict) and "remaining" in candidate:
                return max(0, int(candidate["remaining"]))
        if "remainingConnectionRequests" in limits:
            return max(0, int(limits["remainingConnectionRequests"]))
        return 0

    def _import_local_leads(self, profile_id: str, profile_path: Path) -> None:
        path = profile_path / "data" / "leads.jsonl"
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            lead = record.get("lead", {})
            score = record.get("score", {})
            message = record.get("message") or {}
            qualified = bool(score.get("qualified"))
            self.registry.upsert_lead(
                profile_id,
                lead_key=record.get("lead_key") or lead.get("linkedin_url") or lead.get("full_name", ""),
                full_name=lead.get("full_name", ""),
                linkedin_url=lead.get("linkedin_url", ""),
                score_total=int(score.get("total", 0)),
                tier=score.get("tier", ""),
                status="connection_ready" if qualified else "rejected",
                message_body=message.get("body"),
            )
