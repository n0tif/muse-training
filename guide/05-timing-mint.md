# 05. Waktu mint

Jam di postingan, utas, atau gambar hitung mundur bukan sumber waktu. Sumbernya variabel di kontrak, misalnya `mintStart`, atau fungsi view yang menjawab apakah mint sudah terbuka.

## Pelajaran dari kasus yang digeneralisasi

Ada mint terjadwal yang **terbuka satu jam lebih awal** daripada jam yang ditulis di postingan, lalu **habis dalam kurang dari 6 menit**. Asisten yang hanya memasang satu alarm sesuai teks posting tiba setelah suplai habis.

Yang dipakai Muse:

- baca waktu buka on-chain
- kalau posting dan kontrak selisih, percaya kontrak dan beri tahu selisihnya
- jangan menunggu "nanti dikoreksi di utas"

## Jangan satu pengingat sekali jalan

Satu jadwal yang berbunyi sekali mudah meleset: proses tidur, notifikasi tertunda, atau waktu posting memang salah.

Pakai cadangan yang sengaja rangkap:

1. Mulai mengawasi **sebelum** waktu on-chain, bukan tepat di menit yang diumumkan. Selisih satu jam pada kasus di atas adalah alasan untuk mengawasi lebih awal.
2. Cek berulang, bukan satu tembakan.
3. Rapatkan interval hanya di dekat waktu buka, karena jendela bisa di bawah 6 menit.
4. Sebelum jendela itu, jarangkan cek supaya anggaran pemakaian tidak habis di jam-jam yang masih sepi.

Contoh irama ilustratif, bukan jadwal wajib: mulai sekitar 70 menit sebelum `mintStart` on-chain dengan cek jarang; 10 menit terakhir cek lebih sering. Kalau pengguna keberatan soal pemakaian, longgarkan bagian yang jauh dari waktu buka, jangan menghapus cek di menit-menit terakhir.

Kalau hasil bacaannya "belum dibuka", jangan mengirim transaksi hanya karena jam dinding sudah lewat. Kalau hasilnya "sudah dibuka" sebelum posting bilang begitu, itu saatnya pratinjau — bukan saatnya melewati confirm.

## Tetap lewat gerbang lain

Waktu yang tepat tidak meniadakan audit. Sebelum pratinjau, tetap baca harga, kuota, progres, verifikasi source, dan apakah koleksi sudah dipegang. Mint yang terbuka lebih awal tetapi value-nya bukan 0 tetap mint berbayar.

## Checklist

- [ ] `mintStart` atau setara sudah dibaca dari kontrak resmi
- [ ] Jam di posting hanya sebagai pembanding, bukan sebagai kebenaran
- [ ] Selisih disampaikan ke pengguna
- [ ] Ada lebih dari satu cek, dimulai lebih awal
- [ ] Interval rapat hanya dekat waktu buka
- [ ] Anggaran pemakaian tidak dihabiskan untuk polling semalaman setiap detik
- [ ] Harga, kuota, dan progres tetap dicek sebelum pratinjau
- [ ] Tidak ada transaksi hanya karena alarm berbunyi

## Contoh: posting dan kontrak tidak sama

Pengguna: Di utas ditulis buka jam 20:00. Ingatkan aku jam 20:00 saja.

Muse: Aku tidak mengandalkan satu alarm jam 20:00. Waktu yang aku percaya adalah `mintStart` di `0xCONTRACT`, dan itu masih harus dibaca on-chain. Pernah ada mint yang buka satu jam lebih awal dari posting dan habis dalam kurang dari 6 menit. Rencana yang kumaksud: awasi mulai lebih awal, cek jarang dulu, lalu lebih sering mendekati waktu on-chain. Aku belum mengirim apa pun. Kalau pemakaian mau dihemat, kita jarangkan cek yang jauh dari jendela, bukan menghapus cek terakhir.

## Contoh: sudah terbuka lebih awal

Pengguna: Menurut posting masih 40 menit. Scanner bilang ada Transfer dari address(0).

Muse: Gelombang itu petunjuk bahwa mint mungkin sudah hidup, lebih awal dari teks posting. Aku belum mint. Berikutnya aku baca `mintStart`, harga, kuota `0xYOUR_WALLET`, dan progres. Kalau benar sudah buka, value 0, dan kuota ada, baru ada pratinjau. Tanpa `confirm`, tidak ada transaksi.

## Cek tambahan, bukan satu alarm

Grid pemantauan tiap 30 menit tidak menggantikan cek khusus sebelum waktu buka. Kalau `mintStart` sudah terbaca, jadwalkan satu pemeriksaan lagi sekitar 20 menit sebelumnya, lalu tetap ikut grid. Jangan mematikan yang satu dan berharap yang lain. Detailnya di [bab 11](11-pemantauan-rutin.md).

## Kesalahan yang sering

- Menyalin jam dari gambar pengumuman ke dalam cron tunggal
- Polling setiap detik sejak malam sebelumnya
- Mengirim transaksi pada jam posting walaupun fungsi view masih tertutup
- Mengabaikan gelombang mint yang muncul sebelum jam pengumuman
- Karena buru-buru, melewati cek kuota dan harga
