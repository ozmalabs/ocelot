"""Regression for domains/rule_dispute_full_pipeline.py -- the ONE real,
callable, end-to-end entry point composing severity-as-residual, dispute
escalation, the self-conscious bridge, self-conscious emotion appraisal,
and real/persistent/domain-scoped CAN self_worth. See
docs/research/psychology_affect/WIRE_IN_PREREG.md.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.rule_dispute_full_pipeline import ensure_pipeline_seeds, run_rule_dispute

BOB = {"name": "Bob", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def _fresh():
    return sr.Substrate()._inner


# ---------------------------------------------------------------------
# 1. Prediction 1 -- end to end, one call, real decisions all the way
#    through.
# ---------------------------------------------------------------------
def test_one_call_produces_a_full_decided_trace():
    inner = _fresh()
    r = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert r["dispute_minted"] is True
    assert r["issue_severity"] == pytest.approx(1.0 / 3.0)
    assert r["dispute_outcome"] == "escalate"
    assert r["attribution_locus"] == "specific_act"
    assert r["emotion"] == "guilt"
    assert r["self_worth_before"] == 1.0
    assert r["self_worth_after"] == 0.0


# ---------------------------------------------------------------------
# 2. Prediction 2 -- persistence across repeated REAL disputes, including
#    the emergent guilt -> shame flip as the pattern solidifies.
# ---------------------------------------------------------------------
def test_repeated_real_disputes_drift_self_worth_and_flip_the_emotion():
    inner = _fresh()
    emotions = []
    for _ in range(5):
        r = run_rule_dispute(
            inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", True],
            truth_pred=["pays_pot", "free_parking", False],
            domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
        emotions.append(r["emotion"])
    assert emotions == ["guilt", "guilt", "guilt", "guilt", "shame"]
    assert r["self_worth_after"] == -1.0


# ---------------------------------------------------------------------
# 3. Prediction 3 -- a different domain is untouched by disputes in
#    another domain, for the SAME resident.
# ---------------------------------------------------------------------
def test_a_different_domain_is_unaffected_by_disputes_elsewhere():
    inner = _fresh()
    for _ in range(5):
        run_rule_dispute(
            inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", True],
            truth_pred=["pays_pot", "free_parking", False],
            domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    chess = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["is_a", "queen", "strongest_piece"],
        truth_pred=["is_a", "queen", "strongest_piece"],  # identical -> no dispute
        domain="chess", band_code=0, witnesses=[])
    assert chess["dispute_minted"] is False
    assert chess["self_worth_before"] == chess["self_worth_after"] == 1.0  # projected from global


# ---------------------------------------------------------------------
# 4. Prediction 4 -- identical beliefs mint no dispute, self_worth
#    untouched, through the FULL pipeline (not just the isolated seed).
# ---------------------------------------------------------------------
def test_identical_beliefs_mint_no_dispute_through_the_full_pipeline():
    inner = _fresh()
    r = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["pays_pot", "free_parking", False],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert r["dispute_minted"] is False
    assert r["self_worth_before"] == r["self_worth_after"] == 1.0


# ---------------------------------------------------------------------
# 5. ensure_pipeline_seeds is idempotent.
# ---------------------------------------------------------------------
def test_ensure_pipeline_seeds_is_idempotent():
    inner = _fresh()
    ensure_pipeline_seeds(inner)
    ensure_pipeline_seeds(inner)
    ensure_pipeline_seeds(inner)
    r = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[])
    assert r["dispute_minted"] is True


# ---------------------------------------------------------------------
# 6. Belief plasticity flows through the full pipeline as a real
#    per-claimant trait.
# ---------------------------------------------------------------------
def test_belief_plasticity_flows_through_the_full_pipeline():
    rigid_inner = _fresh()
    flexible_inner = _fresh()
    for _ in range(4):
        rigid = run_rule_dispute(
            rigid_inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", True],
            truth_pred=["pays_pot", "free_parking", False],
            domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0],
            belief_plasticity=0.05)
        flexible = run_rule_dispute(
            flexible_inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", True],
            truth_pred=["pays_pot", "free_parking", False],
            domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0],
            belief_plasticity=0.5)
    assert rigid["self_worth_after"] > flexible["self_worth_after"]


# ---------------------------------------------------------------------
# 7. Only dispute_severity_from_beliefs.json was edited (task charter) --
#    the other three seeds this pipeline composes stay byte-unchanged.
# ---------------------------------------------------------------------
def test_only_the_severity_seed_was_edited_this_rung():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/rule_dispute_escalation.json",
             "seeds/self_conscious_emotions.json",
             "seeds/rule_dispute_self_conscious_bridge.json",
             "seeds/can_native_reimplementation.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
