# 10. Alur scan free-mint lewat X

Ini alur utuh satu putaran pencarian mint gratis. Muse membaca X lewat browser yang sudah login, menyalin posting ke berkas, lalu memakai pemindai baca-saja. Tidak ada langkah yang mengirim transaksi.

Akun yang dipakai adalah **akun X yang login di browser Muse**. Hanya baca.

## 1. Apa yang dicari

Buka pencarian X. Contoh kueri, satu per satu, bukan dicampur sampai tidak terbaca:

- `free mint` bersama BNB atau BNB Chain
- `gas only`
- `FCFS`
- `0 BNB`
- `#BNBChain` bersama kata mint
- kata peluncuran NFT atau agen, kalau proyek memang memakai gerbang itu

Pencarian lanjutan yang berguna:

- `filter:links` supaya posting yang hanya teks kosong tidak mengalahkan yang membawa situs
- `min_faves:20` kalau mau menyaring yang benar-benar dilihat orang; angka ini contoh, bukan ambang wajib
- `since:` tanggal hari ini atau kemarin, supaya yang basi tidak ikut

Selain pencarian, baca daftar akun yang memang dipantau. Namanya di konfigurasi, placeholder semacam `akun_contoh`. Jangan mengarang akun dari ingatan. Posting mereka tidak otomatis aman.

Abaikan giveaway yang minta DM, dan abaikan "kirim X supaya dapat Y".

## 2. Cara membaca satu posting

Catat, tanpa mengklik connect dan tanpa memindai QR:

- alamat kontrak, kalau tertulis
- tautan situs mint
- jam yang disebut di teks (ini hanya klaim, bukan kebenaran)
- umur akun dan jumlah pengikut, kalau terlihat
- balasan yang melaporkan scam, drain, atau mint berbayar yang diklaim gratis

Kalau alamat tidak ada, jangan menebak. Tulis "tanpa alamat" dan lanjut.

## 3. Verifikasi

Alamat resmi hanya dari situs proyek, akun resmi proyek, atau berkas konfigurasi yang kita pegang. Alamat di posting orang lain harus cocok dengan salah satu sumber itu sebelum naik ke pratinjau.

Salin posting yang baru ke `posts.json` (atau tempelan teks). Lalu, tanpa token API kalau berkasnya sudah ada:

```bash
python -m scanner scan --config scanner/config.example.yaml --input posts.json --out out
```

Pemindai hanya `eth_call`, `eth_getCode`, `eth_getStorageAt`, dan pembacaan log. Yang dicari:

- bytecode ada atau tidak
- proxy (slot EIP-1967) dan kuasa owner, terutama petunjuk `withdraw` pada deposit
- harga: gratis (0) atau berbayar
- progres suplai, sold out kalau `>= 99,9%`
- batas per dompet
- paused
- waktu buka on-chain, ditampilkan dalam WIB

Percaya waktu kontrak, bukan jam di posting. Pernah ada mint yang buka sejam lebih awal dari teks dan habis dalam kurang dari 6 menit.

Token id agen yang tampil sebagai nomor manusia bisa berupa hash on-chain. Jangan memakainya sebagai argumen sebelum dibaca dari kontrak.

## 4. Keputusan

Hanya mint yang biayanya gas. Lewati yang sudah dipegang, sudah berakhir, atau sold out. Jaga cadangan gas sekitar 0.0003 BNB.

Pada grid 30 menit, langit-langit satu putaran adalah **5** mint gratis. Itu bukan target. Batas harian tetap mengalahkannya. Kalau batas harian belum ditetapkan, tanyakan.

Kalau harga bukan 0, jelaskan angkanya dan tunggu. Jangan jalankan otomatis.

`setApprovalForAll` tetap ditolak. Approval, kalau nanti diminta untuk jual, hanya satu token id.

## 5. Laporan ke pengguna

Bahasa Indonesia, singkat, jawaban di depan. Untuk setiap kandidat yang layak disebut:

