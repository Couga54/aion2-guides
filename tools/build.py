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
        return Markup(f'<span class="sk" data-sk="{slug}">{name}</span>')
    src = f'{ctx["root"]}assets/icons/{ctx["cls"]["slug"]}/{sk["icon"]}'
    return Markup(f'<span class="sk" data-sk="{slug}"><img src="{src}" width="18" height="18" alt="" loading="lazy">{name}</span>')


def clean_desc(text):
    """Skill descriptions carry damage placeholders like {se_dmg:...}-{se_dmg:...}; show them as X."""
    import re
    text = re.sub(r"\{se_[^}]*\}\s*-\s*\{se_[^}]*\}", "X", text)
    return re.sub(r"\{se_[^}]*\}", "X", text).strip()


def tooltip_json(cls_slug, lang):
    """Compact skill data for the hover tooltips on a class page (embedded as JSON)."""
    out = {}
    for slug, sk in SKILLS[cls_slug].items():
        L = sk[lang]
        out[slug] = {"n": L["name"], "c": sk.get("category"), "cd": round((sk.get("cooldown") or 0) / 1000),
                     "d": clean_desc(L.get("desc", "")), "sp": [[x["level"], x["text"]] for x in L.get("specs", [])]}
    return Markup(json.dumps(out, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))


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
    e.globals.update(tooltip_json=tooltip_json, CHANGELOG=CHANGELOG, fmt_utc=fmt_utc, fmt_day=fmt_day, s=s, sp=sp, skill_data=skill_data, icon_url=icon_url, SITE=SITE)
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


MODES = ("pve", "pvp", "lvl")


def search_entries(cls, lang, html):
    """Search entries for one class page: the class, its guide sections and the skills it mentions."""
    import re
    t = I18N[lang]
    slug, name = cls["slug"], cls["name"][lang]
    off = cls.get("modes_off", [])
    out = [{"k": "class", "t": name, "s": cls["role"][lang], "u": f"{slug}/", "i": f"assets/classes/{slug}.webp"}]
    for sid, only, title in re.findall(
            r'<section id="([^"]+)" class="g-section[^"]*" data-only="([^"]+)"[^>]*>.*?<h2 id="h-[^"]+">(.*?)</h2>', html, re.S):
        modes = [m for m in only.split() if m in MODES and m not in off]
        if not modes:
            continue
        label = t["mode_" + modes[0]]
        out.append({"k": "section", "t": re.sub(r"<[^>]+>", "", title), "s": f"{name} · {label}",
                    "u": f"{slug}/?mode={modes[0]}#{sid}"})
    used = set(re.findall(r'data-sk="([^"]+)"', html))
    for sk_slug in sorted(used):
        sk = SKILLS[slug].get(sk_slug)
        if sk:
            out.append({"k": "skill", "t": sk[lang]["name"], "s": name, "u": f"{slug}/?sk={sk_slug}",
                        "i": f"assets/icons/{slug}/{sk['icon']}"})
    return out


def page_entries(lang):
    """Search entries for the standalone pages and the world bosses."""
    t = I18N[lang]
    out = [{"k": "page", "t": t[key], "s": "", "u": path} for path, key in (
        ("week-1/", "w1_title"), ("weekly/", "wk_title"), ("bosses/", "bs_title"),
        ("sources/", "src_title"), ("changelog/", "wn_history"))]
    for g in BOSSES["groups"]:
        for b in g["bosses"]:
            out.append({"k": "boss", "t": b["name"][lang], "s": f'{g["zone"][lang]} · {g["faction"][lang]}',
                        "u": f'bosses/#b-{b["id"]}'})
    return out


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    e = env()
    urls = []
    for lang in LANGS:
        index = []   # search index for this language (docs/<lang>/search.json)
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
            html = e.get_template("class.html").render(ctx)
            write(f'{lang}/{path}index.html', html)
            urls.append(path)
            index += search_entries(cls, lang, html)
        for path, tpl, key, data in (("week-1/", "week1.html", "week1", WEEK1), ("weekly/", "weekly.html", "weekly", WEEKLY), ("bosses/", "bosses.html", "bosses", BOSSES), ("changelog/", "changelog.html", "changelog", CHANGELOG)):
            ctx = page_ctx(lang, path, "../../")
            ctx[key] = data
            write(f"{lang}/{path}index.html", e.get_template(tpl).render(ctx))
            urls.append(path)
        ctx = page_ctx(lang, "sources/", "../../")
        ctx["sources"] = SOURCES["groups"]
        write(f"{lang}/sources/index.html", e.get_template("sources.html").render(ctx))
        urls.append("sources/")
        index += page_entries(lang)
        write(f"{lang}/search.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))

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
