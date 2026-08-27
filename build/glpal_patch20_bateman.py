#!/usr/bin/env python3
"""
Patch 20 - Bateman-curve medication level model.

The level function `v1` modelled each dose as a 24-hour linear ramp to the
full nominal dose followed by pure exponential elimination. That truncates
absorption at hour 24, which overstates the decline in the days just after
the peak for slow-absorbing medications (semaglutide Tmax ~48h), and puts a
kink in the curve where the two pieces meet.

This replaces the piecewise body with the standard one-compartment
first-order absorption/elimination (Bateman) solution:

    level(o) = dose * [ka/(ka-ke)] * (exp(-ke*o) - exp(-ka*o)) / peak

with ke = ln2 / halfLifeHours and ka solved numerically (bisection, memoised)
so the peak lands at the medication's published Tmax. The curve is
peak-normalised so a 1 mg dose still peaks at 1 mg - the app's existing
"mg on board" display convention and the Current Level card's scale are
preserved. The long tail is unchanged: once absorption completes the curve
converges to the same half-life decay as before.

Tmax is not stored on dose records, so it is looked up from the stored
half-life (the preset values are distinct): 168h Semaglutide/Cagrilintide
-> 48h, 127h Tirzepatide -> 24h, 120h Retatrutide/Custom -> 24h, 108h
Dulaglutide -> 48h, 13h Liraglutide -> 11h. Anything else gets
clamp(0.2 * halfLife, 6h, 48h). Tmax is additionally capped at 0.95/ke,
the mathematical ceiling for a Bateman peak.

Deliberate behaviour changes:
- smooth curve, peak at Tmax instead of a corner at hour 24
- shallower decline in days 1-3 post-dose; troughs read higher
- a missing/zero halfLifeHours now falls back to 168h inside v1 itself, so
  the dose chart no longer renders NaN gaps for such records (the Current
  Level card already had this fallback at its call site)

`v1` is the single source of truth - the Current Level card (zge) and the
dose chart series builder (Vge) both call it - so this one replacement
changes every consumer consistently.

Usage:
  python glpal_patch20_bateman.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "ff23c8f4593df5cefd946aba41b7f013de7274d8e3aad40326c0f87befe1d786"
EXPECTED_OUTPUT_SHA256 = "78f6ca4ca7b000a6ebf44601a4d9caff1b4790852d38a1914fe58c7be043945d"

OLD = (
    'v1=(r,t,e)=>r.reduce((n,i)=>{const o=(e.getTime()-i.date.getTime())/36e5;'
    'if(o<0)return n;let s;if(o<24){const l=o/24;s=i.dose*l}'
    'else{const l=o-24,u=Math.exp(-.693*l/t);s=i.dose*u}return n+s},0)'
)

NEW = (
    '__glpalTmax=t=>({168:48,127:24,120:24,108:48,13:11})[t]'
    '||Math.min(48,Math.max(6,.2*t)),'
    '__glpalKa=(()=>{const c={};return(k,m)=>{const y=k+"|"+m;if(c[y])return c[y];'
    'let l=k*1.000001,h=k*1e3;for(let j=0;j<80;j++){const x=(l+h)/2;'
    'Math.log(x/k)/(x-k)>m?l=x:h=x}return c[y]=(l+h)/2}})(),'
    'v1=(r,t,e)=>{const T=t>0?t:168,K=Math.LN2/T,'
    'm=Math.min(__glpalTmax(T),.95/K),A=__glpalKa(K,m),'
    'F=O=>O<0?0:A/(A-K)*(Math.exp(-K*O)-Math.exp(-A*O)),pk=F(m);'
    'return r.reduce((n,i)=>n+i.dose*F((e.getTime()-i.date.getTime())/36e5)/pk,0)}'
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch20_bateman.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-19 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    if text.count(OLD) != 1:
        raise RuntimeError(f"v1 source found {text.count(OLD)} times, expected 1")
    for name in ("__glpalTmax", "__glpalKa"):
        if name in text:
            raise RuntimeError(f"{name} already present in input bundle")
    text = text.replace(OLD, NEW, 1)

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("level model is now a peak-normalised Bateman curve")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
