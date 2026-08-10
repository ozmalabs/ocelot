"""domains/conditional_foveation.py -- RUN 45 (PHASE 4, the human-gap plan's FINAL phase):
CONDITIONAL FOVEATION, 37A retried with its three diagnosed failure causes each fixed.

RUN 37A (commit cca938fd) built a contrastive verdict that looked SPECIFICALLY at where the
global top-2 candidates differ and re-judged the trial on that region alone -- and it harmed
badly (82 broken / 16 fixed at n=400). The post-mortem named THREE independent causes, all
present at once in that design:
  (1) UNCONDITIONAL -- it fired on EVERY episode (`cv`'s own top-of-file doc: "always contrast
      the top-2... a parameter-free choice"), including the ~80% of episodes the global verdict
      already got right with a COMFORTABLE margin -- a focused look at noise on an already-easy
      trial can only ever cost accuracy, never buy it.
  (2) A REPLACEMENT -- the focused (contrastive) score OVERRODE the global verdict outright
      (`contrastive_pick`'s own `winner` IS the final answer) rather than entering as one more
      piece of evidence a fused decision weighs -- exactly the "REPLACE, not SUPPLEMENT" shape
      RUN 44a's own post-mortem (commit 4990c69e) independently diagnosed as catastrophic scale
      dominance for a DIFFERENT mechanism, and RUN 44b (commit 465d57da) fixed for THAT one via
      spread-matched ADDITIVE entry.
  (3) FRAME-CONTAMINATED -- the difference-region comparison (`cv.difference_elements`/
      `cv.region_score`) normalizes the query and EACH candidate INDEPENDENTLY
      (`scripts.jabberwock_omniglot_run36_failures._normalize_glyph`, one centre + one abs-max
      scale PER GLYPH) -- so the query's own per-glyph frame and each candidate's own per-glyph
      frame can each be shifted/rescaled differently before the "same-frame" region distance is
      ever computed. A small, real distinguishing feature competes against this frame noise on
      an even footing -- exactly backwards from the human mechanism ("align the wholes first,
      arbitrate on the difference only when the wholes genuinely tie, IN THE ALIGNED FRAME").

THIS MODULE builds the fix for cause (3), the ALIGNED FRAME: `difference_elements_aligned`
normalizes the query AND both top-2 candidates INTO ONE SHARED FRAME (`_joint_normalize`, one
pooled centre + one pooled abs-max scale over their UNION) rather than three independent
per-glyph frames, and `foveate_terms` returns a per-candidate ADDITIVE evidence SCALAR (never a
standalone winner) for the caller to enter into a fused recipe at a spread-matched weight
(RUN 44b's own `derive_w_aff` mechanics, reused verbatim by the run script) -- fixing causes (2)
and (2)'s composition. Cause (1) -- UNCONDITIONAL firing -- is fixed by the run script itself
(a pre-registered top-2-margin threshold, derived from BACKGROUND episodes, gates whether this
module's machinery is even invoked for a given episode; this module has no opinion on WHEN it
fires, only on WHAT it computes once asked to).

WHY THE FALLBACK, NOT THE PRIMARY "READ THE SMOOTHDEFORM FIT" DESIGN: the launch brief's first
choice was to extract the aligned frame from the GLOBAL comparator's own whole-figure warp
(`domains.deform_metric.smooth_deform_components`, RUN 44's own `SmoothDeformComponents` Term,
the SAME FFD field `recognition_graph.smoothdeform_error_term` already fits between a query and
a candidate). That Term's exposed decomposition (`rotation`, `shear`, `log_scale`, `tx`, `ty`,
`bending`) is a set of SCALAR summaries of the fitted field, not the field itself: `log_scale`
is `0.5*ln(scaleX*scaleY)`, the GEOMETRIC MEAN of the two axis scales -- the individual
`scaleX`/`scaleY` (needed to reconstruct the 2x2 affine matrix `A` and actually MAP an arbitrary
new point, e.g. a diff-region point, through the fit) are computed internally
(`deform_metric.rs::decompose_affine`) but never returned. Nor is the non-affine "bending" part
of the field returned per-point -- only its aggregate mean-squared magnitude. So "map the
query's diff-region points through the fitted warp" is NOT reachable through the existing Term
surface without a new Rust accessor -- and per CLAUDE.md ("extend Rust if and only if the
existing DSL cannot express what the graph form requires"), a full per-point warp-application
accessor is a materially bigger primitive (the field, not a summary of it) than this run's own
scope justifies for what is, explicitly, this arc's closing measurement. The PRE-REGISTERED
fallback names exactly this situation: "a shared-frame alignment of the two candidates + query
together." `_joint_normalize` is that shared frame -- NOT a rotation-fitting Procrustes/Kabsch
solve (which needs known point CORRESPONDENCES between the two shapes; establishing those
without an ICP pass is exactly what `SmoothDeformDist`/`TpsDeformDist` already do internally, at
materially greater cost, for a different purpose than this run needs). It is the MINIMAL fix
that targets cause (3) as diagnosed: independent per-glyph translation+scale -- `_joint_
normalize` extends `run36._normalize_glyph`'s own convention (one centre + one isotropic
abs-max scale) from PER-GLYPH to PER-EPISODE-TRIPLE, removing exactly the frame disagreement
named, nothing more.

DECISION DISCIPLINE (CLAUDE.md / this arc's own established audit,
`tests/test_contrastive_verdict_migrated.py::test_contrastive_verdict_no_python_decisions`,
extended here): every SELECTION among competing candidates -- the greedy stroke-match
assignment (`_greedy_stroke_match_normed`, repeated held `Argmin` over the remaining valid
pairs, the SAME "argmin over what's left" idiom `contrastive_verdict.top2_candidates` already
established) and the worst-matched-pair pick (`contrastive_verdict._worst_matched_pair`, reused
verbatim) -- is a held Term evaluate, never a Python `sorted(key=...)`/`min`/`max`-by-score. The
FINAL per-episode winner (fused score' argmin over all 20 candidates) is NOT decided in this
module at all -- it is the run script's own held `Argmin`, exactly like every other verdict
variant in this arc (`deform_metric.py`, `contrastive_verdict.py`); this module only ever
returns per-candidate ADDITIVE scalars for the caller to fuse."""
from __future__ import annotations

