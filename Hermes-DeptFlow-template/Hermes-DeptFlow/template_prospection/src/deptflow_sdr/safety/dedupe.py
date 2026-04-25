from __future__ import annotations

from typing import Iterable, Set

from deptflow_sdr.domain.models import Lead


class DedupeIndex:
    def __init__(self, existing_keys: Iterable[str] = ()):
        self.keys: Set[str] = {key.strip().lower().rstrip("/") for key in existing_keys if key}

    def seen(self, lead: Lead) -> bool:
        key = lead.key()
        if key in self.keys:
            return True
        self.keys.add(key)
        return False
