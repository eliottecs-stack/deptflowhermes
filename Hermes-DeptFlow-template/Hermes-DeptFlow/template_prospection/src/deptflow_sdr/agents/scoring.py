from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from deptflow_sdr.domain.models import Lead, LeadScore, Post, ScoreBreakdown


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower()


def contains_any(text: str, terms: Iterable[str]) -> bool:
    haystack = normalize_text(text)
    return any(normalize_text(term) in haystack for term in terms if str(term).strip())


def count_signal_hits(text: str, terms: Iterable[str]) -> int:
    haystack = normalize_text(text)
    return sum(1 for term in terms if str(term).strip() and normalize_text(term) in haystack)


def post_is_recent(post: Post, days: int) -> bool:
    if not post.date:
        return False
    # BeReach uses millisecond timestamps in examples.
    timestamp = post.date / 1000 if post.date > 10_000_000_000 else post.date
    post_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    age_days = (datetime.now(timezone.utc) - post_dt).days
    return age_days <= days


class LeadScorer:
    def __init__(self, icp_config: Dict[str, Any], campaign_config: Dict[str, Any]):
        self.icp_config = icp_config
        self.campaign_config = campaign_config

    def score(self, lead: Lead, posts: List[Post]) -> LeadScore:
        icp = self.icp_config.get("icp", {})
        signals = self.icp_config.get("buying_signals", {})
        threshold = int(self.campaign_config.get("qualification", {}).get("threshold", 75))
        very_hot_threshold = int(self.campaign_config.get("qualification", {}).get("very_hot_threshold", 88))
        recent_days = int(self.campaign_config.get("enrichment", {}).get("recent_activity_days", 45))

        reasons: List[str] = []
        rejection_reasons: List[str] = []
        b = ScoreBreakdown()

        identity_text = " ".join([lead.full_name, lead.headline, lead.company_name, lead.location])
        posts_text = "\n".join(post.text for post in posts)

        excluded_terms = (
            icp.get("excluded_keywords", [])
            + icp.get("excluded_roles", [])
            + icp.get("competitors", [])
        )
        if contains_any(identity_text, excluded_terms):
            b.risk_penalty += 40
            rejection_reasons.append("Exclusion ICP détectée dans le profil")

        if contains_any(" ".join([lead.headline, lead.full_name]), icp.get("target_roles", [])):
            b.icp_fit += 14
            reasons.append("Titre/persona compatible avec l'ICP")
        elif contains_any(" ".join([lead.headline, lead.full_name]), icp.get("target_seniority", [])):
            b.icp_fit += 8
            reasons.append("Séniorité compatible avec l'ICP")
        else:
            rejection_reasons.append("Titre/persona non confirmé")

        if contains_any(lead.location, icp.get("target_locations", [])):
            b.icp_fit += 7
            reasons.append("Localisation compatible")
        elif not icp.get("target_locations"):
            b.icp_fit += 4

        if contains_any(" ".join([lead.headline, lead.company_name]), icp.get("target_industries", [])):
            b.icp_fit += 7
            b.account_fit += 8
            reasons.append("Industrie ou contexte entreprise compatible")

        if lead.company_name:
            b.account_fit += 6
            reasons.append("Entreprise identifiée")
        if lead.headline:
            b.icp_fit += 4
            b.data_confidence += 1
        if lead.linkedin_url:
            b.outreach_feasibility += 4
            b.data_confidence += 1
        if lead.full_name:
            b.outreach_feasibility += 2
            b.data_confidence += 1

        recent_posts = [post for post in posts if post_is_recent(post, recent_days)]
        if recent_posts:
            b.activity += 8
            b.data_confidence += 1
            reasons.append(f"Activité LinkedIn récente détectée ({len(recent_posts)} post(s))")
        elif posts:
            b.activity += 3
            reasons.append("Posts disponibles mais pas récents")

        strong_hits = count_signal_hits(posts_text, signals.get("strong", []))
        medium_hits = count_signal_hits(posts_text, signals.get("medium", []))
        weak_hits = count_signal_hits(posts_text, signals.get("weak", []))

        if strong_hits:
            b.buying_intent += min(14, 7 * strong_hits)
            reasons.append("Signal d'intention fort détecté dans les posts")
        if medium_hits:
            b.buying_intent += min(5, 3 * medium_hits)
            reasons.append("Signal d'intention moyen détecté")
        if weak_hits:
            b.buying_intent += min(2, weak_hits)
            reasons.append("Signal faible détecté")

        if b.buying_intent > 0 and b.activity > 0:
            b.outreach_feasibility += 4

        if not lead.linkedin_url:
            b.risk_penalty += 25
            rejection_reasons.append("URL LinkedIn manquante")
        if not lead.full_name:
            b.risk_penalty += 20
            rejection_reasons.append("Nom manquant")
        if not lead.headline:
            b.risk_penalty += 8
            rejection_reasons.append("Headline manquante")

        total = b.total
        qualified = total >= threshold and not any("Exclusion ICP" in r for r in rejection_reasons)

        if total >= very_hot_threshold and b.buying_intent >= 10:
            tier = "VERY_HOT"
        elif qualified and (b.buying_intent > 0 or b.activity >= 8):
            tier = "HOT"
        elif qualified:
            tier = "WARM"
        else:
            tier = "REJECTED"

        if not qualified and not rejection_reasons:
            rejection_reasons.append(f"Score inférieur au seuil ({total} < {threshold})")

        return LeadScore(
            lead_key=lead.key(),
            total=total,
            tier=tier,
            qualified=qualified,
            breakdown=b,
            reasons=reasons,
            rejection_reasons=rejection_reasons,
        )
