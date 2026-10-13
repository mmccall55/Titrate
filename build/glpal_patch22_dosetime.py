#!/usr/bin/env python3
"""
Patch 22 - place each dose at its recorded time, not local midnight.

Symptom
    The Current Level card and the dose chart treat every dose as taken at
    00:00 on its date. A dose logged at 20:00 is counted 20 hours early, so in
    the first one to two days after a dose the card and chart read the level
    as if more time had passed than really has. Example: a Tmax-48 dose at
    20:00 viewed at 08:00 next morning reads the curve at 32 h instead of 12 h.

Cause
    Both places that turn dose records into model input - `Ege` (dose chart)
    and `zge` (Current Level card) - map each record to
    `{date: Ht.parseLocalDate(record.date), dose}`. `parseLocalDate` returns
    local midnight and `record.time` is never read. The Log Dose form already
    stores `time` as "HH:MM" (pre-filled with the time the form opened), the
    Edit Dose dialog (patch 3) edits it, and CSV import copies it through.

Fix
    A new helper `__glpalDoseAt(record)` returns `Ht.parseLocalDate(date)`
    with the hours and minutes of `record.time` applied via `setHours`, so
    DST is handled by the local-time constructor. It accepts "H:MM",
    "HH:MM", "HH:MM:SS", with an optional AM/PM suffix. Anything else -
    missing, empty, malformed, out of range - leaves the date at local
    midnight, which is exactly the previous behaviour. Both mapping sites call
    the helper instead of `Ht.parseLocalDate`.

What this deliberately does NOT change
    - `v1` (the level model) - asserted byte-identical
    - the chart's sampling: past days at local midnight, today at now
      (patch 14)
    - the dose-day marker on the chart, keyed to the dose date + 1 day; adding
      hours to the dose date never changes which calendar day that is
    - the two other `Ht.parseLocalDate` call sites, which compute chart date
      ranges from `record.date` and are not model input
    - the dead `Wye` protocol path, which uses `new Date(record.date)`
    - storage: no record is read differently or written

Usage
    python glpal_patch22_dosetime.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "d02bc0329c5c0fd7d8629d26f3944bafdf349bbdf658013da4428dc4cdaf941a"
EXPECTED_OUTPUT_SHA256 = "25c35ae27dbaacf6ba5573278fe454ad1ffe8a6c9e3e75b0044ee69ab4cf76e3"

HELPER_ANCHOR = "function __glpalDayKey("
HELPER = (
    'function __glpalDoseAt(d){const D=Ht.parseLocalDate(d.date),'
    'm=/^\\s*(\\d{1,2}):(\\d{2})(?::\\d{2})?\\s*([AaPp][Mm])?\\s*$/.exec(d.time==null?"":String(d.time));'
    'if(m){let h=+m[1];const n=+m[2];'
    'if(m[3]){if(h<1||h>12)return D;h=h%12+(/[Pp]/.test(m[3])?12:0)}'
    'if(h<24&&n<60)D.setHours(h,n,0,0)}return D}'
)

SITES = [
    ("Ege (dose chart)",
     "i[s]=t.filter(l=>l.medication===s).map(l=>({date:Ht.parseLocalDate(l.date),dose:l.dose}))",
     "i[s]=t.filter(l=>l.medication===s).map(l=>({date:__glpalDoseAt(l),dose:l.dose}))"),
    ("zge (Current Level card)",
     "a[s]=r.filter(u=>u.medication===s).map(u=>({date:Ht.parseLocalDate(u.date),dose:u.dose}))",
     "a[s]=r.filter(u=>u.medication===s).map(u=>({date:__glpalDoseAt(u),dose:u.dose}))"),
]

V1_BODY = ("v1=(r,t,e)=>{const T=t>0?t:168,K=Math.LN2/T,"
           "m=Math.min(__glpalTmax(T),.95/K),A=__glpalKa(K,m),"
           "F=O=>O<0?0:A/(A-K)*(Math.exp(-K*O)-Math.exp(-A*O)),pk=F(m);"
           "return r.reduce((n,i)=>n+i.dose*F((e.getTime()-i.date.getTime())/36e5)/pk,0)}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch22_dosetime.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-21 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    if "__glpalDoseAt" in text:
        raise RuntimeError("__glpalDoseAt already present in input bundle")
    if text.count(V1_BODY) != 1:
        raise RuntimeError("v1 body not found exactly once in input")
    before = text.count("Ht.parseLocalDate(")
    if before != 4:
        raise RuntimeError(f"expected 4 Ht.parseLocalDate( call sites, found {before}")

    if text.count(HELPER_ANCHOR) != 1:
        raise RuntimeError(f"helper anchor found {text.count(HELPER_ANCHOR)} times, expected 1")
    text = text.replace(HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1)

    for label, old, new in SITES:
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"{label}: anchor found {n} times, expected 1")
        text = text.replace(old, new, 1)

    # global invariants
    after = text.count("Ht.parseLocalDate(")
    if after != 3:   # 2 call sites remain + 1 inside the new helper
        raise RuntimeError(f"Ht.parseLocalDate( count is {after}, expected 3")
    if text.count("__glpalDoseAt(") != 3:   # definition + 2 call sites
        raise RuntimeError(f"__glpalDoseAt( count is {text.count('__glpalDoseAt(')}, expected 3")
    if text.count(V1_BODY) != 1:
        raise RuntimeError("v1 body changed")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("doses are placed at their recorded time; missing or bad time -> local midnight")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
