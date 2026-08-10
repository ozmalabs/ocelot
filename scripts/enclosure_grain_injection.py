"""enclosure_grain_injection -- POSITIVE-CONTROL THE s13 AUDIT BY INJECTION,
VERIFY THE INJECTION *LANDS IN THE REGION*, AND REPORT WHAT THE GATE CANNOT
SEE.

A predecessor's `verify_lands` checked that the plant was present in the
FILE, not in the audited REGION, and produced seven false verdicts.  So every
plant here is re-selected THROUGH THE SAME SELECTOR the audit uses (AST
identity, never substring) and asserted to lie inside the resolved span; a
NO-OP injection is asserted to FAIL that check, so the landing test is itself
positive-controlled.

AND THE CONTROL IS RUN AS A LADDER, NOT AS A SINGLE PASS.  A single plant
that goes red establishes only that ONE spelling is visible -- which is this
project's own recorded lesson ("six spellings felt like a pattern, were a
SAMPLE").  Five spellings are planted and the RESULT MAP is reported,
including the ones the gate misses.

WHAT THIS FOUND, AND IT IS A DEFECT IN THE GATE, NOT IN THIS RUNG:
`trace` resolves a REBOUND name to its FIRST binding.  An ACCUMULATOR --
`enc_cells = 0` then `enc_cells += <measured>` -- therefore grades AUTHORED
(`-> literal 0`).  That single cause fires in BOTH directions:

  * FALSE NEGATIVE: in `x / n > 0.42` with `x` and `n` both accumulators,
    BOTH sides grade AUTHORED, so `audit_source`'s "both sides authored =>
    constant comparison, dead code" branch SUPPRESSES the sink.  A real
    magic-number threshold on an accumulated quantity is INVISIBLE.
  * FALSE POSITIVE: `max(largest_gnd, ...)` is reported as
    `largest_gnd -> literal 0` when `largest_gnd` is a running maximum whose
    0 is the identity of `max` over counts, not a chosen bound.

REPORTED, NOT FIXED: `scripts/gate_audit.py` is not this rung's file (s11
rule 4).  This script neither edits it nor routes around it -- the affected
sites in this rung's own code are hand-audited in the results instead, since
a gate demonstrably blind to a spelling cannot be leaned on for it.

This control never writes to disk.
"""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import gate_audit as ga                                      # noqa: E402

TARGET = os.path.join(ROOT, "scripts", "enclosure_grain_measure.py")
REGION = "frame_record"
ANCHOR = "    size = np.concatenate(sizes)\n"

#: (name, injected source, the line of the plant that must land in-region,
#:  whether a CORRECT gate must go RED on it)
PLANTS = (
    ("P1 measurement vs bare literal",
     "    if float(np.median(size)) > 0.42:\n        size = size * 2\n",
     "if float(np.median(size)) > 0.42", True),
    ("P2 measurement vs NAME-bound literal",
     "    CUT = 0.42\n    if float(np.median(size)) > CUT:\n"
     "        size = size * 2\n",
     "if float(np.median(size)) > CUT", True),
    ("P3 comparison with no `if` at all",
     "    _v = float(np.median(size)) > 0.42\n",
     "_v = float(np.median(size)) > 0.42", True),
    ("P4 ACCUMULATOR vs bare literal",
     "    if float(enc_cells) / ncell > 0.42:\n        enc_cells = 0\n",
     "if float(enc_cells) / ncell > 0.42", True),
    ("P5 ACCUMULATOR vs NAME-bound literal",
     "    CUT = 0.42\n    if float(enc_cells) / ncell > CUT:\n"
     "        enc_cells = 0\n",
     "if float(enc_cells) / ncell > CUT", True),
)

NOOP = "    _noop_marker_that_is_not_a_decision = None\n"


