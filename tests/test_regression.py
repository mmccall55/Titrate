#!/usr/bin/env python3
"""
Regression cases A-E from GLPAL_HANDOFF.md section 21, run against fork/
in headless Chromium. Each case gets a fresh browser context (fresh IndexedDB).

  A  change only the dose amount      -> same compound key, overwritten, no duplicate
  B  change the date                  -> old key deleted, new key inserted
  C  change the medication            -> old key deleted, new key inserted
  D  delete                           -> medication removed, weights untouched
  E  two medications on one date      -> side-effects/notes hit only the matching record

Usage: python3 test_regression.py [-v]
"""
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, open_app, dose, meds, Report, SEED_JS  # noqa: E402

TITLE = 'h2:text-is("Edit Dose")'
VERBOSE = "-v" in sys.argv


def panel(pg):
    """The editor panel: the direct parent of the 'Edit Dose' heading."""
    return pg.locator(TITLE).locator("..")


def open_editor(pg, row=0):
    """Switch to the Log tab and open the dose editor for the given row."""
    pg.click("button:has-text('Log')")
    pg.wait_for_timeout(1000)
    pg.locator("button:has-text('Edit')").nth(row).click()
    pg.wait_for_selector(TITLE, timeout=5000)
    pg.wait_for_timeout(300)


def field(pg, kind, index=0):
    return panel(pg).locator(kind).nth(index)


def set_fields(pg, date=None, time=None, medication=None, dose_mg=None,
               pain=None, site=None, notes=None):
    if date is not None:
        field(pg, 'input[type="date"]').fill(date)
    if time is not None:
        field(pg, 'input[type="time"]').fill(time)
    if medication is not None:
        field(pg, 'input[type="text"]', 0).fill(medication)
    if dose_mg is not None:
        field(pg, 'input[type="number"]', 0).fill(str(dose_mg))
    if pain is not None:
        field(pg, 'input[type="number"]', 1).fill(str(pain))
    if site is not None:
        field(pg, 'input[type="text"]', 1).fill(site)
    if notes is not None:
        field(pg, "textarea").fill(notes)


def save(pg):
    panel(pg).locator("button:has-text('Save')").click()
    pg.wait_for_selector(TITLE, state="detached", timeout=5000)
    pg.wait_for_timeout(700)


def delete(pg):
    pg.once("dialog", lambda d: d.accept())
    panel(pg).locator("button:has-text('Delete')").click()
    pg.wait_for_selector(TITLE, state="detached", timeout=5000)
    pg.wait_for_timeout(700)


def keys(records):
    return [(r["date"], r["medication"]) for r in records]


# ------------------------------------------------------------------ cases
def case_a(b, rep):
    print("\nA. change only the dose amount")
    ctx, pg = open_app(b, seed=[dose("2026-08-10", "ZZTestMed", 2.5)])
    open_editor(pg)
    set_fields(pg, dose_mg=5)
    save(pg)
    recs, _ = meds(pg)
    rep.check("A", "exactly one record remains", len(recs) == 1, f"{len(recs)}")
    rep.check("A", "dose updated to 5", recs and recs[0]["dose"] == 5,
              str(recs[0]["dose"]) if recs else "-")
    rep.check("A", "compound key unchanged", keys(recs) == [("2026-08-10", "ZZTestMed")], str(keys(recs)))
    rep.check("A", "unedited fields preserved (halfLifeHours)",
              recs and recs[0].get("halfLifeHours") == 168)
    pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1200)
    recs2, _ = meds(pg)
    rep.check("A", "survives reload", recs2 == recs)
    ctx.close()


def case_b(b, rep):
    print("\nB. change the date")
    ctx, pg = open_app(b, seed=[dose("2026-08-10", "ZZTestMed", 2.5)])
    open_editor(pg)
    set_fields(pg, date="2026-08-11")
    save(pg)
    recs, _ = meds(pg)
    rep.check("B", "exactly one record remains", len(recs) == 1, f"{len(recs)}")
    rep.check("B", "old key [2026-08-10, ZZTestMed] deleted",
              ("2026-08-10", "ZZTestMed") not in keys(recs), str(keys(recs)))
    rep.check("B", "new key [2026-08-11, ZZTestMed] present",
              ("2026-08-11", "ZZTestMed") in keys(recs))
    rep.check("B", "dose carried over", recs and recs[0]["dose"] == 2.5)
    ctx.close()


