# Pemindai baca-saja

Alat ini membaca posting dan kontrak. Ia tidak menandatangani, tidak menyimpan kunci, dan tidak mengirim transaksi.

Akun X yang login di browser Muse hanya dipakai untuk membaca. Salin posting ke berkas, lalu jalankan mode `--input`. Token API bersifat opsional dan hanya dari environment.

## Pasang

```bash
python -m pip install -r scanner/requirements.txt
```

## Dua sumber posting

API, kalau `X_BEARER_TOKEN` ada:

```bash
python -m scanner scan --config scanner/config.example.yaml
```

Berkas dari browser, tanpa token:

```bash
python -m scanner scan --config scanner/config.example.yaml --input scanner/examples/posts.example.json --out out
```

`posts.json` berbentuk `{"posts":[{"id","text","url","author","followers"}]}`. Berkas teks biasa juga diterima: satu posting per blok yang dipisah baris kosong.

## Pantau

```bash
python -m scanner monitor --config scanner/config.example.yaml --input posts.json --out out/changes.md
```

Bawaan irama yang didokumentasikan: tiap 30 menit, 07:00–23:00 WIB (`*/30 7-23 * * *`). Alat ini tidak menjadwalkan dirinya. Penjadwal Muse yang menjalankannya. Kalau tidak ada selisih, `out/changes.md` hanya berisi kalimat supaya tidak ada pesan yang dikirim.

Batas per putaran bawaan: 5. Batas harian tetap harus diisi pengguna di `farming.daily_cap`. RPC utama bisa ditimpa `BSC_RPC_URL`, cadangan lewat `BSC_RPC_FALLBACK_URL`.

`state/` dan `out/` tidak di-commit. Jangan menaruh token di YAML.

## Tes

```bash
python -m pytest scanner/tests -q
```

Tes memakai respons palsu. Tidak ada jaringan.
