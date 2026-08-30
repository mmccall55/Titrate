---
updated: 2026-08-30
authority: current
invalidated-by: fixing any of these, or discovering a new one
---

# Open items

Known limitations and backlog. Nothing here is in progress.

## Known limitations

**Dose `time` is discarded.** `parseLocalDate(date)` yields local midnight; the
card samples now, the chart samples midnight per day except today. A fix would
edit the dose-array mapping in `Ege`/`zge` — a separate patch. Known and
accepted.

**Half-life is first-record-wins** per exact medication string. Editing the
half-life on a later dose has no effect on the curve.

**Preset inconsistency inherited from upstream.** The medication picker uses
168/127/120/13/108/120 hours; a demo/seed table elsewhere in the bundle uses 117
for tirzepatide. Not reconciled. Both resolve to Tmax 24, so today it changes
nothing visible.

**A dead fourth `v1` call site.** The hook `Wye` computes a `currentLevel` from
dosing plans that nothing renders — the field appears exactly twice in the
bundle, both as producers. If it is ever wired up it is wrong four ways: it only
sums medications with an active protocol covering the date; it takes half-life
from the protocol and drops the medication silently if that is falsy; it parses
dose dates with `new Date(record.date)` (UTC midnight) instead of
`Ht.parseLocalDate` (local midnight), a 5–6 hour shift in Chicago; and it
matches medications with a lowercasing comparison rather than an exact string.
It still runs `v1` over every dose on every render of the Doses screen and
discards the result.

**No source map, no package toolchain, no source-level unit tests.** The bundle
is the unit; tests are black-box Playwright runs.

**Minified identifiers are stable only for the pinned upstream SHA.**
Re-capturing upstream invalidates every anchor.

## Unresolved

**The original 2026-08-30 report is still undiagnosed.** Marc reported that
older data on the dose chart looked like it was evaluated with the pre-patch-20
algorithm. Established since: the app stores no derived values; there is exactly
one `v1`; at an 8-week span all 110 charted days match the patch-20 model
exactly and none match the old one. The >365-day axis collision was found and
fixed (patch 21) but cannot be the cause — Marc has about 8 weeks of data. The
remaining candidate is two medication strings resolving to different Tmax
values. Needs the medication names in his log, or the peak spacing on his chart.

## Backlog, not committed to

- Honour the dose `time` in the level model.
- Reconcile the 117 vs 127 hour tirzepatide half-life.
- Expose Tmax per medication instead of inferring it from the half-life value.
- Fix or delete the dead `Wye` protocol level path.
- A clean-room rewrite remains the long-term option if the patch chain becomes
  unmanageable. Not warranted; the chain is 21 patches and still reproduces
  byte-for-byte.
