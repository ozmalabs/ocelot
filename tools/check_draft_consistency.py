#!/usr/bin/env python3
"""Check the formal paper set for draft-string and revision inconsistencies.

Three defects this catches, all of which have actually occurred:

  1. Two documents on different draft strings (the set is bumped together, so a
     reader comparing two papers is never comparing two drafts).
  2. A document whose per-page footer or boxed DRAFT notice carries a revision
     that disagrees with its title block --- the footer is hand-maintained and a
     revision bump can miss it.
  3. A document carrying no footer or notice at all, while README says all of
     them do.

Exits non-zero on any finding. Run from anywhere:
    python3 tools/check_draft_consistency.py
"""
import re
import sys
from pathlib import Path

FORMAL = Path(__file__).resolve().parent.parent / "papers" / "formal"
DRAFT_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?")
DATE_REV_RE = re.compile(r"document revision (\d+)")
FOOT_REV_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?[\s,/\\]*r(\d+)")

def main() -> int:
    problems = []
    drafts = {}
    for tex in sorted(FORMAL.glob("*.tex")):
        src = tex.read_text(encoding="utf-8")
        name = tex.name

        found = set(DRAFT_RE.findall(src))
        if not found:
            problems.append(f"{name}: carries no draft string at all")
            continue
        if len(found) > 1:
            problems.append(f"{name}: mixed draft strings within one file: {sorted(found)}")
        drafts[name] = sorted(found)[0]

        # 01s is generated and tracks the long paper's revision, not its own.
        if name.startswith("01s"):
            continue

        date_rev = DATE_REV_RE.search(src)
        if not date_rev:
            problems.append(f"{name}: title block carries no 'document revision N'")
            continue
        want = date_rev.group(1)

        foot_revs = set(FOOT_REV_RE.findall(src))
        if not foot_revs:
            problems.append(
                f"{name}: no footer/notice revision found "
                f"(title says r{want}) --- missing fancyhdr footer or DRAFT box?"
            )
        elif foot_revs != {want}:
            problems.append(
                f"{name}: title says r{want} but footer/notice says "
                f"{', '.join('r' + r for r in sorted(foot_revs))}"
            )

    if len(set(drafts.values())) > 1:
        by_draft = {}
        for n, d in drafts.items():
            by_draft.setdefault(d, []).append(n)
        problems.append(
            "the set is not on one draft string: "
            + "; ".join(f"{d} -> {len(v)} file(s): {', '.join(sorted(v))}"
                        for d, v in sorted(by_draft.items()))
        )

    if problems:
        print(f"draft consistency: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print(f"draft consistency: OK ({len(drafts)} documents, all on {sorted(set(drafts.values()))[0]})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