import numpy as np

from domains import abs_read as ar
from domains import contrastive_verdict as cv


# ===================================================================================================
# CONDITION -- the top-2 margin (background-thresholded by the run script; this module only
# supplies the mechanical read-off, never the threshold comparison itself).
# ===================================================================================================
def top2_from_pairs(native, pairs: list) -> list:
    """`pairs`: an ALREADY-COMPUTED `[(score, candidate_index), ...]` list (e.g. the run
    script's own `full_pairs`, the SAME per-candidate fused-error vector `abs_read.parse_
    marginal_pair_error` produces for every candidate) -- repeated held `Argmin`
    (`abs_read._argmin_pairs_term`, reused verbatim) over the remaining pool, the SAME
    "argmin over what's left" idiom `contrastive_verdict.top2_candidates` established, just
    starting from an already-computed list instead of re-evaluating the pair-error Term a
    second time (this run's own eval loop already needs the FULL 20-candidate ranking for the
    supplement composition below, so recomputing just the top-2 via a fresh `parse_marginal_
    pair_error` sweep would be redundant work, not a different result). Returns up to two
    `(score, candidate_index)` pairs ascending by score (lower = better)."""
    remaining = list(pairs)
    top2: list = []
    for _ in range(min(2, len(remaining))):
        w = native.evaluate(ar._argmin_pairs_term(remaining), {})
        if w is None:
            break
        score, idx = float(w[0]), int(w[1])
        top2.append((score, idx))
        remaining = [(s, i) for (s, i) in remaining if i != idx]
    return top2


def top2_margin(top2: list) -> float:
    """Plain arithmetic on two ALREADY-COMPUTED scalars (`top2[1][0] - top2[0][0]`) -- mirrors
    `scripts.jabberwock_omniglot_run44b_spread.py`'s own `margin = best_imp - true_err` idiom
    (subtracting two held-Term outputs is arithmetic, not a ranking decision). `float("inf")`
    for fewer than two candidates (an uncontested episode -- no possible ambiguity to
    arbitrate, the run script's own condition never fires here)."""
    if len(top2) < 2:
        return float("inf")
    return float(top2[1][0] - top2[0][0])


def derive_threshold(margins: list, pctl: float = 25.0) -> float:
    """THE background-derived firing threshold (design point 1's own pre-registration: "the
    p25 of background top-2 margins, computed on n=100 background 20-way episodes, frozen"):
    a plain percentile over ALREADY-COMPUTED background margins -- mirrors `deform_metric.
    derive_w_aff`'s own "mechanical statistic, never tuned against an eval outcome"
    discipline; the run script computes `margins` ONCE on background episodes and freezes the
    result before any real (test-alphabet) episode is scored."""
    return float(np.percentile(np.asarray(margins, dtype=float), pctl))


