"""tests/test_varcomp_migrated.py -- RUN 52, THE MINIMAL LOOP-FLIP: unit gates for
`domains/character_compose.py::assignment_coverage_term`'s new `weights` kwarg (a per-slot
TIGHTNESS reweight of the composition/arrangement scoring Term -- run 50's own background-
learned `relational_variation.slot_weights(...)` output, substituted in place of the four
hardcoded `1.0` pose-slot weights and the four hardcoded `1.0` cpose weights). This is NOT a new
Term, NOT a new stage, NOT a bolt-on additive supplement -- the SAME `assignment_coverage_term`
Term structure (`MaxOver`/`Sum`/`Plus`/`IfThenElse`), with one constant replaced by DATA.

Hermetic (no real Omniglot files, no substrate seed writes) except one gate that reads run 50's
own frozen `results/run50_checkpoints/learn_relational.json` (READ-ONLY reference, never
recomputed here).

Covers (per the RUN 52 launch brief):
  1. `weights=None` (every pre-existing call site) and `weights={slot: 1.0 for slot in
     ALL_SLOTS}` (the EXPLICIT equal-weight arm, this run's own GUARD) score BYTE-IDENTICAL to
     each other AND to the pre-RUN-52 hardcoded-`1.0` Term -- the critical invariant: "the
     mechanism reduces to baseline when all weights equal."
  2. Tightness-weighting changes the score in the right DIRECTION: a mismatch on a TIGHT
     (high-weight) slot costs MORE than an equal-magnitude (one-bin) mismatch on a LOOSE
     (low-weight) slot.
  3. Frozen-weight mechanics: run 50's own `learn_relational.json` weights apply without error
     and cover exactly `relational_variation.ALL_SLOTS`.
  4. Determinism -- repeated calls, identical inputs, byte-identical score.
  5. Source audit -- no Python argmin/argmax/sort-by-score/min-max-by-key inside
     `assignment_coverage_term` (the ranking decision stays the caller's held `Argmax`).
  6. Seed guard -- `seeds/stroke_shapes.json` md5 unchanged across this whole test module (no
     decode call here touches real drawer files, but the guard is cheap and matches every other
     test file's own discipline in this arc).
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import character_compose as cc
from domains import relational_variation as rv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
RUN50_LEARN_RELATIONAL = os.path.join(ROOT, "results", "run50_checkpoints", "learn_relational.json")


def _md5(path: str):
    if not os.path.exists(path):
        return None
    return hashlib.md5(open(path, "rb").read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, "seeds/stroke_shapes.json changed across test_varcomp_migrated.py"


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


# --------------------------------------------------------------------------------------------- #
# Synthetic composed-signature builder -- mirrors test_relational_variation_migrated.py's own
# fixture exactly (a 2-stroke "character") so the two test modules stay directly comparable.
# --------------------------------------------------------------------------------------------- #
def _sig(rel0, rel1, cpose):
    """`rel0`/`rel1`: (x_q, y_q, o_q, s_q) for stroke 0 / stroke 1. `cpose`: (x, y, o, s)."""
    sig = [["strokeq", 0, "q0"], ["strokeq", 1, "q1"],
           ["rel", 0, *rel0], ["rel", 1, *rel1]]
    for pred, v in zip(rv.CPOSE_SLOTS, cpose):
        sig.append([pred, v])
    return sig


UNIFORM_WEIGHTS = {slot: 1.0 for slot in rv.ALL_SLOTS}


# ===================================================================================== #
# GATE 1 -- equal weights (None, or all-1.0) reproduce the PRE-RUN-52 score byte-identically
# -- "the mechanism reduces to baseline when all weights equal."
# ===================================================================================== #
def test_weights_none_and_uniform_are_byte_identical(native):
    query_sig = _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    cand_sig = _sig((4, 5, 1, 3), (7, 6, 0, 4), (1, 0, 0, 3))
    score_none = float(native.evaluate(cc.assignment_coverage_term(query_sig, cand_sig), {}))
    score_uniform = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_sig, weights=UNIFORM_WEIGHTS), {}))
    assert score_none == score_uniform, (score_none, score_uniform)

    # And the SAME invariant holds at identity_weight=0.0 (arrangement-only, run 50's own scope
    # -- the convention this run's own gate script uses for GUARD/ARM W).
    score_none_arr = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_sig, identity_weight=0.0), {}))
    score_uniform_arr = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_sig, identity_weight=0.0,
                                     weights=UNIFORM_WEIGHTS), {}))
    assert score_none_arr == score_uniform_arr, (score_none_arr, score_uniform_arr)


def test_weights_is_a_pure_additive_reweight_not_a_new_stage():
    """The function signature gains ONLY an additive `weights` kwarg, default `None` -- no new
    Term type, no new stage; every pre-existing call site (no `weights` kwarg at all) is
    untouched (`test_character_composition_migrated.py`'s full suite, unmodified, still green)."""
    sig = inspect.signature(cc.assignment_coverage_term)
    assert "weights" in sig.parameters
    assert sig.parameters["weights"].default is None
    assert "identity_weight" in sig.parameters   # UNCHANGED, still present, still first kwarg.


# ===================================================================================== #
# GATE 2 -- tightness-weighting changes the score in the RIGHT DIRECTION: a mismatch on a
# TIGHT slot costs MORE (lower coverage) than an equal-magnitude mismatch on a LOOSE slot.
# ===================================================================================== #
def test_tight_slot_mismatch_penalized_more_than_loose_slot_mismatch(native):
    weights = dict(UNIFORM_WEIGHTS)
    weights["rel_x"] = 4.0    # TIGHT (learned) -- a class whose stroke-0 x-position never varies.
    weights["rel_y"] = 0.25   # LOOSE (learned) -- a class whose stroke-0 y-position varies freely.

    query_sig = _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    # Candidate A mismatches ONLY the TIGHT slot (stroke 0's x_q, 3 -> 4, one bin).
    cand_a = _sig((4, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    # Candidate B mismatches ONLY the LOOSE slot (stroke 0's y_q, 3 -> 4, ALSO one bin).
    cand_b = _sig((3, 4, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))

    score_a = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_a, identity_weight=0.0, weights=weights), {}))
    score_b = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_b, identity_weight=0.0, weights=weights), {}))
    # coverage: HIGHER is better. Losing the TIGHT slot's weight must cost MORE than losing the
    # LOOSE slot's -- score_a (lost the tight slot) strictly BELOW score_b (lost the loose one).
    assert score_a < score_b, (score_a, score_b)

    # An exact-match candidate scores strictly highest of the three.
    score_same = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, query_sig, identity_weight=0.0, weights=weights),
        {}))
    assert score_same > score_b > score_a, (score_same, score_b, score_a)


