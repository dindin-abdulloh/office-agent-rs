"""Aturan budaya & operasional: zona WIB/WITA/WIT, jam kerja, sholat Jumat, libur nasional."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


@dataclass
class Rules:
    offsets: dict[str, int]
    office_start: time
    office_end: time
    prayer_start: time
    prayer_end: time
    holidays: dict[str, str]

    @classmethod
    def from_dict(cls, d: dict) -> "Rules":
        t = time.fromisoformat
        return cls(
            offsets=d["timezones"],
            office_start=t(d["office_hours"]["start"]),
            office_end=t(d["office_hours"]["end"]),
            prayer_start=t(d["friday_prayer"]["start"]),
            prayer_end=t(d["friday_prayer"]["end"]),
            holidays=d.get("holidays", {}),
        )

    def tz(self, name: str) -> timezone:
        if name not in self.offsets:
            raise ValueError(f"Zona waktu tidak dikenal: {name} (pakai WIB, WITA, atau WIT)")
        return timezone(timedelta(hours=self.offsets[name]))

    def parse_start(self, start_iso: str, tz_name: str) -> datetime:
        dt = datetime.fromisoformat(start_iso)
        return dt.replace(tzinfo=self.tz(tz_name)) if dt.tzinfo is None else dt

    def violations(self, start: datetime, duration_min: int, attendee_tz: dict[str, str]) -> list[dict]:
        """Cek slot untuk setiap peserta pada zona lokalnya. attendee_tz: nama -> kode zona."""
        out: list[dict] = []
        end = start + timedelta(minutes=duration_min)
        for who, zone in attendee_tz.items():
            ls, le = start.astimezone(self.tz(zone)), end.astimezone(self.tz(zone))
            label = f"{who} ({zone}, {ls:%H:%M}-{le:%H:%M})"
            if ls.weekday() >= 5:
                out.append({"rule": "weekend", "who": who, "detail": f"{label} jatuh di hari {DAYS_ID[ls.weekday()]}"})
            if ls.date().isoformat() in self.holidays:
                out.append({"rule": "holiday", "who": who, "detail": f"{label} libur: {self.holidays[ls.date().isoformat()]}"})
            if ls.time() < self.office_start or le.time() > self.office_end or le.date() != ls.date():
                out.append({"rule": "office_hours", "who": who, "detail": f"{label} di luar jam kerja {self.office_start:%H:%M}-{self.office_end:%H:%M}"})
            if ls.weekday() == 4 and ls.time() < self.prayer_end and le.time() > self.prayer_start:
                out.append({"rule": "friday_prayer", "who": who, "detail": f"{label} bentrok waktu sholat Jumat {self.prayer_start:%H:%M}-{self.prayer_end:%H:%M}"})
        return out

    def suggest(self, start: datetime, duration_min: int, attendee_tz: dict[str, str]) -> datetime | None:
        """Slot valid terdekat (kelipatan 30 menit) mulai dari start, maksimal 21 hari ke depan."""
        cur = start.replace(second=0, microsecond=0)
        cur += timedelta(minutes=(-cur.minute) % 30)
        for _ in range(21 * 48):
            if not self.violations(cur, duration_min, attendee_tz):
                return cur
            cur += timedelta(minutes=30)
        return None

    def show(self, dt: datetime, zone: str) -> str:
        l = dt.astimezone(self.tz(zone))
        return f"{DAYS_ID[l.weekday()]}, {l:%d-%m-%Y %H:%M} {zone}"
