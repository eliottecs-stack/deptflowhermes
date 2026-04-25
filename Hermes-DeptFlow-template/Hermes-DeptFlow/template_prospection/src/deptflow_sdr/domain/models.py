from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Lead:
    full_name: str
    linkedin_url: str
    headline: str = ""
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""
    location: str = ""
    public_identifier: str = ""
    profile_urn: str = ""
    source: str = "bereach"
    raw: Dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        if self.linkedin_url:
            return self.linkedin_url.strip().lower().rstrip("/")
        if self.public_identifier:
            return self.public_identifier.strip().lower()
        if self.profile_urn:
            return self.profile_urn.strip().lower()
        return self.full_name.strip().lower()


@dataclass
class Post:
    post_url: str = ""
    text: str = ""
    date: Optional[int] = None
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreBreakdown:
    icp_fit: int = 0
    account_fit: int = 0
    buying_intent: int = 0
    activity: int = 0
    outreach_feasibility: int = 0
    data_confidence: int = 0
    risk_penalty: int = 0

    @property
    def total(self) -> int:
        value = (
            self.icp_fit
            + self.account_fit
            + self.buying_intent
            + self.activity
            + self.outreach_feasibility
            + self.data_confidence
            - self.risk_penalty
        )
        return max(0, min(100, value))


@dataclass
class LeadScore:
    lead_key: str
    total: int
    tier: str
    qualified: bool
    breakdown: ScoreBreakdown
    reasons: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["breakdown"] = asdict(self.breakdown)
        return data


@dataclass
class PreparedMessage:
    lead_key: str
    message_type: str
    body: str
    approved_by_qa: bool
    qa_notes: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class RunResult:
    started_at: str
    finished_at: str
    dry_run: bool
    discovered: int
    qualified: int
    rejected: int
    saved: int
    messages_prepared: int
    report_path: str
    errors: List[str] = field(default_factory=list)
