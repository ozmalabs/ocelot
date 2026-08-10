"""domains/contrastive_verdict.py -- RUN 37A, GAP A: JUDGE-A-TRIAL-BY-ITS-RESULT.

`results/run37_checkpoints/plan.json` (commit 67005b35, the jabberwock's own plan) grounds
Gap A (near-rank verdict confusions, RUN 36 commit 5aa6bcb6) as an `experiment_rule`:
"judge a trial by its RESULT" -- for the episodes the standard full-dwell parse-marginal
verdict (`abs_read.stage_parse_char` + `abs_read.parse_marginal_verdict`) gets WRONG, RUN 36
found 32.1% pick the rank-1/2 nearest impostor (vs 10.5% chance) and, for multi-stroke
confused pairs, the element that actually DISTINGUISHES the true class from its nearest
impostor carries a median 0.187 of the ink -- a small hook outvoted by shared mass under a
comparator that weighs all ink equally. This module is the host-side realization: a
CONTRASTIVE VERDICT that, once the global verdict names its top-2 candidates, looks
SPECIFICALLY at where those two candidates differ and re-judges the trial on that region
alone.

TRIGGER (pre-registered, stated before any eval number below is computed): ALWAYS contrast
the top-2 -- the design doc offered a margin-calibrated trigger as an alternative, but
calibrating a margin threshold on the 5 LEARN/background alphabets buys nothing here (the
contrastive pass is cheap -- O(20) extra `parse_marginal_pair_error` evaluates plus one small
per-stroke greedy match -- see the run script's own timing note) and a margin threshold is one
more knob that could be read as tuned-to-outcome even when it isn't. "Always" is the
parameter-free choice; the run script's own fire-rate report (which for this reason is
trivially 100% of episodes ENTERING the pass, though not all of them end up FLIPPING the
verdict -- see `fired`/`decision` below) is retained purely as an honest instrument, not a
gate.

THE PER-CANDIDATE SCORE VECTOR -- ALREADY EXPOSED, NO NEW RUST NEEDED: the design asked to
"add a minimal read-only accessor for the per-candidate score vector" if `parse_marginal_
verdict` only exposed its Argmax winner. It does only expose the winner -- but
`abs_read.parse_marginal_pair_error(scratch, query_node, cand_node)` is ALREADY that
accessor: it evaluates the EXACT SAME fused error expression `predict_smooth_marginal_sc_term`
wraps in its own held Argmax (`parse_marginal_pair_error_term`'s own docstring: "the SAME
per-candidate quantity the Argmax already ranks by -- `Argmax(-err) == Argmin(err)`"),
standalone per (query, candidate) pair, and RUN 25's own `_c2_scale_probe` already calls it in
exactly this per-candidate-loop shape. `top2_candidates` below is pure composition of that
existing accessor -- no Rust change, no new Term type.

DIFFERENCE REGION (`difference_elements`): between the top-2 candidates' own EXEMPLAR files
(never the query), a per-stroke greedy alignment -- `scripts.jabberwock_omniglot_run36_
failures._greedy_stroke_match`/`_normalize_glyph`, REUSED VERBATIM (the design: "REUSE run
36's machinery... the matcher is exactly what the artifact distorted" -- RUN 37C's own
degenerate-stroke filter protects exactly this matcher). The run script wraps every stroke
LOAD in `scripts.jabberwock_omniglot_run37c_hygiene.DropDegenerateFilter` (MANDATORY per the
design) so both candidates' exemplar strokes AND the query's own strokes are filtered before
this module ever sees them -- this module itself never loads a file or touches `omniglot_
world`, it only accepts already-loaded stroke lists, so it cannot silently bypass the filter.

PRE-REGISTERED DIFFERENCE-ELEMENT RULE (design point 2/4, restated concretely -- decided here,
before ANY eval number, never adjusted against an outcome):
  - EQUAL stroke counts (every stroke paired by the greedy match): each candidate's difference
    element is its OWN side of the SINGLE WORST-MATCHED pair (highest per-stroke `PointSetDist`
    cost among the matched pairs) -- selected via a held `Argmax` (`abs_read._argmax_pairs_
    term`, reused verbatim) over the ALREADY-COMPUTED match costs, never a Python `max` ranked
    by a key-function -- the same "no Python argmin/argmax" discipline `test_abs_read_no_python_decisions`
    already enforces on this codebase's other verdict-affecting modules, extended here to the
    difference-element SELECTION itself, not only the final verdict.
  - A SINGLE-STROKE-vs-SINGLE-STROKE candidate pair (n_true==n_pred==1) falls out of the SAME
    "equal counts" branch with exactly one matched pair -- its difference element is trivially
    its own WHOLE (only) stroke, exactly design point 4's "single-stroke candidates: difference
    element = whole stroke -- the contrastive pass then degenerates to the global compare on
    that stroke." No special-cased code path; `single_stroke` is reported for the run script's
    own honest-count instrument.
  - UNEQUAL stroke counts (design point 4: "the unmatched stroke IS the difference element"):
    each candidate's difference element is the CONCATENATION of every one of its OWN unmatched
    strokes' normalized points (ALL of them -- never a Python pick of "the smallest," which was
    RUN 36's own diagnostic convention for a DIFFERENT purpose, not this decision). A per-glyph
    greedy match with unequal counts always leaves unmatched strokes on AT MOST one side (the
    longer one) -- see `difference_elements`'s own docstring for why -- so exactly one of the
    two candidates typically ends up with an EMPTY difference element (a strict-subset pair);
    `contrastive_pick` below names this the ONE-SIDED case and handles it with its own
    pre-registered rule (see that function's docstring) rather than silently falling back.
  - NO MEANINGFUL DIFFERENCE (design point 4's explicit fallback): both candidates' difference
    elements end up empty (e.g. every stroke on both sides was itself degenerate and filtered
    away) -- the caller falls back to the GLOBAL verdict for that episode, `decision=
    "fallback_no_diff"`.

CONTRASTIVE SCORE (design point 3, `contrastive_winner = argmin_i d(query_region_i, diff_
element_i)`): `d` is realized as a held `MinOver(PointSetDist(Lit(diff_element), Var(q)))`
over the QUERY's OWN per-stroke normalized point arrays (`run36._normalize_glyph` applied to
the query's own strokes, the SAME per-glyph centre+abs-max frame used on every other side of
this comparison) -- "the BEST-matching region of the query" is realized as a per-stroke
MinOver so the query's own EXISTING stroke segmentation supplies the region boundaries, never
a fresh Python-side windowing/sub-sampling scheme. The two-sided verdict is ONE held `Argmin`
(`abs_read._argmin_pairs_term`, reused verbatim) over `[(score1, cand1_idx), (score2,
cand2_idx)]` -- never a Python `min` ranked by a key-function.

THE ONE-SIDED CASE (`contrastive_pick`, unequal-count pairs where exactly one candidate's
difference element is non-empty): there is no symmetric second region to compare against, so
`argmin` over two regions is not available. The pre-registered proxy (stated honestly as a
proxy, in the same spirit as RUN 36's own "coarse, self-contained stand-in... never mistaken
for a calibrated result"): compare `score_extra = d(query, diff_extra)` (does the query's own
ink explain the EXTRA candidate's distinguishing strokes) against `baseline = mean(matched
pair costs)` from the SAME cand1-vs-cand2 greedy match (how different the two candidates'
SHARED strokes already look from each other, in the SAME `PointSetDist` units) -- if the
query's evidence for the extra region is AT LEAST AS GOOD as the two candidates' own shared-
stroke agreement, the extra region is judged present (the candidate WITH it wins); otherwise
the subset candidate wins. This reuses the SAME comparator family and the SAME per-episode
scale (no new tunable constant) but is explicitly weaker evidence than the two-sided case, and
is reported as its own `decision="one_sided"` bucket in every run-script table -- never
conflated with the two-sided verdict.

ARCHITECTURE (CLAUDE.md): every function below is either mechanical held-Term construction (a
comparison Term, an Argmax/Argmin/MinOver invocation) or a fixed-arity read of a value a HELD
Term already produced -- reusing `run36`'s stroke-matching machinery and `abs_read`'s existing
comparator/ranking Terms verbatim, adding no new Rust. No Python argmin/argmax/sort-by-score
anywhere in this module except the two documented, held-Term-replaced selections above; see
`tests/test_contrastive_verdict_migrated.py::test_contrastive_verdict_no_python_decisions`
for the source-level audit (the SAME regex discipline `test_abs_read_no_python_decisions`
already applies to `domains/abs_read.py`)."""
from __future__ import annotations

