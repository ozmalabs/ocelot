"""Regression for ENVY_PREREG.md -- Smith & Kim (2007)'s comparative
envy, Van de Ven, Zeelenberg & Pieters (2009)'s benign-vs-malicious
split. Reuses relative_self_worth entirely unchanged; the only new piece
is the deservingness appraisal.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_peer_comparison_seed, find_or_build_resident_can,
    mint_domain_self_worth, mint_peer_comparison_context,
    read_relative_self_worth, record_peer_observation,
)
from domains.envy import (
    mint_domain_deservingness_belief, read_envy, record_deservingness_incident,
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
    ensure_peer_comparison_seed(inner)
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    return inner, resident_can


def _disadvantage(inner, resident_can, domain):
    """Mints the domain + peer comparison, and pushes peer_log_odds up
    (5 peers doing well) so relative_self_worth reads negative."""
    domain_concept = mint_domain_self_worth(inner, resident_can, domain)
    peer_ctx = mint_peer_comparison_context(inner, domain_concept)
    for _ in range(5):
        record_peer_observation(inner, peer_ctx, peer_did_well=True)
    return domain_concept


# ---------------------------------------------------------------------
# 1. No disadvantage means no envy, regardless of deservingness.
# ---------------------------------------------------------------------
def test_no_disadvantage_means_no_envy_regardless_of_deservingness():
    assert read_envy(1.0, -5.0) == "none"
    assert read_envy(0.0, -5.0) == "none"


# ---------------------------------------------------------------------
# 2. A deserved disadvantage produces benign envy.
# ---------------------------------------------------------------------
def test_deserved_disadvantage_is_benign():
    inner, resident_can = _fresh()
    domain_concept = _disadvantage(inner, resident_can, "chess")
    rsw = read_relative_self_worth(inner, domain_concept)
    assert rsw < 0.0

    deserv = mint_domain_deservingness_belief(inner, resident_can, "chess")
    d = record_deservingness_incident(inner, deserv, deserved=True)
    assert read_envy(rsw, d) == "benign"


# ---------------------------------------------------------------------
# 3. An undeserved disadvantage produces malicious envy.
# ---------------------------------------------------------------------
def test_undeserved_disadvantage_is_malicious():
    inner, resident_can = _fresh()
    domain_concept = _disadvantage(inner, resident_can, "chess")
    rsw = read_relative_self_worth(inner, domain_concept)
    assert rsw < 0.0

    deserv = mint_domain_deservingness_belief(inner, resident_can, "chess")
    d = record_deservingness_incident(inner, deserv, deserved=False)
    assert read_envy(rsw, d) == "malicious"


# ---------------------------------------------------------------------
# 4. The deservingness belief alone flips the verdict, holding
#    relative_self_worth fixed.
# ---------------------------------------------------------------------
def test_deservingness_alone_flips_benign_to_malicious():
    rsw = -0.791759469228055  # a fixed, realistic disadvantage value
    assert read_envy(rsw, deservingness_value=0.3) == "benign"
    assert read_envy(rsw, deservingness_value=-0.3) == "malicious"


# ---------------------------------------------------------------------
# 5. Domain isolation for the deservingness belief.
# ---------------------------------------------------------------------
def test_deservingness_belief_is_domain_isolated():
    inner, resident_can = _fresh()
    chess_deserv = mint_domain_deservingness_belief(inner, resident_can, "chess")
    for _ in range(3):
        record_deservingness_incident(inner, chess_deserv, deserved=False)
    chess_value = inner.node(chess_deserv)["attrs"]["external_field"]
    assert chess_value < 0.0

    football_deserv = mint_domain_deservingness_belief(inner, resident_can, "football")
    assert inner.node(football_deserv)["attrs"]["external_field"] == pytest.approx(0.0)


def test_mint_domain_deservingness_belief_is_idempotent():
    inner, resident_can = _fresh()
    d1 = mint_domain_deservingness_belief(inner, resident_can, "chess")
    d2 = mint_domain_deservingness_belief(inner, resident_can, "chess")
    assert d1 == d2


def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json", "seeds/peer_comparison.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
