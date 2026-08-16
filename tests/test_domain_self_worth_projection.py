"""Regression for domains/can_self_worth_bridge.py's mint_domain_self_worth
-- domain-scoped self-worth as PROJECTION-THEN-DECOUPLING (Rotter 1954's
generalized-vs-specific-expectancy mechanism), plus belief plasticity as a
personality trait (Dweck's fixed vs growth mindset). See
docs/research/psychology_affect/DOMAIN_SELF_WORTH_PROJECTION_PREREG.md.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_can_seed, find_or_build_resident_can, mint_domain_self_worth,
    record_incident_outcome,
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
# 1. Prediction 1 -- a brand-new domain projects the current global state.
# ---------------------------------------------------------------------
def test_new_domain_projects_the_current_global_self_worth():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    assert resident["self_worth"] == 1.0
    domain = mint_domain_self_worth(inner, resident, "public_speaking")
    assert inner.node(domain)["attrs"]["state"] == 1.0


# ---------------------------------------------------------------------
# 2. Prediction 2 -- domain-specific evidence decouples the domain belief;
#    the global belief is never touched by domain-targeted evidence.
# ---------------------------------------------------------------------
def test_domain_specific_evidence_decouples_without_touching_global():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "public_speaking")
    for _ in range(5):
        record_incident_outcome(inner, {"self_worth": domain}, standard_met=False,
                                attribution_locus="global_self", alpha=0.3)
    assert inner.node(domain)["attrs"]["state"] == -1.0
    assert inner.node(resident["concepts"]["self_worth"])["attrs"]["state"] == 1.0


# ---------------------------------------------------------------------
# 3. Prediction 3 -- two different domains for the SAME resident hold
#    DIFFERENT beliefs simultaneously, independent of one another. Since
#    SELF_COMPLEXITY_COUPLING_PREREG.md, a resident's SECOND domain
#    couples more weakly to global (Linville 1985/1987 self-complexity
#    buffering) and, given this engine's own already-measured discrete
#    threshold, lands NEUTRAL rather than mirroring global -- registered
#    and expected, not a regression.
# ---------------------------------------------------------------------
def test_two_domains_hold_independent_beliefs_simultaneously():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    speaking = mint_domain_self_worth(inner, resident, "public_speaking")
    for _ in range(5):
        record_incident_outcome(inner, {"self_worth": speaking}, standard_met=False,
                                attribution_locus="global_self", alpha=0.3)
    chess = mint_domain_self_worth(inner, resident, "chess")
    assert inner.node(speaking)["attrs"]["state"] == -1.0
    # chess is this resident's SECOND domain (existing_domain_count=1 at
    # mint time) -- coupling_weight=0.6/2=0.3, below the ~0.366 discrete
    # threshold, so it lands neutral rather than projecting global=1.0
    # (SELF_COMPLEXITY_COUPLING_PREREG.md prediction 2).
    assert inner.node(chess)["attrs"]["state"] == 0.0
    assert inner.node(resident["concepts"]["self_worth"])["attrs"]["state"] == 1.0


# ---------------------------------------------------------------------
# 4. Prediction 4 -- idempotent minting: a second call reuses the drifted
#    Concept, does not reset it.
# ---------------------------------------------------------------------
def test_minting_is_idempotent_and_preserves_drift():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "public_speaking")
    for _ in range(5):
        record_incident_outcome(inner, {"self_worth": domain}, standard_met=False,
                                attribution_locus="global_self", alpha=0.3)
    drifted = inner.node(domain)["attrs"]["state"]
    domain_again = mint_domain_self_worth(inner, resident, "public_speaking")
    assert domain_again == domain
    assert inner.node(domain_again)["attrs"]["state"] == drifted == -1.0


# ---------------------------------------------------------------------
# 5. Prediction 5 (REVISED live -- see PREREG Sec4) -- the coupling weight
#    has a hard THRESHOLD (can_native_update_3state's own sum*temperature
#    > 0.549 crossing), not a proportional pull. Below ~0.366 (at this
#    resident's temperature=1.5) the domain Concept lands NEUTRAL, not a
#    weaker projection of the global sign; at/above ~0.37 it crosses fully.
# ---------------------------------------------------------------------
def test_coupling_weight_below_threshold_lands_neutral_not_weak_projection():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "cooking", base_coupling=0.3)
    assert inner.node(domain)["attrs"]["state"] == 0.0


def test_coupling_weight_above_threshold_projects_the_global_sign():
    inner = _fresh()
    resident = find_or_build_resident_can(inner, CONFIDENT)
    domain = mint_domain_self_worth(inner, resident, "cooking", base_coupling=0.4)
    assert inner.node(domain)["attrs"]["state"] == 1.0


# ---------------------------------------------------------------------
# 6. Prediction 6 -- belief plasticity is a personality trait: the SAME
#    incidents produce strictly less drift for a low-alpha (fixed mindset)
#    resident than a high-alpha (growth mindset) one.
# ---------------------------------------------------------------------
def test_belief_plasticity_is_a_personality_trait_not_a_constant():
    rigid_inner = _fresh()
    rigid_resident = find_or_build_resident_can(rigid_inner, CONFIDENT)
    rigid_domain = mint_domain_self_worth(rigid_inner, rigid_resident, "public_speaking")

    flexible_inner = _fresh()
    flexible_resident = find_or_build_resident_can(flexible_inner, CONFIDENT)
    flexible_domain = mint_domain_self_worth(flexible_inner, flexible_resident, "public_speaking")

    for _ in range(8):
        record_incident_outcome(rigid_inner, {"self_worth": rigid_domain},
                                standard_met=False, attribution_locus="global_self",
                                alpha=0.05)
        record_incident_outcome(flexible_inner, {"self_worth": flexible_domain},
                                standard_met=False, attribution_locus="global_self",
                                alpha=0.5)

    rigid_final = inner_state = rigid_inner.node(rigid_domain)["attrs"]["state"]
    flexible_final = flexible_inner.node(flexible_domain)["attrs"]["state"]
    assert rigid_final > flexible_final  # rigid stayed closer to the original +1
    assert rigid_final == 0.0  # barely dented after 8 incidents
    assert flexible_final == -1.0  # fully flipped


# ---------------------------------------------------------------------
# 7. No seed was edited (task charter).
# ---------------------------------------------------------------------
def test_no_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/rule_dispute_escalation.json",
             "seeds/self_conscious_emotions.json",
             "seeds/rule_dispute_self_conscious_bridge.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