def fires(margin: float, threshold: float) -> bool:
    """THE CONDITION (design point 1): fire iff the top-2 margin is STRICTLY BELOW the
    pre-registered background threshold -- a plain scalar comparison of two already-computed
    numbers against a FROZEN bound, the SAME bookkeeping idiom `scripts.jabberwock_omniglot_
    run44b_spread.py`'s own `passed = acc_armed >= acc_base - SANITY_MARGIN` already uses (not
    a competing-candidates ranking decision -- the episode's actual WINNER, whether or not
    this fires, is always the run script's own held `Argmin` over `supplement_pairs`' output,
    or over the untouched `full_pairs` when this returns `False`)."""
    return bool(margin < threshold)


# ===================================================================================================
# ALIGNED FRAME -- shared-frame joint normalization (the pre-registered fallback; see module
# docstring for why the primal "read the SmoothDeform fit" design is not reachable).
# ===================================================================================================
def _as_stroke_array(s) -> np.ndarray:
    return np.asarray(s, dtype=float).reshape(-1, 2)


def _joint_normalize(stroke_groups: list) -> list:
    """`stroke_groups`: a list of stroke-lists (e.g. `[query_strokes, cand1_strokes,
    cand2_strokes]`, each itself a list of per-stroke `(n_i, 2)` point arrays). Pools EVERY
    point from EVERY group into one population, computes ONE shared centre (mean) and ONE
    shared isotropic scale (abs-max, `run36._normalize_glyph`'s own convention) from that
    pooled population, and applies `(pts - centre) / scale` to every stroke in every group.
    Returns the SAME nested list-of-groups-of-arrays shape, now all three sides in ONE common
    frame -- this is the module's own "align the wholes first" step; the diff-region
    extraction below operates entirely on its output, never on independently-normalized
    input. An all-empty input returns the groups unchanged (an honest no-op, never a crash --
    the caller's own `difference_elements_aligned` never reaches this on a totally-empty
    triple, but this guard keeps the function itself crash-safe standalone)."""
    arrays = [[_as_stroke_array(s) for s in g] for g in stroke_groups]
    flat = [s for g in arrays for s in g if s.size]
    if not flat:
        return arrays
    pooled = np.concatenate(flat, axis=0)
    centre = pooled.mean(axis=0)
    scale = float(np.abs(pooled - centre).max()) or 1e-9
    return [[(s - centre) / scale for s in g] for g in arrays]


def _greedy_stroke_match_normed(native, t_norm: list, p_norm: list) -> dict:
    """The per-stroke greedy assignment (`contrastive_verdict.difference_elements`'s own
    `run36._greedy_stroke_match` twin), operating on ALREADY-NORMALIZED per-stroke arrays
    directly rather than calling `_normalize_glyph` internally -- `run36._greedy_stroke_
    match` re-normalizes EACH side INDEPENDENTLY as its own first step, which would silently
    UNDO this run's own shared-frame alignment if composed naively (feeding it `_joint_
    normalize`'s output would normalize it AGAIN, per side, cancelling the shared reference
    this module exists to establish). Working-tree-isolation precedent for duplicating a
    small, already-audited algorithm rather than threading a new parameter through it:
    `runners/dsl/src/deform_metric.rs`'s own module doc ("kept local so this module's edits
    never collide with unrelated concurrent work"), applied here in Python. UNLIKE `run36.
    _greedy_stroke_match` (a Python `sorted(costs.items(), key=...)`, pre-existing/read-only
    machinery this arc's audits never required to change), this duplicate is built with
    REPEATED held `Argmin` over the shrinking remaining-pairs pool -- the SAME idiom `top2_
    from_pairs` above uses -- so it needs no `_ALLOWED_SORT_KEYS` audit exemption of its own."""
    pairs_all: list = []
    for i, ts in enumerate(t_norm):
        for j, ps in enumerate(p_norm):
            term = {"type": "PointSetDist",
                    "a": {"type": "Lit", "value": np.asarray(ts, dtype=float).tolist()},
                    "b": {"type": "Lit", "value": np.asarray(ps, dtype=float).tolist()}}
            c = float(native.evaluate(term, {}) or float("nan"))
            pairs_all.append((c, [i, j]))
    remaining = list(pairs_all)
    used_i: set = set()
    used_j: set = set()
    matched: list = []
    while remaining:
        w = native.evaluate(ar._argmin_pairs_term(remaining), {})
        if w is None:
            break
        cost, ij = float(w[0]), w[1]
        i, j = int(ij[0]), int(ij[1])
        used_i.add(i)
        used_j.add(j)
        matched.append((i, j, cost))
        remaining = [(cc, xy) for (cc, xy) in remaining if xy[0] != i and xy[1] != j]
    unmatched_true = [i for i in range(len(t_norm)) if i not in used_i]
    unmatched_pred = [j for j in range(len(p_norm)) if j not in used_j]
    return dict(matched=matched, unmatched_true=unmatched_true, unmatched_pred=unmatched_pred,
                n_true=len(t_norm), n_pred=len(p_norm))


