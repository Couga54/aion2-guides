"""Build the static site into docs/.

  python tools/build.py

Inputs:
  data/site.json, data/i18n.json    classes, languages, UI strings
  data/skills/<class>.json          skill data (tools/fetch_skills.py)
  data/leveling/*.json              leveling checklist steps
  src/templates/*.html              page layouts + macros
  src/content/<class>/<lang>.html   guide text (Jinja, uses macros)
  src/assets/                       css, js, icons (copied as-is)
"""
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, pass_context
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "src"
OUT = ROOT / "docs"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


SITE = load(DATA / "site.json")
I18N = load(DATA / "i18n.json")
LANGS = SITE["langs"]
SOURCES = load(DATA / "sources.json")
WEEKLY = load(DATA / "weekly.json")
CHANGELOG = load(DATA / "changelog.json")["entries"]
WEEK1 = load(DATA / "week1.json")
BOSSES = load(DATA / "bosses.json")
SKILLS = {p.stem: load(p) for p in (DATA / "skills").glob("*.json") if not p.stem.startswith("_")}
for _cls, _fixes in load(DATA / "skills" / "_overrides.json").items():
    for _slug, _langs in ([] if _cls.startswith("_") else _fixes.items()):
        for _lang, _fields in _langs.items():
            SKILLS[_cls][_slug][_lang].update(_fields)


# ---- helpers exposed to templates -------------------------------------------------

@pass_context
def s(ctx, slug, icon=True):
    """Inline skill reference: small icon + localized name."""
    sk = SKILLS[ctx["cls"]["slug"]][slug]
    name = escape(sk[ctx["lang"]]["name"])
    if not icon:
        return Markup(f'<span class="sk">{name}</span>')
    src = f'{ctx["root"]}assets/icons/{ctx["cls"]["slug"]}/{sk["icon"]}'
    return Markup(f'<span class="sk"><img src="{src}" width="18" height="18" alt="" loading="lazy">{name}</span>')


@pass_context
def skill_data(ctx, slug):
    return SKILLS[ctx["cls"]["slug"]][slug]


@pass_context
def icon_url(ctx, slug):
    sk = SKILLS[ctx["cls"]["slug"]][slug]
    return f'{ctx["root"]}assets/icons/{ctx["cls"]["slug"]}/{sk["icon"]}'


@pass_context
def sp(ctx, slug, index):
    """A specialization's text in the page language, e.g. sp('rending-blow', 2)."""
    return SKILLS[ctx["cls"]["slug"]][slug][ctx["lang"]]["specs"][index]["text"]


def expand(text, cls_slug, lang):
    """Replace [[slug]] with the localized skill name and [[slug#N]] with a specialization."""
    import re
    skills = SKILLS[cls_slug]

    def rep(m):
        slug, idx = m.group(1), m.group(2)
        if idx is not None:
            return "<em>" + str(escape(skills[slug][lang]["specs"][int(idx)]["text"])) + "</em>"
        return "<strong>" + str(escape(skills[slug][lang]["name"])) + "</strong>"
    return re.sub(r"\[\[([a-z0-9-]+)(?:#(\d+))?\]\]", rep, text)


MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
           "сентября", "октября", "ноября", "декабря"],
}


def fmt_utc(iso, lang):
    """'2026-09-28T13:00:00Z' -> 'Sep 28 · 13:00 UTC' / '28 сентября · 13:00 UTC'."""
    from datetime import datetime
    d = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    day = f"{MONTHS[lang][d.month - 1]} {d.day}" if lang == "en" else f"{d.day} {MONTHS[lang][d.month - 1]}"
    return f"{day} · {d:%H:%M} UTC"


def fmt_day(iso, lang):
    """'2026-09-27' -> 'Sep 27, 2026' / '27 сентября 2026'."""
    y, m, d = (int(x) for x in iso.split("-"))
    mon = MONTHS[lang][m - 1]
    return f"{mon} {d}, {y}" if lang == "en" else f"{d} {mon} {y}"


