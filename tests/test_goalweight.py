#!/usr/bin/env python3
"""Goal-weight picker: opens, stays open, saves, and persists (patch 9)."""
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report

PROFILE = """async () => {
  const db = await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  const v = await new Promise(r=>{const rq=db.transaction('userProfile','readonly').objectStore('userProfile').getAll();rq.onsuccess=()=>r(rq.result)});
  db.close(); return v; }"""

def main():
    srv = serve(); rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(); ctx = b.new_context(); pg = ctx.new_page()
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(1800)

            print("\n1. the picker opens and stays open")
            pg.locator("button[aria-label='Settings']").click(); pg.wait_for_timeout(1000)
            pg.locator("button", has_text="Goal").first.click()
            pg.wait_for_timeout(400)
            early = pg.evaluate("document.querySelectorAll('input').length")
            pg.wait_for_timeout(1800)
            late = pg.evaluate("document.querySelectorAll('input').length")
            rep.check("GW", "picker renders inputs", late > 0, f"{late}")
            rep.check("GW", "still present after 2s (no flash-and-vanish)", late >= early and late > 0,
                      f"400ms={early} 2s={late}")
            rep.check("GW", "no page errors", not errs, str(errs[:2]))
            body = pg.inner_text("body")
            rep.check("GW", "shows the Goal Weight label", "Goal Weight" in body)

            print("\n2. entering and saving a value")
            # value selection is a touch scroll-wheel; it cannot be driven
            # faithfully headlessly, so this asserts the save path only
            done = pg.locator("button:has-text('Done')").last
            rep.check("GW", "Done button present", done.count() > 0)
            done.click(); pg.wait_for_timeout(1500)

            print("\n3. returns to settings rather than closing everything")
            after = pg.inner_text("body")
            rep.check("GW", "settings still open after save",
                      "Goal Weight" in after or "User Settings" in after,
                      pg.url.split('#')[-1])

            print("\n4. the value persisted")
            prof = pg.evaluate(PROFILE)
            gw = prof[0].get("goalWeight") if prof else None
            rep.check("GW", "goalWeight written to userProfile", gw is not None, str(gw))

            pg.reload(wait_until="networkidle"); pg.wait_for_timeout(2000)
            prof2 = pg.evaluate(PROFILE)
            gw2 = prof2[0].get("goalWeight") if prof2 else None
            rep.check("GW", "survives reload", gw2 == gw, str(gw2))

            print("\n5. cancel path")
            pg.locator("button[aria-label='Settings']").click(); pg.wait_for_timeout(900)
            # after a save the button shows the value, not "Set goal weight"
            pg.locator("label:has-text('Goal Weight')").locator("..").locator("button").first.click()
            pg.wait_for_timeout(1200)
            cancel = pg.locator("button:has-text('Cancel')").last
            if cancel.count():
                cancel.click(); pg.wait_for_timeout(1200)
                prof3 = pg.evaluate(PROFILE)
                rep.check("GW", "cancel leaves the value unchanged",
                          (prof3[0].get("goalWeight") if prof3 else None) == gw)
                rep.check("GW", "cancel returns to settings",
                          "Goal Weight" in pg.inner_text("body") or "User Settings" in pg.inner_text("body"))

            print("\n6. unit conversion on the goal-weight label (patch 10)")
            SETP = """async (prof) => {
              const db = await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
              const cur = await new Promise(r=>{const rq=db.transaction('userProfile','readonly').objectStore('userProfile').getAll();rq.onsuccess=()=>r(rq.result)});
              const rec = Object.assign({}, cur[0]||{}, prof);
              await new Promise(r=>{const tx=db.transaction('userProfile','readwrite');
                tx.objectStore('userProfile').put(rec); tx.oncomplete=r});
              db.close(); return true; }"""
            for units, stored, expect_val, expect_unit in [
                ("imperial", 88.45, "195", "lbs"),
                ("metric",   88.45, "88.5", "kg"),
            ]:
                pg.evaluate(SETP, {"unitSystem": units, "goalWeight": stored, "age": 35, "height": 180})
                pg.reload(wait_until="networkidle"); pg.wait_for_timeout(2200)
                pg.locator("button[aria-label='Settings']").click(); pg.wait_for_timeout(1200)
                label = pg.locator("label:has-text('Goal Weight')").locator("..").locator("button").first.inner_text().strip()
                rep.check("UNIT", f"{units}: {stored}kg shows a weight unit, not inches",
                          "in" != label.split()[-1], label)
                rep.check("UNIT", f"{units}: unit is {expect_unit}", label.endswith(expect_unit), label)
                rep.check("UNIT", f"{units}: value is {expect_val}", label.startswith(expect_val), label)
                pg.locator("button:has-text('Close')").last.click(); pg.wait_for_timeout(800)
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1

if __name__ == "__main__":
    sys.exit(main())
