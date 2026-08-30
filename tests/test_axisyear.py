"""Patch 21 - chart axis categories are year-qualified.

Before patch 21 both charts built their category axis from year-less
"Mon D" labels. Past 365 days of history every label had two owners, and
`Vge`'s past/future split (`O = xAxisDates.indexOf(M)`) resolved each to
the first one. The solid history line then stopped covering the older part
of the chart - that stretch was pushed into the dotted forecast series -
and the remaining points were stacked two-deep on the same x-positions.

Assertion: the solid history line must start at the left edge of the plot
and carry one point per day of history. On a 525-day seed the pre-patch-21
build starts it at 0.624 of the plot width with 323 points instead of 526.

The today marker is deliberately NOT used here: ECharts resolves a
markLine category name to the last match, so it landed in the right place
even when the series split did not, and it does not detect this bug.
"""

import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from testlib import serve, open_app, goto_doses, dose, Report
from playwright.sync_api import sync_playwright

MED = "Semaglutide (Ozempic/Wegovy)"
TODAY = datetime.date.today()

PROBE = """() => {
  const svg = [...document.querySelectorAll('svg')]
      .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!svg) return null;
  const all = [...svg.querySelectorAll('path')];
  // horizontal split lines give the plot's left and right edges
  const horiz = all.map(p => /^M([\\d.]+) ([\\d.]+)L([\\d.]+) \\2$/.exec(p.getAttribute('d') || ''))
                   .filter(Boolean);
  if (!horiz.length) return null;
  const left  = Math.min(...horiz.map(m => +m[1]));
  const right = Math.max(...horiz.map(m => +m[3]));
  // the longest multi-segment path is the solid history line
  const series = all.map(p => {
        const xs = [...(p.getAttribute('d') || '').matchAll(/[ML]([\\d.]+) /g)].map(m => +m[1]);
        return {n: xs.length, min: Math.min(...xs), max: Math.max(...xs)};
      })
      .filter(o => o.n > 5)
      .sort((a, b) => b.n - a.n)[0];
  const ticks = [...svg.querySelectorAll('text')].map(t => t.textContent)
      .filter(s => /^[A-Z][a-z]{2} \\d{1,2}/.test(s));
  return {left, right, series, ticks};
}"""


def weekly(span_days):
    out, d = [], TODAY - datetime.timedelta(days=span_days)
    while d <= TODAY:
        out.append(dose(d.isoformat(), MED, 2.4, halfLifeHours=168))
        d += datetime.timedelta(days=7)
    return out


def run(rep, br, span):
    tag = f"{span}d history"
    ctx, pg = open_app(br, seed=weekly(span))
    pg.set_viewport_size({"width": 1280, "height": 800})
    goto_doses(pg)
    pg.click("button:has-text('All Time')")
    pg.wait_for_timeout(2500)
    r = pg.evaluate(PROBE)
    if not rep.check(tag, f"{tag}: dose chart rendered a history line",
                     r and r.get("series"), "" if r and r.get("series") else "no series path"):
        ctx.close()
        return
    width = r["right"] - r["left"]
    start = (r["series"]["min"] - r["left"]) / width
    rep.check(tag, f"{tag}: history line starts at the left edge of the plot",
              start < 0.01, f"starts at {start:.3f} of plot width")
    rep.check(tag, f"{tag}: history line has one point per day",
              abs(r["series"]["n"] - (span + 1)) <= 2,
              f"{r['series']['n']} points, expected ~{span + 1}")
    rep.check(tag, f"{tag}: axis ticks carry no visible year",
              not any(re.search(r"\d{4}", t) for t in r["ticks"]),
              str([t for t in r["ticks"] if re.search(r"\d{4}", t)][:3]))
    ctx.close()


def main():
    rep = Report()
    srv = serve()
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-sandbox"])
            run(rep, br, 525)   # over a year - the case patch 21 fixes
            run(rep, br, 294)   # under a year - must stay correct
            br.close()
    finally:
        srv.shutdown()
    rep.summary()
    raise SystemExit(0 if all(x[2] for x in rep.rows) else 1)


if __name__ == "__main__":
    main()
