#!/usr/bin/env python3
"""
Level is evaluated at the current time, not at midnight (patch 14).

The chart sampled every day at local midnight, so a dose injected today was
still in the future relative to today's sample and contributed nothing. The
24-hour absorption ramp fell entirely between two daily samples, so nothing
appeared to happen until the next day.

The absorption model itself is deliberate and unchanged: a dose ramps linearly
to full over 24 hours, then decays by half-life. That matches tirzepatide's
~24h median Tmax, so the peak genuinely lands about a day after injection.

What this covers: the reported level tracks an independent reimplementation of
that model continuously through the day, including a dose logged earlier today,
across several dose counts and half-lives.

What it does not cover: the pixels of the chart itself. The marker label is
canvas text, and freezing the clock to make positions predictable stops the
dashboard chart rendering - so a pixel assertion here would be measuring the
harness rather than the app. The patcher asserts on both sample sites, and
test_currentlevel covers the marker being drawn.
"""
import math
import re
import sys
from datetime import date, datetime, timedelta
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report  # noqa: E402

PROFILE = {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male",
           "height": 180, "activityLevel": 1.2, "goalWeight": 80}

SEED = """async (d) => {
  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['medications','userProfile'],'readwrite');
    tx.objectStore('medications').clear();
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    tx.objectStore('userProfile').put(d.p); tx.oncomplete=r});
  db.close(); return true; }"""


def build(n_doses, dose_mg, half_life, today):
    """Weekly doses, the most recent at midnight today."""
    return [{"date": str(today - timedelta(days=7 * i)), "medication": "Tirzepatide",
             "dose": dose_mg, "halfLifeHours": half_life, "isManual": True,
             "time": "00:00"} for i in range(n_doses)]


def expected(n_doses, dose_mg, half_life, hours_today):
    """The app's v1 model, reimplemented independently."""
    total = 0.0
    for i in range(n_doses):
        o = hours_today + 24 * 7 * i
        if o < 0:
            continue
        total += dose_mg * (o / 24) if o < 24 else \
            dose_mg * math.exp(-0.693 * (o - 24) / half_life)
    return total


def level(pg):
    m = re.search(r"Current Level\s*\n?\s*([\d.]+)\s*mg", pg.inner_text("body"))
    return float(m.group(1)) if m else None


def main():
    srv = serve()
    rep = Report()
    cases = [("8 weekly 10mg doses, 7-day half-life", 8, 10, 168.0),
             ("4 weekly 5mg doses, 5-day half-life", 4, 5, 120.0),
             ("single dose logged today", 1, 12.5, 168.0)]
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for label, n, mg, hl in cases:
                ctx = b.new_context(viewport={"width": 900, "height": 1000})
                pg = ctx.new_page()
                pg.goto(BASE, wait_until="networkidle")
                pg.wait_for_timeout(1200)

                now = datetime.now()
                today = date(now.year, now.month, now.day)
                pg.evaluate(SEED, {"m": build(n, mg, hl, today), "p": PROFILE})
                pg.reload(wait_until="networkidle")
                pg.wait_for_timeout(2600)
                pg.click("button:has-text('Doses')")
                pg.wait_for_timeout(1600)

                now = datetime.now()          # re-read: loading took real time
                hours = now.hour + now.minute / 60 + now.second / 3600
                want = expected(n, mg, hl, hours)
                got = level(pg)
                rep.check("NOW", f"{label}: level matches the model",
                          got is not None and abs(got - want) < 0.10,
                          f"got {got}mg, model {want:.2f}mg at {hours:.2f}h")
                rep.check("NOW", f"{label}: today's dose already contributing",
                          got is not None and got > 0, f"{got}mg")
                ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
