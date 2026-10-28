"""Pencarian kontak. Nama ambigu (dua Budi) tidak pernah ditebak diam-diam."""
from __future__ import annotations

import json
import re
from pathlib import Path

_HONORIFICS = re.compile(r"^(pak|bu|ibu|bapak|mas|mbak|dr\.?|drg\.?|ns\.?|prof\.?)\s+", re.IGNORECASE)


class ContactBook:
    def __init__(self, path: Path):
        self.contacts: list[dict] = json.loads(Path(path).read_text(encoding="utf-8"))
        self.by_id = {c["id"]: c for c in self.contacts}

    def search(self, query: str) -> list[dict]:
        q = query.strip()
        if q in self.by_id:
            return [self.by_id[q]]
        by_mail = [c for c in self.contacts if c["email"].lower() == q.lower()]
        if by_mail:
            return by_mail
        while True:
            stripped = _HONORIFICS.sub("", q)
            if stripped == q:
                break
            q = stripped
        low = q.lower()
        if not low:
            return []
        return [c for c in self.contacts if low in c["name"].lower().split() or low in c["name"].lower()]

    @staticmethod
    def public(c: dict) -> dict:
        return {k: c[k] for k in ("id", "name", "title", "email", "tz")}