from typing import Optional

import numpy as np

from domains import abs_read as ar
from scripts import jabberwock_omniglot_run36_failures as run36


def _native(agent):
    return getattr(agent, "_inner", agent)


# --------------------------------------------------------------------------------------------- #
#  TOP-2 -- the per-candidate score vector `abs_read.parse_marginal_pair_error` already exposes
#  (RUN 25's `_c2_scale_probe` precedent), repeated held-Argmin ("remaining index list") twice --
#  the SAME idiom `abs_read.propose_top_k` established for its own repeated-Argmax shortlist,
#  here Argmin because LOWER parse-marginal error is better.
# --------------------------------------------------------------------------------------------- #
def top2_candidates(scratch, query_node: int, cand_nodes: dict[int, int]) -> list[tuple[float, int]]:
    """`cand_nodes`: `{candidate_index: staged_node_id}` (the SAME dict shape `run25._stage_
    candidates`'s own `cand0`/`node0` pairing already produces, inverted). Returns up to two
    `(score, candidate_index)` pairs ascending by score (lower = better) -- the global verdict's
    OWN winner is guaranteed to be `top2[0][1]` (a consistency check the run script's own guard
    stage asserts against `parse_marginal_verdict`'s independently-computed Argmax winner,
    never assumed). An empty or single-candidate pool returns fewer than two pairs, never a
    fabricated second entry."""
    native = _native(scratch)
    remaining = dict(cand_nodes)
    top2: list[tuple[float, int]] = []
    for _ in range(min(2, len(remaining))):
        pairs = [(ar.parse_marginal_pair_error(scratch, query_node, node), ci)
                 for ci, node in remaining.items()]
        w = native.evaluate(ar._argmin_pairs_term(pairs), {})
        if w is None:
            break
        ci = int(w[1])
        top2.append((float(w[0]), ci))
        del remaining[ci]
    return top2


