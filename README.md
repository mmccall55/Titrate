# Titrate

Personal utility. Not for distribution.

A fork of GLPal, an abandoned GLP-1 dose and weight tracking PWA, in daily use.
Deployed at `https://mmccall55.github.io/Titrate/` from `docs/` on `main`.

## Before you change anything

There is no React source. The app is the deployed minified upstream bundle,
modified by a chain of deterministic, SHA-gated Python patch scripts in
`build/`. Five rules, all load-bearing:

1. **Never hand-edit `docs/assets/app/index-DwosoAbB.js`.** Every change is a
   new `build/glpal_patchNN_<name>.py`, wired into `build/build_fork.py`.
2. **Never change the `GLPalDB` schema** — store names, key paths, record
   shapes. The database name stays `GLPalDB` despite the rebrand; renaming it
   orphans real data.
3. **Never re-capture upstream.** Every patch anchor and minified identifier is
   valid only for the pinned SHA.
4. **Never commit health data.**
5. **Ask before pushing.** A push redeploys the PWA Marc uses daily.

## Where to look

| you want | read |
|---|---|
| what the app is, schema, level model, charts | [docs-internal/ARCHITECTURE.md](docs-internal/ARCHITECTURE.md) |
| how to write a patch, build, test, deploy | [docs-internal/WORKFLOW.md](docs-internal/WORKFLOW.md) |
| what will bite you | [docs-internal/GOTCHAS.md](docs-internal/GOTCHAS.md) |
| why it is like this | [docs-internal/DECISIONS.md](docs-internal/DECISIONS.md) |
| what is known broken | [docs-internal/OPEN-ITEMS.md](docs-internal/OPEN-ITEMS.md) |
| the patch chain and its hashes | [docs-internal/CHAIN.md](docs-internal/CHAIN.md) |
| everything, with what invalidates it | [docs-internal/INDEX.md](docs-internal/INDEX.md) |

Machine-specific values — checkout path, where the GitHub token lives — are in
project memory, not in this repository.

## Build

```
python3 build/build_fork.py     # rebuild docs/ from the pinned upstream capture
python3 build/make_docs.py      # regenerate the derived documents
python3 tests/test_<name>.py    # each test is standalone
```
