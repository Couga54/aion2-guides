"""The site moved to https://aion2-guides.info (Oct 13, 2026). This GitHub Pages copy is legacy: every built page in
docs/ is post-processed (no rebuild needed) so that it

  - points search engines to the new address (canonical, hreflang, og:url, sitemap);
  - sends the visitor to the same page there at once (script, keeps ?query and #anchor);
  - shows a banner with a link to the new page, for the case the redirect does not run.

    python tools/legacy_redirect.py      (idempotent: a page that already has the banner is left alone)
"""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
OLD = "https://couga54.github.io/aion2-guides/"
NEW = "https://aion2-guides.info/"
MARK = "legacy-moved"

TEXT = {
    "en": ("This site has moved to", "This copy is no longer updated.", "Open the new site"),
    "ru": ("Сайт переехал на", "Эта копия больше не обновляется.", "Открыть новый сайт"),
    "uk": ("Сайт переїхав на", "Ця копія більше не оновлюється.", "Відкрити новий сайт"),
    "tr": ("Site taşındı:", "Bu kopya artık güncellenmiyor.", "Yeni siteyi aç"),
}

REDIRECT = """<script>/* legacy copy: go to the same page on the new site */(function(){try{var p=location.pathname.replace(/^\\/aion2-guides\\/?/,'');location.replace('%s'+p+location.search+location.hash);}catch(e){}})();</script>""" % NEW

BANNER = """<div class="%s" role="status" style="position:relative;z-index:2147483000;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;justify-content:center;padding:10px 16px;background:#d9b36c;color:#0b0e14;font:600 15px/1.4 system-ui,-apple-system,'Segoe UI',sans-serif;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,.35)"><span>%s <a href="%s" style="color:#0b0e14;text-decoration:underline">aion2-guides.info</a>. %s</span><a href="%s" style="padding:5px 14px;border-radius:999px;background:#0b0e14;color:#d9b36c;text-decoration:none;white-space:nowrap">%s →</a></div>"""


def page_path(f):
    rel = f.relative_to(DOCS).as_posix()
    return rel[: -len("index.html")] if rel.endswith("index.html") else rel


def main():
    n = 0
    for f in sorted(DOCS.rglob("*.html")):
        s = f.read_text(encoding="utf-8")
        if MARK in s:
            continue
        s = s.replace(OLD, NEW)
        lang = (re.search(r'<html lang="(\w+)"', s) or [None, "en"])[1]
        moved, stale, open_ = TEXT.get(lang, TEXT["en"])
        target = NEW + ("" if f.name == "404.html" else page_path(f))
        charset = '<meta charset="utf-8">'
        s = s.replace(charset, charset + "\n" + REDIRECT, 1) if charset in s else s.replace("<head>", "<head>\n" + REDIRECT, 1)
        s = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + BANNER % (MARK, moved, target, stale, target, open_), s, count=1)
        f.write_text(s, encoding="utf-8", newline="\n")
        n += 1
    for name in ("sitemap.xml", "robots.txt"):
        p = DOCS / name
        if p.exists():
            p.write_text(p.read_text(encoding="utf-8").replace(OLD, NEW), encoding="utf-8", newline="\n")
    print(n, "pages")


if __name__ == "__main__":
    main()
