#!/usr/bin/env python3
"""
Timezone correctness for patch 7.

Two directions, because patch 7 deliberately changes only display code:

  READ   a dose stored as 2026-08-10 must display as Aug 10 in every timezone
  WRITE  the stored key must stay 2026-08-10 after an edit, in every timezone
         (this is the regression patch 7 could plausibly have introduced)

Negative offsets (Americas) exposed the original bug; positive offsets (Tokyo)
are where a naive global fix would have corrupted the toISOString round-trip.
"""
import re
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, dose, meds, Report, SEED_JS, BASE  # noqa: E402

TITLE = 'h2:text-is("Edit Dose")'
ZONES = [
    ("America/Los_Angeles", "UTC-7  worst negative offset"),
    ("America/Chicago", "UTC-5  your timezone"),
    ("UTC", "UTC+0  baseline"),
    ("Europe/Berlin", "UTC+2  small positive"),
    ("Asia/Tokyo", "UTC+9  worst positive offset"),
]
STORED = "2026-08-10"


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for tz, label in ZONES:
                print(f"\n{tz}  ({label})")
                ctx = b.new_context(timezone_id=tz)
                pg = ctx.new_page()
                pg.goto(BASE, wait_until="networkidle")
                pg.wait_for_timeout(1200)
                pg.evaluate(SEED_JS, [dose(STORED, "TzMed", 2.5)])
                pg.reload(wait_until="networkidle")
                pg.wait_for_timeout(1800)

                # ---- READ: what the Dose Log row shows
                pg.click("button:has-text('Log')")
                pg.wait_for_timeout(1000)
                body = pg.inner_text("body")
                m = re.search(r"Aug (\d+), 2026", body)
                shown = m.group(0) if m else "(not found)"
                rep.check(tz, f"log row displays Aug 10 (got {shown})", shown == "Aug 10, 2026")

                # ---- editor shows the stored value verbatim
                pg.locator("button:has-text('Edit')").first.click()
                pg.wait_for_selector(TITLE, timeout=5000)
                panel = pg.locator(TITLE).locator("..")
                raw = panel.locator('input[type="date"]').input_value()
                rep.check(tz, "editor date matches stored", raw == STORED, raw)

                # ---- WRITE: edit an unrelated field, key must not drift
                panel.locator('input[type="number"]').first.fill("3.5")
                panel.locator("button:has-text('Save')").click()
                pg.wait_for_selector(TITLE, state="detached", timeout=5000)
                pg.wait_for_timeout(800)
                recs, _ = meds(pg)
                rep.check(tz, "stored key unchanged after edit",
                          len(recs) == 1 and recs[0]["date"] == STORED,
                          recs[0]["date"] if recs else "-")
                rep.check(tz, "dose value written", recs and recs[0]["dose"] == 3.5)

                # ---- WRITE: change the date explicitly, must land exactly
                pg.locator("button:has-text('Edit')").first.click()
                pg.wait_for_selector(TITLE, timeout=5000)
                panel = pg.locator(TITLE).locator("..")
                panel.locator('input[type="date"]').fill("2026-08-11")
                panel.locator("button:has-text('Save')").click()
                pg.wait_for_selector(TITLE, state="detached", timeout=5000)
                pg.wait_for_timeout(800)
                recs, _ = meds(pg)
                rep.check(tz, "explicit date change lands exactly",
                          len(recs) == 1 and recs[0]["date"] == "2026-08-11",
                          recs[0]["date"] if recs else "-")
                body = pg.inner_text("body")
                rep.check(tz, "and displays as Aug 11", "Aug 11, 2026" in body)

                ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
