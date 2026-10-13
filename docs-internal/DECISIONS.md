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

