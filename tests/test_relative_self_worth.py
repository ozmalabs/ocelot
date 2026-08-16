"""Regression for seeds/peer_comparison.json + domains/can_self_worth_
bridge.py's peer-comparison functions -- self-worth as RELATIVE (own state
minus a log-odds social-comparison baseline), not absolute. See
docs/research/psychology_affect/RELATIVE_SELF_WORTH_PREREG.md.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_peer_comparison_seed, find_or_build_resident_can, mint_domain_self_worth,
    mint_peer_comparison_context, read_relative_self_worth, record_peer_observation,
)
from domains.rule_dispute_full_pipeline import run_rule_dispute

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}


def _fresh_domain():
    s = sr.Substrate()
    inner = s._inner
    ensure_peer_comparison_seed(inner)
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "public_speaking")
    ctx = mint_peer_comparison_context(inner, domain)
    return inner, domain, ctx


# ---------------------------------------------------------------------
# 1. Prediction 1 -- zero peer observations: the fictional midpoint is
#    genuinely neutral, relative_self_worth == domain state.
# ---------------------------------------------------------------------
def test_zero_observations_is_a_genuinely_neutral_midpoint():
    inner, domain, ctx = _fresh_domain()
    assert read_relative_self_worth(inner, domain) == inner.node(domain)["attrs"]["state"] == 1.0


# ---------------------------------------------------------------------
# 2. Prediction 2 -- a highlight-reel-skewed sample pushes peer_log_odds
#    strictly positive, at the exact measured magnitude.
# ---------------------------------------------------------------------
def test_highlight_reel_skew_produces_the_measured_log_odds():
    inner, domain, ctx = _fresh_domain()
    for _ in range(8):
        record_peer_observation(inner, ctx, peer_did_well=True)
    record_peer_observation(inner, ctx, peer_did_well=False)
    relative = read_relative_self_worth(inner, domain)
    own_state = inner.node(domain)["attrs"]["state"]
    peer_log_odds = own_state - relative
    assert peer_log_odds == pytest.approx(1.5040773967762742)


# ---------------------------------------------------------------------
# 3. Prediction 3 (the user's own claim, directly tested) -- self-worth
#    can drop with ZERO change to the resident's own track record, purely
#    from observing peers doing well.
# ---------------------------------------------------------------------
def test_self_worth_drops_without_dropping():
    inner, domain, ctx = _fresh_domain()
    own_state_before = inner.node(domain)["attrs"]["state"]
    relative_before = read_relative_self_worth(inner, domain)
    for _ in range(8):
        record_peer_observation(inner, ctx, peer_did_well=True)
    record_peer_observation(inner, ctx, peer_did_well=False)
    own_state_after = inner.node(domain)["attrs"]["state"]
    relative_after = read_relative_self_worth(inner, domain)
    assert own_state_after == own_state_before  # untouched -- no incident occurred
    assert relative_after < relative_before  # yet relative self-worth dropped


# ---------------------------------------------------------------------
# 4. Prediction 4 -- the reverse holds too: observing peers struggling
#    RAISES relative self-worth above the domain's own raw state.
# ---------------------------------------------------------------------
def test_self_worth_rises_without_rising_when_peers_struggle():
    inner, domain, ctx = _fresh_domain()
    own_state_before = inner.node(domain)["attrs"]["state"]
    for _ in range(8):
        record_peer_observation(inner, ctx, peer_did_well=False)
    record_peer_observation(inner, ctx, peer_did_well=True)
    own_state_after = inner.node(domain)["attrs"]["state"]
    relative_after = read_relative_self_worth(inner, domain)
    assert own_state_after == own_state_before
    assert relative_after > own_state_after


# ---------------------------------------------------------------------
# 5. Prediction 5 -- end to end: a highlight-reel-skewed peer baseline,
#    recorded BEFORE the resident's own first incident, changes the full
#    pipeline's attribution/emotion decision for that first dispute --
#    the same resident, same event, different verdict, purely from what
#    they'd observed about others beforehand.
# ---------------------------------------------------------------------
def test_peer_skew_before_the_first_incident_changes_the_pipeline_verdict():
    BOB = {"name": "Bob", "index": 0, "params": {
        "resolution_bins": 8, "arousal": 0.2,
        "prior_world_safe": 0.6, "prior_self_worth": 0.9,
        "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
        "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
        "mood_bias": 0.3,
    }}

    s1 = sr.Substrate()
    inner1 = s1._inner
    unskewed = run_rule_dispute(
        inner1, claimant=BOB, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])

    s2 = sr.Substrate()
    inner2 = s2._inner
    from domains.rule_dispute_full_pipeline import ensure_pipeline_seeds
    ensure_pipeline_seeds(inner2)
    resident = find_or_build_resident_can(inner2, BOB)
    domain2 = mint_domain_self_worth(inner2, resident, "monopoly_rules")
    ctx2 = mint_peer_comparison_context(inner2, domain2)
    for _ in range(8):
        record_peer_observation(inner2, ctx2, peer_did_well=True)
    skewed = run_rule_dispute(
        inner2, claimant=BOB, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])

    assert unskewed["attribution_locus"] == "specific_act"
    assert unskewed["emotion"] == "guilt"
    assert skewed["attribution_locus"] == "global_self"
    assert skewed["emotion"] == "shame"


# ---------------------------------------------------------------------
# 6. Peer comparison context minting is idempotent.
# ---------------------------------------------------------------------
def test_peer_comparison_context_minting_is_idempotent():
    inner, domain, ctx = _fresh_domain()
    ctx2 = mint_peer_comparison_context(inner, domain)
    assert ctx2 == ctx


# ---------------------------------------------------------------------
# 7. can_native_reimplementation.json is untouched (task charter).
# ---------------------------------------------------------------------
def test_can_native_reimplementation_seed_is_untouched():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "seeds/can_native_reimplementation.json"],
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
    import json
    d = json.load(open("seeds/peer_comparison.json"))
    assert d["depends_on"] == ["can_native_reimplementation"]
    assert len(d["productions"]) == 2
    by_edge = {p["edge_type"]: p for p in d["productions"]}
    assert by_edge["has_peer_comparison"]["src"]["type"] == "Concept"
    assert by_edge["has_peer_comparison"]["tgt"]["type"] == "PeerComparisonContext"
    assert by_edge["has_observation"]["src"]["type"] == "PeerComparisonContext"
    assert by_edge["has_observation"]["tgt"]["type"] == "PeerObservation"
