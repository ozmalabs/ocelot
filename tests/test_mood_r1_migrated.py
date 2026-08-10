"""MOOD R1 — the autocorrelation adaptive gate (seed block 236000). Gate on the
PRE-REGISTERED measure (MOOD_R1_PREREG.md). Mood = a slow leaky EMA of the signed
valence-RPE (Eldar/Rutledge/Dolan/Niv 2016); R1's single falsifiable headline is
that mood-momentum earns cumulative reward ONLY when returns are AUTOCORRELATED.

HONEST OUTCOME THIS GATE PINS: at the PINNED config (lr=0.3, gain=1.0) the
pre-registered HEADLINE was **FALSIFIED** — mood did NOT help; it slightly HURT,
and it hurt roughly EQUALLY in the autocorrelated and i.i.d. worlds (the
mood-as-noise signature the i.i.d. control was built to detect). The
pre-registered honest-risk #4 BIT: the fast delta-rule value layer already
tracks the phi=0.9 signal well enough that the additive momentum bias only
overshoots. This gate therefore PINS the null (auto gap NOT CI-above-0) so it can
never silently flip to a claimed positive without a fresh measurement — while
asserting the mechanism and discipline that DID hold:

  * G-momentum — the readable Mood.momentum IS the leaky signed-RPE EMA: it
        tracks the sign/trend of the injected stream (rises in a good run, falls
        in a bad run); a shuffled-stream control kills the tracking.
  * G-glass-box — Mood + gain are readable graph state, every update is a named
        rule, source audit clean (no Python rule engine).
  * G-discipline — NO new Rust Term (only sd_blend's atoms); default-OFF
        byte-identical; no mood nodes on the default path; engine provenance own.
  * experiment validity + the failable control — the two worlds share an
        EXACTLY matched marginal (same multiset), auto is strongly autocorrelated
        and iid is not, and the i.i.d. gap is NOT CI-above-0 (a valid control).

The POST-HOC exploratory lr x gain grid (NOT a pre-registered gate) is recorded
in results but not asserted here as R1's result; it localises where the adaptive
gate IS recoverable (a lead for a future pre-registered rung).
"""
import importlib

import pytest

M = importlib.import_module("scripts.mood_r1_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


# ------------------------------------------------ G-momentum (mechanism holds)
def test_G_momentum_tracks_the_injected_trend(res):
    gm = res["g_momentum"]
    assert gm["good_positive"], gm            # good run -> momentum > 0
    assert gm["bad_negative"], gm             # bad run  -> momentum < 0
    assert gm["mean_good_run_momentum"] > gm["mean_bad_run_momentum"]


def test_G_momentum_shuffle_control_kills_tracking(res):
    gm = res["g_momentum"]
    assert gm["trended_ci_above_0"], gm["boot_ci_sep_trended"]     # trended sep CI>0
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
    assert gd["no_new_term"], gd["new_terms"]   # only sd_blend's atoms


def test_G_discipline_default_off_byte_identical(res):
    gd = res["g_discipline"]
    assert gd["default_off_identical"]
    assert gd["no_mood_nodes_on_default"]


def test_G_discipline_engine_provenance_own(res):
    assert res["g_discipline"]["source_match"] in ("own", "shared")


# ------------------------------------- experiment validity + failable control
def test_worlds_share_exactly_matched_marginals(res):
    ga = res["g_adaptive"]
    assert ga["marginal_match_max_mean_diff"] < 1e-9, ga["marginal_match_max_mean_diff"]
    assert ga["marginal_match_max_var_diff"] < 1e-9, ga["marginal_match_max_var_diff"]


def test_autocorrelation_is_the_only_difference(res):
    ga = res["g_adaptive"]
    # the AR(1) world is strongly autocorrelated; the shuffle destroys it.
    assert ga["autocorr_auto_mean"] > 0.5, ga["autocorr_auto_mean"]
    assert abs(ga["autocorr_iid_mean"]) < 0.1, ga["autocorr_iid_mean"]


def test_iid_is_a_valid_failable_control_not_ci_above_0(res):
    # the control CAN fail: if mood helped in i.i.d. too it would be noise/optimism.
    ga = res["g_adaptive"]
    assert not ga["iid_ci_above_0"], ga["boot_ci_gap_iid"]


# ------------------------------------ the recorded PRE-REGISTERED headline NULL
def test_headline_null_is_pinned_not_silently_flipped(res):
    """The pre-registered headline (auto gap CI-above-0) was FALSIFIED at the
    pinned config. Pin the null so it cannot silently become a claimed positive
    without a fresh, honest measurement. If a future change makes mood genuinely
    help at the pinned config, THIS test must be updated deliberately (with new
    CIs), never left to drift."""
    ga = res["g_adaptive"]
    assert not ga["auto_ci_above_0"], ga["boot_ci_gap_auto"]
    assert not ga["headline_pass"]
    # and it hurt roughly equally in both worlds (mood-as-noise, not adaptive):
    assert ga["mean_gap_auto"] < 0 and ga["mean_gap_iid"] < 0, ga


# --------------------------------------- exploratory presence (not a gate)
def test_exploratory_diagnostics_recorded(res):
    ex = res["exploratory"]
    assert "prediction_mse" in ex and "lr_gain_grid" in ex
    assert ex["lr_gain_grid"]["cells"]   # the grid ran
