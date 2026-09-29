# AION 2 Guides

Static multi-class guide site (EN/RU) for AION 2 global Season 1, built with Python + Jinja2 into `docs/` for GitHub Pages.

Read `CONTEXT.md` first — it has the user's requirements, verified game facts and the site architecture.

- Build: `.venv/Scripts/python tools/build.py` (create the venv with `python -m venv .venv` and `pip install -r requirements.txt` if missing)
- Preview: `python -m http.server 8000 --directory docs`
- Refresh skill data/icons: `.venv/Scripts/python tools/fetch_skills.py gladiator ranger templar assassin chanter sorcerer cleric elementalist`
- Refresh class art: `.venv/Scripts/python tools/fetch_art.py`
- Social previews (og images) after changing a title, lead or header art: `.venv/Scripts/python tools/make_og.py`, then build
- Daevanion boards (interactive board on class pages): `.venv/Scripts/python tools/fetch_boards.py gladiator` → `data/boards/<class>.json`;
  presets (which skills each mode takes) are in `data/boards/presets.json`; show it in a guide with `{{ dv_board('pve') }}`.
- Storyboard a guide video (frames + contact sheets with the transcript line, local `frames/<id>/`, git-ignored):
  `.venv/Scripts/python tools/storyboard.py <file.mp4> <youtube id>`; full-size frames: `... --at 7:45 465`.
- Refresh item icons/names for the guide pages (progression, crafting): `.venv/Scripts/python tools/fetch_items.py` (search: `--find <name>`)
- Save a video transcript: `.venv/Scripts/python tools/fetch_transcript.py <video id>` → `data/transcripts/`
- Launch day (Oct 5): work through `LAUNCH.md` — every value that must be checked against the live servers.
- Do not push without the user's explicit go-ahead; they check locally first.
- Every guide text exists in both `src/content/<class>/en.html` and `ru.html` — change both.
- New or updated guide source → also update its creator in `data/sources.json` (group `creators`): `name` exactly as it is written in
  `site.json → classes[].src`, `lang` (the language they make content in: `en` / `ru`), `plays` (classes they actually play — `[]` for general
  guide channels like Grobs), channel links (`twitch` / `youtube`) and `used` classes. The "Who to watch" line on class pages is built from this (`watch_for` in `tools/build.py`): same-language guide authors who play the class,
  then streamers from the `watch` group (RU), then English authors on RU pages, max 3. New streamers go into the `watch` group with `lang`.