# --------------------------------------------------------------------------------------------- #
#  DIFFERENCE REGION -- run36's own greedy per-stroke match, reused verbatim.
# --------------------------------------------------------------------------------------------- #
def _worst_matched_pair(native, matched: list) -> Optional[tuple[int, int]]:
    """Held `Argmax` (`abs_read._argmax_pairs_term`, reused verbatim) over the ALREADY-COMPUTED
    per-stroke match costs -- the SINGLE worst-matched (i, j) pair, never a Python `max`
    ranked by a key-function. `matched`: `[(i, j, cost), ...]`, `run36._greedy_stroke_match`'s
    own shape."""
    if not matched:
        return None
    pairs = [(float(c), [int(i), int(j)]) for (i, j, c) in matched]
    w = native.evaluate(ar._argmax_pairs_term(pairs), {})
    if w is None:
        return None
    idx = w[1]
    return int(idx[0]), int(idx[1])


def _normalize_glyph_shared(strokes: list) -> tuple:
    """A POSITION-PRESERVING glyph frame -- the shared-frame twin of `run36._normalize_glyph`.

    `run36._normalize_glyph` recenters each glyph on its OWN ink CENTROID (then abs-max
    scales); the centroid depends on the ink distribution, so the SAME figure-position (a
    crossbar high up, a foot at the baseline) lands at DIFFERENT coordinates in two glyphs and
    the position where a stroke SITS is destroyed. That is exactly why the committed
    centroid-frame contrastive verdict fixes the SHAPE-difference pairs (A/O closure, G/Q
    terminal) but cannot separate the POSITION-difference pairs (F/L: same crossbar-shaped
    stroke, different height). This frame instead pins the glyph's own bounding-box min-corner
    to the origin and scales by the max extent, so a stroke at 70% height maps to y~0.7 in ANY
    glyph's frame -- a canonical figure frame shared across glyphs, in which "where the bar
    sits" survives into the region compare. Same `(normed_strokes, offset, scale)` return shape
    as `run36._normalize_glyph`, so it drops into `difference_elements`/`contrastive_pick` as a
    `normalize=` argument with no other change. No new Rust, no new Term -- the position/scale
    prep is host data-preparation, exactly the category `run36._normalize_glyph` already is."""
    pts = np.concatenate([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes], axis=0)
    lo = pts.min(axis=0)
    span = float((pts.max(axis=0) - lo).max()) or 1e-9
    normed = [(np.asarray(s, dtype=float).reshape(-1, 2) - lo) / span for s in strokes]
    return normed, lo, span


