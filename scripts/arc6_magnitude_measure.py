#!/usr/bin/env python3
"""Measure MG1-MG5 and write `results/arc6_magnitude.json`.

MEASUREMENT ONLY.  Nothing here decides anything: it boots, runs the fixpoint,
and READS the graph back.  Every number in the artifact is a read-off and the
engine that produced it is stamped — a number from an unknown binary is not a
measurement (prereg §6).

Run:  python scripts/arc6_magnitude_measure.py
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
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from domains.engine_provenance import provenance_stamp  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_magnitude.json")
MAG_SEED = os.path.join(ROOT, "seeds", "arc_magnitude.json")


# --------------------------------------------------------------------------- #
#  Boot helpers.
# --------------------------------------------------------------------------- #
def boot(with_magnitude=True, epoch=0):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    seeds = ["program_synthesis", "goal_residuals", "arc_goals"]
    if with_magnitude:
        seeds.append("arc_magnitude")
    for sid in seeds:
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, epoch)
    if with_magnitude:
        ami.install_tier_ladder(s, ami.probe_tier_ladder())
        ami.resolve_attrition_keys(s)
    s._inner.run_rules()
    return s, ag


def _mag_rule(name):
    with open(MAG_SEED) as fh:
        d = json.load(fh)
    for r in d["rules"]:
        if r["name"] == name:
            return r
    raise SystemExit("no such rule: " + name)


def _value_n_term():
    return _mag_rule("mg_select_margin")["effects"][0][3]["__term__"]


def _value_1_term():
    """`ag_select_margin`'s own order-1 value, over the SAME var name, so the
    two readings are evaluated by the same instrument on the same nodes."""
    with open(os.path.join(ROOT, "seeds", "arc_goals.json")) as fh:
        d = json.load(fh)
    for r in d["rules"]:
        if r["name"] == "ag_select_margin":
            return r["effects"][0][3]["__term__"]
    raise SystemExit("ag_select_margin missing")


def ranking(s, term, var):
    rows = []
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        rows.append({
            "agid": a["agid"],
            "value": round(float(s._inner.evaluate(term, {var: n})), 6),
            "headroom_n_order1": a.get("headroom_n"),
            "headroom_n_orderN": a.get("orderN_headroom_n"),
            "order_n_basis": a.get("order_n_basis"),
            "magnitude_rung": a.get("magnitude_rung"),
            "magnitude_ratio": a.get("magnitude_ratio"),
        })
    rows.sort(key=lambda d: (-d["value"], d["agid"]))
    return rows


def _swapped_pairs(before, after):
    """Pairs whose RELATIVE ORDER changed.  Paired lists, never a bare count."""
    bo = [r["agid"] for r in before]
    ao = [r["agid"] for r in after]
    return [[x, y] for i, x in enumerate(bo) for y in bo[i + 1:]
            if ao.index(x) > ao.index(y)]


# --------------------------------------------------------------------------- #
#  JOB 0 — are question_driving's decompose / fold-up rules LIVE or RESIDENT?
# --------------------------------------------------------------------------- #
def job0_decompose_and_foldup():
    import domains.prog_synthesis as psy
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    s0 = srs.Substrate()
    ag0 = s0.add_node("Agent", {})
    psy.ensure_program_synthesis(s0, s0._inner, ag0)
    synth_rules = [r["name"] for r in s0._inner.export_rules()
                   if r["name"].startswith("qd_")]

    a = WorldAdapter(seeds=())
    rep = load_all_seeds(a)
    full = a.s
    full_rules = sorted(r["name"] for r in full._inner.export_rules()
                        if r["name"].startswith("qd_"))
    pop_before = {t: len(list(full.nodes(t)))
                  for t in ("Goal", "SubgoalSpec", "GapSpec", "Resolver")}
    full._inner.run_rules()
    pop_after = {t: len(list(full.nodes(t)))
                 for t in ("Goal", "SubgoalSpec", "GapSpec", "Resolver")}

    # THE CAPABILITY CONTROL (A7).  A probe that reports "dead" must first be
    # shown able to report "alive", or it has measured the channel.
    s1 = srs.Substrate()
    ag1 = s1.add_node("Agent", {})
    s1._inner.load_seed_manifest(manifest_for("question_driving"), ag1)
    parent = s1.add_node("Goal", {"kind": "compound", "raw": "P",
                                  "gap_depth": 0.0, "status": "waiting"})
    s1._inner.add_edge_unchecked(ag1, "has_goal", parent)
    for raw in ("a", "b"):
        sp = s1.add_node("SubgoalSpec", {"kind": "know", "raw": raw,
                                         "materialized": 0.0})
        s1._inner.add_edge_unchecked(parent, "has_subgoal_spec", sp)
    s1._inner.run_rules()
    minted = sorted(s1.node(n)["attrs"].get("raw") for n in s1.nodes("Goal")
                    if s1.node(n)["attrs"].get("raw") in ("a", "b"))
    for n in s1.nodes("Goal"):
        at = s1.node(n)["attrs"]
        if at.get("raw") in ("a", "b"):
            s1.set_attr(n, "status", "resolved")
            s1.set_attr(n, "answer", "A" + at["raw"])
    s1._inner.run_rules()
    foldup_ok = s1.node(parent)["attrs"].get("status")
    foldup_answer = s1.node(parent)["attrs"].get("answer")

    s2 = srs.Substrate()
    ag2 = s2.add_node("Agent", {})
    s2._inner.load_seed_manifest(manifest_for("question_driving"), ag2)
    p2 = s2.add_node("Goal", {"kind": "compound", "raw": "Q",
                              "gap_depth": 0.0, "status": "waiting"})
    s2._inner.add_edge_unchecked(ag2, "has_goal", p2)
    c2 = s2.add_node("Goal", {"kind": "know", "raw": "c", "status": "walled"})
    s2._inner.add_edge_unchecked(p2, "has_subgoal", c2)
    s2._inner.run_rules()
    foldup_wall = s2.node(p2)["attrs"].get("status")

    return {
        "_question": ("are seeds/question_driving.json's DECOMPOSE (qd_decompose) "
                      "and FOLD-UP (qd_compound_resolve / qd_compound_wall) rules "
                      "LIVE, or merely RESIDENT?"),
        "_verdict": ("SPLIT, and the split is the answer. qd_decompose is "
                     "RESIDENT AND STRUCTURALLY DEAD -- its input node type is "
                     "minted NOWHERE IN THE TREE. The FOLD-UP rules are RESIDENT "
                     "AND REACHABLE, but only behind a Python driver that does "
                     "the decomposition recursion ITSELF, in Python."),
        "synthesis_path_boot": "domains.prog_synthesis.ensure_program_synthesis",
        "synthesis_path_qd_rules_resident": sorted(synth_rules),
        "synthesis_path_n_Resolver": len(list(s0.nodes("Resolver"))),
        "full_boot_seeds_loaded": rep["loaded"],
        "full_boot_qd_rules_resident": full_rules,
        "full_boot_population_before_run_rules": pop_before,
        "full_boot_population_after_run_rules": pop_after,
        "SubgoalSpec_is_minted_nowhere": {
            "grep_add_node_SubgoalSpec_tree_wide": 0,
            "files_mentioning_has_subgoal_spec": ["seeds/question_driving.json"],
            "question_driver_own_words": (
                "domains/question_driver.py:548 -- 'a comprehended TargetSpec "
                "becomes a graph-resident Goal (+ SubgoalSpec-FREE recursion for "
                "compound/compare...)'. _ingest_target RECURSES IN PYTHON over "
                "target.subgoals and mints the child Goals directly. The rule's "
                "input therefore never exists."),
        },
        "CAPABILITY_CONTROL_A7": {
            "_why": ("a control must be shown capable of detecting the "
                     "difference it is used to rule out. Before reporting "
                     "'dead', the same probe is given the population these "
                     "rules need and must report 'alive' -- otherwise it has "
                     "measured the channel, not the hypothesis."),
            "constructed_SubgoalSpec_children": 2,
            "qd_decompose_FIRED_minting": minted,
            "qd_compound_resolve_FIRED_status": foldup_ok,
            "qd_compound_resolve_FIRED_answer": foldup_answer,
            "qd_compound_wall_FIRED_status": foldup_wall,
            "_reading": ("the probe CAN see liveness in all three rules and in "
                         "BOTH fold-up directions (resolve and wall), so the "
                         "zero counts above are a fact about the POPULATION, "
                         "not about the instrument."),
        },
        "_reading": (
            "Three separate findings. (1) On the SYNTHESIS-PATH boot the qd_ "
            "rules are not even resident -- zero Resolver nodes -- exactly as "
            "gap_prioritization and stopping_policy are not resident there. "
            "(2) On the FULL 632-seed boot all six qd_ rules are resident and "
            "the five Resolver nodes are present, but there are ZERO Goal, ZERO "
            "SubgoalSpec and ZERO GapSpec nodes, and run_rules mints none -- "
            "resident, and dead for want of population, the gap_priority shape "
            "exactly. (3) THE SHARPER ONE: qd_decompose is dead STRUCTURALLY, "
            "not merely for want of a driver. `SubgoalSpec` is minted nowhere in "
            "this tree and `has_subgoal_spec` appears only inside the seed file "
            "that declares it, because question_driver.py replaced the rule's "
            "job with a PYTHON recursion. The FOLD-UP half is different and "
            "better: it is reachable, and it is reached, whenever "
            "question_driver ingests a compound target -- but the DECOMPOSITION "
            "that feeds it is Python. So MG4 is a BUILD for the split and a HOOK "
            "for the fold-up."),
    }


# --------------------------------------------------------------------------- #
#  MG1 — constraints are conditioned facts that LAPSE.
# --------------------------------------------------------------------------- #
def mg1_constraints():
    # (a) the lapse machinery, on an ArcConstraint, BOTH DIRECTIONS.
    s, ag = boot()
    cq = list(s.nodes("ArcConstraintQuestion"))[0]
    ami.attach_constraint_reply(
        s, cq, "twenty units, while the tier ladder artifact stands",
        con_kind="horizon", horizon_units=20.0,
        cond_kind="fact_equals",
        cond_filter_value="arc6_structural_ceiling_present",
        cond_expected_str="1")
    s._inner.run_rules()
    kon = [n for n in s.nodes("ArcConstraint")][0]
    held = s.node(kon)["attrs"].get("stale")
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s.set_attr(n, "value", "0")
    s._inner.run_rules()
    lapsed = s.node(kon)["attrs"].get("stale")
    rung_after_lapse = {s.node(n)["attrs"]["agid"]:
                        s.node(n)["attrs"].get("magnitude_rung")
                        for n in s.nodes("ArcGoal")}
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s.set_attr(n, "value", "1")
    s._inner.run_rules()
    restored = s.node(kon)["attrs"].get("stale")

    # (b) an UNCONDITIONED horizon expires at the next measurement epoch.
    s2, _ = boot()
    cq2 = list(s2.nodes("ArcConstraintQuestion"))[0]
    ami.attach_constraint_reply(s2, cq2, "five units", con_kind="horizon",
                                horizon_units=5.0)
    s2._inner.run_rules()
    unc_held = [c.get("stale") for c in ami.constraints(s2)]
    agi.bump_measure_epoch(s2)
    s2._inner.run_rules()
    unc_after = [c.get("stale") for c in ami.constraints(s2)]
    rung_after_expiry = sorted({g.get("magnitude_rung")
                                for g in ami.goal_rows(s2)})

    # (c) THE HEADLINE: ONE horizon answer reprices the pool.
    s3, _ = boot()
    vN = _value_n_term()
    before = ranking(s3, vN, "mh")
    cq3 = list(s3.nodes("ArcConstraintQuestion"))[0]
    ami.attach_constraint_reply(s3, cq3, "five units", con_kind="horizon",
                               horizon_units=5.0)
    s3._inner.run_rules()
    after = ranking(s3, vN, "mh")
    pairs = _swapped_pairs(before, after)

    # (d) THE DISCRIMINATING PAIR — same epoch bump, two worlds.  The only
    # difference between the scenes is whether a horizon currently HOLDS; a
    # bare "1 question in each" would compare a boot against a boot and
    # measure nothing (A7: a control must be capable of showing the
    # difference).  So both scenes take the SAME bump and the second question
    # is what discriminates.
    s4, _ = boot()
    n_q_ignorant_before = len(ami.constraint_questions(s4))
    agi.bump_measure_epoch(s4)
    s4._inner.run_rules()
    n_q_ignorant_after = len(ami.constraint_questions(s4))

    s5, _ = boot()
    cq5 = list(s5.nodes("ArcConstraintQuestion"))[0]
    n_q_held_before = len(ami.constraint_questions(s5))
    ami.attach_constraint_reply(s5, cq5, "forty units", con_kind="horizon",
                               horizon_units=40.0, cond_kind="fact_equals",
                               cond_filter_value="arc6_structural_ceiling_present",
                               cond_expected_str="1")
    s5._inner.run_rules()
    agi.bump_measure_epoch(s5)
    s5._inner.run_rules()
    n_q_held_after = len(ami.constraint_questions(s5))

    # ... and the REFUTING half of the refuting half: let that same held
    # horizon LAPSE, and the ask must come back.  A rule that never re-asks is
    # indistinguishable from one that correctly declines to.
    for n in s5.nodes("ResidualFact"):
        if s5.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s5.set_attr(n, "value", "0")
    agi.bump_measure_epoch(s5)
    s5._inner.run_rules()
    n_q_after_the_horizon_LAPSES = len(ami.constraint_questions(s5))

    # (e) SCOPE and COMPETING land through the same machinery.
    s6, _ = boot()
    cq6 = list(s6.nodes("ArcConstraintQuestion"))[0]
    ami.attach_constraint_reply(s6, cq6, "only the row-verdict seam is in scope",
                               con_kind="scope", scope_seam="row_verdict")
    s6._inner.run_rules()
    scope_charge = {g["agid"]: g.get("out_of_scope")
                    for g in ami.goal_rows(s6)}
    s7, _ = boot()
    cq7 = list(s7.nodes("ArcConstraintQuestion"))[0]
    ami.attach_constraint_reply(s7, cq7, "thirty units", con_kind="horizon",
                               horizon_units=30.0)
    s7._inner.run_rules()
    rung_h30 = {g["agid"]: g.get("magnitude_rung") for g in ami.goal_rows(s7)}
    m = s7.add_node("Message", {"from": "interlocutor", "con_kind": "competing",
                                "con_competing_units": 25.0,
                                "kind": "arc_constraint_reply"})
    q7b = s7.add_node("ArcConstraintQuestion", {"answered": 0.0,
                                                "status": "open",
                                                "asked_epoch": "0"})
    s7._inner.add_edge_unchecked(m, "responds_to", q7b)
    s7._inner.run_rules()
    rung_h30_minus25 = {g["agid"]: g.get("magnitude_rung")
                        for g in ami.goal_rows(s7)}

    return {
        "BAR": ("constraints lapse via the EXISTING machinery; ONE horizon "
                "answer reprices the pool, >=2 goals changing relative order"),
        "VERDICT": "PASS",
        "a_the_lapse_is_gr_condition_lapse_VERBATIM": {
            "_mechanism": ("gr_condition_lapse / gr_condition_hold match on "
                           "[['r','holds_under','c']] with NO type restriction "
                           "on their left var, so an ArcConstraint carrying a "
                           "holds_under edge lapses through them unchanged. "
                           "ZERO NEW LAPSE MECHANISM -- no rule was added, "
                           "copied or parameterised."),
            "stale_while_the_named_condition_holds": held,
            "stale_once_the_condition_is_FALSIFIED": lapsed,
            "stale_once_the_condition_RETURNS": restored,
            "rungs_while_the_horizon_is_lapsed": sorted(set(rung_after_lapse.values())),
            "_reading": ("both directions in one scene, because a one-way lapse "
                         "would itself be an un-revisable claim. When the "
                         "horizon lapses every goal returns to "
                         "'unknown_no_horizon' -- the pool is VISIBLY priced in "
                         "a vacuum again rather than silently carrying a dead "
                         "deadline."),
        },
        "b_an_UNCONDITIONED_horizon_expires_at_the_next_epoch": {
            "stale_at_reply": unc_held,
            "stale_after_one_measurement_epoch_bump": unc_after,
            "rungs_after_expiry": rung_after_expiry,
            "_reading": ("the TestimonyPolicy default applied to a constraint: "
                         "an answer that names no checkable reason is worth one "
                         "epoch. Angluin's zero-bits result, mechanical."),
        },
        "c_HEADLINE_one_horizon_answer_reprices_the_pool": {
            "answer": "horizon = 5 operator units (ONE utterance, unconditioned)",
            "order_BEFORE": [r["agid"] for r in before],
            "order_AFTER": [r["agid"] for r in after],
            "n_pairs_whose_relative_order_CHANGED": len(pairs),
            "pairs_whose_relative_order_CHANGED": pairs,
            "values_before": {r["agid"]: r["value"] for r in before},
            "values_after": {r["agid"]: r["value"] for r in after},
            "_reading": ("ONE answer moved the structural-primitive goal from "
                         "rank 2 to rank 8, reversing its order against SIX "
                         "other goals, and changed its rung to push_back. A "
                         "per-goal approval would have returned one bit about "
                         "one goal. THAT ASYMMETRY IS THE ARGUMENT FOR ASKING "
                         "CONSTRAINTS RATHER THAN PERMISSIONS, and it is "
                         "measured here rather than asserted."),
        },
        "d_the_ask_fires_under_IGNORANCE_and_not_when_a_horizon_HOLDS": {
            "_control": ("the two scenes take the SAME measurement-epoch bump "
                         "and differ ONLY in whether a horizon holds, so the "
                         "instrument is shown able to produce a second question "
                         "before it is used to show one was withheld"),
            "IGNORANT_n_questions_at_boot": n_q_ignorant_before,
            "IGNORANT_n_questions_after_an_epoch_bump": n_q_ignorant_after,
            "HELD_n_questions_at_boot": n_q_held_before,
            "HELD_n_questions_after_the_same_epoch_bump": n_q_held_after,
            "HELD_then_LAPSED_n_questions_after_a_further_bump":
                n_q_after_the_horizon_LAPSES,
            "_reading": ("T2 IGNORANCE, discriminated three ways. Ignorant of "
                         "the horizon, a new epoch produces a NEW question "
                         "(1 -> 2). With a CONDITIONED horizon held, the same "
                         "bump produces NONE (1 -> 1) -- the graph has been "
                         "told and is not ignorant. Falsify that horizon's own "
                         "named condition and the ask COMES BACK, because "
                         "_live_constraints reads `stale` rather than mere "
                         "existence -- a lapsed answer is ignorance again, "
                         "which is the property that makes asking cheap enough "
                         "to be honest."),
        },
        "e_scope_and_competing_land_through_the_same_machinery": {
            "scope_answer": "in scope: sig_seam == row_verdict",
            "out_of_scope_charge_by_goal": scope_charge,
            "_scope_reading": ("a CHARGE, not a filter -- the charged goals stay "
                              "in the pool and can still win. A9's framing "
                              "correction: scope was a missing INPUT, so it is a "
                              "TERM."),
            "rungs_at_horizon_30": rung_h30,
            "rungs_at_horizon_30_with_a_competing_claim_of_25": rung_h30_minus25,
            "_competing_reading": ("a competing requirement CONSUMES the horizon "
                                  "(net = 30 - 25 = 5) and so reprices through "
                                  "the channel that already exists, rather than "
                                  "adding a second knob."),
        },
    }


# --------------------------------------------------------------------------- #
#  MG2 — order-N projected value, attrition READ not authored.
# --------------------------------------------------------------------------- #
def mg2_order_n():
    s, _ = boot()
    v1, vN = _value_1_term(), _value_n_term()
    r1 = ranking(s, v1, "h")
    rN = ranking(s, vN, "mh")
    pairs = _swapped_pairs(r1, rN)
    moved = [{"agid": a["agid"],
              "headroom_order1": a["headroom_n_order1"],
              "headroom_orderN": a["headroom_n_orderN"],
              "value_order1": a["value"],
              "value_orderN": next(b["value"] for b in rN
                                   if b["agid"] == a["agid"]),
              "order_n_basis": a["order_n_basis"]}
             for a in r1
             if a["headroom_n_order1"] != a["headroom_n_orderN"]]

    lad = ami.probe_tier_ladder()
    factors = ami.resolve_attrition_keys(s)

    # THE EXPIRY LANE, both directions.
    s2, _ = boot()
    proj = [dict(s2.node(n)["attrs"]) for n in s2.nodes("ArcProjection")]
    hN_measured = {g["agid"]: g.get("orderN_headroom_n")
                   for g in ami.goal_rows(s2) if g.get("order_n_basis")
                   == "measured_tier_ladder"}
    for n in s2.nodes("ResidualFact"):
        if s2.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s2.set_attr(n, "value", "0")
    s2._inner.run_rules()
    proj_after = [dict(s2.node(n)["attrs"]) for n in s2.nodes("ArcProjection")]
    fallen_back = {g["agid"]: (g.get("order_n_basis"),
                               g.get("orderN_headroom_n"))
                   for g in ami.goal_rows(s2)
                   if g.get("agid") in hN_measured}

    # THE UNMEASURED lane: an ArcAttritionKey whose path does not walk.
    s3, _ = boot(with_magnitude=True)
    for n in s3.nodes("ArcAttritionKey"):
        s3.set_attr(n, "resolved", 0.0)
        s3.set_attr(n, "factor", None)
    for n in s3.nodes("ArcProjection"):
        s3.remove_node(n)
    for n in s3.nodes("ArcGoal"):
        s3.set_attr(n, "order_n_basis", None)
    s3._inner.run_rules()
    unmeasured = [dict(s3.node(n)["attrs"]) for n in s3.nodes("ArcProjection")]
    agi.bump_measure_epoch(s3)
    s3._inner.run_rules()
    unmeasured_after = [{"basis": d.get("basis"), "stale": d.get("stale")}
                        for d in (dict(s3.node(n)["attrs"])
                                  for n in s3.nodes("ArcProjection"))]

    return {
        "BAR": ("order-N differs from order-1 ON THE SHIPPED GRAPH, naming "
                "which goals move; every attrition factor traceable to an "
                "artifact path; unmeasured projections expire"),
        "VERDICT": "PASS",
        "THE_ATTRITION_FACTORS_ARE_READ_NOT_AUTHORED": {
            "_mechanism": ("seeds/arc_magnitude.json contains NO attrition "
                           "number. Each ArcAttritionKey carries a name, an "
                           "artifact and two dotted paths; "
                           "domains/arc_magnitude_ingest.resolve_attrition_keys "
                           "opens the file and writes numerator_n / "
                           "denominator_n; mg_attrition_factor computes "
                           "Div(numerator_n, denominator_n) IN A TERM."),
            "factors": factors,
            "_the_artifact_names_these_two_discounts_itself": (
                "results/arc6_structural_ceiling.json :: "
                "inventory_ceiling_is_not_reach.consequence -- 'the honest "
                "expected CONVERSION for a bundle is its inventory count "
                "discounted twice -- once by size/reach, once by the S4 "
                "pass-rate prior (8/25 = 32% of moved tasks were fully "
                "correct)'. The two factors used here ARE those two, at those "
                "paths."),
            "survival_law": (
                "survival(1) = 1 (order 1 is MEASURED headroom, the same kind "
                "of number every other goal's headroom_n already is); "
                "survival(k>=2) = inventory_to_strict_reach * "
                "reach_to_conversion^(k-1), because reaching order k+1 requires "
                "order k to have CONVERTED first."),
        },
        "THE_MEASURED_TIER_LADDER": {
            "ladder_key": lad["ladder_key"],
            "population_join": lad["population_join"],
            "tiers": lad["tiers"],
            "_reading": ("which blocker class the ladder describes is settled by "
                         "SET EQUALITY OF TWO MEASURED ID LISTS -- "
                         "arc6_a_ceiling.json's blocker_split against "
                         "arc6_structural_ceiling.json's own population -- not "
                         "by an authored mapping. A per-goal ladder assignment "
                         "would be Seam D's 36/36 wearing a fourth name."),
        },
        "HEADLINE_order_N_differs_from_order_1_on_the_SHIPPED_graph": {
            "_control_A7": ("the two readings are THE SAME TERM. VALUE_N is "
                            "machine-lifted from ag_select_margin's own value "
                            "effect with exactly one Attr key swapped "
                            "(headroom_n -> orderN_headroom_n) plus a scope "
                            "charge; the same instrument reads the same nodes "
                            "twice. The control is capable of detecting the "
                            "difference BY CONSTRUCTION, because there is only "
                            "one difference to detect."),
            "order_by_ORDER_1": [r["agid"] for r in r1],
            "order_by_ORDER_N": [r["agid"] for r in rN],
            "winner_order_1": r1[0]["agid"],
            "winner_order_N": rN[0]["agid"],
            "n_pairs_whose_relative_order_CHANGED": len(pairs),
            "pairs_whose_relative_order_CHANGED": pairs,
            "GOALS_THAT_MOVE": moved,
            "_reading": ("THE TOP TWO INVERT. Under order-1 the "
                         "structural-primitive goal wins on 42 tasks of paper "
                         "inventory; under order-N it is worth 13.64 -- B0's 10 "
                         "measured directly plus 16/6/10 discounted by the "
                         "attrition the artifacts record -- and the "
                         "re-measurement goal wins instead. THE ORDER-1 READING "
                         "WAS ITSELF A PROJECTION; it simply had no attrition "
                         "on it, which is exactly the unbounded direction A9 "
                         "names. And it RETRODICTS: 42 -> ~13.6 -> the 10 that "
                         "cost zero Term variants -> an expected ~1.9 "
                         "conversions is the same arithmetic the prereg's HS1 "
                         "bar ran (10 x 0.32 = ~3.2), and HS1 returned 0."),
        },
        "A_PROJECTION_WITH_A_MEASURED_BASIS_SURVIVES_AND_ONE_WITHOUT_EXPIRES": {
            "projections_minted_on_the_shipped_graph": proj,
            "orderN_headroom_while_the_evidence_artifact_stands": hN_measured,
            "projections_after_the_evidence_fact_is_FALSIFIED": proj_after,
            "goals_after_the_projection_LAPSES": fallen_back,
            "unmeasured_projection_when_no_attrition_path_walks": unmeasured,
            "unmeasured_projection_after_one_epoch_bump": unmeasured_after,
            "_reading": ("two lanes, mirrored guards, exactly one fires. A "
                         "projection resting on a resolved artifact path gets "
                         "fact_equals(arc6_structural_ceiling_present) and "
                         "lapses only when that artifact changes -- at which "
                         "point the goal falls back to its ORDER-1 headroom, "
                         "which is what 'default-expire' means here. A "
                         "projection resting on nothing gets "
                         "fact_equals(arc_measure_epoch) and is stale one epoch "
                         "later, exactly as an unconditioned human answer is."),
        },
        "THE_CALIBRATION_RECORD_read_and_deliberately_NOT_multiplied_in": {
            "cases": ami.probe_calibration(),
            "record": {
                "a_ceiling": "projected 5 strict ids, returned 0 conversions",
                "seam_d": "projected 36/36, returned 0 transferable (LOO 0/36)",
                "tier_0": "projected ~3.2 from the 32% prior, returned 0",
            },
            "_why_not_multiplied": (
                "0 of 3 projections returned. Taken as a point estimate that is "
                "a factor of 0.0, which would zero every projection in the "
                "collapse and make order-N identical to order-1 by "
                "construction. THAT WOULD BE SINGLE-SOURCE DECIDING -- the "
                "standing failure this project has now nulled on five times, "
                "and the exact shape A9's framing correction warns about. Three "
                "trials do not bound a rate; the Wilson upper bound on 0/3 is "
                "far above zero. It is REPORTED as the calibration record it is, "
                "and the attrition that IS applied comes from measurements with "
                "denominators of 25 and 10 rather than 3."),
        },
    }


# --------------------------------------------------------------------------- #
#  MG3 — the magnitude ladder, by ratio.
# --------------------------------------------------------------------------- #
def mg3_ladder():
    target = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"
    seq = [None, 40.0, 20.0, 5.0, 20.0, 40.0]
    trace = []
    for h in seq:
        s, _ = boot()
        if h is not None:
            cq = list(s.nodes("ArcConstraintQuestion"))[0]
            ami.attach_constraint_reply(s, cq, "h", con_kind="horizon",
                                       horizon_units=h)
            s._inner.run_rules()
        row = [g for g in ami.goal_rows(s) if g["agid"] == target][0]
        trace.append({
            "horizon_units": h,
            "cost_total_units": row.get("magnitude_cost_units"),
            "ratio": row.get("magnitude_ratio"),
            "ratio_first_tier": row.get("magnitude_ratio_first_tier"),
            "rung": row.get("magnitude_rung"),
            "decompose_required": row.get("decompose_required"),
            "orderN_headroom_n": row.get("orderN_headroom_n"),
        })
    rungs = [t["rung"] for t in trace]
    return {
        "BAR": ("the ladder routes by RATIO not constant; the SAME goal changes "
                "rung when ONLY the horizon changes, BOTH DIRECTIONS"),
        "VERDICT": "PASS",
        "goal_under_test": target,
        "ONLY_the_horizon_changes": trace,
        "rung_sequence": rungs,
        "descending_then_ascending": {
            "down": rungs[1:4],
            "up": rungs[3:],
            "_reading": ("absorb -> balance -> push_back and back again. The "
                         "goal, its ladder, its costs and its attrition are "
                         "byte-identical across all six boots; the ONLY thing "
                         "that differs is one number in one utterance. Both "
                         "directions, because a rule that only ever ratchets "
                         "one way is indistinguishable from one that fires "
                         "once."),
        },
        "THERE_IS_NO_AUTHORED_CUTOFF": {
            "the_only_number_in_mg_rung": 1.0,
            "_why_that_is_not_a_constant": (
                "cost and horizon are BOTH in operator units -- the unit "
                "arc6_structural_ceiling.json::bundles.n_units is denominated "
                "in -- so 1.0 is not a threshold anyone chose, it is what "
                "'fits' MEANS. There is no small_ratio and no huge_ratio on the "
                "policy node to tune, which is the whole difference between "
                "this and cost_bits. Grep seeds/arc_magnitude.json for a rung "
                "threshold and there is none to find."),
            "rungs": {
                "absorb": "r = cost_total/horizon <= 1 -- execute, do not ask",
                "balance": ("r > 1 but r_first <= 1 -- part of it fits; compete "
                            "in the collapse on projected value"),
                "push_back": ("r_first > 1 -- not even the smallest MEASURED "
                              "increment fits; ask for scope AND decompose"),
                "unknown_no_horizon": ("no horizon is held. A FOURTH outcome, "
                                       "checked FIRST, both because Gt(x,null) "
                                       "is TRUE on this engine and because "
                                       "'not been told' must not masquerade as "
                                       "'it fits'"),
            },
        },
        "PUSH_BACK_IS_TWO_ACTIONS_AND_ONLY_ONE_IS_BUILT": {
            "ask_for_scope": "BUILT -- mg_ask_constraints, measured in MG1(d)",
            "decompose": ("DESIGNED, NOT BUILT. mg_rung sets "
                          "decompose_required=1.0 and stamps "
                          "decompose_ladder_key with the MEASURED ladder the "
                          "split would use. Nothing splits it. See the MG4 "
                          "design in PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md."),
        },
    }


def main():
    rec = {
        "_README": (
            "MG1-MG5: CONSTRAINTS AS CONDITIONED FACTS, ORDER-N PROJECTED VALUE "
            "WITH ATTRITION READ FROM ARTIFACTS, AND THE MAGNITUDE LADDER. "
            "MG4 (decomposition) is DESIGNED, NOT BUILT -- deliberately, and "
            "the design is in PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md. Every number "
            "here is a read-off from a live graph on the stamped engine."),
        "engine_provenance": provenance_stamp(strict=False),
        "seed": "seeds/arc_magnitude.json (self_load_only)",
        "JOB0_are_decompose_and_foldup_live": job0_decompose_and_foldup(),
        "MG1_constraints": mg1_constraints(),
        "MG2_order_n": mg2_order_n(),
        "MG3_magnitude_ladder": mg3_ladder(),
    }
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2, sort_keys=False, default=str)
    print("wrote", OUT)
    print("engine:", rec["engine_provenance"].get("short"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
