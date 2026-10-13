#!/usr/bin/env python3
"""
Generate the derived documents in docs-internal/.

Everything this writes was previously maintained by hand and went stale:
the patch table and its SHAs, the patch count, the git history, the document
index, and the minified identifier map. None of it is typed again.

  CHAIN.md         the patch chain, discovered by following SHA-256 links from
                   the pinned upstream bundle - so it also proves the chain is
                   linear and complete
  INDEX.md         from the frontmatter of every doc in docs-internal/
  ARCHITECTURE.md  the identifier table, injected between markers, from
                   build/identifiers.json

There is no CHANGELOG.md. Commit messages are written as user-visible
effects, so the changelog is:
  git log --reverse --date=short --format='%ad  %s'
A generated copy could never be current inside the commit that contains it.

Usage:
  python3 build/make_docs.py                write the files
  python3 build/make_docs.py --check        exit 1 if any committed file differs
  python3 build/make_docs.py --check-chain  same, CHAIN.md and the identifier
                                            table only - the documents that go
                                            stale when a patch stage changes.
                                            build_fork.py stage [4] runs this.
"""

from pathlib import Path
import ast
import json
import re
import sys

ROOT = Path(__file__).resolve().parent          # build/
REPO = ROOT.parent
DOCS = REPO / "docs-internal"
BEGIN = "<!-- BEGIN GENERATED: identifiers -->"
END = "<!-- END GENERATED: identifiers -->"


