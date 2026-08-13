#!/usr/bin/env python3
"""
Build the purple -> muted-orange colour map.

Every replacement preserves the original colour's WCAG relative luminance, so
all contrast ratios in the UI are unchanged; only hue and saturation move.

Target hue is taken from the supplied swatch #F58C1D (H 31 deg), with
saturation damped so it reads muted rather than safety-orange.
"""
import colorsys, json, re, sys
from collections import Counter

TARGET_HUE = 31 / 360
ACCENT_SAT_SCALE = 1.35     # accents: keep chroma, still well below the raw swatch
ACCENT_SAT_CAP = 0.80
NEUTRAL_SAT_SCALE = 0.45    # near-neutral darks: a warm hint only
NEUTRAL_CUTOFF = 0.30


def luminance(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(c))) for c in rgb))


def recolour(hexv):
    rgb = hex_to_rgb(hexv)
    target_Y = luminance(rgb)
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    s2 = min(s * ACCENT_SAT_SCALE, ACCENT_SAT_CAP) if s >= NEUTRAL_CUTOFF else s * NEUTRAL_SAT_SCALE
    lo, hi = 0.0, 1.0
    for _ in range(60):                      # solve L for equal luminance
        mid = (lo + hi) / 2
        cand = colorsys.hls_to_rgb(TARGET_HUE, mid, s2)
        if luminance([c * 255 for c in cand]) < target_Y:
            lo = mid
        else:
            hi = mid
    return rgb_to_hex([c * 255 for c in colorsys.hls_to_rgb(TARGET_HUE, (lo + hi) / 2, s2)])


def purples(paths):
    found = Counter()
    for p in paths:
        src = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'#([0-9a-fA-F]{6})\b', src):
            found["#" + m.group(1).upper()] += 1
        for m in re.finditer(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', src):
            found[rgb_to_hex([int(x) for x in m.groups()])] += 1
        # Tailwind emits space-separated triplets: rgb(192 132 252 / var(--x))
        for m in re.finditer(r'rgba?\(\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})', src):
            found[rgb_to_hex([int(x) for x in m.groups()])] += 1
        for m in re.finditer(r'#([0-9a-fA-F]{3})\b', src):
            found[rgb_to_hex([int(c * 2, 16) for c in m.group(1)])] += 1
    out = {}
    for hexv, n in found.items():
        r, g, b = hex_to_rgb(hexv)
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s > 0.05 and 240 <= h * 360 <= 310:
            out[hexv] = n
    return out


if __name__ == "__main__":
    # MUST read pristine sources. Reading fork/ would rescan an already
    # recoloured build and silently produce a partial palette.
    import tempfile, zipfile, os
    tmp = tempfile.mkdtemp(prefix="palette-src-")
    repo = Path(__file__).resolve().parent.parent
    with zipfile.ZipFile(repo / "upstream" / "glpal-upstream.zip") as z:
        z.extract("assets/index-CDUEMmyD.css", tmp)
    files = [os.path.join(tmp, "assets/index-CDUEMmyD.css"),
             str(Path(__file__).resolve().parent / ".artifacts" / "titrate-index-chart.js")]
    print(f"sources: upstream CSS (from zip) + {files[1]}\n")
    found = purples(files)
    mapping = {}
    print(f"{'original':>9} {'->':^4} {'new':<9}  {'uses':>5}  contrast-preserving")
    for hexv, n in sorted(found.items(), key=lambda kv: -kv[1]):
        new = recolour(hexv)
        mapping[hexv] = new
        y1, y2 = luminance(hex_to_rgb(hexv)), luminance(hex_to_rgb(new))
        print(f"  {hexv} ->  {new}  {n:5}x   dY={abs(y1-y2):.5f}")
    json.dump(mapping, open(Path(__file__).resolve().parent / "palette.json", "w"), indent=1)
    print(f"\nwrote palette.json  ({len(mapping)} colours)")
