"""Regression for SELF_EFFICACY_PREREG.md -- belief in one's OWN
capability (Bandura 1977, 1997), distinct from self_worth, wired into
the confirmed-dead AffectiveState.competence schema field.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.can_self_worth_bridge import ensure_can_seed, find_or_build_resident_can
from domains.self_efficacy import (
    mint_domain_self_efficacy, read_persistence_disposition,
    record_self_efficacy_incident, sync_competence_to_affective_state,
)

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def _fresh():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    return inner, resident_can


# ---------------------------------------------------------------------
# 1/2. Success raises, failure lowers.
# ---------------------------------------------------------------------
def test_success_raises_and_failure_lowers_self_efficacy():
    inner, resident_can = _fresh()
    concept = mint_domain_self_efficacy(inner, resident_can, "chess")
    v1 = record_self_efficacy_incident(inner, concept, success=True)
    v2 = record_self_efficacy_incident(inner, concept, success=True)
    assert v2 > v1 > 0.0
    v3 = record_self_efficacy_incident(inner, concept, success=False)
    assert v3 < v2


# ---------------------------------------------------------------------
# 3. Persistence/avoidance flips with the sign.
# ---------------------------------------------------------------------
def test_persistence_disposition_flips_with_repeated_failure():
    inner, resident_can = _fresh()
    concept = mint_domain_self_efficacy(inner, resident_can, "chess")
    record_self_efficacy_incident(inner, concept, success=True)
    v = record_self_efficacy_incident(inner, concept, success=True)
    assert read_persistence_disposition(v) == "persist"
    for _ in range(5):
        v = record_self_efficacy_incident(inner, concept, success=False)
    assert v < 0.0
    assert read_persistence_disposition(v) == "avoid"


def test_persistence_disposition_flips_back_with_subsequent_success():
    inner, resident_can = _fresh()
    concept = mint_domain_self_efficacy(inner, resident_can, "chess")
    for _ in range(5):
        v = record_self_efficacy_incident(inner, concept, success=False)
    assert read_persistence_disposition(v) == "avoid"
    for _ in range(5):
        v = record_self_efficacy_incident(inner, concept, success=True)
    assert read_persistence_disposition(v) == "persist"


def test_persistence_disposition_boundary_is_inclusive_of_zero():
    assert read_persistence_disposition(0.0) == "persist"
    assert read_persistence_disposition(-0.0001) == "avoid"


# ---------------------------------------------------------------------
# 4. No cross-domain generalization.
# ---------------------------------------------------------------------
def test_no_cross_domain_generalization():
    inner, resident_can = _fresh()
    chess = mint_domain_self_efficacy(inner, resident_can, "chess")
    for _ in range(5):
        record_self_efficacy_incident(inner, chess, success=True)
    chess_ef = inner.node(chess)["attrs"]["external_field"]
    assert chess_ef > 0.0

    monopoly = mint_domain_self_efficacy(inner, resident_can, "monopoly")
    assert inner.node(monopoly)["attrs"]["external_field"] == pytest.approx(0.0)


def test_mint_domain_self_efficacy_has_no_coupling_edges():
    """Unlike mint_domain_self_worth, this Concept has NO causal_influence
    edges -- fresh and uncoupled, per Bandura's task-specificity claim."""
    inner, resident_can = _fresh()
    concept = mint_domain_self_efficacy(inner, resident_can, "chess")
    assert list(inner.neighbours(concept, "causal_influence")) == []


# ---------------------------------------------------------------------
# 5. Wires the confirmed-dead AffectiveState.competence field.
# ---------------------------------------------------------------------
def test_sync_writes_affective_state_competence():
    inner, resident_can = _fresh()
    concept = mint_domain_self_efficacy(inner, resident_can, "chess")
    for _ in range(3):
        record_self_efficacy_incident(inner, concept, success=True)
    efficacy_value = inner.node(concept)["attrs"]["external_field"]

    affect = inner.add_node("AffectiveState", {"competence": 0.0})
    assert inner.node(affect)["attrs"]["competence"] == 0.0
    synced = sync_competence_to_affective_state(inner, affect, concept)
    assert synced == pytest.approx(efficacy_value)
    assert inner.node(affect)["attrs"]["competence"] == pytest.approx(efficacy_value)


def test_mint_domain_self_efficacy_is_idempotent():
    inner, resident_can = _fresh()
    c1 = mint_domain_self_efficacy(inner, resident_can, "chess")
    c2 = mint_domain_self_efficacy(inner, resident_can, "chess")
    assert c1 == c2


def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/affective_state_core.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
