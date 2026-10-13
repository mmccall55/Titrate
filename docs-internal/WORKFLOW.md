---
updated: 2026-10-13
authority: current
invalidated-by: a change to the build chain, the test harness, or how the site is deployed
---

# Workflow

How to change Titrate safely. For what the app is, see [ARCHITECTURE.md](ARCHITECTURE.md).
Machine-specific values — checkout path, where the GitHub token lives — are in
project memory (`environment.md`), not here.

## The rule

**Never hand-edit `docs/assets/app/index-DwosoAbB.js`.**

Every change is a new `build/glpal_patchNN_<name>.py` that takes the previous
stage's output, asserts its input and output SHA-256, and is wired into
`build/build_fork.py`.

Why: there is no React source. The only guarantee of correctness is that the
whole chain reproduces byte-for-byte from the pinned upstream capture and
refuses to run on unexpected input.

## Non-negotiables

1. Never hand-edit the shipped bundle.
2. Never change the `GLPalDB` schema — store names, key paths, record shapes.
   The database name stays `GLPalDB`.
3. Never re-capture upstream. Every anchor and identifier is valid only for the
   pinned SHA.
4. Never commit health data. `exports/`, `backups/`, `private-data/`, `*.pat`
   are gitignored for that reason.
5. Ask Marc before pushing. A push redeploys the PWA he uses daily.

## Adding a change

**1. Find the anchor in the last artifact in the chain**, currently
`build/.artifacts/titrate-index-dosetime.js` (patch 22 output). Run the build
once to generate it — `.artifacts/` is gitignored.

Do **not** take anchors from `docs/`. `docs/` is post-recolour, so any colour
literal in an anchor must be the original purple (`#B19CD9`, and
`rgba(156, 123, 211, …)` in chart axis styling), never the shipped `#D69A5A`.

Generate long minified literals from the artifact. Do not retype them.

**2. Write `build/glpal_patchNN_<name>.py`.** Docstring format, in this order:

```
Symptom     what the user sees
Cause       the mechanism, named precisely
Fix         what changes and why that is the right place
What this deliberately does NOT change
Usage       python glpal_patchNN_<name>.py IN.js OUT.js
```

Assertions the script must make:

- `EXPECTED_INPUT_SHA256` matches, refuse otherwise
- every anchor occurs exactly the expected number of times, usually 1
- any new helper name is **absent** from the input
- anything that must stay untouched is still there — patch 14 asserts `v1` is
  unchanged, patch 12 asserts the dose chart's zoom is unchanged, patch 21
  asserts `v1`'s body survives byte-identical
- a global count invariant where one exists — patch 21 asserts the short-date
  call sites drop from 19 to 11, which catches an anchor matching somewhere
  unintended
- print the output SHA, then pin `EXPECTED_OUTPUT_SHA256` and re-run

**3. Wire it into `build/build_fork.py`**: a new `EXPECTED_<X>_SHA` constant, a
new block in `patch()`, and repoint `SHIP_SHA`.

**4. Regenerate the generated docs.** Do this before building.

```
python3 build/make_docs.py
```

Writes `docs-internal/CHAIN.md`, `INDEX.md`, and the identifier table inside
`ARCHITECTURE.md`. It reads `build_fork.py` and the patch scripts statically, so
it does not need a build first. Stage `[4]` of the build fails if `CHAIN.md` or
the identifier table is stale (`make_docs.py --check-chain`). `INDEX.md` is not
checked by the build; `make_docs.py --check` covers all three.

There is no `CHANGELOG.md`. Commit messages are written as user-visible
effects, so the changelog is:

```
git log --reverse --date=short --format='%ad  %s'
```

**5. Build.**

```
python3 build/build_fork.py
```

Stages: `[1]` extract upstream ZIP (SHA-checked) → `[2]…[2p]` every patch, SHA
in and out → `[3a]` recolour → `[3]` assemble (icons, index.html rewrite,
manifest, generated `sw.js`, `.nojekyll`, `robots.txt`) → `[4]` verify (no
external requests, no missing references, every precache entry exists, exactly
one `GLPal` string left in the bundle — the DB name — icons are the rebranded
ones, `CHAIN.md` and the identifier table current, every dynamic `import()`
target present) → `[5]` mirror into `docs/`.

Must print through the last patch stage, `[3] fork assembled` and `[4]` ok
with no `FAIL`. A `FAIL` at `[4]` stops before `[5]`, so `docs/` is not
touched. `git status` should then be clean if nothing actually changed.

`node --check docs/assets/app/index-DwosoAbB.js` if node is available.

`GLPAL_WORK`, `GLPAL_ARTIFACTS` and `GLPAL_DEST` override the build's temp,
artifact and output directories.

**6. Add or extend a test in `tests/`.** Keep seeds relative to `date.today()`.
A test pinned to a fixed calendar date goes stale silently.

**7. Commit** the patch script, `build_fork.py`, the regenerated `docs/`, the
regenerated `docs-internal/`, and the test. One-line message stating the
user-visible effect, e.g. "fix the weight chart period selector".

## Tests

Black-box Playwright (Python sync API) against a static server of `docs/` on
port 8099. `tests/testlib.py` provides `serve()`, `open_app(browser, seed)`,
IndexedDB seed/dump/clear JS, a `dose()` record factory, and a `Report` with
PASS/FAIL rows. Each test is a standalone script; run each and read the
`N/N checks passed` line.

