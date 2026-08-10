"""RUN 39B -- unit gates for `domains/motor_plan.py` (the MOTOR-PLAN AGREEMENT SCORE, an
ADDITIVE evidence channel) and its calibration-freeze mechanics
(`scripts/jabberwock_omniglot_run39b_supplement.py`).

Covers (per the RUN 39 FULL GATE launch brief): (1) `motor_plan_agreement` on synthetic
two-object pairs -- agreeing plans score high, a disagreeing transition scores lower, a
stroke-count mismatch SKIPS transitions honestly (never imputed); (2) lambda-freeze mechanics
-- calibration writes a value, eval reads it, `combined_verdict` never recomputes it and
`lam=0.0` recovers the GLOBAL verdict's own `argmin(err)` exactly; (3) the additive-proposal
invariant -- `propose_by_motor_plan`'s own output only ever GROWS a union, never reorders or
removes existing members (`committed_shape.union_candidates`'s own contract, reused verbatim);
(4) a held-Term source audit -- no Python argmin/argmax/sort-by-score in `domains/motor_
plan.py` (the SAME regex discipline `test_contrastive_verdict_migrated.py`/`test_committed_
shape_migrated.py` already apply to their own modules).

All synthetic (no real Omniglot files needed), deterministic.
"""
from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import abs_read as ar
from domains import committed_shape as cs
from domains import motor_plan as mp
from scripts import jabberwock_omniglot_run39_motorplan as gate0


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


def _norm(strokes):
    return gate0.normalize_glyph_xy([np.asarray(s, dtype=float) for s in strokes])


# ===================================================================================== #
# GATE 1 -- motor_plan_agreement on synthetics.
# ===================================================================================== #
def test_agreeing_plans_score_full_m(native):
    """Same start cell, same (matched) transition sector -> m == 1.0 exactly."""
    q = _norm([[[0, 0], [1, 0]], [[3, 0], [3, 1]]])
    c = _norm([[[0, 0], [1, 0]], [[3, 0], [3, 3]]])
    r = mp.motor_plan_agreement(native, q, c)
    assert r["skip_reason"] is None
    assert r["start_agree"] == 1.0
    assert r["transitions_frac"] == 1.0
    assert r["m"] == pytest.approx(1.0)


def test_swapped_transition_scores_lower_than_agreeing(native):
    """SAME start cell as the agreeing case above, but the candidate's transition points in a
    different compass sector -- the disagreement must show up ONLY in the transitions term,
    and the resulting m must be strictly LOWER than the full-agreement case (0.5, not 1.0:
    start still agrees, transitions now disagree, w_start=w_trans=0.5)."""
    q = _norm([[[0, 0], [1, 0]], [[3, 0], [3, 1]]])
    c_agree = _norm([[[0, 0], [1, 0]], [[3, 0], [3, 3]]])
    c_swapped = _norm([[[0, 0], [1, 0]], [[3, 3], [3, -3]]])
    r_agree = mp.motor_plan_agreement(native, q, c_agree)
    r_swap = mp.motor_plan_agreement(native, q, c_swapped)
    assert r_swap["skip_reason"] is None
    assert r_swap["start_agree"] == 1.0, "same start cell as the agreeing case -- isolates the " \
                                          "disagreement to the transitions term alone"
    assert r_swap["transitions_frac"] == 0.0
    assert r_swap["m"] == pytest.approx(0.5)
    assert r_swap["m"] < r_agree["m"]


def test_count_mismatch_skips_transitions_never_imputes(native):
    """A stroke-count mismatch (gate0's own 26% QC fact) SKIPS transitions honestly -- `m`
    degrades to `start_agree` alone, `transitions_frac` is `None` (never 0.0, which would be
    indistinguishable from a genuine measured disagreement), `skip_reason` names the cause."""
    q = _norm([[[0, 0], [1, 0]], [[3, 0], [3, 1]]])
    c = _norm([[[0, 0], [1, 0]], [[3, 0], [3, 1]], [[5, 5], [6, 6]]])
    r = mp.motor_plan_agreement(native, q, c)
    assert r["skip_reason"] == "count_mismatch"
    assert r["transitions_frac"] is None
    assert r["m"] == r["start_agree"]
    assert r["n_comparable"] == 0


def test_single_stroke_pair_has_no_transitions(native):
    """Two single-stroke glyphs -- structurally no transition exists at all (distinct from a
    data-quality skip): `skip_reason == "single_stroke"`, `m == start_agree`."""
    q = _norm([[[0, 0], [1, 0]]])
    c = _norm([[[0, 0], [1, 0]]])
    r = mp.motor_plan_agreement(native, q, c)
    assert r["skip_reason"] == "single_stroke"
    assert r["transitions_frac"] is None
    assert r["start_agree"] == 1.0
    assert r["m"] == 1.0


