# Office Agent RS

Challenge B (The Office Agent), skenario Meeting to action, untuk AI CAN DO IT Hackathon Indonesia 2026.
Notulen atau voice note rumah sakit menjadi minutes, action items, email, dan jadwal follow-up.
Tidak ada yang terkirim atau terjadwal sebelum manusia menyetujui detail persisnya.

## Arsitektur singkat

```
WorkBuddy (LLM + skill)  --MCP-->  office-agent-rs (kernel)  --hanya rencana approved-->  executor mock
        |                              validasi deterministik                                 (email/kalender/task)
        |                              audit log berantai hash
   tidak punya tool approve                    ^
                                               |  approve / tolak
                              UI persetujuan manusia (proses terpisah, 127.0.0.1:8250)
```

Batas kepercayaan: LLM hanya menyusun rencana. Kernel memeriksa kontak ambigu, jadwal (WIB/WITA/WIT, jam kerja,
sholat Jumat, libur), instruksi tertanam, dan kutipan sumber. Persetujuan terikat hash isi rencana; bila isi berubah, eksekusi ditolak.

## Menjalankan

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest          # 23 tes
.venv/Scripts/python -m office_agent.approval_ui   # layar persetujuan
.venv/Scripts/python -m office_agent.server        # MCP server (stdio) untuk WorkBuddy
```

Skill untuk WorkBuddy ada di `workbuddy/SKILL.md`. Semua data (kontak, aturan, notulen) adalah data mock di `data/`.
Daftar hari libur di `data/rules.json` hanya contoh demo.
