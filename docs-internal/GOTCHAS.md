---
updated: 2026-10-13
authority: current
invalidated-by: nothing — entries are only added, or struck through when a fix removes the trap
---

# Gotchas

Hard-won negative results. Each entry cost real time to discover. Read this
before debugging a chart, writing a test, or touching the build.

## Charting

**ECharts matches `[label, value]` series data to a category axis by name, first
match wins.** Duplicate category names silently stack points on top of each
other. This is what broke both charts past 365 days of history before patch 21.

**But a markLine's category name resolves to the LAST match.** So the "today"
marker sat in the correct position even while the series split was completely
wrong. A first version of `test_axisyear.py` asserted on the marker's x position
and passed against the known-broken build. Do not use the today marker to detect
axis problems. Assert on the solid history line's left edge and point count
instead.

**Patch 20 is invisible for medications whose Tmax resolves to 24 h.** A
Tmax-24 Bateman curve is shape-equivalent to the old 24-hour ramp model — max
difference 0.034 mg per 1 mg dose over 8 weeks. Only half-life 168 and 108
(Tmax 48 h) changed visibly. If part of a chart "looks like the old algorithm",
the likely cause is a second medication resolving to a different Tmax, not a
second code path. Diagnostic you can read off the chart: a peak one day after a
dose means Tmax 24; two days means Tmax 48.

**Half-life is first-record-wins per exact medication string.** Editing the
half-life on a later dose changes nothing. Two spellings of the same drug are
two independent series.

**The dose-change marker on the dose chart is keyed to the dose date + 1 day**
(`new Date(M.date.getTime() + 864e5)`). Pre-existing upstream behaviour, kept
deliberately. Do not "fix" it without checking what it lines up with.

**`Vge` drops the combined series entirely when only one medication is tracked**
— `[...(meds.length > 1 ? combined : []), ...perMed]`. A first attempt at the
patch-13 current-level marker appended it to that dropped array and rendered
nothing.

**Freezing the clock stops the dashboard chart rendering.** So a pixel assertion
with a frozen clock measures the harness, not the app. `test_samplenow.py`
asserts on values instead, and re-reads the wall clock after page load because
loading takes real time.

## Dates

**`new Date("2026-08-10")` is UTC midnight**, so `toLocaleDateString` in the
Americas shows the previous day. But the three-argument form
`new Date(y, m-1, d)` is already local and correct — patch 7's regex excludes it
via a no-comma character class.

**Do not localise the `toISOString` round-trips.** Sites doing
`new Date(s) → setTime → toISOString().split("T")[0]` are UTC-in/UTC-out and
correct. Localising them turns a cosmetic bug in the Americas into a data bug in
positive-offset time zones. Patch 7 asserts none were touched.

~~**The dose `time` field is discarded** by the level model. Everything is local
midnight.~~ Fixed by patch 22: doses are placed at their recorded time, local
midnight only when there is no valid time.

## Build

**Lazily imported chunks are invisible to a resource sweep and to stage
`[4]`.** The bundle has two dynamic `import()` targets: `../web-BkP7LE0t.js`
(captured separately) and `../MedicationProgressBar-CpSrqVLQ.js` (never
captured; the Doses screen crashes when a dosing plan is active). Find them
with a regex over the bundle for `import("../` rather than trusting the
upstream ZIP. glpal.app answers unknown paths with 200 `text/html`, so a
status-code check against upstream is not evidence a file exists.

**`docs/` is post-recolour.** Patch anchors lifted from `docs/` will not match,
because the patches run before the recolour stage. Colour literals in anchors
must be the original purple — `#B19CD9`, and `rgba(156, 123, 211, …)` in chart
axis styling.

**`make_palette.py` reads `build/.artifacts/titrate-index-chart.js`**, which is
gitignored. Regenerating the palette on a fresh clone fails until the build has
run once. Its own docstring warns against the related mistake — rescanning
`fork/`, which is already recoloured — but not this one.

**Order of operations matters inside a patch.** Patch 17 had to delete the
standalone `Hge` render *before* inserting the same call into the grid,
otherwise the removal anchor matched twice.

## Environment

**The project folder mount blocks unlinks.** Git cannot clean up its own
`.git/*.lock` files, so a crashed run leaves a lock that blocks every later
commit — a `HEAD.lock` from 2026-08-27 and an `index.lock` from 2026-08-28 were
both still sitting there. Request delete permission for the folder once per
session and clear them before staging.

**`build_fork.py` assembles in scratch space and mirrors in** for the same
reason. It never deletes stale files; it warns about them instead.

**A proxy 403 on `git push` is not a network or credential failure.** Git sends
its first request unauthenticated, so no credential is transmitted at all; the
container's proxy rejects it before the token is ever sent. Force preemptive
auth with `http.extraHeader`. An invalid-token probe returning the same error as
no token is therefore not evidence about the token.

**Missing DNS in a proxy-only sandbox is normal**, not evidence of "no network".

**The desktop browser pane has its own profile.** `GLPalDB` reads zero records
there. That is not Marc's data.

**GitHub Pages serves a stale `sw.js` on a plain reload.** Always verify a
deploy with a cache-busting query string.

## Testing

**A test that passes against the known-broken build is measuring the wrong
thing.** Always run the negative control before believing a green result. Ask
what the test would show if the hypothesis were false.

**`test_offline.py` compares the SW cache against every file under `FORK`** and
cannot pass on a partial copy of `docs/`. Stage the whole tree, fonts included.

**Since patch 22, a seed's dose `time` moves the curve.** A fixed clock time
such as `"08:00"` makes a level-dependent assertion depend on when the test
runs: before 08:00 today's dose has not started. `test_currentlevel.py` broke
this way — its label dropped out of the band it samples — and now seeds
`"00:00"`. For Tmax-24 medications the recorded-time and midnight curves cross
near the peak, so a fixed dose time also stops distinguishing patch 22 from
the old build at some times of day; `test_dosetime.py` places its doses
relative to now for that reason.

**Keep test seeds relative to `date.today()`.** `test_currentlevel.py` was once
pinned to 2026-08-13 and went stale silently.

**`testlib.py` needs three adaptations to run in the cloud container** —
threading server, `wait_until="load"`, and waiting for the `medications` store
to exist before seeding. They are deliberately not committed; see WORKFLOW.

## Method

**Determine what the code does by running it, not by asking Marc for his data.**
His records only identify which candidate is firing for him; they never
determine behaviour. Enumerate candidates from the source, then build a seeded
experiment with a control.

**To read internal chart state, string-patch a throwaway copy of the bundle in
the container** so it hangs the values off `window` — for example capturing
`Vge`'s `x`, `b`, `o` and `s` where they are created. Never in `docs/`; the copy
is diagnostic only and is never committed.

**Hold negative conclusions to a much higher bar than positive ones.** A
negative claims something about every possible approach; one counterexample
destroys it. Say "I haven't found a way", not "it can't be done", and when Marc
pushes back, attack the experiment rather than defending the conclusion.
