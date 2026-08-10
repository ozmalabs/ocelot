"""tests/test_conditional_foveation_migrated.py -- RUN 45, PHASE 4: unit gates for
`domains/conditional_foveation.py` (CONDITIONAL FOVEATION -- 37A retried with its three
diagnosed failure causes fixed: conditional not unconditional, supplement not replacement,
aligned-frame not per-glyph-frame). Hermetic, synthetic strokes only -- no Omniglot dataset
needed; the REAL-DATA guard (GLOBAL reproduces 80.5%/k=322 exactly, background-sanity gate)
is the run script's own `--stage guard`/`--stage sanity`, mirroring RUN 37A/44b's own
precedent -- not duplicated here.

Gates:
  1. CONDITION mechanics: below-threshold fires, at/above-threshold does not, and the
     structural guarantee that a non-fired episode's supplemented score is BYTE-IDENTICAL to
     the untouched fused score (`supplement_pairs` with an empty `terms` dict is a no-op).
  2. ALIGNED-FRAME region comparison: a synthetic pair where INDEPENDENT per-glyph
     normalization (the diagnosed cause-3 bug) puts the query's own hook-feature CLOSER, in
     normalized units, to the WRONG candidate's differently-scaled distinguishing region than
     to the RIGHT one -- `difference_elements_aligned`/`foveate_terms`'s shared frame must
     recover the correct ordering (the query's hook must score closer to the candidate that
     actually carries the matching hook).
  3. SPREAD-MATCHED entry: `supplement_pairs` is invariant at `w_f=0` (and at an empty
     `terms` dict, any `w_f`), and correctly adds `w_f * terms[ci]` only for candidates that
     have a term.
  4. Held-Term source audit (no Python argmin/argmax/sort-by-score/min-max-by-key) -- the
     SAME regex discipline `test_contrastive_verdict_migrated.py`/`test_deform_metric_
     migrated.py` already apply to their own modules.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import conditional_foveation as cf


def _native():
    return srs.Substrate()._inner


def _line(p0, p1, n=20) -> np.ndarray:
    return np.asarray(np.linspace(p0, p1, n), dtype=float)


def _jitter(arr: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """SAME rationale as `test_contrastive_verdict_migrated.py`'s own `_jitter`: avoids an
    exact-zero `PointSetDist` between byte-identical arrays."""
    return arr + eps


# ===================================================================================== #
# GATE 1 -- CONDITION mechanics.
# ===================================================================================== #
def test_derive_threshold_is_a_percentile():
    margins = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    t = cf.derive_threshold(margins, pctl=25.0)
    assert t == pytest.approx(np.percentile(margins, 25.0))


def test_fires_below_threshold_true_above_false():
    threshold = 0.2
    assert cf.fires(0.05, threshold) is True
    assert cf.fires(0.2, threshold) is False   # boundary: strictly below, not <=
    assert cf.fires(0.5, threshold) is False


def test_top2_margin_from_pairs():
    native = _native()
    pairs = [(0.9, 0), (0.1, 1), (0.5, 2), (0.15, 3)]
    top2 = cf.top2_from_pairs(native, pairs)
    assert [ci for (_, ci) in top2] == [1, 3]
    margin = cf.top2_margin(top2)
    assert margin == pytest.approx(0.15 - 0.1)


def test_top2_from_pairs_single_candidate():
    native = _native()
    top2 = cf.top2_from_pairs(native, [(0.3, 5)])
    assert top2 == [(0.3, 5)]
    assert cf.top2_margin(top2) == float("inf")


def test_non_fired_episode_is_byte_identical_supplement_noop():
    """The structural guarantee: when the condition does not fire, the run script never
    populates `terms` for that episode -- `supplement_pairs` with an empty `terms` dict must
    reproduce `full_pairs` EXACTLY, at ANY `w_f`, so a non-fired episode's prediction is
    provably identical to the GLOBAL/GUARD prediction."""
    full_pairs = [(0.42, 0), (0.10, 1), (0.77, 2)]
    out = cf.supplement_pairs(full_pairs, {}, w_f=123.456)
    assert out == full_pairs


# ===================================================================================== #
# GATE 2 -- ALIGNED-FRAME region comparison (the cause-3 fix).
# ===================================================================================== #
def _scaled_candidates():
    """Two candidates sharing two REAL strokes (`line_a`, `line_b`) plus one OWN
    distinguishing stroke each, engineered so INDEPENDENT per-glyph normalization
    (`run36._normalize_glyph`, one abs-max scale PER GLYPH) gives the two glyphs WILDLY
    different effective scales: `cand_hook`'s own extent is dominated by a SMALL hook
    (largest coordinate ~2.2), `cand_decorative`'s own extent is dominated by a HUGE
    decorative stroke (largest coordinate ~52) -- so the SAME real-world shared geometry
    (`line_a`/`line_b`) lands at very different normalized magnitudes depending on which
    candidate it's read off, exactly RUN 37A's diagnosed frame-contamination cause. A query
    carrying the SAME small hook as `cand_hook` is the ground truth this gate checks against."""
    line_a = _line((0.0, 0.0), (2.0, 0.0), n=20)
    line_b = _line((2.0, 0.0), (2.0, 2.0), n=20)
    hook = _line((2.0, 2.0), (2.0, 2.2), n=8)              # small: cand_hook's own extra.
    decorative = _line((2.0, 2.0), (2.0, 52.0), n=8)       # huge: cand_decorative's own extra.

    cand_hook = [line_a, line_b, hook]
    cand_decorative = [_jitter(line_a), _jitter(line_b), decorative]
    query = [_jitter(line_a, 2e-4), _jitter(line_b, 2e-4), _jitter(hook, 2e-4)]
    return cand_hook, cand_decorative, query, hook, decorative


def test_joint_normalize_preserves_true_relative_scale():
    """`_joint_normalize` must NOT rescale the hook and the decorative stroke to look
    similarly-sized (which is what independent per-glyph normalization does, each dividing by
    its OWN dominant extent) -- in the SHARED frame, the decorative stroke (real length 50)
    must remain far larger than the hook (real length 0.2)."""
    cand_hook, cand_decorative, _query, hook, decorative = _scaled_candidates()
    _q, c1_norm, c2_norm = cf._joint_normalize([cand_hook, cand_hook, cand_decorative])
    hook_norm_extent = float(np.abs(c1_norm[2]).max())
    decorative_norm_extent = float(np.abs(c2_norm[2]).max())
    assert decorative_norm_extent > 5 * hook_norm_extent, (
        "the shared frame must preserve the TRUE size disparity between the hook and the "
        "decorative stroke, not rescale each into its own candidate's unit box")


def test_difference_elements_aligned_finds_the_true_distinguishing_pair():
    """The greedy match in the SHARED frame must pair `line_a`<->`line_a` and
    `line_b`<->`line_b` (near-identical real geometry) as the GOOD matches, leaving
    `hook`-vs-`decorative` as the single worst-matched (genuinely distinguishing) pair --
    the CORRECT diagnosis despite the huge scale disparity `test_joint_normalize_preserves_
    true_relative_scale` confirms is preserved, not erased."""
    native = _native()
    cand_hook, cand_decorative, _query, hook, decorative = _scaled_candidates()
    d = cf.difference_elements_aligned(native, cand_hook, cand_hook, cand_decorative)
    assert d["kind"] == "worst_matched"
    assert d["count_mismatch"] is False
    assert len(d["matched_costs"]) == 3
    # exactly one pair (hook vs decorative) should be the clear outlier cost.
    costs_sorted = sorted(d["matched_costs"])
    assert costs_sorted[-1] > 5 * costs_sorted[-2], (
        "hook-vs-decorative must be a clear cost OUTLIER against the two near-identical "
        "shared-line matches")
    assert len(d["diff1"]) == len(hook)
    assert len(d["diff2"]) == len(decorative)


def test_foveate_terms_scores_query_closer_to_its_true_matching_candidate():
    """THE headline gate: a query carrying the SAME small hook as `cand_hook` (not the huge
    decorative stroke) must score STRICTLY BETTER (lower) against `cand_hook`'s own
    difference element than against `cand_decorative`'s, once both are compared in the
    ALIGNED shared frame -- the query's real evidence (a small hook) must not be swamped or
    misjudged by the decorative candidate's own unrelated huge scale."""
    native = _native()
    cand_hook, cand_decorative, query, _hook, _decorative = _scaled_candidates()
    ft = cf.foveate_terms(native, query, cand_hook, cand_decorative, cand1_idx=11, cand2_idx=22)
    assert ft["decision"] == "two_sided"
    assert ft["terms"][11] < ft["terms"][22], (
        "the query's own hook must match cand_hook's difference element far better than "
        "cand_decorative's unrelated decorative stroke")


