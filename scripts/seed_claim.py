#!/usr/bin/env python3
"""READ-SIDE ENFORCEMENT for the burned-seed ledger.

`seed_audit.check_block` asks "does MY runner stay inside the block I
DECLARED?" — a write-side assertion. It needs a declaration to check against,
so it is structurally blind to the ledger's dominant defect: a block consumed
with NO declaration at all (VISION_SEED_ACCOUNTING_RESULTS.md found two —
38000-38099 and 40000-40099).

THIS module asks the other question, the one a rung needs at PRE-REGISTRATION
time, before it spends a seed:

    IS THE RANGE I AM ABOUT TO CLAIM MEASURABLY DRAWN BY ANYONE IN THIS TREE?

The authority is MEASURED DRAWS across the whole tree, not the ledger. The
ledger is consulted only as an ADVISORY second signal, because a declaration
with zero measured consumption is still somebody's reservation.

    from seed_claim import check_claim
    ok, report = check_claim(90000, 90999)
    assert ok, report

CLI:  python3 scripts/seed_claim.py 90000 90999      (exit 1 if occupied)
      python3 scripts/seed_claim.py --sweep          (Class-B: consumed but
                                                      never declared)

TWO CAVEATS, LOAD-BEARING, REPEATED IN EVERY VERDICT THIS TOOL PRINTS
---------------------------------------------------------------------
1. THE UNIT IS THE SEED INTEGER, not consecutive draws from one generator.
   `default_rng(S)` burns an unbounded stream downstream of S. A rung that
   reserves 1000 integers and seeds ONCE at the base measures as ONE seed here.
   That is a declared definitional choice, not an oversight -- so an
   "unoccupied" integer inside someone's seeded stream is still not free to
   take under the other reading.

2. IT UNDER-REPORTS BY DESIGN. `seed_audit` COUNTS unresolvable sink sites
   rather than discarding them (7 declared blind spots: CLI/env values,
   data-derived seeds, cross-MODULE constants, unanalysed library files,
   generator streams, non-Python seeds, over-cap expressions). Therefore

       A CLEAN RESULT MEANS "NO COLLISION DETECTED", NEVER "NO COLLISION
       EXISTS".

   The unresolved-sink count is printed with every verdict so the reader can
   price the silence rather than over-trust it.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from seed_audit import analyse_tree  # noqa: E402
from seed_ledger_audit import LEDGER_FLOOR, parse_ledger  # noqa: E402

#: The roots `seed_ledger_audit` scans. Kept identical on purpose: a claim
#: check and the ledger sweep must not disagree about what "the tree" is.
DEFAULT_ROOTS = ("scripts", "domains", "substrate", "tools",
                 "runners", "benchmarks", "demos", "tests")

_CAVEATS = (
    "  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from\n"
    "    one generator. default_rng(S) burns an unbounded stream downstream of\n"
    "    S; a rung seeding ONCE at its block base measures as ONE seed here.\n"
    "  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;\n"
    "    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS\n"
    "    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'."
)

_scan_cache: dict[tuple, dict] = {}


def scan_tree(roots: tuple[str, ...] = DEFAULT_ROOTS, *, refresh: bool = False):
    """Measured seed -> {files}, plus the unresolved-sink count.

    Cached per root-tuple: a whole-tree AST scan costs seconds, and a gate may
    ask several questions of the same tree state.
    """
    key = tuple(roots)
    if refresh or key not in _scan_cache:
        scan = analyse_tree([os.path.join(ROOT, d) for d in roots])
        seed_files: dict[int, set[str]] = {}
        unknown = 0
        for f in scan["files"]:
            rel = os.path.relpath(f["file"], ROOT)
            unknown += f["unknown_sinks"]
            for s in f["seeds"]:
                seed_files.setdefault(s, set()).add(rel)
        _scan_cache[key] = {
            "seed_files": seed_files,
            "unknown_sinks": unknown,
            "parse_errors": scan["parse_errors"],
            "files_scanned": len(scan["files"]),
        }
    return _scan_cache[key]


def claim_report(lo: int, hi: int, *, roots=DEFAULT_ROOTS, exclude=(),
                 consult_ledger: bool = True, refresh: bool = False) -> dict:
    """Structured occupancy report for the range [lo, hi]. No formatting."""
    if lo > hi:
        raise ValueError(f"empty range: {lo} > {hi}")
    scan = scan_tree(tuple(roots), refresh=refresh)
    excl = {os.path.normpath(p) for p in exclude}

    occupied: dict[int, list[str]] = {}
    for seed, files in scan["seed_files"].items():
        if not (lo <= seed <= hi):
            continue
        keep = sorted(f for f in files if os.path.normpath(f) not in excl)
        if keep:
            occupied[seed] = keep

    declared_overlap = []
    if consult_ledger:
        blocks, rows = parse_ledger()
        for blo, bhi, idx in blocks:
            if blo <= hi and lo <= bhi:
                declared_overlap.append(
                    {"lo": blo, "hi": bhi, "row": rows[idx][:120]})

    return {
        "range": [lo, hi],
        "occupied_seeds": {s: occupied[s] for s in sorted(occupied)},
        "occupied_count": len(occupied),
        "occupying_files": sorted({f for fs in occupied.values() for f in fs}),
        "declared_overlap": declared_overlap,
        "unresolved_sinks_in_tree": scan["unknown_sinks"],
        "files_scanned": scan["files_scanned"],
        "ledger_floor": LEDGER_FLOOR,
        "clean": not occupied and not declared_overlap,
    }


def format_report(rep: dict) -> str:
    lo, hi = rep["range"]
    out = []
    if rep["clean"]:
        out.append(f"SEED CLAIM {lo}-{hi}: CLEAN -- no collision DETECTED.")
    else:
        out.append(f"SEED CLAIM {lo}-{hi}: REFUSED.")
    if rep["occupied_seeds"]:
        out.append(
            f"  OCCUPIED: {rep['occupied_count']} seed integer(s) in this range"
            f" are measurably drawn by {len(rep['occupying_files'])} file(s)."
        )
        for s, files in list(rep["occupied_seeds"].items())[:20]:
            out.append(f"    {s}: {', '.join(files)}")
        if rep["occupied_count"] > 20:
            out.append(f"    ... and {rep['occupied_count'] - 20} more")
    if rep["declared_overlap"]:
        out.append(
            f"  DECLARED ELSEWHERE: overlaps {len(rep['declared_overlap'])}"
            f" ledger block(s). A declaration with zero MEASURED draws is still"
            f" a reservation -- see CAVEAT 1."
        )
        for b in rep["declared_overlap"][:10]:
            out.append(f"    {b['lo']}-{b['hi']}  {b['row']}")
    out.append(
        f"  Scope: {rep['files_scanned']} files with seed sinks;"
        f" {rep['unresolved_sinks_in_tree']} UNRESOLVED sink sites tree-wide"
        f" (counted, not discarded)."
    )
    out.append(_CAVEATS)
    return "\n".join(out)


def check_claim(lo: int, hi: int, *, roots=DEFAULT_ROOTS, exclude=(),
                consult_ledger: bool = True, refresh: bool = False):
    """THE GATE. Returns (ok, report_text).

        ok, report = check_claim(90000, 90999)
        assert ok, report

    ok is False when the range is measurably drawn by any file in the tree, or
    (when consult_ledger) overlaps an existing §11 declaration.
    """
    rep = claim_report(lo, hi, roots=roots, exclude=exclude,
                       consult_ledger=consult_ledger, refresh=refresh)
    return rep["clean"], format_report(rep)


def first_clean_subrange(lo: int, hi: int, width: int, *, roots=DEFAULT_ROOTS,
                         exclude=(), consult_ledger: bool = True):
    """Lowest `width`-wide sub-range of [lo, hi] that passes `check_claim`.

    For the case this tool is expected to produce often: the block you were
    allocated is partly occupied and you need a verified-clean slice of it.
    Returns (sublo, subhi) or None.
    """
    scan = scan_tree(tuple(roots))
    excl = {os.path.normpath(p) for p in exclude}
    taken = {s for s, fs in scan["seed_files"].items()
             if lo <= s <= hi
             and any(os.path.normpath(f) not in excl for f in fs)}
    blocks = parse_ledger()[0] if consult_ledger else []
    start = lo
    while start + width - 1 <= hi:
        end = start + width - 1
        hits = sorted(s for s in taken if start <= s <= end)
        if hits:
            start = hits[-1] + 1
            continue
        clash = [b for b in blocks if b[0] <= end and start <= b[1]]
        if clash:
            start = max(b[1] for b in clash) + 1
            continue
        return (start, end)
    return None


# ---- the ledger sweep: CONSUMED BUT NEVER DECLARED (Class B) ---------------

def undeclared_runs(*, roots=DEFAULT_ROOTS, floor: int = LEDGER_FLOOR):
    """Contiguous runs of measured seeds falling in NO declared ledger block.

    This is the check that would have caught 38000-38099 and 40000-40099. It
    needs no declaration to check against -- that is the entire point.

    Returns a list of {"lo","hi","n","files"}, contiguity broken by a gap of
    more than 1 OR by a change in the drawing file-set.
    """
    scan = scan_tree(tuple(roots))
    blocks = parse_ledger()[0]
    seeds = sorted(s for s in scan["seed_files"] if s >= floor)
    outside = [s for s in seeds
               if not any(lo <= s <= hi for lo, hi, _ in blocks)]

    runs = []
    for s in outside:
        files = tuple(sorted(scan["seed_files"][s]))
        if runs and s == runs[-1]["hi"] + 1 and files == runs[-1]["_files"]:
            runs[-1]["hi"] = s
            runs[-1]["n"] += 1
            continue
        runs.append({"lo": s, "hi": s, "n": 1, "_files": files})
    for r in runs:
        r["files"] = list(r.pop("_files"))
    return runs


def main(argv):
    if len(argv) >= 2 and argv[1] == "--sweep":
        runs = undeclared_runs()
        print(json.dumps({
            "undeclared_runs": len(runs),
            "undeclared_seeds": sum(r["n"] for r in runs),
            "runs": runs,
        }, indent=1))
        print(_CAVEATS, file=sys.stderr)
        return 0
    if len(argv) < 3:
        print(__doc__)
        return 2
    lo, hi = int(argv[1]), int(argv[2])
    ok, report = check_claim(lo, hi, exclude=argv[3:])
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
