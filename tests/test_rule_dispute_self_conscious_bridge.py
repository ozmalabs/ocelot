"""Regression for seeds/rule_dispute_self_conscious_bridge.json -- the live
wiring from a decided rule dispute (seeds/rule_dispute_escalation.json) to a
self-conscious-emotion appraisal (seeds/self_conscious_emotions.json) for
the claim-holder who was wrong. See docs/research/psychology_affect/
RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md and
ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md (v1.1.0: attribution_locus is a
residual against the agent's held SelfPattern, not a lookup from the
dispute outcome) for the registered design.

Mirrors tests/test_rule_dispute_escalation.py's own calling convention.
"""
from __future__ import annotations

import itertools
import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def _dispute_then_appraise(inner, *, issue_severity, band_code, witnesses,
                           held_self_worth=None, audience_gain=0.15):
    """witnesses: list of per-witness closeness values. held_self_worth:
    None (no track record -> circumstance) or a scalar in [-1,1]."""
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
    if held_self_worth is not None:
        pattern = inner.add_node("SelfPattern", {"held_self_worth": held_self_worth})
        inner.add_edge(ctx, "has_self_pattern", pattern, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    dispute_attrs = inner.node(sig)["attrs"]
    sc_ctx_neighbours = inner.neighbours(ctx, "bridged_to")
    sc_ctx = sc_ctx_neighbours[0]
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    return {
        "ctx": ctx, "sc_ctx": sc_ctx,
        "dispute_outcome": dispute_attrs["outcome"],
        "attribution_locus": inner.node(sc_ctx)["attrs"]["attribution_locus"],
        "witness_judgment": inner.node(sc_ctx)["attrs"]["witness_judgment"],
        "standard_met": inner.node(sc_ctx)["attrs"]["standard_met"],
        "emotion": inner.node(sc_sig)["attrs"]["emotion"],
        "witness_belief_count": len(inner.neighbours(sc_ctx, "has_witness_belief")),
        "bridged_to_count": len(sc_ctx_neighbours),
    }


# ---------------------------------------------------------------------
# 1. ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md prediction 1 -- a failure
#    confirming an already-negative held self-pattern reads as global_self
#    -> shame.
# ---------------------------------------------------------------------
def test_failure_confirming_negative_pattern_bridges_to_shame():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0,
                               witnesses=[0.0, 0.0, 0.0], held_self_worth=-0.6)
    assert r["attribution_locus"] == "global_self"
    assert r["standard_met"] == 0.0
    assert r["emotion"] == "shame"


# ---------------------------------------------------------------------
# 2. Prediction 2 -- the IDENTICAL failure, but a positive held pattern
#    (contradicts it) -> specific_act -> guilt, not shame.
# ---------------------------------------------------------------------
def test_same_failure_contradicting_positive_pattern_bridges_to_guilt():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0,
                               witnesses=[0.0, 0.0, 0.0], held_self_worth=0.6)
    assert r["attribution_locus"] == "specific_act"
    assert r["emotion"] == "guilt"


# ---------------------------------------------------------------------
# 3. Prediction 3 -- no held pattern at all -> circumstance, and
#    embarrassment becomes reachable when witnessed. This RETRACTS the
#    prior v1.0.0 "never embarrassment" finding, which was an artifact of
#    the cruder escalate/defuse-only mapping.
# ---------------------------------------------------------------------
def test_no_track_record_is_circumstance_and_none_when_private():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0, witnesses=[])
    assert r["attribution_locus"] == "circumstance"
    assert r["emotion"] == "none"


def test_no_track_record_produces_embarrassment_when_witnessed():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0,
                               witnesses=[0.0, 0.0, 0.0])
    assert r["attribution_locus"] == "circumstance"
    assert r["emotion"] == "embarrassment"


# ---------------------------------------------------------------------
# 4. Full emotion family is now reachable through the bridge (a real
#    sweep, not two cherry-picked points) -- a strictly larger reachable
#    set than v1.0.0's {shame, guilt}.
# ---------------------------------------------------------------------
def test_full_emotion_family_is_reachable_across_a_real_sweep():
    s = _loaded_substrate()
    inner = s._inner
    emotions_seen = set()
    for band, severity10, n_witnesses, pattern in itertools.product(
        (-1, 0, 1, 2, 3, 4, 5), (1, 5, 9), (0, 3),
        (None, -0.6, 0.6),
    ):
        r = _dispute_then_appraise(
            inner, issue_severity=severity10 / 10.0, band_code=band,
            witnesses=[0.0] * n_witnesses, held_self_worth=pattern)
        emotions_seen.add(r["emotion"])
    assert emotions_seen <= {"shame", "guilt", "embarrassment", "none"}
    assert "shame" in emotions_seen
    assert "guilt" in emotions_seen
    assert "embarrassment" in emotions_seen


