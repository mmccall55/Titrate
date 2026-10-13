#!/usr/bin/env python3
"""
Doses are placed at their recorded time, not local midnight (patch 22).

Before patch 22 both places that turn dose records into model input - the
Current Level card (`zge`) and the dose chart (`Ege`) - used local midnight of
`record.date` and ignored `record.time`.

What this covers:
- the card value matches an independent reimplementation of the patch-20
  model with each dose placed at its recorded time, for "HH:MM", "H:MM AM/PM",
  and a weekly history, across Tmax 48 and Tmax 24 medications
- each of those cases is discriminating: the midnight placement gives a value
  at least 0.25 mg away (2.5x the 0.10 tolerance), so the check cannot pass
  against the old build
- a missing time and an out-of-range time both fall back to local midnight,
  i.e. exactly the old behaviour
- the dose chart path: a copy of the site in a temp directory is
  string-patched so `Vge` exposes its dose input and its combined past series
  on `window`; the dose Date carries the recorded hour, and today's chart
  point equals the card value. The copy is never written back to docs/.

Negative control: run against the patch-21 build (TITRATE_SITE pointing at
it). The three "placed at recorded time" checks and the chart-hour check must
FAIL there; the two midnight-fallback checks pass on both builds.
"""
import math
import re
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from testlib import serve, BASE, FORK, Report  # noqa: E402

PROFILE = {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male",
           "height": 180, "activityLevel": 1.2, "goalWeight": 80}

SEED = """async (d) => {
  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['medications','userProfile'],'readwrite');
    tx.objectStore('medications').clear();
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    tx.objectStore('userProfile').put(d.p); tx.oncomplete=r});
  db.close(); return true; }"""

# Debug hook for the chart path, applied to a temp copy only.
HOOK_ANCHOR = "const c={},d={},h=new Set,v={};r.forEach(T=>{c[T]=new Set"
HOOK_X_ANCHOR = 'r.length>0&&y.push({name:"Combined"'


def model(doses, half_life, at):
    """patch-20 v1, reimplemented. doses = [(datetime, mg)]."""
    t = half_life if half_life > 0 else 168.0
    ke = math.log(2) / t
    tmax = {168: 48, 127: 24, 120: 24, 108: 48, 13: 11}.get(t, min(48.0, max(6.0, 0.2 * t)))
    tmax = min(tmax, 0.95 / ke)
    lo, hi = ke * 1.000001, ke * 1e3
    for _ in range(80):
        mid = (lo + hi) / 2
        if math.log(mid / ke) / (mid - ke) > tmax:
            lo = mid
        else:
            hi = mid
    ka = (lo + hi) / 2

    def f(o):
        return 0.0 if o < 0 else ka / (ka - ke) * (math.exp(-ke * o) - math.exp(-ka * o))

    pk = f(tmax)
    return sum(mg * f((at - when).total_seconds() / 3600) / pk for when, mg in doses)


def rec(day, mg, hl, time=None):
    r = {"date": str(day), "medication": "TestMed", "dose": mg,
         "halfLifeHours": hl, "isManual": True}
    if time is not None:
        r["time"] = time
    return r


def at_midnight(day):
    return datetime(day.year, day.month, day.day)


def dose_slot(now):
    """A dose time 4+ hours ago whose time of day is at least 06:00.

    Placing the dose relative to now keeps it on the rising part of the curve
    for every medication here, and keeping its time of day >= 06:00 means the
    midnight placement is at least 6 hours earlier. Together that guarantees
    the recorded-time and midnight models differ by >= 0.25 mg at any time of
    day the test runs (checked over a full day in 5-minute steps). Fixed
    clock times do not: for Tmax-24 medications the two curves cross near the
    peak, so a fixed "yesterday 20:00" case stops discriminating at some times
    of day.
    """
    c = (now - timedelta(hours=4)).replace(second=0, microsecond=0)
    if c.hour < 6:
        c = datetime(c.year, c.month, c.day, 23, 0) - timedelta(days=1)
    return c


def hhmm(d):
    return f"{d.hour:02d}:{d.minute:02d}"


def ampm(d):
    return f"{(d.hour % 12) or 12}:{d.minute:02d} {'PM' if d.hour >= 12 else 'AM'}"


