from __future__ import annotations

from dataclasses import dataclass

from deptflow_sdr.control_plane.registry import Registry


@dataclass
class GateResult:
    allowed: bool
    reasons: list[str]


class GoLiveGate:
    """Blocks real outreach until the profile has enough reviewed evidence."""

    def __init__(self, registry: Registry):
        self.registry = registry

    def evaluate(self, profile_id: str) -> GateResult:
        reasons: list[str] = []
        profile = self.registry.get_profile(profile_id)

        if not self.registry.latest_successful_dry_run(profile_id):
            reasons.append("Un dry-run validé est requis avant le mode réel.")

        approved_count = self.registry.approved_lead_count(profile_id)
        if approved_count < 10:
            reasons.append("Au moins 10 leads/messages doivent être approuvés.")

        if int(profile.get("daily_connection_limit", 0)) <= 0:
            reasons.append("Un quota quotidien de connexions doit être configuré.")

        return GateResult(allowed=not reasons, reasons=reasons)
