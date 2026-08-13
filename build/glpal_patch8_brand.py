#!/usr/bin/env python3
"""
Patch 8 - rebrand to "Titrate".

Runs on the output of glpal_patch7_dates.py. The upstream author granted
permission to rehost on the condition that the branding changes; this stage
implements that condition in the bundle, and build_fork.py handles the static
shell (title, manifest) and icons.

Deliberately NOT changed
------------------------
`super("GLPalDB")` - the IndexedDB database name. It is not user-visible
(devtools only), and renaming it would orphan existing records unless all eight
object stores were migrated on first launch. Data compatibility wins; the
branding condition concerns what users see.

Usage:
  python glpal_patch8_brand.py glpal-index-dates.js titrate-index.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "13971fbc564d4b3df7c6317ad65843b64d1b5c58ea9fc1fcc07b6efcfd68e67f"
EXPECTED_OUTPUT_SHA256 = "4d5953e0277df472e98da30315afda51bee0bab43de9b2021844bf03a10e148a"

BRAND = "Titrate"

REPLACEMENTS = [
    # visible wordmark in the app header
    ('style:{color:"inherit",textDecoration:"none"},children:"GLPal"})',
     'style:{color:"inherit",textDecoration:"none"},children:"' + BRAND + '"})',
     "header wordmark"),
    # Google Drive backup folder name
    ('const t="GLPal Backups"',
     'const t="' + BRAND + ' Backups"',
     "Drive backup folder name"),
    # the caption describing that folder
    ('children:\'Backups are saved to "GLPal Backups" folder in your Google Drive.\'',
     'children:\'Backups are saved to "' + BRAND + ' Backups" folder in your Google Drive.\'',
     "Drive backup caption"),
]

KEEP = 'super("GLPalDB")'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch8_brand.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified date-patched bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    for old, new, label in REPLACEMENTS:
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {n}")
        text = text.replace(old, new, 1)

    # the database name must survive untouched
    if text.count(KEEP) != 1:
        raise RuntimeError("the GLPalDB database name was altered; data compatibility would break")

    remaining = text.count("GLPal")
    if remaining != 1:
        raise RuntimeError(f"expected exactly 1 remaining GLPal (the DB name), found {remaining}")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print(f"rebranded {len(REPLACEMENTS)} strings; GLPalDB retained")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
