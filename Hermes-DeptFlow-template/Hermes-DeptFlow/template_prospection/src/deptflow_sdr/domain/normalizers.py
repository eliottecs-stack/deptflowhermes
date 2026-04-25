from __future__ import annotations

from typing import Any, Dict, Iterable, List

from deptflow_sdr.domain.models import Lead, Post


def _first(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def normalize_lead(item: Dict[str, Any], source: str = "bereach") -> Lead:
    full_name = _first(item.get("name"), item.get("fullName"), item.get("full_name"))
    first_name = _first(item.get("firstName"), item.get("first_name"))
    last_name = _first(item.get("lastName"), item.get("last_name"))

    if not full_name and (first_name or last_name):
        full_name = f"{first_name} {last_name}".strip()

    current_positions = item.get("currentPositions")
    company = _first(item.get("companyName"), item.get("company"), item.get("company_name"))
    if not company and isinstance(current_positions, list) and current_positions:
        first_pos = current_positions[0] if isinstance(current_positions[0], dict) else {}
        company = _first(first_pos.get("company"))

    return Lead(
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        linkedin_url=_first(item.get("profileUrl"), item.get("linkedinUrl"), item.get("url")),
        headline=_first(item.get("headline"), item.get("title")),
        company_name=company,
        location=_first(item.get("location")),
        public_identifier=_first(item.get("publicIdentifier"), item.get("public_identifier")),
        profile_urn=_first(item.get("profileUrn"), item.get("memberUrn"), item.get("profile_urn")),
        source=source,
        raw=item,
    )


def normalize_posts(response: Dict[str, Any]) -> List[Post]:
    raw_posts = response.get("posts") or response.get("items") or response.get("results") or []
    posts: List[Post] = []
    if not isinstance(raw_posts, list):
        return posts

    for item in raw_posts:
        if not isinstance(item, dict):
            continue
        posts.append(
            Post(
                post_url=_first(item.get("postUrl"), item.get("url")),
                text=_first(item.get("text"), item.get("content")),
                date=item.get("date"),
                likes_count=int(item.get("likesCount") or item.get("likes_count") or 0),
                comments_count=int(item.get("commentsCount") or item.get("comments_count") or 0),
                shares_count=int(item.get("sharesCount") or item.get("shares_count") or 0),
                raw=item,
            )
        )
    return posts