def test_foveate_terms_one_sided_neutral_side_is_zero():
    """UNEQUAL stroke counts: the subset candidate (no extra strokes of its own) must get an
    exact `0.0` term -- no evidence, no penalty, never a fabricated score."""
    native = _native()
    shared = _line((0.0, 0.0), (1.0, 0.0))
    hook = _line((1.0, 0.0), (1.0, 1.0), n=8)
    cand_with_hook = [shared, hook]
    cand_subset = [_jitter(shared)]
    query_has_hook = [shared.copy(), hook.copy() + 0.01]

    ft = cf.foveate_terms(native, query_has_hook, cand_with_hook, cand_subset,
                           cand1_idx=7, cand2_idx=8)
    assert ft["decision"] == "one_sided"
    assert ft["terms"][8] == 0.0
    assert ft["terms"][7] >= 0.0


def test_foveate_terms_fallback_no_diff_both_zero():
    native = _native()
    ft = cf.foveate_terms(native, [_line((0, 0), (1, 0))], [], [], cand1_idx=3, cand2_idx=4)
    assert ft["decision"] == "fallback_no_diff"
    assert ft["terms"] == {3: 0.0, 4: 0.0}


# ===================================================================================== #
# GATE 3 -- SPREAD-MATCHED entry (`supplement_pairs`).
# ===================================================================================== #
def test_supplement_pairs_invariant_at_w_f_zero():
    full_pairs = [(1.0, 0), (2.0, 1), (3.0, 2)]
    terms = {1: 100.0, 2: -50.0}
    out = cf.supplement_pairs(full_pairs, terms, w_f=0.0)
    assert out == full_pairs