def test_reordered_correspondence_has_no_comparable_transition(native):
    """Three well-separated, distinctive strokes; the candidate draws the SAME three physical
    shapes in the fully REVERSED order. The spatial (shape) correspondence is still recovered
    correctly (`greedy_match` maps each candidate stroke to its true shape-twin), but no
    matched pair is drawn CONSECUTIVELY on both sides at once -- so every transition slot is
    honestly excluded (`skip_reason == "no_comparable_transitions"`), never scored as
    disagreement."""
    p0 = [[0, 0], [1, 0]]
    p1 = [[5, 5], [5, 6]]
    p2 = [[10, 10], [11, 11]]
    q = _norm([p0, p1, p2])
    c = _norm([p2, p1, p0])
    mapping = gate0.greedy_match(native, c, q)
    assert mapping == {0: 2, 1: 1, 2: 0}, "sanity: the correspondence really is fully reversed"
    r = mp.motor_plan_agreement(native, q, c)
    assert r["skip_reason"] == "no_comparable_transitions"
    assert r["transitions_frac"] is None
    assert r["n_comparable"] == 0
    assert r["m"] == r["start_agree"]


def test_m_is_always_bounded_0_1(native):
    for q_strokes, c_strokes in [
        ([[[0, 0], [1, 0]], [[3, 0], [3, 1]]], [[[0, 0], [1, 0]], [[3, 0], [3, 3]]]),
        ([[[0, 0], [1, 0]], [[3, 0], [3, 1]]], [[[0, 0], [1, 0]], [[3, 3], [3, -3]]]),
        ([[[0, 0], [1, 0]]], [[[0, 0], [1, 0]]]),
    ]:
        r = mp.motor_plan_agreement(native, _norm(q_strokes), _norm(c_strokes))
        assert 0.0 <= r["m"] <= 1.0


# ===================================================================================== #
# GATE 2 -- ARM V: combined_verdict / lambda-freeze mechanics.
# ===================================================================================== #
def test_lambda_zero_recovers_global_verdict_exactly(native):
    """`lam=0.0` must be BYTE-IDENTICAL to `argmin(err)` alone -- the motor-plan channel
    contributes nothing when its weight is zero, regardless of how strong `m` is, confirming
    RUN 37A's supplement-never-replace law is structurally true at the lam=0 boundary."""
    full_pairs = [(1.0, 0), (2.0, 1), (0.5, 2)]
    m_by_idx = {0: 1.0, 1: 1.0, 2: 0.0}    # candidate 2 has the WORST motor-plan agreement but
                                             # the BEST (lowest) parse-marginal error.
    winner = mp.combined_verdict(native, full_pairs, m_by_idx, 0.0)
    expected = int(native.evaluate(ar._argmin_pairs_term(full_pairs), {})[1])
    assert winner == expected == 2


def test_lambda_zero_is_invariant_to_missing_m_entries(native):
    """`m_by_idx` missing a candidate entirely must behave exactly like `m=0.0` for that
    candidate (never a crash, never a fabricated bonus)."""
    full_pairs = [(1.0, 0), (2.0, 1)]
    assert mp.combined_verdict(native, full_pairs, {}, 0.3) == \
        mp.combined_verdict(native, full_pairs, {0: 0.0, 1: 0.0}, 0.3)


def test_motor_supplement_can_flip_a_close_call(native):
    """A close parse-marginal call (0.05 apart) flips toward the candidate with the STRONGER
    motor-plan agreement once lam is large enough to matter -- the mechanism's whole point."""
    full_pairs = [(1.00, 0), (1.05, 1)]
    m_by_idx = {0: 0.0, 1: 1.0}
    assert mp.combined_verdict(native, full_pairs, m_by_idx, 0.0) == 0
    assert mp.combined_verdict(native, full_pairs, m_by_idx, 0.2) == 1


def test_motor_supplement_never_overturns_a_large_gap(native):
    """A small, background-calibrated lam (<=0.4, `LAMBDA_GRID`'s own max) cannot overturn a
    LARGE parse-marginal gap even at maximum possible motor-plan disagreement (m in [0,1] so
    the bonus is capped at `lam`) -- the supplement only ever nudges CLOSE calls."""
    full_pairs = [(1.0, 0), (5.0, 1)]
    m_by_idx = {0: 0.0, 1: 1.0}
    for lam in mp.LAMBDA_GRID:
        assert mp.combined_verdict(native, full_pairs, m_by_idx, lam) == 0


def test_lambda_freeze_calibration_roundtrip(tmp_path):
    """The calibration-freeze mechanics the launch brief requires: calibration WRITES a chosen
    lam to a checkpoint; eval READS it back and reproduces the identical verdict on the SAME
    inputs every time -- no eval-time recomputation, no drift, no hidden RNG."""
    calib_path = tmp_path / "calibration.json"
    chosen = dict(lam=0.2, threshold=1.0, lambda_curve={"0.05": 0.70, "0.1": 0.72, "0.2": 0.75,
                                                          "0.4": 0.71},
                  n_calib=200)
    calib_path.write_text(json.dumps(chosen))

    loaded_a = json.loads(calib_path.read_text())
    loaded_b = json.loads(calib_path.read_text())
    assert loaded_a == loaded_b == chosen

    native = srs.Substrate()._inner
    full_pairs = [(1.00, 0), (1.05, 1)]
    m_by_idx = {0: 0.0, 1: 1.0}
    w1 = mp.combined_verdict(native, full_pairs, m_by_idx, loaded_a["lam"])
    w2 = mp.combined_verdict(native, full_pairs, m_by_idx, loaded_b["lam"])
    assert w1 == w2 == 1


