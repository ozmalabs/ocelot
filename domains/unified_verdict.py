"""unified_verdict -- RUN 56: THE UNIFIED LOG-ODDS NATIVE DERIVATION (the completion of run 55's
native recognition). The creator's spec, verbatim: "log indexes relative admissibility grammar
based graphs" -- FULLY realized.

WHERE RUN 55 STOPPED: run 55 built a genuinely NATIVE per-instance relation precision (read from
graph-resident FrameAxis log_weight EDGES, centered per-derivation) and PROVED it real
(rel_x effective precision std>0 across derivations) and cheap (one Gamma-pruned pass, ~9ms). But
it was a HYBRID: it kept run-54b's STATIC 3-grain reliability-weighted TOP level and let the
per-instance precision act only WITHIN the weak rel grain. Per-instance-within-a-static-weighted-
weak-grain still cannot overcome the dilution law -> nulled -5pp.

THE COMPLETION (this module): a UNIFIED single derivation cost where GEOMETRY and RELATION parts
are BOTH LOG-ODDS ADMISSIBILITY terms sharing ONE per-instance relative precision -- so precision
ARBITRATES geometry-vs-relation AT THE VERDICT LEVEL (geometry dominates when it is DECISIVE;
relations override only when geometry is per-instance AMBIGUOUS and relations CONFIDENT). NO static
3-grain top-level weighting (that was run 55's hybrid flaw). The per-instance precisions ARE the
only weighting, and they arbitrate.

THE KEY MATH (the creator's "log indexes"): each part's admissibility = a PRECISION-WEIGHTED
LOG-LIKELIHOOD. In Gaussian terms the log-likelihood of a part is `-residual^2 * precision`, where
precision = 1/variance = the CONCEPT'S PREDICTED DISTRIBUTION WIDTH for that part. So BOTH the
geometry residual and the relation residual become `precision * residual^2` terms in the SAME
log-odds space -- COMMENSURATE -> summable -> argmin over the negative-log-likelihood COST (higher
log-likelihood = lower cost). LOG-ODDS is the common currency that reconciles the two
scale-incommensurate residuals run 55 could not sum.

PRE-REGISTERED PRECISION NORMALIZATION (the scale reconciliation -- THE point, stated up front):
each part-type's precision is `1 / (background within-TRUE-class variance of that part's residual)`
-- the concept's predicted distribution width, measured on background with known labels (structural,
NOT eval-tuned; the SAME within-class-variance principle run 50's tightness already used). For the
relation part this is applied to run 55's per-INSTANCE native relation residual (which already folds
the per-stroke SC+TPS fit ADMISSIBILITY into each relation's log-precision -- so "geo_precision =
per-stroke fit confidence" participates HERE, as the relation precision, exactly as the brief
specifies). Dividing each squared residual by its own background variance makes every term
dimensionless `(residual / sigma_part)^2` -- one commensurate log-odds scale.

GUARD (the geometry-only verdict, `prec_rel = 0`): `argmin_c [ prec_whole * whole(q,c)^2 ]`. Because
`prec_whole` is a positive constant, this is `argmin_c whole(q,c)` == the whole-shape SC+TPS verdict
BYTE-IDENTICALLY (squaring is monotonic on the non-negative residual). So the geometry-only log-odds
REPRODUCES the SC+TPS baseline exactly -- the GUARD-REDUCTION invariant, and the pre-registered
check that the log-odds geometry formulation is not off.

ARM U (the unified verdict): `argmin_c [ prec_whole * whole(q,c)^2 + prec_rel * rel(q,c)^2 ]` with
`rel` = run 55's per-instance native relation residual. When `prec_rel -> 0` this reduces to GUARD
(structurally cannot badly underperform whole-shape). When geometry is per-instance AMBIGUOUS (the
`whole^2` term is nearly flat across candidates) the `rel^2` term decides; when geometry is DECISIVE
(the `whole^2` term separates candidates) it dominates. That per-instance verdict-level arbitration
is the untested stronger form run 55 named.

ARCHITECTURE (CLAUDE.md legality): every function here is a MECHANICAL Term builder (the squared-
precision Plus combination, the Argmin verdict) or plain arithmetic over already-computed scalars.
The RANKING DECISION is the held `Argmin` (`_argmin_pairs_term`, the SAME pattern as
`compositional_verdict.verdict_pred`); combining precision-weighted squared residuals is ARITHMETIC
(a held Plus/Times over Lits), never a ranking. No Python min/max/argmin/sort anywhere -- gated by
`tests/test_unified_verdict_migrated.py::test_unified_verdict_no_python_decisions`.
"""
from __future__ import annotations

import numpy as np

_VAR_EPS = 1e-9    # floor so precision = 1/var never diverges on a degenerate zero-variance part.


# --------------------------------------------------------------------------- #
#  BACKGROUND-CALIBRATED PRECISION -- the concept's predicted distribution width, 1/within-class
#  variance. Plain arithmetic over already-collected background residuals (the SAME class of
#  reduction `compositional_verdict.reliability_weights` / run 50's tightness derivation are), NOT
#  a decision. `true_class_residuals` is the list of the TRUE candidate's residual for one
#  part-type across background episodes.
# --------------------------------------------------------------------------- #
def part_precision(true_class_residuals: list) -> float:
    """`1 / max(var(true_class_residuals), eps)` -- the Gaussian precision (inverse within-true-
    class variance = the concept's predicted distribution width for that part). Empty / degenerate
    input yields the eps-floored precision (`1/eps`, an honest finite value, never a crash)."""
    arr = np.asarray(true_class_residuals, dtype=float)
    if arr.size == 0:
        return 1.0 / _VAR_EPS
    return float(1.0 / float(np.clip(np.var(arr), _VAR_EPS, None)))


