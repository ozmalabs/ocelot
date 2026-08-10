"""domains/motor_plan.py -- RUN 39 FULL GATE: the MOTOR-PLAN AGREEMENT SCORE, an ADDITIVE
evidence channel (RUN 37A's law, cca938fd, BINDING: focused/auxiliary evidence SUPPLEMENTS
integrated evidence, never replaces it).

GATE 0 (commit 6b85f14c, `scripts/jabberwock_omniglot_run39_motorplan.py`) licensed TWO live
pen-up features on the background split, LEARN alphabets quarantined (class-shuffled-null
excess, run-35's own 2x-null LIVE bar): TRANSITIONS (pen-up travel sector, end_N -> start_
{N+1}, 8-way compass quantization; raw 0.680 vs null 0.229, ~3x null, LIVE for all classes and
the 1-2-stroke desert) and START POSITION (first pen-down, 3x3 grid on the run-36-normalized
glyph frame; raw 0.583 vs null 0.284, strongest in the 1-stroke bucket). ORDER and DIRECTION
are DEAD -- their class-shuffled null absorbs the population-wide drawing CONVENTION (canonical
stroke first, canonical polarity), not identity -- and this module never uses them.

THIS MODULE is the QUERY-VS-ONE-CANDIDATE analogue of gate0's own WITHIN-CLASS machinery:
gate0 measured whether MANY drawers of the SAME known class cohere on a feature; here, at
verdict time, the class is exactly what is unknown -- `motor_plan_agreement` asks how well ONE
query's motor plan agrees with ONE candidate exemplar's motor plan, for every candidate the
verdict considers, and returns a single bounded score in [0, 1].

THE FORMULA (pre-registered BEFORE any RUN 39 FULL GATE number was computed):
    m(query, candidate) = w_s * start_agree + w_t * transitions_frac      [both computable]
                         = start_agree                                    [transitions skipped]
    w_s = w_t = 0.5, FIXED a priori -- never tuned against any eval outcome. (`W_START_DEFAULT`/
    `W_TRANS_DEFAULT` below; a caller wanting the background-calibrated pair would pass explicit
    weights, but this run's own calibration only ever tunes `lam`/`threshold`, per the launch
    brief -- the 0.5/0.5 split itself is stated, not fit.)

  START AGREEMENT (`start_agree`, ALWAYS computable -- every glyph has a first pen-down):
    1.0 iff the query's own first pen-down and the candidate's own first pen-down, both
    quantized to gate0's 3x3 grid over the run-36-normalized [-1,1]^2 frame (`gate0.
    normalize_glyph_xy`/`gate0.grid_cell`, imported and reused VERBATIM below -- the caller is
    responsible for handing in ALREADY-normalized per-stroke arrays, mechanical I/O, no
    decision here), land in the SAME cell; else 0.0.

  TRANSITIONS AGREEMENT (`transitions_frac`, gate0's `transitions` feature's cross-object
    analogue): requires the query and candidate to have the SAME stroke count (else SKIPPED,
    `skip_reason="count_mismatch"` -- gate0's own 26% "wrong stroke count" QC fact, reported
    here as a per-pair skip rate, never silently imputed as agreement OR disagreement). A
    single-stroke pair (both n==1) has no transition to compute at all (`skip_reason=
    "single_stroke"`, a structural fact, not a data-quality one -- kept in its own bucket).
    When counts match and n>=2: `gate0.greedy_match` (THE FALSY-ZERO BUG FIX included --
    `float(v) if v is not None else nan`, never `v or nan`) spatially corresponds the
    CANDIDATE's own strokes to the QUERY's own strokes via the held `PointSetDist` Term,
    cheapest-cost-first, no double assignment -- exactly gate0's own per-class reference
    matcher, here matching TWO OBJECTS instead of a class reference against many drawers. A
    full bijection is required (`len(mapping) == n_strokes`); an incomplete match (an
    unreachable empty-point-set edge case in practice) skips transitions too, reported
    separately (`skip_reason="incomplete_match"`). Given the bijection
    `mapping: query_position -> candidate_position`, for each of the QUERY's own k-1
    consecutive draw-order transitions p (end of its stroke at position p -> start of its
    stroke at position p+1): the transition is COMPARABLE only if the candidate ALSO draws its
    own matched strokes `mapping[p]`/`mapping[p+1]` consecutively
    (`mapping[p+1] == mapping[p] + 1` -- the spatial correspondence preserves adjacency, i.e.
    the two objects executed this pair of matched strokes back-to-back in the SAME relative
    order); agreement on a comparable slot is 1.0 iff the query's own sector-8 quantized pen-up
    vector at position p equals the candidate's own sector-8 quantized pen-up vector at position
    `mapping[p]` (`gate0.sector8`, 8 compass bins, reused verbatim). `transitions_frac` is the
    mean agreement over comparable slots; when NO slot is comparable (every matched pair is
    spatially reordered relative to draw order), transitions is SKIPPED under a third, distinct
    reason (`skip_reason="no_comparable_transitions"`) -- never conflated with a stroke-count
    mismatch, which is a data fact, not a same-count-different-order fact.

ARCHITECTURE (CLAUDE.md, world-adapter-class feature extractor -- the same class `domains/
committed_shape.py`/`domains/contrastive_verdict.py` already are): this module imports and
reuses `scripts.jabberwock_omniglot_run39_motorplan`'s own feature extractors (`normalize_
glyph_xy`, `grid_cell`, `sector8`, `greedy_match`) VERBATIM -- the SAME "reuse a script's own
machinery rather than reimplement it" precedent `domains.contrastive_verdict` already
established for `scripts.jabberwock_omniglot_run36_failures`. The two DECISIONS this module
adds on top of that geometry -- the VERDICT SUPPLEMENT (`combined_verdict`, RUN 39B ARM V) and
the PROPOSAL fallback ranking (`propose_by_motor_plan`, RUN 39B ARM P) -- are held
Argmin/Argmax Terms (`abs_read._argmin_pairs_term`/`_argmax_pairs_term`, reused verbatim, the
SAME idiom `domains.contrastive_verdict` already uses for its own two-sided verdict and worst-
matched-pair selection), never a Python min/max/sorted-by-score; see `tests/test_motor_
supplement_migrated.py`'s own source audit. `motor_plan_agreement` itself makes no ranking
decision at all -- it is pure arithmetic over an already-computed bijection and two already-
quantized categorical values, mirroring `committed_shape.commit_shape`'s own "mechanical,
deterministic transform" class.
"""
from __future__ import annotations

