"""Regression for HATE_RESET_RESENTMENT_COUPLING_PREREG.md -- a
specific_act's reset of confirm_streak is multiplied by
arousal_level/(1+arousal_level) instead of an unconditional wipe to 0 --
the resentment residue.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import (
    AROUSAL_DECAY, AROUSAL_INTENSITY, HATE_STABILITY_THRESHOLD,
    mint_target_pattern, record_hate_incident,
)


def _fresh(name="test_mt"):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


# ---------------------------------------------------------------------
# 1. At zero arousal, specific_act still fully resets confirm_streak.
# ---------------------------------------------------------------------
def test_zero_arousal_specific_act_is_still_an_exact_full_reset():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    ir = inner.add_node("IncidentReport", {"target": "Alex", "signal": 1.0, "status": "pending"})
    inner.add_edge(mt, "has_incident_report", ir, {})
    inner.add_edge(ir, "about_pattern", pat, {})
    # manually stage the pre-state: a nonzero streak, zero arousal
    inner.set_attr(pat, "confirm_streak", 5.0)
    inner.set_attr(pat, "incident_count", 1)  # not first_encounter
    arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
    inner.set_attr(arousal_node, "level", 0.0)
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert inner.node(pat)["attrs"]["confirm_streak"] == 0.0


# ---------------------------------------------------------------------
# 2. At elevated arousal, specific_act leaves a strictly positive
#    residue -- the resentment case.
# ---------------------------------------------------------------------
def test_elevated_arousal_specific_act_leaves_a_positive_residue():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    ir = inner.add_node("IncidentReport", {"target": "Alex", "signal": 1.0, "status": "pending"})
    inner.add_edge(mt, "has_incident_report", ir, {})
    inner.add_edge(ir, "about_pattern", pat, {})
    inner.set_attr(pat, "confirm_streak", 5.0)
    inner.set_attr(pat, "incident_count", 1)
    arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
    inner.set_attr(arousal_node, "level", 1.0)  # retained_fraction = 0.5
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert inner.node(pat)["attrs"]["confirm_streak"] == pytest.approx(2.5)


# ---------------------------------------------------------------------
# 3. The residue matches the formula exactly, live (not staged).
# ---------------------------------------------------------------------
def test_residue_matches_the_formula_exactly_live():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r0 = record_hate_incident(inner, mt, pat, negative=True)
    r_confirm = record_hate_incident(inner, mt, pat, negative=True)
    r_exception = record_hate_incident(inner, mt, pat, negative=False)
    assert r_exception["attribution_locus"] == "specific_act"
    expected = r_confirm["confirm_streak"] * (
        r_confirm["arousal_level"] / (1.0 + r_confirm["arousal_level"]))
    assert r_exception["confirm_streak"] == pytest.approx(expected)


# ---------------------------------------------------------------------
# 4. A resented pattern's confirm_streak stays strictly ahead of a
#    forgiven one's at a matched number of subsequent confirming
#    incidents -- PREREG Sec3 prediction 4, in the form that survives
#    the already-landed increment + threshold-lowering couplings'
#    compounding (checked empirically before registering: the residue's
#    effect on the INTEGER incident count to crystallize is often
#    invisible, since post-exception arousal alone is frequently already
#    enough regardless of the residue -- the streak VALUE at a matched
#    step is the claim that survives).
# ---------------------------------------------------------------------
def test_resented_pattern_streak_stays_ahead_of_a_forgiven_one():
    pre_streak = 1.0
    # regard_for pre-set well negative so the exception's own positive
    # evidence nudge doesn't flip the SIGN of the held pattern (which
    # would misclassify the subsequent confirming incident as
    # specific_act instead of global_other) -- a genuinely established
    # negative pattern absorbing one positive exception.
    regard_ef = -2.0

    def run(hot_level):
        inner, mt = _fresh("t%s" % hot_level)
        pat = mint_target_pattern(inner, mt, "Alex")
        inner.set_attr(pat, "confirm_streak", pre_streak)
        inner.set_attr(pat, "incident_count", 1)
        regard = next(iter(inner.neighbours(pat, "tracks_concept")))
        inner.set_attr(regard, "external_field", regard_ef)
        arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
        inner.set_attr(arousal_node, "level", hot_level)
        r_exc = record_hate_incident(inner, mt, pat, negative=False)
        assert r_exc["attribution_locus"] == "specific_act"
        r_confirm = record_hate_incident(inner, mt, pat, negative=True)
        assert r_confirm["attribution_locus"] == "global_other"
        return r_exc["confirm_streak"], r_confirm["confirm_streak"]

    hot_residue, hot_after = run(hot_level=1.0)
    cold_residue, cold_after = run(hot_level=0.0)

    assert cold_residue == 0.0  # cold exception is still an exact full reset
    assert hot_residue > 0.0    # hot exception leaves the resentment residue
    assert hot_after > cold_after  # the residue's advantage carries forward


# ---------------------------------------------------------------------
# 5. Per-target isolation holds.
# ---------------------------------------------------------------------
def test_resentment_residue_does_not_leak_across_targets():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    ir = inner.add_node("IncidentReport", {"target": "Alex", "signal": 1.0, "status": "pending"})
    inner.add_edge(mt, "has_incident_report", ir, {})
    inner.add_edge(ir, "about_pattern", alex, {})
    inner.set_attr(alex, "confirm_streak", 5.0)
    inner.set_attr(alex, "incident_count", 1)
    arousal_alex = next(iter(inner.neighbours(alex, "tracks_arousal")))
    inner.set_attr(arousal_alex, "level", 1.0)
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert inner.node(alex)["attrs"]["confirm_streak"] == pytest.approx(2.5)

    sam = mint_target_pattern(inner, mt, "Sam")
    ir2 = inner.add_node("IncidentReport", {"target": "Sam", "signal": 1.0, "status": "pending"})
    inner.add_edge(mt, "has_incident_report", ir2, {})
    inner.add_edge(ir2, "about_pattern", sam, {})
    inner.set_attr(sam, "confirm_streak", 5.0)
    inner.set_attr(sam, "incident_count", 1)
    # Sam's own arousal is untouched (still 0) -- Alex's elevated arousal
    # does not leak into Sam's reset.
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert inner.node(sam)["attrs"]["confirm_streak"] == 0.0


def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/shared_arousal.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