# ------------------------------------------------------------------ helpers
def const(path: Path, name: str):
    """Read a module-level string constant without importing the module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    if isinstance(node.value, ast.Constant):
                        return node.value.value
    return None


def docstring_title(path: Path) -> str:
    """First paragraph of the docstring, rewrapped to one line.

    Patch titles wrap, so taking only the first physical line truncates them
    mid-sentence.
    """
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    para = []
    for line in doc.splitlines():
        if line.strip():
            para.append(line.strip())
        elif para:
            break
    if not para:
        return path.stem
    title = " ".join(para).rstrip(".")
    return re.sub(r"^Patch \d+ - ", "", title)


def artifacts_by_script() -> dict:
    """Map patch script filename -> output artifact filename, from build_fork.py."""
    src = (ROOT / "build_fork.py").read_text(encoding="utf-8")
    var_to_art = dict(re.findall(r'(\w+)\s*=\s*ARTIFACTS\s*/\s*"([^"]+)"', src))
    out = {}
    for script, args in re.findall(
            r'str\(ROOT / "(glpal_patch[^"]*\.py)"\), ([^\]]+)\]', src):
        names = re.findall(r"str\((\w+)\)", args)
        if len(names) == 2 and names[1] in var_to_art:
            out[script] = var_to_art[names[1]]
    return out


# ------------------------------------------------------------------ CHAIN.md
def build_chain() -> str:
    upstream = const(ROOT / "build_fork.py", "EXPECTED_BUNDLE_SHA")
    ship = None
    src = (ROOT / "build_fork.py").read_text(encoding="utf-8")
    m = re.search(r"SHIP_SHA\s*=\s*(\w+)", src)
    if m:
        ship = const(ROOT / "build_fork.py", m.group(1))

    scripts = {}
    for p in sorted(ROOT.glob("glpal_patch*.py")):
        i = const(p, "EXPECTED_INPUT_SHA256")
        o = const(p, "EXPECTED_OUTPUT_SHA256")
        if i and o:
            scripts[i] = (p, o)

    arts = artifacts_by_script()
    rows, cur, n = [], upstream, 0
    while cur in scripts:
        p, out = scripts.pop(cur)
        n += 1
        rows.append((p.name, arts.get(p.name, "?"), cur, out, docstring_title(p)))
        cur = out

    lines = [
        "---",
        "updated: generated",
        "generator: build/make_docs.py - do not edit",
        "authority: current",
        "invalidated-by: adding or changing a patch stage",
        "---",
        "",
        "# Patch chain",
        "",
        "Generated. Discovered by following SHA-256 links from the pinned upstream",
        "bundle, so this table also proves the chain is linear, complete, and ends",
        "at what ships.",
        "",
        f"- pinned upstream bundle: `{upstream}`",
        f"- shipping bundle:        `{cur}`",
        f"- patch scripts:           **{len(rows)}**",
        f"- numbered patches:        **{len(rows) + 5}** - the first script applies the",
        "  original six fixes in one stage, so script count and patch number differ by five",
        "",
        "| # | script | artifact | effect |",
        "|---|---|---|---|",
    ]
    for k, (name, art, _, _, title) in enumerate(rows, 1):
        lines.append(f"| {k} | `{name}` | `{art}` | {title} |")

    lines += ["", "## SHA-256 links", "", "| stage | input | output |", "|---|---|---|",
              f"| _upstream capture_ | — | `{upstream}` |"]
    for name, _, i, o, _ in rows:
        lines.append(f"| `{name}` | `{i}` | `{o}` |")

    if ship and ship != cur:
        lines += ["", f"**WARNING: SHIP_SHA is `{ship}` but the chain ends at `{cur}`.**"]
    else:
        lines += ["", "`SHIP_SHA` matches the end of the chain.", "",
                  "The recolour stage runs after the last patch and is not SHA-pinned; it is",
                  "verified instead by `recolour.py` failing if any mapped colour survives."]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ INDEX.md
def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        for line in text[3:end].strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
    body = text[text.find("\n---", 3) + 4:] if text.startswith("---") else text
    purpose = ""
    seen_h1 = False
    for line in body.splitlines():
        if line.startswith("# "):
            seen_h1 = True
            continue
        if seen_h1 and line.strip() and not line.startswith("#"):
            purpose = line.strip()
            break
    return {"title": title, "purpose": purpose, **fm}


ORDER = ["ARCHITECTURE.md", "WORKFLOW.md", "GOTCHAS.md", "DECISIONS.md",
         "OPEN-ITEMS.md", "CHAIN.md"]


def build_index() -> str:
    lines = [
        "---",
        "updated: generated",
        "generator: build/make_docs.py - do not edit",
        "authority: current",
        "invalidated-by: adding, removing or re-purposing a document",
        "---",
        "",
        "# Index",
        "",
        "Every document in `docs-internal/`. `authority: frozen` means a point-in-time",
        "record - read it as history, never as current truth. **unclassified** means",
        "the file predates this scheme and has not been triaged yet.",
        "",
        "| document | purpose | updated | authority |",
        "|---|---|---|---|",
    ]
    files = [DOCS / n for n in ORDER if (DOCS / n).exists()]
    files += sorted(p for p in DOCS.glob("*.md")
                    if p.name not in ORDER + ["INDEX.md"])
    files += sorted(DOCS.glob("archive/*.md"))
    for p in files:
        fm = frontmatter(p)
        rel = p.relative_to(DOCS).as_posix()
        purpose = fm["purpose"][:110]
        authority = fm.get("authority") or "**unclassified**"
        lines.append(f"| [{rel}]({rel}) | {purpose} | {fm.get('updated','—')} "
                     f"| {authority} |")
    lines += ["", "## What invalidates each document", "",
              "| document | invalidated by |", "|---|---|"]
    for p in files:
        fm = frontmatter(p)
        lines.append(f"| `{p.relative_to(DOCS).as_posix()}` | {fm.get('invalidated-by','—')} |")
    return "\n".join(lines) + "\n"


# ------------------------------------------------- identifiers -> ARCHITECTURE
def build_identifiers() -> str:
    d = json.loads((ROOT / "identifiers.json").read_text(encoding="utf-8"))
    out = ["", "### Upstream symbols", "", "| symbol | role |", "|---|---|"]
    out += [f"| `{k}` | {v} |" for k, v in d["upstream"].items()]
    out += ["", "### Symbols this fork adds", "", "| symbol | role |", "|---|---|"]
    out += [f"| `{k}` | {v} |" for k, v in d["ours"].items()]
    out.append("")
    return "\n".join(out)


def inject(path: Path, block: str) -> str:
    text = path.read_text(encoding="utf-8")
    a, b = text.find(BEGIN), text.find(END)
    if a < 0 or b < 0:
        raise SystemExit(f"FAIL: markers not found in {path.name}")
    return text[:a + len(BEGIN)] + block + text[b:]


# ---------------------------------------------------------------------- main
def chain_targets() -> dict:
    """Documents derived from the build chain - stale when a patch stage changes."""
    return {
        DOCS / "CHAIN.md": build_chain(),
        DOCS / "ARCHITECTURE.md": inject(DOCS / "ARCHITECTURE.md", build_identifiers()),
    }


def stale(targets: dict) -> list:
    return [p.name for p, c in targets.items()
            if not p.exists() or p.read_text(encoding="utf-8") != c]


def stale_chain_docs() -> list:
    """Names of chain-derived documents that differ from what would be generated.

    Called by build_fork.py stage [4]."""
    return stale(chain_targets())


def main():
    if "--check-chain" in sys.argv:
        bad = stale_chain_docs()
        if bad:
            print("FAIL: chain documents are stale, run build/make_docs.py: " + ", ".join(bad))
            raise SystemExit(1)
        print("chain documents are up to date")
        return

    check = "--check" in sys.argv
    targets = chain_targets()
    if not check:
        for p, content in targets.items():
            p.write_text(content, encoding="utf-8")
    # INDEX last: it reads the frontmatter of everything above
    idx = build_index()
    if not check:
        (DOCS / "INDEX.md").write_text(idx, encoding="utf-8")
    targets[DOCS / "INDEX.md"] = idx

    if check:
        bad = stale(targets)
        if bad:
            print("FAIL: generated docs are stale, run build/make_docs.py: " + ", ".join(bad))
            raise SystemExit(1)
        print("generated docs are up to date")
    else:
        for p in targets:
            print(f"  wrote {p.relative_to(REPO)}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
