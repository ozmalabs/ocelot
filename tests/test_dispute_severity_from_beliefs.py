"""Regression for seeds/dispute_severity_from_beliefs.json -- issue_severity
COMPUTED as the residual between two held beliefs (1-StructSim), replacing
rule_dispute_escalation.json's own caller-supplied scalar. See
docs/research/psychology_affect/DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md for
the registered design (including the live correction to prediction 1).
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/dispute_severity_from_beliefs.json",
]


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    for path in SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    return s


def _dispute_from_beliefs(inner, *, claim_pred, truth_pred, band_code, witnesses,
                          audience_gain=0.15):
    claims = inner.add_node("HeldBelief", {"pred": list(claim_pred)})
    truth = inner.add_node("HeldBelief", {"pred": list(truth_pred)})
    bd = inner.add_node("BeliefDisagreement", {
        "band_code": band_code, "audience_gain": audience_gain})
    inner.add_edge(bd, "claims", claims, {})
    inner.add_edge(bd, "truth", truth, {})
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(bd, "has_witness", w, {})
    inner.run_rules(50)
    bridged = inner.neighbours(bd, "bridged_to")
    if not bridged:
        return {"bd": bd, "minted": False}
    ctx = bridged[0]
    sig = inner.neighbours(ctx, "has_signal")[0]
    return {"bd": bd, "ctx": ctx, "minted": True,
            "issue_severity": inner.node(ctx)["attrs"]["issue_severity"],
            "outcome": inner.node(sig)["attrs"]["outcome"]}


# ---------------------------------------------------------------------
# 1. Prediction 1 (revised live) -- identical beliefs mint no dispute at
#    all, regardless of band_code/witnesses.
# ---------------------------------------------------------------------
def test_identical_beliefs_mint_no_dispute():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", False],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert r["minted"] is False


def test_identical_beliefs_mint_no_dispute_even_with_rival_band():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["is_a", "cat", "mammal"],
        truth_pred=["is_a", "cat", "mammal"],
        band_code=-1, witnesses=[0.0, 0.0])
    assert r["minted"] is False


# ---------------------------------------------------------------------
# 2. Prediction 2 -- a one-slot contradiction produces a moderate, computed
#    residual (2/3 similarity -> 1/3 severity), not the old hand-picked 0.9.
# ---------------------------------------------------------------------
def test_one_slot_contradiction_produces_computed_residual():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert r["minted"] is True
    assert r["issue_severity"] == pytest.approx(1.0 / 3.0)


# ---------------------------------------------------------------------
# 2b. TRIVIAL_DISPUTE_ESCALATION_VERIFICATION.md -- "you can still escalate
#     effectively nothing... finding something to argue about" (user). A
#     minimal, genuinely-nonzero residual (1/3, the smallest StructSim can
#     produce over a 3-slot predication) STILL escalates when relational
#     tension exists (Coser 1956's "non-realistic conflict": the specific
#     object of conflict is substitutable once tension-release is the real
#     driver) -- and this is CORRECT, literature-matching behavior, not the
#     same class of defect the zero-residual fix addressed. Locked in as a
#     standing regression so a future change does not "fix" this away.
# ---------------------------------------------------------------------
def test_minimal_nonzero_residual_still_escalates_under_relational_tension():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", "one_dollar"],
        truth_pred=["pays_pot", "free_parking", "two_dollars"],
        band_code=-1, witnesses=[0.0] * 5)
    assert r["minted"] is True
    assert r["issue_severity"] == pytest.approx(1.0 / 3.0)
    assert r["outcome"] == "escalate"


def test_same_minimal_residual_defuses_under_secure_relationship():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", "one_dollar"],
        truth_pred=["pays_pot", "free_parking", "two_dollars"],
        band_code=5, witnesses=[])
    assert r["minted"] is True
    assert r["issue_severity"] == pytest.approx(1.0 / 3.0)
    assert r["outcome"] == "defuse"


# ---------------------------------------------------------------------
# 3. Prediction 3 -- total disagreement produces the highest severity.
# ---------------------------------------------------------------------
def test_total_disagreement_produces_maximal_severity():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["collects_rent", "boardwalk", "double"],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert r["minted"] is True
    assert r["issue_severity"] == pytest.approx(1.0)


def test_severity_is_graded_not_binary():
    s = _loaded_substrate()
    inner = s._inner
    one_slot = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[])
    total = _dispute_from_beliefs(
        inner, claim_pred=["collects_rent", "boardwalk", "double"],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[])
    assert 0.0 < one_slot["issue_severity"] < total["issue_severity"]


# ---------------------------------------------------------------------
# 4. Prediction 4 -- end to end: computed severity flows through the
#    UNCHANGED rule_dispute_escalation mechanism to a real outcome.
# ---------------------------------------------------------------------
def test_computed_severity_flows_through_to_a_dispute_outcome():
    s = _loaded_substrate()
    inner = s._inner
    close_friends = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=5, witnesses=[])
    strangers = _dispute_from_beliefs(
        inner, claim_pred=["collects_rent", "boardwalk", "double"],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert close_friends["outcome"] == "defuse"
    assert strangers["outcome"] == "escalate"


# ---------------------------------------------------------------------
# 5. Witness carry-over.
# ---------------------------------------------------------------------
def test_witnesses_carry_over_to_the_minted_dispute_context():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.5, 0.9])
    assert r["minted"] is True
    assert len(inner.neighbours(r["ctx"], "has_witness")) == 3


# ---------------------------------------------------------------------
# 6. Idempotency -- no double-mint on repeated run_rules().
# ---------------------------------------------------------------------
def test_bridge_is_idempotent():
    s = _loaded_substrate()
    inner = s._inner
    r = _dispute_from_beliefs(
        inner, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        band_code=0, witnesses=[0.0, 0.0])
    inner.run_rules(50)
    inner.run_rules(50)
    assert len(inner.neighbours(r["bd"], "bridged_to")) == 1
    assert len(inner.neighbours(r["ctx"], "has_witness")) == 2


# ---------------------------------------------------------------------
# 7. rule_dispute_escalation.json is untouched.
# ---------------------------------------------------------------------
def test_rule_dispute_escalation_seed_is_untouched():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "seeds/rule_dispute_escalation.json"],
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
    d = json.load(open("seeds/dispute_severity_from_beliefs.json"))
    assert d["depends_on"] == ["rule_dispute_escalation"]
    assert len(d["productions"]) == 8
    assert d["version"] == "1.1.0"
