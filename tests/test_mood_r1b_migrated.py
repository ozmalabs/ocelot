"""MOOD R1b — the autocorrelation adaptive gate re-tested on a FAIR
persistent-regime world (seed block 237000). Gate on the PRE-REGISTERED measure
(MOOD_R1B_PREREG.md). Mood = a slow leaky EMA of the signed valence-RPE
(Eldar/Rutledge/Dolan/Niv 2016); R1b re-tests R1's null on a world with genuine
persistence (a dwelling hidden regime) WITHOUT AR(1)'s mean-reversion, and a
fast layer re-pinned SLOWER (lr=0.1) so it genuinely lags — the two principled
changes the R1 diagnosis named. REUSES seeds/mood_r1.json + seeds/mood_r1_task.json
verbatim (no new mood mechanism, no new seed, NO Rust).

HONEST OUTCOME THIS GATE PINS: the pre-registered HEADLINE (regime gap
CI-above-0 AND i.i.d. gap NOT CI-above-0) is a **NULL — but a QUALITATIVELY
DIFFERENT, much more favourable null than R1's**:

  * REGIME world: mean WITH-WITHOUT gap = +0.62, boot95 [-0.05, +1.28] — the
        adaptive DIRECTION is now present (mood HELPS; ~97.5% of the CI is above
        0), but the lower CI bound sits a WHISKER below 0, so it FAILS the strict
        CI-above-0 bar. The pre-registered headline does NOT pass.
  * i.i.d. control (matched marginal): mean gap = -1.90, boot95 [-2.66, -1.14]
        — mood HURTS where returns carry no persistence (CI BELOW 0). A VALID
        failable control (NOT CI-above-0).
  * The FAIR world FLIPPED THE SIGN of the effect vs R1: R1 had BOTH worlds
        negative (mood-as-noise); R1b has regime POSITIVE and i.i.d. NEGATIVE,
        the two CI-separated from EACH OTHER — the adaptive signature in
        direction, just short of CI-separation from 0.

This gate PINS the null (regime NOT CI-above-0) so it can never silently flip to
a claimed positive without a fresh, honest measurement — while asserting the
adaptive DIRECTION that DID emerge (regime gap > 0 > i.i.d. gap), the valid
control, and the mechanism + discipline that held:

  * G-momentum — the readable Mood.momentum IS the leaky signed-RPE EMA (rises
        in a good run, falls in a bad run); a shuffled-stream control kills the
        tracking. Unchanged mechanism, re-checked at lr=0.1.
  * G-glass-box — Mood + gain are readable graph state, every update is a named
        rule, source audit clean (no Python rule engine).
  * G-discipline — NO new Rust Term (only sd_blend's atoms); default-OFF
        byte-identical; no mood nodes on the default path; engine provenance own.
  * experiment validity + the failable control — the two worlds share an
        EXACTLY matched marginal (same multiset), regime is strongly
        autocorrelated and i.i.d. is not, and the i.i.d. gap is NOT CI-above-0.
"""
import importlib

import pytest

M = importlib.import_module("scripts.mood_r1b_measure")


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
    # the regime world is strongly autocorrelated (persistence); the shuffle
    # destroys it — the two worlds differ ONLY in autocorrelation.
    assert ga["autocorr_regime_mean"] > 0.5, ga["autocorr_regime_mean"]
    assert abs(ga["autocorr_iid_mean"]) < 0.1, ga["autocorr_iid_mean"]


def test_iid_is_a_valid_failable_control_not_ci_above_0(res):
    # the control CAN fail: if mood helped in i.i.d. too it would be noise.
    # Here it HURTS (CI below 0) — a valid, correctly-behaving control.
    ga = res["g_adaptive"]
    assert not ga["iid_ci_above_0"], ga["boot_ci_gap_iid"]
    assert ga["mean_gap_iid"] < 0, ga["mean_gap_iid"]


# ------------------------------------ the recorded PRE-REGISTERED headline NULL
def test_headline_null_is_pinned_not_silently_flipped(res):
    """The pre-registered headline (regime gap CI-above-0) was NOT met — the
    regime CI lower bound sits a whisker below 0. Pin the null so it cannot
    silently become a claimed positive without a fresh, honest measurement. If a
    future change makes mood genuinely CI-separated at the pinned config, THIS
    test must be updated deliberately (with new CIs), never left to drift."""
    ga = res["g_adaptive"]
    assert not ga["regime_ci_above_0"], ga["boot_ci_gap_regime"]
    assert not ga["headline_pass"]
    # the regime CI lower bound is only marginally below 0 (a near-miss, not a
    # gross null): most of the CI is above 0.
    assert ga["boot_ci_gap_regime"][0] < 0.0 <= ga["boot_ci_gap_regime"][1]


def test_fair_world_flips_the_direction_to_adaptive(res):
    """R1b's real, honest result vs R1: on the FAIR persistent-regime world the
    effect DIRECTION flipped to adaptive — mood HELPS in the regime world and
    HARMS in i.i.d. (R1 had BOTH negative). Pin this qualitative difference so it
    cannot silently regress."""
    ga = res["g_adaptive"]
    assert ga["mean_gap_regime"] > 0.0, ga["mean_gap_regime"]     # regime: mood helps (direction)
    assert ga["mean_gap_iid"] < 0.0, ga["mean_gap_iid"]           # i.i.d.: mood hurts
    # and the regime effect is CI-separated ABOVE the i.i.d. effect (the fair
    # world moved mood's effect ~+2.5 reward units in the persistent direction).
    assert ga["boot_ci_gap_regime"][0] > ga["boot_ci_gap_iid"][1], (
        ga["boot_ci_gap_regime"], ga["boot_ci_gap_iid"])


# --------------------------------------- diagnostic presence (not a gate)
def test_diagnostic_recorded(res):
    d = res["diagnostic"]
    assert "prediction_mse" in d
    assert "mean_mse_improvement_regime" in d["prediction_mse"]
