# 02. Aturan farming free-mint

Free mint di sini artinya **biaya satu-satunya adalah gas**. Kalau kontrak meminta value lebih dari 0, itu mint berbayar: jelaskan harganya dan jangan jalankan otomatis.

Farming adalah antrean kecil yang tetap lewat audit, pratinjau, dan `confirm` bila pengguna meminta eksekusi. Sinyal scanner tidak menambah izin.

## Syarat sebelum masuk antrean

1. Harga di kontrak 0 (pengguna hanya bayar gas).
2. Kontrak lolos audit bab 03: bytecode ada, source terverifikasi, bukan jerat deposit, alamat sama dengan konfigurasi resmi.
3. Koleksi belum dipegang dompet ini, kecuali pengguna secara eksplisit meminta mint tambahan dan kuota masih ada.
4. Belum berakhir dan belum sold out. Progres `>= 99,9%` diperlakukan habis: lewati.
5. Sisa kuota per dompet lebih dari 0.
6. Batas harian dan batas per putaran yang ditetapkan pengguna belum terlewati.

Kalau pengguna belum menetapkan batas, tanyakan dulu. Jangan mengarang angka lalu mint berulang. Di contoh panduan ini, batas fiktifnya 3 per hari dan 1 per putaran — itu ilustrasi, bukan konfigurasi pribadi siapa pun.

## Tautan jual resmi

Setelah mint yang sah, sertakan tempat jual yang dipakai proyek itu sendiri: halaman market di situs resmi, atau akun resmi proyek. Jangan hanya menempel marketplace umum yang tidak disebut proyek. Kalau tautan resmi tidak ketemu, katakan tidak ketemu. Jangan mengarang URL.

Placeholder bentuknya `https://proyek-contoh.example/market`.

## Urutan satu putaran

1. Baca daftar kandidat (dari pengguna atau dari scanner yang sudah disaring).
2. Buang yang gagal syarat di atas.
3. Urutkan sisa sesuai prioritas bab 07: berpagar, gelombang, lalu panas.
4. Ambil paling banyak sesuai batas per putaran.
5. Untuk tiap kandidat: pratinjau satu mint, tunggu `confirm`, kirim satu transaksi, laporkan explorer setelah receipt.
6. Berhenti kalau batas harian tercapai, gas mendekati cadangan, atau kandidat habis.

Jangan mengirim beberapa mint dalam satu `confirm`.

## Checklist

- [ ] Value di kontrak benar-benar 0
- [ ] Bukan koleksi yang sudah dipegang (kecuali diminta dan kuota ada)
- [ ] Belum berakhir, progres di bawah 99,9%, kuota per dompet > 0
- [ ] Audit kontrak lolos, alamat dari sumber resmi
- [ ] Batas harian dan per putaran diketahui, bukan ditebak
- [ ] Cadangan gas aman setelah perkiraan biaya
- [ ] Tautan jual resmi dicari, atau dinyatakan tidak ada
- [ ] Setiap mint punya pratinjau dan `confirm` sendiri

## Contoh: kandidat digugurkan

Pengguna: Farming lima koleksi ini. Batas harianku 3, per putaran 1.

Muse: Aku belum mengirim mint. Dari lima kandidat, yang bisa masuk antrean cuma satu. Dua sudah ada di `0xYOUR_WALLET`, satu progress-nya di atas 99,9%, satu value-nya bukan 0 jadi bukan free mint. Sisa yang lolos: `0xCONTRACT`, kuota per dompet masih 1, tautan jual resmi `https://proyek-contoh.example/market`. Batas putaran ini 1, jadi hanya itu yang kupratijau. Balas `confirm` kalau mau kirim satu mint value 0 itu.

## Contoh: batas harian sudah penuh

Pengguna: Lanjut putaran lagi, masih ada gelombang.

Muse: Tidak lanjut. Batas harian yang kamu tetapkan sudah tercapai, jadi tidak ada mint tambahan hari ini. Gelombang baru tetap hanya sinyal, bukan izin. Belum ada transaksi dari permintaan ini. Besok kita bisa saring ulang, asal kontraknya masih lolos dan kuotanya masih ada.

## Kalau pemantauan tiap 30 menit

Batas per putaran bawaan pada konfigurasi contoh adalah **5** mint gratis. Itu langit-langit satu pemeriksaan, bukan target untuk dihabiskan. Karena grid-nya rapat, deduplikasi wajib: lead yang sudah dilihat tidak dihitung ulang. Batas harian tetap mengalahkan angka 5. Kalau batas harian belum kamu tetapkan, Muse bertanya dan tidak mengarang angka lalu mint berulang. Lihat [bab 11](11-pemantauan-rutin.md).

## Kesalahan yang sering

- Menganggap "gas only" hanya karena tulisan di postingan, tanpa membaca harga di kontrak
- Mint ulang koleksi yang sudah dipegang hanya karena namanya muncul lagi di scanner
- Memakai marketplace umum karena tautan resmi malas dicari
- Menghabiskan batas harian dalam satu confirm berantai
- Farming mint berbayar yang dipaket "murah" tanpa menjelaskan harga dan menunggu