def difference_elements(native, cand1_strokes: list, cand2_strokes: list,
                        normalize=None) -> dict:
    """The two candidates' own DIFFERENCE ELEMENTS -- see this module's own top-of-file
    docstring, "PRE-REGISTERED DIFFERENCE-ELEMENT RULE", for the exact branch logic. `native`:
    a raw substrate_rs binding (or anything `getattr(x, "_inner", x)` degrades through).
    `cand1_strokes`/`cand2_strokes`: raw per-stroke point arrays as `omniglot_world.load_
    strokes` returns them (a list of `(n_i, 2)` arrays) -- the CALLER is responsible for having
    loaded them with the degenerate filter active (`jabberwock_omniglot_run37c_hygiene.
    DropDegenerateFilter`, MANDATORY per the design; this function never touches disk itself,
    so it cannot silently bypass that filter).

    A greedy match with UNEQUAL stroke counts always leaves unmatched strokes on AT MOST one
    side: `run36._greedy_stroke_match` assigns pairs in ascending-cost order until either index
    set is exhausted, so it always completes exactly `min(n_true, n_pred)` pairs -- the shorter
    side is therefore ALWAYS fully matched, and only the longer side can have leftovers. This
    is why the one-sided case (`contrastive_pick`'s own docstring) is the ONLY unequal-count
    shape that can occur, never a "both sides have unmatched strokes" case.

    Returns a dict: `ok` (at least one side has a non-empty difference element), `kind`
    (`"worst_matched"` or `"unmatched"`), `single_stroke` (both candidates are exactly one
    stroke), `count_mismatch`, `diff1`/`diff2` (lists of `[x, y]` points, possibly empty),
    `matched_costs` (the raw per-stroke costs from the SAME greedy match, the one-sided case's
    own shared-baseline ingredient), `n_true`/`n_pred` (the two candidates' own stroke counts,
    `run36`'s own naming -- `cand1`==`"true"`, `cand2`==`"pred"` in that function's argument
    order, kept here only as the pass-through field names).

    A CANDIDATE WITH ZERO STROKES (both empty, or one side empty) is handled directly here,
    never handed to `run36._greedy_stroke_match`/`_normalize_glyph` (which divide/concatenate
    over the stroke list and crash on an empty one) -- an honest degenerate result, never a
    fabricated match.

    `normalize`: the per-glyph frame builder (default `run36._normalize_glyph`, the committed
    centroid frame). Pass `_normalize_glyph_shared` for the POSITION-PRESERVING frame (F/L)."""
    nrm = normalize or run36._normalize_glyph
    if not cand1_strokes and not cand2_strokes:
        return dict(ok=False, kind="empty", single_stroke=False, count_mismatch=False,
                    diff1=[], diff2=[], matched_costs=[], n_true=0, n_pred=0)
    if not cand1_strokes or not cand2_strokes:
        # Exactly one side is empty -- every stroke on the OTHER side is, by construction,
        # unmatched (there is nothing on the empty side to pair it with).
        if cand1_strokes:
            norm, _, _ = nrm(cand1_strokes)
            diff1 = np.concatenate(norm, axis=0).tolist()
            diff2: list = []
            n_true, n_pred = len(cand1_strokes), 0
        else:
            norm, _, _ = nrm(cand2_strokes)
            diff1 = []
            diff2 = np.concatenate(norm, axis=0).tolist()
            n_true, n_pred = 0, len(cand2_strokes)
        return dict(ok=bool(diff1 or diff2), kind="unmatched", single_stroke=False,
                    count_mismatch=True, diff1=diff1, diff2=diff2, matched_costs=[],
                    n_true=n_true, n_pred=n_pred)

    gm = run36._greedy_stroke_match(native, cand1_strokes, cand2_strokes)
    t_norm, _, _ = nrm(cand1_strokes)
    p_norm, _, _ = nrm(cand2_strokes)

    count_mismatch = bool(gm["unmatched_true"] or gm["unmatched_pred"])
    kind = "unmatched" if count_mismatch else "worst_matched"
    single_stroke = (gm["n_true"] == 1 and gm["n_pred"] == 1)

    if count_mismatch:
        diff1 = (np.concatenate([t_norm[i] for i in gm["unmatched_true"]], axis=0).tolist()
                 if gm["unmatched_true"] else [])
        diff2 = (np.concatenate([p_norm[j] for j in gm["unmatched_pred"]], axis=0).tolist()
                 if gm["unmatched_pred"] else [])
    else:
        wp = _worst_matched_pair(native, gm["matched"])
        if wp is None:
            diff1, diff2 = [], []
        else:
            i, j = wp
            diff1 = t_norm[i].tolist()
            diff2 = p_norm[j].tolist()

    matched_costs = [float(c) for (_, _, c) in gm["matched"]]
    ok = bool(diff1) or bool(diff2)
    return dict(ok=ok, kind=kind, single_stroke=single_stroke, count_mismatch=count_mismatch,
                diff1=diff1, diff2=diff2, matched_costs=matched_costs,
                n_true=gm["n_true"], n_pred=gm["n_pred"])


