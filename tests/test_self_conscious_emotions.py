"""Regression for seeds/self_conscious_emotions.json -- the self-conscious
emotion appraisal mechanism (pride/shame/guilt/embarrassment). See
docs/research/psychology_affect/SELF_CONSCIOUS_EMOTIONS_PREREG.md for the
registered design and SELF_CONSCIOUS_EMOTIONS_RESULTS.md for the
live-demonstration numbers this file's regression assertions encode.

Mirrors tests/test_rule_dispute_escalation.py's own calling convention.
"""
from __future__ import annotations

import json
import re

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATH = "seeds/self_conscious_emotions.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    inner.load_seed_manifest(engine_rules_only(d))
    return s


def _appraise(inner, *, standard_met, attribution_locus, witness_judgments=()):
    ctx = inner.add_node("SelfConsciousContext", {
        "standard_met": 1.0 if standard_met else 0.0,
        "attribution_locus": attribution_locus,
    })
    for judgment in witness_judgments:
        w = inner.add_node("WitnessBelief", {"judgment": judgment})
        inner.add_edge(ctx, "has_witness_belief", w, {})
    sig = inner.add_node("SelfConsciousSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_appraisal", sig, {})
    inner.run_rules(50)
    return dict(inner.node(sig)["attrs"])


# ---------------------------------------------------------------------
# 1. Prediction 1 -- private shame: violated standard, global attribution,
#    no witnesses. Audience-independent (Tangney et al. 1996).
# ---------------------------------------------------------------------
def test_private_global_attribution_violation_is_shame():
    s = _loaded_substrate()
    inner = s._inner
    r = _appraise(inner, standard_met=False, attribution_locus="global_self")
    assert r["emotion"] == "shame"


# ---------------------------------------------------------------------
# 2. Prediction 2 -- private guilt: same violation, specific-act
#    attribution instead.
# ---------------------------------------------------------------------
def test_private_specific_act_attribution_violation_is_guilt():
    s = _loaded_substrate()
    inner = s._inner
    r = _appraise(inner, standard_met=False, attribution_locus="specific_act")
    assert r["emotion"] == "guilt"


# ---------------------------------------------------------------------
# 3. Prediction 3 -- pride bifurcates the same way (Tracy & Robins 2007):
#    same standard MET, different attribution, different emotion.
# ---------------------------------------------------------------------
def test_pride_bifurcates_by_attribution_locus():
    s = _loaded_substrate()
    inner = s._inner
    hubristic = _appraise(inner, standard_met=True, attribution_locus="global_self")
    authentic = _appraise(inner, standard_met=True, attribution_locus="specific_act")
    assert hubristic["emotion"] == "hubristic_pride"
    assert authentic["emotion"] == "authentic_pride"


# ---------------------------------------------------------------------
# 4. Prediction 4 -- embarrassment requires exposure (the one
#    audience-dependent cell, Miller 1996 / Tangney et al. 1996).
# ---------------------------------------------------------------------
def test_circumstance_violation_requires_a_witness_for_embarrassment():
    s = _loaded_substrate()
    inner = s._inner
    private = _appraise(inner, standard_met=False, attribution_locus="circumstance")
    public = _appraise(inner, standard_met=False, attribution_locus="circumstance",
                       witness_judgments=["violated"])
    assert private["emotion"] == "none"
    assert public["emotion"] == "embarrassment"


# ---------------------------------------------------------------------
# 5. Prediction 5 -- the genuine second-order-belief test: embarrassment
#    fires from a witness's MISTAKEN belief even when ground truth
#    (standard_met) says nothing was wrong.
# ---------------------------------------------------------------------
def test_embarrassment_fires_from_a_witnesss_mistaken_belief():
    s = _loaded_substrate()
    inner = s._inner
    r = _appraise(inner, standard_met=True, attribution_locus="circumstance",
                 witness_judgments=["violated"])
    assert r["perceived_violation"] is True
    assert r["emotion"] == "embarrassment"


def test_no_embarrassment_when_witness_correctly_believes_standard_was_met():
    s = _loaded_substrate()
    inner = s._inner
    r = _appraise(inner, standard_met=True, attribution_locus="circumstance",
                 witness_judgments=["met", "met"])
    assert r["perceived_violation"] is False
    assert r["emotion"] == "none"


# ---------------------------------------------------------------------
# 6. Prediction 6 -- shame/guilt are exposure-INDEPENDENT: adding
#    witnesses does not change the outcome away from shame.
# ---------------------------------------------------------------------
def test_shame_is_unchanged_by_witness_count():
    s = _loaded_substrate()
    inner = s._inner
    private = _appraise(inner, standard_met=False, attribution_locus="global_self")
    public = _appraise(inner, standard_met=False, attribution_locus="global_self",
                       witness_judgments=["violated", "violated", "met"])
    assert private["emotion"] == public["emotion"] == "shame"


def test_guilt_is_unchanged_by_witness_count():
    s = _loaded_substrate()
    inner = s._inner
    private = _appraise(inner, standard_met=False, attribution_locus="specific_act")
    public = _appraise(inner, standard_met=False, attribution_locus="specific_act",
                       witness_judgments=["violated"])
    assert private["emotion"] == public["emotion"] == "guilt"


# ---------------------------------------------------------------------
# 7. Idempotency -- a stable fixpoint.
# ---------------------------------------------------------------------
def test_decide_is_a_stable_fixpoint():
    s = _loaded_substrate()
    inner = s._inner
    ctx = inner.add_node("SelfConsciousContext", {
        "standard_met": 0.0, "attribution_locus": "circumstance"})
    w = inner.add_node("WitnessBelief", {"judgment": "violated"})
    inner.add_edge(ctx, "has_witness_belief", w, {})
    sig = inner.add_node("SelfConsciousSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_appraisal", sig, {})
    inner.run_rules(50)
    snapshot1 = dict(inner.node(sig)["attrs"])
    inner.run_rules(50)
    snapshot2 = dict(inner.node(sig)["attrs"])
    assert snapshot1 == snapshot2


# ---------------------------------------------------------------------
# 8. No-Python-decision source audit.
# ---------------------------------------------------------------------
def test_no_python_decision_source_audit():
    harness_src = open("scripts/self_conscious_emotions_demo.py").read()
    forbidden = re.compile(
        r"set_attr\([^)]*[\"'](emotion|perceived_violation)[\"']"
    )
    assert not forbidden.search(harness_src)


# ---------------------------------------------------------------------
# 9. depends_on / dependency hygiene, both productions declared.
# ---------------------------------------------------------------------
def test_seed_manifest_declares_both_productions():
    d = json.load(open(SEED_PATH))
    assert d["depends_on"] == []
    assert len(d["productions"]) == 2
    by_edge = {p["edge_type"]: p for p in d["productions"]}
    assert by_edge["has_appraisal"]["src"]["type"] == "SelfConsciousContext"
    assert by_edge["has_appraisal"]["tgt"]["type"] == "SelfConsciousSignal"
    assert by_edge["has_witness_belief"]["src"]["type"] == "SelfConsciousContext"
    assert by_edge["has_witness_belief"]["tgt"]["type"] == "WitnessBelief"
