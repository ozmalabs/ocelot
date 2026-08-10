#!/usr/bin/env python3
"""BLOCK 234000 -- GLASS-BOX SOCIETY R1 confirmatory measure (pre-registered).

"Language is a coordination technology." Runs the five gates of
GLASS_BOX_R1_PREREG.md and writes results/glassbox_r1/results.json. The agents
decide in-graph via seeds/glassbox_r1_social.json over the LANDED core_emotions
value economy -- this script is a MEASURE, it takes NO agent decision (it only
boots worlds, calls their run(), reads their graph read-offs, and computes CIs).
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
from worlds.glassbox_r1_world import GlassBoxR1World        # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "glassbox_r1")
# CLEAN-ENGINE RE-RUN: this worktree builds its OWN engine (provenance 'own').
# The engine actually loaded (this tree's own build) is fingerprinted at runtime.
# The canonical SHARED engine in the main checkout must stay UNCHANGED; its md5
# was recorded at prereg and is re-confirmed here (that file is never written).
CANON_SHARED_MD5 = "55707cd76a6097c92127b3226109305c"  # main checkout, must not change
CANON_SHARED_SO = os.path.join(
    "/home/matt/ozma/internal/research/experiments/gamma-substrate",
    "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
N = 8
T = 30
RUNS = 60


def _boot_ci(xs, reps=2000, seed=234900):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


# ------------------------------------------------ G-language-coordinates (HEADLINE)
def g_language():
    """All-honest population; comms ON vs OFF, PAIRED by run seed (same walk).
    Metric = mean welfare per agent-tick. Gap = ON - OFF."""
    on, off, gap = [], [], []
    for r in range(RUNS):
        seed = 234000 + r
        won = GlassBoxR1World([1.0] * N, comms=True, seed=seed)
        oon = won.run(T=T); won.close()
        woff = GlassBoxR1World([1.0] * N, comms=False, seed=seed)
        ooff = woff.run(T=T); woff.close()
        on.append(oon["welfare_per_agent_tick"])
        off.append(ooff["welfare_per_agent_tick"])
        gap.append(oon["welfare_per_agent_tick"] - ooff["welfare_per_agent_tick"])
    gci = _boot_ci(gap)
    return dict(
        runs=RUNS, population="all_honest", metric="welfare_per_agent_tick",
        on_mean=round(float(np.mean(on)), 4), on_ci=[round(x, 4) for x in _boot_ci(on)],
        off_mean=round(float(np.mean(off)), 4), off_ci=[round(x, 4) for x in _boot_ci(off)],
        gap_mean=round(float(np.mean(gap)), 4), gap_ci=[round(x, 4) for x in gci],
        gap_ci_excludes_zero=bool(gci[0] > 0),
        verdict_g_language=bool(gci[0] > 0))


# ------------------------------------------------ G-seed-determines
def g_seed():
    """Honest-population ON vs psychopath-population ON, PAIRED by seed. Metric =
    welfare per agent-tick. Verdict: honest CI-separated ABOVE psychopath."""
    hon, psy = [], []
    for r in range(RUNS):
        seed = 234100 + r
        wh = GlassBoxR1World([1.0] * N, comms=True, seed=seed)
        oh = wh.run(T=T); wh.close()
        wp = GlassBoxR1World([0.0] * N, comms=True, seed=seed)
        op = wp.run(T=T); wp.close()
        hon.append(oh["welfare_per_agent_tick"])
        psy.append(op["welfare_per_agent_tick"])
    hci, pci = _boot_ci(hon), _boot_ci(psy)
    return dict(
        runs=RUNS, metric="welfare_per_agent_tick",
        honest_on_mean=round(float(np.mean(hon)), 4), honest_on_ci=[round(x, 4) for x in hci],
        psycho_on_mean=round(float(np.mean(psy)), 4), psycho_on_ci=[round(x, 4) for x in pci],
        ci_separated=bool(hci[0] > pci[1]),
        verdict_g_seed=bool(hci[0] > pci[1]))


# ------------------------------------------------ G-deception-is-real
def g_deception():
    """Mixed population (alternating honest/psychopath), comms ON. Promise-keeping
    rate BY SEED, pooled over runs. Verdict: honest rate == 1.0, psychopath == 0.0,
    CI-separated. Also counts readable stated!=held Promise-node gaps by seed."""
    honest_rates, psy_rates = [], []
    honest_gaps, psy_gaps = 0, 0
    honest_promises, psy_promises = 0, 0
    mix = [1.0, 0.0] * (N // 2)
    for r in range(RUNS):
        seed = 234300 + r
        rng = np.random.default_rng(seed)
        ws = list(mix); rng.shuffle(ws)
        w = GlassBoxR1World(ws, comms=True, seed=seed)
        w.run(T=T)
        for row in w.keeping_by_seed():
            if row["rate"] is None:
                continue
            (honest_rates if row["w"] == 1.0 else psy_rates).append(row["rate"])
        for g in w.deception_gaps():
            if g["w"] == 1.0:
                honest_promises += 1; honest_gaps += (1 if g["gap"] != 0 else 0)
            else:
                psy_promises += 1; psy_gaps += (1 if g["gap"] != 0 else 0)
        w.close()
    hci, pci = _boot_ci(honest_rates), _boot_ci(psy_rates)
    return dict(
        runs=RUNS, population="alternating_honest_psychopath",
        honest_keeping_rate_mean=round(float(np.mean(honest_rates)), 4),
        honest_keeping_rate_ci=[round(x, 4) for x in hci],
        psycho_keeping_rate_mean=round(float(np.mean(psy_rates)), 4),
        psycho_keeping_rate_ci=[round(x, 4) for x in pci],
        ci_separated=bool(hci[0] > pci[1]),
        honest_promises=honest_promises, honest_stated_neq_held=honest_gaps,
        psycho_promises=psy_promises, psycho_stated_neq_held=psy_gaps,
        verdict_g_deception=bool(
            float(np.mean(honest_rates)) == 1.0 and float(np.mean(psy_rates)) == 0.0
            and psy_gaps == psy_promises and honest_gaps == 0))


# ------------------------------------------------ wiring controls (run first)
def wiring():
    """POS: under comms, an honest agent at an encounter holds chosen_give==1.
    NEG: with no comms, encountered agents hold chosen_give==0. Proves the give
    rule CAN fire in both directions (the OFF null is a real outcome)."""
    pos = GlassBoxR1World([1.0] * N, comms=True, seed=234000)
    pos.run(T=T)
    pos_gives = [row["chosen_a"] for row in pos.trade_log] + [row["chosen_b"] for row in pos.trade_log]
    pos.close()
    neg = GlassBoxR1World([1.0] * N, comms=False, seed=234000)
    neg.run(T=T)
    neg_gives = [row["chosen_a"] for row in neg.trade_log] + [row["chosen_b"] for row in neg.trade_log]
    neg.close()
    return dict(
        pos_encounter_gives=int(sum(pos_gives)), pos_encounters=len(pos_gives),
        neg_encounter_gives=int(sum(neg_gives)), neg_encounters=len(neg_gives),
        pos_ok=bool(len(pos_gives) > 0 and sum(pos_gives) == len(pos_gives)),
        neg_ok=bool(sum(neg_gives) == 0))


# ------------------------------------------------ G-glass-box (source audit + reconstruct)
def g_glass_box():
    adapter = os.path.join(ROOT, "worlds", "glassbox_r1_world.py")
    src = open(adapter).read()
    patterns = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule(",
                "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in patterns}
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["add_node", "add_edge_unchecked", "set_attr", "run_rules",
                     "load_seed_manifest"]}
    # reconstruct one episode from graph data alone
    w = GlassBoxR1World([1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0], comms=True, seed=234300)
    w.run(T=T)
    promise_nodes = [w.s.node(pn)["attrs"] for pn in w.promise_nodes]
    reconstruct = dict(
        n_promise_nodes=len(promise_nodes),
        sample_promise=promise_nodes[0] if promise_nodes else None,
        n_trades=len(w.trade_log), sample_trade=w.trade_log[0] if w.trade_log else None,
        deception_gaps_readable=len([g for g in w.deception_gaps() if g["gap"] != 0]))
    w.close()
    return dict(
        adapter=os.path.relpath(adapter, ROOT),
        forbidden_hits=hits, clean=all(v == 0 for v in hits.values()),
        substrate_api_calls=api,
        decisions=dict(
            give_keep="graph rule gb_choose_give (Argmax over candidates by total_value)",
            promise="graph rule gb_state_promise (cheap commissive under comms_on)",
            value="core_emotions em_happiness/em_fulfilment_value/em_total_value (w_supergraph-gated)",
            adapter_role="move agents, form encounters, publish payoff mechanics, run_rules, read chosen_give/stated_give, realise transfers"),
        reconstruct=reconstruct)


# ------------------------------------------------ G-discipline
def g_discipline():
    # This tree's OWN engine (the one actually loaded / measured on).
    own_so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    # The canonical SHARED engine in the main checkout must stay UNCHANGED.
    shared_md5 = (hashlib.md5(open(CANON_SHARED_SO, "rb").read()).hexdigest()
                  if os.path.exists(CANON_SHARED_SO) else None)
    # Provenance verdict of the actually-loaded engine (own / shared / DIVERGED).
    try:
        import substrate_rs  # noqa: F401  (loaded via conftest/sys.path)
        from domains.engine_provenance import engine_provenance
        _p = engine_provenance()
        prov = _p["source_match"]
        prov_line = "%s @ %s (%s)" % (_p["short"], _p["native_path"], _p["source_match"])
    except Exception as e:  # pragma: no cover - reporter only
        prov = f"unavailable: {e}"
        prov_line = prov
    seed = json.load(open(os.path.join(ROOT, "seeds", "glassbox_r1_social.json")))
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
        own_engine_so_md5=own_md5,
        shared_canonical_so_md5=shared_md5,
        shared_canonical_unchanged=(shared_md5 == CANON_SHARED_MD5),
        provenance_verdict=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        integer_native=(len(bad) == 0), non_integer_lits=bad[:10],
        rule_names=[r["name"] for r in seed["rules"]])


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("wiring ..."); wir = wiring()
    assert wir["pos_ok"], f"POS wiring failed: {wir}"
    assert wir["neg_ok"], f"NEG wiring failed: {wir}"
    print("G-language (headline) ..."); lang = g_language()
    print("G-seed-determines ..."); seed = g_seed()
    print("G-deception ..."); dec = g_deception()
    print("G-glass-box ..."); gb = g_glass_box()
    print("G-discipline ..."); disc = g_discipline()
    result = dict(block=234000, n_agents=N, ticks=T, runs=RUNS,
                  wiring=wir, g_language=lang, g_seed=seed, g_deception=dec,
                  g_glass_box=gb, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        wiring_pos=wir["pos_ok"], wiring_neg=wir["neg_ok"],
        g_language=lang["verdict_g_language"], headline_gap=lang["gap_mean"],
        headline_gap_ci=lang["gap_ci"], on=lang["on_mean"], off=lang["off_mean"],
        g_seed=seed["verdict_g_seed"], honest_on=seed["honest_on_mean"], psycho_on=seed["psycho_on_mean"],
        g_deception=dec["verdict_g_deception"],
        honest_keep=dec["honest_keeping_rate_mean"], psycho_keep=dec["psycho_keeping_rate_mean"],
        glass_box_clean=gb["clean"],
        shared_canonical_unchanged=disc["shared_canonical_unchanged"],
        provenance_verdict=disc["provenance_verdict"],
        own_engine_md5=disc["own_engine_so_md5"],
        integer_native=disc["integer_native"]),
        indent=1))


if __name__ == "__main__":
    main()
