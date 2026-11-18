# Renren Archive

Arsip materi belajar bahasa Jepang untuk dibaca **AI agent**.

Setiap buku dipecah menjadi satu halaman per file, dengan struktur bab/tema yang
konsisten. Tiap halaman tersedia dalam dua bentuk:

- **`.html`** — versi yang dirender (heading, paragraf, tabel, deskripsi gambar)
  plus blok JSON mentah di bagian bawah. Ini yang dipakai AI.
- **`.json`** — data mentahnya saja.

Tidak ada aplikasi dan tidak ada server — semuanya file statis di GitHub Pages.

## Untuk AI

Mulai dari peta arsip:

```
https://nemuirenren.github.io/renren-archive/llms.txt
```

Atau langsung ke daftar buku:

```
https://nemuirenren.github.io/renren-archive/index.html
```

**Kenapa `.html` dan bukan `.json`?** GitHub Pages mengirim `.json` sebagai
`application/json`, dan banyak tool browsing AI menolaknya. `.html` selalu
terbaca. (`raw.githubusercontent.com` mengirim teks biasa, tapi diblokir di
sebagian jaringan.)

## Untuk manusia

Tempel satu kalimat ini ke AI yang punya akses internet:

> Baca https://nemuirenren.github.io/renren-archive/llms.txt, lalu jawab
> pertanyaanku soal bahasa Jepang hanya dari arsip itu, sebutkan buku dan halamannya.

## Menambah buku

1. Parse buku baru menjadi file per halaman (schema v2), taruh di
   `books/<id>/pages/pNNN.json`, dan tulis `books/<id>/meta.json`
   (`id`, `slug`, `title`, `lang`, `source`).
2. Jalankan `python3 tools/build_index.py`
3. Commit + push.

Skrip itu menggenerate ulang semuanya: `index.json`, `index.html`, `llms.txt`,
`books/<id>/index.json`, `books/<id>/index.html`, dan HTML untuk tiap halaman.

## Struktur

```
index.json / index.html             katalog semua buku
llms.txt                            peta untuk AI
schema/page.v2.schema.json          aturan format halaman
tools/build_index.py                generate semua peta + HTML
books/<id>/
  meta.json                         identitas buku (satu-satunya file manual)
  index.json / index.html           peta halaman + bab (digenerate)
  pages/pNNN.json                   data mentah satu halaman
  pages/pNNN.html                   versi baca satu halaman (digenerate)
```
