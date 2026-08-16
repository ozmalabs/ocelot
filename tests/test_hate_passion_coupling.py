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
    # HATE_STABILITY_AROUSAL_COUPLING_PREREG.md Sec2: confirm_streak now
    # increments by 1+arousal_level, so back-to-back confirming incidents
    # crystallize SOONER than a bare HATE_STABILITY_THRESHOLD+1 calls --
    # drive incidents until crystallization is observed rather than
    # assuming a fixed call count.
    results = []
    for _ in range(10):
        r = record_hate_incident(inner, mt, pat, negative=True, base_alpha=0.3)
        results.append(r)
        if r["crystallized_this_call"]:
            break
    else:
        pytest.fail("did not crystallize within 10 incidents")
    crystallizing = results[-1]
    assert crystallizing["effective_removal_alpha"] is not None
    assert crystallizing["effective_removal_alpha"] > 0.3

    # exact formula: base_alpha * (1 + arousal_level BEFORE this incident's
    # own update) -- that pre-incident level is exactly the PRIOR result's
    # own (post-its-own-update) arousal_level.
    pre_incident_level = results[-2]["arousal_level"]
    expected_alpha = 0.3 * (1.0 + pre_incident_level)
    assert crystallizing["effective_removal_alpha"] == pytest.approx(expected_alpha)


# ---------------------------------------------------------------------
# 3. Hot vs cold crystallization -- the identical structural event
#    (confirm_streak crossing threshold) produces a markedly different
#    removal alpha depending on whether arousal was allowed to decay.
# ---------------------------------------------------------------------
def test_hot_crystallization_exceeds_cold_crystallization():
    # hot: back-to-back incidents, arousal compounds -- crystallizes
    # sooner than a bare HATE_STABILITY_THRESHOLD+1 calls now that
    # confirm_streak itself is arousal-coupled (HATE_STABILITY_AROUSAL_
    # COUPLING_PREREG.md), so drive until observed rather than assuming a
    # fixed call count.
    inner_hot, mt_hot = _fresh("mt_hot")
    pat_hot = mint_target_pattern(inner_hot, mt_hot, "Alex")
    hot_alpha = None
    for _ in range(10):
        r = record_hate_incident(inner_hot, mt_hot, pat_hot, negative=True)
        if r["crystallized_this_call"]:
            hot_alpha = r["effective_removal_alpha"]
            break
    assert hot_alpha is not None, "hot run did not crystallize within 10 incidents"

    # cold: manually decay arousal to near-zero between each incident,
    # simulating a long gap -- the formula itself is pure arithmetic
    # (level*decay), applied here directly to the tracked arousal node,
    # the same "tick with no incident" shape SHARED_AROUSAL_EXCITATION_
    # TRANSFER_RESULTS.md's own prediction 3 already used. With arousal
    # decayed away between incidents, confirm_streak increments fall back
    # to ~+1 each (the pre-coupling behavior), so this also takes the
    # pre-coupling HATE_STABILITY_THRESHOLD+1 calls to cross the threshold.
    inner_cold, mt_cold = _fresh("mt_cold")
    pat_cold = mint_target_pattern(inner_cold, mt_cold, "Sam")
    arousal_node = next(iter(inner_cold.neighbours(pat_cold, "tracks_arousal")))
    cold_alpha = None
    for _ in range(10):
        r = record_hate_incident(inner_cold, mt_cold, pat_cold, negative=True)
        if r["crystallized_this_call"]:
            cold_alpha = r["effective_removal_alpha"]
            break
        for _ in range(20):
            level = inner_cold.node(arousal_node)["attrs"]["level"]
            inner_cold.set_attr(arousal_node, "level", level * AROUSAL_DECAY)
    assert cold_alpha is not None, "cold run did not crystallize within 10 incidents"

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
