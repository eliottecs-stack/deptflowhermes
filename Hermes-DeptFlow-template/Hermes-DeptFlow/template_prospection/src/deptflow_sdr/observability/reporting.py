from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from deptflow_sdr.config import Settings
from deptflow_sdr.domain.models import Lead, LeadScore, PreparedMessage


class ReportWriter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.reports_dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        discovered: int,
        accepted: list[tuple[Lead, LeadScore, PreparedMessage | None]],
        rejected: list[tuple[Lead, LeadScore]],
        errors: list[str],
        dry_run: bool,
    ) -> Path:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.settings.reports_dir / f"daily_report_{now}.md"

        lines: list[str] = []
        lines.append("# Rapport quotidien DeptFlow SDR")
        lines.append("")
        lines.append(f"- Mode: {'DRY_RUN' if dry_run else 'REAL'}")
        lines.append(f"- Leads découverts: {discovered}")
        lines.append(f"- Leads qualifiés: {len(accepted)}")
        lines.append(f"- Leads rejetés: {len(rejected)}")
        lines.append(f"- Erreurs: {len(errors)}")
        lines.append("")

        lines.append("## Leads qualifiés")
        if not accepted:
            lines.append("Aucun lead qualifié sur ce run.")
        for lead, score, message in accepted[:20]:
            lines.append("")
            lines.append(f"### {lead.full_name or lead.linkedin_url}")
            lines.append(f"- Score: {score.total}/100")
            lines.append(f"- Tier: {score.tier}")
            lines.append(f"- Profil: {lead.linkedin_url}")
            lines.append(f"- Headline: {lead.headline}")
            lines.append(f"- Raisons: {'; '.join(score.reasons) if score.reasons else 'n/a'}")
            if message:
                lines.append(f"- Message préparé: {message.body}")

        lines.append("")
        lines.append("## Rejets principaux")
        for lead, score in rejected[:20]:
            lines.append(f"- {lead.full_name or lead.linkedin_url}: {score.total}/100 — {'; '.join(score.rejection_reasons)}")

        if errors:
            lines.append("")
            lines.append("## Erreurs")
            for error in errors:
                lines.append(f"- {error}")

        lines.append("")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
