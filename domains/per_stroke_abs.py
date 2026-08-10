"""per_stroke_abs — FULLER program inference: BPL's actual engine. Upgrade AbS from one whole-
character point-set (2eb45a1a) to PER-STROKE: PARSE into strokes -> search the stroke CORRESPONDENCE
-> warp EACH stroke (per-stroke TpsDeformDist + ShapeContextDist). graph-native, earn-not-borrow, donkey=0.

THE INSIGHT: BPL recognizes by PER-STROKE program inference — a character is a PROGRAM (strokes +
their correspondence + per-stroke warps), not a holistic blob. The agent HOLDS the pieces: the
segmenter (parse into strokes, dd171c02), TpsDeformDist (per-stroke warp), ShapeContextDist (held Rust
Terms). Whole-character AbS is the COARSE version; this is the fuller inversion.

THE PROGRAM SCORE (lower = the candidate's program better explains the query):
  PARSE query+support into strokes (held load_strokes; each stroke a normalized point-set).
  CORRESPONDENCE: find the assignment of query strokes <-> support strokes (bounded: full permutation
    for <=4 strokes, else greedy) that MINIMIZES the total per-stroke warp cost.
  PER-STROKE WARP: each matched pair scored by held TpsDeformDist + ShapeContextDist.
  TOTAL = sum of per-stroke costs under the BEST correspondence + a parse-mismatch cost (|#strokes
    difference|) — the program's description length. Argmin over candidates wins.

numpy is ADAPTER-ONLY (load + normalize + resample each stroke into a point-set); every DISTANCE / the
correspondence DECISION is held Rust Terms (TpsDeformDist/ShapeContextDist) + a bounded search over
them. NO learned feature, NO borrowed net in the inference. No LLM.

Superseded (2026-07-02) by the graph-resident stroke codebook + segmentation-by-recognition
decode for handwriting: domains/stroke_codebook.py + domains/ink_decode.py (design
scratchpad/HANDWRITING_DESIGN.md). No behavior change here; this module is unmodified otherwise.
"""
from __future__ import annotations
import itertools as _it
import numpy as _np                 # ADAPTER: per-stroke point-set load/normalize/resample
import substrate_rs as _srs
import domains.omniglot_world as _ow

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
PARSE_COST = 0.5                     # cost per unmatched stroke (soft: parse counts vary across drawers)


def stroke_point_sets(path, N=24, max_strokes=6):
    """PARSE a drawing into per-stroke point-sets (held segmenter = load_strokes). The WHOLE character
    is normalized ONCE (translation+scale on the full glyph) so each stroke keeps its POSITION within
    the character (inter-stroke geometry) — per-stroke independent normalization would discard WHERE
    each stroke sits, which is essential for correspondence. numpy normalizes; orientation kept."""
    strokes = _ow.load_strokes(path)
    allp = _np.concatenate([_np.asarray(s, float) for s in strokes if len(s)], 0) if strokes else None
    if allp is None or len(allp) < 3:
        return []
    mn = allp.mean(0); sc = _np.abs(allp - mn).max() + 1e-9      # whole-char normalization (shared)
    out = []
    for s in strokes[:max_strokes]:
        a = (_np.asarray(s, float) - mn) / sc
        if len(a) < 2:
            continue
        d = _np.sqrt((_np.diff(a, axis=0) ** 2).sum(1))
        cum = _np.concatenate([[0.0], _np.cumsum(d)])
        if cum[-1] == 0:
            continue
        u = _np.linspace(0.0, cum[-1], N)
        out.append(_np.stack([_np.interp(u, cum, a[:, 0]), _np.interp(u, cum, a[:, 1])], 1).tolist())
    return out


def _stroke_warp_cost(qs, ss):
    """PER-STROKE warp cost (held Terms): TpsDeformDist + ShapeContextDist between two stroke point-sets.
    LOWER = the support stroke warps onto the query stroke better. The Rust evaluator computes it."""
    tp = float(_S.evaluate({"type": "TpsDeformDist", "a": _L(qs), "b": _L(ss)}, {}))
    sc = float(_S.evaluate({"type": "ShapeContextDist", "a": _L(qs), "b": _L(ss)}, {}))
    return tp + sc


def _best_correspondence(q_strokes, s_strokes, *, beam_cap=4):
    """Search the stroke CORRESPONDENCE that minimizes total per-stroke warp. FULL permutation when
    min(#strokes) <= beam_cap (1-4 strokes = the common case); else GREEDY assignment. Returns the
    minimal total per-stroke cost (the decision is the held metrics' argmin over assignments)."""
    nq, ns = len(q_strokes), len(s_strokes)
    if nq == 0 or ns == 0:
        return PARSE_COST * max(nq, ns, 1)
    # cost matrix (held per-stroke warp) — numpy holds the values, Rust computed each entry
    C = _np.zeros((nq, ns))
    for i in range(nq):
        for j in range(ns):
            C[i, j] = _stroke_warp_cost(q_strokes[i], s_strokes[j])
    m = min(nq, ns)
    if m <= beam_cap:
        # FULL: best injective assignment of the smaller side onto the larger
        if nq <= ns:
            best = min(sum(C[i, perm[i]] for i in range(nq))
                       for perm in _it.permutations(range(ns), nq))
        else:
            best = min(sum(C[perm[j], j] for j in range(ns))
                       for perm in _it.permutations(range(nq), ns))
    else:
        # GREEDY: repeatedly take the cheapest available (row,col), bounded
        best = 0.0
        usedr, usedc = set(), set()
        flat = sorted(((C[i, j], i, j) for i in range(nq) for j in range(ns)))
        for c, i, j in flat:
            if i in usedr or j in usedc:
                continue
            best += c; usedr.add(i); usedc.add(j)
            if len(usedr) == m:
                break
    # parse-mismatch cost: unmatched strokes (description-length penalty)
    return best + PARSE_COST * abs(nq - ns)


def program_score(query_strokes, support_strokes):
    """The PER-STROKE program score: the best stroke-correspondence's total warp + parse cost.
    LOWER = the candidate's program (strokes+correspondence+warps) better explains the query."""
    return _best_correspondence(query_strokes, support_strokes)


def classify(query_strokes, support_sets):
    """Classify a query by FULLER program inference: argmin over candidates of program_score.
    Pure held-Term inversion (per-stroke warp + correspondence search) — no learned feature."""
    scores = [program_score(query_strokes, s) for s in support_sets]
    return int(_np.argmin(scores)), scores
