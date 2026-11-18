#!/usr/bin/env python3
"""Regenerate root index.json, per-book index.json, and llms.txt.

Run after adding or changing anything under books/<id>/.

    python3 tools/build_index.py

A book is a folder books/<id>/ containing:
    meta.json     hand-written: id, slug, title, lang, source
    pages/pNNN.json   one file per page, schema v2
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "books")
BASE_URL = "https://nemuirenren.github.io/renren-archive"
SCHEMA_VERSION = "2.0"


def book_dirs():
    out = []
    for d in sorted(os.listdir(BOOKS)):
        p = os.path.join(BOOKS, d)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "meta.json")):
            out.append(d)
    return out


def load_pages(book_dir):
    pages = []
    for f in sorted(glob.glob(os.path.join(book_dir, "pages", "p[0-9]*.json"))):
        d = json.load(open(f))
        first_heading = ""
        for b in d.get("blocks", []):
            if b.get("type") == "heading":
                first_heading = b["text"]
                break
        pages.append({
            "page": d["page"],
            "page_label": d.get("page_label", ""),
            "kind": d.get("kind", ""),
            "outline": [o["title"] for o in d.get("outline", [])],
            "first_heading": first_heading,
        })
    pages.sort(key=lambda p: p["page"])
    return pages


def build_book_index(book_id, meta, pages):
    ranges = {}
    order = []
    for p in pages:
        top = p["outline"][0] if p["outline"] else ""
        if not top:
            continue
        if top not in ranges:
            ranges[top] = [p["page"], p["page"]]
            order.append(top)
        else:
            ranges[top][1] = p["page"]

    index = {
        "id": book_id,
        "title": meta["title"],
        "lang": meta["lang"],
        "pages": len(pages),
        "outline": [{"level": 1, "title": t, "pages": ranges[t]} for t in order],
        "items": pages,
    }
    with open(os.path.join(BOOKS, book_id, "index.json"), "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    return index


def write_root_index(books):
    index = {
        "schema_version": SCHEMA_VERSION,
        "books": [
            {
                "id": b["id"],
                "slug": b["meta"].get("slug", ""),
                "title": b["meta"]["title"],
                "lang": b["meta"]["lang"],
                "pages": b["index"]["pages"],
                "source": b["meta"].get("source", ""),
                "path": f"books/{b['id']}/",
                "index": f"books/{b['id']}/index.json",
            }
            for b in books
        ],
    }
    with open(os.path.join(ROOT, "index.json"), "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index


def write_llms(books):
    lines = [
        "# Renren Archive",
        "",
        "> Arsip materi belajar bahasa Jepang. Setiap buku dipecah per halaman",
        "> dalam bentuk JSON, dengan peta bab/tema yang konsisten.",
        "",
        "Arsip ini untuk dibaca AI agent. Jangan mengarang isi buku — ambil dari",
        "URL di bawah dan sebutkan sumbernya.",
        "",
        "## Cara pakai",
        "",
        "1. `index.json` di root = katalog semua buku.",
        "2. `books/<id>/index.json` = peta isi satu buku: daftar halaman, bab,",
        "   dan tema. Baca ini dulu sebelum mengambil halaman.",
        "3. Halaman: `books/<id>/pages/pNNN.json` (3 digit, mis. `001/pages/p119.json`).",
        "4. Saat menjawab, kutip: 『judul buku』hlm. <page_label>.",
        "",
        "Jangan ambil semua halaman sekaligus; baca peta dulu, lalu ambil 1–3",
        "halaman yang relevan dengan pertanyaan.",
        "",
        "## Buku",
        "",
    ]
    for b in books:
        m = b["meta"]
        lines += [
            f"### {b['id']} — {m['title']}",
            f"{m['lang']} · {b['index']['pages']} halaman",
            f"peta: {BASE_URL}/books/{b['id']}/index.json",
            "",
        ]
    lines += [
        "## Format halaman",
        "",
        "- `book` {id, title, lang} · `page` (urutan) · `page_label` (nomor cetak)",
        "- `outline` — jalur bab, mis. [\"第2章 地学分野\",\"テーマ18 前線・気圧配置\"]",
        "- `blocks` — `heading` (dengan `level`), `text`, `table` (markdown),",
        "  `figure` (deskripsi gambar, diawali 【図】)",
        "",
        "## Cakupan",
        "",
        "Buku baru ditambahkan sebagai folder `books/<id>/`. Daftar di atas",
        "digenerate dari `books/*/meta.json`. Buku yang tidak tercantum di sini",
        "belum masuk arsip.",
        "",
    ]
    with open(os.path.join(ROOT, "llms.txt"), "w") as f:
        f.write("\n".join(lines))


def main():
    if not os.path.isdir(BOOKS):
        sys.exit("folder books/ tidak ditemukan")

    books = []
    seen = set()
    for book_id in book_dirs():
        meta = json.load(open(os.path.join(BOOKS, book_id, "meta.json")))
        if meta.get("id") != book_id:
            sys.exit(f"books/{book_id}/meta.json: id='{meta.get('id')}' tidak cocok dengan nama folder")
        if book_id in seen:
            sys.exit(f"id dobel: {book_id}")
        seen.add(book_id)
        pages = load_pages(os.path.join(BOOKS, book_id))
        if not pages:
            sys.exit(f"books/{book_id}/pages/ kosong")
        index = build_book_index(book_id, meta, pages)
        books.append({"id": book_id, "meta": meta, "index": index})
        print(f"  {book_id}: {len(pages)} halaman — {meta['title']}")

    write_root_index(books)
    write_llms(books)

    ids = sorted(int(b["id"]) for b in books if b["id"].isdigit())
    if ids:
        gaps = [n for n in range(1, max(ids) + 1) if n not in ids]
        if gaps:
            print(f"  peringatan: nomor buku bolong -> {gaps}")
        print(f"  buku: {len(books)} · id terakhir: {max(ids):03d}")
    print("selesai: index.json, llms.txt, dan index.json per buku diperbarui")


if __name__ == "__main__":
    main()