- tautan posting
- kontrak (`0xCONTRACT` di contoh publik)
- status
- waktu buka WIB
- risiko
- tautan jual resmi proyek, atau kalimat "tautan jual resmi tidak ketemu"

Selalu tutup dengan: pratinjau lalu tunggu konfirmasi. Jangan mengaku sudah mint.

Kalau tidak ada yang baru, jangan mengirim pesan.

## 6. Waktu

Untuk mint berjadwal, mulai mengawasi lebih awal dari jam posting. Grid 30 menit plus satu cek sekitar 20 menit sebelum `mintStart`. Jangan satu pengingat sekali jalan.

## 7. Kebersihan harian

- tandai posting yang sudah dilihat (`state/seen.json`)
- catat keputusan di watchlist: kenapa dilanjut, ditunda, atau dibuang
- variasikan teks raffle kalau hari itu juga ada entri; jangan menyalin kemarin
- jangan menebus kode promo yang tidak diketik pengguna

## 8. Browser

- hanya baca
- jangan memposting, mengikuti, menyukai, atau mengirim DM tanpa izin
- kata sandi hanya di formulir login, tidak di chat
- kode 2FA dimasukkan pengguna
- jangan klik connect wallet dan jangan memindai QR dari posting
- kalau browser logout, berhenti dan beri tahu
- kalau situs minta verifikasi yang aneh, berhenti dan beri tahu

## Contoh putaran A — belum buka

Posting `akun_contoh` menulis free mint jam 21:00 dan menautkan situs resmi. Di situs, kontraknya `0xCONTRACT`. Pemindai membaca `mintStart` yang setara 20:00 WIB, harga 0, progres 4%, kuota per dompet 1, tidak paused.

Muse: Belum aku mint. Posting bilang 21:00, kontrak bilang 20:00 WIB, jadi aku ikut kontrak. Status `waiting_open`. Tautan jual resmi: `https://proyek-contoh.example/market`. Aku pasang grid 30 menit dan satu cek tambahan sekitar 20 menit sebelum 20:00 WIB. Tidak ada transaksi. Nanti, kalau sudah buka dan kuota masih ada, pratinjaunya satu mint value 0, lalu aku menunggu `confirm`.

## Contoh putaran B — disebut gratis, ternyata bayar

Teksnya "gas only", tetapi `price()` bukan 0.

Muse: Ini bukan free mint. Harga on-chain bukan nol, jadi aku tidak memasukkannya ke antrean gas. Belum ada transaksi. Kalau setelah tahu angkanya kamu tetap mau, itu pratinjau berbayar terpisah dan `confirm` terpisah. Aku tidak menjalankannya otomatis.

## Contoh putaran C — scam dan sold out

Satu posting minta DM lalu kirim BNB ke `0xALAMAT_BARU`. Posting lain progresnya 99,95%.

Muse: Dua-duanya tidak dilanjut. Yang pertama pola kirim-supaya-dapat lewat DM; tidak ada dana yang pergi. Yang kedua sold out karena progres melewati 99,9%. Belum ada mint. Keduanya tercatat supaya 30 menit lagi tidak kuulang sebagai berita baru.

## Checklist satu putaran

- [ ] Pencarian dan daftar akun dijalankan, retweet disaring
- [ ] Giveaway DM dan "kirim supaya dapat" dibuang
- [ ] Alamat hanya naik kalau cocok dengan sumber resmi, atau ditandai belum resmi
- [ ] `--input` dipakai untuk posting dari browser; tidak ada tanda tangan
- [ ] Harga, progres, kuota, paused, proxy, dan WIB sudah dibaca
- [ ] Yang dipegang, habis, atau berbayar tidak masuk antrean gratis
- [ ] Tidak lebih dari 5 kandidat pada putaran ini, dan batas harian belum jebol
- [ ] Cadangan gas aman
- [ ] Laporan menyebut tautan, status, WIB, risiko, dan tautan jual resmi
- [ ] Langkah berikut adalah pratinjau lalu `confirm`, atau diam kalau kosong
