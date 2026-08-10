"""tests/test_committed_shape_migrated.py -- RUN 37B, GAP B: unit gates for
`domains/committed_shape.py` (the "committed shape" third proposal modality -- a coarse
per-stroke program-type identity, used ONLY to widen the existing structural shortlist via a
pure-additive union, per RUN 37A's own law: "focused/weak evidence SUPPLEMENTS integrated
evidence, never replaces it"). Hermetic, synthetic strokes only, a FIXED local quantization
grid (not cited from any real run -- mirrors `tests/test_stroke_programs_migrated.py`'s own
"test-local" fixture discipline) -- no Omniglot dataset, no LEARN population needed.

Gates:
  1. commit_shape determinism (same strokes -> same string, twice) + correct per-stroke join
     order (draw order preserved) + the "∅" degenerate/empty conventions.
  2. propose_by_committed_shape: exact-match-first correctness, the 1-edit fallback (only
     engaged when exact match is empty), and the pre-registered `k` cap.
  3. token edit-distance sanity (identical=0, one substitution/insertion/deletion=1, two
     edits=2) underlying the fallback rule.
  4. union_candidates: the ADDITIVE invariant -- shortlist is always an exact, order-preserved
     PREFIX of the result; no duplicates; RUN 37A's law enforced structurally, not by
     discipline alone.
  5. held-Term source audit -- no Python argmin/argmax/sort-by-score/native.evaluate in this
     module (the SAME regex discipline `test_contrastive_verdict_migrated.py`'s own GATE 3
     applies to `domains/contrastive_verdict.py`), documenting that exact-match/edit-distance
     proposal is a structural comparison, never a continuous score needing a held Term.
  6. `load_cited_program_edges` reads RUN 35's own already-fit checkpoint correctly (skipped,
     not failed, if that checkpoint is absent from disk).
"""
from __future__ import annotations

import inspect
import os
import re

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import committed_shape as cs

# Fixed, test-local quantization grid (NOT cited from any real run -- self-contained, mirrors
# test_stroke_programs_migrated.py's own LEVEL_EDGES/DELTA_EDGES fixture).
LEVEL_EDGES = list(np.linspace(-180.0, 180.0, 13))
DELTA_EDGES = [-360.0, -60.0, -20.0, 0.0, 20.0, 60.0, 360.0]
TOL_DEG = 1.0
SEGMENTS = 8
MAX_KNOTS = 16


def _edges_kwargs() -> dict:
    return dict(tol_deg=TOL_DEG, level_edges=LEVEL_EDGES, delta_edges=DELTA_EDGES,
                segments=SEGMENTS, max_knots=MAX_KNOTS)


def _line_points(length: float = 10.0, n: int = 40) -> list:
    return np.stack([np.linspace(0.0, length, n), np.zeros(n)], axis=1).tolist()


def _circle_points(radius: float = 20.0, n: int = 320) -> list:
    theta = np.linspace(0.0, 2 * np.pi, n)
    return np.stack([radius * np.cos(theta), radius * np.sin(theta)], axis=1).tolist()


# ===================================================================================== #
# GATE 1 -- commit_shape determinism, draw order, degenerate conventions.
# ===================================================================================== #
def test_stroke_coarse_type_line_and_circle_match_stroke_programs():
    assert cs.stroke_coarse_type(_line_points(), **_edges_kwargs()) == "L"
    assert cs.stroke_coarse_type(_circle_points(), **_edges_kwargs()) == "A"


def test_stroke_coarse_type_degenerate_is_empty_set_not_a_crash():
    assert cs.stroke_coarse_type([], **_edges_kwargs()) == "∅"
    assert cs.stroke_coarse_type([[0.0, 0.0]], **_edges_kwargs()) == "∅"
    assert cs.stroke_coarse_type([[0.0, 0.0], [0.0, 0.0]], **_edges_kwargs()) == "∅"


