#!/usr/bin/env python3
"""
Patch 7 - fix the date off-by-one in DISPLAY code only.

Runs on the output of glpal_patch.py, so the verified six-fix chain is
untouched and this change can be reviewed or dropped independently.

The bug
-------
`new Date("2026-08-10")` parses as UTC midnight. Rendering that through
toLocaleDateString in a negative-offset timezone shows the previous day, so
every US user sees each dose dated one day early. Stored data is correct.

Why display sites only
----------------------
Three sites do `new Date(r.date)` -> `setTime(+offset)` ->
`toISOString().split("T")[0]`. UTC-parse paired with UTC-serialize round-trips
correctly today. Switching those to local parsing would return the previous day
in POSITIVE-offset zones (Tokyo), turning a cosmetic bug in the Americas into a
data bug in Asia. So only expressions that feed toLocaleDateString are changed;
every parse feeding toISOString is deliberately left alone.

The helper mirrors the idiom already present upstream (`new Date(K,Z-1,U)` after
splitting on "-"), and falls back to plain `new Date(v)` for anything that is not
a bare YYYY-MM-DD string.

Usage:
  python glpal_patch7_dates.py glpal-index-editable.js glpal-index-dates.js
"""

from pathlib import Path
import hashlib
import re
import sys

EXPECTED_INPUT_SHA256 = "dbea7baaff958b56a4567c1a984c9b7a46ef696b792412bd1279e7433f75236e"
EXPECTED_OUTPUT_SHA256 = "13971fbc564d4b3df7c6317ad65843b64d1b5c58ea9fc1fcc07b6efcfd68e67f"

HELPER = (
    'function __glpalLocalDate(v){'
    'if(typeof v=="string"){'
    'const m=/^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(v);'
    'if(m)return new Date(+m[1],+m[2]-1,+m[3])}'
    'return new Date(v)}'
)

# Display sites only. Single-argument calls: the 3-argument
# `new Date(K,Z-1,U)` form is already correct and is excluded by the
# no-comma character class.
DIRECT = re.compile(r'new Date\(([^(),]{1,30})\)\.toLocaleDateString')

# One site parses into a local first and formats on the next statement.
TWO_STEP_OLD = 'const te=new Date(ne.date),ie=te.toLocaleDateString'
TWO_STEP_NEW = 'const te=__glpalLocalDate(ne.date),ie=te.toLocaleDateString'

ANCHOR = ';const y0e='


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch7_dates.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified six-fix bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}"
        )

    text = raw.decode("utf-8")

    # 1. insert the helper as a hoisted function declaration at statement level
    if text.count(ANCHOR) != 1:
        raise RuntimeError(f"anchor {ANCHOR!r} found {text.count(ANCHOR)} times, expected 1")
    text = text.replace(ANCHOR, ";" + HELPER + "const y0e=", 1)

    # 2. two-step display site
    if text.count(TWO_STEP_OLD) != 1:
        raise RuntimeError(f"two-step site found {text.count(TWO_STEP_OLD)} times, expected 1")
    text = text.replace(TWO_STEP_OLD, TWO_STEP_NEW, 1)

    # 3. direct display sites
    sites = DIRECT.findall(text)
    if len(sites) != 9:
        raise RuntimeError(f"expected 9 direct display sites, found {len(sites)}: {sites}")
    text = DIRECT.sub(lambda m: f"__glpalLocalDate({m.group(1)}).toLocaleDateString", text)

    # guard: no toISOString path may have been touched
    for bad in re.finditer(r'__glpalLocalDate\([^()]{0,30}\)[^;]{0,60}toISOString', text):
        raise RuntimeError("a toISOString path was modified: " + bad.group(0)[:80])

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print(f"replacements: 1 helper + 1 two-step + {len(sites)} direct")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
