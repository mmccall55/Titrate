#!/usr/bin/env python3
"""
Patch 23 - remove the unused medication-level calculation from the dosing-plan hook.

Symptom
    None visible. The dosing-plan hook `Wye` (Doses screen: next due,
    countdown, days since last dose, this month, planned doses) also computes
    a `currentLevel` field that nothing renders - the string `currentLevel`
    occurs exactly twice in the bundle, both producers. It is the only `v1`
    caller that disagrees with the Current Level card.

Cause
    Upstream left a fourth `v1` call site in `Wye`. It is wrong four ways:
    it only sums medications with an active dosing plan covering today; it
    takes half-life from the plan and drops the medication if that is falsy;
    it parses dose dates with `new Date(record.date)` (UTC midnight) and
    ignores the dose time (patch 22); and it matches medications through a
    normalising function instead of by exact string. It runs whenever the
    hook's memo recomputes, which includes clock changes, but only for
    medications with an active plan that carries a half-life.

Fix
    Replace the summation loop with nothing, leaving `let j=0;`, so
    `currentLevel` is always 0 - the value the hook's own default already
    uses. The per-medication grouping above it (`R`, `G`) stays; it is cheap
    and removing it would widen the anchor for no gain.

What this deliberately does NOT change
    - every other field `Wye` returns (next due, countdown, planned doses, etc.)
    - `v1` itself, and its three remaining callers: `zge` (card) and the two
      loops in `Vge` (chart)
    - the `currentLevel` key - still produced, so the hook's shape is unchanged

Usage
    python glpal_patch23_wyelevel.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import re
import sys

EXPECTED_INPUT_SHA256 = "25c35ae27dbaacf6ba5573278fe454ad1ffe8a6c9e3e75b0044ee69ab4cf76e3"
EXPECTED_OUTPUT_SHA256 = "9a2e5b39cb4d253cdea5b8c66a985adff38154adaf8426dd68e62741b0449019"

OLD = "let j=0;Object.keys(R).forEach(te=>{R[te].length>0&&G[te]&&(j+=v1(R[te],G[te],o))});"
NEW = "let j=0;"
V1_CALL = re.compile(r"(?<![\w$])v1\(")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch23_wyelevel.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-22 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    calls_before = len(V1_CALL.findall(text))
    if calls_before != 4:
        raise RuntimeError(f"expected 4 v1( call sites, found {calls_before}")
    if text.count("currentLevel") != 2:
        raise RuntimeError(f"expected currentLevel twice, found {text.count('currentLevel')}")
    if text.count(OLD) != 1:
        raise RuntimeError(f"Wye level loop found {text.count(OLD)} times, expected 1")

    text = text.replace(OLD, NEW, 1)

    calls_after = len(V1_CALL.findall(text))
    if calls_after != 3:
        raise RuntimeError(f"v1( call sites after patch: {calls_after}, expected 3")
    if text.count("currentLevel") != 2:
        raise RuntimeError("currentLevel occurrence count changed")
    if "currentLevel:isNaN(j)?0:j" not in text:
        raise RuntimeError("Wye no longer returns currentLevel from j")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("Wye.currentLevel is now always 0; v1 has 3 callers")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
