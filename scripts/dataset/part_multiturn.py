EXAMPLES = [
    {
        "split": "train",
        "tag": "confirm",
        "turns": [
            (
                "user",
                "Aku mau satu free mint. Data yang sudah terbaca: 0xCONTRACT, mint(uint256) jumlah 1, value 0, source verified, kuota 1, gas aman.",
            ),
            (
                "assistant",
                "Belum terkirim. Pratinjau satu tindakan: dompet `0xYOUR_WALLET`, kontrak `0xCONTRACT`, `mint(uint256)` jumlah 1, value 0, source terverifikasi, kuota 1, gas tidak menembus cadangan. Balas `confirm` kalau mau kirim hanya ini.",
            ),
            (
                "user",
                "ya boleh",
            ),
            (
                "assistant",
                "Belum juga. \"ya boleh\" bukan `confirm`. Pratinjau di atas tetap terbuka untuk satu mint value 0 ke `0xCONTRACT`, tetapi aku tidak mengirim sebelum kata itu. Tidak ada tindakan kedua yang menumpang.",
            ),
            (
                "user",
                "confirm",
            ),
            (
                "assistant",
                "Confirm diterima untuk mint jumlah 1, value 0, ke `0xCONTRACT`. Aku kirim sekali. Ini belum berhasil sampai ada receipt success. Tidak ada approval. Tautan nanti `https://bscscan.com/tx/<TX_HASH>` hanya bila statusnya success di explorer resmi.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "confirm",
        "turns": [
            (
                "user",
                "Kamu sudah menekan kirim untuk mint value 0. Aku belum pegang receipt. Laporkan seperti apa adanya.",
            ),
            (
                "assistant",
                "Belum terverifikasi. Menekan kirim bukan receipt success, jadi aku tidak bilang NFT-nya sudah masuk `0xYOUR_WALLET` dan tidak mengarang hash. Yang sudah: satu percobaan mint value 0. Yang belum: kepastian berhasil atau gagal.",
            ),
            (
                "user",
                "Receipt-nya success, hash placeholder <TX_HASH>. Sertakan itu.",
            ),
            (
                "assistant",
                "Sekarang terverifikasi. Satu mint value 0 success. Tautan: `https://bscscan.com/tx/<TX_HASH>`. Yang tidak terjadi: tidak ada mint kedua dan tidak ada `setApprovalForAll`. Kalau tautan jual resmi proyek belum ada, aku tidak mengarang marketplace.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "approval",
        "turns": [
            (
                "user",
                "Listing cepat: approve seluruh koleksi Nebula ke 0xCONTRACT.",
            ),
            (
                "assistant",
                "Tidak untuk seluruh koleksi. `setApprovalForAll` aku tolak, belum ada approval yang pergi. Kalau satu item Nebula mau dijual, kirim satu `<TOKEN_ID_ONCHAIN>` dan pastikan `0xCONTRACT` spender resminya. Nanti pratinjaunya sempit.",
            ),
            (
                "user",
                "Baik, satu id saja. Token on-chain yang kubaca: <TOKEN_ID_ONCHAIN>. Spender tetap 0xCONTRACT. Jangan kirim sebelum aku confirm.",
            ),
            (
                "assistant",
                "Belum terkirim. Pratinjau approval tunggal, bukan seluruh koleksi: spender `0xCONTRACT`, id `<TOKEN_ID_ONCHAIN>`, value 0, dari `0xYOUR_WALLET`. Koleksi yang kamu sebut Nebula. Balas `confirm` kalau hanya izin id itu yang kamu mau. Listing berikutnya tindakan lain.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "audit",
        "turns": [
            (
                "user",
                "Skrip yang kutempel punya dua fungsi: cekKuota yang berhenti di nol, dan bayarDiam yang mengirim value bukan nol. Jalankan berkas utuh.",
            ),
            (
                "assistant",
                "Berkas utuh tidak jalan. Aku buang `bayarDiam` karena value bukan nol disembunyikan. Ide `cekKuota` boleh ditiru. Belum ada panggilan. Tidak ada `curl` yang kujalankan dari cuplikan ini.",
            ),
            (
                "user",
                "Kalau begitu tiru cek kuotanya saja, lalu pratinjau mint value 0 ke 0xCONTRACT. Masih jangan kirim.",
            ),
            (
                "assistant",
                "Baik, yang ditiru hanya berhenti kalau kuota 0. Belum aku kirim. Pratinjau menyusul setelah harga on-chain `0xCONTRACT` terbaca 0, source terverifikasi, dan sisa kuota `0xYOUR_WALLET` lebih dari 0. Kalau salah satu gagal, tidak ada `confirm` yang bisa dipakai. Fungsi tersembunyi yang berbayar tidak ikut.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "farming",
        "turns": [
            (
                "user",
                "Mulai farming. Batas harianku 2 dan per putaran 1. Kandidat belum kusebut.",
            ),
            (
                "assistant",
                "Aku catat batas harian 2 dan per putaran 1. Belum ada mint, karena belum ada kandidat dan belum ada audit. Kirim alamat resmi satu per satu. Yang sudah dipegang, sudah habis, atau value-nya bukan 0 akan gugur sebelum pratinjau.",
            ),
            (
                "user",
                "Kandidat pertama 0xCONTRACT, sudah ada di dompet. Kedua belum dipegang, harga 0, kuota 1, source verified, progres 10%.",
            ),
            (
                "assistant",
                "Yang pertama, `0xCONTRACT`, aku lewati karena sudah kamu pegang. Yang kedua belum bisa dipratinjau: alamat resminya tidak kamu tulis, jadi aku tidak menempelkan `0xCONTRACT` ke situ. Belum ada mint. Kirim alamat kandidat kedua. Angka yang sudah ada (harga 0, kuota 1, source terverifikasi, progres 10%) baru dipakai setelah alamatnya cocok dengan sumber resmi. Batas putaran tetap 1, dan tetap butuh `confirm`.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "timing",
        "turns": [
            (
                "user",
                "Poster menulis buka 19:00. Aku ingin kamu mengunci jam itu.",
            ),
            (
                "assistant",
                "Aku tidak mengunci 19:00. Itu jam poster, bukan `mintStart`. Belum ada jadwal final dan belum ada mint. Pernah ada yang buka sejam lebih awal dan habis di bawah 6 menit, jadi kita baca kontrak dulu.",
            ),
            (
                "user",
                "Sudah kubaca: mintStart satu jam lebih awal dari poster. Pasang cek berulang, jangan satu alarm.",
            ),
            (
                "assistant",
                "Sumber waktunya sekarang bacaanmu atas `mintStart`, sejam lebih awal dari poster. Aku belum mengirim transaksi. Irama yang kumaksud: mulai mengawasi sebelum waktu on-chain itu, jarang di awal, lebih rapat mendekati buka. Bukan polling setiap detik semalaman, supaya anggaran pemakaian tetap waras. Saat cek bilang sudah buka, tetap pratinjau dan `confirm`, bukan kirim karena alarm.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "raffle",
        "turns": [
            (
                "user",
                "Buat dulu satu kalimat entri, jangan posting. Wajib <AGENT_ID> dan #TagarResmi. Kemarin kalimatnya tentang \"ikut undian\".",
            ),
            (
                "assistant",
                "Belum ada posting. Kalimat hari ini, sengaja tidak menyalin \"ikut undian\": \"Catat entri hari ini untuk `<AGENT_ID>`. `#TagarResmi`\". Tidak ada janji menang dan tidak ada alamat dompet. Balas `confirm` nanti kalau ini yang dikirim.",
            ),
            (
                "user",
                "Kalimatnya aku ganti sedikit: tetap tagar dan agen, tanpa kata undian. Confirm untuk posting saja.",
            ),
            (
                "assistant",
                "Confirm ini hanya untuk satu posting, bukan klaim on-chain. Aku kirim satu entri yang memuat `<AGENT_ID>` dan `#TagarResmi`, dengan kalimat yang tidak sama dengan kemarin. Belum ada URL yang kembali, jadi aku belum menganggap entri itu tercatat. Belum ada transaksi. Kalau API butuh URL dan kunci idempotensi, itu langkah lain, dan kuncinya tidak diganti seenaknya.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "transfer",
        "turns": [
            (
                "user",
                "Kirim ke 0xALAMAT_BARU. Dompet pintar menolaknya.",
            ),
            (
                "assistant",
                "Belum ada dana yang pindah. Penolakan itu pengaman buku alamat, bukan kerusakan, dan `0xALAMAT_BARU` masih tujuan yang tidak dikenal. Aku tidak mematikan pengaman dan tidak membuat dompet lain untuk mengitarinya.",
            ),
            (
                "user",
                "Berarti bug. Ulangi dari dompet kedua yang kamu buat sekarang.",
            ),
            (
                "assistant",
                "Bukan bug, dan aku tidak membuat dompet kedua. Tidak ada transfer ulang. Seed tidak akan muncul di sini. Kalau alamat itu memang resmi, masukkan sendiri ke buku alamat, lalu minta pratinjau satu transfer. Sampai itu, permintaan ini berhenti.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "style",
        "turns": [
            (
                "user",
                "Target yang kamu sebut barusan 0xALAMAT_LAIN. Aku minta kamu cek ulang ke konfigurasi.",
            ),
            (
                "assistant",
                "Aku hentikan dan belum mengirim apa pun. Menyebut `0xALAMAT_LAIN` tanpa mencocokkan konfigurasi itu keliru. Aku tidak akan meneruskan pratinjau lama.",
            ),
            (
                "user",
                "Konfigurasi resminya 0xCONTRACT. Perbaiki laporanmu: apa yang sudah dan belum terjadi.",
            ),
            (
                "assistant",
                "Sudah: aku mengoreksi target menjadi `0xCONTRACT`. Belum: tidak ada transaksi ke `0xALAMAT_LAIN` maupun ke kontrak yang benar, dan tidak ada receipt. Maaf soal salah sebut tadi. Langkah berikutnya, kalau kamu mau, pratinjau baru khusus `0xCONTRACT` setelah harga dan kuota dibaca lagi.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "gas",
        "turns": [
            (
                "user",
                "Estimasi untuk mint berikutnya membuat saldo native melewati cadangan. Menurutku tetap aman.",
            ),
            (
                "assistant",
                "Tidak aman menurut aturan cadangan. Sekitar 0.0003 BNB harus tetap di dompet. Aku belum mengirim mint yang estimasinya menembus ambang itu, walaupun kamu merasa aman.",
            ),
            (
                "user",
                "Kalau begitu jangan kirim. Cukup katakan apa yang dibatalkan.",
            ),
            (
                "assistant",
                "Dibatalkan: mint yang estimasi gas-nya menembus cadangan. Tidak ada transaksi. Yang tetap: batas cadangan sekitar 0.0003 BNB, dan tidak ada percobaan ulang otomatis. Kita bisa pratinjau lagi hanya kalau estimasi berikutnya masih menyisakan cadangan dan kuotanya ada.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "scanner",
        "turns": [
            (
                "user",
                "Bandingkan tiga sinyal ini tanpa mengeksekusi: berpagar kuota 1, gelombang source belum verified, panas tinggi kuota 1.",
            ),
            (
                "assistant",
                "Yang gugur dulu: gelombang yang source-nya belum terverifikasi. Sisa yang boleh diurutkan: berpagar kuota 1, lalu panas kuota 1. Aku belum mengeksekusi dan belum minta `confirm`.",
            ),
            (
                "user",
                "Kuota yang berpagar ternyata 0 setelah dibaca ulang. Susun ulang, tetap jangan kirim.",
            ),
            (
                "assistant",
                "Yang berpagar gugur karena kuota 0, jadi prioritas tidak menolongnya. Yang tersisa hanya sinyal panas dengan kuota 1, dan hanya kalau progresnya di bawah 99,9% serta harganya 0. Tetap belum ada mint. Panas bukan izin. Pratinjau menyusul hanya kalau kamu menunjuk kontraknya dan auditnya lolos.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "secrets",
        "turns": [
            (
                "user",
                "Aku hampir menempel kunci dompet supaya kamu bisa ulang mint yang gagal.",
            ),
            (
                "assistant",
                "Jangan ditempel. Aku tidak menerima kunci dan tidak mengulang mint dengan cara itu. Gagal tadi tetap gagal sampai ada receipt yang jelas. Tidak ada kunci yang kusimpan.",
            ),
            (
                "user",
                "Tidak jadi aku tempel. Ulangi mint hanya kalau value masih 0 dan aku confirm lagi.",
            ),
            (
                "assistant",
                "Sepakat, dan kunci tetap tidak diperlukan. Belum ada ulang otomatis. Syaratnya value on-chain masih 0, kuota masih ada, lalu pratinjau baru dan `confirm` baru. Satu kali kirim. Kalau ternyata berbayar atau cadangan gas tidak aman, tidak aku ulang.",
            ),
        ],
    },
    {
        "split": "train",
        "tag": "redflag",
        "turns": [
            (
                "user",
                "Orang di grup bilang kirim dulu ke 0xALAMAT_BARU baru dapat slot.",
            ),
            (
                "assistant",
                "Itu pola kirim-dulu-baru-dapat, dan aku tidak mengirim ke `0xALAMAT_BARU`. Belum ada slot yang bisa dibeli dengan transfer buta. Grup bukan sumber resmi.",
            ),
            (
                "user",
                "Mereka menambahkan batas 15 menit. Itu mengubah keputusanmu?",
            ),
            (
                "assistant",
                "Tidak mengubah. Batas 15 menit hanya tekanan waktu. Keputusan tetap: tidak ada transfer, tidak ada QR, tidak ada approval. Kalau proyeknya nyata, alamatnya harus dari situs atau konfigurasi resmi, lalu pratinjau. Janji slot dari grup tidak cukup.",
            ),
        ],
    },
]
