"""Regression for the self-complexity-weighted coupling in
domains/can_self_worth_bridge.py::mint_domain_self_worth -- coupling
strength is relative to how many domains the resident has already
differentiated (Linville 1985/1987), not a flat constant. See
docs/research/psychology_affect/SELF_COMPLEXITY_COUPLING_PREREG.md.
"""
from __future__ import annotations

import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_can_seed, find_or_build_resident_can, mint_domain_self_worth,
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
    return inner


# ---------------------------------------------------------------------
# 1. Prediction 1 -- a resident's FIRST domain is unaffected: full
#    base_coupling, byte-identical to the pre-audit 0.6 behavior.
# ---------------------------------------------------------------------
def test_first_domain_gets_full_base_coupling():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "public_speaking")
    assert inner.node(domain)["attrs"]["state"] == 1.0  # projects global fully


# ---------------------------------------------------------------------
# 2. Prediction 2 -- a resident's SECOND domain couples more weakly and,
#    given the already-measured discrete threshold, lands neutral.
# ---------------------------------------------------------------------
def test_second_domain_couples_more_weakly_and_lands_neutral():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    mint_domain_self_worth(inner, resident, "public_speaking")
    second = mint_domain_self_worth(inner, resident, "chess")
    assert inner.node(second)["attrs"]["state"] == 0.0


# ---------------------------------------------------------------------
# 3. Prediction 3 -- once triggered, buffering persists as more domains
#    accumulate (the denominator only grows).
# ---------------------------------------------------------------------
def test_buffering_persists_across_many_existing_domains():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    for name in ("public_speaking", "chess", "cooking", "gardening"):
        mint_domain_self_worth(inner, resident, name)
    fifth = mint_domain_self_worth(inner, resident, "painting")
    assert inner.node(fifth)["attrs"]["state"] == 0.0


# ---------------------------------------------------------------------
# 4. Prediction 4 -- re-minting an EXISTING domain does not recompute or
#    perturb its coupling/state.
# ---------------------------------------------------------------------
def test_reminting_an_existing_domain_does_not_perturb_it():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    first = mint_domain_self_worth(inner, resident, "public_speaking")
    assert inner.node(first)["attrs"]["state"] == 1.0
    mint_domain_self_worth(inner, resident, "chess")  # a second domain now exists
    first_again = mint_domain_self_worth(inner, resident, "public_speaking")
    assert first_again == first
    assert inner.node(first_again)["attrs"]["state"] == 1.0  # unperturbed


# ---------------------------------------------------------------------
# 5. No seed was edited (task charter) -- this is a Python-side change
#    only, per the PREREG's own registered scope decision.
# ---------------------------------------------------------------------
def test_no_seed_was_edited():
    import subprocess
    import pytest
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/rule_dispute_escalation.json",
             "seeds/self_conscious_emotions.json",
             "seeds/rule_dispute_self_conscious_bridge.json",
             "seeds/dispute_severity_from_beliefs.json",
             "seeds/peer_comparison.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
