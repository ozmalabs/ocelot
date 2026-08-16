"""Regression for HATE_PASSION_COUPLING_PREREG.md -- removal_desire's
alpha at hate crystallization coupled to the shared TargetArousal pool
(shared_arousal.mint_target_arousal), Sternberg 2003's passion component.
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
# 1/2. Coupled removal-desire evidence exceeds base_alpha, exactly
#      matching the formula.
# ---------------------------------------------------------------------
def test_crystallizing_removal_alpha_is_amplified_by_built_up_arousal():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    results = [record_hate_incident(inner, mt, pat, negative=True, base_alpha=0.3)
               for _ in range(HATE_STABILITY_THRESHOLD + 1)]
    crystallizing = results[HATE_STABILITY_THRESHOLD]
    assert crystallizing["crystallized_this_call"]
    assert crystallizing["effective_removal_alpha"] is not None
    assert crystallizing["effective_removal_alpha"] > 0.3

    # exact formula: base_alpha * (1 + arousal_level BEFORE this incident's
    # own update) -- reconstruct the pre-incident level from the 3 prior
    # incidents' own arousal contributions.
    level = 0.0
    for _ in range(HATE_STABILITY_THRESHOLD):
        level = level * AROUSAL_DECAY + AROUSAL_INTENSITY
    expected_alpha = 0.3 * (1.0 + level)
    assert crystallizing["effective_removal_alpha"] == pytest.approx(expected_alpha)


# ---------------------------------------------------------------------
# 3. Hot vs cold crystallization -- the identical structural event
#    (confirm_streak crossing threshold) produces a markedly different
#    removal alpha depending on whether arousal was allowed to decay.
# ---------------------------------------------------------------------
def test_hot_crystallization_exceeds_cold_crystallization():
    # hot: back-to-back incidents, arousal compounds
    inner_hot, mt_hot = _fresh("mt_hot")
    pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
    hot_results = [record_hate_incident(inner_hot, mt_hot, pat_hot, negative=True)
                   for _ in range(HATE_STABILITY_THRESHOLD + 1)]
    hot_alpha = hot_results[HATE_STABILITY_THRESHOLD]["effective_removal_alpha"]

    # cold: manually decay arousal to near-zero between each incident,
    # simulating a long gap -- the formula itself is pure arithmetic
    # (level*decay), applied here directly to the tracked arousal node,
    # the same "tick with no incident" shape SHARED_AROUSAL_EXCITATION_
    # TRANSFER_RESULTS.md's own prediction 3 already used.
    inner_cold, mt_cold = _fresh("mt_cold")
    pat_cold = mint_target_pattern(inner_cold, mt_cold, "Sam")
    arousal_node = next(iter(inner_cold.neighbours(pat_cold, "tracks_arousal")))
    cold_results = []
    for _ in range(HATE_STABILITY_THRESHOLD + 1):
        r = record_hate_incident(inner_cold, mt_cold, pat_cold, negative=True)
        cold_results.append(r)
        for _ in range(20):
            level = inner_cold.node(arousal_node)["attrs"]["level"]
            inner_cold.set_attr(arousal_node, "level", level * AROUSAL_DECAY)
    cold_alpha = cold_results[HATE_STABILITY_THRESHOLD]["effective_removal_alpha"]

    assert hot_alpha > cold_alpha
    assert cold_alpha == pytest.approx(0.3, abs=0.01)


# ---------------------------------------------------------------------
# 4. Per-target isolation still holds with arousal coupling wired in.
# ---------------------------------------------------------------------
def test_arousal_coupling_does_not_leak_across_targets():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    for _ in range(HATE_STABILITY_THRESHOLD):
        record_hate_incident(inner, mt, alex, negative=True)
    alex_arousal = inner.node(next(iter(inner.neighbours(alex, "tracks_arousal"))))["attrs"]["level"]
    assert alex_arousal > 0.0

    sam = mint_target_pattern(inner, mt, "Sam")
    r = record_hate_incident(inner, mt, sam, negative=True)
    assert r["arousal_level"] == pytest.approx(AROUSAL_INTENSITY)


# ---------------------------------------------------------------------
# Non-crystallizing incidents still contribute to arousal but apply no
# removal evidence.
# ---------------------------------------------------------------------
def test_non_crystallizing_incidents_build_arousal_without_removal_evidence():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = record_hate_incident(inner, mt, pat, negative=True)
    assert not r["crystallized_this_call"]
    assert r["effective_removal_alpha"] is None
    assert r["arousal_level"] > 0.0


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
