#!/usr/bin/env python3
"""
Dosage calculator (patch 29) and Avg Peak (14d) card (patch 30).

Checked against an independent Python reimplementation of the patch-20 model
with patch-22 dose times:

Calculator
- for several targets, the shown dose matches the exact method-B dose: the
  dose taken now that makes the maximum of the modelled level over the next
  7 days equal the target (bisection over a linear model)
- that dose really does make the independent model peak at the target
- the 10 and 15 mg/ml lines are dose/10 and dose/15 ml to 2 decimals, and
  units are ml * 100 rounded to the nearest unit
- the peak line shows the target to 1 decimal
- a target below what the current doses already reach shows "No dose needed"

Avg Peak (14d)
- equals the mean of the independent model's local maxima in the last 336 h
- a dose whose peak is still ahead is not counted
- no peaks in the window shows "--"

Layout: the four Doses cards are 2 columns at phone width and 4 at desktop.

Negative control: the patch-28 build has no calculator and no card, so every
check fails there.
"""
import math
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from testlib import serve, BASE, Report  # noqa: E402

MED = "Tirzepatide (Mounjaro/Zepbound)"
HL = 127
STEP_H = 0.25

SEED = """async (d) => {
  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['medications','userProfile'],'readwrite');
    tx.objectStore('medications').clear();
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    tx.objectStore('userProfile').put(d.u); tx.oncomplete=r});
  db.close(); return true; }"""
STORES_READY = """() => new Promise(r => { const q = indexedDB.open('GLPalDB');
  q.onsuccess = () => { const ok = q.result.objectStoreNames.contains('medications');
  q.result.close(); r(ok); }; q.onerror = () => r(false); })"""
GRID_COLS = """() => { const t=[...document.querySelectorAll('p')].find(p=>p.textContent.trim()==='Total Doses');
  const g=t&&t.closest('.grid'); return g?getComputedStyle(g).gridTemplateColumns.split(' ').length:null; }"""
PROFILE = {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male", "height": 180,
           "activityLevel": 1.2, "goalWeight": 80}


def unit_curve(hl):
    t = hl if hl > 0 else 168.0
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
    return lambda hours: f(hours) / pk


F = unit_curve(HL)


def level(doses, at):
    return sum(mg * F((at - when).total_seconds() / 3600) for when, mg in doses)


def exact_b(doses, target, now):
    n = int(7 * 24 / STEP_H)
    ts = [now + timedelta(hours=i * STEP_H) for i in range(n + 1)]
    base = [level(doses, t) for t in ts]
    unit = [F(i * STEP_H) for i in range(n + 1)]

    def peak(d):
        return max(b + d * u for b, u in zip(base, unit))
    if peak(0) >= target:
        return None
    lo, hi = 0.0, target
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if peak(mid) < target else (lo, mid)
    return (lo + hi) / 2


def avg_peak(doses, now):
    a = now - timedelta(hours=336)
    st = timedelta(hours=STEP_H)
    pv, cu, peaks, t = level(doses, a - st), level(doses, a), [], a + st
    while t <= now:
        nx = level(doses, t)
        if cu > pv and cu >= nx and cu > 0:
            peaks.append(cu)
        pv, cu, t = cu, nx, t + st
    return sum(peaks) / len(peaks) if peaks else None


def records(dose_times, mg):
    return [{"date": d.strftime("%Y-%m-%d"), "time": d.strftime("%H:%M"), "medication": MED,
             "dose": mg, "halfLifeHours": HL, "isManual": True} for d in dose_times]


def minute(d):
    return d.replace(second=0, microsecond=0)


def open_doses(b, recs, width=1280):
    ctx = b.new_context(viewport={"width": width, "height": 1600}, service_workers="block")
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="load")
    pg.wait_for_function(STORES_READY, timeout=15000)
    pg.evaluate(SEED, {"m": recs, "u": PROFILE})
    pg.reload(wait_until="load")
    pg.wait_for_timeout(2000)
    pg.get_by_role("button", name="Doses", exact=True).click()
    pg.wait_for_timeout(1500)
    return ctx, pg


def card_value(pg, label):
    m = re.search(re.escape(label) + r"\s*\n?\s*([\d.]+mg|--)", pg.inner_text("main"))
    return m.group(1) if m else None


