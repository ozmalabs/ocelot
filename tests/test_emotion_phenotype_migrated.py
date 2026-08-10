"""COMPUTATIONAL PHENOTYPING BY INVERSE INFERENCE gate (seed block 206000) —
reproduce a synthetic agent's emotional BASELINE (the 204000 knob-vector) from its
DECISIONS. The agents decide GRAPH-NATIVELY (run_rules over the landed
seeds/core_emotions.json); the fit is a mechanical Bayesian grid posterior over
knobs (model-fitting, NOT an agent decision). Re-derives inverse RL (Ng &
Russell), Bayesian ToM (Baker/Saxe/Tenenbaum), computational-psychiatry per-person
parameter fit (Montague/Huys/Friston).

FRAMING (standing project rule): understanding, not judgment; the FUNCTIONAL fit,
NOT felt qualia. SYNTHETIC-ONLY — real behavioural data is a care-gated follow-on.

Pins the measured criteria:
  * G1 PARAMETER RECOVERY + IDENTIFIABILITY MAP — mood_bias recovers (r>=0.9,
        credible interval covers truth), residual_thresh and threat_half_life
        recover to their identifiable INTERVAL, w_supergraph SIGN recovers, AND
        w_supergraph MAGNITUDE is structurally UNIDENTIFIABLE (a plateau: every
        positive magnitude yields byte-identical decisions).
  * G2 PREDICTION / MANIFOLD — the fitted baseline predicts HELD-OUT decisions
        strictly better than population-mean and random controls.
  * G3 EXPLANATION — counterfactual on the fitted knob attributes the psychopath's
        harm-endorsement and the parent's supergraph-costly act to w_supergraph.
  * G5 integer-native (agent side) + default-OFF byte-identity (no seed/Rust/Term
        added; canonical .so untouched).

The test RUNS the measure (able to fail if a knob does not recover, if the
w-magnitude plateau collapses, if held-out prediction does not beat the controls,
if the counterfactual does not isolate w_supergraph, if a float enters an emotion
decision, or if default-off is not byte-identical). Prereg:
VISION_EMOTION_PHENOTYPE_PREREG.md.
"""
import importlib

import pytest

M = importlib.import_module("scripts.emotion_phenotype_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


# ---------------------------------------------------------------------- G1
def test_G1_mood_recovers(res):
    m = res["g1_recovery"]["mood"]
    assert m["r"] >= 0.9, m
    assert m["coverage"] >= 0.9, m


def test_G1_residual_thresh_interval_recovers(res):
    r = res["g1_recovery"]["residual_thresh"]
    assert r["map_within_step_frac"] >= 0.9, r
    assert r["coverage"] >= 0.9, r


def test_G1_threat_half_life_interval_and_boundedbelow(res):
    h = res["g1_recovery"]["threat_half_life"]
    assert h["observable_flip_frac"] >= 0.9, h
    assert h["persistent_boundedbelow_frac"] >= 0.9, h


def test_G1_w_supergraph_sign_recovers(res):
    assert res["g1_recovery"]["w_supergraph"]["sign_recovery"] >= 0.95


def test_G1_w_magnitude_is_unidentifiable_plateau(res):
    w = res["w_magnitude_plateau"]
    assert w["all_identical"], w
    assert w["distinct_decision_vectors"] == 1, w


def test_G1_verdict(res):
    assert res["verdict"]["g1_parameter_recovery"]
    assert res["verdict"]["structural_identifiability_prediction_held"]


# ---------------------------------------------------------------------- G2
def test_G2_fitted_beats_controls(res):
    g2 = res["g2_prediction"]
    assert g2["fitted"] > g2["population_mean"], g2
    assert g2["fitted"] > g2["random"], g2
    assert g2["fitted_strictly_beats_pop"]
    assert g2["fitted_strictly_beats_random"]
    assert res["verdict"]["g2_prediction"]


# ---------------------------------------------------------------------- G3
def test_G3_psychopath_harm_attributed_to_w(res):
    p = res["g3_explanation"]["psychopath"]
    assert p["endorses_harm_under_fit"]
    assert p["declines_harm_if_w_healthy"]
    assert p["attribution_isolated"]


def test_G3_parent_costly_act_attributed_to_w(res):
    p = res["g3_explanation"]["parent"]
    assert p["endorses_costly_under_fit"]
    assert p["declines_costly_if_w_zero"]
    assert p["attribution_isolated"]


def test_G3_both_attributed_to_w(res):
    assert res["g3_explanation"]["both_attributed_to_w"]
    assert res["verdict"]["g3_explanation"]


# ---------------------------------------------------------------------- G5
def test_G5_integer_native_agent_side(res):
    assert res["integer_audit"]["all_integer"], res["integer_audit"]["offenders"]


def test_G5_default_off_byte_identity(res):
    d = res["default_off"]
    assert d["canonical_untouched"], d
    assert d["no_emotion_nodes_by_default"]
    assert d["adds_no_seed"]
    assert res["verdict"]["g5_integer_default_off"]


# --------------------------------------------------------------- noise-robust
def test_noise_robustness_degrades_gracefully(res):
    n = res["noise_robustness"]
    assert n["w_sign"] >= 0.95, n
    assert n["mood_r"] >= 0.85, n
    assert n["fitted_acc"] > n["population_mean"] if "population_mean" in n \
        else n["fitted_acc"] > n["pop_acc"], n
