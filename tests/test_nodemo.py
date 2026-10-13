#!/usr/bin/env python3
"""
Settings has no "Load Sample Data (Demo)" button (patch 25).

Upstream's button erased every store after a single window.confirm and
replaced the user's log with demo data.

What this covers: the Settings modal opens, the Data Management section still
offers Import / Export CSV, and the demo-data button is absent. Seeded doses
are still present after the modal is opened and closed.

Negative control: the patch-24 build fails "demo-data button is absent".
"""
import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report, SEED_JS, DUMP_JS, dose  # noqa: E402

STORES_READY = """() => new Promise(r => { const q = indexedDB.open('GLPalDB');
  q.onsuccess = () => { const ok = q.result.objectStoreNames.contains('medications');
  q.result.close(); r(ok); }; q.onerror = () => r(false); })"""


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 900, "height": 1400}, service_workers="block")
            pg = ctx.new_page()
            pg.on("dialog", lambda d: d.dismiss())     # never confirm anything
            pg.goto(BASE, wait_until="load")
            pg.wait_for_function(STORES_READY, timeout=15000)
            seed = [dose(str(date.today() - timedelta(days=7 * i)), "Tirzepatide", 5) for i in range(3)]
            pg.evaluate(SEED_JS, seed)
            pg.reload(wait_until="load")
            pg.wait_for_timeout(2000)

            # settings is the gear button in the header
            pg.locator("button[aria-label='Settings']").click()
            pg.wait_for_timeout(1200)
            body = pg.inner_text("body")
            rep.check("DEMO", "Settings opened", "Data Management" in body, body[:60].replace("\n", " | "))
            rep.check("DEMO", "Import / Export CSV still offered", "Import / Export CSV" in body)
            rep.check("DEMO", "demo-data button is absent", "Load Sample Data" not in body)

            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            recs = pg.evaluate(DUMP_JS)["medications"]
            rep.check("DEMO", "seeded doses untouched", len(recs) == 3, f"{len(recs)} records")
            ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