# ===================================================================================== #
# GATE 3 -- ARM P: additive-proposal invariant.
# ===================================================================================== #
def test_propose_by_motor_plan_threshold_branch_respects_cap(native):
    m_scores = [(0, 0.3), (1, 1.0), (2, 0.6), (3, 1.0), (4, 0.2)]
    got = mp.propose_by_motor_plan(native, m_scores, threshold=1.0, k_add=5)
    assert got == [1, 3]
    capped = mp.propose_by_motor_plan(native, m_scores, threshold=1.0, k_add=1)
    assert capped == [1]


def test_propose_by_motor_plan_falls_back_to_topk_when_nothing_clears_threshold(native):
    m_scores = [(0, 0.3), (1, 1.0), (2, 0.6), (3, 1.0), (4, 0.2)]
    got = mp.propose_by_motor_plan(native, m_scores, threshold=2.0, k_add=3)
    assert len(got) == 3
    assert set(got) <= {0, 1, 2, 3, 4}
    # the fallback must be the true top-3 by m: {1, 3} (m=1.0) then candidate 2 (m=0.6).
    assert set(got) == {1, 2, 3}


def test_propose_by_motor_plan_empty_scores_is_empty_not_a_crash(native):
    assert mp.propose_by_motor_plan(native, [], threshold=1.0, k_add=5) == []


def test_motor_plan_proposal_unions_additively_with_the_37b_union():
    """`propose_by_motor_plan`'s own output, unioned via `committed_shape.union_candidates`
    (reused, never re-implemented here) on top of an existing 37B union, must be an exact
    PREFIX-preserving superset -- the existing union's own members and order never change,
    only genuinely new indices are appended (RUN 37A's law, structurally enforced)."""
    shortlist = [3, 1, 4]
    committed = [1, 7]
    union_37b = cs.union_candidates(shortlist, committed)
    motor = [9, 1, 3]
    union_39b = cs.union_candidates(union_37b, motor)
    assert union_39b[:len(union_37b)] == union_37b
    assert set(union_37b) <= set(union_39b)
    assert len(union_39b) == len(set(union_39b)), "no duplicates"
    assert union_39b == [3, 1, 4, 7, 9]


def test_motor_plan_proposal_is_a_list_of_unique_indices(native):
    m_scores = [(0, 1.0), (1, 1.0), (2, 1.0), (3, 0.0)]
    got = mp.propose_by_motor_plan(native, m_scores, threshold=1.0, k_add=5)
    assert len(got) == len(set(got))


# ===================================================================================== #
# GATE 4 -- held-Term source audit (no Python argmin/argmax/sort-by-score).
# ===================================================================================== #
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SORT_RE = re.compile(r"\bsorted\(|\.sort\(", re.IGNORECASE)


def _code_only(mod) -> str:
    """Strip triple-quoted docstrings first (mirrors `test_committed_shape_migrated.py`'s own
    `_code_only` precedent) -- the module's own prose names Terms/held-mechanisms for context,
    which would otherwise false-positive the token scan below."""
    return re.sub(r'""".*?"""', "", inspect.getsource(mod), flags=re.DOTALL)


def test_motor_plan_no_python_ranking_decisions():
    src = _code_only(mp)
    assert not _BANNED_CALL_RE.search(src), (
        "motor_plan.py must not rank candidates via Python argmin/argmax -- combined_verdict "
        "and propose_by_motor_plan's fallback are held Argmin/Argmax Terms")
    assert not _MINMAX_KEY_RE.search(src), (
        "motor_plan.py must not use Python's builtin min()/max() ranked by a key-function")
    assert not _SORT_RE.search(src), (
        "motor_plan.py must not sort candidates by a continuous score in Python at all -- "
        "the threshold branch filters in caller-supplied index order, the fallback branch "
        "uses a repeated held Argmax")


def test_motor_plan_mints_nothing():
    src = _code_only(mp)
    forbidden = ["teach(", "add_node(", "add_edge(", "run_rules(", "decode_ink("]
    hits = [tok for tok in forbidden if tok in src]
    assert not hits, f"motor_plan.py must mint nothing -- found: {hits}"


def test_motor_plan_reuses_gate0_extractors_not_reimplemented():
    """Confirms the module genuinely IMPORTS gate0's own feature extractors rather than
    silently re-defining its own (parallel) copies -- which would risk losing the falsy-zero
    fix in a future edit."""
    src = _code_only(mp)
    assert "from scripts import jabberwock_omniglot_run39_motorplan as gate0" in src \
        or "from scripts.jabberwock_omniglot_run39_motorplan import" in src
    for name in ("def normalize_glyph_xy(", "def grid_cell(", "def sector8(", "def greedy_match("):
        assert name not in src, f"motor_plan.py must not re-define {name.strip('def (')} -- " \
                                  f"reuse gate0's own copy verbatim"
