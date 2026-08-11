#!/usr/bin/env python3
"""A19 -- THE SILENT ORDER-N FALLBACK, MADE OBSERVABLE.  Live measurement, both
directions.  PREREG amendment A19 (AR19a-AR19d).

This script makes NO Python decision: it boots graphs in the same shapes
`tests/test_arc_executor_migrated.py` already uses (`boot()` /
`_boot_with_magnitude()`), runs `run_rules()`, and reads back what the graph
itself decided -- `axe.agenda_verdicts(s, "order_n_fallback")` is a pure query,
the same shape `pool()`/`statuses()`/`orders()` already are.  Whether the
standing fact mints, clears, or leaves dispatch unperturbed is the graph's own
answer.

Writes `results/arc6_silent_fallback.json`.
"""
from __future__ import annotations

import json
import os
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
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from domains.engine_provenance import provenance_stamp  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

RID = "arc6.verdict.row_verdict_seed_only"
AGID = "arc.remeasure." + RID


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


def _boot_with_magnitude(ladder=True):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_magnitude", "arc_executor"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    _assert_engine_coherent(s)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    ami.resolve_attrition_keys(s)
    if ladder:
        ami.install_tier_ladder(s, ami.probe_tier_ladder())
    return s, ag


def answer_open_questions(s, conditioned=False):
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


def fb(s):
    return axe.agenda_verdicts(s, "order_n_fallback")


def agenda(s):
    return s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]


def main():
    t0 = time.time()
    out = {"engine_provenance": provenance_stamp(),
           "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # ---- AR19a: order-N genuinely absent -> the fact mints -------------- #
    s1, _ = boot()
    before_any_run = fb(s1)
    s1._inner.run_rules()
    at1 = agenda(s1)
    out["AR19a"] = {
        "mg_sel_agid": at1.get("mg_sel_agid"),
        "fallback_before_any_run_rules": before_any_run,
        "fallback_after": fb(s1),
        "double_mint_check_after_3_more_passes": None,
    }
    s1._inner.run_rules()
    s1._inner.run_rules()
    s1._inner.run_rules()
    out["AR19a"]["double_mint_check_after_3_more_passes"] = fb(s1)

    # ---- AR19b(i) CONTROL: order-N live from the start, ladder installed #
    s2, _ = _boot_with_magnitude(ladder=True)
    s2._inner.run_rules()
    at2 = agenda(s2)
    axe.arm(s2)
    s2._inner.run_rules()
    orders2 = [dict(s2.node(n)["attrs"]) for n in s2.nodes("ExecOrder")]
    out["AR19b_control_ladder"] = {
        "arc_sel_agid": at2.get("arc_sel_agid"),
        "mg_sel_agid": at2.get("mg_sel_agid"),
        "collapses_disagree": at2.get("arc_sel_agid") != at2.get("mg_sel_agid"),
        "fallback_after_dispatch": fb(s2),
        "orders": [{"agid": o["agid"], "selected_by": o["selected_by"]}
                   for o in orders2],
    }

    # ---- AR19b(i) CONTROL, no ladder: collapses AGREE, still no fallback # #
    s2b, _ = _boot_with_magnitude(ladder=False)
    s2b._inner.run_rules()
    at2b = agenda(s2b)
    out["AR19b_control_no_ladder"] = {
        "arc_sel_agid": at2b.get("arc_sel_agid"),
        "mg_sel_agid": at2b.get("mg_sel_agid"),
        "collapses_agree": at2b.get("arc_sel_agid") == at2b.get("mg_sel_agid"),
        "fallback": fb(s2b),
    }

    # ---- AR19b(ii) TRANSITION: order-N goes live mid-graph, no epoch bump #
    s3, ag3 = boot()
    s3._inner.run_rules()
    before3 = fb(s3)
    epoch_before = agi.measure_epoch(s3)
    s3._inner.load_seed_manifest(manifest_for("arc_magnitude"), ag3)
    ami.resolve_attrition_keys(s3)
    ami.install_tier_ladder(s3, ami.probe_tier_ladder())
    s3._inner.run_rules()
    at3 = agenda(s3)
    epoch_after = agi.measure_epoch(s3)
    out["AR19b_transition"] = {
        "epoch_before": epoch_before,
        "epoch_after": epoch_after,
        "epoch_unchanged": epoch_before == epoch_after,
        "mg_sel_agid_before": None,
        "mg_sel_agid_after": at3.get("mg_sel_agid"),
        "fallback_before": before3,
        "fallback_after": fb(s3),
        "same_node_id": (before3[0]["_id"] == fb(s3)[0]["_id"]
                         if before3 and fb(s3) else None),
    }

    # ---- AR19c: order-1 dispatch, unmodified, alongside the standing fact #
    s4, _ = boot()
    s4._inner.run_rules()
    fb_present_before_dispatch = fb(s4)
    axe.arm(s4)
    s4._inner.run_rules()
    orders_before_reply = list(s4.nodes("ExecOrder"))
    answer_open_questions(s4, conditioned=True)
    s4._inner.run_rules()
    axe.arm(s4)
    s4._inner.run_rules()
    orders4 = [dict(s4.node(n)["attrs"]) for n in s4.nodes("ExecOrder")]
    out["AR19c_order1_dispatch_alongside_fact"] = {
        "fallback_present_before_dispatch": fb_present_before_dispatch,
        "orders_before_reply": orders_before_reply,
        "orders_after_reply": [{"agid": o["agid"], "selected_by": o["selected_by"]}
                               for o in orders4],
        "fallback_still_present": fb(s4),
    }

    out["elapsed_seconds"] = round(time.time() - t0, 2)
    outp = os.path.join(ROOT, "results", "arc6_silent_fallback.json")
    with open(outp, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=False, default=str)
    print(json.dumps(out, indent=2, sort_keys=False, default=str))
    print("wrote", outp)


if __name__ == "__main__":
    main()
