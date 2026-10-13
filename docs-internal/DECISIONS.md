---
updated: 2026-10-13
authority: current
invalidated-by: nothing — append-only; a reversed decision gets a new entry, the old one stays
---

# Decisions

One entry per decision that would otherwise be re-litigated. Append-only.

## Surgical patches to the minified bundle, not a rewrite

Fastest path to a working, data-compatible app. A rewrite was explicitly
deferred until the fork proved itself, and it has. Still the long-term option if
the chain becomes unmanageable.

## One patch script per change, chained, SHA-gated in and out

Byte-for-byte reproducibility from the pinned upstream capture. Each script
refuses to run on unexpected input, and each change stays independently
reviewable and droppable.

## Keep the database name `GLPalDB`

Renaming it to match the brand would orphan Marc's real records unless all eight
object stores were migrated on first launch. The name is devtools-only and not
user-visible, so the rebrand condition does not reach it. **Rejected:** renaming
the database.

## Rebrand to "Titrate"

The upstream author granted rehost permission on the condition that the branding
changes. Patch 8 covers user-visible strings in the bundle; `build_fork.py`
covers the shell, manifest and icons.

## Patch 7 touches only `toLocaleDateString` sites

**Rejected:** fixing the date bug at the parse sites feeding `toISOString`.
Those round-trips are UTC-in/UTC-out and correct; localising them would turn a
cosmetic bug in the Americas into a data bug in positive-offset zones.

## Weight chart y-axis bounds to recorded data ∪ goal, projection excluded

The forward projection is extrapolated rather than recorded and was the largest
contributor to the squashed trend. Including the goal in both directions keeps
the goal line on screen whether Marc is above it or has dropped past it.
**Rejected:** including the projection in the bounds.

## Hide, don't remove, Peptides and Calculator

Two anchors instead of unpicking a minified dependency graph, and existing
peptide records stay intact rather than orphaned. **Rejected:** removing them.

## Bateman level model, peak-normalised (patch 20)

Preserves the app's "mg on board" display convention and the Current Level
card's scale while removing the hour-24 kink and the overstated post-peak
decline for medications with Tmax ≈ 48 h.

## Tmax looked up from the stored half-life

Tmax is not stored on dose records, and the preset half-lives are distinct
enough to double as a medication key. **Consequence accepted:** medications
whose half-life maps to Tmax 24 render the same shape as the old model, so
patch 20 is invisible for them.

## Patch 21 keeps `indexOf`, and qualifies the category values instead

Making the category values unique per calendar day makes the existing `indexOf`
lookups exact, which is a far smaller change than converting every lookup to a
positional index across `Pge`, `Vge`, `Rge`, `kge`, both tooltips and the zoom
helper. Ticks keep their previous text via `axisLabel.formatter`.
**Rejected:** ISO date category values with positional indexing.

## Tests are black-box Playwright runs against the built `docs/`

No source-level units exist; the bundle is the unit. Seeds go straight into
IndexedDB.

**Rejected:** pinning test seed dates to a fixed calendar date — it went stale
silently. Seeds are relative to `date.today()`.

**Rejected:** pixel-asserting the chart marker with a frozen clock — freezing
the clock stops the dashboard chart rendering, so the assertion would measure
the harness. Assert on values instead.

**Rejected:** asserting on the today marker's position to detect the axis-year
bug — ECharts resolves a markLine category to the last match, so it passes
against the broken build.

## Documentation is organised by what invalidates a fact (2026-08-30)

One fact, one home. Code-invalidated facts live next to the code — patch
docstrings, test docstrings, `build_fork.py`. Machine-invalidated facts live in
project memory. Preference facts live in account memory. History is archived and
marked non-authoritative. Derived data is generated, never typed.

Measured cause: the same fact was stated in up to 10 files, two 40 KB documents
were byte-identical, and the hand-maintained patch table went stale the moment a
stage was added.

## Chain documents are checked by the build; CHANGELOG.md removed (2026-10-13)

`build_fork.py` stage `[4]` fails if `CHAIN.md` or the identifier table in
`ARCHITECTURE.md` differs from what `make_docs.py` would generate, so a patch
stage added without regenerating the patch table fails the build the same way a
bad SHA does.

`CHANGELOG.md` was deleted. It was generated from `git log`, so every new
commit made it stale until it was regenerated and the commit amended; a full
`--check` in the build would have failed after every commit (verified: one
empty commit on top of `fcab7fd` made `--check` exit 1 on `CHANGELOG.md`). The
commit messages already are the changelog.

