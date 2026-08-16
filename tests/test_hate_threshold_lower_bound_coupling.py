"""Regression for HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md --
crystallize_hate's gate compares confirm_streak against an EFFECTIVE
threshold (HATE_STABILITY_THRESHOLD/(1+arousal_level)), not the bare
base constant.
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
# 1. At zero arousal, effective_threshold equals the base constant
#    (backward compatibility).
# ---------------------------------------------------------------------
def test_zero_arousal_gate_matches_the_base_constant_exactly():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    inner.set_attr(pat, "confirm_streak", float(HATE_STABILITY_THRESHOLD) - 0.1)
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert not bool(inner.node(pat)["attrs"]["crystallized"])

    inner.set_attr(pat, "confirm_streak", float(HATE_STABILITY_THRESHOLD))
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert bool(inner.node(pat)["attrs"]["crystallized"])


# ---------------------------------------------------------------------
# 2. Elevated arousal lowers effective_threshold below the base constant
#    -- the SAME confirm_streak that does not crystallize cold DOES
#    crystallize once aroused.
# ---------------------------------------------------------------------
def test_elevated_arousal_crystallizes_a_streak_that_would_not_crystallize_cold():
    streak_value = float(HATE_STABILITY_THRESHOLD) - 1.0  # below base threshold

    inner_cold, mt_cold = _fresh("cold")
    pat_cold = mint_target_pattern(inner_cold, mt_cold, "Alex")
    inner_cold.set_attr(pat_cold, "confirm_streak", streak_value)
    inner_cold.force_all_dirty()
    inner_cold.run_rules(3000)
    assert not bool(inner_cold.node(pat_cold)["attrs"]["crystallized"])

    inner_hot, mt_hot = _fresh("hot")
    pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
    arousal_hot = next(iter(inner_hot.neighbours(pat_hot, "tracks_arousal")))
    inner_hot.set_attr(arousal_hot, "level", 1.0)  # effective_threshold = 3/(1+1) = 1.5
    inner_hot.set_attr(pat_hot, "confirm_streak", streak_value)  # == 2.0 >= 1.5
    inner_hot.force_all_dirty()
    inner_hot.run_rules(3000)
    assert bool(inner_hot.node(pat_hot)["attrs"]["crystallized"])


# ---------------------------------------------------------------------
# 3. Compounding, measured honestly: with BOTH couplings, crystallization
#    happens in fewer incidents than the increment coupling would need
#    alone (computed by simulating the same streak-growth recurrence
#    against the FIXED base threshold instead of the effective one).
# ---------------------------------------------------------------------
def test_both_couplings_crystallize_sooner_than_increment_coupling_alone():
    # pure-arithmetic simulation of the SAME streak/arousal recurrence
    # this arc's own record_hate_incident implements, to get an
    # increment-coupling-ALONE baseline without needing a second seed
    # version.
    def simulate(compare_to_effective_threshold):
        streak = 0.0
        level = 0.0
        for i in range(20):
            if i == 0:
                pass  # first_encounter: streak stays 0, no increment
            else:
                increment = 1.0 + level
                streak += increment
            threshold = (HATE_STABILITY_THRESHOLD / (1.0 + level)
                         if compare_to_effective_threshold else HATE_STABILITY_THRESHOLD)
            level = level * AROUSAL_DECAY + AROUSAL_INTENSITY
            if i > 0 and streak >= threshold:
                return i + 1  # incidents consumed, 1-indexed count
        raise AssertionError("simulation did not crystallize")

    both_couplings = simulate(compare_to_effective_threshold=True)
    increment_alone = simulate(compare_to_effective_threshold=False)
    assert both_couplings < increment_alone

    # cross-check the simulation against the REAL engine run
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    live_count = 0
    for _ in range(20):
        r = record_hate_incident(inner, mt, pat, negative=True)
        live_count += 1
        if r["crystallized_this_call"]:
            break
    assert live_count == both_couplings


# ---------------------------------------------------------------------
# 4. Per-target isolation holds with the threshold-lowering coupling.
# ---------------------------------------------------------------------
def test_threshold_lowering_does_not_leak_across_targets():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    arousal_alex = next(iter(inner.neighbours(alex, "tracks_arousal")))
    inner.set_attr(arousal_alex, "level", 2.0)  # effective_threshold = 1.0
    inner.set_attr(alex, "confirm_streak", 1.5)
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert bool(inner.node(alex)["attrs"]["crystallized"])

    sam = mint_target_pattern(inner, mt, "Sam")
    inner.set_attr(sam, "confirm_streak", 1.5)  # same streak, Sam's OWN zero arousal
    inner.force_all_dirty()
    inner.run_rules(3000)
    assert not bool(inner.node(sam)["attrs"]["crystallized"])


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
