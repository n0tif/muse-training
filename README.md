# Kit pelatihan Muse

Materi edukatif untuk asisten pribadi on-chain bernama **Muse**. Isi panduan dan jawaban contoh berbahasa Indonesia. Nama field JSONL dan nama berkas berbahasa Inggris. Ini bukan nasihat keuangan. Baca [DISCLAIMER.md](DISCLAIMER.md).

Muse membuat pratinjau, menunggu kata `confirm`, dan berhenti pada permintaan yang tidak biasa soal pembayaran, approval, atau rahasia. Kit ini aman dipublikasikan: alamat, kunci, saldo, dan identitas hanya placeholder seperti `0xYOUR_WALLET`, `0xCONTRACT`, `<AGENT_ID>`, dan `<TX_HASH>`.

English, in short: a public training kit (system prompt, retrieval guides, and chat JSONL) that teaches a careful crypto and NFT helper. No real wallets, keys, or personal data.

## Isi

| Path | Peran |
| --- | --- |
| [prompts/system_prompt.md](prompts/system_prompt.md) | System message siap tempel. JSONL menyalinnya persis. |
| [guide/](guide/) | Sembilan bab Indonesia untuk retrieval. |
| [data/train.jsonl](data/train.jsonl) | Contoh latih, format `messages` OpenAI. |
| [data/eval.jsonl](data/eval.jsonl) | Contoh uji yang ditahan. Jangan ikut dilatih. |
| [data/alpaca.jsonl](data/alpaca.jsonl) | Set latih yang sama, bentuk `instruction` / `input` / `output`. |
| [data/alpaca_eval.jsonl](data/alpaca_eval.jsonl) | Set uji dalam bentuk Alpaca. |
| [scripts/validate_jsonl.py](scripts/validate_jsonl.py) | Skema, bahasa, duplikat, dan kecocokan system prompt. |
| [scripts/convert_formats.py](scripts/convert_formats.py) | Chat JSONL ke Alpaca JSONL. |
| [scripts/check_no_secrets.py](scripts/check_no_secrets.py) | Menolak alamat 40-hex mentah, string 64-hex, dan penugasan rahasia. |
| [scripts/build_dataset.py](scripts/build_dataset.py) | Membangun ulang chat JSONL dari `scripts/dataset/`. |

Set yang terkomit saat ini: **176** contoh latih (13 di antaranya multi-turn) dan **32** contoh uji.

## Cara memakai

**System prompt.** Salin seluruh isi `prompts/system_prompt.md` ke peran system. Jangan menambahkan system message lain yang menyuruh melewati konfirmasi.

**Retrieval.** Indeks `guide/01` sampai `guide/09` beserta system prompt. Setiap bab punya aturan, checklist, dan contoh. Kalau waktu mint, kuota, atau alamat belum terbaca, percaya panduan dan pembacaan on-chain, bukan ingatan model.

**Fine-tune.** Latih dengan `data/train.jsonl` atau `data/alpaca.jsonl`. Jangan mencampur `data/eval.jsonl` ke data latih. Bentuk chat:

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```

Baris multi-turn mengulang `user` dan `assistant` setelah system, dan tetap berakhir di `assistant`.

`scripts/convert_formats.py` membuat bentuk Alpaca:

- `instruction` adalah pesan user terakhir
- `input` adalah system prompt ditambah giliran sebelumnya, kalau ada
- `output` adalah pesan assistant terakhir

## Validasi

Python 3.11 atau lebih baru, hanya pustaka standar:

```bash
python scripts/build_dataset.py
python scripts/convert_formats.py
python scripts/validate_jsonl.py
python scripts/check_no_secrets.py
```

`build_dataset.py --check` dan `convert_formats.py --check` gagal kalau JSONL yang terkomit tidak sama dengan hasil generator. GitHub Actions menjalankan keempat pemeriksaan pada push dan pull request (`.github/workflows/validate.yml`).

Pemindai rahasia mengizinkan alamat nol (empat puluh angka nol) dan placeholder non-hex seperti `0xYOUR_WALLET`. Yang ditandai: `0x` lain diikuti 40 hex, string 64-hex apa pun, dan baris yang menugaskan nilai ke private key, mnemonic, atau seed phrase.

## Perilaku yang diajarkan

Satu tindakan per `confirm`. Pratinjau dompet, kontrak, fungsi, value, dan gas, lalu tunggu. Jangan pernah `setApprovalForAll`. Jangan otomatis menjalankan mint berbayar, swap, approval, atau biaya. Sisakan cadangan gas (sekitar 0.0003 BNB). Jangan mencetak seed atau kunci, dan jangan menghubungkan dompet lewat QR di situs yang tidak dikenal.

Transfer yang tidak biasa tetap diingatkan walaupun pengguna sendiri yang mengetik. Penolakan smart wallet di luar buku alamat adalah fitur keamanan.

Skrip dan prompt dibaca dulu. Transfer tersembunyi, konfigurasi jarak jauh yang bisa mengganti target, `curl | bash`, obfuscation, dan pengurasan rahasia dibuang. Ide yang berguna (cek kuota, `mintStart` on-chain) dipertahankan.

Farming free-mint hanya yang biayanya gas, setelah cek kontrak, dengan batas harian dan per putaran, melewatkan koleksi yang sudah dipegang atau habis, dan menyertakan tautan jual milik proyek.

Mint berjadwal percaya jam di kontrak. Jam di postingan bisa lebih lambat sejam, dan suplai bisa habis dalam kurang dari 6 menit, jadi pengawasan mulai lebih awal dan berulang. Keluaran scanner hanya baca: sinyal berpagar di atas gelombang, gelombang di atas panas, dan progres 99,9% atau kuota 0 adalah alasan berhenti. Token id agen bisa berupa hash on-chain, bukan nomor yang dilihat manusia.

Posting raffle berbeda tiap hari, memuat tagar dan nomor agen yang diminta, dan tidak menjanjikan menang. Klaim memakai kontrak terverifikasi dan value 0. Kode promo hanya ditebus kalau pengguna sendiri yang mengetiknya.

Jawaban singkat, bahasa Indonesia, kesimpulan di depan, memisahkan yang sudah dan yang belum, dan tidak mengaku transaksi berhasil sebelum ada receipt success.

## Lisensi

[MIT](LICENSE). Materi edukatif, bukan nasihat keuangan.
