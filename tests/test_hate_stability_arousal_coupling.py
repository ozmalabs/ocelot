"""Regression for HATE_STABILITY_AROUSAL_COUPLING_PREREG.md -- a
confirming incident's own contribution to confirm_streak is scaled by
1+arousal_level, not a bare +1.
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
# 1. At zero arousal, the increment is unchanged (backward compatibility).
# ---------------------------------------------------------------------
def test_first_confirming_increment_at_baseline_arousal_is_one_plus_first_incident_intensity():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    first = record_hate_incident(inner, mt, pat, negative=True)
    assert first["arousal_level"] == pytest.approx(AROUSAL_INTENSITY)
    confirm = record_hate_incident(inner, mt, pat, negative=True)
    # the very first confirming incident's own increment reads arousal as
    # left by incident 0 -- 1 + AROUSAL_INTENSITY, not a bare 1.
    assert confirm["confirm_streak"] == pytest.approx(1.0 + AROUSAL_INTENSITY)


# ---------------------------------------------------------------------
# 2. The same sequence of confirming incidents crystallizes in fewer
#    incidents when arousal has built up (hot vs cold, using RAW
#    confirm_streak growth rather than the removal-alpha side effect
#    HATE_PASSION_COUPLING's own test already covers).
# ---------------------------------------------------------------------
def test_hot_run_reaches_the_threshold_in_fewer_incidents_than_a_cold_run():
    inner_hot, mt_hot = _fresh("mt_hot")
    pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
    hot_incidents_to_crystallize = 0
    for _ in range(10):
        r = record_hate_incident(inner_hot, mt_hot, pat_hot, negative=True)
        hot_incidents_to_crystallize += 1
        if r["crystallized_this_call"]:
            break

    inner_cold, mt_cold = _fresh("mt_cold")
    pat_cold = mint_target_pattern(inner_cold, mt_cold, "Sam")
    arousal_node = next(iter(inner_cold.neighbours(pat_cold, "tracks_arousal")))
    cold_incidents_to_crystallize = 0
    for _ in range(10):
        r = record_hate_incident(inner_cold, mt_cold, pat_cold, negative=True)
        cold_incidents_to_crystallize += 1
        if r["crystallized_this_call"]:
            break
        for _ in range(20):
            level = inner_cold.node(arousal_node)["attrs"]["level"]
            inner_cold.set_attr(arousal_node, "level", level * AROUSAL_DECAY)

    assert hot_incidents_to_crystallize < cold_incidents_to_crystallize
    # the cold run, with arousal decayed away each time, falls back to
    # the pre-coupling pace: HATE_STABILITY_THRESHOLD+1 incidents.
    assert cold_incidents_to_crystallize == HATE_STABILITY_THRESHOLD + 1


# ---------------------------------------------------------------------
# 3. The increment matches the formula exactly.
# ---------------------------------------------------------------------
def test_streak_increment_matches_the_formula_exactly():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    prev = record_hate_incident(inner, mt, pat, negative=True)
    streak_before = prev["confirm_streak"]
    r = record_hate_incident(inner, mt, pat, negative=True)
    expected_increment = 1.0 + prev["arousal_level"]
    assert r["confirm_streak"] == pytest.approx(streak_before + expected_increment)


# ---------------------------------------------------------------------
# 4. Per-target isolation holds with the streak coupling wired in.
# ---------------------------------------------------------------------
def test_streak_coupling_does_not_leak_across_targets():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    for _ in range(3):
        record_hate_incident(inner, mt, alex, negative=True)
    alex_streak = inner.node(alex)["attrs"]["confirm_streak"]
    assert alex_streak > HATE_STABILITY_THRESHOLD  # already well past, arousal-amplified

    sam = mint_target_pattern(inner, mt, "Sam")
    record_hate_incident(inner, mt, sam, negative=True)  # first_encounter, streak 0
    r = record_hate_incident(inner, mt, sam, negative=True)
    # Sam's own streak increment uses Sam's own (cold-start) arousal, not
    # Alex's -- exactly 1+AROUSAL_INTENSITY, unaffected by Alex's build-up.
    assert r["confirm_streak"] == pytest.approx(1.0 + AROUSAL_INTENSITY)


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