def test_commit_shape_joins_per_stroke_types_in_draw_order():
    glyph = [_line_points(), _circle_points()]
    assert cs.commit_shape(glyph, **_edges_kwargs()) == "L;A"
    # order matters -- reversing the draw order changes the commit.
    glyph_rev = [_circle_points(), _line_points()]
    assert cs.commit_shape(glyph_rev, **_edges_kwargs()) == "A;L"


def test_commit_shape_no_strokes_is_empty_set():
    assert cs.commit_shape([], **_edges_kwargs()) == "∅"


def test_commit_shape_determinism():
    glyph = [_line_points(), _circle_points(), _line_points(length=4.0)]
    c1 = cs.commit_shape(glyph, **_edges_kwargs())
    c2 = cs.commit_shape(glyph, **_edges_kwargs())
    assert c1 == c2 == "L;A;L"


def test_commit_tokens_roundtrip():
    assert cs.commit_tokens("L;A;L") == ("L", "A", "L")
    assert cs.commit_tokens("∅") == ("∅",)


# ===================================================================================== #
# GATE 3 -- token edit-distance sanity (underlies the fallback rule).
# ===================================================================================== #
def test_token_edit_distance_identical_is_zero():
    assert cs._token_edit_distance(("L", "A"), ("L", "A")) == 0


def test_token_edit_distance_one_substitution():
    assert cs._token_edit_distance(("L", "A"), ("L", "R")) == 1


def test_token_edit_distance_one_insertion_or_deletion():
    assert cs._token_edit_distance(("L", "A"), ("L", "A", "L")) == 1
    assert cs._token_edit_distance(("L", "A", "L"), ("L", "A")) == 1


def test_token_edit_distance_two_edits():
    assert cs._token_edit_distance(("L", "A"), ("R", "R")) == 2
    assert cs._token_edit_distance(("L", "A"), ("R", "R", "R")) >= 2


# ===================================================================================== #
# GATE 2 -- propose_by_committed_shape: exact-first, 1-edit fallback, k cap.
# ===================================================================================== #
def test_propose_exact_match_returns_only_exact_indices():
    query = "L;A"
    exemplars = ["L;A", "L;R", "L;A", "A;L", "L;A"]
    got = cs.propose_by_committed_shape(query, exemplars, k=10)
    assert got == [0, 2, 4], got


def test_propose_exact_match_never_leaks_edit1_candidates():
    query = "L;A"
    # index 1 is edit-distance 1 from query ("L;A" -> "L;R" is one substitution) but index 0
    # is an EXACT match -- edit1 candidates must not appear once an exact match exists.
    exemplars = ["L;A", "L;R"]
    got = cs.propose_by_committed_shape(query, exemplars, k=10)
    assert got == [0], got


def test_propose_falls_back_to_edit1_only_when_exact_is_empty():
    query = "L;A"
    exemplars = ["L;R", "A;A", "R;R;R", "L;A;L"]
    # "L;R" (sub, d=1), "A;A" (sub, d=1), "R;R;R" (d>=2), "L;A;L" (insertion, d=1)
    got = cs.propose_by_committed_shape(query, exemplars, k=10)
    assert got == [0, 1, 3], got


def test_propose_no_candidates_is_empty_not_a_crash():
    query = "L;A"
    exemplars = ["R;R;R;R", "A;A;A"]
    assert cs.propose_by_committed_shape(query, exemplars, k=10) == []


def test_propose_respects_k_cap_on_exact_matches():
    query = "L;A"
    exemplars = ["L;A"] * 8
    got = cs.propose_by_committed_shape(query, exemplars, k=3)
    assert got == [0, 1, 2], got


def test_propose_respects_k_cap_on_edit1_fallback():
    query = "L;A"
    exemplars = ["L;R", "A;A", "L;L", "R;A"]   # all edit-distance 1
    got = cs.propose_by_committed_shape(query, exemplars, k=2)
    assert got == [0, 1], got


