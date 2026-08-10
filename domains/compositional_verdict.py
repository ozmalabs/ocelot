"""compositional_verdict -- RUN 54's MULTI-GRAIN PREDICTIVE-CODING VERDICT (the loop-flip
landed as GRAPH STRUCTURE, not a bolt-on).

THE ARCHITECTURE (creator correction, load-bearing): a graph HOLDS a character at MULTIPLE
GRAINS AT ONCE -- you do not choose between whole-shape and decomposition. So the verdict is not
"per-stroke INSTEAD OF whole-shape"; it is the whole-shape residual (the standing 80.5% GUARD's
own score) as the TOP-LEVEL term, WITH the per-stroke and relational levels ADDED beneath it:

    TOTAL[cand] = w_whole * whole_shape_residual        (the GUARD's own parse-marginal error)
                + w_stroke * Sum(per-stroke residuals)  (per drawn-stroke SC+TPS geometry)
                + w_rel   * Sum(precision-weighted relation residuals)  (run-50 tightness)

argmin over candidates = the verdict.

WHY THIS IS NOT THE FAILED BOLT-ON (runs 45/49/51): those added ONE scalar correction term
(redundant/weak, diluting the geometry verdict). THIS adds MULTI-GRAIN GRAPH STRUCTURE where run
50 PROVED the grains carry ORTHOGONAL information -- whole-shape coherence at the top, part
geometry in the middle, arrangement at the relations (corr(r, geo)=0.093, LICENSED). Summing
prediction-error across ORTHOGONAL levels reads COMPLEMENTARY structure; it does not re-add the
same evidence. The whole-shape term stays IN, so the verdict structurally cannot badly
underperform the GUARD: at `w_stroke=0, w_rel=0, w_whole=1` it REDUCES to the whole-shape verdict
BYTE-IDENTICALLY (the GUARD-reduction invariant, `total_error_term`'s own unit test) -- worst
case the added levels calibrate to ~0.

KEY UNIFICATION (A structural + C mechanism are ONE computation): run 50's per-relation TIGHTNESS
IS predictive-coding's PRECISION. A tight relation (low within-class variance, identity-bearing)
= a HIGH-precision prediction whose residual counts fully; a loose relation (free to vary) =
LOW-precision, residual discounted. `relation_residual` weights each relation mismatch by the
frozen run-50 tightness -- so the tightness-weighting IS the precision term. The whole verdict is
the prediction error read across all grains, precision-weighted where run 50 measured the
precision.

ARCHITECTURE (CLAUDE.md): every function here is MECHANICAL -- a Term builder (the weighted-Plus
combination, the Argmin verdict), a fixed-arity read of a value a HELD Term already produced
(`per_stroke_residual` / `relation_residual` evaluate held SC+TPS / relational Terms and read the
scalar), or plain arithmetic over already-computed numbers (`spread_match_weights`). The RANKING
DECISION is the held `Argmin` (`_argmin_pairs_term`); combining three already-computed scalars
with three weights is arithmetic, not a ranking (`domains/abs_read.py`'s own audit precedent:
`propose_top_k`'s residual-combined score). No Python argmin/argmax/sort-by-score anywhere in this
module -- gated by `tests/test_compositional_verdict_migrated.py::
test_compositional_verdict_no_python_decisions`.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from domains import abs_read as ar
from domains import relational_variation as rv
from scripts import jabberwock_omniglot_run36_failures as run36
from scripts import jabberwock_omniglot_run39_motorplan as run39

DEFAULT_STROKE_N_POINTS = 24


# --------------------------------------------------------------------------- #
#  Held Term builders -- duplicated locally per this codebase's own established
#  convention of a small, pure, call-site-local Term builder.
# --------------------------------------------------------------------------- #
def _argmin_pairs_term(pairs: list) -> dict:
    return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def total_error_term(whole: float, stroke: float, rel: float, *, w_whole: float,
                     w_stroke: float, w_rel: float) -> dict:
    """ONE held `Plus([Times(w_whole, whole)[, Times(w_stroke, stroke)][, Times(w_rel, rel)]])`
    over three ALREADY-COMPUTED per-candidate residual scalars. A level whose weight is exactly
    `0.0` is OMITTED entirely (no wasted `Times(0.0, x)` sub-term, and -- load-bearing -- so the
    GUARD-REDUCTION INVARIANT holds byte-identically: `w_stroke=0, w_rel=0, w_whole=1` returns
    `Plus([Times(1.0, whole)])`, which `evaluate`s to `whole` exactly, so `argmin(total)` ==
    `argmin(whole)` == the whole-shape GUARD, candidate-for-candidate. This is the critical unit
    invariant `test_guard_reduction_invariant` checks. Combining the three scalars is ARITHMETIC
    (a held Plus/Times over Lits), never a ranking -- the ranking is `_argmin_pairs_term`."""
    items = [{"type": "Times", "items": [{"type": "Lit", "value": float(w_whole)},
                                          {"type": "Lit", "value": float(whole)}]}]
    if w_stroke != 0.0:
        items.append({"type": "Times", "items": [{"type": "Lit", "value": float(w_stroke)},
                                                  {"type": "Lit", "value": float(stroke)}]})
    if w_rel != 0.0:
        items.append({"type": "Times", "items": [{"type": "Lit", "value": float(w_rel)},
                                                  {"type": "Lit", "value": float(rel)}]})
    return {"type": "Plus", "items": items}


def verdict_pred(native, per_cand: list, *, w_whole: float, w_stroke: float,
                 w_rel: float) -> int:
    """The MULTI-GRAIN verdict: for each candidate's `(whole, stroke, rel)` residual triple in
    `per_cand` (a list of dicts with those keys, candidate-index order), evaluate the held
    `total_error_term` and pick the winner via ONE held `Argmin` over the `(total, ci)` pairs --
    never a Python min/sort. Returns the winning candidate index (`-1` for an empty pool -- an
    honest non-crash). `w_whole=1, w_stroke=0, w_rel=0` reproduces the whole-shape GUARD's own
    argmin exactly (the GUARD-reduction invariant)."""
    pairs = []
    for ci, c in enumerate(per_cand):
        total = float(native.evaluate(
            total_error_term(c["whole"], c["stroke"], c["rel"],
                             w_whole=w_whole, w_stroke=w_stroke, w_rel=w_rel), {}) or 0.0)
        pairs.append((total, ci))
    if not pairs:
        return -1
    w = native.evaluate(_argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


# --------------------------------------------------------------------------- #
#  PER-STROKE RESIDUAL -- the MIDDLE grain: per drawn-stroke SC+TPS geometry.
#  Segmentation = the pen-up BREAK markers (`omniglot_world.load_strokes` splits on BREAK -- the
#  writer's OWN real stroke boundaries, never a re-segmentation guess). Alignment = the FIXED
#  greedy per-stroke matcher (`run39.greedy_match`, falsy-zero-safe -- run36's `v or nan` bug is
#  already fixed there; a genuine zero-cost identical-stroke match survives). The per-pair score
#  is the STRONG continuous geometry (`abs_read.sctps_verdict_term` = ShapeContext + TPS), applied
#  PER ALIGNED STROKE PAIR rather than to the whole figure -- the geometry the GUARD already
#  trusts, now read at the part grain. Alignment is on the JOINT-normalized glyph (layout kept, so
#  strokes match by position AND shape, mirroring `relational_variation.align_stroke_points`); the
#  per-pair SC+TPS is on each stroke INDEPENDENTLY re-normalized (pure per-stroke SHAPE -- position
#  is the relation grain's job, kept orthogonal).
# --------------------------------------------------------------------------- #
def per_stroke_residual(native, query_strokes: list, cand_strokes: list, *,
                        n_points: int = DEFAULT_STROKE_N_POINTS) -> float:
    """`query_strokes`/`cand_strokes`: lists of `(m_i, 2)` DRAWN-stroke arrays
    (`omniglot_world.load_strokes(path)`, pen-up BREAK boundaries). Returns the MEAN per-aligned-
    stroke-pair SC+TPS geometric residual, inflated by the unmatched-stroke fraction (a stroke-
    count mismatch is itself structure a matched-only mean would silently drop -- the SAME
    structural-penalty discipline `relational_variation.relational_distance` uses). Returns `0.0`
    only for a degenerate side with no usable stroke pair AND no whole-figure fallback (an honest
    no-signal default, never a fabricated distance)."""
    if not query_strokes or not cand_strokes:
        return 0.0
    q_norm, _, _ = run36._normalize_glyph([np.asarray(s, dtype=float) for s in query_strokes])
    c_norm, _, _ = run36._normalize_glyph([np.asarray(s, dtype=float) for s in cand_strokes])
    mapping = run39.greedy_match(native, q_norm, c_norm)      # {c_idx: q_idx}
    scores = []
    for c_idx, q_idx in mapping.items():
        qps = ar.whole_figure_point_set([(q_norm[q_idx], None)], n_points)
        cps = ar.whole_figure_point_set([(c_norm[c_idx], None)], n_points)
        if qps is None or cps is None:
            continue
        s = float(native.evaluate(ar.sctps_verdict_term(qps, cps), {}) or 0.0)
        scores.append(s)
    n_matched = len(mapping)
    n_unmatched = (len(q_norm) - n_matched) + (len(c_norm) - n_matched)
    n_total = len(q_norm) + len(c_norm)
    unmatched_frac = (n_unmatched / n_total) if n_total else 0.0
    if scores:
        return float(np.mean(scores)) * (1.0 + unmatched_frac)
    # Fallback: no per-stroke pair usable -> whole-figure SC+TPS (honest non-zero, never fabricated).
    qw = ar.whole_figure_point_set([(np.asarray(s, dtype=float), None) for s in query_strokes],
                                    n_points)
    cw = ar.whole_figure_point_set([(np.asarray(s, dtype=float), None) for s in cand_strokes],
                                    n_points)
    if qw is None or cw is None:
        return 0.0
    return float(native.evaluate(ar.sctps_verdict_term(qw, cw), {}) or 0.0)


# --------------------------------------------------------------------------- #
#  RELATION RESIDUAL -- the ARRANGEMENT grain: precision-weighted relation mismatch.
#  Reuses run 50's `relational_variation.relational_distance` VERBATIM (the rel/cpose bin mismatch
#  WEIGHTED by the frozen background tightness = the predictive PRECISION). Identity (`strokeq`)
#  is never read -- arrangement only, by construction (run 50's own scope precedent).
# --------------------------------------------------------------------------- #
def relation_residual(native, query_stroke_points: list, query_sig: list,
                      cand_stroke_points: list, cand_sig: list, weights: dict) -> float:
    """ONE `relational_variation.relational_distance` scalar (`["r"]`) -- the precision-weighted
    arrangement mismatch between query and candidate composed signatures. `weights` = run 50's
    frozen per-slot tightness (`results/run50_checkpoints/learn_relational.json`'s `weights`,
    READ-ONLY). Lower = the candidate's arrangement better explains the query's."""
    return float(rv.relational_distance(native, query_stroke_points, query_sig,
                                        cand_stroke_points, cand_sig, weights)["r"])


# --------------------------------------------------------------------------- #
#  SPREAD-MATCHED LEVEL WEIGHTS -- binding rule (a) from run 44a/44b: "a new term enters a
#  balanced recipe at MATCHED SPREAD OR NOT AT ALL." Each added level enters at the weight that
#  makes its across-candidate spread EQUAL the whole-shape term's own spread (so no level's raw
#  scale silently dominates -- the exact failure run 44a diagnosed). Mechanical arithmetic over
#  ALREADY-computed background spreads, never tuned against eval (mirrors `deform_metric.
#  derive_w_aff`'s own median/divide reduction).
# --------------------------------------------------------------------------- #
def spread_match_weights(spread_whole: float, spread_stroke: float, spread_rel: float,
                         *, w_whole: float = 1.0) -> dict:
    """`w_whole` fixed (the reference grain -- the GUARD term keeps its native scale so the
    GUARD-reduction invariant holds); `w_stroke = w_whole * spread_whole / spread_stroke`;
    `w_rel = w_whole * spread_whole / spread_rel`. A zero/absent spread yields a `0.0` weight for
    that level (an honest omission -- a level with no across-candidate spread carries no
    discriminative signal, never a divide-by-zero)."""
    w_stroke = (w_whole * spread_whole / spread_stroke) if spread_stroke > 0 else 0.0
    w_rel = (w_whole * spread_whole / spread_rel) if spread_rel > 0 else 0.0
    return {"w_whole": float(w_whole), "w_stroke": float(w_stroke), "w_rel": float(w_rel)}


# --------------------------------------------------------------------------- #
#  RELIABILITY-WEIGHTED LEVEL WEIGHTS -- RUN 54b's principled recalibration of the level weights
#  (34a->34b precedent: background-derived, NOT eval-tuned). Run 44b's law proved spread-matching
#  equalizes across-candidate VARIANCE, not DISCRIMINATIVE POWER -- so spread-matching two WEAK
#  grains each to the strong whole-shape's variance let 2/3 of the decision variance come from weak
#  grains (run 54's -20pp harm). THE FIX: weight each grain by its DISCRIMINATIVE RELIABILITY (the
#  PRECISION principle applied to LEVELS, exactly as run 50's per-relation tightness = precision
#  within the relation grain -- reliability IS precision, one unification at two scales).
#
#  reliability(grain) = the CHANCE-CORRECTED standalone background accuracy of that grain's OWN
#  argmin verdict: `clip((acc - chance) / (1 - chance), 0, +inf)` -- 1.0 = a perfect discriminator,
#  0.0 = a grain no better than chance (which then drops out entirely, weight 0). A grain enters at
#  its spread-match scale (so raw units never dominate -- run 44a's scale-dominance guard is kept)
#  TIMES its reliability RELATIVE to whole-shape's: the strong whole-shape grain is the reference
#  (weight `w_whole`, reliability ratio 1); a weaker grain enters at a proportionally smaller
#  weight. This is arithmetic over ALREADY-computed background numbers (standalone accuracies +
#  spreads), never a ranking (the ranking is the held `Argmin`) and never tuned against eval.
# --------------------------------------------------------------------------- #
def _chance_corrected(acc: float, chance: float) -> float:
    """`clip((acc - chance) / (1 - chance), 0, +inf)` -- floored at zero via `np.clip` (not a
    Python ranking primitive), so a below-chance grain reads reliability 0 and drops out."""
    if not (1.0 - chance) > 0:
        return 0.0
    return float(np.clip((acc - chance) / (1.0 - chance), 0.0, None))


def reliability_weights(acc_whole: float, acc_stroke: float, acc_rel: float,
                        spread_whole: float, spread_stroke: float, spread_rel: float,
                        *, chance: float, w_whole: float = 1.0) -> dict:
    """`acc_*`: each grain's STANDALONE background accuracy (its own single-grain argmin, computed
    by the caller via the held `verdict_pred` -- never a Python argmin here). `spread_*`: the
    background across-candidate spreads (44b's estimator). `chance`: `1/WAY`. Returns the level
    weights + the reliabilities used, with `w_whole` fixed (the GUARD-reduction invariant holds:
    at zero-reliability weak grains this reduces to `{w_whole, 0, 0}` = the whole-shape GUARD
    byte-identically). `w_grain = w_whole * (reliability_grain / reliability_whole) *
    (spread_whole / spread_grain)` -- spread-match TIMES relative reliability. A zero reliability,
    zero whole-reliability, or non-positive spread yields a `0.0` weight (honest omission, never a
    divide-by-zero)."""
    r_whole = _chance_corrected(acc_whole, chance)
    r_stroke = _chance_corrected(acc_stroke, chance)
    r_rel = _chance_corrected(acc_rel, chance)

    def _lvl(r_grain: float, spread_grain: float) -> float:
        if r_whole <= 0.0 or r_grain <= 0.0 or spread_grain <= 0.0 or spread_whole <= 0.0:
            return 0.0
        return float(w_whole * (r_grain / r_whole) * (spread_whole / spread_grain))

    return {"w_whole": float(w_whole),
            "w_stroke": _lvl(r_stroke, spread_stroke),
            "w_rel": _lvl(r_rel, spread_rel),
            "reliability": {"whole": r_whole, "stroke": r_stroke, "rel": r_rel},
            "standalone_acc": {"whole": float(acc_whole), "stroke": float(acc_stroke),
                               "rel": float(acc_rel)}}


__all__ = ["DEFAULT_STROKE_N_POINTS", "total_error_term", "verdict_pred",
           "per_stroke_residual", "relation_residual", "spread_match_weights",
           "reliability_weights"]