def test_equal_magnitude_mismatch_is_a_wash_under_uniform_weights(native):
    """Sanity companion to GATE 2: the SAME two candidates score IDENTICALLY under the
    UNIFORM-weight arm (GUARD) -- the direction-changing effect in GATE 2 is caused SOLELY by
    the learned weight asymmetry, not by some other difference between candidates A and B."""
    query_sig = _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    cand_a = _sig((4, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    cand_b = _sig((3, 4, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    score_a = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_a, identity_weight=0.0,
                                     weights=UNIFORM_WEIGHTS), {}))
    score_b = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_b, identity_weight=0.0,
                                     weights=UNIFORM_WEIGHTS), {}))
    assert score_a == score_b, (score_a, score_b)


# ===================================================================================== #
# GATE 3 -- frozen-weight mechanics: run 50's own `learn_relational.json` weights (READ-ONLY)
# apply without error and cover exactly `relational_variation.ALL_SLOTS`.
# ===================================================================================== #
def test_frozen_run50_weights_apply_and_cover_all_slots(native):
    assert os.path.exists(RUN50_LEARN_RELATIONAL), (
        "RUN 50's own learn_relational.json must exist -- run 52 reuses it READ-ONLY, never "
        "recomputes the tightness model")
    weights = json.load(open(RUN50_LEARN_RELATIONAL))["weights"]
    assert set(weights) == set(rv.ALL_SLOTS), (set(weights), set(rv.ALL_SLOTS))
    assert all(np.isfinite(v) and v > 0 for v in weights.values()), weights

    query_sig = _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    cand_sig = _sig((4, 5, 1, 3), (7, 6, 0, 4), (1, 0, 0, 3))
    score = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_sig, identity_weight=0.0, weights=weights),
        {}))
    assert np.isfinite(score)


def test_frozen_weights_are_not_flat_there_is_real_structure_to_learn():
    """Companion honesty check (run-28's own 'engagement vs outcome' law, cited by the launch
    brief): if the 8 pooled weights were all ~equal, RUN 52's mechanism is starved by
    construction (nothing for it to reweight) and a null is the ONLY possible outcome -- this
    assertion documents that the run's own precondition (real tight/loose structure) holds,
    it does not by itself predict the eval verdict."""
    weights = json.load(open(RUN50_LEARN_RELATIONAL))["weights"]
    vals = list(weights.values())
    assert (max(vals) / min(vals)) > 2.0, (
        "weights are nearly flat -- RUN 52's mechanism would be structurally starved", weights)


# ===================================================================================== #
# GATE 4 -- determinism.
# ===================================================================================== #
def test_determinism(native):
    weights = {"rel_x": 2.0, "rel_y": 0.5, "rel_o": 1.3, "rel_s": 0.7,
               "cpose_x": 1.1, "cpose_y": 0.9, "cpose_o": 1.0, "cpose_s": 1.0}
    query_sig = _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3))
    cand_sig = _sig((4, 5, 1, 3), (7, 6, 0, 4), (1, 0, 0, 3))
    s1 = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_sig, identity_weight=0.0, weights=weights),
        {}))
    s2 = float(native.evaluate(
        cc.assignment_coverage_term(query_sig, cand_sig, identity_weight=0.0, weights=weights),
        {}))
    assert s1 == s2


# ===================================================================================== #
# GATE 5 -- source audit: no Python argmin/argmax/sort-by-score deciding a ranking inside
# `assignment_coverage_term` itself (the ranking decision stays the caller's held `Argmax`,
# mirrors `test_relational_variation_migrated.py::test_no_python_decision_source_audit`).
# ===================================================================================== #
def test_assignment_coverage_term_no_python_decision_source_audit():
    src = inspect.getsource(cc.assignment_coverage_term)
    for banned in ("np.argmin(", "np.argmax(", ".sort(key=", "min(costs", "max(costs",
                   "sorted(", "min(scores", "max(scores"):
        assert banned not in src, f"found banned decision idiom {banned!r} in assignment_coverage_term"
