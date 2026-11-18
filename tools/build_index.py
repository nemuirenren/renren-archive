#!/usr/bin/env python3
"""Regenerate all maps and HTML mirrors for the archive.

    python3 tools/build_index.py

Writes:
    index.json, index.html, llms.txt
    books/<id>/index.json, books/<id>/index.html
    books/<id>/pages/pNNN.html      (HTML mirror of each page)

Source of truth: books/<id>/meta.json + books/<id>/pages/pNNN.json
"""
import glob
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "books")
BASE_URL = "https://nemuirenren.github.io/renren-archive"
RAW_BASE = "https://raw.githubusercontent.com/nemuirenren/renren-archive/main"
SCHEMA_VERSION = "2.0"

STYLE = """body{font:16px/1.7 -apple-system,Segoe UI,Roboto,sans-serif;margin:2rem auto;
max-width:56rem;padding:0 1rem;color:#1b1a17;background:#faf8f3}
a{color:#8a3b2e}h1{font-size:1.5rem;line-height:1.35}h2{font-size:1.15rem;margin-top:2rem}
table{border-collapse:collapse;margin:.8rem 0;font-size:.95rem}
th,td{border:1px solid #d8d2c4;padding:.35rem .6rem;text-align:left;vertical-align:top}
th{background:#efe9dc}
pre{background:#f1ece1;padding:1rem;overflow:auto;font-size:.78rem;line-height:1.45}
.meta{color:#6d6558;font-size:.9rem}
.fig{display:block;border-left:3px solid #d8d2c4;padding-left:.8rem;margin:1rem 0;color:#3a352c}"""


def esc(s):
    return html.escape(str(s), quote=False)


def html_doc(title, body, css_href):
    return (
        "<!doctype html>\n<html lang=\"id\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n"
        f"<link rel=\"stylesheet\" href=\"{css_href}\">\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>\n"
    )


def render_md_table(text):
    rows = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 3:
        return f"<pre>{esc(text)}</pre>"

    def cells(ln):
        return [c.strip() for c in ln.strip().strip("|").split("|")]

    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{esc(c)}</th>" for c in header]
    out += ["</tr></thead>", "<tbody>"]
    for r in body:
        out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>")
    out += ["</tbody>", "</table>"]
    return "".join(out)


