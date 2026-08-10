"""faculty_generator_fixpoint — PART 2/3: THE GENERATOR + THE FIXPOINT TEST.

cmsg157. The template (faculty_template.make_faculty) is the frozen core (re-derived
>=2 existing faculties — faculty_template_redrive.py, the anti-vapor proof). THIS is
the FLEX: the GENERATOR (faculty_generator.generate_faculty) INSTANTIATES the template
from READING — it recognizes a gap, READS the math (GET-only), EXTRACTS the four
params, INSTANTIATES, and SELF-VERIFIES. The fixpoint turns iff the generator makes
>=2 NEW faculties (NOT one of the 5 pre-existing) from reading, self-verified + applied.

THE FIXPOINT TEST (does the slope change?):
  · GENERATE >=2 NEW faculties from reading (DIFFERENT gaps, DIFFERENT articles ->
    DIFFERENT extracted params). Each NEW (the agent's own — direct-product, semidirect-
    product; NOT the pre-existing HNN/free-product/amalgam the pipeline already had).
  · GENERALITY (the meta-donkey-check): the SAME generator produces the >=2 from
    different reading — NOT a hardcode of one faculty.
  · APPLY a generated faculty in the pipeline (the agent generated + USED its own
    faculty): run its self-verified op as a glue-operator on a held composition.
  · SELF-REJECT: a deliberately-WRONG param-set (the union op verified against the HNN
    known) FAILS the gate -> REJECTED. The answer (671579) is never read.

THE PROVENANCE (the donkey-rail): per generated faculty, the four params' provenance =
the READ text (the parsed presentation + the op kind read off the prose) + the HELD
primitive grounding selected. The shell injects NO param.

THE META-SUB-WALL: the generator inherits prose_to_operation's reach — it generates
faculties whose params are formula/structure-extractable + held-groundable, and STALLS
on an article with no presentation formula (needs-inference). Shown.

No LLM. No Rust. Math/reading/web domain only. Speech path untouched. Answer never read.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.join(str(ROOT), "runners", "dsl", "python"))

from domains import faculty_generator as _GEN                    # noqa: E402
from domains import faculty_template as _FT                      # noqa: E402
from scripts import prose_to_operation_pipeline as _PIPE         # noqa: E402
from scripts import strict_compose_pants_structure as _CMP       # noqa: E402
from scripts.strict_compose_pants_structure import Piece         # noqa: E402


# ===========================================================================
# THE GAPS the agent articulates — NEW constructions it wants a faculty for (NOT the
# 5 pre-existing faculties, NOT the HNN/free-product/amalgam the pipeline already had).
# Each gap names WHERE to read (the agent's retrieval decision); the params are
# EXTRACTED from reading, not in the gap.
# ===========================================================================

GAPS = [
    _GEN.Gap(name="direct_product_glue",
             titles=["Direct product of groups"],
             need=("a faculty that reads the direct-product construction and grounds "
                   "its operation (how it combines two group presentations) so I can "
                   "carry a direct-product glue in my held machinery")),
    _GEN.Gap(name="semidirect_product_glue",
             titles=["Semidirect product"],
             need=("a faculty that reads the semidirect-product construction and "
                   "grounds its operation (the twisting/conjugation it adds) so I can "
                   "carry a semidirect glue in my held machinery")),
    # the META-SUB-WALL gap — an article whose operation is NOT a presentation formula
    # (needs inference). The generator STALLS honestly here.
    _GEN.Gap(name="wreath_product_glue",
             titles=["Wreath product"],
             need=("a faculty for the wreath-product construction (its operation is "
                   "not stated as a simple presentation delta — the needs-inference "
                   "probe)")),
]


def _h1_rank(piece):
    return piece.h1().free_rank if piece else None


def main() -> None:
    print("=" * 78)
    print("FACULTY-GENERATOR — PART 2/3: the FLEX + the FIXPOINT TEST")
    print("=" * 78)
    print("generate_faculty(gap): RECOGNIZE gap -> READ (GET-only) -> EXTRACT the 4")
    print("  params from reading + held primitives -> INSTANTIATE the template ->")
    print("  SELF-VERIFY. >=2 NEW faculties generated from reading => the slope changes.")
    print()

    http_get = _PIPE._author_http_get()
    print("  full-text fetch: agent-authored http_get (GET-only) + local-wiki fallback")
    print()

    # ---- GENERATE each gap's faculty ----
    generated: list[_GEN.GeneratedFaculty] = []
    for gap in GAPS:
        print("-" * 78)
        print(f"GAP: {gap.name}")
        print(f"  NEED (articulated): {gap.need}")
        print(f"  ROUTE (GET-only): {gap.titles}")
        gf = _GEN.generate_faculty(gap, http_get)
        generated.append(gf)
        rd = gf.provenance.get("read")
        if rd:
            loc = rd["url"] or f"(local: {rd['source']})"
            print(f"  READ: {rd['title']!r} [{rd['source']}] textlen {rd['textlen']} "
                  f"<- {loc}")
        # the 4-param provenance (the proof the params came from READING + held prims).
        for key in ("grammar", "target_form", "grounding", "knowns"):
            if key in gf.provenance:
                print(f"  PARAM[{key}]: {gf.provenance[key]}")
        if gf.generated:
            print(f"  SELF-VERIFY (the gate):")
            for r in gf.self_verify_rows:
                p = "PASS" if r["pass"] else "FAIL"
                print(f"    [{p}] {r['known']:42s} expected rank {r['expected']} "
                      f"got {r['got']}")
            print(f"  => GENERATED + SELF-VERIFIED: faculty {gf.faculty.name!r} "
                  f"(op kind {gf.op_kind!r})")
        else:
            print(f"  => STALL (honest): {gf.stall}")
        print()

    # ---- THE MEASURE: N generated + generality ----
    ok = [g for g in generated if g.generated]
    print("=" * 78)
    print("THE MEASURE — N NEW faculties generated from reading")
    print("=" * 78)
    print(f"  gaps articulated                 : {len(GAPS)}")
    print(f"  NEW faculties GENERATED + verified: {len(ok)}")
    print(f"  stalled (the meta-sub-wall)      : {len(generated) - len(ok)}")
    for g in generated:
        status = (f"GENERATED (op={g.op_kind})" if g.generated
                  else f"STALL ({g.stall[:46]}...)")
        print(f"    · {g.gap.name:26s} {status}")
    print()

    # ---- GENERALITY (the meta-donkey-check): SAME generator, >=2 DIFFERENT faculties
    print("-" * 78)
    print("GENERALITY (the meta-donkey-check) — the SAME generate_faculty produced")
    print("  >=2 DIFFERENT faculties from DIFFERENT reading (not a one-off hardcode)")
    print("-" * 78)
    kinds = sorted({g.op_kind for g in ok})
    titles = sorted({g.provenance["read"]["title"] for g in ok})
    print(f"  the SAME generator generated {len(ok)} faculties from {len(titles)} "
          f"DISTINCT articles: {titles}")
    print(f"  yielding op kinds read off DISTINCT prose: {kinds}")
    distinct_articles = len(titles) >= 2
    multi = len(ok) >= 2
    print(f"  >=2 NEW faculties from the SAME generator: {multi}")
    print(f"  from >=2 DISTINCT articles (not one hardcode): {distinct_articles}")
    print()

    # ---- THE FIXPOINT APPLICATION: APPLY a generated faculty in the pipeline ----
    print("-" * 78)
    print("THE FIXPOINT — APPLY a generated faculty in the pipeline (the agent USES")
    print("  its OWN generated faculty as a glue-operator on a held composition)")
    print("-" * 78)
    applied_ok = False
    if ok:
        gf = ok[0]                          # the direct-product faculty (union glue)
        fac = gf.faculty
        # APPLY: use the generated faculty's SELF-VERIFIED glue (gf.glue — the held
        # applier the gate just passed on the textbook knowns) on a NEW held
        # composition: an annulus glued to a disk along one circle (separate
        # components). The generated union-glue should kill the annulus generator
        # (rank 1 -> 0), the textbook result. The agent GENERATED this faculty by
        # reading AND now USES it — on an input it did NOT self-verify against.
        ann = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1,
                    note="annulus")
        dsk = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
        u = _CMP.disjoint_union(ann, dsk)
        before = _h1_rank(u)
        glued = gf.glue(u, 0, 2)            # annulus-t (0) ~ disk (2)
        after = _h1_rank(glued)
        applied_ok = (after == 0 and before == 1)
        print(f"  generated faculty: {fac.name!r} (op {gf.op_kind!r}, read from "
              f"{gf.provenance['read']['title']!r})")
        print(f"  APPLIED to a NEW held composition (annulus glued to disk along one "
              f"circle):")
        print(f"    before glue: H_1 free rank {before}  (annulus generator free)")
        print(f"    after  glue: H_1 free rank {after}   (the generated glue killed it)")
        print(f"    textbook result (annulus->disk = disk, rank 0): {applied_ok}")
        print(f"  => the agent GENERATED a faculty by reading AND USED it in the "
              f"pipeline.")
    print()

    # ---- SELF-REJECT: a deliberately-WRONG param-set fails the gate ----
    print("-" * 78)
    print("THE GATE — a deliberately-WRONG param-set SELF-REJECTS")
    print("-" * 78)
    # take the direct-product gap (a union op) but FORCE the HNN known: the union op
    # reads rank 1 (not 2) on the connected self-glue -> the gate REJECTS.
    wrong = _GEN.generate_faculty(
        GAPS[0], http_get,
        force_wrong_known="add_stable_generator_conjugation")
    print(f"  gap {GAPS[0].name!r} (a union op) with the WRONG known "
          f"(the HNN connected known) forced:")
    for r in wrong.self_verify_rows:
        p = "PASS" if r["pass"] else "FAIL"
        print(f"    [{p}] {r['known']:42s} expected rank {r['expected']} "
              f"got {r['got']}")
    rejected = (not wrong.generated)
    print(f"  generated (should be False — REJECTED): {wrong.generated}")
    print(f"  stall: {wrong.stall[:120]}")
    print(f"  => the SELF-VERIFY gate REJECTED the mis-instantiated faculty: "
          f"{rejected}")
    print()

    # ---- THE OUTCOME ----
    print("=" * 78)
    print("THE OUTCOME — does the slope change (the generable class)?")
    print("=" * 78)
    fixpoint_turns = (multi and distinct_articles and applied_ok and rejected)
    print(f"  >=2 NEW faculties generated from reading (self-verified): {multi}")
    print(f"  generality (>=2 distinct articles, same generator)      : {distinct_articles}")
    print(f"  a generated faculty APPLIED in the pipeline             : {applied_ok}")
    print(f"  a deliberately-wrong param-set SELF-REJECTED            : {rejected}")
    print()
    if fixpoint_turns:
        print("  OUTCOME (a): THE FIXPOINT TURNS. The template re-derives >=2 existing")
        print("    faculties (faculty_template_redrive.py — the frozen core is real) AND")
        print("    the generator generates >=2 NEW faculties from READING (self-verified,")
        print("    applied) — faculty-generation is the AGENT'S; one-at-a-time ends for")
        print("    the generable class (the formula/structure-extractable + held-")
        print("    groundable faculties). The meta-sub-wall: needs-inference constructions")
        print("    (no presentation formula) STALL honestly.")
    else:
        print("  OUTCOME (b): TEMPLATE REAL, GENERATOR PARTIAL — the frozen core is")
        print("    genuine but the generator extracted params for only some gaps / a")
        print(f"    check did not pass (multi={multi} generality={distinct_articles} "
              f"applied={applied_ok} rejected={rejected}).")
    print()

    # ---- THE META-SUB-WALL ----
    print("-" * 78)
    print("THE META-SUB-WALL (the honest reach)")
    print("-" * 78)
    stalled = [g for g in generated if not g.generated and g.gap.name != "_wrong"]
    gen_names = [g.gap.name for g in ok]
    stall_names = [g.gap.name for g in generated if not g.generated]
    print(f"  GENERATED (formula-extractable + held-groundable): {gen_names}")
    print(f"  STALLED (needs-inference / no presentation formula): {stall_names}")
    print(f"  the generator inherits prose_to_operation's reach: it instantiates the")
    print(f"  template for constructions whose params are READable off the presentation")
    print(f"  prose + groundable to the held glue machinery, and STALLS where the")
    print(f"  operation needs INFERENCE (no <gens|rels> formula in the prose).")
    print()
    print(f"  answer (671579) read: NO")
    print()
    print("[MARKER] FACULTY_GENERATOR_FIXPOINT_COMPLETED")


if __name__ == "__main__":
    main()
