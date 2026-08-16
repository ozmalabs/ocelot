"""Regression for CONTEMPT_PREREG.md -- a third consequence_route,
"devaluation", alongside removal/pity (Rozin, Lowery & Haidt 1999's CAD
triad).
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


def _crystallize_negative(inner, mt, pat, violation_type="harm"):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=True, violation_type=violation_type)
        if r["crystallized_this_call"]:
            return r
    raise AssertionError("did not crystallize")


# ---------------------------------------------------------------------
# 1. Backward compatibility: default violation_type still routes removal.
# ---------------------------------------------------------------------
def test_default_violation_type_still_routes_to_removal():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = _crystallize_negative(inner, mt, pat)
    assert r["consequence_route"] == "removal"
    assert r["removal_desire_external_field"] > 0.0
    assert r["devaluation_external_field"] == 0.0


# ---------------------------------------------------------------------
# 2. A controllable norm violation routes to devaluation.
# ---------------------------------------------------------------------
def test_controllable_norm_violation_routes_to_devaluation():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = _crystallize_negative(inner, mt, pat, violation_type="norm")
    assert r["consequence_route"] == "devaluation"
    assert r["devaluation_external_field"] > 0.0
    assert r["removal_desire_external_field"] == 0.0
    assert r["effective_removal_alpha"] is None


# ---------------------------------------------------------------------
# 3. Controllability still gates independently of violation type.
# ---------------------------------------------------------------------
def test_uncontrollable_norm_violation_still_routes_to_pity():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    record_understanding_incident(inner, pat, exculpatory=True)
    record_understanding_incident(inner, pat, exculpatory=True)
    r = _crystallize_negative(inner, mt, pat, violation_type="norm")
    assert r["consequence_route"] == "pity"
    assert r["devaluation_external_field"] == 0.0


# ---------------------------------------------------------------------
# 4. devaluation_for's alpha is unamplified, unlike removal_desire_for's.
# ---------------------------------------------------------------------
def test_devaluation_alpha_is_unamplified_unlike_removal():
    base_alpha = 0.3

    def run(violation_type):
        inner, mt = _fresh("t%s" % violation_type)
        pat = mint_target_pattern(inner, mt, "Alex")
        inner.set_attr(pat, "confirm_streak", 2.0)
        inner.set_attr(pat, "incident_count", 1)
        inner.set_attr(pat, "resentment_debt", 1.0)
        regard = next(iter(inner.neighbours(pat, "tracks_concept")))
        inner.set_attr(regard, "external_field", -3.0)
        arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
        inner.set_attr(arousal_node, "level", 1.0)
        return record_hate_incident(inner, mt, pat, negative=True,
                                    violation_type=violation_type, base_alpha=base_alpha)

    r_removal = run("harm")
    r_devaluation = run("norm")
    assert r_removal["consequence_route"] == "removal"
    assert r_devaluation["consequence_route"] == "devaluation"
    assert r_removal["effective_removal_alpha"] > base_alpha  # amplified
    assert r_devaluation["devaluation_external_field"] == pytest.approx(base_alpha)  # flat
    assert r_devaluation["devaluation_external_field"] < r_removal["effective_removal_alpha"]


# ---------------------------------------------------------------------
# 5. Per-target isolation.
# ---------------------------------------------------------------------
def test_per_target_isolation():
    inner, mt = _fresh()
    jo = mint_target_pattern(inner, mt, "Jo")
    _crystallize_negative(inner, mt, jo, violation_type="norm")
    assert bool(inner.node(jo)["attrs"]["crystallized"])

    kim = mint_target_pattern(inner, mt, "Kim")
    r_kim = record_hate_incident(inner, mt, kim, negative=True, violation_type="harm")
    assert not r_kim["crystallized_this_call"]
    assert inner.node(kim)["attrs"]["violation_type"] == "harm"


def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json", "seeds/shared_arousal.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
