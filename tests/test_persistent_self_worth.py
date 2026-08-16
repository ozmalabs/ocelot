"""Regression for domains/can_self_worth_bridge.py's persistence layer
(find_or_build_resident_can / record_incident_outcome) -- a resident's real
CAN self_worth belief carries forward across repeated appraisals and drifts
with accumulated incidents. See docs/research/psychology_affect/
PERSISTENT_SELF_WORTH_PREREG.md.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import (
    ensure_can_seed, find_or_build_resident_can, record_incident_outcome,
)

DISPUTE_SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def _fresh_substrate():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    return inner


def _appraise_dispute(inner, *, held_self_worth, issue_severity=0.9, band_code=0,
                      witnesses=(0.0, 0.0, 0.0)):
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": issue_severity, "band_code": band_code, "audience_gain": 0.15})
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
    return inner.node(sc_sig)["attrs"]["emotion"]


# ---------------------------------------------------------------------
# 1. Prediction 1 -- force_all_dirty() is necessary: without it, evidence
#    application leaves state unchanged even at a massive magnitude.
# ---------------------------------------------------------------------
def test_evidence_without_force_all_dirty_is_a_silent_noop():
    inner = _fresh_substrate()
    out = find_or_build_resident_can(inner, CONFIDENT)
    sw = out["concepts"]["self_worth"]
    assert inner.node(sw)["attrs"]["state"] == 1.0
    inner.concept_apply_evidence(sw, -1.0, 5.0)
    steps = inner.run_rules(3000)
    assert steps == 0
    assert inner.node(sw)["attrs"]["state"] == 1.0  # unchanged -- the gotcha


def test_force_all_dirty_fixes_it():
    inner = _fresh_substrate()
    out = find_or_build_resident_can(inner, CONFIDENT)
    sw = out["concepts"]["self_worth"]
    inner.concept_apply_evidence(sw, -1.0, 5.0)
    inner.force_all_dirty()
    steps = inner.run_rules(3000)
    assert steps > 0
    assert inner.node(sw)["attrs"]["state"] == -1.0


# ---------------------------------------------------------------------
# 2. Prediction 2 -- repeated confirming incidents flip a resident's basin.
# ---------------------------------------------------------------------
def test_repeated_negative_incidents_flip_a_confident_resident_to_shame_prone():
    inner = _fresh_substrate()
    out = find_or_build_resident_can(inner, CONFIDENT)
    assert out["self_worth"] == 1.0
    states = []
    for _ in range(8):
        sw = record_incident_outcome(
            inner, out["concepts"], standard_met=False, attribution_locus="global_self")
        states.append(sw)
    assert states[-1] == -1.0
    assert states[0] == 1.0  # did not flip on the FIRST incident alone


# ---------------------------------------------------------------------
# 3. Prediction 3 -- circumstance-attributed incidents do not move it.
# ---------------------------------------------------------------------
def test_circumstance_attributed_incidents_never_move_self_worth():
    inner = _fresh_substrate()
    out = find_or_build_resident_can(inner, CONFIDENT)
    before = out["self_worth"]
    for _ in range(10):
        record_incident_outcome(
            inner, out["concepts"], standard_met=False, attribution_locus="circumstance")
    after = inner.node(out["concepts"]["self_worth"])["attrs"]["state"]
    assert after == before


# ---------------------------------------------------------------------
# 4. Prediction 4 -- the same resident, appraised twice, persists (reuses
#    the SAME node, not a freshly reset one).
# ---------------------------------------------------------------------
def test_second_lookup_reuses_the_drifted_network():
    inner = _fresh_substrate()
    first = find_or_build_resident_can(inner, CONFIDENT)
    for _ in range(6):
        record_incident_outcome(inner, first["concepts"], standard_met=False,
                                attribution_locus="global_self")
    drifted = inner.node(first["concepts"]["self_worth"])["attrs"]["state"]
    second = find_or_build_resident_can(inner, CONFIDENT)
    assert second["is_new"] is False
    assert second["concepts"]["self_worth"] == first["concepts"]["self_worth"]
    assert second["self_worth"] == drifted == -1.0


def test_a_genuinely_new_resident_name_builds_fresh():
    inner = _fresh_substrate()
    find_or_build_resident_can(inner, CONFIDENT)
    other = dict(CONFIDENT, name="SomeoneElse", index=1)
    out = find_or_build_resident_can(inner, other)
    assert out["is_new"] is True


# ---------------------------------------------------------------------
# 5. Prediction 5 -- end to end: drift changes a later, otherwise
#    identical dispute's outcome.
# ---------------------------------------------------------------------
def test_drift_changes_the_outcome_of_a_later_identical_dispute():
    inner = _fresh_substrate()
    for path in DISPUTE_SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    resident = find_or_build_resident_can(inner, CONFIDENT)

    before_emotion = _appraise_dispute(
        inner, held_self_worth=inner.node(resident["concepts"]["self_worth"])["attrs"]["state"])
    assert before_emotion == "guilt"  # confident, failure contradicts pattern

    for _ in range(6):
        record_incident_outcome(inner, resident["concepts"], standard_met=False,
                                attribution_locus="global_self")

    after_emotion = _appraise_dispute(
        inner, held_self_worth=inner.node(resident["concepts"]["self_worth"])["attrs"]["state"])
    assert after_emotion == "shame"  # now confirms the (now-negative) pattern
    assert before_emotion != after_emotion


# ---------------------------------------------------------------------
# 6. No seed was edited (task charter).
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
