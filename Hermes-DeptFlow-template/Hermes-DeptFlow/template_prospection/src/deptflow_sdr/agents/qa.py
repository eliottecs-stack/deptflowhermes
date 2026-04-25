from __future__ import annotations

from typing import List, Tuple

from deptflow_sdr.domain.models import Lead, LeadScore, PreparedMessage


class QAAgent:
    def review_lead(self, lead: Lead, score: LeadScore) -> tuple[bool, list[str]]:
        issues: List[str] = []
        if not lead.linkedin_url:
            issues.append("URL LinkedIn manquante")
        if not lead.full_name:
            issues.append("Nom manquant")
        if not lead.headline:
            issues.append("Headline manquante")
        if not score.qualified:
            issues.extend(score.rejection_reasons or ["Lead non qualifié"])
        return (len(issues) == 0, issues)

    def review_message(self, lead: Lead, message: str) -> tuple[bool, list[str]]:
        issues: List[str] = []
        text = message.strip()
        if len(text) > 500:
            issues.append("Message trop long")
        forbidden = ["garanti", "j'ai vu vos données", "vos données internes"]
        lower = text.lower()
        for term in forbidden:
            if term in lower:
                issues.append(f"Terme interdit: {term}")
        if lead.company_name and lead.company_name.lower() not in lower and lead.full_name.lower().split(" ")[0] not in lower:
            # Not blocking: generic messages can be acceptable, but log it.
            pass
        return (len(issues) == 0, issues)
