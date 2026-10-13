#!/usr/bin/env python3
"""
Patch 28 - rename two buttons.

Symptom
    Marc wants plainer button labels:
    - Dashboard "+ Quick Log" (opens the daily log: weight, hydration, mood,
      side effects, food) -> "Weight Check-in"
    - Doses "+ Log Dose Manually" (opens the dose form) -> "Log Dose"

Fix
    Replace the two button label strings. Each occurs exactly once.

What this deliberately does NOT change
    - what either button opens, or the dialogs themselves; the daily-log
      dialog's own title still reads "Quick Log"
    - any other label

Usage
    python glpal_patch28_buttonlabels.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "13295d53d2b17ac6a543df812bfc5a7ea6358603f46df32f36afca79ed042371"
EXPECTED_OUTPUT_SHA256 = "535bdacccaed7c4d48b671990266bb6b7a5dd2667fd4f2bdd5068e9eb12f9352"

LABELS = [
    ('children:"+ Quick Log"', 'children:"Weight Check-in"'),
    ('children:"+ Log Dose Manually"', 'children:"Log Dose"'),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch28_buttonlabels.py INPUT_JS OUTPUT_JS")
    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Input is not the verified patch-27 bundle.\n"
                           f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")
    text = raw.decode("utf-8")
    if "Weight Check-in" in text:
        raise RuntimeError("Weight Check-in already present in input")
    log_dose_before = text.count('children:"Log Dose"')
    for old, new in LABELS:
        if text.count(old) != 1:
            raise RuntimeError(f"{old} found {text.count(old)} times, expected 1")
        text = text.replace(old, new, 1)
    if text.count('children:"Weight Check-in"') != 1:
        raise RuntimeError("Weight Check-in label count wrong")
    if text.count('children:"Log Dose"') != log_dose_before + 1:
        raise RuntimeError("Log Dose label count wrong")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")
    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print('buttons now read "Weight Check-in" and "Log Dose"')
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
