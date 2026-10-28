"""Deteksi instruksi tertanam di dokumen/pesan. Teks dokumen adalah DATA, bukan perintah."""
from __future__ import annotations

import re

REDACTED = "[INSTRUKSI TERTANAM DIABAIKAN]"

_ADDRESSED_TO_AI = re.compile(
    r"^\s*[\[<(]?\s*(ai|a\.i\.|assistant|asisten|agent|agen|claude|workbuddy|system|sistem)\s*[\]>)]?\s*[:\-–,]",
    re.IGNORECASE,
)
_PHRASES = [
    r"ignore (all |any )?(the )?(previous|prior|above) (instructions|rules)",
    r"disregard (all |any )?(the )?(previous|prior|above)",
    r"abaikan (semua |seluruh )?(instruksi|aturan|perintah)",
    r"forward (this|the) (file|document|email|minutes)",
    r"teruskan (file|dokumen|email|notulen) ini",
    r"you are now\b",
    r"kamu sekarang (adalah|menjadi)",
    r"do not (tell|inform|notify) the user",
    r"jangan (beritahu|katakan|laporkan) (ke )?(pengguna|user)",
]
_PHRASE_RE = re.compile("|".join(_PHRASES), re.IGNORECASE)
_HIDDEN_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def scan(text: str) -> tuple[str, list[dict]]:
    """Return (teks_tersanitasi, temuan). Baris yang berisi instruksi diganti penanda."""
    findings: list[dict] = []
    out_lines: list[str] = []
    for no, line in enumerate(text.splitlines(), start=1):
        if _ADDRESSED_TO_AI.search(line) or _PHRASE_RE.search(line) or _HIDDEN_COMMENT.search(line):
            findings.append({"line": no, "text": line.strip()})
            out_lines.append(REDACTED)
        else:
            out_lines.append(line)
    return "\n".join(out_lines), findings