def cases(now):
    d = dose_slot(now)
    day = d.date()
    weekly = [d - timedelta(days=7 * i) for i in range(4)]
    y = now.date() - timedelta(days=1)
    return [
        # label, records, half-life, recorded-time doses, midnight doses, expect_recorded
        (f"HH:MM '{hhmm(d)}', 168h", [rec(day, 10, 168, hhmm(d))], 168,
         [(d, 10)], [(at_midnight(day), 10)], True),
        (f"AM/PM '{ampm(d)}', 120h", [rec(day, 10, 120, ampm(d))], 120,
         [(d, 10)], [(at_midnight(day), 10)], True),
        (f"weekly x4 at '{hhmm(d)}', 127h", [rec(w.date(), 10, 127, hhmm(w)) for w in weekly], 127,
         [(w, 10) for w in weekly], [(at_midnight(w.date()), 10) for w in weekly], True),
        ("no time field -> midnight", [rec(y, 10, 168)], 168,
         None, [(at_midnight(y), 10)], False),
        ("out-of-range '25:00' -> midnight", [rec(y, 10, 168, "25:00")], 168,
         None, [(at_midnight(y), 10)], False),
    ]


def level(pg):
    m = re.search(r"Current Level\s*\n?\s*([\d.]+)\s*mg", pg.inner_text("body"))
    return float(m.group(1)) if m else None


def hooked_copy():
    tmp = Path(tempfile.mkdtemp(prefix="titrate-dosetime-"))
    site = tmp / "site"
    shutil.copytree(FORK, site)
    js = site / "assets" / "app" / "index-DwosoAbB.js"
    s = js.read_text(encoding="utf-8")
    assert s.count(HOOK_ANCHOR) == 1, "Vge dose-input anchor"
    assert s.count(HOOK_X_ANCHOR) == 1, "Vge combined-series anchor"
    s = s.replace(HOOK_ANCHOR, "window.__dbgE=e;" + HOOK_ANCHOR, 1)
    s = s.replace(HOOK_X_ANCHOR, "(window.__dbgX=x)," + HOOK_X_ANCHOR, 1)
    js.write_text(s, encoding="utf-8")
    sw = site / "sw.js"          # no service worker in the copy
    sw.write_text("", encoding="utf-8")
    return tmp, site


def load(b, seed):
    ctx = b.new_context(viewport={"width": 900, "height": 1000}, service_workers="block")
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="load")
    pg.wait_for_function("""() => new Promise(r => { const q = indexedDB.open('GLPalDB');
        q.onsuccess = () => { const ok = q.result.objectStoreNames.contains('medications');
        q.result.close(); r(ok); }; q.onerror = () => r(false); })""", timeout=15000)
    pg.evaluate(SEED, {"m": seed, "p": PROFILE})
    pg.reload(wait_until="load")
    pg.wait_for_timeout(2600)
    pg.click("button:has-text('Doses')")
    pg.wait_for_timeout(1600)
    return ctx, pg


def main():
    tmp, site = hooked_copy()
    srv = serve(site)
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for label, seed, hl, rec_doses, mid_doses, expect_recorded in cases(datetime.now()):
                ctx, pg = load(b, seed)
                now = datetime.now()
                got = level(pg)
                want_mid = model(mid_doses, hl, now)
                if expect_recorded:
                    want = model(rec_doses, hl, now)
                    rep.check("TIME", f"{label}: card uses the recorded time",
                              got is not None and abs(got - want) < 0.10,
                              f"got {got}, recorded-time model {want:.2f}, midnight model {want_mid:.2f}")
                    rep.check("TIME", f"{label}: case discriminates (|recorded - midnight| >= 0.25)",
                              abs(want - want_mid) >= 0.25, f"{abs(want - want_mid):.2f} mg apart")
                else:
                    rep.check("TIME", f"{label}: card uses local midnight",
                              got is not None and abs(got - want_mid) < 0.10,
                              f"got {got}, midnight model {want_mid:.2f}")

                if label.startswith("HH:MM"):
                    dh = rec_doses[0][0]
                    e = pg.evaluate("() => window.__dbgE && Object.fromEntries(Object.entries(window.__dbgE)"
                                    ".map(([k,v]) => [k, v.map(x => [x.date.getHours(), x.date.getMinutes()])]))")
                    x = pg.evaluate("() => window.__dbgX && window.__dbgX.length ? window.__dbgX[window.__dbgX.length-1][1] : null")
                    rep.check("TIME", "chart path: dose input carries the recorded hour",
                              e is not None and e.get("TestMed") == [[dh.hour, dh.minute]],
                              f"{e}, recorded {hhmm(dh)}")
                    rep.check("TIME", "chart path: today's point equals the card",
                              x is not None and got is not None and abs(x - got) < 0.10,
                              f"chart {x}, card {got}")
                ctx.close()
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
