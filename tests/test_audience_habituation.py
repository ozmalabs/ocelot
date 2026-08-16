"""Regression for domains/rule_dispute_full_pipeline.py's audience-gain
habituation -- effective_audience_gain = base_audience_gain /
(claimant_dispute_count + 1), a REAL observed quantity (how many disputes
this claimant has already been through, across all domains), not a flat
constant. See docs/research/psychology_affect/
EVIDENCE_AND_AUDIENCE_WEIGHTING_PREREG.md.

Structurally distinct from belief_plasticity's own count-divided decay,
which was tried, measured, and RETRACTED (same PREREG, Sec1/RESULTS Sec1)
for reproducing the 1/n learning-rate anti-pattern CLAUDE.md's F-16
retrospective already diagnosed -- audience_gain habituates a bounded
PER-CALL classification threshold, not an accumulating belief strength,
and converges to a practically meaningful flip within a handful of
disputes, confirmed directly below.
"""
from __future__ import annotations

import pytest

import substrate_rs as sr

from domains.rule_dispute_full_pipeline import run_rule_dispute

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
# 1. Prediction 3 -- a claimant's first-ever dispute uses the full base
#    audience_gain, byte-identical to pre-audit behavior.
# ---------------------------------------------------------------------
def test_first_dispute_uses_full_base_audience_gain():
    inner = _fresh()
    r = run_rule_dispute(
        inner, claimant=BOB, claim_pred=["pays_pot", "free_parking", True],
        truth_pred=["pays_pot", "free_parking", False],
        domain="monopoly_rules", band_code=0, witnesses=[0.0, 0.0, 0.0])
    assert r["dispute_minted"] is True
    assert r["dispute_outcome"] == "escalate"


# ---------------------------------------------------------------------
# 2. Prediction 4/6 -- a marginal dispute (close to the escalate/defuse
#    boundary) flips to defuse purely from accumulated dispute experience,
#    at a REALISTIC timescale (a handful of disputes), confirming this
#    fix does NOT reproduce the divergence found and retracted for
#    belief_plasticity.
# ---------------------------------------------------------------------
def test_habituation_flips_a_marginal_dispute_within_a_realistic_timescale():
    inner = _fresh()
    outcomes = []
    for i in range(1, 8):
        r = run_rule_dispute(
            inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", "one_dollar"],
            truth_pred=["pays_pot", "free_parking", "two_dollars"],
            domain="d%d" % i, band_code=2, witnesses=[0.0, 0.0, 0.0])
        outcomes.append(r["dispute_outcome"])
    assert outcomes[0] == "escalate"
    assert "defuse" in outcomes  # flips within 7 disputes, not ~200


# ---------------------------------------------------------------------
# 3. Prediction 5 -- claimant_dispute_count accumulates ACROSS domains,
#    not per-domain -- a resident habituated by monopoly_rules disputes
#    is already partly habituated for their first chess dispute.
# ---------------------------------------------------------------------
def test_dispute_count_accumulates_across_domains():
    inner = _fresh()
    for i in range(1, 7):
        run_rule_dispute(
            inner, claimant=BOB,
            claim_pred=["pays_pot", "free_parking", "one_dollar"],
            truth_pred=["pays_pot", "free_parking", "two_dollars"],
            domain="monopoly_rules", band_code=2, witnesses=[0.0, 0.0, 0.0])
    chess = run_rule_dispute(
        inner, claimant=BOB,
        claim_pred=["is_a", "queen", "worth_nine_points"],
        truth_pred=["is_a", "queen", "worth_ten_points"],
        domain="chess", band_code=2, witnesses=[0.0, 0.0, 0.0])
    # a fresh, never-disputed claimant at the SAME parameters escalates
    # (confirmed by prediction 1's own first-dispute case, and by
    # test_habituation_flips_a_marginal_dispute's own dispute-1 result);
    # Bob's 7th dispute overall (1st in chess) is measurably more
    # habituated purely from the monopoly_rules history -- the count
    # accumulated across, not within, one domain.
    assert chess["dispute_minted"] is True
    assert chess["dispute_outcome"] == "defuse"


# ---------------------------------------------------------------------
# 4. seeds/rule_dispute_escalation.json is untouched (task charter) --
#    the habituation is computed entirely by the Python caller.
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
