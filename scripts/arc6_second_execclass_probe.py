#!/usr/bin/env python
"""arc6_second_execclass_probe — A15's own bonus extension (EC3's optional
clause): does the second `ExecClass` actually produce a pool STATE distinct
from A14's own real-only n=2?  NOT a re-litigation of A14's IC2/IC3 verdict
(which stands as measured, AMBIGUOUS/NO-GO) — a narrow, single-purpose check
of whether this rung's own new capability moves what A14 SS9.2 named as the
blocker: "the real-only subset is small (n=2) because this system currently
has exactly one internally-reachable pool composition... only new capability
... can [add a third distinct composition]."

METHOD.  Boot fresh.  The row-verdict residual is ALREADY organically stale
on this engine (`value_layer_list_eq_tuple == '0'`) — no poke needed.  The
structural residual is forced stale via the SAME narrow `_put_fact` poke the
test suite uses (A13 SS7.1's precedent; the real committed artifact is never
touched).  BOTH `re_measure` goals are then driven to real completion in
sequence — TWO real subprocess-backed remeasurements, one ~140s (row-verdict)
and one <1s (structural) — and the resulting pool/impotence state is read
off and compared against A14's own two documented real states.

Not a permanent gate: this is a REPORTING script, run once, for the results
doc. `results/arc6_second_execclass_probe.json` is engine+seed stamped.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from domains.engine_provenance import provenance_stamp  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

RID_ROW = "arc6.verdict.row_verdict_seed_only"
AGID_ROW = "arc.remeasure." + RID_ROW
RID_STRUCT = "arc6.structural.enum_op_table"
AGID_STRUCT = "arc.remeasure." + RID_STRUCT


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_executor"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    return s, ag


def pool_agids(s):
    return sorted(axe.pool(s))


def run_one(s, agid, tag):
    """Clamp every OTHER goal's headroom to 0 (the A13 SS7.1 pool-exit
    technique), drive `agid` to a real dispatch + execution, then RESTORE
    every clamped goal's real headroom.

    BUG FOUND WHILE BUILDING THIS PROBE (recorded in the results doc): the
    first draft clamped but never restored, so the SECOND call in a
    sequence found its OWN target goal still clamped to 0 by the FIRST
    call's loop (every OTHER goal at that time included whichever goal
    would be targeted next).  `pending_orders` came back empty and the
    `assert` below caught it BEFORE any tree-mutating runner was invoked —
    verified clean: `git status` and every protected-file sha were
    unaffected by the failed run.
    """
    snapshot = {}
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        if a.get("agid") != agid:
            snapshot[n] = a.get("headroom_n")
            s.set_attr(n, "headroom_n", 0.0)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1, (agid, pending)
    rec = axe.run_order(s, pending[0], tag=tag)
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    #  Restore every clamped goal's REAL headroom, so the NEXT capability's
    #  own natural pool membership is not left artificially suppressed --
    #  this probe wants to see the REAL resulting agenda, not a narrowed one.
    for n, orig in snapshot.items():
        if orig is not None:
            s.set_attr(n, "headroom_n", orig)
    s._inner.run_rules()
    return rec


def main():
    t0 = time.time()
    s, ag = boot()
    s._inner.run_rules()

    pool_boot = pool_agids(s)
    row_stale_boot = s.node(
        [n for n in s.nodes("GoalResidual")
         if s.node(n)["attrs"].get("rid") == RID_ROW][0])["attrs"].get("stale")

    #  Force the structural residual stale too (A13 SS7.1 poke -- the real
    #  committed artifact stays untouched).
    axe._put_fact(s, "arc6_structural_ceiling_present", "0")
    s._inner.run_rules()
    pool_after_poke = pool_agids(s)
    assert AGID_STRUCT in pool_after_poke, pool_after_poke

    #  Run the CHEAP one first (structural, <1s) so a failure in the
    #  expensive one (row-verdict, ~140s) is not wasted.
    rec_struct = run_one(s, AGID_STRUCT, "a15probe_struct")
    pool_after_struct = pool_agids(s)

    rec_row = run_one(s, AGID_ROW, "a15probe_row")
    pool_after_both = pool_agids(s)

    verdicts = axe.agenda_verdicts(s, "impotent")
    final_verdict = verdicts[-1] if verdicts else None

    out = {
        "_README": (
            "A15's bonus extension probe.  Does the second ExecClass "
            "produce a real pool state A14's own sweep never reached?  "
            "A14's real-only subset was n=2: (a) row-verdict retired alone "
            "-> nearest_unroutable_kind=supply_blocker; (b) a testimony "
            "chain re-ranks the SAME 7-goal pool -> source_claim.  This "
            "probe drives BOTH re_measure residuals to real completion in "
            "one boot -- a pool composition neither A14 state reached, "
            "because A14 had no second capability to reach it with."),
        "engine_provenance": provenance_stamp(),
        "pool_boot_n": len(pool_boot),
        "pool_boot": pool_boot,
        "row_verdict_organically_stale_at_boot": row_stale_boot,
        "pool_after_structural_forced_stale_n": len(pool_after_poke),
        "structural_remeasure_rec": {
            k: rec_struct.get(k) for k in
            ("agid", "runner", "status", "elapsed_seconds")},
        "pool_after_structural_retires_n": len(pool_after_struct),
        "pool_after_structural_retires": pool_after_struct,
        "row_verdict_remeasure_rec": {
            k: rec_row.get(k) for k in
            ("agid", "runner", "status", "elapsed_seconds")},
        "pool_after_BOTH_retire_n": len(pool_after_both),
        "pool_after_BOTH_retire": pool_after_both,
        "is_a_THIRD_distinct_real_composition": (
            sorted(pool_after_both) != sorted(pool_boot) and
            AGID_ROW not in pool_after_both and
            AGID_STRUCT not in pool_after_both),
        "final_impotence_verdict": (
            dict(final_verdict) if final_verdict else None),
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    out_path = os.path.join(ROOT, "results", "arc6_second_execclass_probe.json")
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k not in
                      ("_README",)}, indent=1, default=str))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
