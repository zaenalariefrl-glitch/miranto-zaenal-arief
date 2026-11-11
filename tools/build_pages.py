"""Build the English (/) and Indonesian (/id/) pages from src/portfolio.html.

The source keeps both languages side by side as <span lang="en"> / <span lang="id">.
Each output page keeps only its own language, so search engines index two clean,
separate pages linked by hreflang. Run from the repository root:

    python3 tools/build_pages.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://zaenalariefrl-glitch.github.io/miranto-zaenal-arief/"
SRC = (ROOT / "src" / "portfolio.html").read_text(encoding="utf-8")

META = {
    "en": {
        "title": "Miranto Zaenal Arief · Researcher, Speaker and Duta GenRe Indonesia 2024",
        "desc": "Portfolio of Miranto Zaenal Arief, International Management student at Universitas Pekalongan: "
                "research on the Artificial Illusion of Knowledge (AIK) and AI in learning, Duta GenRe Indonesia 2024, "
                "public speaking and MSME community work.",
        "locale": "en_US",
        "url": BASE,
    },
    "id": {
        "title": "Miranto Zaenal Arief · Peneliti, Pembicara, dan Duta GenRe Indonesia 2024",
        "desc": "Portofolio Miranto Zaenal Arief, mahasiswa Manajemen Internasional Universitas Pekalongan: riset "
                "Artificial Illusion of Knowledge (AIK) dan AI dalam pembelajaran, Duta GenRe Indonesia 2024, "
                "pembicara publik, dan pengabdian UMKM.",
        "locale": "id_ID",
        "url": BASE + "id/",
    },
}


def person_jsonld(lang):
    m = META[lang]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ProfilePage",
                "@id": m["url"] + "#page",
                "url": m["url"],
                "name": m["title"],
                "inLanguage": lang,
                "description": m["desc"],
                "mainEntity": {"@id": BASE + "#person"},
            },
            {
                "@type": "Person",
                "@id": BASE + "#person",
                "name": "Miranto Zaenal Arief",
                "url": BASE,
                "image": BASE + "assets/og-image.jpg",
                "email": "mailto:zaenalariefrl@gmail.com",
                "jobTitle": "Student researcher",
                "description": META["en"]["desc"],
                "address": {"@type": "PostalAddress", "addressLocality": "Pekalongan",
                            "addressRegion": "Central Java", "addressCountry": "ID"},
                "affiliation": {"@type": "CollegeOrUniversity", "name": "Universitas Pekalongan"},
                "alumniOf": [
                    {"@type": "CollegeOrUniversity", "name": "Universitas Pekalongan"},
                    {"@type": "CollegeOrUniversity", "name": "Universitas Islam Indonesia"},
                ],
                "knowsAbout": [
                    "Artificial Illusion of Knowledge (AIK)", "Generative AI in education",
                    "Self-regulated learning", "PLS-SEM", "Digital marketing", "Public speaking",
                ],
                "award": [
                    "Duta GenRe Indonesia 2024 (BKKBN)",
                    "Best I Male, Student GenRe Ambassador Selection, Special Region of Yogyakarta 2023",
                    "First Place Male, Duta GenRe DIY 2023 (BKKBN DIY)",
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def head(lang, prefix):
    m = META[lang]
    other = "id" if lang == "en" else "en"
    return f"""<title>{m['title']}</title>
<meta name="description" content="{m['desc']}">
<meta name="author" content="Miranto Zaenal Arief">
<meta name="google-site-verification" content="tugxu3GKRRHZMuRWRDecQ0keutQe8K_ENlFQDqSv9MA">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{m['url']}">
<link rel="alternate" hreflang="en" href="{META['en']['url']}">
<link rel="alternate" hreflang="id" href="{META['id']['url']}">
<link rel="alternate" hreflang="x-default" href="{META['en']['url']}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="Miranto Zaenal Arief">
<meta property="og:title" content="{m['title']}">
<meta property="og:description" content="{m['desc']}">
<meta property="og:url" content="{m['url']}">
<meta property="og:image" content="{BASE}assets/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Miranto Zaenal Arief, portfolio cover">
<meta property="og:locale" content="{m['locale']}">
<meta property="og:locale:alternate" content="{META[other]['locale']}">
<meta property="profile:first_name" content="Miranto">
<meta property="profile:last_name" content="Zaenal Arief">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{m['title']}">
<meta name="twitter:description" content="{m['desc']}">
<meta name="twitter:image" content="{BASE}assets/og-image.jpg">
<script type="application/ld+json">
{person_jsonld(lang)}
</script>"""


def strip_lang(html, drop):
    """Remove every <span lang="drop">...</span>, nesting-aware."""
    opener = f'<span lang="{drop}">'
    out, i = [], 0
    while True:
        j = html.find(opener, i)
        if j < 0:
            out.append(html[i:])
            return "".join(out)
        out.append(html[i:j])
        depth, k = 0, j
        while True:
            o = html.find("<span", k)
            c = html.find("</span>", k)
            if o != -1 and o < c:
                depth += 1
                k = o + 5
            else:
                depth -= 1
                k = c + 7
                if depth == 0:
                    break
        i = k


def unwrap_lang(html, keep):
    """Drop the now-redundant <span lang="keep"> wrappers, keeping their content."""
    opener = f'<span lang="{keep}">'
    while True:
        j = html.find(opener)
        if j < 0:
            return html
        depth, k = 0, j
        while True:
            o = html.find("<span", k)
            c = html.find("</span>", k)
            if o != -1 and o < c:
                depth += 1
                k = o + 5
            else:
                depth -= 1
                if depth == 0:
                    end = c
                    break
                k = c + 7
        html = html[:j] + html[j + len(opener):end] + html[end + 7:]


def build(lang):
    prefix = "" if lang == "en" else "../"
    html = SRC.replace("{{HEAD}}", head(lang, prefix)).replace("{{LANG}}", lang)
    html = html.replace("{{HREF_EN}}", "./" if lang == "en" else "../")
    html = html.replace("{{HREF_ID}}", "id/" if lang == "en" else "./")
    html = html.replace("{{CUR_EN}}", 'aria-current="page"' if lang == "en" else "")
    html = html.replace("{{CUR_ID}}", 'aria-current="page"' if lang == "id" else "")
    html = strip_lang(html, "id" if lang == "en" else "en")
    html = unwrap_lang(html, lang)
    # The lightbox reads its caption from <b> directly now that each page has one language.
    html = html.replace("var t = b.querySelector('b [lang=\"' + root.dataset.lang + '\"]');", "var t = b.querySelector('b');")
    if prefix:
        html = re.sub(r'((?:src|href|data-full)=")(assets/|scrollcraft\.(?:css|js))', r"\1" + prefix + r"\2", html)
    assert "{{" not in html, "unfilled placeholder"
    leftover = re.findall(r".{50}lang=\"(?:en|id)\">", html.replace("<html lang=\"" + lang + "\"", ""))
    assert not leftover, leftover[:3]
    out = ROOT / ("index.html" if lang == "en" else "id/index.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out.relative_to(ROOT), len(html))


for lang in ("en", "id"):
    build(lang)

(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
(ROOT / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>{META['en']['url']}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{META['en']['url']}"/>
    <xhtml:link rel="alternate" hreflang="id" href="{META['id']['url']}"/>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{META['id']['url']}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{META['en']['url']}"/>
    <xhtml:link rel="alternate" hreflang="id" href="{META['id']['url']}"/>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
""", encoding="utf-8")
print("wrote robots.txt, sitemap.xml")
