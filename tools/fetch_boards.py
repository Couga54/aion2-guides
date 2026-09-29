"""Download Daevanion boards (node grid, costs, effects) for the given classes from questlog.gg.

  python tools/fetch_boards.py gladiator [ranger ...]

Writes data/boards/<class>.json:
  {"boards": [{"id", "name": {en, ru}, "needLevel", "order", "rows", "cols",
               "nodes": [{"id", "row", "col", "type", "grade", "cost", "auto", "name": {en, ru}, "skill", "effect": {en, ru}}]}]}
Node ids are <board id><4-digit cell number> (board 11 -> 110001, 110002, ...), one per grid cell.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_skills import slugify, trpc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "boards"


def all_pages(proc, payload):
    page, out = 1, []
    while True:
        d = trpc(proc, {**payload, "page": page})
        out += d["pageData"]
        if page >= d.get("pageCount", 1):
            return out
        page += 1


def effect_text(node):
    parts = []
    for e in node.get("effect") or []:
        if e.get("type") == "stat":
            parts.append(f'{e.get("statName")} +{e.get("statValue")}')
        elif e.get("description"):
            parts.append(e["description"])
    return "; ".join(parts) or (node.get("description") or "")


def main(classes):
    OUT.mkdir(parents=True, exist_ok=True)
    boards = [b for b in all_pages("getDaevanionBoards", {"language": "en"}) if b.get("mainCategory") in classes]
    print(f"{len(boards)} boards")
    for cls in classes:
        out = []
        for b in sorted((b for b in boards if b["mainCategory"] == cls), key=lambda b: int(b["id"])):
            info = {lang: trpc("getDaevanionBoard", {"language": lang, "id": b["id"]}) for lang in ("en", "ru")}
            # The node list search caps at 1000 results, so walk the ids: every grid cell has one (empty cells are
            # placeholders named after their id), and the ids stop after the last cell.
            items, nid_n, misses = [], int(b["id"]) * 10000 + 1, 0
            while misses < 20:
                nid = str(nid_n)
                nid_n += 1
                en = trpc("getDaevanionNode", {"language": "en", "id": nid})
                if not en:
                    misses += 1
                    continue
                misses = 0
                if en.get("boardId") != b["id"] or en.get("name") == nid:
                    continue
                ru = trpc("getDaevanionNode", {"language": "ru", "id": nid})
                skill = None
                if en.get("mainCategory") == "skilllevel" and " - " in en["name"]:
                    skill = slugify(en["name"].split(" - ", 1)[1])
                items.append({"id": nid, "row": en["row"], "col": en["col"], "type": en.get("nodeType") or en.get("mainCategory"),
                              "cat": en.get("mainCategory"), "grade": en.get("grade"), "cost": en.get("costDaevanionPoint"),
                              "auto": bool(en.get("isAutoLearn")), "name": {"en": en["name"], "ru": ru.get("name") or en["name"]},
                              "skill": skill, "effect": {"en": effect_text(en), "ru": effect_text(ru)}, "raw": en.get("effect")})
            out.append({"id": b["id"], "name": {"en": info["en"]["name"], "ru": info["ru"]["name"]},
                        "needLevel": info["en"].get("needLevel"), "order": info["en"].get("order"),
                        "rows": max((n["row"] for n in items), default=0) + 1, "cols": max((n["col"] for n in items), default=0) + 1,
                        "nodes": sorted(items, key=lambda n: (n["row"], n["col"]))})
            print(f'{cls} {b["name"]}: {len(items)} nodes')
        (OUT / f"{cls}.json").write_text(json.dumps({"boards": out}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