# --------------------------------------------------------------------------------------------- #
#  CONTRASTIVE SCORE -- held MinOver(PointSetDist) region distance, held Argmin verdict.
# --------------------------------------------------------------------------------------------- #
# `MinOver`'s `default` field is a REQUIRED part of the Term's own JSON schema, even though it
# is never actually reached here (`region_score` only ever calls `_region_score_term` after
# confirming `query_norm_strokes` is non-empty) -- a large FINITE sentinel, never `float("inf")`
# / NaN, since either would fail to round-trip through the native binding's own JSON transport
# (Python's `json` module emits the non-standard `Infinity`/`NaN` literals, which the Rust-side
# strict JSON parser rejects outright).
_UNREACHABLE_DEFAULT = 1.0e9


def _region_score_term(diff_points: list, query_norm_strokes: list) -> dict:
    return {"type": "MinOver",
            "source": {"type": "Lit", "value": query_norm_strokes},
            "var_name": "q",
            "value": {"type": "PointSetDist", "a": {"type": "Lit", "value": diff_points},
                      "b": {"type": "Var", "name": "q"}},
            "default": {"type": "Lit", "value": _UNREACHABLE_DEFAULT}}


def region_score(native, diff_points: list, query_norm_strokes: list) -> float:
    """Held `MinOver(PointSetDist(Lit(diff_points), Var(q)))` over the query's OWN per-stroke
    normalized point arrays -- design point 3's `d(query_region_i, diff_element_i)`, "the
    BEST-matching region of the query" realized via the query's own existing stroke
    segmentation, never a fresh Python windowing scheme. Returns `float("inf")` (never a
    fabricated score, never a crash) for an empty `diff_points` or an empty query."""
    if not diff_points or not query_norm_strokes:
        return float("inf")
    return float(native.evaluate(_region_score_term(diff_points, query_norm_strokes), {}))


