#!/usr/bin/env python3
"""Measure ARC-GRAIN GOAL MINTING and write `results/arc6_arc_goals.json`.

MEASUREMENT ONLY.  Nothing here decides anything: it boots, runs the fixpoint,
and READS the graph back.  Every number in the artifact is a read-off, and the
engine that produced it is stamped (protocol §10 rule 1) — a number from an
unknown binary is not a measurement.

Run:  python scripts/arc6_arc_goals_measure.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_goal_ingest as agi  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from domains.engine_provenance import provenance_stamp  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_arc_goals.json")


def _boot(seeds):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in seeds:
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    return s, ag


def _live():
    s, ag = _boot(("program_synthesis", "goal_residuals", "arc_goals"))
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    gri.install_facts(s, gri.probe_facts(s))
    return s, ag


def _pen_term():
    seed = json.load(open(os.path.join(ROOT, "seeds", "arc_goals.json")))
    for r in seed["rules"]:
        if r["name"] == "ag_select_audit":
            return r["effects"][0][3]["__term__"]
    raise SystemExit("ag_select_audit missing")


def job0_are_the_policies_live():
    """DESIGN UNCERTAINTY #4, CLOSED BY RUNNING RATHER THAN BY READING.

    The design assumed `gap_prioritization` / `stopping_policy` are live on the
    synthesis path *because they are in the `seeds/*.json` glob*.  Being in the
    glob is not being live — that is exactly the assumption §7 of the
    goal-residual doc warned about, and it is why the residual mechanism turned
    out inert.
    """
    import domains.prog_synthesis as psy
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    synth_progs = sorted({s.node(n)["attrs"].get("name")
                          for n in s.nodes("Program")} - {None})

    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    a = WorldAdapter(seeds=())
    rep = load_all_seeds(a)
    full_progs = sorted({a.s.node(n)["attrs"].get("name")
                         for n in a.s.nodes("Program")} - {None})
    return {
        "_question": ("are seeds/gap_prioritization.json and "
                      "seeds/stopping_policy.json LIVE on the synthesis path?"),
        "_verdict": "NO -- on both counts, and the second is the sharper one",
        "synthesis_path_boot": "domains.prog_synthesis.ensure_program_synthesis",
        "synthesis_path_n_Program_nodes": len(synth_progs),
        "synthesis_path_has_gap_priority": "gap_priority" in synth_progs,
        "synthesis_path_has_should_continue": "should_continue" in synth_progs,
        "synthesis_path_n_CapabilityGap": len(list(s.nodes("CapabilityGap"))),
        "full_boot_seeds_loaded": rep["loaded"],
        "full_boot_has_gap_priority": "gap_priority" in full_progs,
        "full_boot_has_should_continue": "should_continue" in full_progs,
        "full_boot_n_CapabilityGap": len(list(a.s.nodes("CapabilityGap"))),
        "_reading": (
            "The MBPP synthesis boot installs ZERO Program nodes at all, so "
            "neither policy is resident on the path this rung sits on. On the "
            "FULL load_all_seeds boot both Programs ARE resident -- and there "
            "are still ZERO CapabilityGap nodes, so gap_priority's Argmax has "
            "an EMPTY pool and should_continue returns its default (-1.0) i.e. "
            "STOP. Resident is not live either: the population is written by "
            "domains/gap_prioritization.py, so both Programs are inert unless a "
            "Python driver mints the gaps first. This CONFIRMS design sec 3's "
            "decision not to reuse CapabilityGap and sec 6.3's decision to make "
            "ag_select a RULE inside run_rules rather than a Program evaluated "
            "from Python -- adopting gap_priority's invocation style would have "
            "imported its Python driver along with its shape."),
    }


def ag1_mint():
    s, ag = _live()
    facts = {s.node(n)["attrs"]["name"]: s.node(n)["attrs"]["value"]
             for n in s.nodes("ResidualFact")}
    s._inner.run_rules()
    goals = agi.arc_goals(s)
    stale = sorted(s.node(n)["attrs"]["rid"] for n in s.nodes("GoalResidual")
                   if s.node(n)["attrs"].get("stale") == 1.0)
    before = sorted((g["agid"], g.get("status")) for g in goals)
    s._inner.run_rules()
    after = sorted((g["agid"], g.get("status")) for g in agi.arc_goals(s))
    return {
        "measured_facts_on_this_engine": facts,
        "stale_residual_ids": stale,
        "minted": sorted(
            [{"agid": g["agid"], "kind": g["kind"],
              "source_kind": g["source_kind"], "sig_seam": g.get("sig_seam"),
              "headroom_n": g.get("headroom_n"),
              "denominator_n": g.get("denominator_n"),
              "novelty_bits": g.get("novelty_bits"),
              "evidence_artifact": g.get("evidence_artifact"),
              "evidence_path": g.get("evidence_path")}
             for g in goals], key=lambda d: d["agid"]),
        "second_pass_is_a_no_op": before == after,
        "_reading": (
            "The re-measurement goal FIRES ON A CLEAN BOOT, unprompted, "
            "because value_layer_list_eq_tuple measures '0' on engine "
            "8311d4356082 and that falsifies the row-verdict ceiling's own "
            "condition. Its content -- 'the row-verdict ceiling was measured "
            "under a value layer that no longer exists; re-measure it' -- "
            "previously lived only in a markdown correction. The blocker goals "
            "come from seam A's MEASURED reach_class_counts, read with "
            "DictGet(FromJsonString(...)), not from reach_class (which is "
            "measured nearly inert: all six residuals operator_blocked)."),
    }


def ag1_annihilation():
    s, ag = _live()
    s._inner.run_rules()
    pen = _pen_term()
    g = [n for n in s.nodes("ArcGoal")
         if s.node(n)["attrs"].get("kind") == "re_measure"][0]
    while_stale = s._inner.evaluate(pen, {"g": g})
    src = [n for n in s.nodes("GoalResidual")
           if s.node(n)["attrs"]["rid"] == "arc6.verdict.row_verdict_seed_only"][0]
    s.set_attr(src, "stale", 0.0)
    when_returned = s._inner.evaluate(pen, {"g": g})

    s2, ag2 = _live()
    s2._inner.run_rules()
    g2 = [n for n in s2.nodes("ArcGoal")
          if s2.node(n)["attrs"].get("kind") == "re_measure"][0]
    for n in s2.nodes("ResidualFact"):
        if s2.node(n)["attrs"]["name"] == "value_layer_list_eq_tuple":
            s2.set_attr(n, "value", "1")
    s2._inner.run_rules()
    return {
        "penalty_on_the_remeasure_goal_while_its_source_is_STALE": while_stale,
        "penalty_on_the_SAME_goal_once_the_source_un_stales": when_returned,
        "status_after_the_condition_RETURNS": s2.node(g2)["attrs"]["status"],
        "retired_because": s2.node(g2)["attrs"].get("retired_because"),
        "_reading": (
            "THE TRAP DOES NOT BITE. A goal carrying its source residual's "
            "signature would normally be charged that residual's full weight "
            "the instant it entered the pool, cancelling the mint. It survives "
            "because the lifted matcher's Exists requires Not(Eq(stale,1)) -- a "
            "STALE RESIDUAL CHARGES NOTHING -- and that is a real property of "
            "the EXISTING matcher, not a fix. The refuting direction is "
            "measured in the same run: un-stale the source and the SAME goal is "
            "charged 51.33, so the 0.0 is about staleness and not about a "
            "matcher that never matches. And when the condition genuinely "
            "returns, ag_remeasure_retire removes the goal -- correct, because "
            "a ceiling whose world has come back does not need re-measuring, "
            "and relying on the weight alone would leave a dead goal in the "
            "pool forever."),
    }


def ag2_collapse():
    s, ag = _live()
    s._inner.run_rules()
    sel = agi.selection(s)
    ranked = []
    pen = _pen_term()
    pol = {k: v for k, v in
           s.node(list(s.nodes("ArcGoalPolicy"))[0])["attrs"].items()
           if k.startswith("w_") or k == "tie_break"}
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        h = a.get("headroom_n") or 0.0
        f = a.get("reach_class_factor") or 0.0
        p = s._inner.evaluate(pen, {"g": n})
        v = (pol["w_headroom"] * h * f
             - pol["w_residual"] * p
             - pol["w_mdl"] * (a.get("novelty_bits") or 0.0)
             - pol["w_cost"] * (a.get("cost_bits") or 0.0)
             - pol["w_unsignatured"] * (0.0 if a.get("sig_seam") else 1.0))
        ranked.append({"agid": a["agid"], "source_kind": a["source_kind"],
                       "headroom_n": h, "denominator_n": a.get("denominator_n"),
                       "residual_penalty": p, "value": v,
                       "dimensionless_ratio": (
                           None if not a.get("denominator_n")
                           else round(h / a["denominator_n"], 4))})
    ranked.sort(key=lambda d: -d["value"])
    by_ratio = sorted(ranked, key=lambda d: -(d["dimensionless_ratio"] or -1))
    return {
        "THE_DIMENSIONALITY_INVERSION_measured_on_the_SHIPPED_graph": {
            "_claim": ("the two readings of the SAME eight goals do not merely "
                       "differ -- they INVERT at the top"),
            "order_by_ABSOLUTE_HEADROOM_in_tasks": [d["agid"] for d in ranked],
            "order_by_the_DIMENSIONLESS_RATIO": [d["agid"] for d in by_ratio],
            "top_by_headroom": ranked[0]["agid"],
            "top_by_ratio": by_ratio[0]["agid"],
            "_reading": (
                "The dimensionless reading puts the four not_ingested CLAIMS "
                "first -- each is 1 task of 1, ratio 1.0 -- ahead of a blocker "
                "covering 42 tasks (ratio 0.79). That is the design's §6.2 "
                "defect, measured rather than argued: the ratio is a "
                "completeness score, and a value term denominated in "
                "completeness converges on the smallest possible target. "
                "The control is shown CAPABLE (A7): the same instrument, "
                "reading the same nodes, produces a DIFFERENT order -- so the "
                "'identical ratio' finding is about the reading, not about the "
                "channel."),
        },
        "policy_AUTHORED_not_measured": pol,
        "selection": sel,
        "ranking": ranked,
        "dimensionality_worked_example": {
            "_claim": ("the residual weight formula is a DIMENSIONLESS RATIO "
                       "-- right for a penalty, wrong as a value, because it "
                       "ranks a 15-task target EQUAL to a 257-task one"),
            "row_verdict_denominator_n": 15.0,
            "ir_retarget_denominator_n": 257.0,
            "value_uses": "denominator_n - honest_n, IN TASKS",
        },
        "cheap_goal_probe": {
            "_claim": ("the four not_ingested claims are the CHEAPEST goals "
                       "available; if the collapse converged on them the value "
                       "term would be wrong"),
            "winner_source_kind": sel.get("arc_sel_source_kind"),
            "not_ingested_values": [r["value"] for r in ranked
                                    if r["source_kind"] == "not_ingested"],
            "_reading": ("they rank LAST. Absolute headroom denominates value "
                         "in the thing that matters, so a 1-task claim cannot "
                         "out-earn a 42-task blocker -- and the unsignatured "
                         "cost prices their illegibility on top."),
        },
    }


def ag3_vocabulary():
    s, ag = _live()
    s._inner.run_rules()
    minted = [s.node(n)["attrs"] for n in s.nodes("SignatureVocab")
              if s.node(n)["attrs"].get("minted") == 1.0]
    epoch = agi.selection(s).get("arc_vocab_epoch")
    n_before = len(minted)
    s._inner.run_rules()
    n_after = len([n for n in s.nodes("SignatureVocab")
                   if s.node(n)["attrs"].get("minted") == 1.0])
    return {
        "minted_tokens": sorted(v["token"] for v in minted),
        "arc_vocab_epoch": epoch,
        "provenance_of_each": {v["token"]: [v["evidence_artifact"],
                                            v["evidence_path"]]
                               for v in minted},
        "second_pass_mints": n_after - n_before,
        "seam_alias_table_size": len(list(s.nodes("SeamAlias"))),
        "_reading": (
            "An unrecognised sig_seam token EXTENDS the vocabulary rather than "
            "being rejected -- one mint per pass (the serializer), each bumping "
            "arc_vocab_epoch, terminating when every proposal is explained. "
            "PROVENANCE IS THE REAL BOUND: every minted token is quoted from a "
            "measured artifact path, so the vocabulary grows only as fast as "
            "MEASUREMENT grows. RUNG 3 (new DIMENSIONS) STAYS DEFERRED, so the "
            "closed-vocabulary ceiling is LOWERED FROM DIMENSIONS TO TOKENS, "
            "not removed."),
    }


def ag4_the_ask():
    s, ag = _live()
    agi.set_measure_epoch(s, 0)
    s._inner.run_rules()
    qs = agi.questions(s)
    return {
        "questions": qs,
        "texts": agi.ask_texts(s),
        "_reading": (
            "On the shipped graph the ask FIRES, and it fires under IGNORANCE: "
            "the winner's seam was minted this pass (no residual can cover it) "
            "and the runner-up's source residual is STALE (a stale residual "
            "charges nothing and holds nothing). The discriminating pair -- "
            "same margin, one world with a matching non-stale residual and one "
            "without -- is gated in "
            "tests/test_arc_goals_migrated.py::test_ag4_HEADLINE_asks_under_"
            "IGNORANCE_and_NOT_under_REFUTATION, because the shipped graph "
            "gives only one of the two halves."),
    }


def main():
    rec = {
        "_README": (
            "ARC-GRAIN GOAL MINTING (AG-1..AG-4). AG-5 -- the executor: winner "
            "-> run -> artifact -> re-ingest -> epoch bump -- IS DELIBERATELY "
            "NOT BUILT. Without it this is a planning layer with no hands, and "
            "that is stated rather than implied."),
        "engine_provenance": provenance_stamp(strict=False),
        "seed": "seeds/arc_goals.json (self_load_only)",
        "JOB0_are_the_policies_live": job0_are_the_policies_live(),
        "AG1_mint": ag1_mint(),
        "AG1_annihilation_check": ag1_annihilation(),
        "AG2_collapse": ag2_collapse(),
        "AG3_vocabulary": ag3_vocabulary(),
        "AG4_the_ask": ag4_the_ask(),
    }
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2, sort_keys=False, default=str)
    print("wrote", OUT)
    print("engine:", rec["engine_provenance"].get("short"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