**Rejected:** running the full `--check` in the build. **Rejected:** keeping
`CHANGELOG.md` and excluding it from `--check` — it would always lag one
commit.

## Patch 22 honours the dose time, with midnight as the fallback (2026-10-13)

Treating every dose as taken at 00:00 put it up to 24 h early, always in the
same direction, which overstates the level in the first one to two days after a
dose. The fix is at the two places that build model input (`Ege`, `zge`), not
in `v1`, so the model stays byte-identical and the chart's sampling (patch 14)
is unchanged. A missing or unparseable time keeps the old behaviour, so records
without a time read exactly as before.

Accepted limitation: the stored time is when the dose was logged unless edited.

**Rejected:** honouring the time in the card only — the chart's today point
would then disagree with the card.

## Patch 23 removes the unused `Wye` level loop rather than fixing it (2026-10-13)

Nothing renders `currentLevel`, so a correct version would be correct code with
no output. Removing it leaves `v1` with exactly the three callers that agree
with each other (`zge`, both loops in `Vge`), and a future patch cannot wire up
the wrong one by accident. The `currentLevel` key is still produced (always 0)
so the hook's return shape is unchanged.

**Rejected:** fixing it to match the card. **Rejected:** leaving it documented.

## Patch 24 stubs the missing progress-bar chunk instead of hiding plans (2026-10-13)

The chunk cannot be fetched from upstream any more, and no copy was found. A
component that renders nothing keeps dosing plans usable (next due, countdown,
the plan list) at the cost of the progress bar. Stage `[4]` also checks every
dynamic import so a missing chunk fails the build instead of a screen.

**Rejected:** hiding the dosing-plan feature (loses working functionality).
**Deferred:** recovering the original chunk.

## Hide the demo-data button rather than guard it (patch 25, 2026-10-13)

A personal tracker has no use for demo data, and the button's only effect on
real use is to erase the log after one confirm. Same technique as patch 15.

**Rejected:** exporting a CSV before generating demo data — new UI logic for a
feature with no use.

## Clean-room rewrite deferred, with triggers (2026-10-13)

Not warranted: at 25 patches (20 scripts) the chain reproduces byte-for-byte,
and each recent change was one anchored script plus one black-box test.
Upstream publishing a newer bundle (`index-aZASsn-R.js`, seen 2026-10-13) is
not a trigger, because upstream is never re-captured.

Revisit if any of these happens:
- a needed change cannot be anchored in the minified bundle without
  restructuring code across many sites
- a change would require altering the `GLPalDB` schema
- the chain stops reproducing byte-for-byte from the pinned capture
- a patch's anchors start depending on the output of more than one earlier
  patch in ways that make reordering or dropping a patch impractical

## Hide dosing plans and medication storage, don't remove them (patches 26, 27, 2026-10-13)

Marc does not use either feature. Render guards on the sections and their
cards are five anchors; removing the features would mean unpicking stores,
hooks, CSV import/export and dialogs from minified code, and dropping the
stores would break the schema rule. Hiding also makes the plan actions that
clear and rewrite the medications store unreachable.

**Rejected:** removing the features or their stores.

## Dosage calculator sizes the dose to the peak, not to today's level (patch 29, 2026-10-13)

Marc chose "method B": the dose that makes the modelled level peak at the
target, rather than target minus the current level. Because a new tirzepatide
dose peaks ~24 h after it is taken while the existing level keeps decaying,
target minus current level undershoots the target by roughly the 24-hour decay
(about 0.5 mg at a 5 mg weekly steady state). The exact form searches for the
dose whose actual maximum equals the target; reading the level at exactly Tmax
overshoots by up to ~1.2% because the combined level peaks a few hours
earlier.

Tested 2026-10-13 against published tirzepatide PK (FDA Clinical Pharmacology
Review, NDA 215866: dose-proportional 0.25-15 mg, accumulation ratio ~1.6-1.7,
half-life 104-152 h, Tmax 8-96 h). Within the model the result is exact; with
real parameters at the ends of those ranges the realised peak was -10% to
+18.5% of target for a dose 7 days after the last weekly dose, and up to +25%
for a dose 3 days after. Method A carries the same error about 5 points lower.

**Rejected by Marc:** rounding syringe units down; a warning above 15 mg.
**Kept:** exact peak solve; a projected-peak line.

