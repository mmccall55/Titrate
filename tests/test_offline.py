#!/usr/bin/env python3
"""
Service worker, offline cold launch, and data-egress checks for fork/.

  1  service worker registers and activates
  2  every shell file is precached
  3  cold launch with the network cut serves the whole app from cache
  4  doses can be added and edited while offline, and persist across an offline reload
  5  no request ever leaves the origin
"""
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, dose, meds, Report, SEED_JS, BASE, FORK  # noqa: E402

TITLE = 'h2:text-is("Edit Dose")'


def main():
    srv = serve()
    rep = Report()
    offsite = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context()
            ctx.on("request", lambda r: offsite.append(r.url)
                   if not r.url.startswith(BASE) and not r.url.startswith("data:") else None)

            # ---------------------------------------------------- 1. register
            print("\n1. service worker registration")
            pg = ctx.new_page()
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_timeout(1500)
            state = pg.evaluate("""async () => {
              const r = await navigator.serviceWorker.ready;
              return { scope: r.scope, script: r.active && r.active.scriptURL,
                       state: r.active && r.active.state };
            }""")
            rep.check("SW", "worker is active", state["state"] == "activated", str(state["state"]))
            rep.check("SW", "scope covers the app", state["scope"] == BASE, state["scope"])

            # ---------------------------------------------------- 2. precache
            print("\n2. precache contents")
            cached = pg.evaluate("""async () => {
              const names = await caches.keys();
              const out = {};
              for (const n of names) out[n] = (await (await caches.open(n)).keys()).map(r => r.url);
              return out;
            }""")
            rep.check("SW", "exactly one cache", len(cached) == 1, str(list(cached)))
            urls = set(sum(cached.values(), []))
            on_disk = sorted(p2.relative_to(FORK).as_posix() for p2 in FORK.rglob("*")
                             if p2.is_file() and p2.name not in {"sw.js", ".nojekyll", "robots.txt"})
            missing = [f for f in on_disk if BASE + f not in urls]
            rep.check("SW", f"all {len(on_disk)} shell files cached", not missing, str(missing[:4]))
            rep.check("SW", "navigation root cached", BASE in urls)

            # ---------------------------------------------------- 3. cold launch offline
            print("\n3. cold launch with the network cut")
            pg.evaluate(SEED_JS, [dose("2026-08-10", "OfflineMed", 2.5)])
            pg.close()
            ctx.set_offline(True)

            pg2 = ctx.new_page()
            failed = []
            pg2.on("requestfailed", lambda r: failed.append(r.url))
            errs = []
            pg2.on("pageerror", lambda e: errs.append(str(e)[:120]))
            pg2.goto(BASE, wait_until="load")
            pg2.wait_for_timeout(2500)
            rep.check("OFFLINE", "app renders with no network",
                      pg2.eval_on_selector("#root", "e => e.children.length") > 0)
            rep.check("OFFLINE", "no failed requests", not failed, str(failed[:3]))
            rep.check("OFFLINE", "no page errors", not errs, str(errs[:2]))
            rep.check("OFFLINE", "seeded dose is visible",
                      "OfflineMed" in pg2.inner_text("body"))

            # ---------------------------------------------------- 4. edit offline
            print("\n4. editing while offline")
            pg2.click("button:has-text('Log')")
            pg2.wait_for_timeout(1000)
            pg2.locator("button:has-text('Edit')").first.click()
            pg2.wait_for_selector(TITLE, timeout=5000)
            pg2.locator(TITLE).locator("..").locator('input[type="number"]').first.fill("4")
            pg2.locator(TITLE).locator("..").locator("button:has-text('Save')").click()
            pg2.wait_for_selector(TITLE, state="detached", timeout=5000)
            pg2.wait_for_timeout(800)
            recs, _ = meds(pg2)
            rep.check("OFFLINE", "edit saved while offline",
                      len(recs) == 1 and recs[0]["dose"] == 4, str(recs[0]["dose"] if recs else "-"))

            pg2.reload(wait_until="load")
            pg2.wait_for_timeout(2000)
            recs2, _ = meds(pg2)
            rep.check("OFFLINE", "survives an offline reload", recs2 == recs)

            # ---------------------------------------------------- 5. egress
            print("\n5. data egress")
            ctx.set_offline(False)
            pg2.reload(wait_until="networkidle")
            pg2.wait_for_timeout(2000)
            rep.check("PRIVACY", "no request left the origin", not offsite, str(sorted(set(offsite))[:5]))

            # ------------------------------------------------ extra: date display
            print("\n6. date handling (upstream behaviour, not patch-related)")
            shown = pg2.inner_text("body")
            pg2.locator("button:has-text('Edit')").first.click()
            pg2.wait_for_selector(TITLE, timeout=5000)
            raw = pg2.locator(TITLE).locator("..").locator('input[type="date"]').input_value()
            rep.check("DATE", "editor loads the stored date verbatim", raw == "2026-08-10", raw)
            tz = pg2.evaluate("Intl.DateTimeFormat().resolvedOptions().timeZone + ' offset ' + new Date().getTimezoneOffset()")
            print(f"     browser timezone: {tz}")
            print(f"     list shows 'Aug 9' for stored 2026-08-10: {'Aug 9' in shown}")

            ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
