"""Regression for domains/can_self_worth_bridge.py -- SelfPattern.
held_self_worth sourced from a resident's REAL, live CAN self_worth belief
(relaxed via seeds/can_native_reimplementation.json's own discrete-
asynchronous update rule) instead of a hand-picked scalar. See
docs/research/psychology_affect/HELD_SELF_WORTH_FROM_CAN_PREREG.md.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed, relax_resident_self_worth

SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]


def _base_params(prior_self_worth):
    return {
        "resolution_bins": 8, "arousal": 0.2,
        "prior_world_safe": 0.6, "prior_self_worth": prior_self_worth,
        "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
        "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
        "mood_bias": 0.3,
    }


def _resident(name, prior_self_worth, index=0):
    return {"name": name, "index": index, "params": _base_params(prior_self_worth)}


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def _dispute_then_appraise(inner, *, issue_severity, band_code, witnesses,
                           held_self_worth, audience_gain=0.15):
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
    pattern = inner.add_node("SelfPattern", {"held_self_worth": float(held_self_worth)})
    inner.add_edge(ctx, "has_self_pattern", pattern, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    sc_ctx = inner.neighbours(ctx, "bridged_to")[0]
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    return {
        "attribution_locus": inner.node(sc_ctx)["attrs"]["attribution_locus"],
        "emotion": inner.node(sc_sig)["attrs"]["emotion"],
    }


# ---------------------------------------------------------------------
# 1. Prediction 1 -- opposite personality priors converge to opposite REAL
#    CAN self_worth states.
# ---------------------------------------------------------------------
def test_opposite_priors_converge_to_opposite_can_self_worth_states():
    s = _loaded_substrate()
    inner = s._inner
    confident = relax_resident_self_worth(inner, _resident("Confident", 0.9))
    insecure = relax_resident_self_worth(inner, _resident("Insecure", 0.1, index=1))
    assert confident["self_worth"] == 1.0
    assert insecure["self_worth"] == -1.0


def test_relaxation_converges_within_a_bounded_number_of_steps():
    s = _loaded_substrate()
    inner = s._inner
    out = relax_resident_self_worth(inner, _resident("Confident", 0.9))
    assert out["steps"] < 3000  # < max_steps, i.e. reached a stable fixpoint


# ---------------------------------------------------------------------
# 2. Prediction 2 -- end to end: the SAME dispute, appraised through each
#    resident's REAL, independently-relaxed CAN self_worth, produces the
#    theoretically-expected opposite emotions.
# ---------------------------------------------------------------------
def test_end_to_end_real_can_self_worth_drives_opposite_emotions():
    s = _loaded_substrate()
    inner = s._inner
    confident = relax_resident_self_worth(inner, _resident("Confident", 0.9))
    insecure = relax_resident_self_worth(inner, _resident("Insecure", 0.1, index=1))

    guilt_case = _dispute_then_appraise(
        inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=confident["self_worth"])
    shame_case = _dispute_then_appraise(
        inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=insecure["self_worth"])

    assert guilt_case["attribution_locus"] == "specific_act"
    assert guilt_case["emotion"] == "guilt"
    assert shame_case["attribution_locus"] == "global_self"
    assert shame_case["emotion"] == "shame"


# ---------------------------------------------------------------------
# 3. Idempotent seed loading (ensure_can_seed called twice on one
#    substrate does not error or reload).
# ---------------------------------------------------------------------
def test_ensure_can_seed_is_idempotent():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    ensure_can_seed(inner)
    ensure_can_seed(inner)
    out = relax_resident_self_worth(inner, _resident("Confident", 0.9))
    assert out["self_worth"] == 1.0


# ---------------------------------------------------------------------
# 4. No seed was edited by this rung (task charter).
# ---------------------------------------------------------------------
def test_no_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/rule_dispute_escalation.json",
             "seeds/self_conscious_emotions.json",
             "seeds/rule_dispute_self_conscious_bridge.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
