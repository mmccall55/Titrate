#!/usr/bin/env python3
"""
Medication storage and dosing plans are hidden (patches 26, 27); the rest of
the app is unaffected. Also keeps the patch-24 check that an active dosing
plan does not crash the Doses screen.

Seeded: four logged doses, ten weights, one active weekly plan, one storage
item - so every hidden element would have something to show.

What this covers:
- Dashboard: no Medication Storage section; weight cards, both charts and
  "Weight Check-in" (formerly "+ Quick Log", patch 28) still render and it
  still opens the daily log
- Doses: no Dosing Plans section and no Cost/Month, Current Dose or Planned
  Doses cards; Total Doses, Current Level and Logged Doses remain and the
  card grid is 4 columns at desktop width (3 remaining + Avg Peak from patch 30); "Log Dose" (formerly "+ Log Dose Manually", patch 28) still opens
- Log: the dose log lists the seeded doses
- no error boundary, no page errors, no request for the never-captured
  MedicationProgressBar chunk
- the seeded plan and storage records are still in the database

Negative control: the patch-25 build fails the "hidden" checks and the grid
check.
"""
import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report  # noqa: E402

MED = "Tirzepatide (Mounjaro/Zepbound)"

SEED = """async (d) => {
  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['medications','protocols','medicationStorage','weights','userProfile'],'readwrite');
    for (const s of ['medications','protocols','medicationStorage','weights']) tx.objectStore(s).clear();
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    d.p.forEach(x=>tx.objectStore('protocols').put(x));
    d.s.forEach(x=>tx.objectStore('medicationStorage').put(x));
    d.w.forEach(x=>tx.objectStore('weights').put(x));
    tx.objectStore('userProfile').put(d.u); tx.oncomplete=r});
  db.close(); return true; }"""

COUNTS = """async () => {
  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  const n=async s=>await new Promise(r=>{const q=db.transaction(s).objectStore(s).count();q.onsuccess=()=>r(q.result)});
  const out={protocols:await n('protocols'),medicationStorage:await n('medicationStorage'),medications:await n('medications')};
  db.close(); return out; }"""

STORES_READY = """() => new Promise(r => { const q = indexedDB.open('GLPalDB');
  q.onsuccess = () => { const ok = q.result.objectStoreNames.contains('protocols');
  q.result.close(); r(ok); }; q.onerror = () => r(false); })"""

DOSES_GRID_COLS = """() => { const t=[...document.querySelectorAll('p')].find(p=>p.textContent.trim()==='Total Doses');
  if (!t) return null; const g=t.closest('.grid'); if (!g) return null;
  return getComputedStyle(g).gridTemplateColumns.split(' ').length; }"""


def seed():
    today = date.today()
    start = today - timedelta(days=24)
    return {
        "m": [{"date": str(start + timedelta(days=7 * i)), "medication": MED, "dose": 5,
               "halfLifeHours": 127, "isManual": True, "time": "08:00"} for i in range(4)],
        "w": [{"date": str(today - timedelta(days=3 * i)), "weight": round(100 - 0.3 * i, 1)}
              for i in range(10)],
        "p": [{"id": "plan-test", "medication": MED, "dose": 5, "frequencyPerWeek": 1,
               "startDate": str(start), "halfLifeHours": 127, "isArchived": False}],
        "s": [{"id": "store-test", "medicationName": MED, "category": "glp1", "type": "pen",
               "dosagePerUnit": 5, "initialUnits": 4, "remainingUnits": 2, "unitCost": 250,
               "purchaseDate": str(start), "expiryDate": "", "notes": "", "isActive": True}],
        "u": {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male", "height": 180,
              "activityLevel": 1.2, "goalWeight": 80},
    }


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1280, "height": 1600}, service_workers="block")
            pg = ctx.new_page()
            errors, chunk = [], []
            pg.on("pageerror", lambda e: errors.append(str(e)[:200]))
            pg.on("request", lambda r: "MedicationProgressBar" in r.url and chunk.append(r.url))
            pg.goto(BASE, wait_until="load")
            pg.wait_for_function(STORES_READY, timeout=15000)
            pg.evaluate(SEED, seed())
            pg.reload(wait_until="load")
            pg.wait_for_timeout(2500)

            print("\nDashboard")
            body = pg.inner_text("body")
            rep.check("HIDE", "old button labels gone",
                      "+ Quick Log" not in body)
            rep.check("HIDE", "Medication Storage section hidden",
                      "Medication Storage" not in body and "Add Storage Item" not in body)
            rep.check("HIDE", "weight cards still render", "Current Weight" in body and "Time Active" in body)
            rep.check("HIDE", "both charts still render",
                      pg.locator("div[_echarts_instance_]").count() >= 2,
                      f"{pg.locator('div[_echarts_instance_]').count()} charts")
            pg.get_by_role("button", name="Weight Check-in", exact=True).click()
            pg.wait_for_timeout(1000)
            rep.check("HIDE", "Weight Check-in button opens the daily log", "Hydration" in pg.inner_text("body"))
            pg.click("button:has-text('Cancel')")
            pg.wait_for_timeout(600)

            print("\nDoses")
            pg.click("button:has-text('Doses')")
            pg.wait_for_timeout(2000)
            body = pg.inner_text("body")
            rep.check("HIDE", "no error boundary with an active plan", "Something went wrong" not in body)
            rep.check("HIDE", "Dosing Plans section hidden",
                      "Dosing Plans" not in body and "Custom Plan" not in body and "+ Schedule" not in body)
            for card in ("Cost/Month", "Current Dose", "Planned Doses"):
                rep.check("HIDE", f"{card} card hidden", card not in body)
            for card in ("Total Doses", "Current Level", "Logged Doses"):
                rep.check("HIDE", f"{card} card remains", card in body)
            rep.check("HIDE", "Log Dose Manually label gone", "Log Dose Manually" not in body)
            cols = pg.evaluate(DOSES_GRID_COLS)
            rep.check("HIDE", "Doses card grid is 4 columns at desktop width (patch 30 adds Avg Peak)", cols == 4, f"{cols} columns")
            pg.get_by_role("button", name="Log Dose", exact=True).click()
            pg.wait_for_timeout(1000)
            rep.check("HIDE", "Log Dose button opens the dose form", "Cancel" in pg.inner_text("body"))
            pg.locator("button", has_text="Cancel").last.click()
            pg.wait_for_timeout(800)

            print("\nLog")
            pg.get_by_role("button", name="Log", exact=True).click()
            pg.wait_for_timeout(1500)
            body = pg.inner_text("body")
            rep.check("HIDE", "dose log lists the seeded doses", body.count(MED) >= 4, f"{body.count(MED)} rows")

            print("\nData")
            counts = pg.evaluate(COUNTS)
            rep.check("HIDE", "plan and storage records untouched",
                      counts["protocols"] == 1 and counts["medicationStorage"] == 1 and counts["medications"] == 4,
                      f"{counts}")
            rep.check("HIDE", "no page errors", not errors, f"{errors}")
            rep.check("HIDE", "missing progress-bar chunk never requested", not chunk, f"{chunk}")
            ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
