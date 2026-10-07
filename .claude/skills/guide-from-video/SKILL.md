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
- No transcript on YouTube (fresh upload, captions switched off): make one locally with
  `.venv/Scripts/python tools/transcribe.py <id> --lang en` (needs `pip install faster-whisper`; about 10 minutes per hour of
  video on the CPU), then run `tools/storyboard.py <id>` again to put the lines on the sheets. Speech recognition mishears
  game terms ("hug off" = Heart Gore) - take every skill name and number from the frames, and say in the analysis that the
  transcript is machine-made.

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

### 4a. Hotbar and macro (every class video)

Every class guide built or updated from a video gets the game-like hotbar panel, so read the author's bar even if the
video does not talk about it.

1. Find on the sheets the moments where the whole hotbar is visible and calm (no cast animation, no tooltip over it);
   for a mode switch (leveling vs endgame, PvE vs PvP) the author may show two bars - note which is which.
2. Enlarge the bar and make the reference sheet of the class's icons:
   ```bash
   .venv/Scripts/python tools/hotbar_kit.py crop <id> <mm:ss> <x0> <y0> <x1> <y1> --scale 2   # 1920x1080 coordinates
   .venv/Scripts/python tools/hotbar_kit.py icons <class>                                    # frames/_icons/<class>.jpg
   ```
   Match every slot against `frames/_icons/<class>.jpg`; when two icons look alike, take another frame (the moment a
   skill is cast or its tooltip is open) instead of guessing.
3. Read each key's column **from the bottom up**: the bottom slot fires first (highest priority), so the list in
   `hotbar()` / `hotline()` starts with the bottom skill. Getting this order backwards is the usual mistake - check
   it against a frame where the line is used.
4. Write the bar down as it is, all three groups: keys 1–4, 5–8, then Q / E / mouse buttons / T (whatever the author
   uses), empty keys and empty slots included.
5. The in-game macro (Settings → Key Settings → General → Macro; RU client «Настройки → Клавиши → Общее → Связка»):
   which keys it presses and in what order, and the key the author binds it to (we recommend RMB). Note the lines that
   are **not** in the macro too (buffs, debuffs like Debilitating Mark, emergency skills) - the panel shows them.
6. Skill picks seen on the bar or in the skill window, with the level: a third pick at 20 goes to `then=[i]`.

If no frame shows the bar for a mode, say so in the analysis; never fill a panel from the transcript alone.

## 5. Compare with the current guide

Read `CONTEXT.md` (verified facts and rules), then the current text: `src/content/<class>/en.html` only (the other
languages repeat it line by line - no need to read them), the class entry in `data/site.json`, `data/boards/presets.json` when the video shows Daevanion
boards, and `data/progression.json` / `data/crafting.json` for general advice. Sort every finding:

- **New** - the guide does not have it.
- **Conflict** - the guide says otherwise. Give both versions, which source each comes from, and which is
  stronger (global over KR/TW, newer over older, a main of the class over a general channel, the screen
  over the words).
- **Confirmed** - the same as in the guide (one line, it matters for the "checked" date).
- **Not for the guide** - opinion, KR/TW-only, outdated, off topic.

Always compare the hotbar and the macro (step 4a) with the guide's `hotbar(...)`, `hotline(...)` and `macroseq(...)`
calls in the macro section of each mode: a different line order or a different set of skills on a key is a conflict.

## 6. Propose the changes

Give the user a short list, grouped by guide section and mode (the hotbar panel and the macro as their own item), each item with: what changes, where, the
timestamp (and frame) it comes from, and the recommendation. Put the conflicts and the questions first.
Then stop and wait. Nothing is edited before the user agrees; they may accept only a part.

## 7. Apply after the go-ahead

Write the text in our own words - facts and numbers from the video, never its sentences.

**English first:** apply everything to `src/content/<class>/en.html` and the `"en"` data strings, show the user, and
translate only after they approve - with the `translate-site` skill (it finds the changed lines itself). Small
fixes (a number, a name) go into all languages at once.

- [ ] Guide text in `en.html`. Skill cards: at most 2 specialization picks below skill level 20 (1 below 12), no pick
      that unlocks above the card's level, the level-20 pick in `then=[i]`; the build checks this (`guide check:` lines).
- [ ] The macro section of every mode the video covers (section id starting with `macro` - it gets the "?" tip about
      binding the macro key): at the top `{{ hotbar([('1', [...]), ..., None, ('5', [...]), ..., None, ('Q', [...]), ...],
      macro=['Q', ...]) }}` - every key and empty slot, first slug = bottom slot, `None` between the groups, mouse keys as
      `'LMB'` / `'RMB'` (RU and UK `'ЛКМ'` / `'ПКМ'`, TR as EN); keys exactly as the author binds them; for side mouse
      buttons / numpad add `own_keys=true` (a note says to copy the lines, not the keys); every key label must be unique (`'Side'`,
      `'Side 2'`) - the gold macro columns are matched by label; then the macro steps (`macroseq`) and one `hotline(...)` per
      macro line with notes; then the lines outside the macro. The source author in the text if several are combined.
- [ ] Data the text leans on: `data/boards/presets.json`, `data/class_items.json` + `tools/fetch_items.py`,
      `data/progression.json` / `data/crafting.json` (their `sources` with `video` and timestamps in `at`).
- [ ] `data/site.json`, the class: `updated` = today; `src.<mode>` = `["<authors>", "<today>"]` for every
      mode that was re-checked against the video (add the author's name if new); site-wide `updated` = today.
- [ ] `data/sources.json`, group `creators`: the author with `name` exactly as written in `classes[].src`,
      `lang`, `plays` (the one class they main - a creator is shown in "Who to watch" for a single class even
      if they make guides for several; `[]` for general channels such as Grobs), channel links, `used` classes; the video itself among the sources.
- [ ] `wip` / `wip_modes` / `modes_off` in `site.json` if the video makes a mode solid (or opens a new one).
- [ ] `data/changelog.json`: a What's new entry (all languages after translation) with a new id - what changed for the
      reader; one entry per push, never items that are already published.
- [ ] `LAUNCH.md`: every value taken on trust that must be checked on the live servers.
- [ ] Build (`.venv/Scripts/python tools/build.py`): no `guide check:` lines; check the page in the preview (the hotbar
      panel at phone width too).
- [ ] After translation: `.venv/Scripts/python tools/preflight.py` shows no errors.
- [ ] Social preview (`tools/make_og.py`) only if a title, lead or header art changed.
- [ ] Report what was changed. **No commit and no push** until the user says so.
