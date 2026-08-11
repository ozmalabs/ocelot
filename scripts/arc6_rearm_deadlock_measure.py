#!/usr/bin/env python3
"""AR18a -- does the re-arm deadlock, as literally described in
PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md SS5, still reproduce live on the CURRENT
(post-A17) shipped graph?  Run BEFORE any fix is written (PREREG amendment
A18).  This script makes NO Python decision: it boots the graph, runs the
SAME `live_run` scene `tests/test_arc_executor_migrated.py` already gates,
moves the row-verdict artifact off disk (the same real-world-change EX4's
own cell C uses), and then repeatedly probes / re-runs the fixpoint, reading
graph state back out at each step.  Whether the goal stays stuck is the
graph's own answer, read off `axe.pool` / `ArcGoal.status` / the epoch --
never decided here.

Writes `results/arc6_rearm_deadlock_before_fix.json`.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
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

RID = "arc6.verdict.row_verdict_seed_only"
AGID = "arc.remeasure." + RID
RID_2 = "arc6.structural.enum_op_table"
AGID_2 = "arc.remeasure." + RID_2


def _assert_engine_coherent(s):
    n = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    assert a["lst"] != a["tup"], "VALUE LAYER ABSENT"


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_executor"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    _assert_engine_coherent(s)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    return s, ag


def res(s, rid):
    for n in s.nodes("GoalResidual"):
        if s.node(n)["attrs"].get("rid") == rid:
            return n
    return None


def goal(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            return n
    return None


def snap(s, tag):
    g = goal(s, AGID)
    r = res(s, RID)
    return {
        "tag": tag,
        "epoch": agi.measure_epoch(s),
        "goal_status": s.node(g)["attrs"].get("status") if g else None,
        "retired_epoch": s.node(g)["attrs"].get("retired_epoch") if g else None,
        "residual_stale": s.node(r)["attrs"].get("stale") if r else None,
        "in_pool": AGID in axe.pool(s),
        "pool": sorted(axe.pool(s)),
        "structural_residual_stale": (
            s.node(res(s, RID_2))["attrs"].get("stale")
            if res(s, RID_2) else None),
        "structural_goal_present": goal(s, AGID_2) is not None,
        #  ONLY kind=='re_measure' is EVER executable on this graph (the
        #  other two shipped kinds, supply_blocker/source_claim, have no
        #  ExecClass -- confirmed by reading tools/build_arc_executor_seed.py
        #  and PROGRAM_SYNTHESIS_ARC6_PREREG.md A15 item 2).  A re_measure
        #  goal in the pool with no evidence_artifact is the testimony-
        #  sourced shape (AG-5 SS8 item 2) and is ALSO unroutable, so this is
        #  a conservative (may over-count) reading of "any candidate for
        #  executability", cheap and sufficient to show the pool is empty of
        #  even CANDIDATES, without evaluating the DSL route Term from
        #  Python (which would be exactly the kind of decision-in-Python
        #  this file must not contain).
        "re_measure_kind_pool_members": [
            a for a in axe.pool(s)
            for n in s.nodes("ArcGoal")
            if s.node(n)["attrs"].get("agid") == a
            and s.node(n)["attrs"].get("kind") == "re_measure"
        ],
    }


def answer_open_questions(s, conditioned=True):
    sent = 0
    for n in s.nodes("ArcQuestion"):
        a = s.node(n)["attrs"]
        if a.get("answered") == 1.0 or a.get("status") != "open":
            continue
        if conditioned:
            agi.attach_reply(s, n, "worth it while the op table stands",
                             cond_kind="fact_equals",
                             cond_filter_value="arc6_structural_ceiling_present",
                             cond_expected_str="1")
        else:
            agi.attach_reply(s, n, "I do not know either.")
        sent += 1
    return sent


def main():
    t0 = time.time()
    out = {"engine_provenance": provenance_stamp(),
           "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    s, ag = boot()
    s._inner.run_rules()
    n_q = answer_open_questions(s, conditioned=True)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1, "expected exactly one ExecOrder, got %d" % len(pending)

    steps = [snap(s, "0_before_execution")]
    rec = axe.run_order(s, pending[0], tag="ar18a")
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    steps.append(snap(s, "1_after_real_execution_retired"))

    #  Confirm: is the OTHER ExecClass organically stale on this engine right
    #  now?  If not, the pool genuinely holds ZERO executable re_measure
    #  goals at this point -- the deadlock's stated precondition, reached
    #  naturally, not constructed.
    steps[-1]["OTHER_execclass_organically_stale"] = (
        steps[-1]["structural_residual_stale"] == 1.0)

    #  Churn: repeated fixpoints, nothing external changes.
    for i in range(3):
        s._inner.run_rules()
    steps.append(snap(s, "2_churn_3x_run_rules"))

    #  A REAL world change: move the fresh artifact off disk.
    r = res(s, RID)
    art = os.path.join(ROOT, s.node(r)["attrs"]["evidence_artifact"])
    moved = art + ".ar18a_probe"
    shutil.move(art, moved)
    try:
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        steps.append(snap(s, "3_refailed_ONE_probe"))

        #  Repeat the probe + fixpoint cycle several more times.  If the
        #  deadlock is real, NOTHING here should ever move the epoch or
        #  bring the goal back, no matter how many times we look.
        for i in range(5):
            axe.refresh_evidence_facts(s)
            s._inner.run_rules()
            steps.append(snap(s, "4_repeat_probe_%d" % (i + 1)))
    finally:
        shutil.move(moved, art)
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
    steps.append(snap(s, "5_world_restored"))

    stuck = all(
        st["goal_status"] == "retired" and not st["in_pool"]
        and st["epoch"] == steps[1]["epoch"]
        for st in steps[2:2 + 1 + 5]  # cells 2..4_repeat_5 inclusive
    )
    genuinely_refailed_throughout = all(
        st["residual_stale"] == 1.0 for st in steps if st["tag"].startswith(
            ("3_", "4_")))

    out["steps"] = steps
    out["elapsed_seconds"] = round(time.time() - t0, 2)
    out["DEADLOCK_REPRODUCES"] = bool(stuck and genuinely_refailed_throughout)
    out["zero_executable_goals_at_retirement"] = (
        steps[1]["OTHER_execclass_organically_stale"] is False
        and steps[1]["re_measure_kind_pool_members"] == [])

    outp = os.path.join(ROOT, "results", "arc6_rearm_deadlock_before_fix.json")
    with open(outp, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=False)
    print(json.dumps({k: v for k, v in out.items() if k != "steps"}, indent=2))
    print("wrote", outp)
    for st in steps:
        print(st["tag"], "status=%s in_pool=%s epoch=%s stale=%s" % (
            st["goal_status"], st["in_pool"], st["epoch"], st["residual_stale"]))


if __name__ == "__main__":
    main()
