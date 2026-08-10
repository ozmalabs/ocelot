#!/usr/bin/env python3
"""BLOCK 240000 -- MARSHMALLOW DISSOLUTION confirmatory measure (pre-registered).

Runs G-dissolution (HEADLINE factorial), G-rational-impatience (Kidd 2013),
G-confound-exhibited, G-glass-box, G-discipline; writes
results/marshmallow_delay/results.json. Predictions per MARSHMALLOW_DELAY_PREREG.md.
The wait/take choice is the graph rule mm_choose over 204000 core_emotions
(seeds/marshmallow_delay.json); this script is a MEASURE -- it takes NO agent
decision (it sets temperament/prior data, sweeps elapsed, reads chosen_action).
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

import numpy as np                                         # noqa: E402
from domains.marshmallow_world import (                    # noqa: E402
    MarshmallowWorld, predicted_wait_time,
    DELAYED_REWARD, IMMEDIATE_SMALL, COST_PER_TICK, PRIOR_SCALE, DELAY_CAP)

OUTDIR = os.path.join(ROOT, "results", "marshmallow_delay")
CANON_MD5 = "e75bc65021b6be0740abeee63662e21b"   # canonical .so on base ecdcd8dbad
BLOCK = 240000
N = 60                # agents per cohort (pre-registered)
_RNG = np.random.default_rng(BLOCK)


def _boot_ci(xs, reps=2000, seed=BLOCK):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _wait_times(temps, priors):
    mw = MarshmallowWorld(list(temps), list(priors))
    wt = mw.wait_times()
    mw.close()
    return wt


# ---------------------------------------------------------------- factorial grid
GRID_TEMPS = [2, 4, 8]
GRID_PRIORS = [60, 80, 100]


def factorial_grid():
    temps, priors = [], []
    for p in GRID_PRIORS:
        for w in GRID_TEMPS:
            temps.append(w); priors.append(p)
    wt = _wait_times(temps, priors)
    grid, k, all_match = {}, 0, True
    for p in GRID_PRIORS:
        row = {}
        for w in GRID_TEMPS:
            pred = predicted_wait_time(p, w)
            row[f"temp{w}"] = dict(measured=wt[k], predicted=pred)
            all_match = all_match and (wt[k] == pred)
            k += 1
        grid[f"prior{p}"] = row
    return dict(grid=grid, matches_prereg=all_match,
                temps=GRID_TEMPS, priors=GRID_PRIORS)


# ------------------------------------------------- G-dissolution (main effects + CIs)
def g_dissolution():
    # PURE TEMPERAMENT: hold the prior DISTRIBUTION fixed, vary only temperament.
    P_MID = np.array([58, 66, 74, 82, 90, 98])
    priors_pop = _RNG.choice(P_MID, size=N).tolist()
    low_temp = _RNG.choice([2, 3], size=N).tolist()     # patient (low time-cost weight)
    high_temp = _RNG.choice([7, 8], size=N).tolist()    # impatient
    wt_low_t = _wait_times(low_temp, priors_pop)
    wt_high_t = _wait_times(high_temp, priors_pop)
    ci_low_t, ci_high_t = _boot_ci(wt_low_t), _boot_ci(wt_high_t)
    temp_sep = ci_low_t[0] > ci_high_t[1]               # patient waits strictly longer
    # NULL CONTROL: hold temperament CONSTANT (both cohorts drawn from the SAME set)
    ctrl_a = _wait_times(_RNG.choice([2, 3], size=N).tolist(), priors_pop)
    ctrl_b = _wait_times(_RNG.choice([2, 3], size=N).tolist(), priors_pop)
    ci_a, ci_b = _boot_ci(ctrl_a), _boot_ci(ctrl_b)
    temp_ctrl_overlap = not (ci_a[0] > ci_b[1] or ci_b[0] > ci_a[1])

    # PURE PRIOR: hold the temperament DISTRIBUTION fixed, vary only the prior.
    T_MID = np.array([2, 3, 4, 6, 8])
    temps_pop = _RNG.choice(T_MID, size=N).tolist()
    low_prior = _RNG.choice([58, 60, 62], size=N).tolist()
    high_prior = _RNG.choice([96, 98, 100], size=N).tolist()
    wt_low_p = _wait_times(temps_pop, low_prior)
    wt_high_p = _wait_times(temps_pop, high_prior)
    ci_low_p, ci_high_p = _boot_ci(wt_low_p), _boot_ci(wt_high_p)
    prior_sep = ci_high_p[0] > ci_low_p[1]              # high prior waits strictly longer
    # NULL CONTROL: hold the prior CONSTANT
    ctrl_c = _wait_times(temps_pop, _RNG.choice([58, 60, 62], size=N).tolist())
    ctrl_d = _wait_times(temps_pop, _RNG.choice([58, 60, 62], size=N).tolist())
    ci_c, ci_d = _boot_ci(ctrl_c), _boot_ci(ctrl_d)
    prior_ctrl_overlap = not (ci_c[0] > ci_d[1] or ci_d[0] > ci_c[1])

    return dict(
        pure_temperament=dict(
            low_weight_mean=round(float(np.mean(wt_low_t)), 3), low_weight_ci=[round(x, 3) for x in ci_low_t],
            high_weight_mean=round(float(np.mean(wt_high_t)), 3), high_weight_ci=[round(x, 3) for x in ci_high_t],
            ci_separated=bool(temp_sep),
            note="prior distribution held FIXED; only temperament varies -> pure temperament effect"),
        pure_temperament_null_control=dict(
            ci_a=[round(x, 3) for x in ci_a], ci_b=[round(x, 3) for x in ci_b],
            overlap_as_expected=bool(temp_ctrl_overlap),
            note="temperament held CONSTANT -> CIs must OVERLAP (no effect from the machinery)"),
        pure_prior=dict(
            low_prior_mean=round(float(np.mean(wt_low_p)), 3), low_prior_ci=[round(x, 3) for x in ci_low_p],
            high_prior_mean=round(float(np.mean(wt_high_p)), 3), high_prior_ci=[round(x, 3) for x in ci_high_p],
            ci_separated=bool(prior_sep),
            note="temperament distribution held FIXED; only prior varies -> pure prior effect"),
        pure_prior_null_control=dict(
            ci_c=[round(x, 3) for x in ci_c], ci_d=[round(x, 3) for x in ci_d],
            overlap_as_expected=bool(prior_ctrl_overlap),
            note="prior held CONSTANT -> CIs must OVERLAP"),
        verdict_g_dissolution=bool(temp_sep and prior_sep and temp_ctrl_overlap and prior_ctrl_overlap))


# ----------------------------------------------- G-rational-impatience (Kidd 2013)
def g_rational_impatience():
    # SAME patient temperament (w=2); the ONLY difference is the reliability-prior,
    # calibrated to an UNRELIABLE (P=60) vs RELIABLE (P=100) environment.
    unreliable = _wait_times([2] * N, _RNG.choice([58, 60, 62], size=N).tolist())
    reliable = _wait_times([2] * N, _RNG.choice([96, 98, 100], size=N).tolist())
    ci_u, ci_r = _boot_ci(unreliable), _boot_ci(reliable)
    # deterministic anchor (exact single-agent points from the grid)
    anchor = dict(patient_low_prior=predicted_wait_time(60, 2),
                  patient_high_prior=predicted_wait_time(100, 2))
    sep = ci_r[0] > ci_u[1]
    return dict(
        temperament="patient (w=2) held FIXED in both arms",
        unreliable_prior_mean=round(float(np.mean(unreliable)), 3), unreliable_ci=[round(x, 3) for x in ci_u],
        reliable_prior_mean=round(float(np.mean(reliable)), 3), reliable_ci=[round(x, 3) for x in ci_r],
        deterministic_anchor=anchor,
        ci_separated_reliable_gt_unreliable=bool(sep),
        headline="a PATIENT temperament waits SHORT under a low reliability-prior -- "
                 "impatience as the RATIONAL output of a correct belief, attributed to "
                 "the PRIOR not a temperament deficit; the high-prior control waits long.",
        verdict_g_rational_impatience=bool(sep))


# ------------------------------------------------- G-confound-exhibited (the teeth)
def g_confound():
    # (A) SAME temperament, DIFFERENT prior -> DIFFERENT wait (naive: diff self-control)
    same_temp = _wait_times([4, 4, 4], [60, 80, 100])
    a_pred = [predicted_wait_time(p, 4) for p in (60, 80, 100)]
    a_strictly_increasing = same_temp[0] < same_temp[1] < same_temp[2]
    # (B) DIFFERENT temperament, COMPENSATING prior -> SAME wait (naive: identical)
    diff_temp_temps, diff_temp_priors = [2, 4, 8], [60, 68, 85]
    comp = _wait_times(diff_temp_temps, diff_temp_priors)
    b_pred = [predicted_wait_time(p, w) for w, p in zip(diff_temp_temps, diff_temp_priors)]
    b_all_equal = (comp[0] == comp[1] == comp[2])
    return dict(
        same_temperament_different_prior=dict(
            temperament=4, priors=[60, 80, 100], wait_times=same_temp, predicted=a_pred,
            strictly_increasing=bool(a_strictly_increasing),
            reading="identical temperament, yet a naive marshmallow score reads these as "
                    "3 DIFFERENT 'self-control' levels -- the wait-time is NOT identifiable "
                    "for temperament"),
        different_temperament_compensating_prior=dict(
            temperaments=diff_temp_temps, priors=diff_temp_priors, wait_times=comp, predicted=b_pred,
            all_equal=bool(b_all_equal),
            reading="temperament differs 4x, yet all three wait EXACTLY the same -- a naive "
                    "marshmallow score reads them as IDENTICAL 'self-control'"),
        verdict_g_confound=bool(a_strictly_increasing and b_all_equal
                                and same_temp == a_pred and comp == b_pred))


# --------------------------------------------------------------- G-glass-box
def g_glass_box():
    mw = MarshmallowWorld([2, 8], [60, 100])
    # read the decisive state straight from the graph at a mid tick
    gb0 = mw.glass_box(0, t=3)
    gb1 = mw.glass_box(1, t=3)
    mw.close()
    # source audit of the adapter: no Python rule engine, no agent-decision if/else
    adapter = os.path.join(ROOT, "domains", "marshmallow_world.py")
    src = open(adapter).read()
    forbidden = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule(",
                 "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in forbidden}
    # no reward/punishment shaping tokens in the decision path
    shaping = {t: len(re.findall(r"\b" + re.escape(t) + r"\b", src))
               for t in ["reward_signal", "punish", "reinforce", "backprop", "gradient"]}
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["add_node", "add_edge_unchecked", "set_attr", "run_rules", "load_seed_manifest"]}
    return dict(
        agent0_readout=gb0, agent1_readout=gb1,
        readable_from_graph=all(k in gb0 for k in
            ("temperament", "reliability_prior", "elapsed", "chosen_action",
             "wait_total_value", "take_total_value")),
        forbidden_hits=hits, source_audit_clean=all(v == 0 for v in hits.values()),
        shaping_tokens=shaping, no_shaping=all(v == 0 for v in shaping.values()),
        substrate_api_calls=api,
        decisions=dict(
            wait_take="graph rule mm_choose (Argmax over candidate total_value)",
            valuation="graph rules mm_appraise_wait / mm_appraise_take over core_emotions em_happiness/em_total_value",
            adapter_role="set temperament (Drive.weight) + reliability_prior data, sweep elapsed, read chosen_action"),
        verdict_g_glass_box=bool(all(v == 0 for v in hits.values())
                                 and all(v == 0 for v in shaping.values())))


# --------------------------------------------------------------- G-discipline
def g_discipline():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    seed = json.load(open(os.path.join(ROOT, "seeds", "marshmallow_delay.json")))
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
    # self_load_only -> absent from load_all_seeds
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    return dict(
        canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5),
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        integer_native=(len(bad) == 0), non_integer_lits=bad[:10],
        absent_from_load_all=("marshmallow_delay" not in seeds),
        world_constants=dict(delayed_reward=DELAYED_REWARD, immediate_small=IMMEDIATE_SMALL,
                             cost_per_tick=COST_PER_TICK, prior_scale=PRIOR_SCALE, delay_cap=DELAY_CAP),
        rule_names=[r["name"] for r in seed["rules"]],
        verdict_g_discipline=bool(md5 == CANON_MD5 and len(bad) == 0
                                  and seed.get("self_load_only") is True
                                  and "marshmallow_delay" not in seeds))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("factorial grid ..."); grid = factorial_grid()
    print("G-dissolution ..."); diss = g_dissolution()
    print("G-rational-impatience ..."); rat = g_rational_impatience()
    print("G-confound ..."); conf = g_confound()
    print("G-glass-box ..."); gb = g_glass_box()
    print("G-discipline ..."); disc = g_discipline()
    result = dict(block=BLOCK, n_per_cohort=N, rng_seed=BLOCK,
                  factorial_grid=grid, g_dissolution=diss,
                  g_rational_impatience=rat, g_confound=conf,
                  g_glass_box=gb, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        grid_matches_prereg=grid["matches_prereg"],
        g_dissolution=diss["verdict_g_dissolution"],
        pure_temperament_ci=[diss["pure_temperament"]["high_weight_ci"],
                             diss["pure_temperament"]["low_weight_ci"]],
        pure_prior_ci=[diss["pure_prior"]["low_prior_ci"], diss["pure_prior"]["high_prior_ci"]],
        g_rational_impatience=rat["verdict_g_rational_impatience"],
        g_confound=conf["verdict_g_confound"],
        confound_same_temp=conf["same_temperament_different_prior"]["wait_times"],
        confound_diff_temp=conf["different_temperament_compensating_prior"]["wait_times"],
        g_glass_box=gb["verdict_g_glass_box"],
        g_discipline=disc["verdict_g_discipline"]), indent=1))


if __name__ == "__main__":
    main()
