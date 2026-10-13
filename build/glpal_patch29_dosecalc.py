#!/usr/bin/env python3
"""
Patch 29 - dosage calculator under the Log Dose button on the Doses tab.

What Marc asked for
    One input, "Target medication level (mg)", to one decimal place. The
    calculator works out the dose that makes the modelled level PEAK at the
    target (method B, exact), and shows it as:
        Dose: 5.44 mg
        10 mg/ml vial: 0.54 ml (54 units)
        15 mg/ml vial: 0.36 ml (36 units)
        Peak ≈ 10.0 mg in ~20 h
    or "No dose needed" when the level would reach the target without a new
    dose. Units are U-100 insulin-syringe units (1 ml = 100 units), rounded to
    the nearest unit; ml to 2 decimals. Results update as the target changes.

Method
    Same model and inputs as the Current Level card: records grouped by exact
    medication string, half-life from the first record of each (fallback
    168 h), dose times from __glpalDoseAt (patch 22), level from v1. The new
    dose is taken now, as the medication of the most recent record (127 h if
    there are no records). Because the model is linear, the level after a dose
    d is base(t) + d * unit(t). The calculator samples t over the next 7 days
    at 15-minute steps and bisects d in [0, target] so that the maximum of
    base + d * unit equals the target. The reported peak and its time are that
    maximum. This removes the small overshoot of reading the level at exactly
    Tmax (the combined level peaks a few hours earlier).

    Rejected by Marc: rounding units down, a warning above 15 mg.

Fix (how)
    New module-level functions inserted before `function __glpalDoseAt(`:
    __glpalLevels(records), __glpalTotalAt(levels, date), __glpalCalc(records,
    target, nowMs), and the component __glpalDoseCalc. One insertion after the
    Log Dose button renders the component with the Doses screen's dose records
    (`r`), its ticking clock (`ie`) and the card label class (`Qe.label`).

What this deliberately does NOT change
    - v1, the Current Level card, the chart, any stored data
    - the hidden upstream "Peptide Calculator" tab (stays hidden)

Usage
    python glpal_patch29_dosecalc.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "535bdacccaed7c4d48b671990266bb6b7a5dd2667fd4f2bdd5068e9eb12f9352"
EXPECTED_OUTPUT_SHA256 = "a9ba5fcf6250d8fab2b230eadfd0c54aed4f5507dc955de7d0769f8494453a4e"

HELPER_ANCHOR = "function __glpalDoseAt("
HELPERS = (
    'function __glpalLevels(r){const m={},o=[];(r||[]).forEach(e=>{if(!m[e.medication]){m[e.medication]={k:e.medication,h:e.halfLifeHours,d:[]};o.push(m[e.medication])}'
    'm[e.medication].d.push({date:__glpalDoseAt(e),dose:e.dose})});return o.map(x=>({k:x.k,h:x.h||168,d:x.d}))}'
    'function __glpalTotalAt(L,t){let s=0;for(const x of L){const v=v1(x.d,x.h,t);isNaN(v)||(s+=v)}return s}'
    'function __glpalCalc(r,T,now){if(!(T>0))return null;const L=__glpalLevels(r),z=r&&r.length?r[r.length-1].medication:null,'
    'g=L.find(x=>x.k===z),h=g?g.h:127,st=9e5,n=672,B=[],U=[];'
    'for(let i=0;i<=n;i++){const t=new Date(now+i*st);B.push(__glpalTotalAt(L,t));U.push(v1([{date:new Date(now),dose:1}],h,t))}'
    'const P=d=>{let b=-1,j=0;for(let i=0;i<=n;i++){const v=B[i]+d*U[i];v>b&&(b=v,j=i)}return[b,j]};'
    'if(P(0)[0]>=T)return{none:!0};let lo=0,hi=T;for(let k=0;k<60;k++){const md=(lo+hi)/2;P(md)[0]<T?lo=md:hi=md}'
    'const d=(lo+hi)/2,q=P(d);return{dose:d,peak:q[0],hours:q[1]*st/36e5}}'
    'function __glpalDoseCalc(p){const[t,sT]=Q.useState(""),{isDarkMode:dk}=jr(),r=p.entries||[],mk=Math.floor(p.now.getTime()/6e4),'
    'T=Math.round(parseFloat(t)*10)/10,R=Q.useMemo(()=>__glpalCalc(r,T,mk*6e4),[r,T,mk]),'
    'tx=`text-sm ${dk?"text-white":"text-gray-700"}`,'
    'ln=(a,b)=>S.jsxs("div",{className:"flex justify-between "+tx,children:[S.jsx("span",{children:a}),S.jsx("span",{className:"font-semibold",children:b})]}),'
    'ml=c=>{const v=R.dose/c;return v.toFixed(2)+" ml ("+Math.round(v*100)+" units)"};'
    'return S.jsxs("div",{className:"mt-3","data-glpal":"dose-calc",children:['
    'S.jsx("label",{htmlFor:"glpalTarget",className:p.labelClass,children:"Target medication level (mg)"}),'
    'S.jsx("input",{id:"glpalTarget",type:"number",step:"0.1",min:"0",inputMode:"decimal",value:t,onChange:e=>sT(e.target.value),placeholder:"e.g. 10.1",'
    'className:`w-full px-3 py-2 mt-1 mb-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#B19CD9]/50 ${dk?"border-[#B19CD9]/30 bg-black/20 text-white placeholder-gray-400":"border-gray-300 bg-white text-gray-700 placeholder-gray-400"}`}),'
    'R&&(R.none?S.jsx("p",{className:tx,children:"No dose needed"}):S.jsxs("div",{children:['
    'ln("Dose",R.dose.toFixed(2)+" mg"),ln("10 mg/ml vial",ml(10)),ln("15 mg/ml vial",ml(15)),'
    'ln("Peak","\\u2248 "+R.peak.toFixed(1)+" mg in ~"+Math.round(R.hours)+" h")]}))]})}'
)

BUTTON = 'S.jsx(Xx,{onClick:()=>l("medication"),fullWidth:!0,children:"Log Dose"})'
CALC = ',S.jsx(__glpalDoseCalc,{entries:r,now:ie,labelClass:Qe.label})'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch29_dosecalc.py INPUT_JS OUTPUT_JS")
    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Input is not the verified patch-28 bundle.\n"
                           f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")
    text = raw.decode("utf-8")
    for name in ("__glpalLevels", "__glpalTotalAt", "__glpalCalc", "__glpalDoseCalc"):
        if name in text:
            raise RuntimeError(f"{name} already present in input")
    for anchor in (HELPER_ANCHOR, BUTTON):
        if text.count(anchor) != 1:
            raise RuntimeError(f"anchor {anchor[:40]!r} found {text.count(anchor)} times, expected 1")
    text = text.replace(HELPER_ANCHOR, HELPERS + HELPER_ANCHOR, 1)
    text = text.replace(BUTTON, BUTTON + CALC, 1)
    if text.count("S.jsx(__glpalDoseCalc,") != 1:
        raise RuntimeError("calculator not rendered exactly once")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")
    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("dosage calculator rendered under Log Dose")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
