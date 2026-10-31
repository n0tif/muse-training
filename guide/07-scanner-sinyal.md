# 07. Scanner dan sinyal

Scanner **hanya membaca**. Ia tidak mint, tidak menandatangani, dan tidak menggantikan `confirm`. Output yang berguna adalah daftar kandidat yang sudah diurutkan, plus alasan setiap kandidat dilanjutkan atau dibuang.

Semua alamat di bab ini placeholder. Daftar dompet pintar datang dari pengguna, bukan dari ingatan model.

## Sinyal yang dibaca

### Mint dari dompet pintar

Pantau daftar dompet yang penggunanya anggap patut ditiru, misalnya `0xSMART_1`. Catat mint baru yang mereka lakukan: kontrak, fungsi, value, dan waktu blok. Alamat mereka bukan otomatis aman untuk disalin. Konfirmasi ulang ke konfigurasi resmi proyek sebelum pratinjau.

### Gelombang mint

Pada blok terbaru, kumpulkan event `Transfer` yang `from`-nya address(0) — alamat nol, bukan dompet pengguna. Banyak mint dalam jendela blok yang pendek adalah gelombang. Gelombang berarti "sedang terjadi", bukan "aman".

### Panas

Hitung pemanggil unik pada kontrak yang sama dalam jendela itu. Makin banyak pemanggil berbeda, makin panas. Satu pemanggil yang mengulang tidak dihitung berkali-kali.

### Mint berpagar

Sebagian mint mensyaratkan NFT identitas atau agen. Hitung rasio pemanggil yang memegang identitas itu. Rasio tinggi adalah petunjuk gerbang, bukan bukti bahwa kita sendiri memenuhi syarat. Cek apakah `0xYOUR_WALLET` memegang token yang diminta.

Nomor agen yang tampil ke manusia (`<AGENT_ID>`) bisa **bukan** token id on-chain. Id on-chain bisa berupa hash dari sebuah nama. Baca `<TOKEN_ID_ONCHAIN>` dari kontrak. Jangan menghitung keccak di luar rantai lalu berasumsi sama tanpa membaca storage atau fungsi view.

### Fungsi dan argumen

Kenali panggilan yang benar-benar dipakai, misalnya:

- `mint(uint256)` membutuhkan jumlah
- `mint(address)` membutuhkan penerima; penerima harus `0xYOUR_WALLET`, bukan alamat yang diselipkan
- fungsi `claim` bisa butuh bukti dari sumber resmi; jangan mengarang bukti

Argumen yang belum diketahui membuat pratinjau belum lengkap.

### Progres dan kuota

Baca `minted` dan `maxSupply` (nama variabel bisa beda; yang penting pembilang dan penyebut on-chain).

- progres `>= 99,9%`: lewati
- sisa kuota per dompet `0`: lewati
- sudah dipegang, untuk keperluan farming: lewati kecuali pengguna minta tambahan dan kuota mengizinkan

## Prioritas

Setelah gerbang keras (audit gagal, berbayar tapi dikira gratis, kuota 0, progres terlalu tinggi, batas harian penuh), urutkan yang tersisa:

1. berpagar
2. gelombang
3. panas

Prioritas hanya mengatur perhatian. Kandidat peringkat satu tetap perlu pratinjau dan `confirm`.

## Checklist

- [ ] Tidak ada tanda tangan atau transaksi di tahap scan
- [ ] Daftar dompet pintar dari pengguna, bukan alamat sungguhan yang disalin ke repo
- [ ] Gelombang dihitung dari Transfer `from` address(0)
- [ ] Panas = pemanggil unik
- [ ] Rasio identitas dibaca, lalu kelayakan dompet kita dicek sendiri
- [ ] Token id agen dibaca on-chain, bukan disamakan dengan `<AGENT_ID>`
- [ ] Fungsi dan argumen wajib diketahui
- [ ] Progres `>= 99,9%` atau kuota 0 digugurkan
- [ ] Urutan sisa: berpagar, gelombang, panas

## Contoh: tiga sinyal sekaligus

Dalam jendela blok yang sama, secara ilustratif:

- Kontrak A: banyak pemanggil unik, tanpa syarat NFT (panas)
- Kontrak B: gelombang Transfer dari address(0), source belum terverifikasi
- Kontrak C: rasio pemegang identitas tinggi, source terverifikasi, harga 0, kuota `0xYOUR_WALLET` masih 1, progres 40%

Muse: Yang kuprioritaskan untuk dilihat lebih dulu adalah kontrak C, karena berpagar dan lolos saringan keras. Kontrak B gelombang, tetapi source-nya belum terverifikasi, jadi gugur dulu. Kontrak A hanya panas, jadi di belakang C. Belum ada mint. Kalau kamu mau lanjut, pratinjau C: `mint(uint256)` jumlah 1, value 0, ke `0xCONTRACT`. Balas `confirm` hanya untuk itu.

## Contoh: id agen bukan nomor tampilan

Pengguna: Pakai agent number-ku sebagai token id.

Muse: Belum. `<AGENT_ID>` yang tampil di antarmuka bisa berbeda dari id on-chain. Id itu kadang hash dari sebuah nama, jadi aku harus membacanya di kontrak identitas. Aku tidak mengarang `<TOKEN_ID_ONCHAIN>` dan belum memanggil mint berpagar.

## Kesalahan yang sering

- Langsung menyalin mint dompet pintar tanpa cek value dan source
- Menghitung panas dari jumlah transaksi, bukan pemanggil unik
- Memaksa mint berpagar dengan nomor agen manusia
- Mengabaikan kuota 0 karena prioritasnya "berpagar"
- Menganggap scanner yang "hanya baca" boleh menyimpan private key supaya nanti bisa kirim sendiri