from typing import Optional

from domains import abs_read as ar
from scripts import jabberwock_omniglot_run39_motorplan as gate0

W_START_DEFAULT = 0.5              # pre-registered a priori, never tuned against an outcome.
W_TRANS_DEFAULT = 0.5
K_ADD_DEFAULT = 5                  # mirrors committed_shape.K_ADD_DEFAULT -- pre-registered cap
                                    # on motor-plan proposals ADDED into a union, never tuned.
LAMBDA_GRID = (0.05, 0.1, 0.2, 0.4)    # ARM V's pre-registered background-calibration grid.
THRESHOLD_GRID = (1.0, 0.75, 0.5)      # ARM P's pre-registered background-calibration grid.


def _own_transition_vector(strokes_xy_norm: list, p: int):
    """The vector from the end of the glyph's OWN stroke at draw-position `p` to the start of
    its own stroke at draw-position `p + 1` -- gate0's own `transitions` feature ingredient,
    read directly off a single object's own already-normalized per-stroke arrays (no
    correspondence needed for THIS half of the computation)."""
    end_pt = strokes_xy_norm[p][-1]
    start_pt = strokes_xy_norm[p + 1][0]
    return start_pt - end_pt


def motor_plan_agreement(native, query_xy_norm: list, cand_xy_norm: list, *,
                          w_start: float = W_START_DEFAULT,
                          w_trans: float = W_TRANS_DEFAULT) -> dict:
    """m(query, candidate) in [0, 1] -- see this module's own top-of-file docstring for the
    pre-registered formula. `query_xy_norm`/`cand_xy_norm`: each a list of per-stroke
    `(n_i, 2)` arrays, own draw order, ALREADY normalized via `gate0.normalize_glyph_xy`
    (mechanical I/O, the caller's job -- this function makes no decision about how
    normalization happened).

    Returns `{m, start_agree, transitions_frac (float or None), skip_reason (None /
    "count_mismatch" / "single_stroke" / "incomplete_match" / "no_comparable_transitions"),
    n_comparable}` -- `skip_reason` is None iff `transitions_frac` genuinely entered the
    formula; every skip degrades to `m = start_agree` alone (renormalized weight, never a
    fabricated zero for missing evidence)."""
    q_start = gate0.grid_cell(query_xy_norm[0][0])
    c_start = gate0.grid_cell(cand_xy_norm[0][0])
    start_agree = 1.0 if q_start == c_start else 0.0

    nq, nc = len(query_xy_norm), len(cand_xy_norm)
    if nq != nc:
        return dict(m=start_agree, start_agree=start_agree, transitions_frac=None,
                    skip_reason="count_mismatch", n_comparable=0)
    if nq < 2:
        return dict(m=start_agree, start_agree=start_agree, transitions_frac=None,
                    skip_reason="single_stroke", n_comparable=0)

    mapping = gate0.greedy_match(native, cand_xy_norm, query_xy_norm)   # query_pos->cand_pos
    if len(mapping) != nq:
        return dict(m=start_agree, start_agree=start_agree, transitions_frac=None,
                    skip_reason="incomplete_match", n_comparable=0)

    n_comparable = 0
    n_agree = 0
    for p in range(nq - 1):
        cp, cp1 = mapping[p], mapping[p + 1]
        if cp1 != cp + 1:
            continue
        n_comparable += 1
        q_sector = gate0.sector8(_own_transition_vector(query_xy_norm, p))
        c_sector = gate0.sector8(_own_transition_vector(cand_xy_norm, cp))
        if q_sector == c_sector:
            n_agree += 1

    if n_comparable == 0:
        return dict(m=start_agree, start_agree=start_agree, transitions_frac=None,
                    skip_reason="no_comparable_transitions", n_comparable=0)

    transitions_frac = n_agree / n_comparable
    m = w_start * start_agree + w_trans * transitions_frac
    return dict(m=m, start_agree=start_agree, transitions_frac=transitions_frac,
                skip_reason=None, n_comparable=n_comparable)


