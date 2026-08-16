"""Regression for HATE_RESENTMENT_PASSION_COUPLING_PREREG.md --
removal_desire's crystallization alpha amplified by BOTH momentary
arousal AND accumulated (never-decremented) resentment_debt.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import mint_target_pattern, record_hate_incident


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
# 3. resentment_debt matches the residue formula exactly (also verifies
#    the effect-ordering fix directly).
# ---------------------------------------------------------------------
def test_resentment_debt_matches_the_residue_exactly():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    inner.set_attr(pat, "confirm_streak", 1.0)
    inner.set_attr(pat, "incident_count", 1)
    regard = next(iter(inner.neighbours(pat, "tracks_concept")))
    inner.set_attr(regard, "external_field", -2.0)
    arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
    inner.set_attr(arousal_node, "level", 1.0)
    r_exc = record_hate_incident(inner, mt, pat, negative=False)
    assert r_exc["attribution_locus"] == "specific_act"
    assert r_exc["resentment_debt"] == pytest.approx(r_exc["confirm_streak"])
    assert r_exc["resentment_debt"] == pytest.approx(0.5)


# ---------------------------------------------------------------------
# 4. resentment_debt accumulates across MULTIPLE specific_act incidents.
# ---------------------------------------------------------------------
def test_resentment_debt_accumulates_across_multiple_exceptions():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    inner.set_attr(pat, "confirm_streak", 2.0)
    inner.set_attr(pat, "incident_count", 1)
    regard = next(iter(inner.neighbours(pat, "tracks_concept")))
    inner.set_attr(regard, "external_field", -3.0)
    arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
    inner.set_attr(arousal_node, "level", 1.0)

    r1 = record_hate_incident(inner, mt, pat, negative=False)
    assert r1["attribution_locus"] == "specific_act"
    debt_after_1 = r1["resentment_debt"]
    assert debt_after_1 > 0.0

    # stage a second exception directly (skip re-growing the streak
    # organically, since the sign of regard_for already shifted from the
    # first exception's own evidence).
    inner.set_attr(pat, "confirm_streak", 2.0)
    inner.set_attr(regard, "external_field", -3.0)
    inner.set_attr(arousal_node, "level", 1.0)
    r2 = record_hate_incident(inner, mt, pat, negative=False)
    assert r2["attribution_locus"] == "specific_act"
    debt_after_2 = r2["resentment_debt"]

    assert debt_after_2 == pytest.approx(debt_after_1 + (2.0 * 0.5))
    assert debt_after_2 > debt_after_1  # monotonically accumulating


# ---------------------------------------------------------------------
# 1/2/3. effective_removal_alpha: backward compatible at zero debt,
#    strictly higher with accumulated debt (isolated from arousal),
#    matches the formula exactly.
# ---------------------------------------------------------------------
def test_removal_alpha_amplified_by_resentment_debt_isolated_from_arousal():
    base_alpha = 0.3
    crystallization_arousal = 1.0  # held equal in both runs

    def run(pre_debt):
        inner, mt = _fresh("t%s" % pre_debt)
        pat = mint_target_pattern(inner, mt, "Alex")
        threshold_pat_streak = 3.0  # comfortably crosses the base gate
        inner.set_attr(pat, "confirm_streak", threshold_pat_streak - 1.0)
        inner.set_attr(pat, "incident_count", 1)
        inner.set_attr(pat, "resentment_debt", pre_debt)
        regard = next(iter(inner.neighbours(pat, "tracks_concept")))
        inner.set_attr(regard, "external_field", -3.0)
        arousal_node = next(iter(inner.neighbours(pat, "tracks_arousal")))
        inner.set_attr(arousal_node, "level", crystallization_arousal)
        r = record_hate_incident(inner, mt, pat, negative=True, base_alpha=base_alpha)
        assert r["crystallized_this_call"]
        return r["effective_removal_alpha"], r["arousal_level"]

    alpha_no_debt, _ = run(pre_debt=0.0)
    alpha_with_debt, _ = run(pre_debt=1.0)

    # Prediction 1: zero debt matches the arousal-only (v1.1.0) formula.
    expected_no_debt = base_alpha * (1.0 + crystallization_arousal)
    assert alpha_no_debt == pytest.approx(expected_no_debt)

    # Prediction 2: nonzero debt is strictly higher, holding arousal fixed.
    assert alpha_with_debt > alpha_no_debt

    # Prediction 3: matches the full two-channel formula exactly.
    expected_with_debt = base_alpha * (1.0 + crystallization_arousal) * (1.0 + 1.0)
    assert alpha_with_debt == pytest.approx(expected_with_debt)


# ---------------------------------------------------------------------
# 4. Per-target isolation.
# ---------------------------------------------------------------------
def test_resentment_debt_does_not_leak_across_targets():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    inner.set_attr(alex, "confirm_streak", 1.0)
    inner.set_attr(alex, "incident_count", 1)
    regard_alex = next(iter(inner.neighbours(alex, "tracks_concept")))
    inner.set_attr(regard_alex, "external_field", -2.0)
    arousal_alex = next(iter(inner.neighbours(alex, "tracks_arousal")))
    inner.set_attr(arousal_alex, "level", 1.0)
    record_hate_incident(inner, mt, alex, negative=False)
    assert inner.node(alex)["attrs"]["resentment_debt"] > 0.0

    sam = mint_target_pattern(inner, mt, "Sam")
    assert inner.node(sam)["attrs"]["resentment_debt"] == 0.0


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
