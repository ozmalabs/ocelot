"""committed_shape -- RUN 37B GAP B: a THIRD PROPOSAL MODALITY, ADDITIVE ONLY.

RUN 37A's law (commit cca938fd, BINDING for this module's design): "FOCUSED/WEAK EVIDENCE
SUPPLEMENTS INTEGRATED EVIDENCE, NEVER REPLACES IT." RUN 36 (5aa6bcb6) found 1-2-stroke
classes carry most of the proposal/shortlist failure mass (little arrangement for the
structural composed-signature proposal to grab onto -- `character_compose.
compose_character_signature` is nearly EMPTY for a 1-2-stroke glyph). RUN 35's own program-
type tokenizer (`domains/stroke_programs.py`) measured a real-but-weak class signal at COARSE
grain (token TYPES only, e.g. "L-A-R" -- 1.9x the shuffled null, just under the 2.0x bar for a
full featureset). Gap B's translation: that weak signal is exactly what a PROPOSAL (not a
verdict) needs -- "bins propose, continuous decides" (RUN 16's own reconciliation). This
module builds the agent's "committed shape": a coarse per-stroke program-type identity for a
whole glyph (draw order preserved), used ONLY to widen the shortlist that already exists,
NEVER to replace or reorder it (structurally enforced by `union_candidates`, below -- the
existing shortlist's own members and order are always a PREFIX of the returned union).

ARCHITECTURE (CLAUDE.md): a WORLD-ADAPTER-class feature extractor, the same class of thing
`domains/stroke_programs.py`/`domains/adaptive_bins.py` already are -- every function here is
a MECHANICAL, DETERMINISTIC transform over numbers/strings already produced by the existing
held `StrokeQuantize` Term (via `stroke_programs.stroke_turn_sequence`, reused verbatim) or by
plain draw-order stroke geometry. No conditional over graph state, no rule engine, no agent
decision, no `teach()`/codebook mutation anywhere in this module -- it MINTS NOTHING.

HELD-TERM SOURCE AUDIT (what does and does NOT need a Term here): the only numeric geometry
this module touches is the per-segment turn residual `StrokeQuantize` already computes
(reached via `stroke_programs.stroke_turn_sequence` -> `ink.ingest_ink`, an EXISTING held
Term evaluation, not reimplemented). Everything downstream of that -- joining per-stroke
coarse-type strings into one glyph identity, comparing two identity strings for EXACT equality,
and counting a bounded TOKEN-LIST edit distance -- is discrete/structural comparison over
already-computed labels, not a continuous SCORE, so there is no Argmin/Argmax/distance-Term
to hold: `propose_by_committed_shape` never ranks candidates by a computed number, it only
partitions them into "identity matches" / "one token away" / "unrelated" and returns index
sets in a fixed (exemplar-index) order. `tests/test_committed_shape_migrated.py`'s own source
audit asserts this precisely (no `native.evaluate`/`Argmax`/`Argmin`/`sorted(..., key=` in this
module).

THE COMMITTED SHAPE (`commit_shape`): for a glyph's own strokes, in DRAW ORDER (the order
`omniglot_world.load_strokes` already yields, "pen-down order"), globally denoise each stroke
(`mouse_model.denoise_path_global`, RUN 34b's own proven instrument -- the SAME denoise RUN 35
cites for its LEARN population), tokenize each stroke's turn sequence into RUN 35's own
program-token sequence (`stroke_programs.tokenize_turn_sequence`), and take its COARSE
identity (token TYPES only, e.g. "L-A-R" or a degenerate stroke's own "∅"). The glyph's
committed shape is those per-stroke coarse strings joined with ";" in draw order (e.g.
"L-A-R;L" for a two-stroke glyph) -- deterministic, no RNG, no fitting.

CITED EDGES (`load_cited_program_edges`): `tol_deg`/`level_edges`/`delta_edges` are read
VERBATIM from `results/run35_checkpoints/programs.json` -- the SAME quantization RUN 35 already
fit once over its 1500-stroke LEARN population (`domains.adaptive_bins.compute_quantile_edges`
et al, reused, never refit here). This module never re-fits an edge set; a caller that wants a
DIFFERENT edge set (e.g. a unit test's own small fixed grid) passes `tol_deg`/`level_edges`/
`delta_edges` explicitly -- there is no hidden default.

PROPOSAL (`propose_by_committed_shape`): given a query's own committed-shape string and a
block's own list of exemplar committed-shape strings, return candidate indices whose committed
shape EXACTLY matches the query's (pre-registered PRIMARY rule); if (and only if) that yields
no candidates, fall back to exemplars within TOKEN edit-distance 1 (one stroke's coarse type
differs, inserted, or deleted -- `_token_edit_distance`, a standard list-Levenshtein, cheap at
these tiny stroke-count lengths). Capped at `k_add` (a pre-registered constant, default 5,
NEVER tuned per-query) -- an honest, bounded ADDITION, matching the existing shortlist's own
`SHORTLIST_K`-is-a-logged-constant discipline (`abs_read.propose_top_k`'s own doc).

ADDITIVE UNION (`union_candidates`): the existing shortlist's members and order are preserved
EXACTLY as a prefix; committed-shape candidates not already present are appended in exemplar-
index order. This is the structural enforcement of RUN 37A's law -- a caller cannot construct a
union that drops or reorders a shortlist member through this function's own contract, and
`tests/test_committed_shape_migrated.py` gates the invariant directly.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np

from domains import mouse_model as mm
from domains import stroke_programs as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITED_PROGRAMS_PATH = os.path.join(ROOT, "results", "run35_checkpoints", "programs.json")

K_ADD_DEFAULT = 5   # pre-registered cap on committed-shape proposals ADDED into the union
                     # (never tuned per-query -- see module docstring).


def load_cited_program_edges(path: str = CITED_PROGRAMS_PATH) -> dict:
    """`{"tol_deg": float, "level_edges": [...], "delta_edges": [...]}`, read VERBATIM from
    RUN 35's own already-fit checkpoint (see module docstring) -- never refit here."""
    with open(path) as f:
        d = json.load(f)
    return {"tol_deg": d["tol_deg"], "level_edges": d["level_edges"], "delta_edges": d["delta_edges"]}


