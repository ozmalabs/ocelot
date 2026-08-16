"""Regression for SELF_CONSCIOUS_CONSEQUENCE_PREREG.md --
reparative_desire_for/withdrawal_desire_for as guilt/shame's own
motivational consequence, mirroring hate/pity's removal_desire_for/
pity_for pattern.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.can_self_worth_bridge import (
    ensure_can_seed, find_or_build_resident_can, mint_domain_self_worth,
    record_self_conscious_consequence,
)
from domains.rule_dispute_full_pipeline import run_rule_dispute

CONFIDENT = {"name": "Confident", "index": 0, "params": {
    "resolution_bins": 8, "arousal": 0.2,
    "prior_world_safe": 0.6, "prior_self_worth": 0.9,
    "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
    "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
    "mood_bias": 0.3,
}}

BOB = {"name": "Bob", "index": 0, "params": {
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
# 1. Guilt applies evidence to reparative_desire, not withdrawal.
# ---------------------------------------------------------------------
def test_guilt_moves_reparative_desire_only():
    inner = _fresh()
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    mint_domain_self_worth(inner, resident_can, "chess")
    r = record_self_conscious_consequence(inner, resident_can, "chess", emotion="guilt")
    assert r["consequence"] == "reparative"
    assert r["reparative_desire_state"] > 0.0
    assert r["withdrawal_desire_state"] == 0.0


# ---------------------------------------------------------------------
# 2. Shame applies evidence to withdrawal_desire, not reparative.
# ---------------------------------------------------------------------
def test_shame_moves_withdrawal_desire_only():
    inner = _fresh()
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    mint_domain_self_worth(inner, resident_can, "chess")
    r = record_self_conscious_consequence(inner, resident_can, "chess", emotion="shame")
    assert r["consequence"] == "withdrawal"
    assert r["withdrawal_desire_state"] > 0.0
    assert r["reparative_desire_state"] == 0.0


# ---------------------------------------------------------------------
# 3. Every other classification moves neither.
# ---------------------------------------------------------------------
@pytest.mark.parametrize("emotion", ["hubristic_pride", "authentic_pride", "embarrassment", "none"])
def test_other_emotions_move_neither_concept(emotion):
    inner = _fresh()
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    mint_domain_self_worth(inner, resident_can, "chess")
    r = record_self_conscious_consequence(inner, resident_can, "chess", emotion=emotion)
    assert r["consequence"] is None
    assert r["reparative_desire_state"] == 0.0
    assert r["withdrawal_desire_state"] == 0.0


# ---------------------------------------------------------------------
# 4. Repeated guilt in the same domain accumulates.
# ---------------------------------------------------------------------
def test_repeated_guilt_accumulates_on_the_same_concept():
    inner = _fresh()
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    mint_domain_self_worth(inner, resident_can, "chess")
    r1 = record_self_conscious_consequence(inner, resident_can, "chess", emotion="guilt")
    r2 = record_self_conscious_consequence(inner, resident_can, "chess", emotion="guilt")
    assert r2["reparative_desire_state"] > r1["reparative_desire_state"]


# ---------------------------------------------------------------------
# 5. Domain isolation holds.
# ---------------------------------------------------------------------
def test_domain_isolation_holds():
    inner = _fresh()
    resident_can = find_or_build_resident_can(inner, CONFIDENT)
    mint_domain_self_worth(inner, resident_can, "chess")
    mint_domain_self_worth(inner, resident_can, "monopoly")
    record_self_conscious_consequence(inner, resident_can, "chess", emotion="guilt")
    r_other = record_self_conscious_consequence(inner, resident_can, "monopoly", emotion="guilt")
    # monopoly's own reparative_desire starts fresh at base evidence, not
    # inflated by chess's own accumulation.
    assert r_other["reparative_desire_state"] == pytest.approx(0.3)


# ---------------------------------------------------------------------
# 6. Integration: the real guilt -> shame flip scenario
#    (test_rule_dispute_full_pipeline.py's own established fixture)
#    correctly routes reparative_desire for the first 4 incidents, then
#    withdrawal_desire for the 5th.
# ---------------------------------------------------------------------
def test_full_pipeline_routes_reparative_then_withdrawal_as_the_pattern_solidifies():
    inner = sr.Substrate()._inner
    results = []
    for _ in range(5):
        r = run_rule_dispute(
            inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", True],
            truth_pred=["pays_pot", "free_parking", False],
            domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
        results.append(r)
    emotions = [r["emotion"] for r in results]
    assert emotions == ["guilt", "guilt", "guilt", "guilt", "shame"]

    reparative_trace = [r["reparative_desire_state"] for r in results]
    withdrawal_trace = [r["withdrawal_desire_state"] for r in results]
    # reparative_desire climbs across the 4 guilt incidents
    assert reparative_trace[0] > 0.0
    assert reparative_trace[3] > reparative_trace[0]
    # withdrawal_desire stays untouched through the guilt run, then moves
    # exactly on the shame incident
    assert withdrawal_trace[3] == 0.0
    assert withdrawal_trace[4] > 0.0
    # the shame incident does NOT also move reparative_desire further
    assert reparative_trace[4] == reparative_trace[3]


def test_self_conscious_emotions_seed_is_untouched():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "seeds/self_conscious_emotions.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
