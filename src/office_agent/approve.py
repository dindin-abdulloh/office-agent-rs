"""Persetujuan manusia lewat terminal (alternatif UI web).

Pakai:  python -m office_agent.approve P-xxxxxxxx --by "Nama Anda"
Tampilkan detail persis, lalu minta Anda mengetik 'setuju'. Menolak berjalan tanpa terminal
interaktif, supaya skrip atau agent tidak bisa menyetujui atas nama manusia.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .kernel import Kernel, KernelError

DATA_DIR = Path(os.getenv("OFFICE_AGENT_DATA", Path(__file__).resolve().parents[2] / "data"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Setujui atau tolak rencana Office Agent sebagai manusia.")
    ap.add_argument("plan_id")
    ap.add_argument("--by", required=True, help="Nama Anda, dicatat di audit")
    ap.add_argument("--reject", action="store_true", help="Tolak rencana, bukan menyetujui")
    args = ap.parse_args(argv)

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("Ditolak: perintah ini hanya jalan di terminal interaktif yang diketik manusia.", file=sys.stderr)
        return 2

    kernel = Kernel(DATA_DIR)
    try:
        plan = kernel.get_plan(args.plan_id)
        view = kernel.describe(plan)
    except KernelError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"\nRencana {plan['plan_id']}  status: {plan['status']}")
    print(f"Permintaan: {plan['request_text']}\n")
    for line in view["ringkasan_aksi"]:
        print("  " + line)
    for f in view["injection_findings"]:
        print(f"\n  ! Instruksi tertanam DIABAIKAN ({f['doc_id']} baris {f['line']}): {f['text']}")
    for i in view["issues"]:
        print(f"  [{i['severity']}] {i['code']}: {i['message']}")
    for q in view["clarifying_questions"]:
        print(f"  ? {q}")
    print()

    try:
        if args.reject:
            if input("Ketik 'tolak' untuk menolak rencana ini: ").strip().lower() != "tolak":
                print("Dibatalkan, tidak ada perubahan.")
                return 1
            kernel.reject_plan(args.plan_id, args.by)
            print("Rencana ditolak dan dicatat di audit.")
            return 0

        high = view["needs_extra_confirmation"]
        if input("Ketik 'setuju' untuk menyetujui PERSIS detail di atas: ").strip().lower() != "setuju":
            print("Dibatalkan, tidak ada perubahan.")
            return 1
        if high and input("Rencana berdampak tinggi. Ketik 'saya paham' untuk melanjutkan: ").strip().lower() != "saya paham":
            print("Dibatalkan, tidak ada perubahan.")
            return 1
        kernel.approve_plan(args.plan_id, args.by, confirm_high_impact=high)
        print(f"Disetujui oleh {args.by} dan dicatat di audit. Agent sekarang boleh mengeksekusi.")
        return 0
    except KernelError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nDibatalkan, tidak ada perubahan.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
