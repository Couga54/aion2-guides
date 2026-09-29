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
PROGRESSION = load(DATA / "progression.json")
CRAFTING = load(DATA / "crafting.json")
BOARDS = {p.stem: load(p) for p in (DATA / "boards").glob("*.json") if p.stem != "presets"}
BOARD_PRESETS = load(DATA / "boards" / "presets.json")
ITEMS = load(DATA / "items.json")
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


@pass_context
def it(ctx, text):
    """Progression page text: replace {i:key} with an item chip (icon + localized name, colored by grade)."""
    import re
    lang, root = ctx["lang"], ctx["root"]

    def chip(m):
        item = ITEMS[m.group(1)]
        name = re.sub(r"\s*\((Bound|привяз\.)\)$", "", item[lang])
        return (f'<span class="it g{item["grade"]}" data-sk="i:{m.group(1)}"><img src="{root}assets/icons/items/{item["icon"]}"'
                f' width="20" height="20" alt="" loading="lazy">{escape(name)}</span>')
    return Markup(re.sub(r"\{i:(\w+)\}", chip, text))


# Stat ids used by the items on the progression page -> labels (questlog gives ids only).
STAT_LABELS = {
    "en": {"weaponfixingdamage": "Attack", "armordefense": "Defense", "hpmax": "HP", "critical": "Critical Hit",
           "weaponaccuracy": "Accuracy", "justice": "Justice [Nezekan]", "wisdom": "Wisdom [Lumiel]", "death": "Death [Triniel]",
           "space": "Space [Israphel]", "illusion": "Illusion [Kaisinel]", "destruction": "Destruction [Zikel]",
           "life": "Life [Yustiel]", "destiny": "Destiny [Marchutan]"},
    "ru": {"weaponfixingdamage": "Атака", "armordefense": "Защита", "hpmax": "ОЗ", "critical": "Крит. удар",
           "weaponaccuracy": "Точность", "justice": "Справедливость [Нэзакан]", "wisdom": "Мудрость [Люмиэль]",
           "death": "Смерть [Триниэль]", "space": "Пространство [Исфаэль]", "illusion": "Иллюзия [Кайсинель]",
           "destruction": "Разрушение [Зикель]", "life": "Жизнь [Юстиэль]", "destiny": "Судьба [Марчутан]"},
}


def items_tip_json(lang):
    """Hover tooltips for the item chips on the guide pages (embedded as JSON)."""
    return Markup(json.dumps(items_tip(lang), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))


def items_tip(lang):
    """Item chip tooltips in the same shape as the skill tooltips (n name, m meta line, d description,
    sp list of [label, text]) so site.js shows them the same way. Used on guide pages and class guides."""
    t = I18N[lang]
    out = {}
    for key, item in ITEMS.items():
        tip = item["tip_" + lang]
        meta = [f'{t["pg_il"]} {tip["il"]}'] if tip.get("il") else []
        if tip.get("set"):
            meta.append(f'{t["pg_set"]}: {tip["set"]["name"]}')
        lines = [tip["desc"]] if tip["desc"] else []
        lines += [f'{STAT_LABELS[lang].get(k, k)}: {v}' for k, v in tip["stats"] if k in STAT_LABELS[lang]]
        out["i:" + key] = {"n": item[lang], "m": " · ".join(meta), "g": item["grade"], "d": "\n".join(lines),
                           "sp": [[f'{n}×', b] for n, b in (tip["set"]["bonus"] if tip.get("set") else [])]}
    return out


WATCH_FILL = {"ru": "en"}   # RU pages fill free places with the English-speaking authors of the guide


def watch_for(cls, lang, limit=3):
    """'Who to watch' on a class page: players of this class among the guide's source authors (the names in
    site.json classes[].src whose sources.json 'plays' lists the class) who make content in the page language,
    then the streamers from the Sources page 'watch' group, then (RU pages only) the English-speaking ones."""
    src_text = " ".join(v[0] for v in (cls.get("src") or {}).values())
    authors, streamers, fill = [], [], []
    for g in SOURCES["groups"]:
        for item in g["items"]:
            langs = item.get("lang", [])
            if lang not in langs and WATCH_FILL.get(lang) not in langs:
                continue
            links = {l["type"]: l["url"] for l in item["links"]}
            channel = ("twitch", links["twitch"]) if "twitch" in links else ("youtube", links["youtube"]) if "youtube" in links else None
            if not channel:
                continue
            entry = {"name": item["name"], "type": channel[0], "url": channel[1], "title": item["what"][lang]}
            if g["id"] == "creators" and item["name"] in src_text and cls["slug"] in item.get("plays", []):
                (authors if lang in langs else fill).append(entry)
            elif g["id"] == "watch" and cls["slug"] in item["used"] and lang in langs:
                streamers.append(entry)
    return (authors + streamers + fill)[:limit]


