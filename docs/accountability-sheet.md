# Accountability Sheet: Office Agent RS

Challenge B (The Office Agent), skenario Meeting to Action. Pengguna: staf administrasi dan sekretaris direksi rumah sakit.
Agent mengubah notulen rapat atau voice note menjadi minutes, action items, email, dan jadwal tindak lanjut. Tidak ada yang dikirim atau dijadwalkan sebelum manusia menyetujui detail persisnya.

## 1. Apa yang bisa diakses agent

| Data | Cara akses | Batas |
|---|---|---|
| Dokumen sumber (notulen, transkrip voice note) | `read_document`, hanya yang terdaftar di indeks | Teks diperlakukan sebagai data, bukan perintah |
| Buku kontak (nama, jabatan, email, zona waktu) | `find_contact` | Hanya orang di buku kontak |
| Aturan operasional (jam kerja, sholat Jumat, libur) | `check_slot` | Daftar libur saat ini data contoh |
| Rencana dan audit miliknya sendiri | `get_plan_status`, `get_audit_trail` | Hanya baca |

Agent tidak punya akses ke email, kalender, atau sistem rumah sakit yang sebenarnya. Semua tool eksekusi adalah simulasi (mock).

## 2. Yang dijalankan agent secara mandiri (tanpa persetujuan)

* Membaca dokumen dan mencari kontak.
* Memeriksa slot jadwal.
* Menyusun dan mengajukan rencana (`submit_plan`). Mengajukan tidak mengeksekusi apa pun.
* Melaporkan status dan jejak audit.

## 3. Yang wajib disetujui manusia

| Aksi | Persetujuan |
|---|---|
| Kirim email | Layar konfirmasi: penerima, subjek, isi persis |
| Buat acara kalender | Layar konfirmasi: peserta, waktu per zona, durasi |
| Buat tugas | Layar konfirmasi: penanggung jawab, tenggat |
| Dampak tinggi (penerima eksternal, lebih dari 3 penerima, menyinggung pembayaran) | Konfirmasi kedua yang eksplisit |
| Undo | Hanya dalam 60 detik sejak eksekusi |

Persetujuan hanya bisa diberikan lewat UI web lokal atau CLI yang menolak berjalan tanpa terminal interaktif. Persetujuan terikat hash isi rencana: bila isi diubah setelah diajukan atau disetujui, eksekusi ditolak.

## 4. Yang tidak akan pernah dilakukan agent

1. Menyetujui rencananya sendiri. Tidak ada tool approve di MCP server.
2. Mengikuti instruksi yang tertanam di dokumen atau pesan. Instruksi terdeteksi dibuang, dilaporkan, dan dicatat.
3. Menebak penerima yang ambigu (misalnya dua orang bernama Budi). Ia bertanya.
4. Menjadwalkan di luar jam kerja, di akhir pekan, di hari libur, di waktu yang sudah lewat, atau saat sholat Jumat (dihitung pada jam lokal setiap peserta).
5. Mengirim ke orang yang tidak ada di buku kontak.
6. Mengubah isi rencana setelah disetujui, atau menghapus jejak audit tanpa terdeteksi (rantai hash).
7. Mengeksekusi rencana yang ditolak, belum disetujui, atau sudah dieksekusi.

## 5. Bukti dan catatan

* Setiap kueri, keputusan, persetujuan, dan eksekusi tercatat di catatan audit yang hanya bisa ditambah, dengan rantai hash.
* Aksi dari dokumen ditandai `origin=document` dan ditolak kernel. Setiap aksi menyertakan kutipan sumber yang diperiksa terhadap isi dokumen.

## 6. Keterbatasan yang diketahui (jujur)

* Tool email, kalender, dan tugas hanya mensimulasikan hasil. Tidak ada pengiriman nyata.
* Deteksi instruksi tertanam berbasis pola (kata kunci dan penyapaan ke AI). Instruksi yang disamarkan dengan cara lain bisa lolos dari pemindai. Lapisan kedua, yaitu penandaan `origin` oleh agent, bergantung pada kejujuran model.
* Pertanyaan klarifikasi nama ambigu terjadi di sisi agent; kernel menjadi pagar kedua saat rencana diajukan.
* Dalam uji, WorkBuddy pernah menjawab pertanyaan pilihan secara otomatis dengan opsi pertama. Karena itu pilihan kontak tetap diperiksa lagi di layar konfirmasi.
* Dalam uji, agent pernah menulis "slot sudah dicek" tanpa memanggil `check_slot`, dan memakai kata "terkirim" untuk hasil simulasi. Skill sudah diperbaiki (wajib `check_slot`, wajib menyebut "simulasi"), tetapi belum diulang pada seluruh kasus uji.
* Agent belum otomatis membuat tugas dari action item notulen; baru email dan acara yang teruji dari ujung ke ujung.
* Input voice note saat ini berupa transkrip teks, bukan audio.
* Nama penyetuju diketik bebas; belum ada autentikasi pengguna.
* Daftar hari libur adalah data contoh dan perlu diganti dengan SKB resmi.