def calc_text(pg):
    loc = pg.locator("[data-glpal='dose-calc']")
    return loc.inner_text() if loc.count() else ""


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            now0 = minute(datetime.now())
            # weekly 5 mg; latest 30 h ago, so its peak (~6 h ago) is inside the window
            weekly = [now0 - timedelta(hours=30 + 168 * i) for i in range(6)]
            doses = [(minute(d), 5.0) for d in weekly]

            print("\nCalculator")
            ctx, pg = open_doses(b, records(weekly, 5.0))
            present = pg.locator("#glpalTarget").count() == 1
            rep.check("CALC", "calculator is under Log Dose", present)
            if present:
                for target in (10.1, 12.5, 15.3):
                    pg.fill("#glpalTarget", str(target))
                    pg.wait_for_timeout(700)
                    txt = calc_text(pg)
                    now = minute(datetime.now())
                    want = exact_b(doses, target, now)
                    m = re.search(r"Dose\s*([\d.]+) mg", txt)
                    got = float(m.group(1)) if m else None
                    rep.check("CALC", f"target {target}: dose matches exact method B",
                              got is not None and want is not None and abs(got - want) < 0.02,
                              f"app {got}, independent {want:.3f}" if want else f"app {got}")
                    if got is not None:
                        pk = max(level(doses + [(now, got)], now + timedelta(hours=i * STEP_H))
                                 for i in range(int(168 / STEP_H) + 1))
                        rep.check("CALC", f"target {target}: that dose peaks at the target",
                                  abs(pk - target) < 0.02, f"independent peak {pk:.3f}")
                        for c in (10, 15):
                            v = got / c
                            exp = f"{v:.2f} ml ({round(v * 100)} units)"
                            mm = re.search(rf"{c} mg/ml vial\s*([\d.]+ ml \(\d+ units\))", txt)
                            shown = mm.group(1) if mm else None
                            # app rounds from its unrounded dose; allow a 1-unit / 0.01 ml difference
                            ok = shown is not None and abs(float(shown.split()[0]) - v) <= 0.0051 + 1e-9 \
                                and abs(int(re.search(r"\((\d+)", shown).group(1)) - v * 100) <= 0.5 + 0.01
                            rep.check("CALC", f"target {target}: {c} mg/ml line", ok, f"{shown} vs {exp}")
                        mp = re.search(r"Peak\s*≈\s*([\d.]+) mg in ~(\d+) h", txt)
                        rep.check("CALC", f"target {target}: peak line shows the target",
                                  mp is not None and abs(float(mp.group(1)) - target) < 0.051,
                                  mp.group(0) if mp else txt.replace("\n", " | "))
                low = 0.5
                pg.fill("#glpalTarget", str(low))
                pg.wait_for_timeout(700)
                rep.check("CALC", "target below current reach shows 'No dose needed'",
                          "No dose needed" in calc_text(pg) and exact_b(doses, low, minute(datetime.now())) is None)
                pg.fill("#glpalTarget", "")
                pg.wait_for_timeout(400)
                rep.check("CALC", "empty target shows no result", "Dose" not in calc_text(pg))

            print("\nAvg Peak (14d)")
            got = card_value(pg, "Avg Peak (14d)")
            want = avg_peak(doses, datetime.now())
            rep.check("PEAK", "matches the mean of the model's peaks in the last 14 days",
                      got not in (None, "--") and want is not None and abs(float(got[:-2]) - want) < 0.02,
                      f"app {got}, independent {want:.3f}" if want else f"app {got}")
            cols = pg.evaluate(GRID_COLS)
            rep.check("PEAK", "4 cards in one row at desktop width (1280 px; lg starts at 1024)", cols == 4, f"{cols} columns")
            ctx.close()

            # a dose 4 h ago: its peak is still ahead and must not be counted
            recent = weekly + [now0 - timedelta(hours=4)]
            ctx, pg = open_doses(b, records(recent, 5.0))
            got = card_value(pg, "Avg Peak (14d)")
            want = avg_peak([(minute(d), 5.0) for d in recent], datetime.now())
            rep.check("PEAK", "a peak still ahead is not counted",
                      got not in (None, "--") and abs(float(got[:-2]) - want) < 0.02,
                      f"app {got}, independent {want:.3f}")
            ctx.close()

            # nothing for 40 days: no peaks in the window
            old = [now0 - timedelta(days=40 + 7 * i) for i in range(3)]
            ctx, pg = open_doses(b, records(old, 5.0), width=390)
            rep.check("PEAK", "no peaks in the window shows --", card_value(pg, "Avg Peak (14d)") == "--",
                      f"{card_value(pg, 'Avg Peak (14d)')}")
            cols = pg.evaluate(GRID_COLS)
            rep.check("PEAK", "2 columns at phone width", cols == 2, f"{cols} columns")
            ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
