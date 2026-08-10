"""tests/test_contrastive_verdict_migrated.py -- RUN 37A, GAP A: unit gates for
`domains/contrastive_verdict.py` (the JUDGE-A-TRIAL-BY-ITS-RESULT contrastive verdict, see
that module's own top-of-file docstring for the full design). Hermetic, synthetic strokes
only -- no Omniglot dataset needed; the REAL-DATA consistency check (top2's winner matching
`parse_marginal_verdict`'s own Argmax, and the n=400 accuracy reproduction) is the run
script's own `--stage guard`, mirroring `jabberwock_omniglot_run37c_hygiene.py::stage_verify`'s
precedent -- not duplicated here.

Gates:
  1. difference-element extraction: extra-stroke pair (unequal counts), same-count-one-
     differing-stroke pair (equal counts, worst-matched branch), single-stroke pair
     (degenerates to the whole stroke).
  2. contrastive score prefers the candidate whose difference element the query actually
     contains (synthetic, both directions).
  3. held-Term source audit (no Python argmin/argmax/sort-by-score in the new module) -- the
     SAME regex discipline `test_abs_read_no_python_decisions`/`test_ink_decode_no_python_
     decisions` already apply to their own modules.
  4. degenerate-filter interplay: an unfiltered degenerate stray-point stroke corrupts the
     difference element into a near-empty artifact; filtering it first (the run script's own
     `DropDegenerateFilter`, MANDATORY per the design) restores a real, multi-point element.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

from domains import contrastive_verdict as cv
from domains import omniglot_world as ow


def _native():
    return srs.Substrate()._inner


def _line(p0, p1, n=20) -> np.ndarray:
    return np.asarray(np.linspace(p0, p1, n), dtype=float)


def _jitter(arr: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """A tiny, deterministic perturbation -- avoids an exact-zero `PointSetDist` between two
    literally byte-identical point arrays, which trips a pre-existing `0.0 or float("nan")`
    idiom quirk in the REUSED `run36._greedy_stroke_match` (Python's `0.0` is falsy, so an
    EXACT-zero distance is silently replaced by `nan` there -- an honest anomaly this test
    suite surfaced and reports rather than patches, since that module is read-only reference
    machinery per this run's own design). Real, continuous, noisy ink never produces an
    exact-zero distance between two different drawings, so the quirk is invisible on real
    data; it only bites a synthetic fixture that deliberately reuses identical coordinates
    across two different "candidates" to model a shared stroke."""
    return arr + eps


# ===================================================================================== #
# GATE 1 -- difference-element extraction.
# ===================================================================================== #
def test_difference_element_extra_stroke_pair():
    """UNEQUAL stroke counts: candidate 1 has a real extra stroke (a 'hook') candidate 2
    lacks entirely. Design point 4: 'the unmatched stroke IS the difference element.' The
    shared line is made LONG relative to the hook so it DOMINATES each candidate's own
    normalization frame (`run36._normalize_glyph` centres+scales over the WHOLE glyph) --
    otherwise the hook's own presence/absence measurably shifts cand1's bbox/centroid
    relative to cand2's, which is a real property of per-glyph normalization (not a bug) but
    would make the "near-identical shared line" assertion below flaky for reasons unrelated
    to what this gate is testing."""
    native = _native()
    shared = _line((-5.0, 0.0), (5.0, 0.0), n=40)
    hook = _line((5.0, 0.0), (5.0, 0.3), n=8)
    cand1 = [shared, hook]              # 2 strokes
    cand2 = [_jitter(shared)]           # 1 stroke -- a strict (near-)subset of cand1

    d = cv.difference_elements(native, cand1, cand2)
    assert d["count_mismatch"] is True
    assert d["kind"] == "unmatched"
    assert d["single_stroke"] is False
    assert d["n_true"] == 2 and d["n_pred"] == 1
    # cand1 (the longer side) carries the real difference element; cand2, the strict
    # subset, has none of its own.
    assert d["diff1"], "cand1's extra hook must survive as its own difference element"
    assert not d["diff2"], "cand2 (subset) must have an EMPTY difference element"
    assert d["ok"] is True
    # exactly one shared pair was matched (the two near-identical lines).
    assert len(d["matched_costs"]) == 1
    assert d["matched_costs"][0] < 0.05, "the two near-IDENTICAL shared lines must match near-zero"


def test_difference_element_same_count_one_differing_stroke():
    """EQUAL stroke counts: one shared stroke matches near-perfectly, one stroke genuinely
    differs (hook up vs hook down) -- the WORST-MATCHED branch, held Argmax over the
    already-computed per-stroke costs picks the diverging pair, never a Python `max` ranked
    by a key-function. Again a LONG dominant shared line (see the extra-stroke-pair test's
    own note) so the small hooks' direction difference, not a whole-glyph frame shift, is
    what drives the worst-matched selection."""
    native = _native()
    shared = _line((-5.0, 0.0), (5.0, 0.0), n=40)
    hook_up = _line((5.0, 0.0), (5.0, 0.3), n=8)
    hook_down = _line((5.0, 0.0), (5.0, -0.3), n=8)
    cand1 = [shared, hook_up]
    cand2 = [_jitter(shared), hook_down]

    d = cv.difference_elements(native, cand1, cand2)
    assert d["count_mismatch"] is False
    assert d["kind"] == "worst_matched"
    assert d["single_stroke"] is False
    assert d["ok"] is True
    assert len(d["matched_costs"]) == 2
    # the shared-line pair must be the LOW-cost match, the hook pair the high-cost (worst)
    # match -- i.e. the worst-matched cost must be the max of the two.
    assert max(d["matched_costs"]) > min(d["matched_costs"])
    # both difference elements must be non-trivial point sets (the hooks), not the shared line.
    assert len(d["diff1"]) == len(hook_up)
    assert len(d["diff2"]) == len(hook_down)


def test_difference_element_single_stroke_degenerates_to_whole_stroke():
    """Design point 4: 'single-stroke candidates: difference element = whole stroke.' No
    special-cased branch -- this falls out of the SAME equal-count/worst-matched path with
    exactly one matched pair."""
    native = _native()
    cand1 = [_line((0.0, 0.0), (1.0, 0.0))]     # horizontal, 1 stroke
    cand2 = [_line((0.0, 0.0), (0.0, 1.0))]     # vertical, 1 stroke

    d = cv.difference_elements(native, cand1, cand2)
    assert d["single_stroke"] is True
    assert d["count_mismatch"] is False
    assert d["kind"] == "worst_matched"
    assert len(d["matched_costs"]) == 1
    # the difference element IS the whole (only) stroke on each side.
    assert len(d["diff1"]) == len(cand1[0])
    assert len(d["diff2"]) == len(cand2[0])


def test_difference_element_no_meaningful_difference_falls_back():
    """Two essentially IDENTICAL single-stroke candidates (near-zero real difference): the
    greedy match still produces a worst-matched pair (there is only one), and it IS a
    meaningful (non-degenerate) comparison -- `ok=True` even when the two shapes are almost
    the same. The TRUE 'no meaningful difference' fallback (both diffs empty) is exercised
    via `contrastive_pick`'s own `fallback_no_diff` gate below, which is the path a caller
    actually observes."""
    native = _native()
    same = _line((0.0, 0.0), (1.0, 0.0))
    d = cv.difference_elements(native, [same], [_jitter(same)])
    assert d["ok"] is True
    assert d["matched_costs"][0] < 1e-2


# ===================================================================================== #
# GATE 2 -- contrastive score prefers the candidate whose difference element the query
# actually contains.
# ===================================================================================== #
def test_contrastive_pick_flips_to_the_candidate_the_query_actually_matches():
    """Global verdict (simulated) wrongly picked candidate B (`cand1_idx`); the query's own
    ink actually contains candidate A's hook, not B's -- the contrastive pass must FLIP the
    winner to A (`cand2_idx` here, the runner-up slot), via the held two-sided Argmin."""
    native = _native()
    shared = _line((0.0, 0.0), (1.0, 0.0))
    hook_up = _line((1.0, 0.0), (1.0, 1.0), n=8)
    hook_down = _line((1.0, 0.0), (1.0, -1.0), n=8)
    cand_a = [shared, hook_up]              # the TRUE class
    cand_b = [_jitter(shared), hook_down]   # the wrongly-favoured global winner
    query = [shared.copy(), hook_up.copy() + 0.01]   # ink matching A's hook (tiny jitter)

    r = cv.contrastive_pick(native, query, cand_b, cand_a, cand1_idx=99, cand2_idx=42)
    assert r["decision"] == "two_sided"
    assert r["winner"] == 42, "the query's own ink matches candidate A -- the contrastive " \
                              "pass must override the wrong global pick"


def test_contrastive_pick_confirms_the_global_winner_when_it_is_already_right():
    """Symmetric control: the query matches B's hook -- the contrastive pass must NOT flip
    away from the (already correct) global winner."""
    native = _native()
    shared = _line((0.0, 0.0), (1.0, 0.0))
    hook_up = _line((1.0, 0.0), (1.0, 1.0), n=8)
    hook_down = _line((1.0, 0.0), (1.0, -1.0), n=8)
    cand_a = [shared, hook_up]
    cand_b = [_jitter(shared), hook_down]
    query = [shared.copy(), hook_down.copy() + 0.01]

    r = cv.contrastive_pick(native, query, cand_b, cand_a, cand1_idx=99, cand2_idx=42)
    assert r["decision"] == "two_sided"
    assert r["winner"] == 99


def test_contrastive_pick_one_sided_case_prefers_extra_when_query_contains_it():
    """UNEQUAL-count pair: candidate with the extra stroke wins the one-sided proxy when the
    query's own ink explains that extra region at least as well as the two candidates'
    shared strokes already explain each other."""
    native = _native()
    shared = _line((0.0, 0.0), (1.0, 0.0))
    hook = _line((1.0, 0.0), (1.0, 1.0), n=8)
    cand_with_hook = [shared, hook]
    cand_subset = [_jitter(shared)]
    query_has_hook = [shared.copy(), hook.copy() + 0.01]

    r = cv.contrastive_pick(native, query_has_hook, cand_with_hook, cand_subset,
                             cand1_idx=7, cand2_idx=8)
    assert r["decision"] == "one_sided"
    assert r["winner"] == 7, "the query contains the extra hook -- the extra-stroke " \
                             "candidate must win"


def test_contrastive_pick_fallback_no_diff():
    """Two candidates with literally nothing to compare (empty stroke lists on both sides)
    fall back to the global winner (`cand1_idx`), never crash."""
    native = _native()
    r = cv.contrastive_pick(native, [_line((0, 0), (1, 0))], [], [], cand1_idx=3, cand2_idx=4)
    assert r["decision"] == "fallback_no_diff"
    assert r["winner"] == 3


# ===================================================================================== #
# GATE 3 -- held-Term source audit (no Python argmin/argmax/sort-by-score).
# ===================================================================================== #
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")
_ALLOWED_SORT_KEYS: set[str] = set()


def test_contrastive_verdict_no_python_decisions():
    """The SAME audit `test_abs_read_no_python_decisions`/`test_ink_decode_no_python_
    decisions` already apply to their own modules, applied here to `domains/contrastive_
    verdict.py`: the difference-element SELECTION (worst-matched pair) and the final
    two-sided verdict are both held Argmax/Argmin Terms, never a Python ranking."""
    src = Path(cv.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "contrastive_verdict.py must not call argmin/argmax in Python -- the worst-matched-"
        "pair selection and the final verdict are held Argmax/Argmin Terms")
    assert not _MINMAX_KEY_RE.search(src), (
        "contrastive_verdict.py must not use Python's builtin min()/max() ranked by a "
        "key-function either")
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===================================================================================== #
# GATE 4 -- degenerate-filter interplay (RUN 37C's own artifact, reproduced synthetically).
# ===================================================================================== #
def test_degenerate_stroke_corrupts_difference_element_unless_filtered():
    """Reproduces RUN 36's own diagnosed artifact at unit scale: a stray degenerate
    (single-point) 'stroke' in the raw trace becomes candidate 1's ONLY unmatched stroke
    (since the real hook is dropped here to isolate the effect), so its difference element
    degenerates to a single point -- exactly the ink_fraction~0 phantom RUN 36 found. Loading
    with `drop_degenerate=True` first (mirroring `DropDegenerateFilter`, MANDATORY per this
    run's own design) removes it, and the difference element correctly falls back to the
    (real, multi-point) shared-line comparison instead."""
    native = _native()
    shared = _line((0.0, 0.0), (1.0, 0.0))
    degenerate = np.asarray([[0.5, 0.5]], dtype=float)   # a single recorded sample -- the
                                                          # EXACT `_is_degenerate_stroke`
                                                          # criterion ("m==1").
    assert ow._is_degenerate_stroke(degenerate) is True
    assert ow._is_degenerate_stroke(shared) is False

    cand1_raw = [shared, degenerate]         # unfiltered: 2 "strokes"
    cand2_raw = [_jitter(shared)]            # 1 stroke, near-identical to cand1's real stroke

    d_unfiltered = cv.difference_elements(native, cand1_raw, cand2_raw)
    assert d_unfiltered["count_mismatch"] is True
    assert d_unfiltered["kind"] == "unmatched"
    # the phantom difference element is the degenerate point ALONE -- exactly one point.
    assert len(d_unfiltered["diff1"]) == 1, (
        "before filtering, the difference element must be the single degenerate point -- "
        "the artifact RUN 36 diagnosed")

    # Now filter (the run script's own DropDegenerateFilter equivalent, applied inline here
    # since these are synthetic in-memory strokes rather than a file on disk).
    cand1_filtered = [s for s in cand1_raw if not ow._is_degenerate_stroke(s)]
    assert len(cand1_filtered) == 1

    d_filtered = cv.difference_elements(native, cand1_filtered, cand2_raw)
    assert d_filtered["count_mismatch"] is False, (
        "after filtering, both candidates are the SAME single real stroke -- equal counts")
    assert d_filtered["kind"] == "worst_matched"
    assert len(d_filtered["diff1"]) == len(shared), (
        "the difference element must now be the REAL shared line, not a 1-point artifact")


def test_load_strokes_drop_degenerate_default_is_false():
    """Byte-identical-default guard: `omniglot_world.load_strokes`'s own `drop_degenerate`
    param must still default to `False` -- this run's filter is opt-in via `DropDegenerateFilter`
    context-manager patching only, never a changed module default (see
    `jabberwock_omniglot_run37c_hygiene.DropDegenerateFilter`'s own docstring)."""
    import inspect
    sig = inspect.signature(ow.load_strokes)
    assert sig.parameters["drop_degenerate"].default is False