# ---------------------------------------------------------------------
# 5. witness_judgment is UNCHANGED -- still keyed to the dispute's own
#    escalate/defuse outcome, independent of attribution_locus's new
#    residual source. Confirmed by holding held_self_worth fixed (so
#    attribution_locus/emotion stay identical) while outcome differs.
# ---------------------------------------------------------------------
def test_witness_judgment_still_keyed_to_dispute_outcome_not_the_residual():
    s = _loaded_substrate()
    inner = s._inner
    escalated = _dispute_then_appraise(
        inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=-0.6)
    defused = _dispute_then_appraise(
        inner, issue_severity=0.2, band_code=4, witnesses=[],
        held_self_worth=-0.6)
    assert escalated["dispute_outcome"] == "escalate"
    assert defused["dispute_outcome"] == "defuse"
    assert escalated["witness_judgment"] == "violated"
    assert defused["witness_judgment"] == "met"
    # emotion is the SAME in both -- attribution_locus (global_self, from
    # the identical held_self_worth) drives it, not witness_judgment
    assert escalated["emotion"] == defused["emotion"] == "shame"


# ---------------------------------------------------------------------
# 6. Witness count carried over exactly (unchanged mechanism).
# ---------------------------------------------------------------------
@pytest.mark.parametrize("n_witnesses", [0, 1, 2, 3, 5])
def test_witness_count_carried_over_exactly(n_witnesses):
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.5, band_code=0,
                               witnesses=[0.0] * n_witnesses)
    assert r["witness_belief_count"] == n_witnesses


# ---------------------------------------------------------------------
# 7. Idempotent bridging: re-running run_rules() does not double-mint.
# ---------------------------------------------------------------------
def test_bridge_is_idempotent_on_repeated_run_rules():
    s = _loaded_substrate()
    inner = s._inner
    r1 = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0,
                                witnesses=[0.0, 0.0, 0.0], held_self_worth=-0.6)
    inner.run_rules(50)
    inner.run_rules(50)
    assert len(inner.neighbours(r1["ctx"], "bridged_to")) == 1
    assert len(inner.neighbours(r1["sc_ctx"], "has_witness_belief")) == 3


# ---------------------------------------------------------------------
# 8. End to end: the ACTUAL rule_dispute_escalation_demo.py scenarios.
# ---------------------------------------------------------------------
def test_end_to_end_matches_the_dispute_demos_own_scenarios():
    s = _loaded_substrate()
    inner = s._inner
    escalated = _dispute_then_appraise(
        inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0],
        held_self_worth=-0.6)
    defused = _dispute_then_appraise(
        inner, issue_severity=0.2, band_code=4, witnesses=[], held_self_worth=0.6)
    assert escalated["emotion"] == "shame"
    assert defused["emotion"] == "guilt"


# ---------------------------------------------------------------------
# 9. Neither prior FOUNDATIONAL seed was edited (task charter) -- confirmed
#    via git. The bridge seed itself is deliberately refined in place
#    (this session's own glue layer, not a foundational rung).
# ---------------------------------------------------------------------
def test_foundational_seeds_are_untouched():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/rule_dispute_escalation.json",
             "seeds/self_conscious_emotions.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout


# ---------------------------------------------------------------------
# 10. depends_on / dependency hygiene, including the new SelfPattern
#     production.
# ---------------------------------------------------------------------
def test_seed_manifest_dependencies_and_productions():
    d = json.load(open("seeds/rule_dispute_self_conscious_bridge.json"))
    assert set(d["depends_on"]) == {"rule_dispute_escalation", "self_conscious_emotions"}
    assert d["version"] == "1.1.0"
    assert len(d["productions"]) == 3
    by_edge = {p["edge_type"]: p for p in d["productions"]}
    assert by_edge["bridged_to"]["src"]["type"] == "DisputeContext"
    assert by_edge["bridged_to"]["tgt"]["type"] == "SelfConsciousContext"
    assert by_edge["mirrored_as"]["src"]["type"] == "WitnessPresence"
    assert by_edge["mirrored_as"]["tgt"]["type"] == "WitnessBelief"
    assert by_edge["has_self_pattern"]["src"]["type"] == "DisputeContext"
    assert by_edge["has_self_pattern"]["tgt"]["type"] == "SelfPattern"