def region_span(src, qualname):
    """The span the audit's OWN selector resolves -- by AST identity."""
    node = ga.resolve(ast.parse(src), qualname)
    lo = min(n.lineno for n in ast.walk(node) if hasattr(n, "lineno"))
    hi = max(n.end_lineno for n in ast.walk(node) if hasattr(n, "end_lineno"))
    return lo, hi


def lands(src, qualname, needle):
    lo, hi = region_span(src, qualname)
    for i, line in enumerate(src.splitlines(), start=1):
        if needle in line:
            return (lo <= i <= hi), i, (lo, hi)
    return False, None, (lo, hi)


def main():
    original = open(TARGET).read()
    ok = True

    base_a, base_u = ga.audit_source(original, TARGET, REGION)
    span = region_span(original, REGION)
    base_key = {(f.lineno, f.expr) for f in base_a}
    print(f"[region] `{REGION}` resolves BY AST IDENTITY to lines "
          f"{span[0]}-{span[1]}")
    print(f"[before] authored={len(base_a)} unresolved={len(base_u)}")
    for f in base_a:
        print(f"         baseline: line {f.lineno}  {f.expr}  <- {f.detail}")

    # --- the landing check is itself positive-controlled: a NO-OP must FAIL
    noop_src = original.replace(ANCHOR, NOOP + ANCHOR, 1)
    nl, _, _ = lands(noop_src, REGION, "if float(np.median(size))")
    na, _ = ga.audit_source(noop_src, TARGET, REGION)
    print(f"\n[noop ] plant visible in region: {nl} (must be False);  "
          f"authored={len(na)} (must equal baseline {len(base_a)})")
    if nl or len(na) != len(base_a):
        ok = False
        print("  !! THE NO-OP CONTROL FAILED -- the landing check is blind")

    print("\n[ladder] five spellings, each landed and audited:")
    results = []
    for name, body, needle, must_red in PLANTS:
        planted = original.replace(ANCHOR, body + ANCHOR, 1)
        if planted == original:
            raise SystemExit(f"ANCHOR NOT FOUND for {name}")
        did_land, line, sp = lands(planted, REGION, needle)
        a, u = ga.audit_source(planted, TARGET, REGION)
        new = [f for f in a if (f.lineno, f.expr) not in base_key]
        red = bool(new) and any(sp[0] <= f.lineno <= sp[1] for f in new)
        results.append((name, did_land, red, must_red))
        print(f"  {name:38s} lands@{line} in-region={did_land}  "
              f"RED={red}  (a correct gate must be RED={must_red})"
              f"{'   <-- MISS' if did_land and red != must_red else ''}")
        for f in new:
            print(f"        NEW: line {f.lineno}  {f.expr}  <- {f.detail}")
        if not did_land:
            ok = False
            print("        !! DID NOT LAND IN THE AUDITED REGION")

    rev_a, _ = ga.audit_source(original, TARGET, REGION)
    same = {(f.lineno, f.expr) for f in rev_a} == base_key
    print(f"\n[green] after revert: authored={len(rev_a)}, "
          f"identical to baseline = {same}")
    if not same or open(TARGET).read() != original:
        ok = False
        print("  !! REVERT FAILED or the target file was modified on disk")

    landed = all(r[1] for r in results)
    bites = [r[0] for r in results if r[2]]
    blind = [r[0] for r in results if not r[2] and r[3]]
    print(f"\nALL FIVE PLANTS LANDED IN THE AUDITED REGION: {landed}")
    print(f"GATE BITES on {len(bites)}/5: {bites}")
    print(f"GATE IS BLIND to {len(blind)}/5: {blind}")
    print("  ^ REPORTED AS A GATE DEFECT, NOT FIXED HERE (s11 rule 4). "
          "The affected spelling is hand-audited in the results.")
    print(f"\nINJECTION CONTROL (landing + revert + gate ALIVE in region): "
          f"{'PASSES' if (ok and landed and bites) else 'FAILED'}")
    return 0 if (ok and landed and bites) else 1


if __name__ == "__main__":
    raise SystemExit(main())