# --------------------------------------------------------------------------------------------- #
#  ONE STROKE -> its coarse program-type string (denoise -> StrokeQuantize residual -> tokenize).
# --------------------------------------------------------------------------------------------- #
def stroke_coarse_type(points, *, tol_deg: float, level_edges: list, delta_edges: list,
                        segments: int, max_knots: int) -> str:
    """`"∅"` for a degenerate (<2-point, or <2-knot after ingest) stroke -- an honest
    empty type, never a crash. `mouse_model.denoise_path_global` already no-ops (returns the
    input unchanged) on a <3-point stroke, so no separate guard is needed for that case."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return "∅"
    dn = mm.denoise_path_global(pts).tolist()
    import substrate_rs as srs   # local import -- mirrors stroke_programs.py's own throwaway-
                                  # substrate idiom, keeps this module importable without the
                                  # Rust extension for callers that never tokenize a real stroke.
    s = srs.Substrate()
    turn_seq = sp.stroke_turn_sequence(s, dn, segments=segments, max_knots=max_knots)
    if not turn_seq:
        return "∅"
    res = sp.tokenize_turn_sequence(turn_seq, tol_deg, level_edges, delta_edges=delta_edges)
    return res["coarse"]


# --------------------------------------------------------------------------------------------- #
#  THE GLYPH-LEVEL COMMITTED SHAPE -- per-stroke coarse types, joined in draw order.
# --------------------------------------------------------------------------------------------- #
def commit_shape(strokes: list, *, tol_deg: float, level_edges: list, delta_edges: list,
                  segments: int, max_knots: int) -> str:
    """`strokes`: a glyph's own list of per-stroke point arrays, in DRAW ORDER (the order
    `omniglot_world.load_strokes` yields). Returns the ";"-joined per-stroke coarse-type
    string -- e.g. `"L-A-R;L"` for a two-stroke glyph, `"∅"` for a strokeless glyph
    (an honest empty commit, never a crash). Deterministic: no RNG, no fitting, no mutation."""
    if not strokes:
        return "∅"
    parts = [stroke_coarse_type(s, tol_deg=tol_deg, level_edges=level_edges,
                                 delta_edges=delta_edges, segments=segments, max_knots=max_knots)
             for s in strokes]
    return ";".join(parts)


def commit_tokens(commit: str) -> tuple:
    """Split a joined commit string back into its per-stroke tokens (";"  is never produced
    inside a single stroke's own coarse string -- `format_coarse` only ever emits letters and
    "-", or the single sentinel "∅" -- so this split is lossless)."""
    if commit == "∅":
        return ("∅",)
    return tuple(commit.split(";"))


# --------------------------------------------------------------------------------------------- #
#  TOKEN-LIST EDIT DISTANCE (standard Levenshtein over the per-stroke token sequence, not over
#  raw characters -- "one stroke's type differs" is the meaningful unit of change here, not
#  "one character differs"). Structural/discrete, not a Term-scored decision (see module
#  docstring's own audit note).
# --------------------------------------------------------------------------------------------- #
def _token_edit_distance(a: tuple, b: tuple) -> int:
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


# --------------------------------------------------------------------------------------------- #
#  PROPOSAL -- exact-match first, 1-edit fallback only when exact match is empty. Capped at
#  `k`, deterministic exemplar-index order (never a Python sort by a computed score).
# --------------------------------------------------------------------------------------------- #
def propose_by_committed_shape(query_commit: str, exemplar_commits: list,
                                k: int = K_ADD_DEFAULT) -> list:
    """Returns up to `k` exemplar indices, in exemplar-index order. PRIMARY: exact
    string-equality matches. FALLBACK (only when the primary rule finds nothing): exemplars
    whose committed-shape token sequence is exactly TOKEN edit-distance 1 from the query's own
    (see `_token_edit_distance`). `[]` (never a crash, never padded) when neither rule finds a
    candidate -- an honest "this modality has nothing to add" result."""
    exact = [i for i, c in enumerate(exemplar_commits) if c == query_commit]
    if exact:
        return exact[:k]
    q_tok = commit_tokens(query_commit)
    edit1 = [i for i, c in enumerate(exemplar_commits)
             if _token_edit_distance(q_tok, commit_tokens(c)) == 1]
    return edit1[:k]


def match_kind(query_commit: str, exemplar_commits: list) -> str:
    """Reporting-only classification of which rule `propose_by_committed_shape` would use for
    this query against this exemplar pool -- `"exact"` / `"edit1"` / `"none"`. Never itself a
    ranking decision; a caller wanting the actual candidate list still calls
    `propose_by_committed_shape`."""
    if any(c == query_commit for c in exemplar_commits):
        return "exact"
    q_tok = commit_tokens(query_commit)
    if any(_token_edit_distance(q_tok, commit_tokens(c)) == 1 for c in exemplar_commits):
        return "edit1"
    return "none"


# --------------------------------------------------------------------------------------------- #
#  ADDITIVE UNION -- the structural enforcement of RUN 37A's law. `shortlist` is ALWAYS a
#  prefix of the result, in its own original order; `committed` contributes only genuinely NEW
#  indices, appended in exemplar-index order. A caller can never use this function to drop or
#  reorder a shortlist member.
# --------------------------------------------------------------------------------------------- #
def union_candidates(shortlist: list, committed: list) -> list:
    seen = set(shortlist)
    extra = [c for c in committed if c not in seen]
    return list(shortlist) + extra


__all__ = [
    "K_ADD_DEFAULT", "CITED_PROGRAMS_PATH", "load_cited_program_edges",
    "stroke_coarse_type", "commit_shape", "commit_tokens",
    "propose_by_committed_shape", "match_kind", "union_candidates",
]
