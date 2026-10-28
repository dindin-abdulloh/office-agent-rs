"""Layar konfirmasi manusia. Proses terpisah dari MCP server: di sinilah satu-satunya tempat approve.

Jalankan: python -m office_agent.approval_ui   (http://127.0.0.1:8251)
"""
from __future__ import annotations

import html
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .kernel import Kernel, KernelError

DATA_DIR = Path(os.getenv("OFFICE_AGENT_DATA", Path(__file__).resolve().parents[2] / "data"))
kernel = Kernel(DATA_DIR)
app = FastAPI(title="Office Agent RS - Persetujuan")
e = html.escape

CSS = """
:root{--bg:#f6f7f9;--fg:#1c2430;--card:#fff;--line:#dde2ea;--ok:#117a4a;--bad:#b42318;--warn:#a15c00;--acc:#1d4ed8}
@media (prefers-color-scheme:dark){:root{--bg:#10151c;--fg:#e6eaf0;--card:#18202a;--line:#2b3644;--ok:#4ade80;--bad:#f87171;--warn:#fbbf24;--acc:#7aa2ff}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.tag{display:inline-block;padding:2px 8px;border-radius:99px;border:1px solid var(--line);font-size:13px}
.blocking{color:var(--bad)}.warning{color:var(--warn)}.high_impact{color:var(--bad);font-weight:600}
button{font:inherit;padding:8px 16px;border-radius:8px;border:1px solid var(--line);cursor:pointer;background:var(--card);color:var(--fg)}
button.ok{background:var(--ok);color:#fff;border-color:var(--ok)}button.no{border-color:var(--bad);color:var(--bad)}
input[type=text]{font:inherit;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg)}
pre{white-space:pre-wrap;margin:0;font:inherit}a{color:var(--acc)}
"""


def page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"<!doctype html><html lang='id'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                        f"<title>{e(title)}</title><style>{CSS}</style></head><body><main>{body}</main></body></html>")


@app.get("/", response_class=HTMLResponse)
def index():
    rows = ""
    for p in reversed(kernel.list_plans()):
        rows += (f"<div class='card'><a href='/plans/{p['plan_id']}'><b>{e(p['plan_id'])}</b></a> "
                 f"<span class='tag'>{e(p['status'])}</span><br>{e(p['request_text'][:140])}</div>")
    ok, n = kernel.audit.verify()
    return page("Persetujuan", f"<h1>Persetujuan Office Agent RS</h1>{rows or '<p>Belum ada rencana.</p>'}"
                               f"<p>Audit log: {n} entri, rantai hash {'utuh' if ok else '<b class=blocking>RUSAK</b>'}.</p>")


@app.get("/plans/{plan_id}", response_class=HTMLResponse)
def view(plan_id: str, msg: str = ""):
    try:
        plan = kernel.get_plan(plan_id)
    except KernelError as ex:
        return page("Error", f"<p class='blocking'>{e(str(ex))}</p>")
    d = kernel.describe(plan)
    b = f"<h1>Rencana {e(plan_id)} <span class='tag'>{e(plan['status'])}</span></h1>"
    if msg:
        b += f"<div class='card blocking'>{e(msg)}</div>"
    b += f"<div class='card'><b>Permintaan asli</b><pre>{e(plan['request_text'])}</pre></div>"
    if plan["minutes"]:
        minutes = plan["minutes"].replace("\\n", "\n")  # LLM kadang mengirim newline ter-escape
        b += f"<div class='card'><b>Draf notulen</b><pre>{e(minutes)}</pre></div>"
    if plan["injection_findings"]:
        items = "".join(f"<li><code>{e(f['text'])}</code> ({e(f['doc_id'])}, baris {f['line']})</li>" for f in plan["injection_findings"])
        b += f"<div class='card'><b class='blocking'>Instruksi tertanam terdeteksi dan DIABAIKAN</b><ul>{items}</ul></div>"
    b += "<div class='card'><b>Aksi yang akan dijalankan setelah Anda setuju</b><ul>" + "".join(f"<li>{e(l)}</li>" for l in d["ringkasan_aksi"]) + "</ul></div>"
    if plan["issues"]:
        items = "".join(f"<li class='{i['severity']}'>[{e(i['code'])}] {e(i['message'])}</li>" for i in plan["issues"])
        b += f"<div class='card'><b>Catatan validasi</b><ul>{items}</ul></div>"
    if plan["clarifying_questions"]:
        items = "".join(f"<li>{e(q)}</li>" for q in plan["clarifying_questions"])
        b += f"<div class='card'><b>Menunggu klarifikasi (belum bisa disetujui)</b><ul>{items}</ul></div>"
    srcs = [(a["id"], s) for a in plan["actions"] for s in a["sources"]]
    if srcs:
        b += "<div class='card'><b>Sumber</b><ul>" + "".join(f"<li>[{e(i)}] {e(s['doc_id'])}: &ldquo;{e(s['quote'])}&rdquo;</li>" for i, s in srcs) + "</ul></div>"
    if plan["status"] == "awaiting_approval":
        high = d["needs_extra_confirmation"]
        extra = ("<p class='high_impact'><label><input type='checkbox' name='confirm_high_impact' value='1'> "
                 "Saya paham ini berdampak tinggi (penerima eksternal / banyak penerima / pembayaran) dan menyetujuinya.</label></p>") if high else ""
        b += (f"<form method='post' action='/plans/{e(plan_id)}/approve' class='card'><p>Setujui <b>persis</b> detail di atas?</p>{extra}"
              "<p><input type='text' name='approver' placeholder='Nama Anda' required> "
              "<button class='ok' type='submit'>Setujui</button></p></form>"
              f"<form method='post' action='/plans/{e(plan_id)}/reject'><input type='text' name='reason' placeholder='Alasan (opsional)'> "
              "<input type='hidden' name='approver' value='manusia'><button class='no' type='submit'>Tolak</button></form>")
    trail = "".join(f"<li><code>{e(r['ts'][11:19])}</code> {e(r['event'])} oleh {e(r['actor'])}</li>" for r in kernel.audit.read(plan_id))
    b += f"<div class='card'><b>Jejak audit</b><ul>{trail}</ul></div><p><a href='/'>Kembali</a></p>"
    return page(f"Rencana {plan_id}", b)


@app.post("/plans/{plan_id}/approve")
def approve(plan_id: str, approver: str = Form(...), confirm_high_impact: str = Form("")):
    try:
        kernel.approve_plan(plan_id, approver.strip() or "manusia", confirm_high_impact == "1")
        return RedirectResponse(f"/plans/{plan_id}", status_code=303)
    except KernelError as ex:
        return RedirectResponse(f"/plans/{plan_id}?msg={e(str(ex))}", status_code=303)


@app.post("/plans/{plan_id}/reject")
def reject(plan_id: str, approver: str = Form("manusia"), reason: str = Form("")):
    try:
        kernel.reject_plan(plan_id, approver, reason)
    except KernelError:
        pass
    return RedirectResponse(f"/plans/{plan_id}", status_code=303)


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("APPROVAL_UI_PORT", "8251")))


if __name__ == "__main__":
    main()
