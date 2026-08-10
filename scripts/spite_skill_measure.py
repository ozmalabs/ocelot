#!/usr/bin/env python3
"""BLOCK 213000 -- SPITE + SKILL confirmatory measure (all Gs, pre-registered power).

Extends the 212000 HARVEST value economy with two NEW graph-data knobs
(seeds/spite_skill.json): w_spite (the negative-social MIRROR of w_supergraph) and
order_n (planning depth). Every agent decision is a graph RULE (ss_decision_value
-> ss_choose_harvest / ss_choose_burn); this script is a MEASURE, it takes NO
agent decision. Writes results/spite_skill/results.json. Numbers per
SPITE_SKILL_PREREG.md.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np                                          # noqa: E402
from domains.harvest_spite_world import HarvestSpiteWorld, socially_optimal_h, R0  # noqa: E402
from domains.harvest_world import HarvestWorld              # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "spite_skill")
CANON_MD5 = "793ce09ed498a749abb79aeaea44b92e"
N = 6
RUNS = 40
T = 40
ENF = 25          # institutional sanction magnitude (pre-registered)


def _boot_ci(xs, reps=2000, seed=213000):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


# ------------------------------------------------------------------ G-spite
def g_spite():
    """(a) DETERMINISTIC triple: payoff-max / psychopath / spiteful side by side in
    ONE bare commons -- only the spiteful agent takes the self-costly BURN.
    (b) POWERED population: fraction spiteful p -> collective harm (total burned +
    others' yield loss), with CIs; the w_spite=0 control burns nothing."""
    # (a) deterministic triple, held over a full run (self-cost accumulates)
    triple = HarvestSpiteWorld([0.0, 0.0, 0.0], w_spites=[0.0, 0.0, 1.0],
                               order_ns=[1.0, 1.0, 1.0], comms=False, enforcement=0)
    triple.step()
    rows = triple.decisions()
    o = triple.outcome(T=T)      # continues the run from the recorded first step
    triple.close()
    det = dict(
        labels=["payoff_max", "psychopath", "spiteful"],
        knobs=[dict(w_supergraph=r["w_supergraph"], w_spite=r["w_spite"], order_n=r["order_n"]) for r in rows],
        chosen_harvest=[r["chosen_harvest"] for r in rows],
        chosen_burn=[r["chosen_burn"] for r in rows],
        burns=[r["burns"] for r in rows],
        per_agent_yield=o["per_agent_yield"],
        per_agent_burned=o["per_agent_burned"],
        # malice != indifference: only the spiteful burns; it is SELF-COSTLY
        only_spiteful_burns=(rows[0]["burns"] == 0 and rows[1]["burns"] == 0 and rows[2]["burns"] == 1),
        spiteful_self_costly=(o["per_agent_yield"][2] < o["per_agent_yield"][1]),
        psychopath_equals_payoffmax=(rows[0]["chosen_harvest"] == rows[1]["chosen_harvest"]
                                     and rows[0]["burns"] == rows[1]["burns"]))

    # (b) powered population sweep: p = P(agent spiteful); control zeroes w_spite
    levels, ctrl_levels = [], []
    for k in range(0, N + 1):
        p = k / N
        burned, oyield, ctrl_burned = [], [], []
        for r in range(RUNS):
            rng = np.random.default_rng(213100 + 100 * k + r)
            spite_mask = [1.0 if rng.random() < p else 0.0 for _ in range(N)]
            ws = [0.0] * N                              # all selfish on the CARE axis
            hw = HarvestSpiteWorld(ws, w_spites=list(spite_mask), order_ns=[1.0] * N,
                                   comms=False, enforcement=0)
            oo = hw.outcome(T=T); hw.close()
            burned.append(oo["total_burned"])
            oyield.append(oo["total_yield"])
            # CONTROL: identical composition but w_spite forced 0 (knob attribution)
            hc = HarvestSpiteWorld(ws, w_spites=[0.0] * N, order_ns=[1.0] * N,
                                   comms=False, enforcement=0)
            oc = hc.outcome(T=T); hc.close()
            ctrl_burned.append(oc["total_burned"])
        levels.append(dict(k=k, p_spiteful=round(p, 4),
                           total_burned_mean=round(float(np.mean(burned)), 2),
                           total_burned_ci=[round(x, 2) for x in _boot_ci(burned)],
                           total_yield_mean=round(float(np.mean(oyield)), 1),
                           total_yield_ci=[round(x, 1) for x in _boot_ci(oyield)]))
        ctrl_levels.append(dict(k=k, p_spiteful=round(p, 4),
                                total_burned_mean=round(float(np.mean(ctrl_burned)), 2)))
    lo, hi = levels[0], levels[-1]
    return dict(
        deterministic_triple=det,
        population_sweep=levels, control_wspite0=ctrl_levels,
        burn_ci_separated=bool(hi["total_burned_ci"][0] > lo["total_burned_ci"][1]),
        control_all_zero=all(lv["total_burned_mean"] == 0 for lv in ctrl_levels),
        verdict_g_spite=bool(det["only_spiteful_burns"] and det["spiteful_self_costly"]
                             and hi["total_burned_ci"][0] > lo["total_burned_ci"][1]
                             and all(lv["total_burned_mean"] == 0 for lv in ctrl_levels)))


# ------------------------------------------------------------------ G-skill
def g_skill():
    """(a) DETERMINISTIC 2x2 (skill x environment) for a SELFISH agent: only
    strategic x enforced restrains (order_n x environment interaction); prosocial
    restrains from CARE regardless of skill/enforcement.
    (b) POWERED: fraction high-skill among selfish under enforcement -> restraint
    fraction with CIs; bare-commons control -> all grab."""
    norm0 = socially_optimal_h(R0, N)

    def one_selfish_harvest(order_n, enforcement, comms, w_sg=0.0):
        hw = HarvestSpiteWorld([w_sg] * N, w_spites=[0.0] * N,
                               order_ns=[float(order_n)] * N, comms=comms, enforcement=enforcement)
        hw.step()
        h = hw.decisions()[0]["chosen_harvest"]; hw.close()
        return h
    det = dict(
        norm=norm0, enforcement=ENF,
        selfish=dict(
            myopic_bare=one_selfish_harvest(0, 0, False),
            myopic_enforced=one_selfish_harvest(0, ENF, True),
            strategic_bare=one_selfish_harvest(1, 0, False),
            strategic_enforced=one_selfish_harvest(1, ENF, True)),
        prosocial=dict(
            order0_bare=one_selfish_harvest(0, 0, False, w_sg=1.0),
            order0_enforced=one_selfish_harvest(0, ENF, True, w_sg=1.0),
            order1_enforced=one_selfish_harvest(1, ENF, True, w_sg=1.0)))
    # interaction: strategic+enforced restrains; the other three grab
    s = det["selfish"]
    det["interaction_only_strategic_enforced_restrains"] = bool(
        s["strategic_enforced"] < 20 and s["myopic_bare"] == 20
        and s["myopic_enforced"] == 20 and s["strategic_bare"] == 20)
    det["cooperation_from_care_survives_zero_skill"] = bool(
        det["prosocial"]["order0_bare"] < 20 and det["prosocial"]["order0_enforced"] < 20)

    # (b) powered: fraction high-skill selfish under enforcement
    levels, ctrl = [], []
    for k in range(0, N + 1):
        p = k / N
        restr, restr_bare = [], []
        for r in range(RUNS):
            rng = np.random.default_rng(213500 + 100 * k + r)
            skill_mask = [1.0 if rng.random() < p else 0.0 for _ in range(N)]
            # enforced environment
            hw = HarvestSpiteWorld([0.0] * N, w_spites=[0.0] * N, order_ns=list(skill_mask),
                                   comms=True, enforcement=ENF)
            hw.step()
            decs = hw.decisions()
            norm = hw.decs and int(hw.s.node(hw.decs[0])["attrs"]["norm"])
            restr.append(float(np.mean([1.0 if d["chosen_harvest"] <= norm else 0.0 for d in decs])))
            hw.close()
            # bare control
            hb = HarvestSpiteWorld([0.0] * N, w_spites=[0.0] * N, order_ns=list(skill_mask),
                                   comms=False, enforcement=0)
            hb.step()
            db = hb.decisions()
            restr_bare.append(float(np.mean([1.0 if d["chosen_harvest"] <= norm else 0.0 for d in db])))
            hb.close()
        levels.append(dict(k=k, p_highskill=round(p, 4),
                           restraint_frac_mean=round(float(np.mean(restr)), 3),
                           restraint_frac_ci=[round(x, 3) for x in _boot_ci(restr)]))
        ctrl.append(dict(k=k, p_highskill=round(p, 4),
                         restraint_frac_mean=round(float(np.mean(restr_bare)), 3)))
    lo, hi = levels[0], levels[-1]
    return dict(
        deterministic_2x2=det, population_sweep_enforced=levels, control_bare=ctrl,
        restraint_ci_separated=bool(hi["restraint_frac_ci"][0] > lo["restraint_frac_ci"][1]),
        bare_control_no_restraint=all(lv["restraint_frac_mean"] == 0 for lv in ctrl),
        verdict_g_skill=bool(det["interaction_only_strategic_enforced_restrains"]
                             and hi["restraint_frac_ci"][0] > lo["restraint_frac_ci"][1]
                             and all(lv["restraint_frac_mean"] == 0 for lv in ctrl)))


# ------------------------------------------------------------------ G-2d
def g_2d():
    """The (emotion x skill) flip: a high-skill PSYCHOPATH cooperates under
    enforcement by CALCULATION -- zero its order_n and it flips to defection. A
    PROSOCIAL agent cooperates by CARE -- zeroing order_n does NOT flip it. Same
    behaviour, different knob; the glass box attributes each to the right knob."""
    def harvest(w_sg, order_n, w_spite=0.0):
        hw = HarvestSpiteWorld([w_sg] * N, w_spites=[w_spite] * N,
                               order_ns=[float(order_n)] * N, comms=True, enforcement=ENF)
        hw.step(); h = hw.decisions()[0]["chosen_harvest"]; hw.close()
        return h
    cells = dict(
        psychopath_highskill=harvest(0.0, 1),      # cooperates (calculation)
        psychopath_zeroskill=harvest(0.0, 0),      # DEFECTS (calculation removed)
        prosocial_highskill=harvest(1.0, 1),       # cooperates (care)
        prosocial_zeroskill=harvest(1.0, 0),       # STILL cooperates (care intact)
        spiteful_highskill=harvest(0.0, 1, w_spite=1.0))  # a spiteful cell for the grid
    return dict(
        cells=cells,
        psychopath_flips_on_zeroing_skill=bool(cells["psychopath_highskill"] < 20
                                               and cells["psychopath_zeroskill"] == 20),
        prosocial_does_not_flip=bool(cells["prosocial_highskill"] < 20
                                     and cells["prosocial_zeroskill"] < 20),
        verdict_g_2d=bool(cells["psychopath_highskill"] < 20 and cells["psychopath_zeroskill"] == 20
                          and cells["prosocial_highskill"] < 20 and cells["prosocial_zeroskill"] < 20))


# ------------------------------------------------------------------ G-graph-native
def g_graph_native():
    adapter = os.path.join(ROOT, "domains", "harvest_spite_world.py")
    src = open(adapter).read()
    patterns = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule(",
                "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in patterns}
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["add_node", "add_edge_unchecked", "set_attr", "run_rules",
                     "load_seed_manifest"]}
    return dict(
        adapter=os.path.relpath(adapter, ROOT),
        forbidden_hits=hits, clean=all(v == 0 for v in hits.values()),
        substrate_api_calls=api,
        knob_locations=dict(
            w_spite="graph data: HeldEmotionParams.w_spite, read by rule ss_decision_value "
                    "(seeds/spite_skill.json) -- spite_value = IfThenElse(w_spite>0, burn_harm, 0)",
            order_n="graph data: HeldEmotionParams.order_n, read by rule ss_decision_value "
                    "-- gated_cost = IfThenElse(order_n>0, individual_cost, 0)",
            harvest="graph rule ss_choose_harvest (Argmax over candidate decision_value)",
            burn="graph rule ss_choose_burn (burn_level of the SAME Argmax)",
            adapter_role="publish observations (future_yield, sanction, burn_harm), "
                         "run_rules, read chosen_harvest2/chosen_burn, apply to pool"))


# ------------------------------------------------------------------ G-discipline
def g_discipline():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    seed = json.load(open(os.path.join(ROOT, "seeds", "spite_skill.json")))
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)

    # neutral byte-identity: a spite-world agent at neutral knobs (w_spite=0,
    # order_n=1) reproduces the 212000 harvest decision in the BARE commons.
    ws = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    a = HarvestWorld(list(ws), comms=False)
    a.step(); a_h = [max(0, int(a.s.node(d)["attrs"]["chosen_harvest"])) for d in a.decs]; a.close()
    b = HarvestSpiteWorld(list(ws), comms=False, enforcement=0)
    b.step(); b_h = [r["chosen_harvest"] for r in b.decisions()]; b.close()

    return dict(
        canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5),
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        integer_native=(len(bad) == 0), non_integer_lits=bad[:10],
        rule_names=[r["name"] for r in seed["rules"]],
        neutral_matches_212000=(a_h == b_h), neutral_212000=a_h, neutral_spite=b_h)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("G-spite ..."); sp = g_spite()
    print("G-skill ..."); sk = g_skill()
    print("G-2d ..."); g2 = g_2d()
    gn = g_graph_native(); disc = g_discipline()
    result = dict(block=213000, n_agents=N, runs=RUNS, ticks=T, enforcement=ENF,
                  g_spite=sp, g_skill=sk, g_2d=g2,
                  g_graph_native=gn, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        g_spite_verdict=sp["verdict_g_spite"], spite_triple=sp["deterministic_triple"],
        g_skill_verdict=sk["verdict_g_skill"], skill_2x2=sk["deterministic_2x2"],
        g_2d_verdict=g2["verdict_g_2d"], g_2d_cells=g2["cells"],
        graph_native_clean=gn["clean"],
        canonical_untouched=disc["canonical_untouched"],
        integer_native=disc["integer_native"],
        neutral_matches_212000=disc["neutral_matches_212000"]), indent=1))


if __name__ == "__main__":
    main()
