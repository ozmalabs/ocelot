"""Regression for SHAPE_FIT_PREFERENCE_PREREG.md -- an inverted-U
(Berlyne 1971's Wundt curve) preference over ShapeDecode's own already-
surfaced fluency, plus a novelty-driven side observable into the shared
TargetArousal pool.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.shape_fit_preference import preference_from_shape


def _fresh(name="test_mt"):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    d = json.load(open("seeds/shared_arousal.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


def _mint_proto(inner, name, signature):
    return inner.add_node("ShapeSignature", {"name": name, "signature": signature})


PROTO_SIG = [["shape", "round"], ["color", "red"], ["size", "small"]]


# ---------------------------------------------------------------------
# 1. Exact match (fluency=1.0) -> preference=0.0, the boring extreme.
# ---------------------------------------------------------------------
def test_exact_match_scores_zero_preference():
    inner, mt = _fresh()
    _mint_proto(inner, "proto", PROTO_SIG)
    r = preference_from_shape(inner, mt, "stimulus", list(PROTO_SIG))
    assert r["fluency"] == pytest.approx(1.0)
    assert r["preference"] == pytest.approx(0.0)


# ---------------------------------------------------------------------
# 2. No match at all (fluency=0.0) -> preference=0.0, the overwhelming
#    extreme.
# ---------------------------------------------------------------------
def test_total_novelty_scores_zero_preference():
    inner, mt = _fresh()
    _mint_proto(inner, "proto", PROTO_SIG)
    novel = [["shape", "triangle"], ["color", "green"], ["size", "medium"]]
    r = preference_from_shape(inner, mt, "stimulus", novel)
    assert r["fluency"] == pytest.approx(0.0)
    assert r["preference"] == pytest.approx(0.0)


# ---------------------------------------------------------------------
# 3. Partial match scores strictly higher than both extremes.
# ---------------------------------------------------------------------
def test_partial_match_scores_higher_than_both_extremes():
    inner, mt = _fresh()
    _mint_proto(inner, "proto", PROTO_SIG)
    partial = [["shape", "round"], ["color", "green"], ["size", "small"]]  # 2/3
    r_partial = preference_from_shape(inner, mt, "s1", partial)
    r_exact = preference_from_shape(inner, mt, "s2", list(PROTO_SIG))
    r_novel = preference_from_shape(inner, mt, "s3",
        [["shape", "triangle"], ["color", "green"], ["size", "medium"]])
    assert r_partial["preference"] > r_exact["preference"]
    assert r_partial["preference"] > r_novel["preference"]


# ---------------------------------------------------------------------
# 4. Symmetry -- fluency=0.3 and fluency=0.7 score identically.
# ---------------------------------------------------------------------
def test_preference_is_symmetric_around_the_midpoint():
    inner, mt = _fresh()
    proto_rels = [["k%d" % i, "v%d" % i] for i in range(10)]
    _mint_proto(inner, "proto10", proto_rels)

    goal_30 = proto_rels[:3] + [["novel%d" % i, "x"] for i in range(7)]
    goal_70 = proto_rels[:7] + [["novel%d" % i, "x"] for i in range(3)]

    r30 = preference_from_shape(inner, mt, "s_30", goal_30)
    r70 = preference_from_shape(inner, mt, "s_70", goal_70)
    assert r30["fluency"] == pytest.approx(0.3)
    assert r70["fluency"] == pytest.approx(0.7)
    assert r30["preference"] == pytest.approx(r70["preference"])


# ---------------------------------------------------------------------
# 5. Novelty feeds arousal -- a novel stimulus raises arousal more than
#    a familiar one.
# ---------------------------------------------------------------------
def test_novelty_raises_arousal_more_than_familiarity():
    inner, mt = _fresh()
    _mint_proto(inner, "proto", PROTO_SIG)
    r_familiar = preference_from_shape(inner, mt, "s_familiar", list(PROTO_SIG))
    r_novel = preference_from_shape(inner, mt, "s_novel",
        [["shape", "triangle"], ["color", "green"], ["size", "medium"]])
    assert r_novel["arousal_level"] > r_familiar["arousal_level"]
    assert r_familiar["arousal_level"] == pytest.approx(0.0)  # zero novelty, zero contribution


def test_preference_formula_matches_the_registered_parabola_exactly():
    inner, mt = _fresh()
    _mint_proto(inner, "proto", PROTO_SIG)
    partial = [["shape", "round"], ["color", "green"], ["size", "small"]]
    r = preference_from_shape(inner, mt, "s", partial)
    expected = 4.0 * r["fluency"] * (1.0 - r["fluency"])
    assert r["preference"] == pytest.approx(expected)


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