def _mean_cost_term(costs: list) -> dict:
    return {"type": "Div",
            "a": {"type": "Sum", "source": {"type": "Lit", "value": costs}, "var_name": "c",
                  "value": {"type": "Var", "name": "c"}},
            "b": {"type": "Lit", "value": float(len(costs))}}


def contrastive_pick(native, query_strokes: list, cand1_strokes: list, cand2_strokes: list,
                      cand1_idx: int, cand2_idx: int, normalize=None) -> dict:
    """THE contrastive re-judgement for ONE episode's top-2. `query_strokes`/`cand1_strokes`/
    `cand2_strokes`: raw per-stroke point arrays, ALREADY loaded with the degenerate filter
    active by the caller (this function never touches disk). `cand1_idx`/`cand2_idx`: the
    candidate indices `top2_candidates` returned, `cand1_idx` being the global verdict's own
    winner (`top2[0][1]`) by construction of that function's caller.

    Returns a dict always carrying `winner` (a candidate index -- `cand1_idx` on every fallback
    branch, so a caller that always substitutes `winner` for the global pick is safe even when
    the contrastive pass found nothing) and `decision` naming which branch fired:
      - `"fallback_no_diff"`   -- design point 4's explicit "no meaningful difference" case.
      - `"fallback_no_shared_baseline"` -- the one-sided case's own shared-baseline
        (`matched_costs`) was empty (candidates share literally no strokes at all) -- an honest
        second fallback the design's one-sided proxy cannot resolve without a baseline.
      - `"one_sided"`          -- unequal stroke counts, exactly one candidate's difference
        element is non-empty (see this module's own top-of-file docstring for the proxy rule).
      - `"two_sided"`          -- the general case: both candidates have a non-empty difference
        element, decided by a held `Argmin` over `[(score1, cand1_idx), (score2, cand2_idx)]`.
    """
    nrm = normalize or run36._normalize_glyph
    diff = difference_elements(native, cand1_strokes, cand2_strokes, normalize=normalize)
    result: dict = dict(cand1_idx=cand1_idx, cand2_idx=cand2_idx, **diff)

    if not diff["ok"]:
        result.update(decision="fallback_no_diff", winner=cand1_idx)
        return result

    q_norm, _, _ = nrm(query_strokes)
    q_norm_lists = [q.tolist() for q in q_norm]

    if diff["count_mismatch"]:
        has1, has2 = bool(diff["diff1"]), bool(diff["diff2"])
        if has1 and has2:
            pass  # both sides non-empty (can happen only if BOTH counts differ from a THIRD
                  # implicit shape -- not reachable per this function's own docstring, but
                  # handled uniformly by falling through to the two-sided branch below rather
                  # than asserting, an honest non-crash).
        elif has1 or has2:
            extra_idx, extra_points = (cand1_idx, diff["diff1"]) if has1 else (cand2_idx, diff["diff2"])
            other_idx = cand2_idx if has1 else cand1_idx
            if not diff["matched_costs"]:
                result.update(decision="fallback_no_shared_baseline", winner=cand1_idx)
                return result
            baseline = float(native.evaluate(_mean_cost_term(diff["matched_costs"]), {}))
            score_extra = region_score(native, extra_points, q_norm_lists)
            winner = extra_idx if score_extra <= baseline else other_idx
            result.update(decision="one_sided", extra_idx=extra_idx, other_idx=other_idx,
                          score_extra=score_extra, baseline=baseline, winner=winner)
            return result
        else:
            result.update(decision="fallback_no_diff", winner=cand1_idx)
            return result

    score1 = region_score(native, diff["diff1"], q_norm_lists)
    score2 = region_score(native, diff["diff2"], q_norm_lists)
    pairs = [(score1, cand1_idx), (score2, cand2_idx)]
    w = native.evaluate(ar._argmin_pairs_term(pairs), {})
    winner = int(w[1]) if w is not None else cand1_idx
    result.update(decision="two_sided", score1=score1, score2=score2, winner=winner)
    return result
