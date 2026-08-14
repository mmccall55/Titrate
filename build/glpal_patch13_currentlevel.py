#!/usr/bin/env python3
"""
Patch 13 - show the current medication level on the dose chart.

The weight chart marks its latest reading with a labelled dot ("228lbs"). The
dose chart had no equivalent: the estimated level right now was only visible on
the "Current Level" dashboard card, not on the curve itself.

How it works
------------
Inside `Vge`, the combined-level series is built by walking each day from
firstDate to lastDate and splitting the points either side of today:

    O = o.indexOf(M)            // index of this day in the axis
    O <= s && x.push([M, P])    // past  -> solid "Combined" series
    O >= s && b.push([M, P])    // future -> dotted "Combined_future" series

So the last element of `x` is the level at today, already computed. This adds a
scatter series at that point carrying a label.

The marker is appended AFTER the two forEach passes that add labels to scatter
series and thin them to six points, so neither rewrites it.

Styling mirrors the weight chart's LastWeight marker, in the dose series colour
rather than the weight green, and reuses the app's own dose formatting rule
(two decimals below 1mg, otherwise one).

Usage:
  python glpal_patch13_currentlevel.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "5797758f0e14262c54051165c93129eb91d9c5e2905716a0b07a08f95d1c9a76"
EXPECTED_OUTPUT_SHA256 = "0290848e7b5db004b190a76a8af3dc74b3b17ec093fa5ad6e544d7cef59d99c5"

MARKER = (
    'const __glpalMk=(()=>{const F=x.length?x[x.length-1]:null;'
    'if(F&&F[1]!=null&&isFinite(F[1])){'
    'const V=F[1],L=V<1?V.toFixed(2):V.toFixed(1),'
    'CS=((r.length>1?g:(t[r[0]]||g))||g).stroke;'
    'return[{name:"CurrentLevel",type:"scatter",z:25,showInLegend:!1,'
    'data:[{value:[F[0],V]}],symbolSize:14,'
    'itemStyle:{color:CS,borderColor:"#36210B",borderWidth:3},'
    'label:{show:!0,position:"top",formatter:()=>L+"mg",color:CS,'
    'fontSize:10,fontWeight:"bold",distance:8,'
    'backgroundColor:"rgba(0, 0, 0, 0.9)",borderRadius:4,'
    'borderColor:CS,borderWidth:1,padding:[4,6],'
    'textShadowColor:"rgba(0,0,0,0.8)",textShadowBlur:4,'
    'textShadowOffsetX:1,textShadowOffsetY:1}}]}return[]})();'
)

# Vge drops the combined array `y` entirely when only one medication is
# tracked, so the marker has to be appended to the returned array instead.
RET_TODAY_OLD = '[...r.length>1?y:[],...C,N]}'
RET_TODAY_NEW = '[...r.length>1?y:[],...C,N,...__glpalMk]}'
RET_PLAIN_OLD = 'return[...r.length>1?y:[],...C]}'
RET_PLAIN_NEW = 'return[...r.length>1?y:[],...C,...__glpalMk]}'

# insert immediately before the per-medication series are built, which is after
# the label and thinning passes have already run over the scatter series
ANCHOR = 'const C=r.map(T=>{const M=[],N=[],k=[],P=t[T],O=new Date(n);'

# Both dashboard charts carry a labelled marker at the top of a line, and both
# used a 10px grid top - so the label was clipped whenever the marked value sat
# near the axis maximum. 30px leaves room for the plate.
GRID_OLD = 'grid:{top:10,left:10,right:10,bottom:40,containLabel:!0}'
GRID_NEW = 'grid:{top:30,left:10,right:10,bottom:40,containLabel:!0}'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch13_currentlevel.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-12 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    if text.count(ANCHOR) != 1:
        raise RuntimeError(f"anchor found {text.count(ANCHOR)} times, expected 1")
    text = text.replace(ANCHOR, MARKER + ANCHOR, 1)

    for old, new, label in ((RET_TODAY_OLD, RET_TODAY_NEW, "return with today marker"),
                            (RET_PLAIN_OLD, RET_PLAIN_NEW, "return without today marker")):
        if text.count(old) != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {text.count(old)}")
        text = text.replace(old, new, 1)

    if text.count(GRID_OLD) != 2:
        raise RuntimeError(f"expected 2 dashboard grids, found {text.count(GRID_OLD)}")
    text = text.replace(GRID_OLD, GRID_NEW, 2)

    # the weight chart's own marker must be untouched
    if text.count('name:"LastWeight"') != 1:
        raise RuntimeError("the weight chart marker was altered")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("dose chart now marks the current level at today")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
