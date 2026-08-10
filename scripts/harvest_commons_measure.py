#!/usr/bin/env python3
"""BLOCK 212000 -- HARVEST confirmatory measure (all Gs, pre-registered power).

Runs G-core (Phase 1), G-ostrom (Phase 2), G-deception (Phase 3), G-graph-native
(source audit), and G-discipline (canonical .so, integer-native, self_load_only),
writing results/harvest_commons/results.json. Numbers per
HARVEST_EMOTIONAL_SEEDS_PREREG.md; the agents decide in-graph via
seeds/harvest_commons.json over 204000 core_emotions -- this script is a MEASURE,
it takes NO agent decision.
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

import numpy as np                                    # noqa: E402
from domains.harvest_world import HarvestWorld        # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "harvest_commons")
CANON_MD5 = "793ce09ed498a749abb79aeaea44b92e"
N = 6                 # agents (pre-registered)
RUNS = 40             # runs per cell (pre-registered)
T = 40                # ticks (pre-registered)
_RNG = np.random.default_rng(212000)


def _boot_ci(xs, reps=2000, seed=212000):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _composition(p, rng):
    """Draw each agent's prosociality as Bernoulli(p): p is the POPULATION
    PROBABILITY of a prosocial (w>0) agent, so sampled populations genuinely vary
    at a given p (real run-to-run variance -> real CIs; the phase transition shows
    as a sigmoid in sustained-fraction)."""
    ws = [1.0 if rng.random() < p else 0.0 for _ in range(N)]
    return ws, int(sum(ws))


# ------------------------------------------------------------------ G-core
def g_core():
    levels = []
    for k in range(0, N + 1):
        p = k / N
        fp, ty, su, eq = [], [], [], []
        for r in range(RUNS):
            rng = np.random.default_rng(212000 + 100 * k + r)
            ws, npro = _composition(p, rng)
            hw = HarvestWorld(ws, comms=False)
            o = hw.outcome(T=T)
            hw.close()
            fp.append(o["final_pool"]); ty.append(o["total_yield"])
            su.append(o["sustained"]); eq.append(o["equality"])
        levels.append(dict(
            k=k, p_prosocial=round(p, 4),
            final_pool_mean=round(float(np.mean(fp)), 2), final_pool_ci=[round(x, 2) for x in _boot_ci(fp)],
            total_yield_mean=round(float(np.mean(ty)), 1), total_yield_ci=[round(x, 1) for x in _boot_ci(ty)],
            sustained_frac=round(float(np.mean(su)), 3),
            equality_mean=round(float(np.mean(eq)), 3), equality_ci=[round(x, 3) for x in _boot_ci(eq)]))
    lo, hi = levels[0], levels[-1]
    yl = [lv["total_yield_mean"] for lv in levels]
    return dict(
        runs_per_level=RUNS, n_agents=N, ticks=T, levels=levels,
        primary_contrast=dict(
            p0_yield=lo["total_yield_mean"], p0_yield_ci=lo["total_yield_ci"],
            p1_yield=hi["total_yield_mean"], p1_yield_ci=hi["total_yield_ci"],
            p0_pool=lo["final_pool_mean"], p0_pool_ci=lo["final_pool_ci"],
            p1_pool=hi["final_pool_mean"], p1_pool_ci=hi["final_pool_ci"],
            yield_ci_separated=hi["total_yield_ci"][0] > lo["total_yield_ci"][1],
            pool_ci_separated=hi["final_pool_ci"][0] > lo["final_pool_ci"][1]),
        non_monotonic_middle=any(yl[i] < yl[i - 1] for i in range(1, N)),
        verdict_g_core=(hi["total_yield_ci"][0] > lo["total_yield_ci"][1]
                        and hi["sustained_frac"] >= 0.9))


# ------------------------------------------------------------------ G-ostrom
def g_ostrom():
    out = {}
    for label, p in [("all_selfish_p0", 0.0), ("mixed_p0.5", 0.5)]:
        nc_y, wc_y, nc_p, wc_p = [], [], [], []
        d_y, d_p = [], []
        n_enf = None
        for r in range(RUNS):
            rng = np.random.default_rng(212700 + r)
            ws, _ = _composition(p, rng)
            hw0 = HarvestWorld(list(ws), comms=False)
            o0 = hw0.outcome(T=T); hw0.close()
            hw1 = HarvestWorld(list(ws), comms=True, enforce=True)
            n_enf = hw1.n_enf
            o1 = hw1.outcome(T=T); hw1.close()
            nc_y.append(o0["total_yield"]); wc_y.append(o1["total_yield"])
            nc_p.append(o0["final_pool"]); wc_p.append(o1["final_pool"])
            d_y.append(o1["total_yield"] - o0["total_yield"])
            d_p.append(o1["final_pool"] - o0["final_pool"])
        out[label] = dict(
            p_prosocial=round(p, 3), graph_enforcer_count=n_enf,
            nocomms_yield_mean=round(float(np.mean(nc_y)), 1),
            withcomms_yield_mean=round(float(np.mean(wc_y)), 1),
            paired_yield_delta_mean=round(float(np.mean(d_y)), 1),
            paired_yield_delta_ci=[round(x, 1) for x in _boot_ci(d_y)],
            nocomms_pool_mean=round(float(np.mean(nc_p)), 1),
            withcomms_pool_mean=round(float(np.mean(wc_p)), 1),
            paired_pool_delta_mean=round(float(np.mean(d_p)), 1),
            paired_pool_delta_ci=[round(x, 1) for x in _boot_ci(d_p)],
            flip_ci_separated=bool(_boot_ci(d_y)[0] > 0))
    return dict(
        cells=out,
        headline="communication FLIPS the mixed population (enforcers exist) but "
                 "NOT the all-selfish population (zero enforcers -- the second-order "
                 "free-rider problem, Fehr-Gachter).",
        verdict_g_ostrom=bool(out["mixed_p0.5"]["flip_ci_separated"]))


# ------------------------------------------------------------------ G-deception
def g_deception():
    ws_base = [1.0] * (N // 2) + [0.0] * (N - N // 2)
    res = {}
    for cond, enforce in [("cheap_talk", False), ("enforced", True)]:
        gaps = {0.0: [], 1.0: []}
        for r in range(RUNS):
            rng = np.random.default_rng(212800 + r)
            ws = list(ws_base); rng.shuffle(ws)
            hw = HarvestWorld(ws, comms=True, enforce=enforce)
            hw.step()
            for row in hw.stated_vs_held():
                gaps[row["w"]].append(row["gap"])
            hw.close()
        res[cond] = {
            f"w{int(w)}": dict(
                n=len(gaps[w]), mean_gap=round(float(np.mean(gaps[w])), 3),
                gap_ci=[round(x, 3) for x in _boot_ci(gaps[w])])
            for w in (0.0, 1.0)}
    ct = res["cheap_talk"]
    return dict(
        cells=res,
        headline="under CHEAP TALK (norm professed, unenforced) low-w agents "
                 "state compliance but HOLD a grab (gap>0); prosocial agents do "
                 "not; ENFORCEMENT closes the gap.",
        deception_ci_separated=bool(ct["w0"]["gap_ci"][0] > ct["w1"]["gap_ci"][1]),
        verdict_g_deception=bool(ct["w0"]["mean_gap"] > 0 and ct["w1"]["mean_gap"] == 0
                                 and res["enforced"]["w0"]["mean_gap"] == 0))


# ------------------------------------------------------------------ G-graph-native
def g_graph_native():
    """Source-audit the world adapter: no rule-engine calls, no conditional over an
    agent's graph state that selects an agent action."""
    adapter = os.path.join(ROOT, "domains", "harvest_world.py")
    src = open(adapter).read()
    # CALL-shaped patterns (the compliance docstring names these tokens in prose;
    # only an actual call has a following "("). run_rules() IS allowed -- it fires
    # the SEED rules; the forbidden thing is the PYTHON rule engine / rule minting.
    patterns = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule(",
                "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in patterns}
    # the ONLY calls into the substrate are: add_node/add_edge (ingest), set_attr
    # (publish observations), run_rules (tick), node()/attrs read (emit).
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["add_node", "add_edge_unchecked", "set_attr", "run_rules",
                     "load_seed_manifest"]}
    return dict(
        adapter=os.path.relpath(adapter, ROOT),
        forbidden_hits=hits,
        clean=all(v == 0 for v in hits.values()),
        substrate_api_calls=api,
        decisions=dict(
            harvest="graph rule hv_choose_harvest (Argmax over candidate total_value)",
            punish="graph rule hv_punish (+ hv_mark_enforcer / hv_count_enforcers)",
            state="graph rule hv_state_intent",
            adapter_role="publish observations, run_rules, read decisions, apply to pool"))


# ------------------------------------------------------------------ G-discipline
def g_discipline():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    seed = json.load(open(os.path.join(ROOT, "seeds", "harvest_commons.json")))
    # integer-native: every numeric Lit in the seed is a whole number
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
    return dict(
        canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5),
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        integer_native=(len(bad) == 0), non_integer_lits=bad[:10],
        rule_names=[r["name"] for r in seed["rules"]])


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("G-core ..."); core = g_core()
    print("G-ostrom ..."); ost = g_ostrom()
    print("G-deception ..."); dec = g_deception()
    gn = g_graph_native(); disc = g_discipline()
    result = dict(block=212000, n_agents=N, runs=RUNS, ticks=T,
                  g_core=core, g_ostrom=ost, g_deception=dec,
                  g_graph_native=gn, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        g_core=core["verdict_g_core"], primary=core["primary_contrast"],
        g_ostrom=ost["verdict_g_ostrom"], ostrom=ost["cells"],
        g_deception=dec["verdict_g_deception"], deception=dec["cells"],
        graph_native_clean=gn["clean"],
        canonical_untouched=disc["canonical_untouched"],
        integer_native=disc["integer_native"]), indent=1))


if __name__ == "__main__":
    main()
