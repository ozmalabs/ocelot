"""Regression for ADMIRATION_GRATITUDE_PREREG.md -- the positive mirror
of hate's own crystallization ladder (OCC's Attribution branch,
praiseworthy cell), plus a real bug fix (crystallize_hate's gate never
checked the sign of the crystallizing pattern) and gratitude_debt
(McCullough, Emmons & Tsang 2002).
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


def _crystallize_positive(inner, mt, pat):
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=False)
        if r["crystallized_this_call"] or r["admiration_crystallized_this_call"]:
            return r
    raise AssertionError("did not crystallize")


# ---------------------------------------------------------------------
# 1. The bug fix: repeated positive incidents never crystallize into Hate.
# ---------------------------------------------------------------------
def test_repeated_positive_incidents_never_crystallize_hate():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = _crystallize_positive(inner, mt, pat)
    assert not r["crystallized_this_call"]
    assert len(list(inner.nodes("Hate"))) == 0


# ---------------------------------------------------------------------
# 2. Repeated positive incidents crystallize into Admiration instead.
# ---------------------------------------------------------------------
def test_repeated_positive_incidents_crystallize_admiration():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = _crystallize_positive(inner, mt, pat)
    assert r["admiration_crystallized_this_call"]
    assert len(list(inner.nodes("Admiration"))) == 1


# ---------------------------------------------------------------------
# 3. Controllability gates admiration's routing.
# ---------------------------------------------------------------------
def test_uncontrollable_positive_pattern_routes_to_none():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    record_understanding_incident(inner, pat, exculpatory=True)
    record_understanding_incident(inner, pat, exculpatory=True)
    r = _crystallize_positive(inner, mt, pat)
    assert r["admiration_consequence_route"] == "none"
    assert r["admiration_external_field"] == 0.0


def test_controllable_positive_pattern_routes_to_admiration():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = _crystallize_positive(inner, mt, pat)
    assert r["admiration_consequence_route"] == "admiration"
    assert r["admiration_external_field"] > 0.0


# ---------------------------------------------------------------------
# 4. gratitude_debt accumulates on every positive incident, independent
#    of locus or crystallization.
# ---------------------------------------------------------------------
def test_gratitude_debt_accumulates_on_every_positive_incident():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r1 = record_hate_incident(inner, mt, pat, negative=False)  # first_encounter
    assert r1["gratitude_debt"] == pytest.approx(1.0)
    r2 = record_hate_incident(inner, mt, pat, negative=False)
    assert r2["gratitude_debt"] == pytest.approx(2.0)


def test_a_single_isolated_positive_act_raises_gratitude_debt_without_crystallizing():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = record_hate_incident(inner, mt, pat, negative=False)
    assert not r["admiration_crystallized_this_call"]
    assert r["gratitude_debt"] > 0.0


# ---------------------------------------------------------------------
# 5. gratitude_debt amplifies admiration_for's crystallizing alpha, the
#    same way resentment_debt amplifies removal_desire_for's.
# ---------------------------------------------------------------------
def test_gratitude_debt_amplifies_admiration_alpha_isolated_from_arousal():
    base_alpha = 0.3
    crystallization_arousal = 1.0

    def run(pre_debt):
        inner, mt = _fresh("t%s" % pre_debt)
        pat = mint_target_pattern(inner, mt, "Alex")
        inner.set_attr(pat, "confirm_streak", 2.0)
        inner.set_attr(pat, "incident_count", 1)
        inner.set_attr(pat, "gratitude_debt", pre_debt)
        regard = next(iter(inner.neighbours(pat, "tracks_concept")))
        inner.set_attr(regard, "external_field", 3.0)
        arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
        inner.set_attr(arousal_node, "level", crystallization_arousal)
        r = record_hate_incident(inner, mt, pat, negative=False, base_alpha=base_alpha)
        assert r["admiration_crystallized_this_call"]
        return r["effective_admiration_alpha"]

    alpha_no_debt = run(pre_debt=0.0)
    alpha_with_debt = run(pre_debt=1.0)

    expected_no_debt = base_alpha * (1.0 + crystallization_arousal)
    assert alpha_no_debt == pytest.approx(expected_no_debt)
    assert alpha_with_debt > alpha_no_debt
    expected_with_debt = base_alpha * (1.0 + crystallization_arousal) * 2.0
    assert alpha_with_debt == pytest.approx(expected_with_debt)


# ---------------------------------------------------------------------
# 6. Per-target isolation for both Admiration crystallization and
#    gratitude_debt.
# ---------------------------------------------------------------------
def test_per_target_isolation():
    inner, mt = _fresh()
    jo = mint_target_pattern(inner, mt, "Jo")
    _crystallize_positive(inner, mt, jo)
    assert bool(inner.node(jo)["attrs"]["crystallized"])

    kim = mint_target_pattern(inner, mt, "Kim")
    r_kim = record_hate_incident(inner, mt, kim, negative=True)
    assert r_kim["gratitude_debt"] == 0.0
    assert not r_kim["admiration_crystallized_this_call"]
    assert not bool(inner.node(kim)["attrs"]["crystallized"])


# ---------------------------------------------------------------------
# 7. Negative patterns still correctly crystallize into Hate (regression).
# ---------------------------------------------------------------------
def test_negative_pattern_still_crystallizes_hate():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = None
    for _ in range(HATE_STABILITY_THRESHOLD + 3):
        r = record_hate_incident(inner, mt, pat, negative=True)
        if r["crystallized_this_call"]:
            break
    assert r["crystallized_this_call"]
    assert not r["admiration_crystallized_this_call"]
    assert len(list(inner.nodes("Admiration"))) == 0


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
