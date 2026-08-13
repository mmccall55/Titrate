# Titrate

A private, offline GLP-1 tracker. Log doses, weight, and side effects — and
**correct them afterwards**.

No account. No server. No analytics. Every health record stays in your browser's
IndexedDB on your own device.

Titrate is a rebranded, patched build of the GLPal web app, rehosted with the
original author's written permission. See [Attribution](#attribution).

## Why this exists

The app it is built from has no way to edit a dose once logged. Mistyped a dose,
logged the wrong day, changed medication mid-protocol — all of it was permanent.
For a tracker whose whole purpose is an accurate history, that is a fatal flaw.

Fixing it surfaced five further defects. All are fixed here.

## What changed

Upstream is distributed only as a minified production bundle, so these are
surgical patches against that bundle rather than edits to a source tree. Each
stage is hash-pinned: it verifies its input, asserts an exact match count for
every replacement, and verifies its own output. A stage that does not find
exactly what it expects fails rather than guessing.

| # | Change | Kind |
|---|---|---|
| 1 | `deleteDose` deleted from the **weights** table instead of `medications` — doses could never actually be deleted | Bug fix |
| 2 | Added a transactional `updateDose` handling the `[date+medication]` compound primary key | Feature |
| 3 | Exposed `updateDose` through the application store | Feature |
| 4 | Added an Edit Dose dialog (date, time, medication, dose, pain level, injection site, ISR, notes) with Delete | Feature |
| 5 | Side-effects/notes matched records **by date alone**, so two medications logged on one day overwrote each other's notes | Bug fix |
| 6 | Added an Edit button to each manual dose in the Dose Log | Feature |
| 7 | Dates displayed one day early in every negative-UTC-offset timezone (all of the Americas) | Bug fix |
| 8 | Rebrand to Titrate | Branding |
| 9 | Goal-weight picker flashed open and vanished — it was a child of the settings modal, which unmounted as the picker opened | Bug fix |
| 10 | Goal weight rendered through the **height** formatter: 195 lb displayed as "35 in" | Bug fix |
| 11 | Weight chart y-axis was unbounded, so the forward projection squashed the real trend into ~16% of the plot | Bug fix |

Beyond the patch chain the build also adds a **service worker** (upstream has
none — it was installable but refetched 1.8 MB on every cold launch),
**self-hosts the fonts**, and **recolours** the palette from purple to a muted
orange.

### Notes on specific fixes

Changing a dose's date or medication changes its primary key, so the update runs
as a single Dexie transaction: delete the old key, insert the new record. Never
two records, never a lost one.

Patch 7 touches **display code only**. Three sites parse a date, add an offset,
then re-serialise with `toISOString()`; UTC-parse paired with UTC-serialise
round-trips correctly, and switching those to local parsing would return the
wrong day in positive-offset timezones. Those paths are deliberately untouched.

Patch 11 bounds the axis to recorded weights **union the goal**, in both
directions, so the goal line stays visible whether you are above it or have
dropped below it. The extrapolated projection is excluded from the bounds — it
was the largest contributor to the squashing.

The recolour preserves each colour's WCAG relative luminance, moving only hue
and saturation, so every contrast ratio in the UI is unchanged. It rewrites
colours in all four notations they appear in: `#RRGGBB`, `#RGB`, comma-separated
`rgb()`, and Tailwind's space-separated `rgb(r g b / a)`.

The IndexedDB database is still named `GLPalDB`. That name is not user-visible,
and keeping it means data exported from the original app imports without a
migration. The build asserts exactly one occurrence so it cannot drift.

## Privacy

- All records live in IndexedDB on your device
- No account, no sync, no telemetry, no third-party requests
- The optional Google Drive backup in the original code is never invoked
- The host serves static files only and never receives your data

IndexedDB is scoped per **origin**, not per path. Everything served from
`mmccall55.github.io` shares one database namespace. Moving to a different
domain means your history does not follow — export first.

## Rebuilding

Everything needed is in `tools/`, including the upstream capture. Requires
Python 3 and, for the tests, `pip install playwright && playwright install
chromium`.

```bash
cd tools
python3 make_icons.py                       # regenerate brand assets
python3 make_palette.py                     # regenerate the colour map
GLPAL_DEST=.. python3 build_fork.py         # build the site into the repo root
```

`build_fork.py` runs the whole chain: verify ZIP → verify upstream bundle →
patches 1-11 → recolour → assemble → self-verify → write output. It aborts on
any hash mismatch rather than producing a questionable artifact.

```
upstream     a561c9f0a86560313b7165758e131b3140807482ba140922035c810f0d7f5631
+ fixes 1-6  dbea7baaff958b56a4567c1a984c9b7a46ef696b792412bd1279e7433f75236e
+ fix 7      13971fbc564d4b3df7c6317ad65843b64d1b5c58ea9fc1fcc07b6efcfd68e67f
+ fix 8      4d5953e0277df472e98da30315afda51bee0bab43de9b2021844bf03a10e148a
+ fix 9      cd67d85fc07934caf3c2e23395fc713660ddda0fe611cea244470029a3761aff
+ fix 10     e1330709887aeb115ac65dc0023e9372e8c7056b1161d77a51a703d1773a66ab
+ fix 11     37638391810ef2babbee71c5482db5c6bc49fe8d3163b2a9a54d78326b4dfd69
```

The recolour runs after patch 11, so the shipped bundle's hash differs from the
last line above; it is deterministic given the same `palette.json`.

## Tests

**77 automated checks** in headless Chromium:

```bash
cd tools
python3 test_regression.py   # 18  dose edit/delete, compound-key changes, cross-contamination
python3 test_offline.py      # 13  service worker, precache, offline cold launch, zero egress
python3 test_dates.py        # 30  date correctness across five timezones, UTC-7 to UTC+9
python3 test_goalweight.py   # 16  goal-weight picker lifecycle and unit conversion
```

`test_dates.py` checks both directions — what is displayed *and* what is
stored — because patch 7 changes display code only and the risk was a write-path
regression.

## Install

Open the site on your phone and use "Add to Home Screen". After that it works
offline; the host is only needed for updates, a new device, or if you clear site
data.

## Layout

```
index.html, sw.js, assets/, fonts/   the deployable site (GitHub Pages serves from root)
tools/                               patchers, build script, tests, upstream capture
tools/glpal-upstream.zip             upstream assets captured 2026-08-13, hash-pinned
```

## Attribution

Titrate is a modified build of the GLPal web application, rehosted with the
original author's written permission, granted on the condition that the branding
differs from the original. The name, wordmark, and icons here are accordingly
distinct; no affiliation with or endorsement by the original author is implied.

Not medical advice. Verify your own dosing records.
