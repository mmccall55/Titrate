#!/usr/bin/env python3
"""
Patch 21 - year-qualified chart axis categories.

Symptom
    Once a user's history passes 365 days, both charts break. The today
    marker jumps back to the same month/day one year earlier, a long block
    of real logged history is drawn as the dotted "future" projection, and
    the current year's curve is plotted on top of last year's x-positions.
    Measured on a 525-day seed: 586 axis labels of which 221 were
    duplicates, todayIndex 160 instead of 525, and the solid series held
    322 points on 161 distinct x-positions.

Cause
    Both category axes are built from
    toLocaleDateString("en-US",{month:"short",day:"numeric"}) - "Aug 30",
    with no year. Past 365 days every label has two owners, and three
    separate consumers resolve a duplicate to its FIRST index:
      * Pge:  todayIndex = xAxisDates.indexOf(todayLabel)
      * Vge:  O = o.indexOf(M) / V = o.indexOf(G), the past-vs-future split
      * ECharts itself, matching series data given as [label, value] pairs
        against xAxis.data

Fix
    Two module-scope helpers next to __glpalSampleAt:
      __glpalDayKey(D)    -> "Aug 30 2026"  (unique per calendar day)
      __glpalDayLabel(v)  -> "Aug 30"       (strips the trailing year)
    Every site that builds an axis category, or a string compared against
    one, now uses __glpalDayKey; both xAxis blocks get
    axisLabel.formatter = __glpalDayLabel so the ticks read exactly as
    before. The two tooltip titles already appended the year by hand
    ("Aug 30 2026") and now just use the key, which is the same text.
    indexOf stays - the keys are unique, so it is now exact.

    Nine label-construction sites change: Pge (axis array, today label),
    Vge (dose-marker key, combined-series label, per-medication label),
    kge (weight displayDate), Rge (axis array, today label, dose-change
    pin label).

What this deliberately does NOT change
    * v1 and all level math - asserted byte-identical.
    * The visible tick text and the tooltip title text.
    * The peptide injection sparkline (f0e). Its series data is a
      positional array, so ECharts matches by index, not by name, and
      duplicate labels cannot displace a value there.
    * The seven non-axis uses of the short-date format (Yh.short, Jj,
      next-due date strings, "Last:" text) - count asserted to drop from
      19 to 10 exactly.
    * Stored data. No record shape, store name or key path is touched.

Usage:
  python glpal_patch21_axisyear.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "78f6ca4ca7b000a6ebf44601a4d9caff1b4790852d38a1914fe58c7be043945d"
EXPECTED_OUTPUT_SHA256 = "d02bc0329c5c0fd7d8629d26f3944bafdf349bbdf658013da4428dc4cdaf941a"

SHORT = 'toLocaleDateString("en-US",{month:"short",day:"numeric"})'
PURPLE = 'rgba(156, 123, 211, 0.2)'   # pre-recolour; recolour.py runs later

EDITS = [
    # 1. helpers, beside __glpalSampleAt (module scope, function declarations)
    ("helpers",
     '?n:D}const y0e=(',
     '?n:D}'
     'function __glpalDayKey(D){return D.' + SHORT + '+" "+D.getFullYear()}'
     'function __glpalDayLabel(v){return typeof v=="string"?v.replace(/ \\d{4}$/,""):v}'
     'const y0e=('),

    # 2. Pge - dose-chart axis array and today label
    ("Pge axis+today",
     'const c=[],d=new Date(o);for(;d<=s;)c.push(d.' + SHORT + '),'
     'd.setDate(d.getDate()+1);const h=l.' + SHORT + ';',
     'const c=[],d=new Date(o);for(;d<=s;)c.push(__glpalDayKey(d)),'
     'd.setDate(d.getDate()+1);const h=__glpalDayKey(l);'),

    # 3. Vge - dose marker key (dose date + 1 day, pre-existing offset kept)
    ("Vge marker key",
     'const k=new Date(M.date.getTime()+864e5).' + SHORT + ';',
     'const k=__glpalDayKey(new Date(M.date.getTime()+864e5));'),

    # 4. Vge - combined-series day label
    ("Vge combined label",
     'const M=D.' + SHORT + ',k=h.has(M)?v[M]:void 0,',
     'const M=__glpalDayKey(D),k=h.has(M)?v[M]:void 0,'),

    # 5. Vge - per-medication series day label
    ("Vge per-med label",
     'G=O.' + SHORT + ',q=c[T].has(G)?d[T][G]:void 0',
     'G=__glpalDayKey(O),q=c[T].has(G)?d[T][G]:void 0'),

    # 6. kge - weight point displayDate (compared against the axis)
    ("kge displayDate",
     'displayDate:__glpalLocalDate(o.date).' + SHORT + '}',
     'displayDate:__glpalDayKey(__glpalLocalDate(o.date))}'),

    # 7. Rge - weight-chart axis array and today label
    ("Rge axis+today",
     'for(;Y<=N;)ee.push(Y.' + SHORT + '),Y.setDate(Y.getDate()+1);'
     'return ee},[x,N]),P=_x().' + SHORT + ',',
     'for(;Y<=N;)ee.push(__glpalDayKey(Y)),Y.setDate(Y.getDate()+1);'
     'return ee},[x,N]),P=__glpalDayKey(_x()),'),

    # 8. Rge - dose-change pin label
    ("Rge pin label",
     'const te=__glpalLocalDate(ne.date),ie=te.' + SHORT + ',ye=U.indexOf(ie);',
     'const te=__glpalLocalDate(ne.date),ie=__glpalDayKey(te),ye=U.indexOf(ie);'),

    # 9. weight chart xAxis - display ticks without the year
    ("weight xAxis formatter",
     'data:k,boundaryGap:!1,axisLine:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisTick:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisLabel:{fontSize:12,color:"#94a3b8",margin:10},splitLine:{show:!1}}',
     'data:k,boundaryGap:!1,axisLine:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisTick:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisLabel:{fontSize:12,color:"#94a3b8",margin:10,formatter:__glpalDayLabel},'
     'splitLine:{show:!1}}'),

    # 10. dose chart xAxis - display ticks without the year
    ("dose xAxis formatter",
     'data:g,boundaryGap:!1,axisLine:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisTick:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisLabel:{fontSize:12,color:"#94a3b8"},splitLine:{show:!1}}',
     'data:g,boundaryGap:!1,axisLine:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisTick:{lineStyle:{color:"' + PURPLE + '"}},'
     'axisLabel:{fontSize:12,color:"#94a3b8",formatter:__glpalDayLabel},'
     'splitLine:{show:!1}}'),

    # 11. weight tooltip title - the key already carries the year
    ("weight tooltip title",
     'Ie=`${$.axisValue} ${ye.getFullYear()}`;',
     'Ie=$.axisValue;'),

    # 12. dose tooltip title - same
    ("dose tooltip title",
     'V=`${j} ${X.getFullYear()}`;',
     'V=j;'),
]

NEW_NAMES = ("__glpalDayKey", "__glpalDayLabel")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def die(msg):
    raise SystemExit("FAIL: " + msg)


def main():
    if len(sys.argv) != 3:
        die("usage: glpal_patch21_axisyear.py IN.js OUT.js")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    got = sha(raw)
    if got != EXPECTED_INPUT_SHA256:
        die(f"input sha mismatch\n  expected {EXPECTED_INPUT_SHA256}\n  actual   {got}")
    text = raw.decode("utf-8")

    for name in NEW_NAMES:
        if name in text:
            die(f"{name} already present in input")

    before_short = text.count(SHORT)
    if before_short != 19:
        die(f"expected 19 short-date sites in input, found {before_short}")

    # v1 must survive untouched
    v1_start = text.index("v1=(r,t,e)=>{const T=t>0?t:168")
    v1_body = text[v1_start:text.index(",zge=(r,t)=>{", v1_start)]

    for label, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            die(f"{label}: expected 1 occurrence of anchor, found {n}")
        text = text.replace(old, new, 1)

    after_short = text.count(SHORT)
    # 9 axis sites converted; helper 1 adds one back -> 19 - 9 + 1 = 11
    if after_short != 11:
        die(f"expected 11 short-date sites after patch, found {after_short}")
    if text.count("__glpalDayKey(") != 10:      # 1 definition + 9 call sites
        die(f"unexpected __glpalDayKey count: {text.count('__glpalDayKey(')}")
    if text.count("__glpalDayLabel") != 3:      # 1 definition + 2 formatters
        die(f"unexpected __glpalDayLabel count: {text.count('__glpalDayLabel')}")
    if v1_body not in text:
        die("v1 was modified; it must be byte-identical")

    out = text.encode("utf-8")
    got_out = sha(out)
    print("output sha256:", got_out)
    if EXPECTED_OUTPUT_SHA256 != "REPLACE_ME" and got_out != EXPECTED_OUTPUT_SHA256:
        die(f"output sha mismatch\n  expected {EXPECTED_OUTPUT_SHA256}\n  actual   {got_out}")
    dst.write_bytes(out)


if __name__ == "__main__":
    main()