def case_c(b, rep):
    print("\nC. change the medication name")
    ctx, pg = open_app(b, seed=[dose("2026-08-10", "MedA", 2.5)])
    open_editor(pg)
    set_fields(pg, medication="MedB")
    save(pg)
    recs, _ = meds(pg)
    rep.check("C", "exactly one record remains", len(recs) == 1, f"{len(recs)}")
    rep.check("C", "old key [2026-08-10, MedA] deleted",
              ("2026-08-10", "MedA") not in keys(recs), str(keys(recs)))
    rep.check("C", "new key [2026-08-10, MedB] present",
              ("2026-08-10", "MedB") in keys(recs))
    ctx.close()


def case_d(b, rep):
    print("\nD. delete a dose (and prove weights are untouched)")
    ctx, pg = open_app(b, seed=[dose("2026-08-10", "ZZTestMed", 2.5)])
    pg.evaluate("""async () => {
      const db = await new Promise(r => { const q = indexedDB.open('GLPalDB'); q.onsuccess = () => r(q.result); });
      await new Promise(r => { const tx = db.transaction('weights','readwrite');
        tx.objectStore('weights').put({date:'2026-08-10', weight:82.5}); tx.oncomplete = r; });
      db.close();
    }""")
    before_recs, before_w = meds(pg)
    open_editor(pg)
    delete(pg)
    recs, weights = meds(pg)
    rep.check("D", "medication record removed", len(recs) == 0, f"{len(recs)} left")
    rep.check("D", "weights table untouched", len(weights) == 1 and weights[0]["weight"] == 82.5,
              str(weights))
    ctx.close()


def case_e(b, rep):
    print("\nE. two medications on one date - side-effects/notes targeting")
    seed = [dose("2026-08-10", "MedA", 2.5), dose("2026-08-10", "MedB", 7.5)]
    ctx, pg = open_app(b, seed=seed)
    pg.click("button:has-text('Log')")
    pg.wait_for_timeout(1000)

    rows = pg.locator("button:has-text('Side Effects')").count()
    rep.check("E", "both doses render their own controls", rows == 2, f"{rows} rows")
    if rows != 2:
        ctx.close()
        return

    # figure out which row is MedA
    texts = pg.eval_on_selector_all(
        "button:has-text('Side Effects')",
        "els => els.map(e => e.closest('div[class]') ? e.closest('div[class]').parentElement.innerText : '')")
    target = 0 if "MedA" in (texts[0] or "") else 1

    pg.locator("button:has-text('Side Effects')").nth(target).click()
    pg.wait_for_timeout(900)
    ta = pg.locator("textarea").last
    ta.fill("NOTE-FOR-MEDA-ONLY")
    for label in ["Save", "Done", "Apply"]:
        btn = pg.locator(f"button:has-text('{label}')").last
        if btn.count() and btn.is_visible():
            btn.click()
            break
    pg.wait_for_timeout(1200)

    recs, _ = meds(pg)
    by = {r["medication"]: r for r in recs}
    rep.check("E", "both records still exist", set(by) == {"MedA", "MedB"}, str(sorted(by)))
    if set(by) == {"MedA", "MedB"}:
        rep.check("E", "note written to MedA", by["MedA"].get("notes") == "NOTE-FOR-MEDA-ONLY",
                  repr(by["MedA"].get("notes")))
        rep.check("E", "MedB notes NOT touched (this is Fix 5)",
                  not by["MedB"].get("notes"), repr(by["MedB"].get("notes")))
    ctx.close()


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for fn in (case_a, case_b, case_c, case_d, case_e):
                try:
                    fn(b, rep)
                except Exception as exc:
                    rep.check(fn.__name__, f"raised {type(exc).__name__}", False, str(exc)[:160])
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
