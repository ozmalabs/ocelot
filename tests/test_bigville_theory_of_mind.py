"""Regression for domains/bigville_theory_of_mind.py -- the named entry
point for a resident's ToM belief about another resident's mind/
circumstances (as distinct from the resident's own affect toward them).
See TOM_SYSTEM_UNIFICATION_RESULTS.md.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.bigville_theory_of_mind import mint_resident_tom_belief
from domains.hate_attribution import mint_target_pattern


def _fresh(name="test_mt"):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


def test_mint_resident_tom_belief_names_the_conventional_concept():
    inner, mt = _fresh()
    concept = mint_resident_tom_belief(inner, mt, "controllability", "Alex")
    assert inner.node(concept)["attrs"]["name"] == "controllability_for:Alex"


def test_mint_resident_tom_belief_is_idempotent():
    inner, mt = _fresh()
    c1 = mint_resident_tom_belief(inner, mt, "controllability", "Alex")
    c2 = mint_resident_tom_belief(inner, mt, "controllability", "Alex")
    assert c1 == c2


def test_hate_attribution_controllability_routes_through_the_named_entry_point():
    """hate_attribution.py's own controllability_for Concept is minted via
    mint_resident_tom_belief -- same node, whichever caller reaches it
    first."""
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    via_pattern = next(iter(inner.neighbours(pat, "tracks_controllability")))
    via_named_entry_point = mint_resident_tom_belief(inner, mt, "controllability", "Alex")
    assert via_pattern == via_named_entry_point


def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/shared_arousal.json", "seeds/hate_attribution.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
