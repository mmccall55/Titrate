#!/usr/bin/env python3
"""
Generate the Titrate icon set into brand/.

A 'T' monogram in the app's existing accent purple on its dark background, so the
icon matches the UI it opens. Icons are declared "any maskable" in the manifest,
so the glyph stays inside the central safe zone that survives Android's circular,
squircle, and rounded-square masks.

Outputs: brand/logo512.png, brand/logo192.png, brand/favicon.ico
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "brand"
BG = (26, 24, 21, 255)        # #1A1815  app background
FG = (214, 154, 90, 255)     # #D69A5A  app accent
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LETTER = "T"
SAFE = 0.52                   # glyph height as a fraction of canvas (maskable safe zone)


def font_at(size):
    for path in (FONT, FALLBACK):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise SystemExit("no usable font found")


def render(px):
    img = Image.new("RGBA", (px, px), BG)
    d = ImageDraw.Draw(img)

    # rounded-square plate, slightly lighter than the background, for definition
    # on light home screens without relying on the mask
    pad = int(px * 0.06)
    d.rounded_rectangle([pad, pad, px - pad - 1, px - pad - 1],
                        radius=int(px * 0.22), fill=(33, 30, 27, 255))

    # size the glyph by measured bbox so it is optically centred, not box-centred
    target = px * SAFE
    size = int(target)
    for _ in range(24):
        f = font_at(size)
        box = d.textbbox((0, 0), LETTER, font=f)
        h = box[3] - box[1]
        if h <= 0:
            break
        if abs(h - target) <= max(1, px * 0.01):
            break
        size = max(8, int(size * target / h))
    f = font_at(size)
    box = d.textbbox((0, 0), LETTER, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text((px / 2 - w / 2 - box[0], px / 2 - h / 2 - box[1]), LETTER, font=f, fill=FG)
    return img


def main():
    OUT.mkdir(exist_ok=True)
    master = render(512)
    master.save(OUT / "logo512.png")
    render(192).save(OUT / "logo192.png")

    ico = [render(s) for s in (16, 24, 32, 64)]
    ico[-1].save(OUT / "favicon.ico", format="ICO",
                 sizes=[(16, 16), (24, 24), (32, 32), (64, 64)])

    for p in sorted(OUT.iterdir()):
        print(f"  {p.name:14} {p.stat().st_size:>7,} bytes")

    # contact sheet so the small sizes can be eyeballed
    sheet = Image.new("RGBA", (16 + 512 + 16 + 192 + 16, 544), (245, 245, 248, 255))
    sheet.paste(master, (16, 16), master)
    sheet.paste(render(192), (544, 16), render(192))
    x = 544
    for s in (64, 32, 24, 16):
        im = render(s)
        sheet.paste(im, (x, 224), im)
        x += s + 12
    sheet.save("/tmp/icon-preview.png")


if __name__ == "__main__":
    main()