# ------------------------------------------------------------------------------------------- #
#  ARM V -- VERDICT SUPPLEMENT (RUN 37A's law: supplement, never replace).
# ------------------------------------------------------------------------------------------- #
def combined_verdict(native, full_pairs: list, m_by_idx: dict, lam: float) -> Optional[int]:
    """`full_pairs`: the GLOBAL verdict's own per-candidate `(err, candidate_index)` pairs
    (`abs_read.parse_marginal_pair_error`, LOWER = better -- `abs_read.parse_marginal_verdict`
    is `Argmax(-err)` == `Argmin(err)` over the SAME quantity). `m_by_idx`:
    `{candidate_index: m}` motor-plan agreement, `m in [0, 1]`, missing entries default to 0.0
    (no motor-plan evidence for that candidate contributes no bonus, never a penalty).

    `combined(ci) = err(ci) - lam * m(ci)` -- higher motor-plan agreement LOWERS the effective
    error, exactly a SUPPLEMENT: `lam=0.0` recovers `argmin(err)` alone, BYTE-IDENTICAL to the
    GLOBAL verdict's own winner (gated by `tests/test_motor_supplement_migrated.py`'s own
    lambda-zero-recovers-global test) -- the motor-plan channel can only ever nudge a close
    call, never overrule a large parse-marginal gap on its own (`lam` is calibrated on
    background episodes to stay small relative to typical `err` spreads; see RUN 39B's own
    calibration stage). Winner = held `Argmin` (`abs_read._argmin_pairs_term`, reused verbatim)
    over the combined pairs -- never a Python `min()`."""
    combined_pairs = [(err - lam * m_by_idx.get(ci, 0.0), ci) for err, ci in full_pairs]
    w = native.evaluate(ar._argmin_pairs_term(combined_pairs), {})
    return int(w[1]) if w is not None else None


# ------------------------------------------------------------------------------------------- #
#  ARM P -- PROPOSAL MODALITY #4, additive only (RUN 37B's own union precedent).
# ------------------------------------------------------------------------------------------- #
def propose_by_motor_plan(native, m_scores: list, *, threshold: float,
                           k_add: int = K_ADD_DEFAULT) -> list:
    """`m_scores`: `[(candidate_index, m), ...]`, ASCENDING candidate-index order (the caller's
    own responsibility -- this function performs no reordering of its own). PRIMARY rule: every
    candidate at or above `threshold` (background-calibrated, RUN 39B's own calibration stage),
    kept in the caller's own ascending-index order (mirrors `committed_shape.propose_by_
    committed_shape`'s own index-order convention), capped at `k_add`. FALLBACK (only when NO
    candidate clears `threshold`, mirroring `committed_shape`'s own exact-then-fallback
    structure): the top `k_add` candidates by `m`, via REPEATED held `Argmax`
    (`abs_read._argmax_pairs_term`, `propose_top_k`'s own idiom) -- never a Python
    sort/key ranking by the score. Caller unions the result into an existing candidate set
    (e.g. `committed_shape.union_candidates`, which this module does not re-implement) --
    additive only, this function never removes or reorders anyone else's candidates."""
    above = [ci for ci, m in m_scores if m >= threshold][:k_add]
    if above:
        return above
    remaining = {ci: m for ci, m in m_scores}
    order: list = []
    for _ in range(min(k_add, len(remaining))):
        pairs = [(m, ci) for ci, m in remaining.items()]
        w = native.evaluate(ar._argmax_pairs_term(pairs), {})
        if w is None:
            break
        idx = int(w[1])
        order.append(idx)
        del remaining[idx]
    return order


__all__ = ["W_START_DEFAULT", "W_TRANS_DEFAULT", "K_ADD_DEFAULT", "LAMBDA_GRID",
           "THRESHOLD_GRID", "motor_plan_agreement", "combined_verdict",
           "propose_by_motor_plan"]
