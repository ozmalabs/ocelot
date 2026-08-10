#!/usr/bin/env python3
"""Compare VISION_PROTOCOL.md's DECLARED burned-seed blocks against seeds
MEASURED from source by `seed_audit.py`.

Three mismatch classes, FIXED in the pre-registration and not redefined after
seeing results (VISION_PROTOCOL.md §5):

  A. declared > measured  -- over-declared. Harmless alone, but it is what
     makes the ledger unreliable for a successor claiming a free sub-range.
  B. measured NOT-SUBSET-OF declared -- a draw outside every declared block.
     A real accounting error.
  C. genuine collision -- one seed integer measurably drawn by two DIFFERENT
     source files.

Attribution note: this tool needs NO script->rung map. A declared block's
measured consumption is the set of seeds drawn anywhere in the tree that fall
inside it, and a collision is defined file-wise. Both are directly measurable.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from seed_audit import analyse_tree  # noqa: E402

LEDGER = os.path.join(ROOT, "VISION_PROTOCOL.md")

# Seeds below this are conventional determinism arguments (default_rng(0),
# Random(1), manual_seed(42)...), not ledger allocations. The lowest declared
# block in the ledger is verified against this at runtime.
LEDGER_FLOOR = 1000

RANGE_RE = re.compile(r"(\d{4,6})\s*[–—-]\s*(\d{4,6})")


def parse_ledger(path: str = LEDGER):
    """Extract declared blocks from the burned-seed ledger table.

    Returns (blocks, rows) where blocks is a list of (lo, hi, row_index) and
    rows is the list of raw first-cell strings.
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    in_ledger = False
    blocks, rows = [], []
    for ln in lines:
        if ln.startswith("## Burned-seed ledger"):
            in_ledger = True
            continue
        if in_ledger and ln.startswith("## ") and "Burned-seed" not in ln:
            break
        if not in_ledger or not ln.startswith("|"):
            continue
        cells = ln.split("|")
        if len(cells) < 3:
            continue
        head = cells[1]
        if set(head.strip()) <= {"-", ":", " "} or not head.strip():
            continue
        found = RANGE_RE.findall(head)
        if not found:
            continue
        idx = len(rows)
        rows.append(head.strip())
        for lo, hi in found:
            lo, hi = int(lo), int(hi)
            if lo <= hi:
                blocks.append((lo, hi, idx))
    return blocks, rows


def main():
    blocks, rows = parse_ledger()
    scan = analyse_tree([os.path.join(ROOT, d) for d in
                         ("scripts", "domains", "substrate", "tools",
                          "runners", "benchmarks", "demos", "tests")])

    seed_files: dict[int, set[str]] = {}
    unknown_sinks = 0
    for f in scan["files"]:
        rel = os.path.relpath(f["file"], ROOT)
        unknown_sinks += f["unknown_sinks"]
        for s in f["seeds"]:
            seed_files.setdefault(s, set()).add(rel)

    all_seeds = set(seed_files)
    ledger_seeds = {s for s in all_seeds if s >= LEDGER_FLOOR}
    low_seeds = all_seeds - ledger_seeds

    # ---- class A: over-declaration -----------------------------------------
    per_block = []
    for lo, hi, idx in blocks:
        hit = sorted(s for s in ledger_seeds if lo <= s <= hi)
        per_block.append({
            "lo": lo, "hi": hi, "row": idx,
            "declared_width": hi - lo + 1,
            "measured": len(hit),
            "measured_min": hit[0] if hit else None,
            "measured_max": hit[-1] if hit else None,
        })

    # ---- class B: measured outside every declared block ---------------------
    covered = set()
    for lo, hi, _ in blocks:
        covered |= {s for s in ledger_seeds if lo <= s <= hi}
    outside = sorted(ledger_seeds - covered)

    # ---- class C: genuine collisions ---------------------------------------
    collisions = {s: sorted(fs) for s, fs in seed_files.items()
                  if s >= LEDGER_FLOOR and len(fs) > 1}

    zero_blocks = [b for b in per_block if b["measured"] == 0]
    nonzero = [b for b in per_block if b["measured"] > 0]
    ratios = sorted(b["measured"] / b["declared_width"] for b in nonzero)

    out = {
        "declared_blocks": len(blocks),
        "ledger_rows": len(rows),
        "files_with_seeds": len(scan["files"]),
        "parse_errors": scan["parse_errors"],
        "unknown_sinks": unknown_sinks,
        "distinct_seeds_measured": len(all_seeds),
        "ledger_range_seeds": len(ledger_seeds),
        "low_convention_seeds": sorted(low_seeds),
        "class_A_zero_measured_blocks": len(zero_blocks),
        "class_A_nonzero_blocks": len(nonzero),
        "class_A_median_fill": (ratios[len(ratios) // 2] if ratios else None),
        "class_B_outside_count": len(outside),
        "class_B_outside": outside[:200],
        "class_C_collisions": {str(k): v for k, v in
                               sorted(collisions.items())},
        "class_C_count": len(collisions),
        "per_block": per_block,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