def test_supplement_pairs_adds_only_where_a_term_exists():
    full_pairs = [(1.0, 0), (2.0, 1), (3.0, 2)]
    terms = {1: 4.0, 2: -1.0}
    out = cf.supplement_pairs(full_pairs, terms, w_f=2.0)
    by_idx = {ci: s for (s, ci) in out}
    assert by_idx[0] == pytest.approx(1.0)          # untouched (no term).
    assert by_idx[1] == pytest.approx(2.0 + 2.0 * 4.0)
    assert by_idx[2] == pytest.approx(3.0 + 2.0 * -1.0)


# ===================================================================================== #
# GATE 4 -- held-Term source audit (no Python argmin/argmax/sort-by-score/min-max-by-key).
# ===================================================================================== #
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def test_conditional_foveation_no_python_decisions_source_audit():
    """The greedy stroke-match assignment and the top-2 pick are both REPEATED held `Argmin`
    over a shrinking pool (`top2_from_pairs`/`_greedy_stroke_match_normed`), never a Python
    `sorted`/`min`/`max` ranked by a score-like key -- the SAME audit discipline `test_
    contrastive_verdict_migrated.py::test_contrastive_verdict_no_python_decisions` and
    `test_deform_metric_migrated.py::test_deform_metric_no_python_decisions_source_audit`
    already apply to their own modules."""
    src = Path(cf.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "conditional_foveation.py must not call argmin/argmax in Python")
    assert not _MINMAX_KEY_RE.search(src), (
        "conditional_foveation.py must not use Python's builtin min()/max() ranked by a "
        "key-function")
    assert not _SORT_KEY_RE.search(src), (
        "conditional_foveation.py must not sort by a score-like key -- every ranking "
        "decision is a held Argmin/Argmax Term")
