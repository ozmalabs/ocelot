#!/usr/bin/env python3
"""MOOD R1b — the AUTOCORRELATION ADAPTIVE GATE on a FAIR persistent-regime
world (block 237000). MECHANICAL measure.

Runs the pre-registered R1b (MOOD_R1B_PREREG.md): mood-momentum earns cumulative
reward ONLY when environmental returns carry PERSISTENCE (a hidden regime that
dwells); in an i.i.d. world of matched marginal mean/variance (the same regime
stream permuted) it must NOT help. The mechanism — value learning, the
accept/decline choice, the momentum EMA, the appraisal feedback — is entirely
graph RULES in the REUSED R1 seeds (``seeds/mood_r1_task.json`` +
``seeds/mood_r1.json``); this script only generates reward streams, ticks the
world adapter (``domains/mood_r1b_world.py``, at the pinned lagging lr=0.1), and
reads/aggregates. No agent decision, no Rust, no Term, no new seed.

Gates: G-adaptive-regime (HEADLINE; the i.i.d. world is the failable control),
G-momentum (momentum IS the leaky signed-RPE EMA; a shuffled stream kills the
tracking), G-glass-box (readable node + named rules + clean source audit),
G-discipline (default-OFF byte-identity, no Rust, provenance own).

IMPORT-INERT: nothing runs at import; ``main()`` is the only entry.

SINGLE PINNED CONFIG, RUN ONCE. There is NO lr/gain sweep here (that would be
p-hacking a rung informed by a peek); the only diagnostic is the value-prediction
MSE, reported as a LABELED NON-GATE mechanism readout.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.mood_r1b_world import (               # noqa: E402
    B_BOOT, GAIN, K_EPISODES, LR_LAGGING, MOMENTUM_LR, MU, N_TRIALS, P_SWITCH,
    SIGMA, iid_permute, lag1_autocorr, regime_stream, run_arm, run_arm_trace)

SEED_BASE = 237000
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "mood_r1b")


# -------------------------------------------------------------- one episode
def episode(seed):
    """One episode: a persistent-regime stream + its i.i.d. permutation (matched
    multiset -> identical marginal mean/variance, persistence destroyed). WITH
    and WITHOUT run on the SAME stream (paired)."""
    rng = np.random.default_rng(seed)
    regime, _states = regime_stream(rng)
    iid = iid_permute(rng, regime)
    cw_reg = run_arm(regime, True)
    co_reg = run_arm(regime, False)
    cw_iid = run_arm(iid, True)
    co_iid = run_arm(iid, False)
    return dict(
        gap_regime=cw_reg - co_reg, gap_iid=cw_iid - co_iid,
        cw_regime=cw_reg, co_regime=co_reg, cw_iid=cw_iid, co_iid=co_iid,
        ac_regime=lag1_autocorr(regime), ac_iid=lag1_autocorr(iid),
        mean_regime=float(regime.mean()), var_regime=float(regime.var()),
        mean_iid=float(iid.mean()), var_iid=float(iid.var()))


# ------------------------------------------------------------------- stats
def boot_ci(vals, b=B_BOOT, seed=SEED_BASE + 900, alpha=0.05):
    vals = np.asarray(vals, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(b, len(vals)))
    means = vals[idx].mean(axis=1)
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return lo, hi


def t_ci(vals, alpha=0.05):
    vals = np.asarray(vals, float)
    n = len(vals)
    m = float(vals.mean())
    se = float(vals.std(ddof=1) / math.sqrt(n))
    z = 1.959963985  # 95% normal approx (n large)
    return m - z * se, m + z * se


# --------------------------------------------------- G-adaptive (headline)
def g_adaptive():
    eps = [episode(SEED_BASE + 100 + i) for i in range(K_EPISODES)]
    gap_regime = [e["gap_regime"] for e in eps]
    gap_iid = [e["gap_iid"] for e in eps]
    co_regime = [e["co_regime"] for e in eps]
    co_iid = [e["co_iid"] for e in eps]

    br_lo, br_hi = boot_ci(gap_regime)
    bi_lo, bi_hi = boot_ci(gap_iid)
    tr_lo, tr_hi = t_ci(gap_regime)
    ti_lo, ti_hi = t_ci(gap_iid)

    mean_gap_regime = float(np.mean(gap_regime))
    mean_gap_iid = float(np.mean(gap_iid))
    mean_co_regime = float(np.mean(co_regime))
    rel_gap_regime = (mean_gap_regime / abs(mean_co_regime)
                      if mean_co_regime else float("nan"))

    regime_ci_above0 = br_lo > 0.0
    iid_ci_contains0 = (bi_lo <= 0.0 <= bi_hi) or (bi_hi < 0.0)
    iid_ci_above0 = bi_lo > 0.0

    match_mean = max(abs(e["mean_regime"] - e["mean_iid"]) for e in eps)
    match_var = max(abs(e["var_regime"] - e["var_iid"]) for e in eps)
    ac_regime_mean = float(np.mean([e["ac_regime"] for e in eps]))
    ac_iid_mean = float(np.mean([e["ac_iid"] for e in eps]))

    return dict(
        k=K_EPISODES, n_trials=N_TRIALS, mu=MU, sigma=SIGMA, p_switch=P_SWITCH,
        lr=LR_LAGGING, momentum_lr=MOMENTUM_LR, gain=GAIN,
        mean_gap_regime=mean_gap_regime, mean_gap_iid=mean_gap_iid,
        mean_cum_without_regime=mean_co_regime,
        mean_cum_without_iid=float(np.mean(co_iid)),
        rel_gap_regime=rel_gap_regime,
        boot_ci_gap_regime=[br_lo, br_hi], boot_ci_gap_iid=[bi_lo, bi_hi],
        t_ci_gap_regime=[tr_lo, tr_hi], t_ci_gap_iid=[ti_lo, ti_hi],
        regime_ci_above_0=regime_ci_above0,
        iid_ci_contains_0=iid_ci_contains0, iid_ci_above_0=iid_ci_above0,
        # HEADLINE verdict: mood helps in the regime world (CI>0) AND does NOT
        # help in i.i.d. (CI not >0)
        headline_pass=(regime_ci_above0 and not iid_ci_above0),
        marginal_match_max_mean_diff=match_mean,
        marginal_match_max_var_diff=match_var,
        autocorr_regime_mean=ac_regime_mean, autocorr_iid_mean=ac_iid_mean,
        gap_regime=gap_regime, gap_iid=gap_iid)


# ---------------------------------------- G-momentum-is-signed-RPE-EMA
def _momentum_over_blocks(stream, block_bounds):
    """Run WITH-mood on a stream (at the pinned lagging lr), return mean
    momentum over each [lo,hi) block."""
    out, _ma, _ta = run_arm_trace(stream, True)
    mom = np.array([t["momentum"] for t in out["trace"]])
    return [float(mom[lo:hi].mean()) for (lo, hi) in block_bounds]


def g_momentum(k2=100, m=30, mu=3.0, noise=1.0):
    """Momentum IS the leaky signed-RPE EMA (unchanged mechanism, re-checked at
    lr=0.1): a GOOD run (rewards +mu) drives it positive, a BAD run (rewards
    -mu) negative. The SHUFFLED stream (same values permuted -> no run) KILLS
    the good/bad separation."""
    good_bounds = [(0, m)]
    bad_bounds = [(m, 2 * m)]
    sep_trend, sep_shuf = [], []
    good_mom, bad_mom = [], []
    for i in range(k2):
        rng = np.random.default_rng(SEED_BASE + 300 + i)
        good = rng.normal(mu, noise, m)
        bad = rng.normal(-mu, noise, m)
        stream = np.concatenate([good, bad])
        gm = _momentum_over_blocks(stream, good_bounds)[0]
        bm = _momentum_over_blocks(stream, bad_bounds)[0]
        good_mom.append(gm); bad_mom.append(bm)
        sep_trend.append(gm - bm)                 # good - bad, should be >0
        shuf = rng.permutation(stream)            # same multiset, run destroyed
        sgm = _momentum_over_blocks(shuf, good_bounds)[0]
        sbm = _momentum_over_blocks(shuf, bad_bounds)[0]
        sep_shuf.append(sgm - sbm)                # should be ~0
    bt_lo, bt_hi = boot_ci(sep_trend, seed=SEED_BASE + 901)
    bs_lo, bs_hi = boot_ci(sep_shuf, seed=SEED_BASE + 902)
    return dict(
        k2=k2, m=m, mu=mu,
        mean_good_run_momentum=float(np.mean(good_mom)),
        mean_bad_run_momentum=float(np.mean(bad_mom)),
        mean_sep_trended=float(np.mean(sep_trend)),
        mean_sep_shuffled=float(np.mean(sep_shuf)),
        boot_ci_sep_trended=[bt_lo, bt_hi],
        boot_ci_sep_shuffled=[bs_lo, bs_hi],
        good_positive=float(np.mean(good_mom)) > 0,
        bad_negative=float(np.mean(bad_mom)) < 0,
        trended_ci_above_0=bt_lo > 0.0,
        shuffle_ci_contains_0=(bs_lo <= 0.0 <= bs_hi),
        tracking_pass=(bt_lo > 0.0 and (bs_lo <= 0.0 <= bs_hi)
                       and float(np.mean(good_mom)) > 0 > float(np.mean(bad_mom))))


# ------------------------------------------------------------- G-glass-box
def g_glass_box():
    """Mood is a readable node; every update is a named rule; the R1b adapter
    runs no Python rule engine and takes no if/else decision over a mood value."""
    out, ma, ta = run_arm_trace([2.0, 2.0, 2.0], True)
    readable = all(k in ma for k in ("momentum", "gain", "enabled")) and "bias" in ta

    task = json.load(open(os.path.join(ROOT, "seeds", "mood_r1_task.json")))
    mood = json.load(open(os.path.join(ROOT, "seeds", "mood_r1.json")))
    task_rules = {r["name"] for r in task["rules"]}
    mood_rules = {r["name"] for r in mood["rules"]}
    has_task = {"mt_decide", "mt_accrue", "mt_rpe", "mt_learn"} <= task_rules
    has_mood = {"mood_momentum", "mood_bias"} <= mood_rules
    mood_guarded = all("enabled" in json.dumps(r.get("where", {})) for r in mood["rules"])

    src = open(os.path.abspath(__file__)).read()
    adapter = open(os.path.join(ROOT, "domains", "mood_r1b_world.py")).read()
    r1_adapter = open(os.path.join(ROOT, "domains", "mood_r1_world.py")).read()
    forbidden = ["gr" + ".run(", "graph_" + "rewrite", "make_" + "rule",
                 "gr." + "_match(", "gr." + "_apply("]
    clean = not any(t in src or t in adapter or t in r1_adapter for t in forbidden)
    return dict(
        mood_readable=readable, has_task_rules=has_task, has_mood_rules=has_mood,
        mood_rules_enabled_guarded=mood_guarded,
        adapter_runs_no_python_rule_engine=clean,
        glass_box_pass=(readable and has_task and has_mood and mood_guarded and clean))


# ------------------------------------------------------------- G-discipline
# atoms sd_blend (staleness_decay) uses; the momentum EMA must stay inside them.
SDBLEND_ATOMS = {"Plus", "Times", "Minus", "Div", "Attr", "Lit", "IfThenElse",
                 "Ashr", "IDiv", "Max", "Eq", "Gt", "Gte", "Lt", "And", "Abs",
                 "Var"}


def _term_types(term, acc):
    if isinstance(term, dict):
        if "type" in term:
            acc.add(term["type"])
        for k in ("a", "b", "arg", "cond", "then", "other", "node", "source",
                  "value", "member", "container"):
            if k in term:
                _term_types(term[k], acc)
        for x in term.get("items", []):
            _term_types(x, acc)
    return acc


def g_discipline():
    from substrate.seed_loader import manifest_for
    # (1) no new Term: every Term type in the two REUSED seeds is already used by
    #     sd_blend's atoms
    used = set()
    for sid in ("mood_r1_task", "mood_r1"):
        seed = json.load(open(os.path.join(ROOT, "seeds", sid + ".json")))
        for r in seed["rules"]:
            for eff in r.get("effects", []):
                if isinstance(eff, list) and len(eff) >= 4 and isinstance(eff[3], dict):
                    _term_types(eff[3].get("__term__", {}), used)
            _term_types(r.get("where", {}), used)
    new_terms = sorted(used - SDBLEND_ATOMS)
    no_new_term = (len(new_terms) == 0)

    # (2) default-OFF byte-identity: with NO hub/nodes, loading the two REUSED
    #     seeds is byte-identical to not loading them.
    def run(load):
        from domains.photon_eye import GraphEye
        eye = GraphEye(n_az=2, n_el=2, adapt_rate=0.15,
                       context={"retina_2d": True, "synchronous": True,
                                "worker_capacity": 1}).build()
        inner = eye.substrate._inner
        if load:
            inner.load_seed_manifest(manifest_for("mood_r1_task"), eye._agent)
            inner.load_seed_manifest(manifest_for("mood_r1"), eye._agent)
        rng = np.random.default_rng(SEED_BASE)
        for _t in range(1, 6):
            pk = [{"col": c, "row": r, "wavelength_nm": 498.0,
                   "count": int(rng.poisson(40))}
                  for r in range(2) for c in range(2)]
            eye.submit_photons_2d(pk)
            inner.run_cognitive_tasks(1)
            inner.run_rules()
        cells = []
        for cid in eye._cells:
            a = eye.substrate.node(cid)["attrs"]
            cells.append({k: (round(v, 9) if isinstance(v, float) else v)
                          for k, v in sorted(a.items())})
        counts = {"node_count": eye.substrate._inner.node_count(),
                  "MoodTask": len(eye.substrate.nodes("MoodTask")),
                  "Mood": len(eye.substrate.nodes("Mood"))}
        fp = json.dumps({"counts": counts, "cells": cells}, sort_keys=True)
        eye.stop()
        return fp, counts
    fp_off, c_off = run(False)
    fp_on, c_on = run(True)
    default_off_identical = (fp_off == fp_on)
    no_nodes = (c_on.get("MoodTask", 0) == 0 and c_on.get("Mood", 0) == 0)

    # (3) engine provenance
    try:
        from domains.engine_provenance import engine_provenance
        source_match = engine_provenance().get("source_match", "unknown")
    except Exception as e:  # pragma: no cover
        source_match = f"error:{e}"

    return dict(
        no_new_term=no_new_term, new_terms=new_terms, terms_used=sorted(used),
        default_off_identical=default_off_identical, no_mood_nodes_on_default=no_nodes,
        source_match=source_match,
        discipline_pass=(no_new_term and default_off_identical and no_nodes))


# ============================================================================
# LABELED NON-GATE DIAGNOSTIC — the value-prediction MSE mechanism readout.
# NOT a pre-registered gate; recorded for interpretation only.
# ============================================================================
def _run_metrics(stream, mood_enabled, warmup=20):
    out, _ma, _ta = run_arm_trace(stream, mood_enabled)
    tr = out["trace"]
    cum = tr[-1]["cum_reward"]
    rpes = np.array([t["raw_rpe"] for t in tr[warmup:]])
    return cum, float(np.mean(rpes ** 2))


def diag_prediction_mse(k=100):
    """NON-GATE diagnostic: does momentum improve VALUE-PREDICTION accuracy (MSE
    of v vs r = mean raw_rpe^2) selectively in the persistent-regime world? Tests
    the paper's core mechanism directly, independent of the choice metric."""
    imp_reg, imp_iid = [], []
    for i in range(k):
        rng = np.random.default_rng(SEED_BASE + 500 + i)
        regime, _s = regime_stream(rng)
        iid = iid_permute(rng, regime)
        _, mse_wr = _run_metrics(regime, True)
        _, mse_or = _run_metrics(regime, False)
        _, mse_wi = _run_metrics(iid, True)
        _, mse_oi = _run_metrics(iid, False)
        imp_reg.append(mse_or - mse_wr)   # >0 => mood REDUCES prediction error
        imp_iid.append(mse_oi - mse_wi)
    br = boot_ci(imp_reg, seed=SEED_BASE + 903)
    bi = boot_ci(imp_iid, seed=SEED_BASE + 904)
    return dict(
        note="LABELED NON-GATE diagnostic, not a pre-registered gate",
        mean_mse_improvement_regime=float(np.mean(imp_reg)),
        mean_mse_improvement_iid=float(np.mean(imp_iid)),
        boot_ci_improvement_regime=list(br), boot_ci_improvement_iid=list(bi),
        regime_improves_ci_above_0=br[0] > 0, iid_improves_ci_above_0=bi[0] > 0)


