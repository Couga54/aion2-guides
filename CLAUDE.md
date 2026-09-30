# AION 2 Guides

Static multi-class guide site (EN/RU) for AION 2 global Season 1, built with Python + Jinja2 into `docs/` for GitHub Pages.

Read `CONTEXT.md` first — it has the user's requirements, verified game facts and the site architecture.

- Build: `.venv/Scripts/python tools/build.py` (create the venv with `python -m venv .venv` and `pip install -r requirements.txt` if missing)
- Preview: `python -m http.server 8000 --directory docs`
- Refresh skill data/icons: `.venv/Scripts/python tools/fetch_skills.py gladiator ranger templar assassin chanter sorcerer cleric elementalist`
- Refresh class art: `.venv/Scripts/python tools/fetch_art.py`
- Social previews (og images) after changing a title, lead or header art: `.venv/Scripts/python tools/make_og.py`, then build
- Daevanion boards (static route board on class pages; every class has the data, Elementalist has no route yet): `.venv/Scripts/python tools/fetch_boards.py <class>` → `data/boards/<class>.json` (takes a few minutes);
  presets (which skills each mode takes) are in `data/boards/presets.json`; show it in a guide with `{{ dv_board('pve') }}`.
- Update a guide from a YouTube video: follow the `guide-from-video` skill (`.claude/skills/guide-from-video/SKILL.md`) —
  prepare, analyse, compare with the guide, propose, and edit only after the user agrees. Prepare in one command:
  `.venv/Scripts/python tools/video_guide.py <youtube url or id>` = `fetch_video.py` (Full HD, no sound → `frames/<id>/video.*`,
  git-ignored) + `fetch_transcript.py` (→ `frames/<id>/transcript.json`) + `storyboard.py <id>` (frames + contact sheets with the transcript line; a frame every
  1–4 s depending on the length, `--every N` to override). Full-size frames: `tools/storyboard.py <id> --at 7:45 465`.
  A video file of your own: `tools/storyboard.py <file.mp4> <youtube id>`.
- Refresh item icons/names for the guide pages (progression, crafting): `.venv/Scripts/python tools/fetch_items.py` (search: `--find <name>`)
- **Source material stays local, never in git:** creators' guides, videos, transcripts, frames and screenshots live in
  `frames/<youtube id>/` (git-ignored). Do not save them under `data/`, `src/` or `docs/`, and do not publish them on the site —
  the repo holds only our own text, the data from questlog.gg and links to the sources.
  Transcript only: `.venv/Scripts/python tools/fetch_transcript.py <video id>` → `frames/<id>/transcript.json`.
- Launch day (Oct 5): work through `LAUNCH.md` — every value that must be checked against the live servers.
- Do not push without the user's explicit go-ahead; they check locally first.
- Every guide text exists in both `src/content/<class>/en.html` and `ru.html` — change both.
- Changed a class guide → set that class's `updated` in `data/site.json` to today (the "Updated" date in the guide header and on the
  home card), the date in `classes[].src.<mode>` for every mode whose source was re-checked, and the site-wide `updated` (footer, sitemap).
- New or updated guide source → also update its creator in `data/sources.json` (group `creators`): `name` exactly as it is written in
  `site.json → classes[].src`, `lang` (the language they make content in: `en` / `ru`), `plays` (the class they main — **one class per creator**, even if they make guides for several:
  TitanTheF writes about Ranger, Assassin and Chanter but is listed only for Ranger; more than one only for a known exception; `[]` for general
  guide channels like Grobs), channel links (`twitch` / `youtube`) and `used` classes. The "Who to watch" line on class pages is built from this (`watch_for` in `tools/build.py`): same-language guide authors who play the class,
  then streamers from the `watch` group (RU), then English authors on RU pages, max 3. New streamers go into the `watch` group with `lang`
  and one class in `used` — the same rule: a streamer is shown in "Who to watch" for one class only.
