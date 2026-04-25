from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from deptflow_sdr.config import Settings


@dataclass
class BeReachError(Exception):
    status_code: int
    code: str
    message: str
    retry_after: int = 0
    payload: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        wait = f" retry_after={self.retry_after}s" if self.retry_after else ""
        return f"BeReachError({self.status_code}, {self.code}): {self.message}{wait}"


class BeReachClient:
    """Small stdlib client for the BeReach endpoints used by DeptFlow.

    Default workflow intentionally excludes Sales Navigator endpoints.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.bereach_base_url

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "DeptFlow-SDR/0.1",
        }
        token = self.settings.bereach_api_key
        if token:
            if self.settings.bereach_auth_scheme:
                value = f"{self.settings.bereach_auth_scheme} {token}"
            else:
                value = token
            headers[self.settings.bereach_auth_header] = value
        return headers

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.settings.bereach_api_key:
            raise BeReachError(401, "missing_api_key", "BEREACH_API_KEY is empty")

        query = ""
        if params:
            clean = {k: v for k, v in params.items() if v is not None and v != ""}
            query = "?" + urllib.parse.urlencode(clean, doseq=True) if clean else ""

        url = f"{self.base_url}{path}{query}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        last_error: Optional[BeReachError] = None
        for attempt in range(self.settings.bereach_max_retries + 1):
            request = urllib.request.Request(
                url=url,
                data=body,
                method=method.upper(),
                headers=self._headers(),
            )
            try:
                with urllib.request.urlopen(request, timeout=self.settings.bereach_timeout_seconds) as response:
                    text = response.read().decode("utf-8")
                    data = json.loads(text) if text else {}
                    retry_after = int(data.get("retryAfter", 0) or 0)
                    if retry_after > 0:
                        time.sleep(min(retry_after, 10))
                    return data
            except urllib.error.HTTPError as exc:
                text = exc.read().decode("utf-8", errors="replace")
                try:
                    payload_data = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    payload_data = {"raw": text}
                error = payload_data.get("error", {}) if isinstance(payload_data, dict) else {}
                retry_after = int(error.get("retryAfter", 0) or payload_data.get("retryAfter", 0) or 0)
                last_error = BeReachError(
                    status_code=exc.code,
                    code=str(error.get("code", "http_error")),
                    message=str(error.get("message", exc.reason)),
                    retry_after=retry_after,
                    payload=payload_data if isinstance(payload_data, dict) else None,
                )
                if exc.code in {429, 500, 502, 503} and attempt < self.settings.bereach_max_retries:
                    time.sleep(min(retry_after or (attempt + 1) * 2, 30))
                    continue
                raise last_error
            except urllib.error.URLError as exc:
                last_error = BeReachError(0, "network_error", str(exc.reason))
                if attempt < self.settings.bereach_max_retries:
                    time.sleep((attempt + 1) * 2)
                    continue
                raise last_error

        if last_error:
            raise last_error
        raise BeReachError(0, "unknown_error", "Unknown BeReach request failure")

    def resolve_parameters(self, parameter_type: str, keywords: str, limit: int = 10) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/search/linkedin/parameters",
            params={"type": parameter_type, "keywords": keywords, "limit": limit},
        )

    def search_people(self, keywords: str, count: int = 10, start: int = 0, **filters: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "category": "people",
            "keywords": keywords,
            "count": max(1, min(int(count), 25)),
            "start": max(0, int(start)),
        }
        payload.update({k: v for k, v in filters.items() if v not in (None, "", [], {})})
        return self._request("POST", "/search/linkedin", payload=payload)

    def search_posts(self, keywords: str, count: int = 10, start: int = 0, **filters: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "category": "posts",
            "keywords": keywords,
            "count": max(1, min(int(count), 25)),
            "start": max(0, int(start)),
        }
        payload.update({k: v for k, v in filters.items() if v not in (None, "", [], {})})
        return self._request("POST", "/search/linkedin", payload=payload)

    def collect_posts(self, profile_url: str, count: int = 5, start: int = 0) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/collect/linkedin/posts",
            payload={"profileUrl": profile_url, "count": max(0, min(int(count), 100)), "start": max(0, int(start))},
        )

    def collect_comments(self, post_url: str, count: int = 100, start: int = 0) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/collect/linkedin/comments",
            payload={"postUrl": post_url, "count": max(0, min(int(count), 100)), "start": max(0, int(start))},
        )

    def collect_likes(self, post_url: str, count: int = 100, start: int = 0) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/collect/linkedin/likes",
            payload={"postUrl": post_url, "count": max(0, min(int(count), 100)), "start": max(0, int(start))},
        )

    def follow_profile(self, profile: str) -> Dict[str, Any]:
        return self._request("POST", "/follow/linkedin/profile", payload={"profile": profile})

    def unfollow_profile(self, profile: str) -> Dict[str, Any]:
        return self._request("POST", "/unfollow/linkedin/profile", payload={"profile": profile})

    def get_contact_by_url(self, linkedin_url: str) -> Dict[str, Any]:
        return self._request("GET", "/contacts/by-url", params={"linkedinUrl": linkedin_url})

    def bulk_update_contacts(self, contact_ids: List[str], update: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", "/contacts/bulk", payload={"contactIds": contact_ids, "update": update})


def extract_people(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle shape differences from BeReach search responses."""
    for key in ("items", "results", "profiles", "people"):
        value = response.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    data = response.get("data")
    if isinstance(data, dict):
        for key in ("items", "results", "profiles", "people"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []
