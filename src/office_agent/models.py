"""Model data rencana (plan) dan aksi. Semua aksi lewat model ini sebelum divalidasi."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    doc_id: str
    quote: str = Field(description="Kutipan persis dari dokumen sumber yang mendasari aksi ini")


class Action(BaseModel):
    id: str
    type: Literal["send_email", "create_event", "create_task"]
    # "document" = instruksi berasal dari isi dokumen/pesan (data), bukan dari pengguna. Selalu ditolak.
    origin: Literal["user_request", "document"] = "user_request"
    sources: list[SourceRef] = []

    # send_email
    to: list[str] = []
    subject: str = ""
    body: str = ""

    # create_event
    title: str = ""
    start: Optional[str] = None  # ISO lokal tanpa offset, mis. 2026-10-23T12:00
    tz: str = "WIB"
    duration_min: int = 60
    attendees: list[str] = []
    location: str = ""

    # create_task
    assignee: Optional[str] = None
    due: Optional[str] = None  # YYYY-MM-DD


class Issue(BaseModel):
    code: str
    severity: Literal["blocking", "warning", "high_impact"]
    action_id: Optional[str] = None
    message: str
    candidates: list[dict] = []
    suggestion: Optional[dict] = None
