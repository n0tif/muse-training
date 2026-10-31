# Daftar cek — satu putaran scan free-mint

Ikuti urutan ini. Berhenti di langkah yang gagal. Jangan mengirim transaksi di daftar ini.

1. Buka X dengan akun X yang login di browser Muse. Hanya baca. Kalau logout atau verifikasi terasa aneh, berhenti dan beri tahu.
2. Jangan memposting, mengikuti, menyukai, atau mengirim DM. Jangan ketik kata sandi di chat. 2FA dimasukkan pengguna. Jangan klik connect wallet. Jangan memindai QR.
3. Jalankan kueri: `free mint`, `gas only`, `FCFS`, `0 BNB`, `#BNBChain` mint, plus kata peluncuran NFT atau agen bila relevan. Pakai `filter:links`, dan `since:` hari ini. `min_faves` hanya penyaring longgar.
4. Baca akun pada daftar pantau (`akun_contoh` hanyalah placeholder). Jangan mengarang akun.
5. Buang giveaway yang minta DM atau "kirim supaya dapat".
6. Untuk tiap posting: catat kontrak, situs, jam di teks, umur akun, pengikut, dan balasan yang menuduh scam.
7. Cocokkan alamat dengan situs resmi, akun resmi, atau konfigurasi. Kalau tidak cocok, jangan naikkan ke pratinjau.
8. Simpan posting baru ke `posts.json`. Jalankan `python -m scanner scan --input posts.json`.
9. Baca harga, progres, batas per dompet, paused, proxy, dan waktu buka WIB. Percaya kontrak, bukan posting.
10. Lewati yang sudah dipegang, sold out (`>= 99,9%`), berakhir, paused, atau berbayar.
11. Pada putaran ini paling banyak 5 kandidat gratis. Batas harian tetap berlaku. Cadangan gas sekitar 0.0003 BNB harus utuh.
12. Laporkan yang lolos: tautan posting, kontrak, status, WIB, risiko, tautan jual resmi (atau katakan tidak ketemu).
13. Tutup dengan pratinjau lalu menunggu `confirm`. Satu tindakan per `confirm`.
14. Tandai seen. Kalau tidak ada yang baru, jangan kirim pesan.
