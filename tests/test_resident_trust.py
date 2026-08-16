"""Regression for RESIDENT_TRUST_PREREG.md -- trust as
competence x willingness (Castelfranchi & Falcone's cognitive trust
theory), generalizing trust_mayor to any target via
bigville_theory_of_mind.mint_resident_tom_belief.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.can_self_worth_bridge import ensure_can_seed
from domains.resident_trust import (
    mint_trust_beliefs, read_trust, record_trust_incident,
)


def _fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    mt = inner.add_node("Microtheory", {"name": "test_mt", "temperature": 1.5})
    return inner, mt


# ---------------------------------------------------------------------
# 1. Competence evidence alone does not raise trust.
# ---------------------------------------------------------------------
def test_competence_alone_does_not_raise_trust():
    inner, mt = _fresh()
    beliefs = mint_trust_beliefs(inner, mt, "Alex")
    record_trust_incident(inner, beliefs, dimension="competence", positive=True)
    assert read_trust(inner, beliefs) == pytest.approx(0.0)


# ---------------------------------------------------------------------
# 2. Trust rises only once BOTH dimensions are positively evidenced.
# ---------------------------------------------------------------------
def test_trust_rises_once_both_dimensions_are_positive():
    inner, mt = _fresh()
    beliefs = mint_trust_beliefs(inner, mt, "Alex")
    record_trust_incident(inner, beliefs, dimension="competence", positive=True)
    record_trust_incident(inner, beliefs, dimension="willingness", positive=True)
    competence_ef = inner.node(beliefs["competence"])["attrs"]["external_field"]
    willingness_ef = inner.node(beliefs["willingness"])["attrs"]["external_field"]
    assert read_trust(inner, beliefs) == pytest.approx(min(competence_ef, willingness_ef))
    assert read_trust(inner, beliefs) > 0.0


# ---------------------------------------------------------------------
# 3. A betrayal caps trust regardless of competence.
# ---------------------------------------------------------------------
def test_a_betrayal_caps_trust_even_with_high_competence():
    inner, mt = _fresh()
    beliefs = mint_trust_beliefs(inner, mt, "Alex")
    for _ in range(5):
        record_trust_incident(inner, beliefs, dimension="competence", positive=True)
    record_trust_incident(inner, beliefs, dimension="willingness", positive=True)
    trust_before = read_trust(inner, beliefs)
    assert trust_before > 0.0

    record_trust_incident(inner, beliefs, dimension="willingness", positive=False)
    record_trust_incident(inner, beliefs, dimension="willingness", positive=False)
    willingness_ef = inner.node(beliefs["willingness"])["attrs"]["external_field"]
    assert willingness_ef < 0.0
    assert read_trust(inner, beliefs) == pytest.approx(willingness_ef)
    competence_ef = inner.node(beliefs["competence"])["attrs"]["external_field"]
    assert competence_ef > 0.0  # high competence, unchanged
    assert read_trust(inner, beliefs) < competence_ef  # trust capped below it


# ---------------------------------------------------------------------
# 4. Per-target isolation.
# ---------------------------------------------------------------------
def test_per_target_isolation():
    inner, mt = _fresh()
    beliefs_alex = mint_trust_beliefs(inner, mt, "Alex")
    for _ in range(3):
        record_trust_incident(inner, beliefs_alex, dimension="competence", positive=True)
        record_trust_incident(inner, beliefs_alex, dimension="willingness", positive=True)
    assert read_trust(inner, beliefs_alex) > 0.0

    beliefs_sam = mint_trust_beliefs(inner, mt, "Sam")
    assert read_trust(inner, beliefs_sam) == pytest.approx(0.0)


# ---------------------------------------------------------------------
# 5. Reuses the named ToM entry point.
# ---------------------------------------------------------------------
def test_trust_beliefs_are_named_tom_beliefs():
    inner, mt = _fresh()
    beliefs = mint_trust_beliefs(inner, mt, "Alex")
    assert inner.node(beliefs["competence"])["attrs"]["name"] == "competence_for:Alex"
    assert inner.node(beliefs["willingness"])["attrs"]["name"] == "willingness_for:Alex"


def test_mint_trust_beliefs_is_idempotent():
    inner, mt = _fresh()
    b1 = mint_trust_beliefs(inner, mt, "Alex")
    b2 = mint_trust_beliefs(inner, mt, "Alex")
    assert b1["competence"] == b2["competence"]
    assert b1["willingness"] == b2["willingness"]


def test_trust_mayor_seed_is_untouched():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json", "worlds/bigville_can_beliefs.py"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