def board_route(board, targets):
    """Cheapest connected set of nodes from Start that includes every target (targets taken nearest-first,
    so shared path segments are reused). Node weight = its Daevanion point cost."""
    import heapq
    pos = {(n["row"], n["col"]): n for n in board["nodes"]}
    by_id = {n["id"]: n for n in board["nodes"]}
    start = next(n for n in board["nodes"] if n["auto"])
    taken, left = {start["id"]}, set(targets)

    def near(n):
        return [pos[k] for k in ((n["row"] + 1, n["col"]), (n["row"] - 1, n["col"]), (n["row"], n["col"] + 1), (n["row"], n["col"] - 1)) if k in pos]
    while left:
        dist, prev, pq = {i: 0 for i in taken}, {}, [(0, i) for i in taken]
        while pq:
            c, i = heapq.heappop(pq)
            if c > dist[i]:
                continue
            for m in near(by_id[i]):
                if c + (m["cost"] or 0) < dist.get(m["id"], 1e9):
                    dist[m["id"]], prev[m["id"]] = c + (m["cost"] or 0), i
                    heapq.heappush(pq, (dist[m["id"]], m["id"]))
        reach = [t for t in left if t in dist]
        if not reach:
            break
        t = min(reach, key=lambda x: dist[x])
        while t not in taken:
            taken.add(t)
            t = prev[t]
        left -= taken                 # the target and any others picked up on its path
    return taken


@pass_context
def board_view(ctx, cls_slug, mode):
    """One Daevanion route (data/boards/presets.json -> mode) on every board of the class, for the static board macro."""
    lang = ctx["lang"]
    skills = SKILLS[cls_slug]
    preset = BOARD_PRESETS[cls_slug][mode]
    out, total, levels, focus = [], 0, {}, set()
    for i, b in enumerate(BOARDS[cls_slug]["boards"]):
        rule = preset[str(i)] if str(i) in preset else preset.get("*")
        targets = []
        if rule:
            focus.update(rule.get("skills", []))
            targets = [n["id"] for n in b["nodes"] if (n["skill"] in rule.get("skills", [])) or (rule.get("special") and n["grade"] == 41)]
        if not rule and preset.get("_hide_empty"):
            continue
        taken = board_route(b, targets)
        r0, c0 = min(n["row"] for n in b["nodes"]), min(n["col"] for n in b["nodes"])      # crop empty rows / columns
        rows, cols = max(n["row"] for n in b["nodes"]) - r0 + 1, max(n["col"] for n in b["nodes"]) - c0 + 1
        pos = {(n["row"], n["col"]): n for n in b["nodes"]}
        nodes, lines, cost = [], [], 0
        for n in b["nodes"]:
            on = n["id"] in taken
            cost += (n["cost"] or 0) if on else 0
            sk = n["skill"] if n["skill"] in skills else None
            if on and sk:
                levels[sk] = levels.get(sk, 0) + 1
            nodes.append({"x": (n["col"] - c0 + 0.5) / cols * 100, "y": (n["row"] - r0 + 0.5) / rows * 100, "g": n["grade"], "on": on,
                          "start": n["auto"], "skill": sk, "icon": f'assets/icons/{cls_slug}/{skills[sk]["icon"]}' if sk else None,
                          "name": skills[sk][lang]["name"] if sk else n["name"][lang], "cost": n["cost"] or 0})
            for d in ((0, 1), (1, 0)):
                m = pos.get((n["row"] + d[0], n["col"] + d[1]))
                if m:
                    lines.append({"x1": n["col"] - c0 + 0.5, "y1": n["row"] - r0 + 0.5, "x2": m["col"] - c0 + 0.5, "y2": m["row"] - r0 + 0.5,
                                  "on": on and m["id"] in taken})
        total += cost
        out.append({"id": b["id"], "name": b["name"][lang], "lv": b["needLevel"], "rows": rows, "cols": cols, "cost": cost,
                    "max": sum(n["cost"] or 0 for n in b["nodes"]), "nodes": nodes, "lines": lines})
    key = sorted((s for s in levels if s in focus), key=lambda s: -levels[s])
    other = sorted((s for s in levels if s not in focus), key=lambda s: -levels[s])
    name = lambda s: skills[s][lang]["name"]
    return {"boards": out, "total": total, "key": [(s, name(s), levels[s]) for s in key], "other": [(s, name(s), levels[s]) for s in other]}


def asset_version():
    """Short hash of the CSS/JS files and preview images: added to their URLs so browsers and chat apps
    pick up a new build instead of a cached one."""
    import hashlib
    h = hashlib.sha1()
    for f in sorted([*(SRC / "assets").glob("*/*.[cj]s"), *(SRC / "assets" / "og").glob("*.jpg")]):
        h.update(f.read_bytes())
    return h.hexdigest()[:8]


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
    out.update(items_tip(lang))   # item chips inside the guide text: {{ it('{i:key}') }}
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
    e.globals.update(ASSET_V=asset_version(), tooltip_json=tooltip_json, CHANGELOG=CHANGELOG, fmt_utc=fmt_utc, fmt_day=fmt_day, s=s, sp=sp, skill_data=skill_data, icon_url=icon_url, it=it, items_tip_json=items_tip_json, board_view=board_view, BOARDS=BOARDS, SITE=SITE, watch_for=watch_for)
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
        ("week-1/", "w1_title"), ("progression/", "pg_title"), ("crafting/", "cr_title"), ("weekly/", "wk_title"), ("bosses/", "bs_title"),
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
        for path, tpl, key, data in (("week-1/", "week1.html", "week1", WEEK1), ("progression/", "guide_page.html", "prog", PROGRESSION), ("crafting/", "guide_page.html", "prog", CRAFTING), ("weekly/", "weekly.html", "weekly", WEEKLY), ("bosses/", "bosses.html", "bosses", BOSSES), ("changelog/", "changelog.html", "changelog", CHANGELOG)):
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
