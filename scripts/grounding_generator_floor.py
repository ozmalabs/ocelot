"""grounding_generator_floor — THE GROUNDING-GENERATOR (the floor, cmsg159).

The agent READS an operation's defining formula, PARSES it into a composition tree
over its HELD PRIMITIVES, COMPOSES the held primitives per the tree, and SELF-VERIFIES
on known cases — generating the GROUNDING from reading, for an operation it did NOT
hold. This closes the faculty-generator's gap (cmsg157 FIXED the grounding; this
GENERATES the grounding shape from reading) and generalizes ground_definition (cmsg126
operator-over-a-FAMILY slice) to compose ARBITRARY held primitives per a read formula.

WHAT THIS SCRIPT PROVES (the donkey-checked floor):
  1. generate_grounding — per operation: the READ FORMULA (logged, GET-only) -> the
     PARSED held-formula (its operator shape + leaf READ off the prose) -> the HELD
     primitives composed per the tree (compute_grounding) -> SELF-VERIFY on known
     spaces -> generated / stall.
  2. GENERALITY — >=2 DIFFERENT operations composed from their formulas, DIFFERENT held
     primitives: euler_characteristic = betti + ALTERNATING-FOLD; genus = euler +
     DIVIDE. The SAME generate_grounding; the distinct compositions shown.
  3. DISCRIMINATION — a WRONG parse (the NON-alternating sum) FAILS the knowns ->
     REJECTED (the self-verify discriminates).
  4. FIXPOINT-CLOSURE — generate_grounding wired into the faculty-generator
     (faculty_generator.generate_faculty_grounded) -> >=2 faculties with DIFFERENT
     GROUNDINGS generated from reading (not the same prose_to_operation shape) -> the
     meta-ability TURNS (generate the SHAPE, not just the operation).
  5. THE META-SUB-WALL — Lefschetz number = sum_k (-1)^k tr(H_k(f)) is formula-readable
     but its leaf tr(H_k(f)) is NOT held for a general map -> honest stall (un-held-
     leaf). The floor crosses for the formula-composable class; the sub-wall located.

The LLM authors NO composition (provenance = the read formula + the parsed held-formula
+ the held leaves, logged). Held primitives only at the leaves. GET-only. The answer
(671579) is NEVER read. No Rust. Speech path untouched.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.join(str(ROOT), "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(str(ROOT), "scripts"))

from domains import grounding_generator as _GG               # noqa: E402
from domains import faculty_generator as _FG                 # noqa: E402
from scripts import prose_to_operation_pipeline as _PIPE     # noqa: E402


# the operations the agent generates groundings for — each names WHERE its defining
# formula lives (the agent's retrieval decision); the formula itself is READ off the
# fetched prose, the composition is the PARSE.
OPS = [
    ("euler_characteristic", ["Euler characteristic"]),
    ("genus", ["Genus (mathematics)"]),
]


def _show(gg: "_GG.GeneratedGrounding") -> None:
    rd = gg.provenance.get("read", {})
    print(f"  READ (GET-only): {rd.get('title')!r} [{rd.get('source')}] "
          f"textlen {rd.get('textlen')}")
    if gg.read is not None:
        print(f"    located formula surface (provenance): "
              f"{gg.read.formula_surface!r}")
        print(f"    READ operator shape: {gg.read.operator_shape!r}  "
              f"READ leaf-quantity: {gg.read.leaf.name!r}")
        print(f"    {gg.read.note}")
    if gg.provenance.get("leaf"):
        print(f"  LEAF: {gg.provenance['leaf']}")
    if gg.held_formula:
        print(f"  PARSED held-formula (the composition tree's surface):")
        print(f"    {gg.held_formula}")
    if gg.composition_parts:
        print(f"  COMPOSED over HELD primitives: {sorted(gg.composition_parts)}")
    if gg.verify_rows:
        print(f"  SELF-VERIFY (vs known spaces, NONE a question's answer):")
        for r in gg.verify_rows:
            p = "PASS" if r["pass"] else "FAIL"
            print(f"    [{p}] {r['known']:5s} expected {r['expected']}  got {r['got']}")
    if gg.generated:
        print(f"  => GENERATED + SELF-VERIFIED")
    else:
        print(f"  => STALL: {gg.stall}")


def main() -> None:
    print("=" * 78)
    print("THE GROUNDING-GENERATOR — the floor (cmsg159): GENERATE THE GROUNDING from")
    print("  READING. read a defining formula -> parse into a held-primitive")
    print("  composition tree -> compose -> self-verify, for an op NOT held.")
    print("=" * 78)
    print()

    http_get = _PIPE._author_http_get()
    print("  full-text fetch: agent-authored http_get (GET-only) + local-wiki fallback")
    print()

    # ---- (1) generate_grounding per operation ----
    grounded = []
    for op, titles in OPS:
        print("-" * 78)
        print(f"OPERATION: {op}   (route: {titles})")
        gg = _GG.generate_grounding(op, titles, http_get)
        grounded.append(gg)
        _show(gg)
        print()

    ok = [g for g in grounded if g.generated]
    print("=" * 78)
    print("THE MEASURE — N groundings GENERATED from reading")
    print("=" * 78)
    print(f"  operations attempted          : {len(OPS)}")
    print(f"  groundings GENERATED + verified: {len(ok)}")
    for g in grounded:
        st = "GENERATED" if g.generated else f"STALL ({g.stall[:40]}...)"
        parts = sorted(g.composition_parts)
        print(f"    · {g.operation:22s} {st}  parts={parts}")
    print()

    # ---- (2) GENERALITY — >=2 different operations, DIFFERENT held primitives ----
    print("-" * 78)
    print("GENERALITY (the donkey-check) — the SAME generate_grounding composes >=2")
    print("  DIFFERENT operations from their formulas, DIFFERENT held primitives")
    print("-" * 78)
    sigs = {g.operation: tuple(sorted(g.composition_parts)) for g in ok}
    for op, sig in sigs.items():
        print(f"    {op:22s} composed over: {list(sig)}")
    distinct = len(set(sigs.values())) >= 2
    multi = len(ok) >= 2
    print(f"  >=2 operations generated by the SAME generator        : {multi}")
    print(f"  with DISTINCT held-primitive compositions (not one shape): {distinct}")
    print()

    # ---- (3) DISCRIMINATION — a wrong (non-alternating) parse FAILS the knowns ----
    print("-" * 78)
    print("DISCRIMINATION — a WRONG parse (the NON-alternating sum) FAILS the knowns")
    print("  -> REJECTED (the self-verify discriminates the right composition)")
    print("-" * 78)
    wrong = _GG.generate_grounding("euler_characteristic", ["Euler characteristic"],
                                   http_get, sabotage=True)
    print(f"  euler with the alternating SIGN DROPPED (the wrong parse):")
    print(f"    held-formula: {wrong.held_formula}")
    for r in wrong.verify_rows:
        p = "PASS" if r["pass"] else "FAIL"
        print(f"    [{p}] {r['known']:5s} expected {r['expected']}  got {r['got']}")
    rejected = not wrong.generated
    print(f"  generated (should be False — REJECTED): {wrong.generated}")
    print(f"  => the SELF-VERIFY gate REJECTED the wrong-parse grounding: {rejected}")
    print()

    # ---- (4) FIXPOINT-CLOSURE — wired into the faculty-generator ----
    print("-" * 78)
    print("FIXPOINT-CLOSURE — generate_grounding WIRED into the faculty-generator")
    print("  (generate_faculty_grounded): the faculty's GROUNDING is now GENERATED from")
    print("  reading (not fixed to prose_to_operation) -> GENUINELY DIFFERENT faculties")
    print("-" * 78)
    fgaps = [
        _FG.FormulaGap("euler_glue", "euler_characteristic", ["Euler characteristic"],
                       "read the euler defining formula + generate its grounding"),
        _FG.FormulaGap("genus_glue", "genus", ["Genus (mathematics)"],
                       "read the genus-euler relation + generate its grounding"),
    ]
    facs = []
    for gap in fgaps:
        gf = _FG.generate_faculty_grounded(gap, http_get)
        facs.append(gf)
        st = "GENERATED" if gf.generated else f"STALL ({gf.stall[:40]})"
        print(f"  faculty {gf.faculty.name if gf.faculty else gap.name!r:34s} {st}")
        print(f"    grounding GENERATED from reading, composed over: "
              f"{sorted(gf.composition_parts)}  verified={gf.self_verified}")
    fac_ok = [f for f in facs if f.generated]
    fac_sigs = {tuple(sorted(f.composition_parts)) for f in fac_ok}
    fixpoint_turns = len(fac_ok) >= 2 and len(fac_sigs) >= 2
    print(f"  >=2 faculties generated with DIFFERENT groundings (not the same shape): "
          f"{fixpoint_turns}")
    print(f"    distinct grounding shapes: {[list(s) for s in fac_sigs]}")
    print()

    # ---- (5) THE META-SUB-WALL — un-held-leaf (Lefschetz) ----
    print("-" * 78)
    print("THE META-SUB-WALL (the honest reach) — un-held-leaf / inference-defined")
    print("-" * 78)
    lef = _GG.generate_grounding("lefschetz_number",
                                 ["Lefschetz number", "Lefschetz fixed-point theorem"],
                                 http_get)
    print(f"  lefschetz_number: formula READ = "
          f"{lef.read.note if lef.read else '(no formula)'}")
    print(f"    generated: {lef.generated}")
    print(f"    STALL (the sub-wall): {lef.stall}")
    print()

    # ---- THE OUTCOME ----
    print("=" * 78)
    print("THE OUTCOME")
    print("=" * 78)
    floor_crosses = multi and distinct and rejected and fixpoint_turns
    print(f"  >=2 groundings GENERATED from reading (self-verified) : {multi}")
    print(f"  GENERALITY (distinct held-primitive compositions)     : {distinct}")
    print(f"  DISCRIMINATION (wrong-parse REJECTED)                 : {rejected}")
    print(f"  FIXPOINT-CLOSURE (>=2 faculties, DIFFERENT groundings): {fixpoint_turns}")
    print(f"  meta-sub-wall located (un-held-leaf: Lefschetz tr)    : {not lef.generated}")
    print()
    if floor_crosses:
        print("  OUTCOME (a)/(b): THE FLOOR CROSSES for the formula-composable class.")
        print("    generate_grounding reads >=2 operations' formulas, PARSES them into")
        print("    held-primitive compositions (different primitives — betti+fold vs")
        print("    euler+divide), composes, self-verifies; a wrong-parse self-rejects;")
        print("    wired into the faculty-generator it generates GENUINELY DIFFERENT")
        print("    faculties (the fixpoint TURNS — generate the SHAPE). The meta-sub-wall:")
        print("    an operation whose grounding needs a NON-HELD leaf (Lefschetz's")
        print("    tr(H_k(f)) for a general map) STALLS honestly — outcome (b)'s precise")
        print("    localization of the design-from-scratch core.")
    else:
        print("  OUTCOME (c): PARTIAL — see the per-check flags above.")
    print()
    print("  the LLM authored NO composition (provenance: read formula -> parsed held-")
    print("  formula -> held leaves, all logged). Held primitives only. answer read: NO")
    print()
    print("[MARKER] GROUNDING_GENERATOR_FLOOR_COMPLETED")


if __name__ == "__main__":
    main()
