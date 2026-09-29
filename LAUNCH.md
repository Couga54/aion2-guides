# Launch-day checklist (global launch — October 5, 2026)

Everything on the site that was set before launch and must be checked against the live global servers.
Work top to bottom, then rebuild (`.venv/Scripts/python tools/build.py`), check locally, add a changelog entry, push.

## 1. Timers (`data/site.json`)

- [ ] **Weekly reset** — `weekly_reset.anchor`: set the real reset time (UTC, ISO) of any past or upcoming reset,
      then `weekly_reset.confirmed: true`. This drives the reset timer on /weekly/ and /week-1/ and the
      automatic clearing of the weekly checklist. When confirmed, the "not announced yet" note disappears.
- [ ] **Launch schedule** — `events`: the Early Access event has `celebrate: true` (the launch party); after
      the first day remove the flag or keep it for the "Servers are open" card.
      Also after the launch the home panel shows them as finished; remove events that
      are no longer useful or add new ones (next patch, season events).
- [ ] **`updated`** — site-wide date shown in the footer.
- [ ] Footer text "before the global launch" — `footer_before_launch` in `data/i18n.json` (EN + RU): drop or reword.

## 2. Odyle energy (`data/site.json → energy`)

- [ ] `regen` (per tick), `interval_min` (tick length), `cap`, `chest` (cost of one chest). Values come from the EU
      test client. Check them in game; the weekly tracker computes everything from these four numbers.

## 3. Weekly content (`data/weekly.json`, `data/week1.json`)

- [ ] Weekly entry limits (`max`) — taken from KR/TW and the EU test. Check each against the global client.
- [ ] After checking, reword or remove `wk_limits` in `data/i18n.json` (the "limits come from Korean servers" note).
- [ ] First-week goals — still valid for global? Remove or add goals.
- [ ] Items from Sanya Jacuzzi's datamine video (`src: sanya` in `data/week1.json`), check in game:
      enemy-side ? marks / sealed dungeons give 1,000 AP + 2–5k stones instead of Daevanion nodes (`rift`);
      feathers nerfed, 95 for Monolith level 11 (`feathers`); Nightmare charges start at 45 (`nightmare-45`);
      Daily Dungeon / trial pass boxes (`pass-boxes`).
- [ ] **Item level route** (`roadmap` in `data/week1.json`, "After 45" on /week-1/): the thresholds 1,400 / 1,900 /
      2,100 / 2,500 / 2,800, the Drupnir guarantee (14 chests, 7 with premium), the Vakron guard tickets and the real
      name of "the Dog" dungeon. When confirmed, drop `note` (the "Datamine" tag) or reword it.

## 4. World bosses (`data/bosses.json`)

- [ ] For each boss: `respawn_min` (minutes after a kill) **or** `schedule` (fixed times). With `respawn_min` set, the
      page shows the next spawn and sends browser notifications.
- [ ] Check the list: Verteron / Altgard (Lv 45) and Lower Reshanta. Add bosses that exist on global, remove those that don't.
- [ ] Remove the `kr` reference schedules once the global ones are known.
- [ ] Reword `bs_lead` / `bs_tba` / `bs_later` in `data/i18n.json`.

## 5. Guides

- [ ] **Patch version** — `classes[].patch` in `data/site.json` (shown as "Patch: TBD" on every guide).
- [ ] **Ranger** (`src/content/ranger/*.html`, section "global"): fifth stigma slot at 45 — confirmed or not?
      Accuracy cap for Ludra on global.
- [ ] **All guides**, section "Global Season 1: what changes": replace "expected / not confirmed" statements with facts.
- [ ] **PvP** — Ranger, Assassin, Chanter, Sorcerer have PvP switched off (`modes_off` in `data/site.json`).
      Turn it back on only with a real global source; write the PvP text from that source.
- [ ] **WIP marks** — `wip` (whole guide: Sorcerer, Cleric, Elementalist) and `wip_modes` (Gladiator PvP,
      Templar PvE/PvP): remove when a solid global source is used.
- [ ] **Sources** — after re-checking a mode, update its date in `classes[].src` (shown in the guide header)
      and `classes[].updated`.

## 6. Publish

- [ ] New entry at the top of `data/changelog.json` (new `id`, so everyone sees it once).
- [ ] Rebuild, check EN + RU locally, push.
