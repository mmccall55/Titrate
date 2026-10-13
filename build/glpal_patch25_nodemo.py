#!/usr/bin/env python3
"""
Patch 25 - remove the "Load Sample Data (Demo)" button from Settings.

Symptom
    Settings -> Data Management has a "Load Sample Data (Demo)" button. One
    tap and one OK on `window.confirm("This will clear all current data and
    generate sample data. Continue?")` erases every store and replaces the
    user's log with demo data. Nothing is backed up first.

Cause
    Upstream ships the demo generator (`generateSampleData`: `J2()` clears
    every store, then `WW()` writes demo weights, profile and doses) behind a
    single confirm, rendered whenever the settings modal receives the
    `onGenerateSampleData` callback - which it always does.

Fix
    The button is rendered as `o&&S.jsxs("button", ...)`, where `o` is that
    callback. Replace the guard with `!1&&`, so the button never renders -
    the same technique patch 15 used to hide Peptides and Calculator.

What this deliberately does NOT change
    - the generator code (`WW`, `generateSampleData`), which stays in the
      bundle, unreachable from the UI
    - the other Data Management buttons (Import / Export CSV, Cloud Backup)
    - any stored data

Usage
    python glpal_patch25_nodemo.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "cb28ba6620061907c58b525223183d4918a615a471049856e72e2680da9db723"
EXPECTED_OUTPUT_SHA256 = "8334d584743780575f8f1ec04809f170feb4699f27a3df604c24a886809d22a7"

CONFIRM = ('window.confirm("This will clear all current data and generate sample data. '
           'Continue?")&&(o(),i())}')
OLD = 'o&&S.jsxs("button",{onClick:()=>{' + CONFIRM
NEW = '!1&&S.jsxs("button",{onClick:()=>{' + CONFIRM


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch25_nodemo.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-24 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    for needle, n in ((CONFIRM, 1), ("Load Sample Data (Demo)", 1), (OLD, 1),
                      ("Import / Export CSV", 1)):
        if text.count(needle) != n:
            raise RuntimeError(f"{needle[:40]!r} found {text.count(needle)} times, expected {n}")

    text = text.replace(OLD, NEW, 1)

    if text.count(NEW) != 1 or OLD in text:
        raise RuntimeError("guard replacement did not apply exactly once")
    if text.count("Import / Export CSV") != 1:
        raise RuntimeError("Import / Export CSV button changed")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("Load Sample Data (Demo) no longer renders")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