# --------------------------------------------------------------------- render
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    ga = res["g_adaptive"]
    ax = axes[0]
    labels = ["persistent regime\n(dwell~%d)" % int(round(1 / P_SWITCH)),
              "i.i.d.\n(matched marginal)"]
    means = [ga["mean_gap_regime"], ga["mean_gap_iid"]]
    cis = [ga["boot_ci_gap_regime"], ga["boot_ci_gap_iid"]]
    err = [[means[i] - cis[i][0] for i in range(2)],
           [cis[i][1] - means[i] for i in range(2)]]
    colors = ["#1b7837", "#8073ac"]
    ax.bar(range(2), means, color=colors, yerr=err, capsize=6)
    ax.axhline(0, color="#999", ls=":")
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("WITH - WITHOUT cumulative reward\n(per-episode gap, 95% boot CI)")
    ax.set_title("G-adaptive-regime: momentum pays IFF returns\npersist (i.i.d. = failable control)")
    ax = axes[1]
    gm = res["g_momentum"]
    labels2 = ["trended\n(good then bad run)", "shuffled\n(same values)"]
    means2 = [gm["mean_sep_trended"], gm["mean_sep_shuffled"]]
    cis2 = [gm["boot_ci_sep_trended"], gm["boot_ci_sep_shuffled"]]
    err2 = [[means2[i] - cis2[i][0] for i in range(2)],
            [cis2[i][1] - means2[i] for i in range(2)]]
    ax.bar(range(2), means2, color=["#1b7837", "#b2182b"], yerr=err2, capsize=6)
    ax.axhline(0, color="#999", ls=":")
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels2, fontsize=8)
    ax.set_ylabel("momentum(good run) - momentum(bad run)")
    ax.set_title("G-momentum: Mood.momentum tracks the trend;\nshuffle kills the tracking")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(FRAMES, exist_ok=True)
    ga = g_adaptive()
    gm = g_momentum()
    ggb = g_glass_box()
    gd = g_discipline()

    criteria = dict(
        g_adaptive_regime_ci_above_0=ga["regime_ci_above_0"],
        g_adaptive_iid_not_ci_above_0=(not ga["iid_ci_above_0"]),
        g_adaptive_iid_ci_contains_0=ga["iid_ci_contains_0"],
        g_adaptive_headline=ga["headline_pass"],
        g_adaptive_marginals_matched=(ga["marginal_match_max_mean_diff"] < 1e-9
                                      and ga["marginal_match_max_var_diff"] < 1e-9),
        g_momentum_good_positive=gm["good_positive"],
        g_momentum_bad_negative=gm["bad_negative"],
        g_momentum_trended_ci_above_0=gm["trended_ci_above_0"],
        g_momentum_shuffle_ci_contains_0=gm["shuffle_ci_contains_0"],
        g_momentum_tracking=gm["tracking_pass"],
        g_glass_box=ggb["glass_box_pass"],
        g_discipline_no_new_term=gd["no_new_term"],
        g_discipline_default_off_identical=gd["default_off_identical"],
        g_discipline_no_mood_nodes_on_default=gd["no_mood_nodes_on_default"],
    )
    diag_mse = diag_prediction_mse()

    res = dict(seed_base=SEED_BASE, g_adaptive=ga, g_momentum=gm,
               g_glass_box=ggb, g_discipline=gd, criteria=criteria,
               diagnostic=dict(prediction_mse=diag_mse))
    with open(os.path.join(RESULTS, "mood_r1b.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    try:
        render(res, os.path.join(FRAMES, "mood_r1b.png"))
    except Exception as e:
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))
    ga = r["g_adaptive"]; gm = r["g_momentum"]
    print("\n-- G-adaptive-regime (headline) --")
    print("  regime gap mean=%+.4f  boot95=[%+.4f, %+.4f]  rel=%+.1f%%"
          % (ga["mean_gap_regime"], *ga["boot_ci_gap_regime"], 100 * ga["rel_gap_regime"]))
    print("  i.i.d. gap mean=%+.4f  boot95=[%+.4f, %+.4f]"
          % (ga["mean_gap_iid"], *ga["boot_ci_gap_iid"]))
    print("  autocorr regime=%.3f  iid=%.3f  marginal-match(mean/var diff)=%.2e/%.2e"
          % (ga["autocorr_regime_mean"], ga["autocorr_iid_mean"],
             ga["marginal_match_max_mean_diff"], ga["marginal_match_max_var_diff"]))
    print("  headline PASS:", ga["headline_pass"])
    print("-- G-momentum --")
    print("  good-run mom=%+.3f  bad-run mom=%+.3f  sep trended=%+.3f boot95=%s  shuffled=%+.3f boot95=%s"
          % (gm["mean_good_run_momentum"], gm["mean_bad_run_momentum"],
             gm["mean_sep_trended"], [round(x, 3) for x in gm["boot_ci_sep_trended"]],
             gm["mean_sep_shuffled"], [round(x, 3) for x in gm["boot_ci_sep_shuffled"]]))
    print("provenance source_match:", r["g_discipline"]["source_match"])
    dm = r["diagnostic"]["prediction_mse"]
    print("\n-- LABELED NON-GATE diagnostic --")
    print("  value-prediction MSE improvement (without-with, >0=mood helps): "
          "regime=%+.4f CI%s  iid=%+.4f CI%s"
          % (dm["mean_mse_improvement_regime"], [round(x, 4) for x in dm["boot_ci_improvement_regime"]],
             dm["mean_mse_improvement_iid"], [round(x, 4) for x in dm["boot_ci_improvement_iid"]]))
    print("\nALL PRE-REGISTERED CRITERIA PASS:", all(r["criteria"].values()))
