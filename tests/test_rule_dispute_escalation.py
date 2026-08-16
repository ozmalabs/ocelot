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
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": issue_severity, "band_code": band_code,
        "witnesses": witnesses, "audience_gain": audience_gain,
    })
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
# 2. Prediction 1 -- manipulation check: pressure strictly decreases as
#    closeness increases, holding severity/witnesses fixed.
# ---------------------------------------------------------------------
def test_pressure_strictly_decreases_with_closeness():
    s = _loaded_substrate()
    inner = s._inner
    pressures = [_decide(inner, issue_severity=0.8, band_code=b, witnesses=3)["pressure"]
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
# 5. Prediction 4 -- the interaction: at FIXED high witness count and high
#    severity, raising closeness flips escalate -> defuse. This is the
#    load-bearing claim (PREREG Sec2): the SAME public dispute plays out
#    differently depending on who is having it.
# ---------------------------------------------------------------------
def test_closeness_flips_outcome_at_fixed_high_witness_severity():
    s = _loaded_substrate()
    inner = s._inner
    low = _decide(inner, issue_severity=0.8, band_code=0, witnesses=3)
    high = _decide(inner, issue_severity=0.8, band_code=5, witnesses=3)
    assert low["outcome"] == "escalate"
    assert high["outcome"] == "defuse"


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
# 7. Idempotency -- a stable fixpoint, matching every other sd-loop-family
#    rule in this codebase.
# ---------------------------------------------------------------------
def test_decide_is_a_stable_fixpoint():
    s = _loaded_substrate()
    inner = s._inner
    ctx = inner.add_node("DisputeContext", {
        "issue_severity": 0.5, "band_code": 2, "witnesses": 1, "audience_gain": 0.15})
    sig = inner.add_node("RuleDisputeSignal", {"status": "pending"})
    inner.add_edge(ctx, "has_signal", sig, {})
    inner.run_rules(50)
    snapshot1 = dict(inner.node(sig)["attrs"])
    inner.run_rules(50)
    snapshot2 = dict(inner.node(sig)["attrs"])
    assert snapshot1 == snapshot2


# ---------------------------------------------------------------------
# 8. No-Python-decision source audit -- the harness must never itself
#    set_attr a computed closeness/pressure/outcome value.
# ---------------------------------------------------------------------
def test_no_python_decision_source_audit():
    harness_src = open("scripts/rule_dispute_escalation_demo.py").read()
    forbidden = re.compile(
        r"set_attr\([^)]*[\"'](closeness|pressure|outcome)[\"']"
    )
    assert not forbidden.search(harness_src)


# ---------------------------------------------------------------------
# 9. depends_on / dependency hygiene.
# ---------------------------------------------------------------------
def test_seed_manifest_declares_the_dispute_context_production():
    d = json.load(open(SEED_PATH))
    assert d["depends_on"] == []
    assert len(d["productions"]) == 1
    prod = d["productions"][0]
    assert prod["src"]["type"] == "DisputeContext"
    assert prod["edge_type"] == "has_signal"
    assert prod["tgt"]["type"] == "RuleDisputeSignal"
