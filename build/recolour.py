#!/usr/bin/env python3
"""
Apply palette.json (purple -> muted orange) to the built fork.

Runs over the shipping bundle and the app stylesheet, replacing colours in
every form they appear: #RRGGBB (any case) and rgb()/rgba() triplets, including
the Tailwind arbitrary-value syntax like from-[#B19CD9].

Every mapping preserves the original's WCAG relative luminance, so contrast
ratios are unchanged - only hue and saturation move.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PALETTE = json.load(open(ROOT / "palette.json"))  # ROOT is build/


def apply(text):
    n = 0
    for old, new in PALETTE.items():
        # hex, case-insensitive
        pat = re.compile(re.escape(old), re.IGNORECASE)
        text, c = pat.subn(new, text)
        n += c
        # rgb()/rgba() triplets
        r, g, b = (int(old[i:i + 2], 16) for i in (1, 3, 5))
        nr, ng, nb = (int(new[i:i + 2], 16) for i in (1, 3, 5))
        pat2 = re.compile(r'(rgba?\(\s*)%d(\s*,\s*)%d(\s*,\s*)%d' % (r, g, b))
        text, c = pat2.subn(lambda m: f"{m.group(1)}{nr}{m.group(2)}{ng}{m.group(3)}{nb}", text)
        n += c
        # Tailwind space-separated form
        pat3 = re.compile(r'(rgba?\(\s*)%d(\s+)%d(\s+)%d' % (r, g, b))
        text, c = pat3.subn(lambda m: f"{m.group(1)}{nr}{m.group(2)}{ng}{m.group(3)}{nb}", text)
        n += c
        # 3-digit hex, only when it is an exact shorthand of this colour
        if all(x >> 4 == (x & 0xF) for x in (r, g, b)):
            short = "#{:X}{:X}{:X}".format(r >> 4, g >> 4, b >> 4)
            text, c = re.compile(re.escape(short) + r'\b', re.IGNORECASE).subn(new, text)
            n += c
    return text, n


def main(paths):
    total = 0
    for p in paths:
        p = Path(p)
        src = p.read_text(encoding="utf-8", errors="surrogateescape")
        out, n = apply(src)
        p.write_text(out, encoding="utf-8", errors="surrogateescape")
        print(f"  {p.name}: {n} colour references recoloured")
        total += n
    leftover = 0
    for p in paths:
        s = Path(p).read_text(encoding="utf-8", errors="surrogateescape")
        for old in PALETTE:
            leftover += len(re.findall(re.escape(old), s, re.IGNORECASE))
            r, g, b = (int(old[i:i + 2], 16) for i in (1, 3, 5))
            leftover += len(re.findall(r'rgba?\(\s*%d\s*[, ]\s*%d\s*[, ]\s*%d' % (r, g, b), s))
    if leftover:
        raise SystemExit(f"FAIL: {leftover} purple references remain")
    print(f"  total {total}; no purple references remain")


if __name__ == "__main__":
    main(sys.argv[1:])
