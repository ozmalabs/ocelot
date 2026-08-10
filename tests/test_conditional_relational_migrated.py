"""tests/test_conditional_relational_migrated.py -- RUN 51: unit gates for
`scripts/jabberwock_omniglot_run51_conditional.py` (THE CONDITIONAL RELATIONAL VERDICT -- run
45's conditional-fire scaffold + run 50's orthogonal relational-variation evidence). Hermetic,
synthetic strokes/signatures only -- no Omniglot dataset needed; the REAL-DATA guards
(background-sanity, GLOBAL reproduces 80.5%/k=322 exactly) are the run script's own
`--stage sanity`/`--stage guard`, mirroring run 45/50's own precedent -- not duplicated here.

Gates (per the launch brief):
  1. CONDITIONAL-FIRE mechanics -- low-margin + multi-stroke fires; low-margin + single-stroke
     does NOT fire (the structural gate run 50's own "single-stroke has no relations" note
     requires); high-margin + multi-stroke does NOT fire; the non-fired case is byte-identical
     to the untouched fused score.
  2. R-ADJUDICATION re-ranks a synthetic tied-top-2 correctly -- a near-tied `full_pairs` where
     geo picks the WRONG candidate by a hair, and the relational evidence clearly favours the
     TRUE candidate, must FLIP the argmin once fused at a large-enough `w_r`.
  3. FROZEN-THRESHOLD mechanics -- `MARGIN_PCTL`/`cf.fires` boundary semantics (strictly below,
     not <=) and `MIN_STROKES_QUERY` wiring.
  4. SUPPLEMENT INVARIANT when disabled -- `_armc_from_terms` with `fired=False` must reproduce
     `full_pairs` exactly at ANY `w_r`, and asserts `terms` is empty (catching a caller bug that
     forgets to gate `terms` on `fired`).
  5. Held-Term source audit -- no Python argmin/argmax/sort-by-score/min-max-by-key deciding a
     ranking in the run script (the SAME regex discipline `test_conditional_foveation_migrated.py`
     / `test_relational_variation_migrated.py` already apply to their own modules).
  6. seeds/stroke_shapes.json md5 unchanged across this whole test module (no decode call here
     touches real drawer files, but the guard is cheap and matches every other test file's own
     discipline in this arc).
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import conditional_foveation as cf
from domains import relational_variation as rv
import scripts.jabberwock_omniglot_run51_conditional as run51

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(path: str):
    if not os.path.exists(path):
        return None
    return hashlib.md5(open(path, "rb").read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, ("seeds/stroke_shapes.json changed across "
                              "test_conditional_relational_migrated.py")


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


# ===================================================================================== #
# GATE 1 -- CONDITIONAL-FIRE mechanics (margin AND multi-stroke, both required).
# ===================================================================================== #
def test_fires_conditional_requires_both_low_margin_and_multistroke():
    threshold = 0.2
    assert run51._fires_conditional(0.05, threshold, True) is True
    assert run51._fires_conditional(0.05, threshold, False) is False, (
        "a single-stroke query must never fire -- it has no relations for r to adjudicate with")
    assert run51._fires_conditional(0.5, threshold, True) is False, (
        "a comfortable margin must not fire even when the query is multi-stroke")
    assert run51._fires_conditional(0.5, threshold, False) is False


def test_fires_conditional_boundary_is_strict():
    threshold = 0.2
    assert run51._fires_conditional(0.2, threshold, True) is False   # AT threshold: no fire.
    assert run51._fires_conditional(0.2 - 1e-9, threshold, True) is True


# ===================================================================================== #
# GATE 2 -- R-ADJUDICATION flips a synthetic tied-top-2 the right way.
# ===================================================================================== #
_STROKE0_PTS = [[0.0, 0.0], [0.1, 0.0], [0.2, 0.0]]
_STROKE1_PTS = [[1.0, 1.0], [1.1, 1.0], [1.2, 1.0]]


def _stroke_points():
    return [(_STROKE0_PTS, "q0", None, None), (_STROKE1_PTS, "q1", None, None)]


def _sig(rel0, rel1, cpose):
    sig = [["strokeq", 0, "q0"], ["strokeq", 1, "q1"],
           ["rel", 0, *rel0], ["rel", 1, *rel1]]
    for pred, v in zip(rv.CPOSE_SLOTS, cpose):
        sig.append([pred, v])
    return sig


_UNIFORM_WEIGHTS = {slot: 1.0 for slot in rv.ALL_SLOTS}


def test_relational_terms_for_top2_is_hermetic_and_matches_relational_distance(native):
    q_dec = (_stroke_points(), _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3)))
    c1_dec = (_stroke_points(), _sig((4, 5, 1, 3), (7, 6, 0, 4), (1, 0, 0, 3)))
    c2_dec = (_stroke_points(), _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3)))   # exact match.
    terms = run51._relational_terms_for_top2(native, q_dec, c1_dec, c2_dec, 11, 22,
                                              _UNIFORM_WEIGHTS)
    expect1 = rv.relational_distance(native, *q_dec, *c1_dec, _UNIFORM_WEIGHTS)["r"]
    expect2 = rv.relational_distance(native, *q_dec, *c2_dec, _UNIFORM_WEIGHTS)["r"]
    assert terms == {11: pytest.approx(expect1), 22: pytest.approx(expect2)}
    assert terms[22] == pytest.approx(0.0, abs=1e-9)     # exact match -> zero distance.
    assert terms[11] > terms[22]


def test_adjudication_flips_a_near_tied_top2_toward_the_relationally_true_candidate(native):
    """`full_pairs`: candidate 0 (WRONG) narrowly beats candidate 1 (TRUE) on geo alone. The
    relational evidence must clearly favour candidate 1 (an exact arrangement match) over
    candidate 0 (a mismatched arrangement on every slot) -- fused at a large-enough `w_r`, the
    argmin must FLIP from 0 to 1, exactly the mechanism this run's own eval measures at scale."""
    full_pairs = [(1.000, 0), (1.001, 1), (5.0, 2)]     # geo: 0 wins by a hair; true class is 1.
    query_dec = (_stroke_points(), _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3)))
    cand0_dec = (_stroke_points(), _sig((9, 9, 2, 1), (0, 0, 3, 7), (5, 5, 2, 1)))  # all mismatch.
    cand1_dec = (_stroke_points(), _sig((3, 3, 0, 3), (7, 7, 0, 3), (0, 0, 0, 3)))  # exact match.

    terms = run51._relational_terms_for_top2(native, query_dec, cand0_dec, cand1_dec, 0, 1,
                                              _UNIFORM_WEIGHTS)
    assert terms[1] < terms[0], "the exact-match candidate must have strictly lower r"

    pred_pre, _ = run51._armc_from_terms(native, full_pairs, False, {}, w_r=999.0)
    assert pred_pre == 0, "sanity: geo alone picks the WRONG candidate on this synthetic pair"

    pred_post, pairs_prime = run51._armc_from_terms(native, full_pairs, True, terms, w_r=1.0)
    assert pred_post == 1, "the adjudicated argmin must flip to the relationally-true candidate"
    by_idx = {ci: s for (s, ci) in pairs_prime}
    assert by_idx[2] == pytest.approx(5.0), "an un-adjudicated candidate must be untouched"