def difference_elements_aligned(native, query_strokes: list, cand1_strokes: list,
                                 cand2_strokes: list) -> dict:
    """ALIGNED-FRAME twin of `contrastive_verdict.difference_elements`: the SAME branch logic
    (empty / unmatched / worst_matched -- see that function's own docstring for the exact
    pre-registered rule, unchanged here) but `cand1_strokes`/`cand2_strokes` AND `query_
    strokes` are normalized JOINTLY (`_joint_normalize`, one shared centre+scale over their
    UNION) rather than independently per-glyph -- RUN 45's fix for 37A's diagnosed cause (3).
    Returns the SAME keys as `contrastive_verdict.difference_elements` PLUS `query_norm` (the
    jointly-normalized query, a list of per-stroke arrays already in the SAME shared frame
    `diff1`/`diff2` live in -- callers MUST score against `query_norm`, never a fresh
    independently-normalized query, or the alignment this function exists to provide is lost
    downstream)."""
    q_norm, c1_norm, c2_norm = _joint_normalize([query_strokes, cand1_strokes, cand2_strokes])
    query_norm_lists = [q.tolist() for q in q_norm]

    if not cand1_strokes and not cand2_strokes:
        return dict(ok=False, kind="empty", single_stroke=False, count_mismatch=False,
                    diff1=[], diff2=[], matched_costs=[], n_true=0, n_pred=0,
                    query_norm=query_norm_lists)
    if not cand1_strokes or not cand2_strokes:
        if cand1_strokes:
            diff1 = np.concatenate(c1_norm, axis=0).tolist()
            diff2: list = []
            n_true, n_pred = len(cand1_strokes), 0
        else:
            diff1 = []
            diff2 = np.concatenate(c2_norm, axis=0).tolist()
            n_true, n_pred = 0, len(cand2_strokes)
        return dict(ok=bool(diff1 or diff2), kind="unmatched", single_stroke=False,
                    count_mismatch=True, diff1=diff1, diff2=diff2, matched_costs=[],
                    n_true=n_true, n_pred=n_pred, query_norm=query_norm_lists)

    gm = _greedy_stroke_match_normed(native, c1_norm, c2_norm)
    count_mismatch = bool(gm["unmatched_true"] or gm["unmatched_pred"])
    kind = "unmatched" if count_mismatch else "worst_matched"
    single_stroke = (gm["n_true"] == 1 and gm["n_pred"] == 1)

    if count_mismatch:
        diff1 = (np.concatenate([c1_norm[i] for i in gm["unmatched_true"]], axis=0).tolist()
                 if gm["unmatched_true"] else [])
        diff2 = (np.concatenate([c2_norm[j] for j in gm["unmatched_pred"]], axis=0).tolist()
                 if gm["unmatched_pred"] else [])
    else:
        wp = cv._worst_matched_pair(native, gm["matched"])
        if wp is None:
            diff1, diff2 = [], []
        else:
            i, j = wp
            diff1 = c1_norm[i].tolist()
            diff2 = c2_norm[j].tolist()

    matched_costs = [float(c) for (_, _, c) in gm["matched"]]
    ok = bool(diff1) or bool(diff2)
    return dict(ok=ok, kind=kind, single_stroke=single_stroke, count_mismatch=count_mismatch,
                diff1=diff1, diff2=diff2, matched_costs=matched_costs,
                n_true=gm["n_true"], n_pred=gm["n_pred"], query_norm=query_norm_lists)


