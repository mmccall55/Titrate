#!/usr/bin/env python3
"""
Patch 24 - stop the Doses screen crashing when a dosing plan is active.

Symptom
    With any active dosing plan (protocol), opening Doses shows
    "Oops! Something went wrong". Reproduced on the patch-21 build, which was
    live at the time.

Cause
    The per-medication plan card lazily imports
    `../MedicationProgressBar-CpSrqVLQ.js` (`Bye`, rendered inside a
    `Suspense`). That chunk was never captured: it is not in
    `upstream/glpal-upstream.zip`, so it is not in `docs/`, and glpal.app no
    longer serves it (the path returns the site's HTML fallback). The dynamic
    import 404s, the lazy component rejects, and the error boundary takes the
    whole screen.

Fix
    Replace the lazy import with a lazy component that resolves immediately to
    a component rendering nothing. The plan card's Suspense wrapper and props
    are unchanged; it just renders empty. Everything else on the Doses screen
    renders normally with a plan active.

What this deliberately does NOT change
    - the dosing-plan data, stores, or the hook `Wye` (next due, countdown)
    - the other dynamic import, the Capacitor shim `../web-BkP7LE0t.js`, which
      is shipped
    - What is lost: whatever the missing chunk drew - a progress bar and,
      judging by its props (`onLogDose`, `isLogging`), a log-dose control for
      the plan. Doses can still be logged from the normal Log Dose flow. If
      the original chunk is ever recovered, ship it like the shim and drop
      this patch.

Usage
    python glpal_patch24_progressbar.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import re
import sys

EXPECTED_INPUT_SHA256 = "9a2e5b39cb4d253cdea5b8c66a985adff38154adaf8426dd68e62741b0449019"
EXPECTED_OUTPUT_SHA256 = "cb28ba6620061907c58b525223183d4918a615a471049856e72e2680da9db723"

OLD = 'Bye=Bu.lazy(()=>Sz(()=>import("../MedicationProgressBar-CpSrqVLQ.js"),[]))'
NEW = 'Bye=Bu.lazy(()=>Promise.resolve({default:()=>null}))'
DYN = re.compile(r'import\("([^"]+)"\)')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch24_progressbar.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-23 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    before = DYN.findall(text)
    if before != ["../web-BkP7LE0t.js", "../MedicationProgressBar-CpSrqVLQ.js"]:
        raise RuntimeError(f"unexpected dynamic imports in input: {before}")
    if text.count(OLD) != 1:
        raise RuntimeError(f"Bye lazy import found {text.count(OLD)} times, expected 1")

    text = text.replace(OLD, NEW, 1)

    after = DYN.findall(text)
    if after != ["../web-BkP7LE0t.js"]:
        raise RuntimeError(f"dynamic imports after patch: {after}, expected only the shim")
    if "MedicationProgressBar" in text:
        raise RuntimeError("MedicationProgressBar still referenced")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("plan progress bar renders nothing instead of importing a missing chunk")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