# ===================================================================================== #
# GATE 3 -- frozen-threshold mechanics (reused `cf.derive_threshold`/`cf.fires`, wired via
# run51's own constants).
# ===================================================================================== #
def test_margin_pctl_and_min_strokes_are_frozen_pre_registered_constants():
    assert run51.MARGIN_PCTL == 25.0
    assert run51.MIN_STROKES_QUERY == 2


def test_derive_threshold_still_a_plain_percentile():
    margins = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    t = cf.derive_threshold(margins, pctl=run51.MARGIN_PCTL)
    assert t == pytest.approx(np.percentile(margins, run51.MARGIN_PCTL))


# ===================================================================================== #
# GATE 4 -- SUPPLEMENT INVARIANT when disabled.
# ===================================================================================== #
def test_armc_from_terms_not_fired_is_byte_identical_at_any_w_r(native):
    full_pairs = [(0.42, 0), (0.10, 1), (0.77, 2)]
    for w_r in (0.0, 1.0, 123.456, -7.0):
        pred, pairs_prime = run51._armc_from_terms(native, full_pairs, False, {}, w_r)
        assert pairs_prime == full_pairs
        assert pred == 1     # argmin of the untouched pairs (0.10 is lowest).


def test_armc_from_terms_not_fired_rejects_a_nonempty_terms_dict(native):
    """A caller bug that computes `terms` but forgets to gate it on `fired=False` must be caught
    immediately, not silently masked by `supplement_pairs`' own no-op-on-empty-dict behaviour."""
    full_pairs = [(0.42, 0), (0.10, 1)]
    with pytest.raises(AssertionError):
        run51._armc_from_terms(native, full_pairs, False, {1: 5.0}, w_r=1.0)


def test_armc_from_terms_fired_adds_only_where_a_term_exists(native):
    full_pairs = [(1.0, 0), (2.0, 1), (3.0, 2)]
    terms = {1: 4.0, 2: -1.0}
    pred, pairs_prime = run51._armc_from_terms(native, full_pairs, True, terms, w_r=2.0)
    by_idx = {ci: s for (s, ci) in pairs_prime}
    assert by_idx[0] == pytest.approx(1.0)                  # untouched (no term, K=2 excludes it).
    assert by_idx[1] == pytest.approx(2.0 + 2.0 * 4.0)
    assert by_idx[2] == pytest.approx(3.0 + 2.0 * -1.0)
    assert pred == 0     # lowest score after fusion is still candidate 0.


# ===================================================================================== #
# GATE 5 -- held-Term source audit (no Python argmin/argmax/sort-by-score/min-max-by-key
# deciding a ranking in the run script).
# ===================================================================================== #
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def test_run51_no_python_decisions_source_audit():
    src = Path(run51.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "jabberwock_omniglot_run51_conditional.py must not call argmin/argmax in Python -- "
        "every ranking decision is `_argmin_ci` (a held Argmin evaluate)")
    assert not _MINMAX_KEY_RE.search(src), (
        "must not use Python's builtin min()/max() ranked by a key-function")
    assert not _SORT_KEY_RE.search(src), (
        "must not sort by a score-like key -- every ranking decision is a held Argmin/Argmax Term")


def test_run51_reuses_generic_conditional_foveation_scaffold_not_a_reimplementation():
    """The condition/supplement machinery must be IMPORTED from `conditional_foveation`, never
    re-implemented -- the launch brief's own reuse discipline ("run 45's conditional-fire
    scaffold... reused, not re-invented")."""
    src = Path(run51.__file__).read_text()
    assert "from domains import conditional_foveation as cf" in src
    for name in ("cf.top2_from_pairs", "cf.top2_margin", "cf.fires", "cf.supplement_pairs"):
        assert name in src, f"expected {name} to be reused from conditional_foveation.py"
    # and must NOT redefine its own top2/margin/fires/supplement functions.
    assert "def top2_from_pairs" not in src
    assert "def supplement_pairs" not in src
