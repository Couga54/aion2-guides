---
name: guide-from-video
description: Update an AION 2 class guide (or the progression / crafting / first week pages) from a YouTube guide video - download the video, get the transcript, storyboard it, analyse what is said and shown, compare with the current guide, propose changes and apply them after the user agrees. Use when the user gives a YouTube link or id and asks to analyse it, compare it with a guide, "онови гайд по відео", "проаналізуй відео", or to add a new guide source.
---

# Update a guide from a YouTube video

The user gives one or more YouTube links (or ids) and usually the class. The goal is a list of proposed
changes to the existing guide, then - only after the user agrees - the changes themselves.

**Ask, don't assume.** Steps 1-6 are analysis: change nothing in `src/` or `data/` until the user has agreed to the proposals. If the class, the mode (PvE / PvP / leveling) or the
game version (global, KR, TW) of the video is unclear, ask.

## 1-3. Prepare the video (one command)

```bash
.venv/Scripts/python tools/video_guide.py <youtube url or id> [more ...]
```

It runs three tools; each can also be run on its own:

| Step | Tool | Result |
|---|---|---|
| 1. Video, Full HD, no sound | `tools/fetch_video.py <id>` | `frames/<id>/video.<ext>`, `video.json` (title, channel, channel url, upload date, duration) |
| 2. Transcript | `tools/fetch_transcript.py <id>` | `frames/<id>/transcript.json` - `rows: [{t: seconds, text}]` |
| 3. Storyboard | `tools/storyboard.py <id>` | `frames/<id>/f/<seconds>.jpg`, `sheets/sheetNN.jpg`, `index.json` |

- The frame step is picked from the length: every second up to 8 min, 2 s up to 16 min, 3 s up to 30 min,
  4 s for longer. Override with `--every N` (e.g. `--every 1` for a fast video full of build screens).
  Frames that look the same as the previous kept one are dropped.
- Everything for a video lives in `frames/<id>/`, which is git-ignored: the video, the transcript and the frames
  stay local and are never committed. The same goes for any screenshot or file saved from a creator's guide:
  put it in `frames/<id>/`, never under `data/`, `src/` or `docs/`. `video.*` can be deleted once the analysis is done; keep the rest for re-checks.
- If the download fails, update yt-dlp first (`.venv/Scripts/python -m pip install -U yt-dlp`). If it still
  fails, or the video has no transcript, tell the user: they can put their own file through
  `tools/storyboard.py <file> <id>`.
- No transcript: the storyboard still works, the sheets just have no caption lines. Say so in the analysis -
  the conclusions then rest on the picture only.

## 4. Analyse transcript + frames

1. Read the whole transcript (`frames/<id>/transcript.json`). Note the sections with their timestamps.
2. Read **every** contact sheet in `frames/<id>/sheets/` (30 frames each, timestamp + the line spoken at
   that moment under each frame). The picture is often more exact than the words: skill bars, stigma
   builds, Daevanion boards, stat screens, gear, arcana, settings menus.
3. For every screen that carries data, take full-size frames and read the numbers and names from them,
   never from the small thumbnails:
   `.venv/Scripts/python tools/storyboard.py <id> --at 7:45 465` -> `frames/<id>/hd/t<seconds>.jpg`
4. Match what is shown with what is said at the same timestamp. When they disagree, trust the screen and
   note the conflict.
5. Write down for the video: author, channel, upload date, game version / server (global beta, KR, TW),
   the class and whether the author actually plays it, the modes covered, and the facts with timestamps:
   skill priorities and levels, specializations, stigmas, rotation / opener, gear and stats, arcana,
   Daevanion route, leveling route, settings, tips.

Skill, item and stat names: use the official ones from `data/skills/<class>.json` and `data/items.json`
(EN and RU), not the author's nicknames. For a new item, `tools/fetch_items.py --find <name>`.

## 5. Compare with the current guide

Read `CONTEXT.md` (verified facts and rules), then the current text: `src/content/<class>/en.html` and
`ru.html`, the class entry in `data/site.json`, `data/boards/presets.json` when the video shows Daevanion
boards, and `data/progression.json` / `data/crafting.json` for general advice. Sort every finding:

- **New** - the guide does not have it.
- **Conflict** - the guide says otherwise. Give both versions, which source each comes from, and which is
  stronger (global over KR/TW, newer over older, a main of the class over a general channel, the screen
  over the words).
- **Confirmed** - the same as in the guide (one line, it matters for the "checked" date).
- **Not for the guide** - opinion, KR/TW-only, outdated, off topic.

## 6. Propose the changes

Give the user a short list, grouped by guide section and mode, each item with: what changes, where, the
timestamp (and frame) it comes from, and the recommendation. Put the conflicts and the questions first.
Then stop and wait. Nothing is edited before the user agrees; they may accept only a part.

## 7. Apply after the go-ahead

Write the text in our own words - facts and numbers from the video, never its sentences.

- [ ] Guide text in **both** `src/content/<class>/en.html` and `ru.html`.
- [ ] Data the text leans on: `data/boards/presets.json`, `data/class_items.json` + `tools/fetch_items.py`,
      `data/progression.json` / `data/crafting.json` (their `sources` with `video` and timestamps in `at`).
- [ ] `data/site.json`, the class: `updated` = today; `src.<mode>` = `["<authors>", "<today>"]` for every
      mode that was re-checked against the video (add the author's name if new); site-wide `updated` = today.
- [ ] `data/sources.json`, group `creators`: the author with `name` exactly as written in `classes[].src`,
      `lang`, `plays` (the one class they main - a creator is shown in "Who to watch" for a single class even
      if they make guides for several; `[]` for general channels such as Grobs), channel links, `used` classes; the video itself among the sources.
- [ ] `wip` / `wip_modes` / `modes_off` in `site.json` if the video makes a mode solid (or opens a new one).
- [ ] `data/changelog.json`: a What's new entry (EN + RU) with a new id - what changed for the reader.
- [ ] `LAUNCH.md`: every value taken on trust that must be checked on the live servers.
- [ ] Build (`.venv/Scripts/python tools/build.py`) and check the page in the preview.
- [ ] Social preview (`tools/make_og.py`) only if a title, lead or header art changed.
- [ ] Report what was changed. **No commit and no push** until the user says so.
