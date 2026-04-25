from __future__ import annotations

from typing import Dict, Any


def can_follow_profiles(campaign_config: Dict[str, Any], dry_run: bool) -> bool:
    if dry_run:
        return False
    outreach = campaign_config.get("outreach", {})
    limit = campaign_config.get("limits", {}).get("daily_follow_profiles", 0)
    return bool(outreach.get("allow_follow_profiles", False)) and int(limit or 0) > 0


def can_send_messages(campaign_config: Dict[str, Any], dry_run: bool) -> bool:
    if dry_run:
        return False
    outreach = campaign_config.get("outreach", {})
    return bool(outreach.get("send_messages_automatically", False))
