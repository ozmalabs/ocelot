"""Regression for seeds/rule_dispute_escalation.json -- the Monopoly rule-
dispute defuse-vs-escalate mechanism. See docs/research/engine_substrate/
RULE_DISPUTE_ESCALATION_PREREG.md for the registered design and
RULE_DISPUTE_ESCALATION_RESULTS.md for the live-demonstration numbers this
file's regression assertions encode.

Mirrors tests/test_can_register_quantization.py's own calling convention.
"""
from __future__ import annotations

import json
import re

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATH = "seeds/rule_dispute_escalation.json"


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    inner.load_seed_manifest(engine_rules_only(d))
    return s


def _decide(inner, *, issue_severity, band_code, witnesses, audience_gain=0.15):
    """`witnesses` is a list of per-witness closeness values (Rung 2,
    PREREG Sec3b) -- pass an int for an all-anonymous witness count."""
    if isinstance(witnesses, int):
        witnesses = [0.0] * witnesses
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
    return dict(inner.node(sig)["attrs"])


# ---------------------------------------------------------------------
# 1. Codebook shape -- PREREG Sec2.
# ---------------------------------------------------------------------
def test_dispute_outcome_anchors_are_exactly_defuse_and_escalate():
    s = _loaded_substrate()
    inner = s._inner
    labels = {inner.node(n)["attrs"]["label"]: inner.node(n)["attrs"]["canonical_value"]
              for n in inner.nodes("DisputeOutcomeAnchor")}
    assert labels == {"defuse": -1.0, "escalate": 1.0}


# ---------------------------------------------------------------------
# 2. Prediction 1 -- manipulation check: pressure strictly decreases as the
#    DYAD's own closeness increases, holding severity/witnesses fixed
#    (witnesses all anonymous -- their contribution is now decoupled from
#    dyad closeness, Rung 2, so this isolates the dyad term alone).
# ---------------------------------------------------------------------
def test_pressure_strictly_decreases_with_dyad_closeness():
    s = _loaded_substrate()
    inner = s._inner
    pressures = [_decide(inner, issue_severity=0.8, band_code=b, witnesses=0)["pressure"]
                 for b in range(6)]
    assert all(pressures[i] > pressures[i + 1] for i in range(len(pressures) - 1)), pressures


# ---------------------------------------------------------------------
# 3. Prediction 2 -- defuses easily: close friends, low severity, no
#    witnesses.
# ---------------------------------------------------------------------
def test_close_friends_private_ambiguous_issue_defuses():
    s = _loaded_substrate()
    inner = s._inner
    r = _decide(inner, issue_severity=0.2, band_code=4, witnesses=0)
    assert r["outcome"] == "defuse"


# ---------------------------------------------------------------------
# 4. Prediction 3 -- escalates: near-strangers, high severity, several
#    witnesses (the Free Parking myth, monopoly_rulebook.txt:151, confidently
#    contradicted in front of the whole table).
# ---------------------------------------------------------------------
def test_near_strangers_public_confident_contradiction_escalates():
    s = _loaded_substrate()
    inner = s._inner
    r = _decide(inner, issue_severity=0.9, band_code=0, witnesses=3)
    assert r["outcome"] == "escalate"


# ---------------------------------------------------------------------
# 5. Rung 2 correction (PREREG Sec3b): Rung 1's "prediction 4" claimed dyad
#    closeness suppresses generic-audience amplification at a FIXED witness
#    count. That was a conflation -- Rung 2 decouples a witness's own
#    closeness from the dyad's, so anonymous witnesses now contribute a
#    CONSTANT term regardless of dyad closeness. This is the corrected,
#    intentional behavior, encoded as a standing regression: with all-
#    anonymous witnesses, dyad closeness alone is no longer enough to flip
#    a high-severity, well-witnessed dispute to defuse.
# ---------------------------------------------------------------------
def test_anonymous_witness_pressure_is_independent_of_dyad_closeness():
    s = _loaded_substrate()
    inner = s._inner
    low = _decide(inner, issue_severity=0.8, band_code=0, witnesses=3)
    high = _decide(inner, issue_severity=0.8, band_code=5, witnesses=3)
    # both still escalate -- three anonymous witnesses' fixed pressure
    # floor is not overcome by dyad closeness alone (Rung 1's claim here is
    # retracted, RESULTS.md Sec3b)
    assert low["outcome"] == "escalate"
    assert high["outcome"] == "escalate"
    # the audience contribution itself (pressure minus the dyad-only terms)
    # is identical regardless of dyad closeness
    assert low["pressure"] - (0.8 - 0.0) == pytest.approx(high["pressure"] - (0.8 - 1.0))


