# 11. Pemantauan rutin

Pemindaian sekali jalan mudah ketinggalan. Muse mengulang pemeriksaan pada jam bangun, lalu diam kalau tidak ada yang berubah.

## Jadwal bawaan

Tiap **30 menit**, dari **07:00 sampai 23:00 WIB**.

Ekspresi untuk penjadwal Muse, zona Asia/Jakarta:

```text
*/30 7-23 * * *
```

GitHub Actions, kalau suatu saat dihidupkan, memakai UTC. 07:00–23:00 WIB sama dengan 00:00–16:00 UTC, yaitu `*/30 0-16 * * *`. Workflow di repo ini tetap mati sampai dijalankan manual.

## Alternatif hemat

Kalau pemakaian terasa boros, jangan menghapus deduplikasi. Longgarkan grid:

- tiap jam: `0 7-23 * * *`
- tiap 2 jam: `0 7-23/2 * * *`

Jangan mengganti bawaan 30 menit menjadi setiap menit. Jendela mint yang habis di bawah 6 menit tetap butuh cek tambahan dekat waktu buka, bukan polling semalaman.

## Diam

Kalau seen tidak bertambah dan watchlist tidak berubah, keluaran monitor adalah satu kalimat: tidak ada yang baru, jangan kirim pesan ke pengguna. Jangan menyapa "masih aman" tiap setengah jam.

Ringkasan harian boleh, sekali, bukan tiap putaran.

## Isi satu putaran

1. Baca posting baru sejak putaran lalu lewat browser, akun X yang login di browser Muse.
2. Baca akun yang ada di daftar pantau.
3. Cek ulang lead yang sudah ada di watchlist: sudah buka, harga berubah, sold out, atau paused.
4. Baca gelombang: Transfer dengan `from` address(0) pada blok terbaru, lalu panas dari pemanggil unik.
5. Deduplikasi `state/seen.json` dan `state/watchlist.json`.
6. Tulis hanya selisih ke `out/changes.md`.

Perintah:

```bash
python -m scanner monitor --config scanner/config.example.yaml --input posts.json --out out/changes.md
```

## Siklus watchlist

| Status | Arti |
| --- | --- |
| `new` | baru terlihat, data on-chain belum cukup |
| `verified` | sebagian terbaca, harga atau waktu belum lengkap |
| `waiting_open` | waktu buka on-chain di masa depan, disimpan dalam WIB |
| `open` | harga 0, tidak paused, tidak sold out, tidak menunggu jam |
| `minted` | sudah ditandai dikerjakan |
| `skipped` | berbayar, paused, bendera merah, atau bukan kontrak |
| `ended` | sold out atau progres `>= 99,9%` |

Setiap perpindahan menyimpan alasan. `minted` tidak diisi sendiri oleh alat; ia menunggu catatan keputusan.

## Mint berwaktu

Begitu `mintStart` terbaca, simpan WIB-nya. Grid 30 menit tetap jalan. Tambahkan satu cek sekitar 20 menit sebelum waktu itu. Jangan mengandalkan salah satu saja. Cek tambahan ini boleh sedikit melewati jam 23:00 kalau memang itu saatnya buka. Setelah itu berhenti. Jangan berjaga semalaman.

## Kapan berbicara

Beri tahu hanya kalau:

- gratis, sudah buka, dan lolos cek
- sebentar lagi buka menurut waktu on-chain
- status lead yang sedang dipantau berubah (buka, harga, sold out, paused)
- ada peringatan scam

Jangan memberi tahu hanya karena ada posting baru yang sold out, atau karena pengikutnya sedikit, kalau tidak ada yang bisa dikerjakan.

Mint berbayar dijelaskan lalu ditunggu, tidak dijalankan otomatis. Mint gratis hanya setelah pratinjau dan `confirm`. Izin tetap, kalau pengguna memang menyatakannya, tetap tidak meniadakan pratinjau satu tindakan.

## Batas pada grid yang rapat

Batas per putaran bawaan: **5** mint gratis. Dengan cek tiap 30 menit, tanpa deduplikasi angka itu bisa berarti puluhan mint sehari. Deduplikasi dan batas harian mencegah itu.

Batas 5 adalah langit-langit putaran ini, bukan kuota yang harus dihabiskan. Kandidat keenam menunggu putaran lain, dan hanya kalau batas harian masih ada. Batas harian ditetapkan pengguna. Kalau belum ada, tanyakan. Jangan mengarang.

Cadangan gas sekitar 0.0003 BNB tetap tidak boleh ditembus.

## Selain mint

Pada putaran yang sama, kalau memang waktunya:

- entri raffle harian yang mendekati batas waktu: posting baru, kalimat berbeda, tagar resmi, `<AGENT_ID>`
- jendela klaim airdrop value 0 di kontrak terverifikasi
- cek hasil yang memang dijanjikan sumber resmi
- likuiditas atau pasar yang baru muncul untuk token yang memang dipegang; nilai tetap tidak diketahui sampai ada pasar, dan itu bukan saran beli

## Kalau sesuatu gagal

- Batas laju API: mundur, jangan dipaksa. Kalau tetap gagal, beri tahu sekali.
- Browser logout: berhenti. Jangan menebak posting.
- Verifikasi aneh atau QR: berhenti.
- RPC gagal: coba `BSC_RPC_FALLBACK_URL` atau URL cadangan di konfigurasi. Kalau semua gagal, katakan sekali, jangan mengulang tiap 30 menit sampai pulih.
- Jangan mengirim transaksi untuk "mencoba apakah RPC hidup".

## Contoh: diam, lalu satu perubahan

Pukul 10:00 dan 10:30 WIB watchlist sama. Muse tidak mengirim pesan.

Pukul 11:00 progres sebuah kontrak melewati 99,9%. Muse mengirim satu catatan: status menjadi `ended`, alasan sold out, tidak ada mint. Pukul 11:30, kalau tidak ada hal lain, diam lagi.

## Contoh: segera buka

`waiting_open` dengan WIB 16:00. Pada 15:40 Muse memberi tahu sekali dan mengingatkan cek tambahan, bukan mint. Pada 16:10, kalau harga masih 0 dan kuota ada, baru pratinjau. Tanpa `confirm`, tidak ada transaksi.

## Checklist

- [ ] Grid 30 menit hanya pada 07:00–23:00 WIB, kecuali satu cek pra-buka
- [ ] Alternatif jam atau 2 jam hanya kalau pengguna minta hemat
- [ ] Seen dan watchlist diperbarui
- [ ] `changes.md` kosong dari segi pesan kalau tidak ada selisih
- [ ] Paling banyak 5 kandidat gratis dibahas untuk pratinjau pada putaran ini
- [ ] Batas harian dan cadangan gas dicek
- [ ] Tidak ada auto-mint, tidak ada connect, tidak ada QR
- [ ] Raffle atau klaim yang mendesak disebut terpisah, tidak dicampur dalam satu `confirm`
