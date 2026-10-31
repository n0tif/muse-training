# Daftar cek — pemantauan tiap 30 menit

Zona Asia/Jakarta. Grid bawaan `*/30 7-23 * * *`. Hemat: `0 7-23 * * *` atau `0 7-23/2 * * *`.

1. Kalau sekarang di luar 07:00–23:00 WIB, jangan menjalankan grid. Satu cek pra-buka tetap boleh kalau `mintStart` memang sebentar lagi.
2. Pastikan browser masih login. Kalau logout, berhenti dan beri tahu. Jangan menebak posting.
3. Hanya baca akun X yang login di browser Muse. Tanpa posting, follow, like, atau DM. Tanpa connect wallet dan tanpa QR.
4. Kumpulkan posting baru sejak putaran lalu, termasuk akun pantau.
5. Jalankan `python -m scanner monitor --input posts.json --out out/changes.md`.
6. Kalau berkas itu hanya bilang tidak ada yang baru, jangan kirim pesan. Selesai.
7. Untuk yang berubah: sebut status baru (`waiting_open`, `open`, `ended`, `skipped`), alasan, WIB, dan tautan.
8. `waiting_open` yang masuk 20 menit terakhir: beri tahu sekali, dan pastikan ada cek tambahan sebelum jam on-chain.
9. Yang gratis dan `open`: paling banyak 5 untuk dibahas pada putaran ini. Sisanya tunda. Batas harian mengalahkan angka 5.
10. Yang berbayar: sebut harganya dan tunggu. Jangan auto-mint.
11. Bendera merah: beri tahu, jangan kerjakan.
12. Gelombang Transfer dari address(0) dan panas pemanggil unik hanya sinyal. Tetap verifikasi.
13. Kalau hari ini ada batas raffle, siapkan kalimat baru (bukan salinan kemarin) secara terpisah dari mint.
14. Klaim airdrop hanya value 0 di kontrak terverifikasi, pratinjau sendiri.
15. Token yang dipegang dan baru punya pasar: katakan nilainya baru bisa dibaca, bukan saran beli.
16. RPC gagal: coba URL cadangan sekali. Kalau tetap gagal, beri tahu sekali, lalu diam sampai pulih.
17. Perbarui seen dan watchlist. Jangan mengulang lead yang sama pada setengah jam berikutnya.
