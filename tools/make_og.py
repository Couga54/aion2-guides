"""Render social preview images (1200x630) into src/assets/og/.

  python tools/make_og.py

One image for the home page and one per ready class, in every language.
Needs Pillow and fonts with Cyrillic (Georgia / Segoe UI on Windows, DejaVu elsewhere).
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "assets" / "og"
SITE = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
I18N = json.loads((ROOT / "data" / "i18n.json").read_text(encoding="utf-8"))
W, H = 1200, 630
BG = (11, 14, 20)
GOLD = (217, 179, 108)
ACCENTS = {"crimson": (200, 50, 60), "emerald": (40, 170, 115), "sapphire": (60, 110, 230), "amber": (220, 140, 40), "violet": (140, 80, 230), "frost": (40, 170, 210), "sunlight": (235, 205, 110), "spirit": (225, 80, 180)}


def font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


SERIF = ["georgiab.ttf", "georgia.ttf", "DejaVuSerif-Bold.ttf"]
SANS = ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
MONO = ["consolab.ttf", "DejaVuSansMono-Bold.ttf"]


def glow(color, cx, cy, r):
    layer = Image.new("RGB", (W, H), BG)
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    return layer.filter(ImageFilter.GaussianBlur(r // 2))


def base(accent):
    img = Image.blend(Image.new("RGB", (W, H), BG), glow(accent, 1050, 40, 380), 0.55)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 26):           # dot grid, fading downwards
        for y in range(0, 300, 26):
            a = int(34 * (1 - y / 300))
            d.point((x, y), fill=(BG[0] + a, BG[1] + a, BG[2] + a))
    return img


def wrap(d, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def emblem(img, slug, x, y, size):
    em = Image.open(ROOT / "src" / "assets" / "classes" / f"{slug}.webp").convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=255)
    ImageDraw.Draw(img).rounded_rectangle((x - 3, y - 3, x + size + 2, y + size + 2), radius=size // 5 + 3, fill=GOLD)
    img.paste(em, (x, y), mask)


def render_class(cls, lang):
    t = I18N[lang]
    img = base(ACCENTS[cls["accent"]])
    d = ImageDraw.Draw(img)
    emblem(img, cls["slug"], 80, 90, 170)
    d.text((290, 100), t["home_kicker"].upper(), font=font(MONO, 26), fill=GOLD)
    d.text((286, 135), cls["name"][lang], font=font(SERIF, 104), fill=(245, 240, 230))
    y = 300
    for line in wrap(d, cls["pitch"][lang], font(SANS, 34), 1020)[:3]:
        d.text((80, y), line, font=font(SANS, 34), fill=(200, 205, 215))
        y += 46
    chips = f'{t["mode_pve"]}  ·  {t["mode_pvp"]}  ·  {t["mode_lvl"]}'
    d.text((80, 520), chips, font=font(MONO, 30), fill=GOLD)
    d.text((W - 80, 520), t["site_name"], font=font(SERIF, 34), fill=(200, 205, 215), anchor="ra")
    return img


def render_home(lang):
    t = I18N[lang]
    img = base((160, 130, 70))
    d = ImageDraw.Draw(img)
    d.text((80, 90), t["home_kicker"].upper(), font=font(MONO, 26), fill=GOLD)
    y = 135
    for line in wrap(d, t["home_h1"], font(SERIF, 78), 1040)[:2]:
        d.text((76, y), line, font=font(SERIF, 78), fill=(245, 240, 230))
        y += 92
    x = 80
    for c in SITE["classes"]:
        emblem(img, c["slug"], x, 400, 104)
        if c["status"] != "ready":
            ov = Image.new("RGB", (104, 104), BG)
            img.paste(Image.blend(img.crop((x, 400, x + 104, 504)), ov, 0.55), (x, 400))
        x += 130
    d.text((80, 545), t["site_name"], font=font(SERIF, 34), fill=(200, 205, 215))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in SITE["langs"]:
        render_home(lang).save(OUT / f"home-{lang}.jpg", quality=86, optimize=True, progressive=True)
        for c in SITE["classes"]:
            if c["status"] == "ready":
                render_class(c, lang).save(OUT / f'{c["slug"]}-{lang}.jpg', quality=86, optimize=True, progressive=True)
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.jpg"))))


if __name__ == "__main__":
    main()
