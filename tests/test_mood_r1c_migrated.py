"""MOOD R1c — the DECISIVE, POWERED confirmation of R1b's near-miss (seed block
238000). Gate on the PRE-REGISTERED measure (MOOD_R1C_PREREG.md). R1c is POWER,
NOT TUNING: the ONLY change from R1b is the sample size K (200 -> 750); the world
(domains/mood_r1b_world.py), the two seeds (seeds/mood_r1.json +
seeds/mood_r1_task.json), the learning rates, the gain, the accept threshold, the
RPE choice, N=200, and the metric are all reused VERBATIM. The estimator is
byte-identical (episode/boot_ci/run_arm reused from scripts.mood_r1b_measure);
only the sample size and the in-block (238000-238999) seed integers differ.

HONEST OUTCOME THIS GATE PINS: the pre-registered HEADLINE **PASSES** at the
powered N — the absolute-net-benefit bar is CONFIRMED:

  * REGIME world: mean WITH-WITHOUT gap = +0.564, boot95 [+0.266, +0.855]
        (t95 [+0.272, +0.856]) — the CI now CLEARS 0. Mood-momentum is net
        beneficial where returns persist. (R1b's K=200 point +0.622 fell a
        whisker short at [-0.050, +1.277]; K=750 shrank the SE 1.936x and the
        lower bound moved from -0.05 to +0.27, as the pre-registration predicted
        ~[+0.28, +0.97].)
  * i.i.d. control (matched marginal): mean gap = -2.029, boot95 [-2.391,
        -1.660] — mood HURTS where returns carry no persistence (CI BELOW 0). A
        VALID failable control (NOT CI-above-0).
  * headline_pass = (regime_ci_above_0 AND not iid_ci_above_0) = True.

This gate PINS the PASS so it can never silently regress to a null without a
fresh, honest measurement — and asserts the mechanism + discipline that held:

  * G-momentum — the readable Mood.momentum IS the leaky signed-RPE EMA (rises
        in a good run, falls in a bad run); a shuffled-stream control kills the
        tracking. Unchanged mechanism, re-checked at lr=0.1.
  * G-glass-box — Mood + gain are readable graph state, every update is a named
        rule, source audit clean (no Python rule engine).
  * G-discipline — NO new Rust Term (only sd_blend's atoms); default-OFF
        byte-identical; no mood nodes on the default path; engine provenance own.
  * experiment validity + the failable control — the two worlds share an EXACTLY
        matched marginal (same multiset), regime is strongly autocorrelated and
        i.i.d. is not, and the i.i.d. gap is NOT CI-above-0.

PRE-COMMIT TO STOP honored: the powered config was run ONCE; no sweep, no
re-tune, no second K. This is the FINAL verdict on the net-benefit bar.
"""
import importlib

import pytest

M = importlib.import_module("scripts.mood_r1c_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


# ---------------------------------- the powered PRE-REGISTERED headline (PASS)
def test_headline_regime_ci_clears_zero(res):
    """The powered headline PASSES: the persistent-regime WITH-WITHOUT gap is
    CI-above-0 at K=750. Pin the PASS so it cannot silently regress to a null
    without a fresh, honest measurement."""
    ga = res["g_adaptive"]
    assert ga["k"] == 750, ga["k"]                       # powered N, not R1b's 200
    assert ga["regime_ci_above_0"], ga["boot_ci_gap_regime"]
    assert ga["boot_ci_gap_regime"][0] > 0.0, ga["boot_ci_gap_regime"]
    assert ga["mean_gap_regime"] > 0.0, ga["mean_gap_regime"]
    assert ga["headline_pass"], (ga["boot_ci_gap_regime"], ga["boot_ci_gap_iid"])


def test_iid_is_a_valid_failable_control_not_ci_above_0(res):
    """The control CAN fail: if mood helped in i.i.d. too it would be noise.
    Here it HURTS (CI below 0) — a valid, correctly-behaving control that makes
    the regime PASS meaningful."""
    ga = res["g_adaptive"]
    assert not ga["iid_ci_above_0"], ga["boot_ci_gap_iid"]
    assert ga["mean_gap_iid"] < 0.0, ga["mean_gap_iid"]


def test_regime_ci_separated_above_iid(res):
    """The persistent world's benefit is CI-separated ABOVE the i.i.d. world's:
    mood's effect is materially more positive where returns persist."""
    ga = res["g_adaptive"]
    assert ga["mean_gap_regime"] > 0.0 > ga["mean_gap_iid"]
    assert ga["boot_ci_gap_regime"][0] > ga["boot_ci_gap_iid"][1], (
        ga["boot_ci_gap_regime"], ga["boot_ci_gap_iid"])


# ------------------------------------------------ G-momentum (mechanism holds)
def test_G_momentum_tracks_the_injected_trend(res):
    gm = res["g_momentum"]
    assert gm["good_positive"], gm            # good run -> momentum > 0
    assert gm["bad_negative"], gm             # bad run  -> momentum < 0
    assert gm["mean_good_run_momentum"] > gm["mean_bad_run_momentum"]


def test_G_momentum_shuffle_control_kills_tracking(res):
    gm = res["g_momentum"]
    assert gm["trended_ci_above_0"], gm["boot_ci_sep_trended"]      # trended sep CI>0
    assert gm["shuffle_ci_contains_0"], gm["boot_ci_sep_shuffled"]  # shuffle sep contains 0
    assert gm["tracking_pass"]


# ---------------------------------------------------------------- G-glass-box
def test_G_glass_box_readable_named_rules_clean_source(res):
    ggb = res["g_glass_box"]
    assert ggb["mood_readable"]
    assert ggb["has_task_rules"] and ggb["has_mood_rules"]
    assert ggb["mood_rules_enabled_guarded"]
    assert ggb["adapter_runs_no_python_rule_engine"]
    assert ggb["glass_box_pass"]


# ---------------------------------------------------------------- G-discipline
def test_G_discipline_no_new_rust_term(res):
    gd = res["g_discipline"]
    assert gd["no_new_term"], gd["new_terms"]   # only sd_blend's atoms; NO new seed either


def test_G_discipline_default_off_byte_identical(res):
    gd = res["g_discipline"]
    assert gd["default_off_identical"]
    assert gd["no_mood_nodes_on_default"]


def test_G_discipline_engine_provenance_own(res):
    assert res["g_discipline"]["source_match"] == "own"


# ------------------------------------------- experiment validity + the control
def test_worlds_share_exactly_matched_marginals(res):
    ga = res["g_adaptive"]
    assert ga["marginal_match_max_mean_diff"] < 1e-9, ga["marginal_match_max_mean_diff"]
    assert ga["marginal_match_max_var_diff"] < 1e-9, ga["marginal_match_max_var_diff"]


def test_persistence_is_the_only_difference(res):
    ga = res["g_adaptive"]
    assert ga["autocorr_regime_mean"] > 0.5, ga["autocorr_regime_mean"]
    assert abs(ga["autocorr_iid_mean"]) < 0.1, ga["autocorr_iid_mean"]


# --------------------------------------- diagnostic presence (not a gate)
def test_diagnostic_recorded(res):
    d = res["diagnostic"]
    assert "prediction_mse" in d
    assert "mean_mse_improvement_regime" in d["prediction_mse"]
