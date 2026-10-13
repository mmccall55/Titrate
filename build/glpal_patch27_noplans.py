#!/usr/bin/env python3
"""
Patch 27 - hide dosing plans.

Symptom
    Marc does not use dosing plans (protocols). They take a section of the
    Doses screen and two of its summary cards.

Cause
    Upstream feature, always rendered.

Fix
    Render guards (`!1&&`, the patch-15 technique) on:
    - the Doses "Dosing Plans" section: plan list, "+ Custom Plan",
      "+ Schedule". The plan edit, schedule and disclaimer dialogs are opened
      only from that section, so they become unreachable.
    - the Current Dose card (sum of active plan doses)
    - the Planned Doses card (future plan doses, counted to 2099 for an
      ongoing plan)
    and changes the Doses card grid from `lg:grid-cols-6` to `lg:grid-cols-3`
    so the three remaining cards (Total Doses, Current Level, Logged Doses)
    fill one row on a wide screen. The Dashboard's grid has the same class
    string; the anchor includes the Total Doses card so only the Doses grid
    changes.

    Side effect, wanted: every plan action (save, delete, archive, Schedule)
    clears the medications store and rewrites it with manual doses plus
    regenerated plan doses. With the section hidden nothing can trigger that.

What this deliberately does NOT change
    - the `protocols` store and its records (schema rule)
    - dose records the plan feature generated earlier (not marked isManual);
      they still count as doses and can be deleted from the Log tab
    - `Wye`, patch 24's empty progress bar, CSV export/import of plans
    - Log Dose Manually, the dose chart, Current Level, the Dashboard

Usage
    python glpal_patch27_noplans.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "055531610e1c54a3488a0bfb9b1a181072fdc6972b78357b38449bd126ce5eda"
EXPECTED_OUTPUT_SHA256 = "13295d53d2b17ac6a543df812bfc5a7ea6358603f46df32f36afca79ed042371"

GUARDS = [
    ("Doses Dosing Plans section",
     '}),S.jsxs("div",{className:Se,children:[S.jsx("h1",{className:Ve.title,children:"Dosing Plans"})'),
    ("Doses Current Dose card",
     '}),S.jsxs("div",{className:Pe,children:[S.jsx("p",{className:Qe.label,children:"Current Dose"})'),
    ("Doses Planned Doses card",
     '}),S.jsxs("div",{className:Pe,children:[S.jsx("p",{className:Qe.label,children:"Planned Doses"})'),
]
GRID_OLD = ('grid grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3 overflow-visible",children:[S.jsxs("div",'
            '{className:Pe,children:[S.jsx("p",{className:Qe.label,children:"Total Doses"')
GRID_NEW = GRID_OLD.replace("lg:grid-cols-6", "lg:grid-cols-3", 1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch27_noplans.py INPUT_JS OUTPUT_JS")
    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Input is not the verified patch-26 bundle.\n"
                           f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")
    text = raw.decode("utf-8")
    guards_before = text.count("!1&&")
    six_before = text.count("lg:grid-cols-6")
    for label, old in GUARDS:
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"{label}: anchor found {n} times, expected 1")
        text = text.replace(old, old[:3] + "!1&&" + old[3:], 1)
    if text.count(GRID_OLD) != 1:
        raise RuntimeError(f"Doses grid anchor found {text.count(GRID_OLD)} times, expected 1")
    text = text.replace(GRID_OLD, GRID_NEW, 1)

    if text.count("!1&&") != guards_before + len(GUARDS):
        raise RuntimeError("guard count did not rise by exactly the number of guards")
    if text.count("lg:grid-cols-6") != six_before - 1:
        raise RuntimeError("more than one grid changed")
    for needle in ('"Dosing Plans"', '"+ Custom Plan"', '"+ Schedule"', '"Current Dose"', '"Planned Doses"'):
        if text.count(needle) != 1:
            raise RuntimeError(f"{needle} occurrence count changed")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")
    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("dosing plans section and Current Dose / Planned Doses cards no longer render")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