# --------------------------------------------------------------------------- #
#  Held Term builders -- call-site-local, mirroring `compositional_verdict`'s own convention.
# --------------------------------------------------------------------------- #
def _sq(value: float) -> dict:
    """`residual^2` as a held Term (`Times([Lit(v), Lit(v)])`) -- squaring in the log-odds space,
    never a Python `**`."""
    return {"type": "Times", "items": [{"type": "Lit", "value": float(value)},
                                       {"type": "Lit", "value": float(value)}]}


def unified_cost_term(whole: float, stroke: float, rel: float, *, prec_whole: float,
                      prec_stroke: float, prec_rel: float) -> dict:
    """ONE held log-odds cost Term over a candidate's already-computed `(whole, stroke, rel)`
    residual triple:

        Plus([ Times(prec_whole,  whole^2)
             [, Times(prec_stroke, stroke^2)]
             [, Times(prec_rel,    rel^2)] ])

    Each term is `precision * residual^2` = the negative Gaussian log-likelihood of that part (the
    scale-reconciling log-odds currency). A part whose precision is exactly `0.0` is OMITTED
    entirely (no wasted `Times(0.0, .)` sub-term) -- so `prec_rel=0` returns the geometry-only cost
    and `prec_rel=0, prec_stroke=0` returns `Plus([Times(prec_whole, whole^2)])`, whose argmin is
    `argmin(whole)` == the whole-shape GUARD byte-identically (the GUARD-REDUCTION invariant).
    Combining the terms is ARITHMETIC (held Plus/Times over Lits), never a ranking."""
    items = []
    if prec_whole != 0.0:
        items.append({"type": "Times", "items": [{"type": "Lit", "value": float(prec_whole)},
                                                  _sq(whole)]})
    if prec_stroke != 0.0:
        items.append({"type": "Times", "items": [{"type": "Lit", "value": float(prec_stroke)},
                                                  _sq(stroke)]})
    if prec_rel != 0.0:
        items.append({"type": "Times", "items": [{"type": "Lit", "value": float(prec_rel)},
                                                  _sq(rel)]})
    if not items:                       # degenerate all-zero precision -> honest zero cost.
        return {"type": "Lit", "value": 0.0}
    return {"type": "Plus", "items": items}


def _argmin_pairs_term(pairs: list) -> dict:
    """Held `Argmin` over `(cost, candidate_index)` pairs -- the verbatim pattern
    `compositional_verdict._argmin_pairs_term` uses (returns the winning pair; the caller reads
    index 1)."""
    return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def unified_verdict_pred(native, per_cand: list, *, prec_whole: float, prec_stroke: float,
                         prec_rel: float) -> int:
    """THE UNIFIED LOG-ODDS VERDICT: for each candidate's `(whole, stroke, rel)` triple in
    `per_cand` (candidate-index order), evaluate the held `unified_cost_term` and pick the winner
    via ONE held `Argmin` over the `(cost, ci)` pairs -- never a Python min/sort. Returns the
    winning candidate index (`-1` for an empty pool -- an honest non-crash). `prec_rel=0,
    prec_stroke=0` reproduces the whole-shape GUARD's own argmin exactly (GUARD-reduction)."""
    pairs = []
    for ci, c in enumerate(per_cand):
        cost = float(native.evaluate(
            unified_cost_term(c["whole"], c["stroke"], c["rel"],
                              prec_whole=prec_whole, prec_stroke=prec_stroke,
                              prec_rel=prec_rel), {}) or 0.0)
        pairs.append((cost, ci))
    if not pairs:
        return -1
    w = native.evaluate(_argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


# --------------------------------------------------------------------------- #
#  ARBITRATION DIAGNOSTIC (reporting only, no decision) -- the load-bearing per-instance evidence:
#  on geo-AMBIGUOUS episodes the relation term should FLIP the verdict; on geo-DECISIVE ones it
#  should NOT. `geo_margin` = the normalized separation of the top-two whole-shape residuals for a
#  query (small = ambiguous, large = decisive) -- pure statistics over already-computed residuals.
# --------------------------------------------------------------------------- #
def geo_margin(per_cand: list) -> float:
    """`(second_lowest_whole - lowest_whole) / (mean_whole + eps)` -- the normalized top-2
    whole-shape residual gap for one query. 0 = geometry cannot separate the top two candidates
    (AMBIGUOUS); large = geometry is DECISIVE. Uses `np.partition` (a selection, not a ranking
    decision -- the VERDICT ranking is the held Argmin); returns 0.0 for fewer than two
    candidates."""
    ws = np.asarray([c["whole"] for c in per_cand], dtype=float)
    if ws.size < 2:
        return 0.0
    lo2 = np.partition(ws, 1)                 # lo2[0] <= lo2[1] <= rest (a selection, not a rank).
    lowest, second = float(lo2[0]), float(lo2[1])
    denom = float(np.mean(ws)) + 1e-9
    return (second - lowest) / denom


__all__ = ["part_precision", "unified_cost_term", "unified_verdict_pred", "geo_margin"]