# ---------------------------------------------------------------------
# 6. Prediction 5 -- rival floor: band_code=-1 never reads as safer than
#    band_code=0 (rivalry does not accidentally look like ordinary distance).
# ---------------------------------------------------------------------
def test_rival_band_never_produces_lower_pressure_than_stranger():
    s = _loaded_substrate()
    inner = s._inner
    stranger = _decide(inner, issue_severity=0.8, band_code=0, witnesses=3)
    rival = _decide(inner, issue_severity=0.8, band_code=-1, witnesses=3)
    assert rival["pressure"] >= stranger["pressure"]


# ---------------------------------------------------------------------
# 7. Prediction 6 (Rung 2, PREREG Sec3b) -- a regulating witness (a
#    disputant's partner, high closeness) always LOWERS pressure relative
#    to an anonymous witness in the same slot, holding everything else
#    fixed. This holds even where it is not enough to flip the outcome
#    (RESULTS.md Sec3b's honest null on the flip at high severity) --
#    the direction is the registered, robust claim; the flip is not.
# ---------------------------------------------------------------------
def test_regulating_partner_always_lowers_pressure_vs_anonymous_witness():
    s = _loaded_substrate()
    inner = s._inner
    anon = _decide(inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.0])
    partner = _decide(inner, issue_severity=0.9, band_code=0, witnesses=[0.0, 0.0, 0.9])
    assert partner["pressure"] < anon["pressure"]
    # honest null: one partner among three witnesses does not overcome a
    # genuinely severe, near-stranger, public dispute
    assert anon["outcome"] == "escalate"
    assert partner["outcome"] == "escalate"


def test_regulating_partner_flips_a_borderline_dispute():
    """A milder, near-stranger, lightly-witnessed dispute sits close enough
    to the defuse/escalate boundary that a single regulating partner's
    bounded effect (max swing = audience_gain per witness) is enough to
    flip it -- range-found honestly (RESULTS.md Sec3b), not cherry-picked
    to match the originally-proposed severe scenario."""
    s = _loaded_substrate()
    inner = s._inner
    anon = _decide(inner, issue_severity=0.1, band_code=1, witnesses=[0.0])
    partner = _decide(inner, issue_severity=0.1, band_code=1, witnesses=[0.9])
    assert anon["outcome"] == "escalate"
    assert partner["outcome"] == "defuse"


def test_anonymous_witness_closeness_zero_reproduces_rung1_per_witness_term():
    """An anonymous witness (closeness=0.0) contributes exactly
    audience_gain*(1-0)=audience_gain, the same per-witness contribution
    Rung 1's bare witness count used -- PREREG Sec3b's backward-
    compatibility claim, checked directly against the closed-form value."""
    s = _loaded_substrate()
    inner = s._inner
    one = _decide(inner, issue_severity=0.5, band_code=0, witnesses=[0.0])
    three = _decide(inner, issue_severity=0.5, band_code=0, witnesses=[0.0, 0.0, 0.0])
    # each additional anonymous witness adds exactly audience_gain=0.15
    assert three["pressure"] - one["pressure"] == pytest.approx(2 * 0.15)


# ---------------------------------------------------------------------
# 8. Idempotency -- a stable fixpoint, matching every other sd-loop-family
#    rule in this codebase.
# ---------------------------------------------------------------------
def test_decide_is_a_stable_fixpoint():
    s = _loaded_substrate()
    inner = s._inner
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": 0.5, "band_code": 2, "audience_gain": 0.15})
    w = inner.add_node("WitnessPresence", {"closeness": 0.3})
    inner.add_edge(ctx, "has_witness", w, {})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    snapshot1 = dict(inner.node(sig)["attrs"])
    inner.run_rules(50)
    snapshot2 = dict(inner.node(sig)["attrs"])
    assert snapshot1 == snapshot2


# ---------------------------------------------------------------------
# 9. No-Python-decision source audit -- the harness must never itself
#    set_attr a computed closeness/pressure/outcome value.
# ---------------------------------------------------------------------
def test_no_python_decision_source_audit():
    harness_src = open("scripts/rule_dispute_escalation_demo.py").read()
    forbidden = re.compile(
        r"set_attr\([^)]*[\"'](closeness|pressure|outcome)[\"']"
    )
    assert not forbidden.search(harness_src)


# ---------------------------------------------------------------------
# 10. depends_on / dependency hygiene, including the Rung 2 production.
# ---------------------------------------------------------------------
def test_seed_manifest_declares_both_productions():
    d = json.load(open(SEED_PATH))
    assert d["depends_on"] == []
    assert d["version"] == "1.1.0"
    assert len(d["productions"]) == 2
    by_edge = {p["edge_type"]: p for p in d["productions"]}
    assert by_edge["has_signal"]["src"]["type"] == "DisputeContext"
    assert by_edge["has_signal"]["tgt"]["type"] == "RuleDisputeSignal"
    assert by_edge["has_witness"]["src"]["type"] == "DisputeContext"
    assert by_edge["has_witness"]["tgt"]["type"] == "WitnessPresence"
