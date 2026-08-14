#!/usr/bin/env python3
"""
Weight-chart period selector (patch 12).

The selector was inert on the weight chart. Two faults combined: the zoom
window was derived from the weight-data span rather than the rendered axis,
and `period` was missing from the chart memo's dependency array - so with a
short history the memo never re-ran at all and the chart stayed stale.

History length is the variable that exposed it, so each case is asserted at a
different length. All four periods must render differently in every case.
"""
import hashlib
import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report  # noqa: E402

SEED = """async (d) => {
  const db = await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['weights','medications','userProfile'],'readwrite');
    tx.objectStore('weights').clear(); tx.objectStore('medications').clear();
    d.w.forEach(x=>tx.objectStore('weights').put(x));
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    tx.objectStore('userProfile').put(d.p); tx.oncomplete=r});
  db.close(); return true; }"""

TODAY = date(2026, 8, 13)
PERIODS = ("Week", "Month", "90 Days", "All Time")
PROFILE = {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male",
           "height": 180, "activityLevel": 1.2, "goalWeight": 80}


def weights(span_days, points):
    step = max(1, span_days // points)
    return [{"date": str(TODAY - timedelta(days=i * step)),
             "weight": round(95 - i * 0.3, 1)} for i in range(points)]


def doses():
    return [{"date": str(TODAY - timedelta(days=i * 7)), "medication": "Tirzepatide",
             "dose": 7.5, "halfLifeHours": 168, "isManual": True, "time": "08:00"}
            for i in range(21)]


def main():
    srv = serve()
    rep = Report()
    cases = [("short history (6 days, 3 points)", 6, 3),
             ("medium history (45 days)", 45, 9),
             ("long history (150 days)", 150, 30)]
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for label, span, pts in cases:
                print(f"\n{label}")
                ctx = b.new_context(viewport={"width": 760, "height": 900})
                pg = ctx.new_page()
                pg.goto(BASE, wait_until="networkidle")
                pg.wait_for_timeout(1200)
                pg.evaluate(SEED, {"w": weights(span, pts), "m": doses(), "p": PROFILE})
                pg.reload(wait_until="networkidle")
                pg.wait_for_timeout(2800)

                shots = {}
                for period in PERIODS:
                    pg.locator(f"button:has-text('{period}')").first.click()
                    pg.wait_for_timeout(1700)
                    host = pg.locator("div[_echarts_instance_]").first
                    host.scroll_into_view_if_needed()
                    pg.wait_for_timeout(400)
                    shots[period] = hashlib.sha256(host.screenshot()).hexdigest()

                distinct = len(set(shots.values()))
                rep.check("PERIOD", f"{label}: all 4 periods render differently",
                          distinct == 4, f"{distinct}/4 distinct")
                for a, bb in ((0, 1), (1, 2), (2, 3)):
                    rep.check("PERIOD", f"{label}: {PERIODS[a]} != {PERIODS[bb]}",
                              shots[PERIODS[a]] != shots[PERIODS[bb]])
                ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
