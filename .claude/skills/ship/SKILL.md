---
name: ship
description: Commit and push the AION 2 guide site - check dates, What's new, translations and secrets with tools/preflight.py, build, commit as Couga54 and push to GitHub Pages. Use ONLY when the user explicitly says "Коміт і пуш" (or "commit and push", "пуш"). Never on your own initiative and never on a vague "давай" / "+".
---

# Commit and push

The user checks locally first; a push publishes the site (GitHub Pages from `docs/`). Run this only on an explicit
"Коміт і пуш". "Давай", "так", "+" after a proposal mean "do the work", not "push" - ask if unsure.

## 1. Check

```bash
.venv/Scripts/python tools/preflight.py
```

It compares the working tree and local commits with `origin/main` (what is live) and prints:

- **ERROR** - fix before committing:
  - source material in git (`frames/`, videos) or something that looks like a token. **Never commit the Telegram bot
    token** (it lives only in Cloudflare Worker secrets) or any key;
  - site `updated` not today when `src/` or `data/` changed;
  - a class whose `en.html` (or leveling / board data) changed but `classes[].updated` is not today;
  - more than one new What's new entry, the new entry not first, an item that repeats an already published one,
    an item without `ru` / `uk` / `tr`;
  - `tools/i18n_check.py` found a missing language or a broken guide skeleton.
- **WARN** - decide:
  - no new What's new entry. Small fixes do not get one; a real change does - **one entry per push**, only what
    changed in this push, never items that were already published (memory: changelog-only-real-changes);
  - a published entry was edited or got new items. Visitors who closed the popup will not see added items - new items
    go into a new entry with a new `id` (`YYYY-MM-DD`, or `YYYY-MM-DD-topic` for a second push that day);
  - translations "same as en" / "unchanged" - run the `translate-site` skill or confirm the line needs no change.
- **NOTE** - reminders: `src` dates per mode (update a mode's date only if its source was re-checked),
  `tools/make_og.py` after a title / lead / header art change, build, `data/sources.json` for a new source.

Fix with `tools/jedit.py` (keeps the hand-formatted JSON layout), e.g.
`.venv/Scripts/python tools/jedit.py set data/site.json updated '"2026-10-07"'`. Re-run until there are no errors.

## 2. Build

```bash
.venv/Scripts/python tools/build.py
```

`docs/` is committed - always build right before the commit so it matches the sources. If the build fails, stop and fix.
The build also prints `guide check:` lines (`tools/lint_guides.py`: specialization slots, unknown skill / item slugs) -
fix them before committing.

## 3. Commit

```bash
git add -A
git status --short          # look: no frames/, no stray files from the scratchpad
git -c user.name=Couga54 commit -m "<message>"
```

Message: one line in English, what changed for a reader of the site, the same style as `git log --oneline -5`:
the biggest change first, details after a colon, parts joined with "; ", ends with "What's new entry" when there is
one. Do not mention private things the user asked to keep out (e.g. the Cleric easter egg).

## 4. Push and report

```bash
git push
```

Then tell the user in Ukrainian: the short hash, what went in (3-6 bullets), that GitHub Pages updates in a minute or
two, anything that is still open. If a local preview server is running, say so (or stop it if they asked).
