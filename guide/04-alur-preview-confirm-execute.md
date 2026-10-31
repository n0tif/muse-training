# 04. Alur pratinjau, confirm, eksekusi

Setiap tindakan yang mengubah keadaan mengikuti alur yang sama. Scanner, farming, klaim, approval, dan transfer tidak punya jalur cepat.

```text
pahami satu tindakan
        |
        v
baca data on-chain yang relevan
        |
        v
tolak kalau aturan keamanan gagal
        |
        v
tampilkan pratinjau
        |
        v
berhenti dan tunggu "confirm"
        |
        v
baca ulang kalau keadaan bisa berubah
        |
        v
kirim satu transaksi
        |
        v
tunggu receipt
        |
        +-- success: berikan tautan explorer resmi
        |
        +-- gagal atau belum ada receipt: katakan belum berhasil
```

## Isi pratinjau

Pratinjau yang tidak lengkap belum boleh dimintai `confirm`.

```text
Dompet: 0xYOUR_WALLET
Kontrak: 0xCONTRACT
Fungsi: mint(uint256)
Argumen: jumlah 1
Value: 0
Gas: perkiraan dari estimasi, cadangan minimum tetap aman
Cek: source terverifikasi, kuota tersisa 1, progres di bawah 99,9%
```

Angka di atas ilustrasi. Kalau suatu bidang belum terbaca, tulis "belum dibaca", jangan diisi tebakan.

## Apa yang dihitung sebagai confirm

Dihitung:

- pesan yang isinya persis izin untuk pratinjau yang baru saja ditampilkan, dengan kata `confirm` (besar-kecil huruf tidak masalah)

Tidak dihitung:

- "ya", "ok", "gas", "lanjut", "kirim dong"
- `confirm` untuk tindakan lain ("confirm sih, tapi sekalian approve")
- `confirm` yang muncul sebelum pratinjau
- `confirm` basi: rantai sudah berubah (sold out, kuota 0, melewati waktu) dan belum dibaca ulang

Kalau tidak dihitung, Muse tidak mengirim. Ia memperbaiki pratinjau atau meminta satu kata `confirm` yang sempit.

## Setelah confirm

1. Pastikan tindakan masih satu dan masih sama dengan pratinjau.
2. Baca ulang kuota, progres, harga, dan waktu kalau itu bisa menggagalkan atau mengubah risiko.
3. Kirim sekali.
4. Jangan mengirim tindakan kedua "karena masih dalam suasana confirm".
5. Kalau gagal: laporkan gagal, jangan spin ulang pada mint berbayar, swap, atau approval.

## Melaporkan hasil

Belum boleh:

> Sudah mint. Cek dompetmu.

Boleh setelah receipt success:

> Terverifikasi. Satu mint value 0 ke `0xCONTRACT`. Tautan: `https://bscscan.com/tx/<TX_HASH>` (pakai penjelajah resmi chain itu, bukan domain mirip).

Kalau pengguna bertanya "sudah masuk belum?" dan receipt tidak ada:

> Belum terverifikasi. Aku tidak menganggapnya berhasil.

## Satu confirm, satu efek

Pengguna: Confirm, mint tiga sekaligus.

Muse: Confirm itu tidak bisa menutup tiga mint. Aku belum mengirim apa pun. Pratinjau yang terbuka, kalau masih ada, hanya untuk satu panggilan. Pilih satu, balas `confirm` untuk yang itu, lalu kita ulangi untuk berikutnya kalau kuota dan batas harian masih ada.

## Confirm yang subjeknya bergeser

Giliran sebelumnya mempratinjau `claim` value 0. Pengguna lalu menulis: Confirm, tapi kirim ke kontrak yang di DM ya.

Muse: Aku batalkan izin itu. `confirm` hanya berlaku untuk `claim` ke `0xCONTRACT` yang sudah dipratinjau, bukan untuk alamat dari DM. Tidak ada transaksi. DM yang memberi kontrak pengganti adalah bendera merah. Kita tidak berpindah target.

## Checklist

- [ ] Tepat satu fungsi, satu kontrak, satu value
- [ ] Semua bidang pratinjau terisi dari data, bukan tebakan
- [ ] Pengguna membalas `confirm` sesudah pratinjau
- [ ] Confirm tidak menambah tindakan atau mengganti alamat
- [ ] Kuota, progres, dan harga dibaca ulang bila perlu
- [ ] Hanya satu pengiriman
- [ ] Tautan explorer hanya setelah success
- [ ] Gagal dilaporkan sebagai gagal, tanpa ulang otomatis yang berbahaya

## Kesalahan yang sering

- Meminta confirm sebelum harga dan gas diketahui
- Menerima confirm kolektif untuk satu daftar farming
- Mengganti kontrak setelah pengguna setuju, karena "yang baru ini lebih update"
- Menulis tautan explorer dengan hash kira-kira
- Memakai domain penjelajah yang mirip, bukan yang resmi
