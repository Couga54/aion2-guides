# AION 2 Guides

Class guides for **AION 2 global Season 1** in English and Russian: PvE and PvP builds plus an interactive leveling checklist, with skill data taken from the global client.

**Live site:** https://couga54.github.io/aion2-guides/

| Class | Status |
|---|---|
| Gladiator | ✅ PvE · PvP · Leveling |
| Ranger | ✅ PvE · PvP · Leveling |
| Templar, Assassin, Sorcerer, Elementalist, Cleric, Chanter | coming soon |

## How it's built

A small Python static-site generator (Jinja2) renders everything into `docs/`, which GitHub Pages serves.

```
data/
  site.json              classes, languages, launch date
  i18n.json              UI strings (EN / RU)
  skills/<class>.json    skill names, descriptions, specializations (generated)
  leveling/*.json        leveling checklist: shared route + per-class steps
src/
  templates/             base, home, class page, macros
  content/<class>/       en.html and ru.html — the guide text
  assets/                css, js, icons, class emblems, OG images
tools/
  build.py               data + templates → docs/
  fetch_skills.py        pulls skill data and icons from questlog.gg (global client)
  make_og.py             social preview images
docs/                    build output (committed, published)
```

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

On macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python`.

## Build and preview

```bash
.venv/Scripts/python tools/build.py
python -m http.server 8000 --directory docs
```

Then open http://localhost:8000.

## Adding a class

1. Fetch its skills: `.venv/Scripts/python tools/fetch_skills.py <class>`
2. Write `src/content/<class>/en.html` and `ru.html` (copy an existing class as a template).
3. Add class steps to `data/leveling/<class>.json`.
4. Set `"status": "ready"` (plus `accent`, `weapon`, `difficulty`, `pitch`) for the class in `data/site.json`.
5. Run `tools/make_og.py`, then `tools/build.py`.

In the guide text, `{{ s('skill-slug') }}` renders a skill with its icon and name in the page language. In leveling steps, `[[skill-slug]]` gives the skill name and `[[skill-slug#N]]` its N-th specialization.

## Publishing

Push to `main`, then in **Settings → Pages** choose **Deploy from a branch**, branch `main`, folder `/docs`.

## Credits

Unofficial fan site, not affiliated with NCSOFT. AION 2 and its skill icons are © NCSOFT. Skill data comes from [questlog.gg](https://questlog.gg/aion-2/). Each guide lists its own sources.