# ===================================================================================================
# SUPPLEMENT EVIDENCE -- per-candidate ADDITIVE scalars, NEVER a standalone winner (contrast
# `contrastive_verdict.contrastive_pick`, which decides one outright).
# ===================================================================================================
def foveate_terms(native, query_strokes: list, cand1_strokes: list, cand2_strokes: list,
                   cand1_idx: int, cand2_idx: int) -> dict:
    """THE per-candidate ADDITIVE diff-region evidence for RUN 45's conditional supplement.
    Returns a dict carrying `decision` (`"fallback_no_diff"` / `"one_sided"` / `"two_sided"`,
    the SAME names `contrastive_verdict.contrastive_pick` uses for the analogous branches) and
    `terms` (`{candidate_index: scalar}` for `cand1_idx`/`cand2_idx` ONLY -- every OTHER
    candidate in the episode's full pool gets NO term at all; the caller's own fusion treats
    an absent key as `0.0`, i.e. 'no extra evidence for this candidate'). Every branch that
    lacks a genuine two-sided region comparison (no difference at all; a one-sided count-
    mismatch pair) assigns `0.0` to whichever side has no distinguishing evidence of its own --
    NEVER a fabricated penalty -- so a candidate is never additively punished for evidence
    that simply doesn't exist for it.

    A `region_score` that comes back non-finite (`contrastive_verdict.region_score`'s own
    `float("inf")` convention for a degenerate empty-query/empty-diff read) is floored to
    `0.0` here (an HONEST safety valve against exactly the scale-dominance failure RUN 44a's
    own post-mortem diagnosed -- an unbounded additive term would drown the fused recipe
    regardless of how small `w_f` is derived to be) -- `n_nonfinite` counts how often this
    valve engaged, reported by the run script as an honest anomaly, never silently absorbed."""
    diff = difference_elements_aligned(native, query_strokes, cand1_strokes, cand2_strokes)
    result: dict = dict(cand1_idx=cand1_idx, cand2_idx=cand2_idx, n_nonfinite=0, **diff)
    q_norm = diff["query_norm"]

    def _finite(score: float) -> float:
        if np.isfinite(score):
            return float(score)
        result["n_nonfinite"] += 1
        return 0.0

    if not diff["ok"]:
        result.update(decision="fallback_no_diff", terms={cand1_idx: 0.0, cand2_idx: 0.0})
        return result

    if diff["count_mismatch"]:
        has1, has2 = bool(diff["diff1"]), bool(diff["diff2"])
        if has1 and has2:
            pass  # both non-empty -- falls through to the two-sided scoring below (mirrors
                  # `contrastive_verdict.contrastive_pick`'s own documented "not reachable per
                  # this function's own docstring, but handled uniformly" fallthrough).
        elif has1 or has2:
            extra_idx, extra_points = ((cand1_idx, diff["diff1"]) if has1
                                        else (cand2_idx, diff["diff2"]))
            other_idx = cand2_idx if has1 else cand1_idx
            score_extra = _finite(cv.region_score(native, extra_points, q_norm))
            result.update(decision="one_sided", extra_idx=extra_idx, other_idx=other_idx,
                          terms={extra_idx: score_extra, other_idx: 0.0})
            return result
        else:
            result.update(decision="fallback_no_diff", terms={cand1_idx: 0.0, cand2_idx: 0.0})
            return result

    score1 = _finite(cv.region_score(native, diff["diff1"], q_norm))
    score2 = _finite(cv.region_score(native, diff["diff2"], q_norm))
    result.update(decision="two_sided", terms={cand1_idx: score1, cand2_idx: score2})
    return result


# ===================================================================================================
# SPREAD-MATCHED FUSION -- pure arithmetic composition, no decision (the run script's own held
# Argmin over the resulting `score'` list is what decides the episode's winner).
# ===================================================================================================
def supplement_pairs(full_pairs: list, terms: dict, w_f: float) -> list:
    """`score'(ci) = fused(ci) + w_f * terms.get(ci, 0.0)` for EVERY candidate in `full_pairs`
    -- a candidate with no entry in `terms` (everyone outside the fired episode's own top-2)
    is passed through byte-identical. Plain arithmetic over already-computed scalars (mirrors
    `deform_metric.supplement_pair_error_term`'s own `existing_fused + w_aff * mahalanobis_
    affine` shape, done here in Python over already-evaluated floats rather than as a held
    Term, since -- unlike `deform_metric`'s pure-Rust Mahalanobis term -- `terms` above is the
    product of a multi-step Python-orchestrated pipeline, not a single Term evaluate; the
    FINAL winner argmin over this function's own output is still a held Term, never decided
    here)."""
    return [(score + w_f * terms.get(ci, 0.0), ci) for (score, ci) in full_pairs]
