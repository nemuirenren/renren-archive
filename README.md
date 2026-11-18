# Renren Archive

Arsip materi belajar bahasa Jepang untuk dibaca **AI agent**.

Setiap buku dipecah menjadi satu file JSON per halaman, dengan struktur bab/tema
yang konsisten. Tidak ada aplikasi, tidak ada server — semuanya file statis yang
bisa diambil lewat URL biasa.

## Untuk AI

Mulai dari:

```
https://nemuirenren.github.io/renren-archive/llms.txt
```

File itu berisi peta seluruh arsip: buku apa saja yang tersedia, cara
menavigasinya, dan format datanya.

## Untuk manusia

Tempel satu kalimat ini ke AI yang punya akses internet:

> Baca https://nemuirenren.github.io/renren-archive/llms.txt, lalu jawab
> pertanyaanku soal bahasa Jepang hanya dari arsip itu, sebutkan buku dan halamannya.

## Menambah buku

1. Parse buku baru menjadi file per halaman (schema v2), taruh di
   `books/<id>/pages/pNNN.json`, dan tulis `books/<id>/meta.json`
   (`id`, `slug`, `title`, `lang`, `source`).
2. Jalankan `python3 tools/build_index.py`
3. Commit + push. `index.json` dan `llms.txt` ikut ter-update otomatis.

## Struktur

```
index.json                 katalog semua buku
llms.txt                   peta untuk AI
schema/page.v2.schema.json aturan format halaman
tools/build_index.py       generate semua peta dari books/*/meta.json
books/<id>/
  meta.json                identitas buku (satu-satunya file manual)
  index.json               peta halaman + bab (digenerate)
  pages/pNNN.json          satu halaman
```