def leveling_steps(cls_slug, lang):
    """Merge the shared route with class-specific steps, ordered by level."""
    steps = load(DATA / "leveling" / "common.json")["steps"]
    cls_file = DATA / "leveling" / f"{cls_slug}.json"
    if cls_file.exists():
        steps = steps + load(cls_file)["steps"]
    out = []
    for st in steps:
        out.append({
            "id": st["id"],
            "order": st["order"],
            "when": st["when"][lang],
            "text": expand(st["text"][lang], cls_slug, lang),
            "kind": "class" if st["id"].startswith(cls_slug) else "route",
            "skills": st.get("skills", []),
        })
    return sorted(out, key=lambda x: x["order"])


def env():
    e = Environment(
        loader=FileSystemLoader([SRC / "templates", SRC / "content"]),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=["jinja2.ext.do"],
    )
    e.globals.update(CHANGELOG=CHANGELOG, fmt_utc=fmt_utc, fmt_day=fmt_day, s=s, sp=sp, skill_data=skill_data, icon_url=icon_url, SITE=SITE)
    return e


# ---- pages ------------------------------------------------------------------------

def page_ctx(lang, path, root, cls=None):
    other = [l for l in LANGS if l != lang][0]
    return {
        "lang": lang,
        "other_lang": other,
        "t": I18N[lang],
        "t_other": I18N[other],
        "root": root,
        "path": path,                       # path under /<lang>/, e.g. "gladiator/"
        "canonical": f'{SITE["base_url"]}{lang}/{path}',
        "alt_urls": {l: f'{SITE["base_url"]}{l}/{path}' for l in LANGS},
        "classes": SITE["classes"],
        "cls": cls,
        "updated": SITE["updated"],
    }


def write(rel, html):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    e = env()
    urls = []
    for lang in LANGS:
        ctx = page_ctx(lang, "", "../")
        write(f"{lang}/index.html", e.get_template("home.html").render(ctx))
        urls.append("")
        for cls in SITE["classes"]:
            if cls["status"] != "ready":
                continue
            path = f'{cls["slug"]}/'
            ctx = page_ctx(lang, path, "../../", cls)
            ctx["steps"] = leveling_steps(cls["slug"], lang)
            ctx["content_tpl"] = f'{cls["slug"]}/{lang}.html'
            write(f'{lang}/{path}index.html', e.get_template("class.html").render(ctx))
            urls.append(path)
        for path, tpl, key, data in (("week-1/", "week1.html", "week1", WEEK1), ("weekly/", "weekly.html", "weekly", WEEKLY), ("bosses/", "bosses.html", "bosses", BOSSES), ("changelog/", "changelog.html", "changelog", CHANGELOG)):
            ctx = page_ctx(lang, path, "../../")
            ctx[key] = data
            write(f"{lang}/{path}index.html", e.get_template(tpl).render(ctx))
            urls.append(path)
        ctx = page_ctx(lang, "sources/", "../../")
        ctx["sources"] = SOURCES["groups"]
        write(f"{lang}/sources/index.html", e.get_template("sources.html").render(ctx))
        urls.append("sources/")

    # Root: language chooser that redirects by browser language.
    write("index.html", e.get_template("root.html").render(page_ctx("en", "", "")))
    write("404.html", e.get_template("404.html").render(page_ctx("en", "", "/aion2-guides/")))

    base = SITE["base_url"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in dict.fromkeys(urls):
        for lang in LANGS:
            sm.append(f"  <url><loc>{base}{lang}/{path}</loc><lastmod>{SITE['updated']}</lastmod>")
            for alt in LANGS:
                sm.append(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{base}{alt}/{path}"/>')
            sm.append("  </url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n")
    print(f"built {len(urls)} pages -> docs/")


if __name__ == "__main__":
    build()
