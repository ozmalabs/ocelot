#!/usr/bin/env python3
"""MOOD R1c — the DECISIVE, POWERED confirmation of R1b's near-miss (block
238000). MECHANICAL measure.

R1b (block 237000) got a NEAR-MISS NULL on the strict absolute-net-benefit bar:
the persistent-regime WITH-WITHOUT cumulative-reward gap was +0.622, boot95
[-0.050, +1.277] -- POSITIVE and adaptive in DIRECTION, but the lower CI bound
sat a WHISKER (0.05) below 0. R1b's measured residual named WHY: the per-episode
gap has high variance (the benefit is concentrated in ~10 short post-switch
transients per episode), so the bar was UNDER-POWERED, not the effect moved.

R1c is POWER, NOT TUNING. **The ONLY change from R1b is the sample size K
(200 -> 750).** The world (``domains/mood_r1b_world.py``), the two seeds
(``seeds/mood_r1.json`` + ``seeds/mood_r1_task.json``), the learning rates, the
gain, the accept threshold, the RPE choice, N=200, and the metric are all reused
VERBATIM. The estimator is byte-identical: this script imports the R1b world
adapter (``regime_stream``/``iid_permute``/``run_arm``/``run_arm_trace``) and the
R1b measurement helpers (``episode``/``boot_ci``/``t_ci``/``g_glass_box``/
``g_discipline``/``_momentum_over_blocks``/``_run_metrics``) from
``scripts.mood_r1b_measure`` and re-runs the SAME functions at K = 750 with an
in-block (238000-238999) seed layout.

Seed layout (all strictly inside the claimed block 238000-238999; none touch the
sibling's 239000 block), forced by keeping the per-episode independent-seed
construction of R1b VERBATIM (one default_rng(seed) per episode):

    G-adaptive episodes   238000 .. 238749   (750, the headline)
    G-momentum streams    238750 .. 238849   (100, mechanism sanity, unchanged)
    diagnostic MSE        238850 .. 238949   (100, LABELED NON-GATE, unchanged)
    bootstrap resamples   238950 .. 238955   (6)

Gates: G-adaptive-regime-powered (HEADLINE; the i.i.d. world is the failable
control), G-momentum (momentum IS the leaky signed-RPE EMA; a shuffled stream
kills the tracking), G-glass-box, G-discipline (default-OFF byte-identity, no
Rust, provenance own).

IMPORT-INERT: nothing runs at import; ``main()`` is the only entry.

SINGLE PINNED CONFIG, RUN ONCE. There is NO lr/gain/world sweep here; the only
diagnostic is the value-prediction MSE, reported as a LABELED NON-GATE readout.
Whatever comes out is the FINAL verdict on the absolute-net-benefit bar (no
sweep, no re-tune, no R1d) -- see MOOD_R1C_PREREG.md §2 (pre-commit to stop).
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

# The world adapter, reused VERBATIM (no change).
from domains.mood_r1b_world import (               # noqa: E402
    B_BOOT, GAIN, LR_LAGGING, MOMENTUM_LR, MU, N_TRIALS, P_SWITCH, SIGMA,
    iid_permute, lag1_autocorr, regime_stream)
# The R1b measurement helpers, reused VERBATIM (the estimator is byte-identical;
# only the sample size and the in-block seed integers change here).
from scripts.mood_r1b_measure import (             # noqa: E402
    _momentum_over_blocks, _run_metrics, boot_ci, episode, g_discipline,
    g_glass_box, t_ci)

# ----------------------------------------------------------------------------
# THE ONE CHANGE from R1b: K 200 -> 750 (variance reduction to power the bar).
# ----------------------------------------------------------------------------
K_EPISODES = 750                 # R1b was 200; 3.75x -> SE shrinks by sqrt(3.75)=1.936x

# In-block seed layout (MOOD_R1C_PREREG §1).
EP_BASE = 238000                 # episodes 238000 .. 238749
MOM_BASE = 238750                # G-momentum streams 238750 .. 238849
DIAG_BASE = 238850               # diagnostic MSE 238850 .. 238949
BOOT_BASE = 238950               # bootstrap seeds 238950 .. 238955

RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "mood_r1c")


# --------------------------------------------------- G-adaptive (headline)
def g_adaptive():
    """The powered headline. episode() (reused verbatim) generates a
    persistent-regime stream + its i.i.d. permutation (matched multiset ->
    identical marginal mean/variance, persistence destroyed) and runs WITH and
    WITHOUT on the SAME stream (paired). Only K and the seed base differ from
    R1b."""
    eps = [episode(EP_BASE + i) for i in range(K_EPISODES)]
    gap_regime = [e["gap_regime"] for e in eps]
    gap_iid = [e["gap_iid"] for e in eps]
    co_regime = [e["co_regime"] for e in eps]
    co_iid = [e["co_iid"] for e in eps]

    br_lo, br_hi = boot_ci(gap_regime, seed=BOOT_BASE + 0)
    bi_lo, bi_hi = boot_ci(gap_iid, seed=BOOT_BASE + 1)
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


# ---------------------------------------- G-momentum (mechanism sanity)
def g_momentum(k2=100, m=30, mu=3.0, noise=1.0):
    """Momentum IS the leaky signed-RPE EMA (unchanged mechanism, re-checked at
    lr=0.1): a GOOD run (rewards +mu) drives it positive, a BAD run (-mu)
    negative; the SHUFFLED stream (same values permuted -> no run) KILLS the
    good/bad separation. Identical to R1b's g_momentum; only the in-block seed
    base differs (MOM_BASE)."""
    good_bounds = [(0, m)]
    bad_bounds = [(m, 2 * m)]
    sep_trend, sep_shuf = [], []
    good_mom, bad_mom = [], []
    for i in range(k2):
        rng = np.random.default_rng(MOM_BASE + i)
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
    bt_lo, bt_hi = boot_ci(sep_trend, seed=BOOT_BASE + 2)
    bs_lo, bs_hi = boot_ci(sep_shuf, seed=BOOT_BASE + 3)
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


# ============================================================================
# LABELED NON-GATE DIAGNOSTIC — value-prediction MSE. NOT a pre-registered gate.
# ============================================================================
def diag_prediction_mse(k=100):
    """NON-GATE diagnostic (identical to R1b; only DIAG_BASE differs): does
    momentum improve value-prediction accuracy (MSE of v vs r = mean raw_rpe^2)
    selectively in the persistent-regime world?"""
    imp_reg, imp_iid = [], []
    for i in range(k):
        rng = np.random.default_rng(DIAG_BASE + i)
        regime, _s = regime_stream(rng)
        iid = iid_permute(rng, regime)
        _, mse_wr = _run_metrics(regime, True)
        _, mse_or = _run_metrics(regime, False)
        _, mse_wi = _run_metrics(iid, True)
        _, mse_oi = _run_metrics(iid, False)
        imp_reg.append(mse_or - mse_wr)   # >0 => mood REDUCES prediction error
        imp_iid.append(mse_oi - mse_wi)
    br = boot_ci(imp_reg, seed=BOOT_BASE + 4)
    bi = boot_ci(imp_iid, seed=BOOT_BASE + 5)
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
    labels = ["persistent regime\n(dwell~%d, K=%d)" % (int(round(1 / P_SWITCH)), ga["k"]),
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
    ax.set_title("G-adaptive-regime POWERED (K=%d): headline %s"
                 % (ga["k"], "PASS" if ga["headline_pass"] else "NULL"))
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
    ggb = g_glass_box()          # reused verbatim from mood_r1b_measure
    gd = g_discipline()          # reused verbatim from mood_r1b_measure

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

    res = dict(seed_base=EP_BASE, k_episodes=K_EPISODES,
               g_adaptive=ga, g_momentum=gm,
               g_glass_box=ggb, g_discipline=gd, criteria=criteria,
               diagnostic=dict(prediction_mse=diag_mse))
    with open(os.path.join(RESULTS, "mood_r1c.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    try:
        render(res, os.path.join(FRAMES, "mood_r1c.png"))
    except Exception as e:
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))
    ga = r["g_adaptive"]; gm = r["g_momentum"]
    print("\n-- G-adaptive-regime POWERED (headline), K=%d --" % ga["k"])
    print("  regime gap mean=%+.4f  boot95=[%+.4f, %+.4f]  t95=[%+.4f, %+.4f]  rel=%+.1f%%"
          % (ga["mean_gap_regime"], *ga["boot_ci_gap_regime"],
             *ga["t_ci_gap_regime"], 100 * ga["rel_gap_regime"]))
    print("  i.i.d. gap mean=%+.4f  boot95=[%+.4f, %+.4f]"
          % (ga["mean_gap_iid"], *ga["boot_ci_gap_iid"]))
    print("  autocorr regime=%.3f  iid=%.3f  marginal-match(mean/var diff)=%.2e/%.2e"
          % (ga["autocorr_regime_mean"], ga["autocorr_iid_mean"],
             ga["marginal_match_max_mean_diff"], ga["marginal_match_max_var_diff"]))
    print("  regime_ci_above_0:", ga["regime_ci_above_0"],
          " iid_ci_above_0:", ga["iid_ci_above_0"])
    print("  HEADLINE PASS:", ga["headline_pass"])
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
