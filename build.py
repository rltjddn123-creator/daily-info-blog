#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content/**/*.md 를 읽어 site/ 폴더에 정적 HTML 블로그를 생성한다.
외부 라이브러리 없이 동작 (markdown 변환은 이 파일의 규칙에 맞춘 경량 파서).
"""
import glob
import html
import os
import re
import sys

from make_cover import make_cover

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CONTENT_DIR = os.path.join(PROJECT_DIR, "content")
POSTS_DIR = os.path.join(BASE_DIR, "posts")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
SITE_TITLE = "생활정보 꿀팁"
SITE_DESC = "생활에 도움되는 정보와 추천템을 모아드립니다."
SITE_URL = os.environ.get("SITE_URL", "https://REPLACE_ME.github.io/daily-info-blog")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


def slugify(name):
    name = re.sub(r"\.md$", "", name)
    name = re.sub(r"^[0-9]+-", "", name)
    return name


def md_inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r'<a href="\2" target="_blank" rel="nofollow sponsored noopener">\1</a>', text)
    return text


def md_to_html(body_lines):
    html_out = []
    para = []

    def flush_para():
        if para:
            html_out.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    in_quote = False
    quote_buf = []

    def flush_quote():
        nonlocal in_quote
        if quote_buf:
            html_out.append('<blockquote>' + "<br>".join(quote_buf) + "</blockquote>")
            quote_buf.clear()
        in_quote = False

    for raw in body_lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped == "---":
            flush_para()
            flush_quote()
            continue
        if stripped.startswith(">"):
            flush_para()
            in_quote = True
            content = stripped.lstrip(">").strip()
            if content:
                quote_buf.append(md_inline(content))
            continue
        else:
            if in_quote:
                flush_quote()
        if stripped.startswith("### "):
            flush_para()
            html_out.append(f"<h3>{md_inline(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            flush_para()
            html_out.append(f"<h2>{md_inline(stripped[3:])}</h2>")
            continue
        if stripped == "":
            flush_para()
            continue
        para.append(md_inline(stripped))
    flush_para()
    flush_quote()
    return "\n".join(html_out)


def parse_post(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    title = lines[0].strip()
    title = re.sub(r"^#\s*(\[제목\]\s*)?", "", title)
    tags = []
    body_start = 0
    for i, line in enumerate(lines[1:], start=1):
        m = re.match(r"\*\*추천 태그\*\*:\s*(.+)", line.strip())
        if m:
            tags = [t.strip() for t in m.group(1).split() if t.strip().startswith("#")]
        if line.strip() == "---":
            body_start = i + 1
            break
    body_lines = lines[body_start:] if body_start else lines[1:]
    body_html = md_to_html(body_lines)
    plain = re.sub(r"<[^>]+>", "", body_html)
    desc = re.sub(r"\s+", " ", plain).strip()[:120]
    return {"title": title, "tags": tags, "body_html": body_html, "desc": desc}


POST_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {site_title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:image" content="{site_url}/images/{slug}.jpg">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="site-header"><a href="../index.html">{site_title}</a></header>
<main class="post">
<img class="cover" src="../images/{slug}.jpg" alt="{title}">
<h1>{title}</h1>
<div class="tags">{tags_html}</div>
<div class="content">
{body}
</div>
<p class="back"><a href="../index.html">&larr; 목록으로</a></p>
</main>
<footer>&copy; {site_title}</footer>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{site_title}</title>
<meta name="description" content="{site_desc}">
<meta name="google-site-verification" content="Yy1UbbQQu4Oav9rL7LByselcH0V3KHstxtRUDphT8Bc" />
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header"><a href="index.html">{site_title}</a></header>
<main>
<p class="lead">{site_desc}</p>
<ul class="post-list">
{items}
</ul>
</main>
<footer>&copy; {site_title}</footer>
</body>
</html>
"""

CSS = """
:root{--fg:#222;--bg:#fff;--accent:#2563eb;--muted:#666;}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:760px;margin:0 auto;padding:0 20px 60px;color:var(--fg);background:var(--bg);line-height:1.7}
.site-header{padding:24px 0;font-weight:700;font-size:1.2rem}
.site-header a{color:var(--fg);text-decoration:none}
h1{font-size:1.6rem;margin-bottom:8px}
h2{font-size:1.25rem;margin-top:32px}
h3{font-size:1.05rem;margin-top:24px}
a{color:var(--accent)}
.tags{color:var(--muted);font-size:.9rem;margin-bottom:24px}
blockquote{background:#f3f6ff;border-left:4px solid var(--accent);margin:24px 0;padding:12px 16px;border-radius:4px;font-size:.95rem}
.post-list{list-style:none;padding:0}
.post-list li{display:flex;gap:16px;align-items:center;padding:16px 0;border-bottom:1px solid #eee}
.post-list .thumb{width:96px;height:64px;object-fit:cover;border-radius:8px;flex-shrink:0}
.post-list a{font-weight:600;text-decoration:none;color:var(--fg)}
.post-list .meta{color:var(--muted);font-size:.85rem;margin-top:4px}
.post .cover{width:100%;aspect-ratio:1200/630;object-fit:cover;border-radius:10px;margin:8px 0 24px}
.lead{color:var(--muted)}
.back{margin-top:40px}
footer{margin-top:60px;color:var(--muted);font-size:.85rem;text-align:center}
"""


def main():
    md_files = sorted(glob.glob(os.path.join(CONTENT_DIR, "*", "*.md")))
    items_html = []
    for path in reversed(md_files):
        folder = os.path.basename(os.path.dirname(path))
        fname = os.path.basename(path)
        slug = f"{folder}-{slugify(fname)}"
        slug = re.sub(r"[^a-zA-Z0-9\-가-힣]", "-", slug)
        post = parse_post(path)
        tags_html = " ".join(f'<span>{html.escape(t)}</span>' for t in post["tags"])
        img_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
        if not os.path.exists(img_path):
            make_cover(post["title"], img_path)

        out_path = os.path.join(POSTS_DIR, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(POST_TEMPLATE.format(
                title=html.escape(post["title"]),
                site_title=SITE_TITLE,
                desc=html.escape(post["desc"]),
                tags_html=tags_html,
                body=post["body_html"],
                slug=slug,
                site_url=SITE_URL,
            ))
        items_html.append(
            f'<li><img class="thumb" src="images/{slug}.jpg" alt="">'
            f'<div><a href="posts/{slug}.html">{html.escape(post["title"])}</a>'
            f'<div class="meta">{folder}</div></div></li>'
        )

    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX_TEMPLATE.format(
            site_title=SITE_TITLE,
            site_desc=SITE_DESC,
            items="\n".join(items_html),
        ))

    with open(os.path.join(BASE_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)

    with open(os.path.join(BASE_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    urls = [SITE_URL + "/"] + [SITE_URL + f"/posts/{os.path.basename(p)[:-5]}.html" for p in sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append(f"  <url><loc>{u}</loc></url>")
    sitemap.append("</urlset>")
    with open(os.path.join(BASE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))

    print(f"built {len(md_files)} posts")


if __name__ == "__main__":
    main()
