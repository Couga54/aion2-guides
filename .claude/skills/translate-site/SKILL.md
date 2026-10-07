---
name: translate-site
description: Translate approved English changes on the AION 2 guide site into the other languages (RU, UK, TR; FR when it is added) - only the strings and guide lines that changed, with the site's glossary and rules, then check that every language is in step with English. Use after the user approves an English-only change and says "перекладай", "переклади на інші мови", "translate", or "додай французьку".
---

# Translate approved English changes

New content is written in English first (see `CLAUDE.md`). After the user approves it, this skill brings every
other language in step. **Translate only what changed** - never re-translate whole files: it costs tokens and
undoes hand fixes and native speakers' PRs.

Small fixes (a typo, a number, a renamed item) are not this skill: they go into all languages at once.

## 1. Find what changed

```bash
.venv/Scripts/python tools/i18n_check.py                # working tree vs the last commit
.venv/Scripts/python tools/i18n_check.py --since <ref>  # if the English was already committed
```

It lists:
- **data strings** whose `"en"` is new or changed, and which languages still hold the old text (`not updated`)
  or have none (`missing`). `data/i18n.json` keys are listed by key;
- **guide lines** changed in `src/content/<class>/en.html` (line ranges);
- **missing languages** and **guide skeleton** problems (see step 4).

Read only those strings / line ranges (and a few lines around them for context) in EN and in every target language.

## 2. Translate

Work per file, all target languages in one pass. Edit the target files in place:

- **Guides** (`src/content/<class>/<lang>.html`): the line numbers in every language match `en.html`
  line by line. Change the same lines; keep the template tags exactly as in English (macro calls, slugs,
  `picks`, `then=`, `hotbar(...)` / `hotline(...)` lists, `upto=`). Translate only string arguments that are
  visible text (section titles, `badge` texts) and the HTML text between tags.
- **Data** (`data/*.json`): set the `"ru"`, `"uk"`, `"tr"` values of the listed strings. New strings: put
  `"tr"` right after `"uk"` and keep the hand-formatted layout - edit the text in place, never re-dump the file
  with `json.dumps`.
- HTML inside strings (`<strong>`, `<a>`, `{{ s('slug') }}`, `{{ it('{i:key}') }}`) stays as in English;
  only the text is translated.

### Language rules

| | Game names (skills, items, sets, bosses, zones, boards, classes) | Our text |
|---|---|---|
| **ru** | Official names of the global RU client (questlog `ru`); class names: `glossary.md` | Russian |
| **uk** | **English**, as in the EN text | Ukrainian |
| **tr** | **English**, as in the EN text | Turkish |
| **fr** | Official names of the global FR client if questlog has `fr`, else English (ask the user) | French |

- Inline `{{ s('slug') }}` / `{{ it(...) }}` already print the right name per language - never write the name
  next to them by hand.
- Numbers: four digits without a space (`1600`), bigger ones grouped (`12 000`); decimal comma in RU/UK/TR.
- Keep the meaning and the amount of detail of English; do not add advice that is not in the EN text.
- Tone: short, direct, informal second person, as the site already writes: RU «Бери», «Ставь»; UK «Бери», «Візьми»;
  TR «al», «koy» (not «Берите», «Беріть», «alın»).
- Terms: **use `glossary.md`** (same folder). A term that is not there - look at how the site already says it
  (`grep` in that language's files) and keep that; add new recurring terms to the glossary.

## 3. Proofread Russian

Run the `ru-check` skill on the new / changed Russian text (only those strings, not whole files) and apply the
findings that fit a game guide (game slang from the glossary such as «бафф», «КД», «агр» is allowed).
NBSP after one-letter words and before dashes is added at build time (`typograph()` in `tools/build.py`) -
do not insert NBSP characters into the sources.

## 4. Check

```bash
.venv/Scripts/python tools/i18n_check.py --all
.venv/Scripts/python tools/build.py
```

- `Missing languages: none` and `Guide skeleton ... ok` are required (exit code 0).
- `(note) skill/item mentions differ` is informational: a translation may name a skill with `s()` where English
  only describes it. Look at the lines you touched; leave older notes alone.
- Open one changed page per language in the preview (`preview_start` name `site`) when layout could break
  (long Turkish / Russian words in buttons, chips, table headers).

Then tell the user what was translated (files, number of strings) and wait for "Коміт і пуш".

## Adding a language (e.g. French)

1. `data/site.json` → `langs`: add `"fr"`; `tools/build.py`: add it to `TEXT_FALLBACK` (`"fr": "en"`) and,
   if questlog has no French, to `DATA_LANG`.
2. `data/i18n.json`: a `"fr"` block with every key of `"en"`.
3. Every `{"en": ...}` string in hand-written `data/*.json`: a `"fr"` value after `"tr"` (`i18n_check.py` lists the
   ones missing once `fr` is in `langs`).
4. `src/content/<class>/fr.html` for every class: same lines and tags as `en.html`.
5. Add a French column to `glossary.md`, translate in batches (one file per step), run step 4 after each batch.
6. A What's new entry in every language.
