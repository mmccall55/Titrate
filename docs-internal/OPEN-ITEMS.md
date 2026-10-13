---
updated: 2026-10-13
authority: current
invalidated-by: fixing any of these, or discovering a new one
---

# Open items

Known limitations and backlog. Nothing here is in progress.

## Known limitations

**Half-life is first-record-wins** per exact medication string. Editing the
half-life on a later dose has no effect on the curve.

**Upstream is not frozen.** As of 2026-10-13 `https://glpal.app/app/` serves
`assets/app/index-aZASsn-R.js`, not the pinned `index-DwosoAbB.js`. The pinned
capture is unaffected; the "abandoned" label is out of date.

**No source map, no package toolchain, no source-level unit tests.** The bundle
is the unit; tests are black-box Playwright runs.

**Minified identifiers are stable only for the pinned upstream SHA.**
Re-capturing upstream invalidates every anchor.

## Closed

**Dosing plans and medication storage. Hidden 2026-10-13 by patches 26 and 27**
at Marc's request. This also retires the Planned Doses count-to-2099 problem
(the card is hidden) and makes patch 24's empty progress bar unreachable.

**Settings "Load Sample Data (Demo)" erased all data after one confirm. Fixed
2026-10-13 by patch 25.** The button no longer renders; the generator code
remains in the bundle, unreachable.

**Doses screen crashed when a dosing plan was active. Fixed 2026-10-13 by patch
24.** The plan card lazily imported `../MedicationProgressBar-CpSrqVLQ.js`, a
chunk that was never captured and that glpal.app no longer serves; the 404
reached the error boundary. Patch 24 replaces the import with a component that
renders nothing, so the plan's progress bar is gone. Stage `[4]` of the build
now fails if any dynamic `import()` target is missing. The crash was live on the
patch-21 site. Recovering the original chunk is not planned; the dosing-plan feature is
slated for removal (see Backlog).

**Unused fourth `v1` call site in `Wye`. Fixed 2026-10-13 by patch 23.** The
dosing-plan hook computed a `currentLevel` nothing renders, using a calculation
wrong in four ways (plan-only medications, plan half-life, UTC-midnight dates
without dose time, normalised name matching). Its loop is removed;
`currentLevel` is always 0 and `v1` has three callers. In practice the loop only
ran with an active dosing plan, which currently crashes the Doses screen (see
Known limitations), so no working screen ever exercised it.

**Tmax per medication. Closed 2026-10-13, no change.** Tmax stays inferred from
the half-life (`__glpalTmax`). For picker entries the table value is exact
(semaglutide 48 h, tirzepatide 24 h, matching published Tmax). Known gaps,
accepted: a custom medication whose half-life is not in the table gets
`clamp(0.2 * t, 6, 48)`; medications sharing a half-life share a Tmax
(cagrilintide with semaglutide at 168 h, Custom with retatrutide at 120 h). If
that matters later, the smallest fix is a name-based lookup before the
half-life table, which needs no schema change.

**Tirzepatide half-life, 117 h vs 127 h. Closed 2026-10-13, no change.** 127 h
is the medication-picker preset and is what dose records store. 117 h appears
only in the demo-data generator (`WW`), unreachable since patch 25. Published
values: study geometric means 104-152 h for subcutaneous dosing (FDA Clinical
Pharmacology Review, NDA 215866, study GPGA Parts A-C and GPGC); population-PK
mean 5.4 days, about 130 h, in T2DM at steady state (CPT Pharmacometrics Syst
Pharmacol 2024, PMC10962491); the label rounds to "approximately 5 days". Both
values are inside the measured range, and 127 h resolves to Tmax 24 h while
117 h resolves to 23.4 h, so the curves are effectively identical.

**Dose `time` was discarded. Fixed 2026-10-13 by patch 22.** Doses are placed
at their recorded time in both the card and the chart; no time means local
midnight as before.

**2026-08-30 report: older dose-chart data looked like the pre-patch-20
algorithm. Closed 2026-10-13, not reproduced.** Marc chose to close it rather
than export his data for a replay. What was established before closing: the app
stores no derived values; there is exactly one `v1`; at an 8-week span all 110
charted days of a seeded test matched the patch-20 model and none matched the
old one; the >365-day axis collision (patch 21) could not be the cause. The only
candidate left untested was two medication strings resolving to different Tmax
values (see GOTCHAS, "Patch 20 is invisible for medications whose Tmax resolves
to 24 h"). If the effect is seen again, reopen with a CSV export from
Settings -> Data Management -> Import / Export CSV and replay it through the
bundle.

## Backlog, not committed to

Empty. The clean-room rewrite moved to DECISIONS.md with explicit triggers.
