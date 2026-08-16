"""Regression for seeds/rule_dispute_self_conscious_bridge.json -- the live
wiring from a decided rule dispute (seeds/rule_dispute_escalation.json) to a
self-conscious-emotion appraisal (seeds/self_conscious_emotions.json) for
the claim-holder who was wrong. See docs/research/psychology_affect/
RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md for the registered design.

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


def _dispute_then_appraise(inner, *, issue_severity, band_code, witnesses, audience_gain=0.15):
    """witnesses: list of per-witness closeness values."""
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": issue_severity, "band_code": band_code,
        "audience_gain": audience_gain,
    })
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(ctx, "has_witness", w, {})
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
        "standard_met": inner.node(sc_ctx)["attrs"]["standard_met"],
        "emotion": inner.node(sc_sig)["attrs"]["emotion"],
        "witness_belief_count": len(inner.neighbours(sc_ctx, "has_witness_belief")),
        "bridged_to_count": len(sc_ctx_neighbours),
    }


# ---------------------------------------------------------------------
# 1. Prediction 1 -- escalated dispute bridges to shame.
# ---------------------------------------------------------------------
def test_escalated_dispute_bridges_to_shame():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0,
                               witnesses=[0.0, 0.0, 0.0])
    assert r["dispute_outcome"] == "escalate"
    assert r["attribution_locus"] == "global_self"
    assert r["standard_met"] == 0.0
    assert r["emotion"] == "shame"


# ---------------------------------------------------------------------
# 2. Prediction 2 -- defused dispute bridges to guilt, not shame.
# ---------------------------------------------------------------------
def test_defused_dispute_bridges_to_guilt():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.2, band_code=4, witnesses=[])
    assert r["dispute_outcome"] == "defuse"
    assert r["attribution_locus"] == "specific_act"
    assert r["emotion"] == "guilt"


# ---------------------------------------------------------------------
# 3. Prediction 3 -- never embarrassment, across a real sweep of the two
#    prior rungs' own registered parameter ranges.
# ---------------------------------------------------------------------
def test_bridge_never_produces_embarrassment_or_none():
    s = _loaded_substrate()
    inner = s._inner
    emotions_seen = set()
    for band, severity10, n_witnesses in itertools.product(
        (-1, 0, 1, 2, 3, 4, 5), (1, 3, 5, 7, 9), (0, 1, 3)
    ):
        r = _dispute_then_appraise(
            inner, issue_severity=severity10 / 10.0, band_code=band,
            witnesses=[0.0] * n_witnesses)
        emotions_seen.add(r["emotion"])
    assert emotions_seen <= {"shame", "guilt"}
    assert "embarrassment" not in emotions_seen
    assert "none" not in emotions_seen


# ---------------------------------------------------------------------
# 4. Prediction 4 -- witness count carried over exactly.
# ---------------------------------------------------------------------
@pytest.mark.parametrize("n_witnesses", [0, 1, 2, 3, 5])
def test_witness_count_carried_over_exactly(n_witnesses):
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_then_appraise(inner, issue_severity=0.5, band_code=0,
                               witnesses=[0.0] * n_witnesses)
    assert r["witness_belief_count"] == n_witnesses


# ---------------------------------------------------------------------
# 5. Prediction 5 -- idempotent bridging: re-running run_rules() does not
#    double-mint a SelfConsciousContext or duplicate WitnessBelief nodes.
# ---------------------------------------------------------------------
def test_bridge_is_idempotent_on_repeated_run_rules():
    s = _loaded_substrate()
    inner = s._inner
    r1 = _dispute_then_appraise(inner, issue_severity=0.9, band_code=0,
                                witnesses=[0.0, 0.0, 0.0])
    inner.run_rules(50)
    inner.run_rules(50)
    assert len(inner.neighbours(r1["ctx"], "bridged_to")) == 1
    assert len(inner.neighbours(r1["sc_ctx"], "has_witness_belief")) == 3


# ---------------------------------------------------------------------
# 6. Prediction 6 -- end to end: the ACTUAL rule_dispute_escalation_demo.py
#    scenarios, not synthetic self-conscious inputs.
# ---------------------------------------------------------------------
def test_end_to_end_matches_the_dispute_demos_own_scenarios():
    s = _loaded_substrate()
    inner = s._inner
    escalated = _dispute_then_appraise(
        inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0])
    defused = _dispute_then_appraise(
        inner, issue_severity=0.2, band_code=4, witnesses=[])
    assert escalated["emotion"] == "shame"
    assert defused["emotion"] == "guilt"


# ---------------------------------------------------------------------
# 7. Neither prior seed was edited (task charter) -- confirmed via git,
#    mirroring test_can_register_quantization.py's own
#    test_already_landed_seeds_are_untouched precedent.
# ---------------------------------------------------------------------
def test_prior_seeds_are_untouched():
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
# 8. depends_on / dependency hygiene.
# ---------------------------------------------------------------------
def test_seed_manifest_dependencies_and_productions():
    d = json.load(open("seeds/rule_dispute_self_conscious_bridge.json"))
    assert set(d["depends_on"]) == {"rule_dispute_escalation", "self_conscious_emotions"}
    assert len(d["productions"]) == 2
    by_edge = {p["edge_type"]: p for p in d["productions"]}
    assert by_edge["bridged_to"]["src"]["type"] == "DisputeContext"
    assert by_edge["bridged_to"]["tgt"]["type"] == "SelfConsciousContext"
    assert by_edge["mirrored_as"]["src"]["type"] == "WitnessPresence"
    assert by_edge["mirrored_as"]["tgt"]["type"] == "WitnessBelief"
