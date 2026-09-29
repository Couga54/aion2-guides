# AION 2 Guides

Static multi-class guide site (EN/RU) for AION 2 global Season 1, built with Python + Jinja2 into `docs/` for GitHub Pages.

Read `CONTEXT.md` first — it has the user's requirements, verified game facts and the site architecture.

- Build: `.venv/Scripts/python tools/build.py` (create the venv with `python -m venv .venv` and `pip install -r requirements.txt` if missing)
- Preview: `python -m http.server 8000 --directory docs`
- Refresh skill data/icons: `.venv/Scripts/python tools/fetch_skills.py gladiator ranger templar assassin chanter sorcerer cleric elementalist`
- Refresh class art: `.venv/Scripts/python tools/fetch_art.py`
- Refresh item icons/names for the progression page: `.venv/Scripts/python tools/fetch_items.py` (search: `--find <name>`)
- Save a video transcript: `.venv/Scripts/python tools/fetch_transcript.py <video id>` → `data/transcripts/`
- Launch day (Oct 5): work through `LAUNCH.md` — every value that must be checked against the live servers.
- Do not push without the user's explicit go-ahead; they check locally first.
- Every guide text exists in both `src/content/<class>/en.html` and `ru.html` — change both.
