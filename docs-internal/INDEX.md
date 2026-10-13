---
updated: generated
generator: build/make_docs.py - do not edit
authority: current
invalidated-by: adding, removing or re-purposing a document
---

# Index

Every document in `docs-internal/`. `authority: frozen` means a point-in-time
record - read it as history, never as current truth. **unclassified** means
the file predates this scheme and has not been triaged yet.

| document | purpose | updated | authority |
|---|---|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | What Titrate is and how it works. For how to change it, see [WORKFLOW.md](WORKFLOW.md). | 2026-10-13 | current |
| [WORKFLOW.md](WORKFLOW.md) | How to change Titrate safely. For what the app is, see [ARCHITECTURE.md](ARCHITECTURE.md). | 2026-10-13 | current |
| [GOTCHAS.md](GOTCHAS.md) | Hard-won negative results. Each entry cost real time to discover. Read this | 2026-10-13 | current |
| [DECISIONS.md](DECISIONS.md) | One entry per decision that would otherwise be re-litigated. Append-only. | 2026-10-13 | current |
| [OPEN-ITEMS.md](OPEN-ITEMS.md) | Known limitations and backlog. Nothing here is in progress. | 2026-10-13 | current |
| [CHAIN.md](CHAIN.md) | Generated. Discovered by following SHA-256 links from the pinned upstream | generated | current |
| [archive/2026-08-13-reverse-engineering.md](archive/2026-08-13-reverse-engineering.md) | **Handoff date:** 2026-08-13 | 2026-08-13 | frozen |
| [archive/2026-08-28-transfer-package.md](archive/2026-08-28-transfer-package.md) | > **FROZEN.** The machine-and-account transfer package, preserved verbatim. | 2026-08-28 | frozen |

## What invalidates each document

| document | invalidated by |
|---|---|
| `ARCHITECTURE.md` | any patch that changes the bundle's behaviour, the Dexie schema, or the level model |
| `WORKFLOW.md` | a change to the build chain, the test harness, or how the site is deployed |
| `GOTCHAS.md` | nothing — entries are only added, or struck through when a fix removes the trap |
| `DECISIONS.md` | nothing — append-only; a reversed decision gets a new entry, the old one stays |
| `OPEN-ITEMS.md` | fixing any of these, or discovering a new one |
| `CHAIN.md` | adding or changing a patch stage |
| `archive/2026-08-13-reverse-engineering.md` | nothing - this is a point-in-time record and is never updated |
| `archive/2026-08-28-transfer-package.md` | nothing - this is a point-in-time record and is never updated |
