---
name: find-guides
description: Find fresh, popular AION 2 guide videos on YouTube for a class or a topic (views, likes, date, author), mark the ones already used on the site, and suggest which are worth processing. Use when the user asks to look for new / fresh guides, "пошукай гайди", "чи є свіжі гайди", "знайди гайд по <класу>".
---

# Find fresh guides

The user wants guides with **many views and likes**, not random videos. Global client guides are preferred;
English and Russian authors both count.

## 1. Search

```bash
.venv/Scripts/python tools/find_guides.py <class>                     # this week, English
.venv/Scripts/python tools/find_guides.py <class> --lang ru
.venv/Scripts/python tools/find_guides.py <class> --period month      # if the week is thin
.venv/Scripts/python tools/find_guides.py "<topic>" --period any      # e.g. "gear after 45", "dungeon"
```

Run the English and Russian searches together (two commands in one message). Several classes: one command per class,
all in one message. Each call takes ~3 s per video (`--top`, default 10).

Marks: `USED` - already linked on the site (skip unless the user asks to re-check); `AUTHOR` - a creator we already
cite (a new video from them is a likely update); `KR/TW?` - another client: only if nothing global exists, and say so;
`STREAM` - a long stream, not a guide (skip).

## 2. Pick

Worth proposing: a real guide (build, skills, macro, rotation, gear, PvP), global client, high views for its age and a
like ratio around 1% or more. Compare with what the class guide already uses (`data/site.json` → `classes[].src`,
`data/sources.json`). Do not propose TitanTheF as a class guide source (he stays only in the source lists).

## 3. Report

A short list in Ukrainian, best first: author, title (shortened), views / likes / date, link, and one line why it is
worth it (what it could add or change in our guide). Then ask which to process; processing follows the
`guide-from-video` skill and changes nothing before the user agrees.
