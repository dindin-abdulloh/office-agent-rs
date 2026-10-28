"""Audit log append-only dengan rantai hash, supaya perubahan diam-diam terdeteksi."""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_lock = threading.Lock()


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "GENESIS"
        last = "GENESIS"
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = json.loads(line)["hash"]
        return last

    def log(self, event: str, actor: str, **detail) -> dict:
        with _lock:
            entry = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "event": event,
                "actor": actor,
                "detail": detail,
                "prev_hash": self._last_hash(),
            }
            entry["hash"] = _digest(entry)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return entry

    def read(self, plan_id: str | None = None) -> list[dict]:
        if not self.path.exists():
            return []
        rows = [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if plan_id:
            rows = [r for r in rows if r["detail"].get("plan_id") == plan_id]
        return rows

    def verify(self) -> tuple[bool, int]:
        """Return (utuh, jumlah_entri). False bila ada entri yang diubah atau dihapus."""
        prev = "GENESIS"
        rows = self.read()
        for r in rows:
            if r["prev_hash"] != prev or _digest(r) != r["hash"]:
                return False, len(rows)
            prev = r["hash"]
        return True, len(rows)


def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