| test | covers |
|---|---|
| `test_regression.py` | cases A–E: edit amount (same key), change date (key move), change medication (key move), delete (weights untouched), two meds one date (side-effects hit the right record) |
| `test_dates.py` | patch 7 display dates across five timezones, both read and write |
| `test_goalweight.py` | patches 9/10 — picker stays open, saves, persists, label in lb/kg |
| `test_chartperiod.py` | patch 12 — all four periods render differently at three history lengths |
| `test_currentlevel.py` | patch 13 — marker drawn, label not clipped, empty state |
| `test_samplenow.py` | patches 14/20 — card value tracks an independent Bateman reimplementation within 0.10 mg |
| `test_offline.py` | SW precache, offline cold launch, offline edit, zero egress |
| `test_axisyear.py` | patch 21 — history line starts at the left edge with one point per day, above and below a year |
| `test_nodemo.py` | patch 25 — Settings has no demo-data button; Import / Export CSV remains; seeded data untouched |
| `test_dosecalc.py` | patches 29, 30 — calculator dose matches an independent exact method-B solve and peaks at the target; ml/unit lines; No dose needed; Avg Peak matches independent peak detection, excludes a peak still ahead, `--` with none; grid 2 / 4 columns |
| `test_hiddenfeatures.py` | patches 24, 26, 27, 28 — button labels renamed; with a plan and a storage item seeded, storage and plans are hidden, remaining cards, Quick Log, Log Dose, Dose Log and charts work, no crash, chunk never requested, records untouched |
| `test_dosetime.py` | patch 22 — card and chart place doses at their recorded time (HH:MM, AM/PM, weekly history); missing or bad time falls back to midnight; negative control is the patch-21 build |

### Running tests in the cloud container

The device VM has no Playwright. Stage `docs/` and `tests/` into the container,
point `TITRATE_SITE` at the staged `docs/`, and run each script. Stage the whole
`docs/` tree — `test_offline.py` compares the service worker cache against every
file on disk and cannot pass on a partial copy.

`testlib.py` needs three adaptations to run there, which are **not** committed
because a normal local checkout does not need them:

- `socketserver.ThreadingTCPServer` instead of `TCPServer` — the single-threaded
  server deadlocks on `page.reload()`
- `wait_until="load"` instead of `"networkidle"`
- wait for `objectStoreNames.contains('medications')` before seeding, otherwise
  the seed races Dexie's first open

Launch Chromium with `executable_path='/opt/pw-browsers/chromium'` and
`--no-sandbox`.

## Git

Branch `main`, remote `origin = https://github.com/mmccall55/Titrate.git`.

**Clear stale lock files first.** The project folder mount allows writes but not
unlinks, so git cannot clean up its own `.git/*.lock` files and a crashed run
leaves one that blocks every later commit. Request delete permission for the
project folder once per session, then:

```
find .git -name '*.lock' -delete
```

Do this before staging, not after hitting the error.

## Deploy

The device VM can commit but its egress does not reach github.com, so the push
goes through the cloud container.

1. commit on the device
2. `git bundle create <file> origin/main..main`, copy the bundle into the
   project folder, stage it along with the token file
3. in the container: fetch origin, then
   `git fetch <bundle> main:refs/heads/main`
4. push with a preemptive auth header:

```
git -c http.extraHeader="Authorization: Basic $(printf 'x-access-token:%s' \
  "$(tr -d '\r\n' < <token-file>)" | base64 -w0)" push origin main
```

   Git sends its first request unauthenticated and only presents credentials
   after a 401. On that anonymous request the container's git proxy tries to
   inject its own credential, finds the repo unattached to the session, and
   returns 403 — so the token is never transmitted. `http.extraHeader` forces
   preemptive auth on every request. **A proxy 403 is not evidence that the
   network or the token is broken.**

5. back on the device: `git update-ref refs/remotes/origin/main <newsha>` so the
   next bundle range is correct, and delete the bundle file

## Verify a deploy

GitHub Pages serves `docs/`. The container cannot reach github.io; use the
desktop browser pane.

- **navigate** the pane to `sw.js?cb=<anything>` and check the
  `titrate-<fingerprint>` cache name matches what the build printed; then
  navigate to `assets/app/index-DwosoAbB.js?cb=<anything>` and hash
  `document.body.innerText` against the build's `docs/` bundle SHA
- do **not** use `fetch()` from an app page: once the worker controls the page,
  asset requests are answered from its cache with `ignoreSearch: true`, so a
  cache-busting query still returns the previous version. Navigations are
  network-first and bypass this.
- load the app and confirm `GLPalDB` still has its eight stores

The browser pane has its own profile, so `GLPalDB` reads zero records there.
That is not Marc's data; his installed PWA is untouched.

## Environments

| environment | used for | quirks |
|---|---|---|
| Marc's PC "bifrost", reached through a mounted Linux VM | source of truth, builds, commits | mount allows writes but not unlinks; no Playwright; no github.com egress |
| Anthropic cloud container | Playwright tests, `node --check`, the push | files must be staged in; `TITRATE_SITE` points at the staged `docs/` |
| Desktop browser pane | verifying the live deploy | separate browser profile |

A plain local checkout with Python 3.10+ and `pip install playwright && playwright install chromium` removes the first two rows' quirks.