def test_match_kind_classification():
    assert cs.match_kind("L;A", ["L;A", "X"]) == "exact"
    assert cs.match_kind("L;A", ["L;R", "X;Y;Z;W"]) == "edit1"
    assert cs.match_kind("L;A", ["R;R;R;R"]) == "none"


# ===================================================================================== #
# GATE 4 -- union_candidates: the ADDITIVE invariant (RUN 37A's law, enforced structurally).
# ===================================================================================== #
def test_union_shortlist_is_always_an_exact_prefix():
    shortlist = [5, 2, 9, 1]
    committed = [9, 2, 7, 3]
    union = cs.union_candidates(shortlist, committed)
    assert union[:len(shortlist)] == shortlist, (
        "the existing shortlist must survive as an unmodified, unreordered PREFIX")
    assert union == [5, 2, 9, 1, 7, 3]


def test_union_no_duplicates():
    shortlist = [1, 2, 3]
    committed = [3, 2, 1]   # entirely overlapping -- nothing new to add.
    assert cs.union_candidates(shortlist, committed) == [1, 2, 3]


def test_union_empty_committed_is_shortlist_unchanged():
    shortlist = [4, 1, 8]
    assert cs.union_candidates(shortlist, []) == shortlist


def test_union_empty_shortlist_is_just_committed_in_order():
    committed = [3, 1, 2]
    assert cs.union_candidates([], committed) == committed


# ===================================================================================== #
# GATE 5 -- held-Term source audit (no Python argmin/argmax/sort-by-score/native.evaluate;
# the SAME regex discipline test_contrastive_verdict_migrated.py's own GATE 3 applies).
# ===================================================================================== #
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_SCORE_KEYWORDS = ("score", "dist", "count", "covered", "vote", "fit")


def _code_only(mod) -> str:
    """Strip triple-quoted docstrings first -- the module/function docstrings PROSE names
    Terms/held-mechanisms for context (e.g. this module's own audit note), which would
    otherwise false-positive the token scan below; only ACTUAL code is disqualifying (mirrors
    `tests/test_mouse_model_migrated.py`'s own `test_mouse_model_makes_no_graph_or_term_calls`
    precedent)."""
    return re.sub(r'""".*?"""', "", inspect.getsource(mod), flags=re.DOTALL)


def test_committed_shape_no_python_ranking_decisions():
    src = _code_only(cs)
    assert ".evaluate(" not in src, (
        "committed_shape.py's own proposal rule is structural equality/edit-distance, not a "
        "Term-scored decision -- it must not call native.evaluate")
    assert not _BANNED_CALL_RE.search(src), (
        "committed_shape.py must not rank candidates via Python argmin/argmax")
    assert not _MINMAX_KEY_RE.search(src), (
        "committed_shape.py must not use Python's builtin min()/max() ranked by a key-function")
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


def test_committed_shape_mints_nothing():
    src = _code_only(cs)
    forbidden = ["teach(", "add_node(", "add_edge(", "run_rules(", "decode_ink("]
    hits = [tok for tok in forbidden if tok in src]
    assert not hits, f"committed_shape.py must mint nothing -- found: {hits}"


# ===================================================================================== #
# GATE 6 -- load_cited_program_edges (RUN 35's own already-fit checkpoint).
# ===================================================================================== #
@pytest.mark.skipif(not os.path.exists(cs.CITED_PROGRAMS_PATH),
                     reason="results/run35_checkpoints/programs.json not present on disk")
def test_load_cited_program_edges_has_expected_shape():
    edges = cs.load_cited_program_edges()
    assert set(edges.keys()) == {"tol_deg", "level_edges", "delta_edges"}
    assert isinstance(edges["tol_deg"], float)
    assert len(edges["level_edges"]) >= 2
    assert len(edges["delta_edges"]) >= 2
    assert all(edges["level_edges"][i] < edges["level_edges"][i + 1]
               for i in range(len(edges["level_edges"]) - 1))
