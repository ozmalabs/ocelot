"""THE META-LAYER LANDS — the jabberwock PLANS + ORCHESTRATES its OWN operational
work from a natural-language instruction. The companion to the probe
(scripts/jabberwock_plans_bulk_load.py) that NAMED the four meta-gaps; this script
SHOWS them closed, each verbatim:

  META-GAP 2 (codebook)     -> the CODEBOOK FIX: 'bulk load of wikipedia' now matches
                               the bulk_load OperationalCapability, NOT the ink LETTER
                               'a' the composer decoded it as.
  META-GAP 1 (no faculty)   -> INSTRUCTION->PLAN: the 3-sentence instruction becomes an
                               ordered plan of capability-bound steps.
  META-GAP 4 (no orchestr.) -> EXECUTE END-TO-END: run_plan FIRES the plan — a real
                               small load, the agent's OWN sufficiency verdict, the
                               other gaps perceived — the SAME assessment the probe
                               HAND-DROVE, now AGENT-ORCHESTRATED from the instruction.
  META-GAP 3 (fixed cycles) -> MULTI-LAYER: a NESTED instruction becomes a plan TREE
                               (for-each over the perceived gaps, an if-then guard,
                               report, stop) the executor iterates + branches.

donkey=0 — no LLM in the match, the plan, the guards, or the executor.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_plans_and_runs.py
"""
from __future__ import annotations
import os, sys, io, contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

ORIGINAL = ("Do a bulk load of Wikipedia. Identify if it is sufficiently fast. "
            "Identify if there are other gaps.")
NESTED = ("Load 15 articles. For each gap you find, diagnose it; if it is worth "
          "fixing, fix it. Then report how many were fixed and stop when the rest "
          "is sufficient.")
DIFFERENT = "Warm up wordnet. Then measure timing. Finally summarize."


def _rule(c="="):
    print(c * 78)


def _boot():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return fn(*a, **k)


def main() -> int:
    import domains.operational_planning as op
    a = _boot()

    _rule()
    print("THE JABBERWOCK PLANS + ORCHESTRATES ITS OWN OPERATIONAL WORK")
    _rule()

    # --- CODEBOOK FIX (headline vs the probe) ---------------------------------
    _rule("-")
    print("CODEBOOK FIX — the exact probe failures now resolve to OPERATIONS, not ink\n")
    for clause in ("bulk load of wikipedia", "measure timing", "other gaps",
                   "is it fast enough", "report the result"):
        m = op.match_capability(a, clause)
        print(f"  {clause!r:28} -> OperationalCapability {m['name']!r:18} "
              f"(overlap score={m['score']}, tokens={m['tokens']})")
    print("\n  (the probe's compose_design_for_concept('bulk load of wikipedia') "
          "returned\n   the handwriting LETTER 'a'; the capability_match Argmax "
          "returns bulk_load.)")

    # --- INSTRUCTION -> PLAN ---------------------------------------------------
    _rule("-")
    print("INSTRUCTION -> PLAN  (the original 3-sentence instruction)\n")
    print(f"  INSTRUCTION: {ORIGINAL!r}\n")
    parsed = op.parse_instruction(a, ORIGINAL)
    print(op.plan_view(a, parsed))

    # --- EXECUTE END-TO-END ----------------------------------------------------
    _rule("-")
    print("EXECUTE END-TO-END  (run_plan FIRES it — the human did NOT sequence it)\n")
    res = _quiet(op.run_plan, a, parsed, max_load=6)
    print(op.trace_view(res["trace"]))
    print("\n  >>> the load, the sufficiency verdict, and the other-gaps perception")
    print("      were sequenced by the PLAN (parse_instruction) and fired by run_plan —")
    print("      NOT by a human-written script. That is meta-gap 4 closed.")

    # --- MULTI-LAYER -----------------------------------------------------------
    _rule("-")
    print("MULTI-LAYER  (a NESTED instruction -> a plan TREE; iterate + branch)\n")
    print(f"  INSTRUCTION: {NESTED!r}\n")
    p2 = op.parse_instruction(a, NESTED)
    print(op.plan_view(a, p2))
    print("\n  --- executing the tree (foreach iterates, if-then branches) ---\n")
    res2 = _quiet(op.run_plan, a, p2, max_load=6)
    print(op.trace_view(res2["trace"]))

    # --- DATA-DRIVEN -----------------------------------------------------------
    _rule("-")
    print("DATA-DRIVEN  (a DIFFERENT instruction -> a DIFFERENT plan, same parser)\n")
    print(f"  INSTRUCTION: {DIFFERENT!r}\n")
    p3 = op.parse_instruction(a, DIFFERENT)
    print(op.plan_view(a, p3))

    # --- LEDGER ----------------------------------------------------------------
    _rule()
    print("HONEST LEDGER")
    _rule()
    print("""
  GRAPH (the decisions):
    · the clause->capability MATCH is the capability_match Argmax Program (overlap
      of clause tokens vs each OperationalCapability's token_blob) — no Python maps
      a clause to a capability;
    · the if-then GUARD is an authored cond Term (Gt(it.norm_salience,
      FixWorthPolicy.threshold)) evaluated in Rust; the stop guard is the
      should_continue Program;
    · the PLAN is graph nodes/edges (Plan / PlanStep + has_step / next / substep /
      uses_capability / foreach_source).

  BOUNDARY (the mechanics):
    · SEGMENTATION (instruction -> clauses -> content tokens via comprehend_text.gaps);
    · the CAPABILITY BINDINGS (_CAPABILITY_REGISTRY -> the EXISTING object fns:
      consume / where_does_load_time_go / should_continue / perceive_consumption_gaps
      / the gap drivers) — registered + called, NOT reimplemented;
    · run_plan is a MECHANICAL enactor (the _enact_advance twin): it dispatches by
      binding_key + evaluates the plan's cond Terms; it never decides the work.

  CONTROL-FLOW COVERAGE (implemented): SEQUENCE (next), FOR-EACH (over a graph-
    produced item set), IF-THEN (an authored graph cond Term), plus a stop guard.

  RESIDUALS (honest): 'diagnose' has no distinct operational capability -> it shows
    as an honest no-match step (a coverage residual, printed above); deeper (>2-level)
    nesting is parsed recursively but only exercised to 2 levels; if-ELSE / while-until
    are not yet control kinds; complex inter-step data dependencies beyond the threaded
    context dict; the NL segmenter is regex/comprehension-token based, not a full
    parser; the reflex-driven (tick-loop) executor variant is a documented residual
    (run_plan is the direct executor).
""")
    _rule()
    print("donkey (LLM calls) = 0  — the match, plan, guards, and executor are all graph/boundary")
    _rule()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