def render_blocks(blocks):
    out = []
    for b in blocks:
        t = b.get("type")
        txt = b.get("text", "")
        if t == "heading":
            lvl = min(max(int(b.get("level", 3)), 3), 6)
            out.append(f"<h{lvl}>{esc(txt)}</h{lvl}>")
        elif t == "table":
            out.append(render_md_table(txt))
        elif t == "figure":
            out.append(f'<p class="fig">{esc(txt)}</p>')
        else:
            out.append("<p>" + "<br>".join(esc(p) for p in txt.split("\n")) + "</p>")
    return "\n".join(out)


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
    ranges, order = {}, []
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

    rows = []
    for p in pages:
        label = p["page_label"] or "—"
        rows.append(
            f'<tr><td><a href="pages/p{p["page"]:03d}.html">hal. {esc(label)}</a></td>'
            f'<td>{esc(" → ".join(p["outline"]))}</td>'
            f'<td>{esc(p["first_heading"])}</td></tr>'
        )
    body = (
        f'<p class="meta"><a href="../../index.html">Renren Archive</a> · '
        f'{esc(meta["lang"])} · {len(pages)} halaman</p>'
        f"<h1>{esc(meta['title'])}</h1>"
        "<h2>Peta halaman</h2>"
        "<p>Kolom kedua = bab/tema, kolom ketiga = heading pertama halaman itu.</p>"
        "<table><thead><tr><th>Halaman</th><th>Bab / tema</th><th>Heading pertama</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )
    with open(os.path.join(BOOKS, book_id, "index.html"), "w") as f:
        f.write(html_doc(f"{book_id} — {meta['title']}", body, "../style.css"))
    return index


def write_page_html(book_id, meta, d):
    raw = json.dumps(d, ensure_ascii=False, indent=1)
    crumb = esc(" → ".join(o["title"] for o in d.get("outline", [])) or meta["title"])
    body = (
        f'<p class="meta"><a href="../../../index.html">Renren Archive</a> · '
        f'<a href="../index.html">{esc(meta["title"])}</a> · '
        f'hal. {esc(d.get("page_label") or "—")} (urutan {d["page"]})</p>'
        f"<h1>{crumb}</h1>"
        + render_blocks(d.get("blocks", []))
        + "<h2>JSON</h2>"
        + f"<pre>{esc(raw)}</pre>"
    )
    path = os.path.join(BOOKS, book_id, "pages", f"p{d['page']:03d}.html")
    with open(path, "w") as f:
        f.write(html_doc(f"{book_id} p{d['page']:03d} — {meta['title']}", body, "../../../style.css"))


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

    items = "".join(
        f'<li><a href="books/{b["id"]}/index.html">{b["id"]} — {esc(b["meta"]["title"])}</a>'
        f'<span class="meta"> · {esc(b["meta"]["lang"])} · {b["index"]["pages"]} halaman</span></li>'
        for b in books
    )
    body = (
        "<h1>Renren Archive</h1>"
        "<p>Arsip materi belajar bahasa Jepang. Setiap buku dipecah per halaman; "
        "tiap halaman tersedia sebagai HTML (mudah dibaca AI) dan JSON (data mentah).</p>"
        f"<h2>Buku</h2><ul>{items}</ul>"
    )
    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(html_doc("Renren Archive", body, "style.css"))
    return index


def write_llms(books):
    lines = [
        "# Renren Archive",
        "",
        "> Arsip materi belajar bahasa Jepang. Setiap buku dipecah per halaman,",
        "> dengan struktur bab/tema yang konsisten.",
        "",
        "Arsip ini untuk dibaca AI agent. Jangan mengarang isi buku — ambil dari",
        "URL di bawah dan sebutkan sumbernya.",
        "",
        "## ATURAN WAJIB: buka versi .html",
        "",
        "Setiap halaman tersedia dalam dua bentuk: `.html` (untuk dibaca) dan",
        "`.json` (data mentah). Gunakan yang **.html**.",
        "",
        "JANGAN memakai `nemuirenren.github.io/.../*.json` — dikirim sebagai",
        "`application/json` dan sering gagal dibaca tool AI.",
        "",
        "JANGAN memakai `raw.githubusercontent.com` — diblokir di sebagian jaringan.",
        "",
        "Kalau sebuah tautan berakhiran `.json`, ubah ekstensinya menjadi `.html`.",
        "",
        "## Cara pakai",
        "",
        "1. `index.html` = daftar semua buku.",
        "2. `books/<id>/index.html` = peta isi satu buku: daftar halaman, bab,",
        "   dan tema. Baca ini dulu sebelum mengambil halaman.",
        "3. Halaman: `books/<id>/pages/pNNN.html` (3 digit, mis. `001/pages/p119.html`).",
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
            f"peta: {BASE_URL}/books/{b['id']}/index.html",
            "",
        ]
    lines += [
        "## Data mentah (untuk program, bukan untuk browsing)",
        "",
        f"- Katalog: {RAW_BASE}/index.json",
        f"- Halaman: {RAW_BASE}/books/<id>/pages/pNNN.json",
        "",
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

    books, seen = [], set()
    for book_id in book_dirs():
        meta = json.load(open(os.path.join(BOOKS, book_id, "meta.json")))
        if meta.get("id") != book_id:
            sys.exit(f"books/{book_id}/meta.json: id tidak cocok dengan nama folder")
        if book_id in seen:
            sys.exit(f"id dobel: {book_id}")
        seen.add(book_id)
        pages = load_pages(os.path.join(BOOKS, book_id))
        if not pages:
            sys.exit(f"books/{book_id}/pages/ kosong")
        index = build_book_index(book_id, meta, pages)
        for p in pages:
            d = json.load(open(os.path.join(BOOKS, book_id, "pages", f"p{p['page']:03d}.json")))
            write_page_html(book_id, meta, d)
        books.append({"id": book_id, "meta": meta, "index": index})
        print(f"  {book_id}: {len(pages)} halaman — {meta['title']} (+{len(pages)} HTML)")

    with open(os.path.join(ROOT, "style.css"), "w") as f:
        f.write(STYLE + "\n")
    write_root_index(books)
    write_llms(books)

    ids = sorted(int(b["id"]) for b in books if b["id"].isdigit())
    if ids:
        gaps = [n for n in range(1, max(ids) + 1) if n not in ids]
        if gaps:
            print(f"  peringatan: nomor buku bolong -> {gaps}")
        print(f"  buku: {len(books)} · id terakhir: {max(ids):03d}")
    print("selesai: index/llms + peta buku + HTML per halaman diperbarui")


if __name__ == "__main__":
    main()
