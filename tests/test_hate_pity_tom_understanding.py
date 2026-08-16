"""Regression for HATE_PITY_TOM_UNDERSTANDING_PREREG.md -- Weiner's
controllability dimension, read from the resident's own Theory-of-Mind
belief about the target (controllability_for), routes a crystallizing
hate's evidence to removal_desire_for or a new pity_for Concept.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
    record_understanding_incident,
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


def _crystallize(inner, mt, pat, negative=True):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=negative)
        if r["crystallized_this_call"]:
            return r
    raise AssertionError("did not crystallize")


# ---------------------------------------------------------------------
# 1. No understanding at all -> routes to removal (Ross 1977 default).
# ---------------------------------------------------------------------
def test_no_understanding_routes_to_removal():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = _crystallize(inner, mt, pat)
    assert r["consequence_route"] == "removal"
    assert r["removal_desire_external_field"] > 0.0
    assert r["pity_external_field"] == 0.0
    assert r["controllability_external_field"] == 0.0


# ---------------------------------------------------------------------
# 2. Sufficient exculpatory understanding before crystallization ->
#    routes to pity, removal_desire_for gets ZERO evidence.
# ---------------------------------------------------------------------
def test_exculpatory_understanding_routes_to_pity():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    record_understanding_incident(inner, pat, exculpatory=True)
    record_understanding_incident(inner, pat, exculpatory=True)
    assert inner.node(
        next(iter(inner.neighbours(pat, "tracks_controllability"))))["attrs"]["external_field"] < 0.0

    r = _crystallize(inner, mt, pat)
    assert r["consequence_route"] == "pity"
    assert r["removal_desire_external_field"] == 0.0
    assert r["pity_external_field"] > 0.0
    assert r["effective_removal_alpha"] is None


# ---------------------------------------------------------------------
# 3. The routing matches the sign test exactly, including the boundary.
# ---------------------------------------------------------------------
def test_boundary_zero_controllability_routes_to_removal():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    # controllability_for stays at its minted default (0.0, never touched)
    controllability = next(iter(inner.neighbours(pat, "tracks_controllability")))
    assert inner.node(controllability)["attrs"]["external_field"] == 0.0
    r = _crystallize(inner, mt, pat)
    assert r["consequence_route"] == "removal"


def test_non_exculpatory_understanding_keeps_the_removal_route():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    # explicit evidence the act WAS deliberate/controllable
    record_understanding_incident(inner, pat, exculpatory=False)
    controllability = next(iter(inner.neighbours(pat, "tracks_controllability")))
    assert inner.node(controllability)["attrs"]["external_field"] > 0.0
    r = _crystallize(inner, mt, pat)
    assert r["consequence_route"] == "removal"


# ---------------------------------------------------------------------
# 4. Per-target isolation.
# ---------------------------------------------------------------------
def test_understanding_does_not_leak_across_targets():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    record_understanding_incident(inner, alex, exculpatory=True)
    record_understanding_incident(inner, alex, exculpatory=True)

    sam = mint_target_pattern(inner, mt, "Sam")
    controllability_sam = next(iter(inner.neighbours(sam, "tracks_controllability")))
    assert inner.node(controllability_sam)["attrs"]["external_field"] == 0.0

    r_sam = _crystallize(inner, mt, sam)
    assert r_sam["consequence_route"] == "removal"

    r_alex = _crystallize(inner, mt, alex)
    assert r_alex["consequence_route"] == "pity"


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
