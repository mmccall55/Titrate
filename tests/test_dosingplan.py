#!/usr/bin/env python3
"""
The app works with an active dosing plan (patch 24).

Before patch 24 the plan card lazily imported
`../MedicationProgressBar-CpSrqVLQ.js`, a chunk that was never captured. With
any active dosing plan the import 404'd and the error boundary replaced the
screen with "Oops! Something went wrong".

What this covers: with one active weekly plan and four logged doses, the
Dashboard and the Doses screen both render without the error boundary, the
Doses screen lists the plan, and the Current Level card shows a value. It also
asserts no request for the missing chunk is made.

What it does not cover: the progress bar itself, which patch 24 replaces with
nothing.

Negative control: the patch-23 build fails the error-boundary checks.
"""
import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report  # noqa: E402

MED = "Tirzepatide (Mounjaro/Zepbound)"
ERROR_TEXT = "Something went wrong"

SEED = """async (d) => {
  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['medications','protocols','userProfile'],'readwrite');
    tx.objectStore('medications').clear(); tx.objectStore('protocols').clear();
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    tx.objectStore('protocols').put(d.p);
    tx.objectStore('userProfile').put(d.u); tx.oncomplete=r});
  db.close(); return true; }"""

STORES_READY = """() => new Promise(r => { const q = indexedDB.open('GLPalDB');
  q.onsuccess = () => { const ok = q.result.objectStoreNames.contains('protocols');
  q.result.close(); r(ok); }; q.onerror = () => r(false); })"""


def seed():
    today = date.today()
    start = today - timedelta(days=24)
    plan = {"id": "plan-test", "medication": MED, "dose": 5, "frequencyPerWeek": 1,
            "startDate": str(start), "halfLifeHours": 127, "isArchived": False}
    doses = [{"date": str(start + timedelta(days=7 * i)), "medication": MED, "dose": 5,
              "halfLifeHours": 127, "isManual": True, "time": "08:00"} for i in range(4)]
    profile = {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male",
               "height": 180, "activityLevel": 1.2, "goalWeight": 80}
    return {"m": doses, "p": plan, "u": profile}


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 900, "height": 1400}, service_workers="block")
            pg = ctx.new_page()
            chunk_requests = []
            pg.on("request", lambda r: "MedicationProgressBar" in r.url and chunk_requests.append(r.url))
            pg.goto(BASE, wait_until="load")
            pg.wait_for_function(STORES_READY, timeout=15000)
            pg.evaluate(SEED, seed())
            pg.reload(wait_until="load")
            pg.wait_for_timeout(2500)

            body = pg.inner_text("body")
            rep.check("PLAN", "Dashboard renders with an active plan",
                      ERROR_TEXT not in body, body[:80].replace("\n", " | "))

            pg.click("button:has-text('Doses')")
            pg.wait_for_timeout(2000)
            body = pg.inner_text("body")
            rep.check("PLAN", "Doses screen renders with an active plan",
                      ERROR_TEXT not in body, body[:80].replace("\n", " | "))
            rep.check("PLAN", "Doses screen lists the plan",
                      "Dosing Plans" in body and MED in body)
            rep.check("PLAN", "Current Level card shows a value",
                      "Current Level" in body and "mg" in body.split("Current Level", 1)[-1][:20])
            rep.check("PLAN", "missing chunk is never requested",
                      not chunk_requests, f"{chunk_requests}")
            ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
