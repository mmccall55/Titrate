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

**A dead fourth `v1` call site.** The hook `Wye` computes a `currentLevel` from
dosing plans that nothing renders — the field appears exactly twice in the
bundle, both as producers. If it is ever wired up it is wrong four ways: it only
sums medications with an active protocol covering the date; it takes half-life
from the protocol and drops the medication silently if that is falsy; it parses
dose dates with `new Date(record.date)` (UTC midnight) instead of
`__glpalDoseAt` (local date at the recorded time), a 5–6 hour shift in Chicago
before even counting the dose time; and it
matches medications with a lowercasing comparison rather than an exact string.
It still runs `v1` over every dose on every render of the Doses screen and
discards the result.

**No source map, no package toolchain, no source-level unit tests.** The bundle
is the unit; tests are black-box Playwright runs.

**Minified identifiers are stable only for the pinned upstream SHA.**
Re-capturing upstream invalidates every anchor.

## Closed

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
only in the demo-data generator (`WW`, Settings -> Load Sample Data). Published
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

- Fix or delete the dead `Wye` protocol level path.
- A clean-room rewrite remains the long-term option if the patch chain becomes
  unmanageable. Not warranted; the chain is 22 patches and still reproduces
  byte-for-byte.
