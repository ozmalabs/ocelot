"""abs_read — the "ABS AS DEFAULT" S item of scratchpad/HANDWRITING_DESIGN.md: "the
generation and reading model is the same, like speech — AbS is the default. It just runs
the same engine in reverse." A stroke quantum is a GENERATIVE program (`StrokeQuantize`'s
own signature dequantizes back to a polyline via its Rust-side inverse, `StrokeRender`,
`strokes.rs`); reading a character is PROPOSE (the fast, already-earned quantized-index
coverage that earns 33.8%, UNCHANGED) then RENDER-COMPARE (the generative verdict): for
each of the top-K proposed exemplars, render its own held stroke quanta at the QUERY's own
decoded per-stroke poses (draw-order correspondence) and score the render against the
query's ACTUAL observed ink via ONE held comparison Term per candidate — final pick is a
held `Argmin` over the K candidates. The frame-anchor instability the earlier ARRANGEMENT
FIDELITY lever tried to patch with a quantized-frame fix (`assignment_coverage_term`,
measured WORSE twice — "STRICTNESS IS THE SIGNAL") dissolves here rather than being
patched further: bins only ever PROPOSE a shortlist; the verdict is continuous, fitted-pose
render-compare, so no cross-drawer BIN agreement is required to win.

ARCHITECTURE (CLAUDE.md): every function in this module is MECHANICAL — Term construction
(a render invocation, a comparison Term) or a fixed-arity read of a value a HELD Term
already produced. `propose_top_k` calls a held `Argmax` K times over a Python-managed
"remaining" index list (removing an already-decided winner is bookkeeping, not a ranking —
the SAME single-winner idiom every classification loop in this codebase already uses,
repeated K times, never a Python sort/argmax over the candidates' own scores); the final
verdict is ONE held `Argmin` evaluate over the K candidates' own already-computed scores.
No Python argmin/argmax/sort-by-score anywhere in this module (see
`tests/test_character_composition_migrated.py::test_character_compose_no_python_decisions`'s
audit pattern, mirrored for this module in `tests/test_character_composition_migrated.py`'s
own ABS AS DEFAULT section).

`StrokeRender` (strokes.rs, beside its inverse `StrokeQuantize`) is being built in PARALLEL
against this design (2026-07-03) — `_stroke_render_live()` below is the SAME "authored, not
yet operative" probe pattern `stroke_codebook._stroke_quantize_live()` established before
`StrokeQuantize` itself landed. Every function here that needs a real render degrades to an
honest `None`/empty result (never a fabricated score) when the probe is False; callers (the
Omniglot script's RUN 10, the pytest gates) check the probe FIRST and report authorable-work
status honestly rather than print a number that was never actually computed by the Term.

PROPOSAL RECALL / VARIABLE-APERTURE DWELL (scratchpad/HANDWRITING_DESIGN.md's section of the
same name, the 42855d5f residual + the radar frame's first falsifiable instance, 2026-07-03):
RUN 10 measured coverage@5 = 53.8% — the fixed K=5 shortlist misses the true exemplar on
~46% of episodes BEFORE render-compare ever gets a look. The radar frame's dwell-scheduling
principle ("spend renders where proposal AMBIGUITY is high; ties = widen the beam, clear
margin = narrow") is realized here as `propose_variable_k`: the shortlist is every candidate
within margin `delta` (DATA) of the top proposal score, decided by held `MaxOver` (read the
ambiguity signal) + held `FilterList` (the shortlist-SIZE decision, a Count/Filter over the
proposal pairs) — never a Python score branch. `abs_rerank` below now accepts an optional
pre-computed `top_k` list so callers can swap in `propose_variable_k`'s (or a full-dwell,
all-candidates) shortlist in place of the fixed-K `propose_top_k` call, with every downstream
step (render-compare per candidate, held Argmin verdict) unchanged. `proposal_rank` is the
RECALL-TAIL instrument: the 1-based rank of the true exemplar in the SAME proposal ordering,
for episodes where it fell outside the K=5 shortlist — read off via held `Count(FilterList)`,
never a Python sort.

TARGETED WIDEN + SECOND MODALITY (scratchpad/HANDWRITING_DESIGN.md's section of the same
name, the 6db362d1 residual, 2026-07-03): state going in — delta=0 variable-K control 38.8%
@ mean 2.05 renders; uniform widening measured monotonically HARMFUL (delta=1/2 both lose to
delta=0); recall-tail: 16/37 misses beam-reachable (rank 6-10), 3 proposal-blind (rank 16+).
Two independent, additive levers, both realized as held Terms over ALREADY-COMPUTED scores
(never a Python score branch):

LEVER 1 — TARGETED WIDEN (`widen_decision`, radar "track-quality feedback: bad track -> back
to search"): AFTER the delta=0 re-rank, a SECOND-STAGE ambiguity signal — held
`Or(Lt(Minus(runner_up, best), margin_threshold), Gt(best, fit_threshold))` — decides whether
to widen and re-dwell ONCE (`abs_rerank_targeted`'s `use_widen`). `runner_up`/`best` are
read off the delta=0 re-rank's OWN render-compare scores via held `MinOver` (+ the SAME
held-`Argmin` winner-id `abs_rerank` itself already computes, excluded from the "remaining"
list as bookkeeping — the identical idiom `propose_top_k` uses to remove an already-decided
winner). Both thresholds are DATA (design: "as data args"); a widen re-dwells over
`propose_top_k(k=widen_to)` — "proposal ranks up to W" — ONCE, never iteratively (design:
"no iterative loops this phase").

LEVER 2 — SECOND PROPOSAL MODALITY (`propose_appearance_top_m`, a different search angle,
non-overlapping blind spots with the structural/coverage proposal): direct APPEARANCE
proposal via held `PointSetDist` between the query's OBSERVED ink and each exemplar's own
STORED observed ink — both already in the decode cache (`_stroke_frame_slices` on each
side's own `stroke_points`), no rendering, no new Rust. Top-M via the SAME repeated-`Argmin`
"remaining index list" idiom `propose_top_k` established, just Argmin (distance,
lower-is-better) instead of Argmax (coverage, higher-is-better). The structural and
appearance shortlists are UNIONED (`abs_rerank_targeted`'s `shortlist0`) — a plain Python
`set`/`sorted` over candidate INDICES, mechanical bookkeeping ("the shortlist union
mechanical" per the design), never a ranking of the union's members — before the ONE
render-compare pass that decides the verdict.

`abs_rerank_targeted` combines both levers behind two independent flags
(`use_widen`/`use_appearance`) so ONE function realizes RUN 12's four arms (delta=0 control /
+widen / +appearance / +both); `use_widen=False, use_appearance=False` reproduces RUN 11's
delta=0 control byte-identically (additivity discipline, gated by
`tests/test_character_composition_migrated.py`).

INSTANCE-CONDITIONED QUANTA (scratchpad/HANDWRITING_DESIGN.md's section of the same name, the
a6c7740f endgame clause, 2026-07-03): state going in — 41.2% (delta=0 + appearance top-3); the
far tail (3 proposal-blind cases) is 0/3 reachable by any SEARCH arm; the residual is read as
EXEMPLAR-SIDE — the render-compare verdict approximates every candidate stroke through the
GLOBAL codebook's small (5-7 class) vocabulary, discarding the specific exemplar's own actual
geometry ("the information bound"). Two independent, additive, GENERATION-side levers (never a
Python score branch):

LEVER A — EXEMPLAR-TRUE RENDERING (`_exemplar_true_seg`, `abs_render_compare_term`'s new
`exemplar_true` flag): render each candidate's own STORED per-stroke points (already in the
decode cache, `candidate_stroke_points[ci][k]`) via ONE held `StrokeQuantize` evaluate
(`canonical_pose=True`, the SAME convention `stroke_codebook.grow_stroke_quantum` uses to author
a codebook entry) instead of looking up the shared GLOBAL quantum's stored `seg` (`_candidate_
seg`). No new nodes, no cross-candidate leakage possible (each candidate's own render draws only
from its own stored points) — the cheapest possible test of the information-bound hypothesis.

LEVER B — INSTANCE-CODEBOOK QUERY DECODE (`build_instance_codebook`/`instance_decode_query`/
`instance_conditioned_signatures`): per EPISODE, every candidate's own per-stroke points form a
TEMPORARY codebook on a FRESH, throwaway `substrate_rs.Substrate()` (never the agent's own held
graph — "episode-scoped... nothing persists across episodes, and the LEARN codebook is
untouched"; the scratch substrate is a local variable, garbage-collected the instant the caller
returns, with no edge ever created into the agent's own graph). The query's own per-stroke
points are then re-quantized (invariant-only) and decoded against that scratch instance codebook
via ONE held `ShapeDecode` evaluate per query stroke (the SAME Occam `beam=1/max_steps=1/
cand_k=1` pattern `ink_decode._score_span` already established) — an EXACT match names a
SPECIFIC exemplar-stroke instance, read straight off `covered_by`, never searched/ranked in
Python. The match is surfaced as an ADDITIVE `["strokeq_instance", k, name]` relation on BOTH
the query's own signature and (trivially, by construction — a stroke is its own instance) each
candidate's own signature, so the EXISTING strict-coverage proposal Term (`_coverage_term`,
UNCHANGED) becomes CLASS-SPECIFIC for free: a query stroke matching exemplar 7's own stroke 2
now ONLY boosts candidate 7's proposal score, never a sibling candidate that merely shares the
same coarse GLOBAL quantum. `strokeq`/`strokeq_fine`/`rel`/`cpose` relations are untouched
(additivity — the run-5/eager-child-minting precedent: identity only ever ADDS).

`abs_rerank_targeted`'s new `use_exemplar_true`/`use_instance` flags realize RUN 13's four arms
(control = the RUN 12 adopted config [delta=0 + appearance] / +A / +B / +A+B) on top of the SAME
combinator; both default `False`, reproducing RUN 12's own arms byte-identically.

BRANCH B CONTINUOUS — JUNCTION-BLENDED RENDERING (scratchpad/HANDWRITING_DESIGN.md's "RUN 15 —
POWER THE GATE, THEN BRANCH B CONTINUOUS" section, 2026-07-03, PHASE 2): the jabberwock's OWN
verdict (d2cd7bed) picked sub-stroke composition (Branch A) over junction coarticulation
(Branch B) at the representation grain — Branch A was BUILT and FALSIFIED (RUN 14, 9f10cf74).
This phase executes the surviving fork branch under the SAME "two-grain fragmentation law" that
made discrete Branch A fail: NOT a new discrete relation (no "junction quantum," no context-
conditioned strokeq) — a CONTINUOUS deformation entirely inside the AbS render-compare channel,
the only channel that has ever moved this featureset's accuracy (RUN 10/12's appearance lever).
`_junction_blend` (pure mechanical geometry, no decision — the same class of helper as
`_stroke_frame_slices`/`_rotate_points_deg` elsewhere in this codebase) takes the CANDIDATE's
own already-rendered per-stroke polylines (draw order) and warps each stroke's TRAILING/LEADING
`junction_frac` arc-length-fraction of points LINEARLY toward the shared midpoint of the two
adjacent strokes' own endpoints — a bounded, endpoint-anchored deformation that never touches a
stroke's interior beyond the blended span, and reaches the exact joint value only at the single
outermost point (a taper, not a hard clamp, so the ORIGINAL geometry is never fully discarded).
`abs_render_compare_term`'s new `junction_blend`/`junction_frac` params (both default off, the
byte-identical control): when `junction_blend=True`, each stroke's `StrokeRender` Term is
EVALUATED individually (one extra `native.evaluate` per stroke — the SAME "evaluate to get raw
points" idiom `_exemplar_true_seg`/`instance_decode_query` already use elsewhere in this module)
so the blend can run in Python on the resulting point lists BEFORE the comparison; the blended
points are then fed into the SAME `DtwTo`/`Plus`/`Div` comparison Term shape as a `Lit`, and the
held `Argmin` verdict downstream is completely unchanged — "pure geometry in the compare path;
the compare Terms unchanged, held Argmin unchanged," per the design. `junction_blend=False`
(every pre-existing call site) reproduces the ORIGINAL single-nested-Term-per-candidate
evaluate byte-identically — this function never evaluates anything itself in that mode, exactly
as before. `abs_rerank`/`abs_rerank_targeted`'s new `junction_blend`/`use_junction_blend` +
`junction_frac` params thread straight through to every `abs_render_compare_term` call, off by
default.

RUN 19 -- EARNED PARSE JOINS THE MARGINALIZATION + TOKEN-REFIT (scratchpad/HANDWRITING_DESIGN.md's
section of the same name, 2026-07-03): standing -- parse-marginal 80.5% [76.3, 84.1] @ n=400
(2c669fd1), but it bypasses the EARNED stroke-codebook layer entirely (its own `stage_parse_char`
re-segments every character at a fixed theta GRID, `canonical_parse.canonical_parts`, never
touching `ink_decode.decode_ink`'s own learned segmentation-by-recognition). Two levers, both
GENERAL drawn-shape faculties (never character-specific):

LEVER 1 -- THE RECONCILIATION (1a, `_earned_parts_from_stroke_points`/`stage_parse_char`'s new
`earned_stroke_points` param): the codebook's own lattice-decoded per-stroke spans (`stroke_
points`, the SAME `[(points, name[, fine_child[, substroke_points]]), ...]` draw-order sequence
`abs_rerank`'s own decode cache already threads through everywhere else in this module) become
ONE MORE `ParseHyp` staged alongside the theta-grid hypotheses (55/70/85) -- LEARN finally
contributes structure to the marginal verdict instead of being bypassed by a fixed re-
segmentation. `_earned_parts_from_stroke_points` mirrors `canonical_parse.canonical_parts`'s OWN
joint-normalize (one centroid + RMS over every sub-point, so stroke LAYOUT is preserved) +
per-part arc-length resample exactly -- the only difference is WHERE the parts come from (the
lattice's own on-path spans, not a fresh corner-split) -- so the earned ParseHyp's `Stroke`
children are structurally identical in shape to every theta hypothesis's own, and `recognition_
graph.predict_smooth_marginal_sc_term`'s SAME held Term marginalises over it with zero changes.
Default (`earned_stroke_points=None`) reproduces the pre-existing theta-grid-only staging BYTE-
IDENTICALLY -- purely additive.

LEVER 2 -- TOKEN-REFIT AbS (`program_refit_verdict`/`program_refit_rerank`, the biggest remaining
BPL-ism): a GENERAL directional program-explains-observation faculty that knows NOTHING of
characters -- `program_parts`/`observed_path_parts` are bare Python lists of point-set arrays
("parts"), never graph nodes. THE ASYMMETRY (documented explicitly, per the design): RUN 17/18's
`marginal_part_error_term`/`_parse_pair_dist` is SYMMETRIC -- it sums BOTH directions (query's own
parts explained-by-candidate PLUS candidate's own parts explained-by-query), so an observed part
with no counterpart ANYWHERE in the candidate (extra/noisy query ink) is charged to EVERY
candidate via the query-side term, regardless of how well that candidate explains the ink it DOES
cover. `program_refit_verdict` marginalises in ONE DIRECTION ONLY -- the program's own parts
explained BY the observation -- treating the EXEMPLAR's canonical parts as a GENERATIVE PROGRAM
fitted TO the query's ink (never the reverse): a program that is a genuine SUBSET of a noisier
observation still explains its own part perfectly and pays nothing for the observation's extra,
unmatched ink, where a symmetric distance would. The per-part base cost is `TpsDeformDist`
(design: "TpsDeformDist already returns fit residual + bending energy = a deformation prior") --
itself directional in its OWN Rust implementation (warps `a` toward `b`'s nearest points;
`TpsDeformDist(a, b) != TpsDeformDist(b, a)` in general) -- used here as `TpsDeformDist(program_
part, observed_part)`, fitting the program's part TO the observation. The part CORRESPONDENCE
(which observed part explains a given program part) is MARGINALISED via the SAME soft-min (log-
sum-exp, temperature `beta_corr`) `recognition_graph._soft_directed_part_dist` already establishes
for one direction of ITS OWN symmetric sum -- composed here over Python-managed `Lit` point-set
lists (no graph Neighbours, since this function never touches a graph at all) rather than graph
`Sum`/`Nbrs`. `beta_corr=2.0` (`DEFAULT_REFIT_BETA`) reuses `recognition_graph`'s OWN existing
default (`marginal_part_error_term`'s `beta`, `_soft_directed_part_dist`'s `beta_corr`) verbatim
-- no new weight, no tuning. `program_refit_rerank` is the multi-candidate verdict: ONE held
`Argmin` (`_argmin_pairs_term`, the SAME idiom every other rerank in this module already uses)
over the per-candidate `program_refit_verdict` scores.

RUN 25 -- THE NUMBER (scratchpad/HANDWRITING_DESIGN.md's "RUN 25" scope): three levers off RUN
17b's own real-character 20-way one-shot 80.5% [76.3, 84.1] @ n=400 (2c669fd1), the SAME
`stage_parse_char`/`parse_marginal_verdict` stack, all measured behind that control.

C1 -- FINER THETA GRID (`DEFAULT_PARSE_THETAS_FINE`, no new function): `predict_smooth_
marginal_sc_term` already marginalises over EVERY staged `ParseHyp` regardless of `theta`, so
widening the theta grid from (55, 70, 85) to (40, 50, 60, 70, 80, 90) is a PURE hypothesis-count
increase at the SAME `stage_parse_char(thetas=...)` call site -- no new weight, no new Term.

C2 -- VERDICT FUSION AT DIFFERENT GRAINS (`fused_grain_verdict_term`/`fused_grain_rerank`, new):
never tested before -- RUN 16/17 tried the whole-figure SC+TPS verdict as an ALTERNATIVE to the
parse-marginal verdict, never FUSED with it. `fused_grain_verdict_term` sums the part-marginal
error (`parse_marginal_pair_error_term`, needs graph `s`/`w`) with the whole-figure SC+TPS error
(`sctps_verdict_term`, bare point-sets) at unit weight inside ONE held `Plus` -- `joined_refit_
marginal_term`'s own graph/non-graph fusion precedent, a different second term. If raw staging
data shows the two error scales mismatched, `fused_grain_rerank(normalize=True)` divides each
sub-term by its OWN per-episode candidate-mean (mechanical scale alignment, a plain Python
`sum(...)/len(...)` over an ALREADY-fully-computed list of floats -- the same class of
bookkeeping `run17_close._grid_winner`'s own weighted combination of already-Term-computed raw
distances already establishes as legal); which variant (raw sum vs normalized) is ADOPTED is a
PRE-REGISTERED choice made from real staged numbers before any accuracy is computed, documented
in the run script's own header, never chosen by outcome.

C3 -- EXEMPLAR-NUISANCE MARGINALIZATION (`stage_parse_char`'s new `nuisance_variant_parts`
param, K=4 pre-registered): for each candidate, K `glyph_motor_world.write_with_hand`-perturbed
re-draws of that candidate's OWN raw strokes (re-split back to per-stroke boundaries, mirroring
`symbol_motor_world.write_hand_instance`'s own concatenate/vary/re-split idiom) become K
ADDITIONAL `ParseHyp` branches (sentinel `theta=DEFAULT_PARSE_NUISANCE_THETA`) under the SAME
candidate Concept node, joining the theta-grid hypotheses in the SAME marginalization -- testing
whether a candidate's own token variability (BPL's re-drawn stroke detail) is partially
SIMULABLE without any learned model. `nuisance_variant_parts=None` (default) reproduces the
pre-existing staging byte-identically -- purely additive."""
from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np

from domains import character_compose as cc
from domains import ink_decode as ink
from domains.glyph_motor_world import _resample_arclen
from domains.stroke_codebook import DEFAULT_SEGMENTS, _find_stroke_node, _native, _quantize, _sub

DEFAULT_TOPK = 5
DEFAULT_RENDER_N_POINTS = 24


# --------------------------------------------------------------------------- #
#  LIVENESS PROBE — mirrors stroke_codebook._stroke_quantize_live()'s pattern exactly.
# --------------------------------------------------------------------------- #
def _stroke_render_live(native) -> bool:
    """Cheap probe: is the Rust `StrokeRender` Term callable yet? A minimal, structurally
    valid `seg`-only signature + the smallest option set this module actually needs
    (`n_points`, `apply_pose`, `field`) — mirrors `stroke_codebook._stroke_quantize_live`'s
    own "probe the SPECIFIC surface this module needs, not just the Term's bare existence"
    discipline."""
    try:
        native.evaluate(
            {"type": "StrokeRender",
             "signature": {"type": "Lit", "value": [["seg", 0, 0, 4, 0]]},
             "n_points": 8, "apply_pose": False, "field": "points"},
            {})
        return True
    except ValueError as e:
        msg = str(e)
        if "UnknownTermType" in msg or "unknown field" in msg.lower():
            return False
        raise


# --------------------------------------------------------------------------- #
#  PROPOSE — the existing strict naive coverage (UNCHANGED, the control-reproducing
#  metric), repeated K times to build a SHORTLIST. Duplicated locally per this codebase's
#  own established convention of a small, pure, call-site-local Term builder rather than a
#  shared import across scripts/tests/domains (see e.g. scripts/jabberwock_omniglot_
#  dynamic_quantization.py's `_coverage_term`/`_argmax_pairs_term` and tests/test_character_
#  composition_migrated.py's identical copy).
# --------------------------------------------------------------------------- #
def _coverage_term(query_sig, exemplar_sig) -> dict:
    return {"type": "Sum", "source": {"type": "Lit", "value": query_sig}, "var_name": "n",
            "value": {"type": "IfThenElse",
                      "cond": {"type": "In", "member": {"type": "Var", "name": "n"},
                               "container": {"type": "Lit", "value": exemplar_sig}},
                      "then": {"type": "Lit", "value": 1.0}, "other": {"type": "Lit", "value": 0.0}}}


def _argmax_pairs_term(pairs) -> dict:
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _argmin_pairs_term(pairs) -> dict:
    return {"type": "Argmin", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


# --------------------------------------------------------------------------- #
#  RUN 32 -- SUB-BIN RESIDUAL, proposal-side lever (`domains/adaptive_bins.py`'s "the
#  remainder goes to more detail," applied to the STRUCTURAL PROPOSAL distance rather than
#  discarded): `residual_aware_distance` is a HELD `Sum`/`Minus`/`Times` Term over paired
#  per-segment `[turn_residual, len_residual]` arrays (`StrokeQuantize`'s own `emit_residual`
#  output, `domains/ink_decode.py`'s `_span_signature`) — a sum-of-squared-differences, never
#  raw Python float arithmetic doing the comparison (the SAME "no Python argmin/argmax/score-
#  ranking" discipline this module's own audit test, `test_abs_read_no_python_decisions`,
#  checks for source-level; combining this Term's own SCALAR result with a coverage score
#  below is plain arithmetic on two already-computed numbers, not a ranking decision — the
#  ranking itself stays the held `Argmax` in `propose_top_k`, unchanged).
# --------------------------------------------------------------------------- #
def _residual_distance_term(query_residuals: list, exemplar_residuals: list) -> dict:
    n = min(len(query_residuals), len(exemplar_residuals))
    pairs = [[float(query_residuals[i][0]), float(query_residuals[i][1]),
              float(exemplar_residuals[i][0]), float(exemplar_residuals[i][1])]
             for i in range(n)]
    if not pairs:
        return {"type": "Lit", "value": 0.0}

    def _idx(k):
        return {"type": "IndexAt", "seq": {"type": "Var", "name": "p"},
                "index": {"type": "Lit", "value": k}}
    d_turn = {"type": "Minus", "a": _idx(0), "b": _idx(2)}
    d_len = {"type": "Minus", "a": _idx(1), "b": _idx(3)}
    sq = {"type": "Plus", "items": [{"type": "Times", "items": [d_turn, d_turn]},
                                    {"type": "Times", "items": [d_len, d_len]}]}
    return {"type": "Sum", "source": {"type": "Lit", "value": pairs}, "var_name": "p", "value": sq}


def residual_aware_distance(native, query_residuals: list, exemplar_residuals: list) -> float:
    """ONE held-Term evaluate — the sum-of-squared per-segment `(turn, len)` residual offset
    between a query span sequence and a candidate exemplar's own stored residuals. `0.0` for
    an empty pairing (an honest no-signal default, never a fabricated distance)."""
    return float(native.evaluate(
        _residual_distance_term(query_residuals, exemplar_residuals), {}) or 0.0)


# --------------------------------------------------------------------------- #
#  PROPOSAL RECALL / VARIABLE-APERTURE DWELL (scratchpad/HANDWRITING_DESIGN.md's
#  "PROPOSAL RECALL / VARIABLE-APERTURE DWELL" section, the 42855d5f residual + the radar
#  frame's first falsifiable instance): "dwell scheduling — spend renders where proposal
#  AMBIGUITY is high; ties = widen the beam, clear margin = narrow." The shortlist-SIZE
#  decision is itself a held Term (never a Python score branch): held `MaxOver` reads the
#  top proposal score (the ambiguity signal), held `FilterList` (order/duplicate-preserving
#  twin of `Filter`) keeps every candidate within margin `delta` (DATA) of it. `delta=0`
#  passes through EXACT ties only — the degenerate case that recovers a single-winner
#  Argmax's own shortlist when there is no tie at all.
# --------------------------------------------------------------------------- #
def _max_score_term(pairs) -> dict:
    """HELD `MaxOver`: the TOP proposal score among a Python-assembled `(score, id)` list —
    read-off of an already-computed coverage score, never a Python max()."""
    return {"type": "MaxOver", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}},
            "default": {"type": "Lit", "value": 0.0}}


def _within_margin_term(pairs, top_score: float, delta: float) -> dict:
    """HELD `FilterList`: every `(score, id)` pair whose score is `>= top_score - delta` —
    the shortlist-SIZE decision, `delta` passed as DATA. `FilterList` (not `Filter`) is used
    deliberately: it preserves source order/duplicates (a `Tuple`, not a `Set`) so the
    returned shortlist is deterministic candidate-index order, never re-ranked by this step
    (ranking is `abs_rerank`'s held `Argmin` over render-compare scores, downstream)."""
    return {"type": "FilterList", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "predicate": {"type": "Gte",
                          "a": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                                "index": {"type": "Lit", "value": 0}},
                          "b": {"type": "Lit", "value": float(top_score) - float(delta)}}}


def propose_variable_k(native, query_sig: list, exemplar_sigs: list, delta: float) -> list[int]:
    """VARIABLE-K DWELL SCHEDULER: the shortlist is every candidate whose coverage score is
    within margin `delta` (DATA) of the TOP proposal score — held `MaxOver` reads the
    ambiguity signal, held `FilterList` makes the shortlist-SIZE decision (Count/Filter over
    the proposal pairs, per the design: "no Python score branching — the audits scan").
    The per-candidate coverage evaluate calls below are mechanical DATA COLLECTION (ONE
    `_coverage_term` evaluate per candidate — the SAME metric `propose_top_k`/the naive-
    coverage control already use), never a ranking decision; the decision (which candidates
    pass the margin) is the held Terms above. Returns candidate indices in their ORIGINAL
    order (never re-sorted by score — `FilterList`'s own "ordered twin of Filter" contract);
    an empty `exemplar_sigs` returns `[]`, never a crash."""
    if not exemplar_sigs:
        return []
    pairs = [(float(native.evaluate(_coverage_term(query_sig, exemplar_sigs[i]), {}) or 0.0), i)
             for i in range(len(exemplar_sigs))]
    top_score = float(native.evaluate(_max_score_term(pairs), {}))
    filtered = native.evaluate(_within_margin_term(pairs, top_score, delta), {}) or ()
    return [int(p[1]) for p in filtered]


def _rank_term(pairs, true_score: float) -> dict:
    """HELD `Count(FilterList(...))`: how many OTHER candidates strictly outscore
    `true_score` — the ingredient of a 1-based RANK read-off (`proposal_rank`), never itself
    a ranking decision (ties share a rank rather than being broken by a Python sort)."""
    return {"type": "Count", "source": {
        "type": "FilterList", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
        "predicate": {"type": "Gt",
                      "a": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                            "index": {"type": "Lit", "value": 0}},
                      "b": {"type": "Lit", "value": float(true_score)}}}}


def proposal_rank(native, query_sig: list, exemplar_sigs: list, true_idx: int) -> Optional[int]:
    """The 1-based RANK of the TRUE exemplar (`true_idx`) in the SAME strict naive-coverage
    proposal ordering `propose_top_k`/`propose_variable_k` use — held `Count(FilterList(...))`
    counts how many OTHER candidates strictly outscore it (ties share a rank, never broken by
    a Python sort/argmax). Used ONLY for the RECALL-TAIL report (design: "where the true
    exemplar ranks in proposals when OUTSIDE the top-5") — a read-off of an ALREADY-computed
    coverage score, never itself a classification decision. Returns `None` for an
    out-of-range `true_idx` (an honest non-crash, never a fabricated rank)."""
    if not (0 <= true_idx < len(exemplar_sigs)):
        return None
    pairs = [(float(native.evaluate(_coverage_term(query_sig, exemplar_sigs[i]), {}) or 0.0), i)
             for i in range(len(exemplar_sigs))]
    true_score = pairs[true_idx][0]
    n_better = int(native.evaluate(_rank_term(pairs, true_score), {}) or 0)
    return n_better + 1


DEFAULT_RESIDUAL_WEIGHT = 1e-6
"""RUN 32 -- pre-registered: small enough that the residual term only ever breaks a
COVERAGE tie (coverage counts whole relations, so its own scale is >= 1.0 per differing
relation; a squared-residual sum of a handful of small within-bin offsets sits several
orders of magnitude below that), never overturns a genuine coverage-count winner."""


def propose_top_k(native, query_sig: list, exemplar_sigs: list,
                   k: int = DEFAULT_TOPK,
                   query_residuals: Optional[list] = None,
                   exemplar_residuals: Optional[list] = None,
                   residual_weight: float = DEFAULT_RESIDUAL_WEIGHT) -> list[int]:
    """PROPOSE: the K best exemplar indices by the EXISTING strict naive coverage (the
    33.8%-earning `_coverage_term`, byte-identical to the script's own logged control) —
    repeated held `Argmax` over a Python-managed "remaining" index list. `k` is a LOGGED
    CONSTANT (design: "K~3-5"), never tuned per-query; the loop stops early if fewer than
    `k` exemplars exist or a round returns no winner (an honest, non-crashing shortlist,
    never padded).

    RUN 32 -- SUB-BIN RESIDUAL (`query_residuals`/`exemplar_residuals`, both optional,
    default `None` — every pre-existing caller gets BYTE-IDENTICAL behaviour, since the
    combined-score arithmetic below degenerates to the raw coverage float when either is
    absent): `exemplar_residuals[i]` is exemplar `i`'s own per-segment `[turn, len]` residual
    list (`StrokeQuantize`'s `emit_residual` output, threaded through
    `domains/character_compose.py`'s composition — NOT wired as of this commit, callers pass
    `None` until that wiring lands). When both are given, each candidate's ranking value is
    `coverage_score - residual_weight * residual_aware_distance(...)` — the coverage count
    still dominates (see `DEFAULT_RESIDUAL_WEIGHT`'s own doc), the residual term only spreads
    apart candidates that TIE on coverage. The ranking DECISION stays the held `Argmax`
    (`_argmax_pairs_term`) — combining two already-computed scalars is arithmetic, not a
    Python ranking (see `_residual_distance_term`'s own doc for the audit discipline)."""
    use_residual = query_residuals is not None and exemplar_residuals is not None
    remaining = list(range(len(exemplar_sigs)))
    order: list[int] = []
    for _ in range(min(k, len(exemplar_sigs))):
        pairs = []
        for i in remaining:
            cov = float(native.evaluate(_coverage_term(query_sig, exemplar_sigs[i]), {}) or 0.0)
            if use_residual and i < len(exemplar_residuals):
                dist = residual_aware_distance(native, query_residuals, exemplar_residuals[i])
                cov = cov - residual_weight * dist
            pairs.append((cov, i))
        winner = native.evaluate(_argmax_pairs_term(pairs), {})
        if winner is None:
            break
        idx = int(winner[1])
        order.append(idx)
        remaining.remove(idx)
    return order


# --------------------------------------------------------------------------- #
#  FRAME GEOMETRY — reuses character_compose's OWN `_character_frame`/`_frame_bbox`
#  (byte-identical inputs -> byte-identical outputs) so a query's/exemplar's observed ink,
#  read here independently of `compose_character_signature`'s own internal computation,
#  lands in the EXACT SAME normalized frame the composed signature's "rel"/"cpose" bins
#  were already quantized against — no new geometry, no re-derivation.
# --------------------------------------------------------------------------- #
def _stroke_frame_slices(stroke_points: list) -> tuple:
    """`stroke_points`: `[(points, identity_name[, fine_child]), ...]` draw order (the SAME
    shape `character_compose.compose_character_signature` itself accepts). Returns
    `(bbox, {k: frame_slice_points})` — mechanical geometry only, no decision."""
    norm = [np.asarray(item[0], dtype=float).reshape(-1, 2) for item in stroke_points]
    if not norm:
        return (0.0, 0.0, 1.0, 1.0), {}
    all_pts = np.concatenate(norm, axis=0)
    if all_pts.shape[0] < 2:
        return (0.0, 0.0, 1.0, 1.0), {}
    frame = cc._character_frame(all_pts)
    bbox = cc._frame_bbox(frame)
    slices: dict[int, list] = {}
    offset = 0
    for k, pts in enumerate(norm):
        n = pts.shape[0]
        seg = frame[offset:offset + n]
        if seg.shape[0] >= 2:
            slices[k] = seg.tolist()
        offset += n
    return bbox, slices


def _strokeq_map(sig: list) -> dict:
    return {r[1]: r[2] for r in sig if r and r[0] == "strokeq"}


def _rel_map(sig: list) -> dict:
    return {r[1]: tuple(r[2:6]) for r in sig if r and r[0] == "rel"}


# --------------------------------------------------------------------------- #
#  RENDER-COMPARE — one held comparison Term per candidate.
# --------------------------------------------------------------------------- #
def _candidate_seg(sub, name: str) -> Optional[list]:
    """The candidate stroke quantum's own stored FINE `seg` relations (the canonical-pose
    codebook entry, `stroke_codebook.grow_stroke_quantum`'s convention) — mechanical lookup
    + the SAME `ink_decode._fine_seg_relations` projection already applied to a LIVE decode
    result, here applied to a HELD codebook entry's own stored signature instead."""
    node = _find_stroke_node(sub, name)
    if node is None:
        return None
    try:
        sig = json.loads(sub.node(node)["attrs"].get("signature") or "[]")
    except (TypeError, ValueError):
        return None
    seg = ink._fine_seg_relations(sig)
    return seg or None


def _exemplar_true_seg(native, points, *, segments: int, turn_bins: int, len_bins: int,
                        grid: int, scale_bins: int) -> Optional[list]:
    """LEVER A — EXEMPLAR-TRUE RENDERING (scratchpad/HANDWRITING_DESIGN.md's "INSTANCE-
    CONDITIONED QUANTA" section): the candidate's OWN per-stroke `seg` relations, quantized
    DIRECTLY from its own already-decoded raw points (`candidate_stroke_points[ci][k][0]`,
    already in the decode cache — no re-decode) via the SAME held `StrokeQuantize` Term
    (`canonical_pose=True`, the codebook-authoring convention `stroke_codebook.grow_stroke_
    quantum` itself uses) — NOT the codebook's stored GLOBAL quantum seg (`_candidate_seg`,
    which approximates every stroke recognized as the same quantum with ONE shared canonical
    shape, discarding this exemplar's own actual geometry, "the information bound" the design
    names). Returns `None` (never a fabricated seg) for degenerate (<2 points) input — the
    caller falls through to the whole-ink `PointSetDist` comparison, the SAME honest-miss
    discipline `_candidate_seg` already establishes."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return None
    q = _quantize(native, pts.tolist(), segments=segments, turn_bins=turn_bins,
                  len_bins=len_bins, grid=grid, scale_bins=scale_bins, canonical_pose=True)
    seg = ink._fine_seg_relations(q["signature"])
    return seg or None


def _render_goal(seg: list, pose_bins: tuple) -> list:
    """Splice the QUERY's own observed pose bins onto the CANDIDATE's stored `seg` — the
    RENDER-side twin of `ink_decode._pose_read_goal`'s DECODE-side splice (there: the
    observed pose spliced onto the chosen PARENT's own seg, to read a delta OFF a decode;
    here the same substitution feeds a RENDER instead, "draw-order correspondence" — stroke
    k's OWN decoded pose, applied to stroke k's PROPOSED identity)."""
    x_q, y_q, o_q, s_q = pose_bins
    return list(seg) + [["pose_x", x_q], ["pose_y", y_q], ["pose_o", o_q], ["pose_s", s_q]]


def _render_term(signature: list, *, n_points: int, bounds, turn_bins: int, len_bins: int,
                  grid: int, scale_bins: int) -> dict:
    """A `StrokeRender` Term (not yet evaluated — built for nesting straight into a
    comparison Term, ONE evaluate per candidate rather than one evaluate per stroke).
    `field: "points"` (the SAME field-selection convention `StrokeQuantize`/`ShapeDecode`
    already support) returns the polyline directly, the shape `DtwTo`/`PointSetDist`
    expect, no Dict-unwrapping in Python."""
    return {"type": "StrokeRender", "signature": {"type": "Lit", "value": signature},
            "n_points": n_points, "apply_pose": True,
            "turn_bins": turn_bins, "len_bins": len_bins, "grid": grid,
            "scale_bins": scale_bins, "field": "points",
            "bounds": {"type": "Lit", "value": [float(v) for v in bounds]}}


def _dtw_term(render_term: dict, observed_points: list) -> dict:
    return {"type": "DtwTo", "a": render_term, "b": {"type": "Lit", "value": observed_points}}


# --------------------------------------------------------------------------- #
#  BRANCH B CONTINUOUS -- JUNCTION-BLENDED RENDERING (see this module's own top-of-file
#  docstring, "BRANCH B CONTINUOUS" section, for the full rationale).
# --------------------------------------------------------------------------- #
DEFAULT_JUNCTION_FRAC = 0.15


def _junction_blend(rendered_by_k: dict, j_frac: float) -> dict:
    """Pure mechanical geometry (NOT a decision): for every pair of DRAW-ORDER-CONSECUTIVE
    keys `(a, b)` in `rendered_by_k` (sorted key order -- stroke index k), warp stroke `a`'s
    TRAILING `j_frac` arc-length-index fraction of points, and stroke `b`'s LEADING `j_frac`
    fraction, LINEARLY toward their shared junction target -- the midpoint of stroke `a`'s own
    last point and stroke `b`'s own first point (the two strokes' OWN independently-rendered
    endpoints, never the query's). The taper is LINEAR in point index, reaching full strength
    (the exact joint value) only at the single outermost point of each blended span and
    tapering toward (never quite reaching) zero at its inner edge -- "a bounded deformation ...
    over the last/first J% of arc length," never touching a stroke's interior beyond that span.

    `rendered_by_k`: `{k: [[x, y], ...]}` in draw order (typically a candidate's own freshly
    `StrokeRender`-evaluated per-stroke polylines). Returns a NEW dict (the input is never
    mutated) with the SAME keys and per-key point COUNTS -- only coordinates inside a blended
    span are altered. `j_frac <= 0` returns the ORIGINAL dict object unchanged (an honest,
    byte-identical no-op -- the design's own "flag-gated, off = byte-identical" discipline,
    the SAME contract `character_compose.compose_character_signature`'s `include_rel2`/
    `include_substroke` flags already establish for their own additive features). A stroke
    with fewer than 2 points, or with no draw-order neighbour on a given side, is left
    untouched on that side (an honest non-crash, never a fabricated junction)."""
    if j_frac <= 0:
        return rendered_by_k
    ks = sorted(rendered_by_k)
    out = {k: [list(p) for p in rendered_by_k[k]] for k in ks}
    for a, b in zip(ks, ks[1:]):
        pa, pb = out[a], out[b]
        if len(pa) < 2 or len(pb) < 2:
            continue
        end_a = np.asarray(pa[-1], dtype=float)
        start_b = np.asarray(pb[0], dtype=float)
        joint = (end_a + start_b) / 2.0
        n_a = max(1, int(round(j_frac * len(pa))))
        for i, idx in enumerate(range(len(pa) - n_a, len(pa))):
            w = (i + 1) / n_a                          # tapers up to 1.0 at the LAST point
            pt = np.asarray(pa[idx], dtype=float)
            pa[idx] = ((1.0 - w) * pt + w * joint).tolist()
        n_b = max(1, int(round(j_frac * len(pb))))
        for i, idx in enumerate(range(n_b)):
            w = 1.0 - i / n_b                          # 1.0 at the FIRST point, tapers down
            pt = np.asarray(pb[idx], dtype=float)
            pb[idx] = ((1.0 - w) * pt + w * joint).tolist()
    return out


def abs_render_compare_term(sub, query_sig: list, query_frame_slices: dict, query_bbox,
                             candidate_sig: list, *, n_points: int, turn_bins: int,
                             len_bins: int, grid: int, scale_bins: int,
                             segments: int = DEFAULT_SEGMENTS, exemplar_true: bool = False,
                             candidate_stroke_points: Optional[list] = None,
                             junction_blend: bool = False,
                             junction_frac: float = DEFAULT_JUNCTION_FRAC) -> Optional[dict]:
    """ONE held comparison Term for ONE candidate — mean per-stroke `DtwTo` between the
    CANDIDATE's own stroke quanta rendered at the QUERY's decoded per-stroke poses and the
    QUERY's actual observed ink (draw-order correspondence by stroke index `k`). A single
    nested `Div(Plus([DtwTo(render_k, observed_k), ...]), Lit(n))` — one evaluate call,
    same "ONE held Term per candidate" discipline `character_compose.assignment_coverage_
    term` already established for its own multi-stroke score.

    Returns `None` (never a fabricated Term) when the candidate's stroke COUNT differs from
    the query's own, or a candidate stroke's identity was never held as a stroke quantum —
    both honest structural misses the caller routes to the whole-ink `PointSetDist` fallback
    instead (design: "stroke-count mismatch -> whole-ink PointSetDist comparison").

    LEVER A — EXEMPLAR-TRUE RENDERING (`exemplar_true`, default `False` — every pre-existing
    call site reproduces the byte-identical GLOBAL-quantum render): when `True`,
    `candidate_stroke_points` (the SAME `[(points, identity_name[, fine_child]), ...]` shape
    `abs_rerank` already threads through for the `PointSetDist` fallback) supplies stroke `k`'s
    OWN actual points, quantized fresh via `_exemplar_true_seg` instead of looking up
    `c_strokeq[k]`'s stored global entry — `segments` is only ever consumed on this path.
    Returns `None` (the SAME honest-miss discipline) when `exemplar_true` is requested but the
    candidate's own points are missing/degenerate for a needed stroke index.

    BRANCH B CONTINUOUS (`junction_blend`, `junction_frac`, both default off -- every
    pre-existing call reproduces the BYTE-IDENTICAL single-nested-Term evaluate): when
    `junction_blend=True`, each stroke's `StrokeRender` Term is evaluated INDIVIDUALLY (one
    extra `native.evaluate` per stroke) so `_junction_blend` can warp the resulting per-stroke
    polylines toward draw-order junction continuity BEFORE the comparison -- the blended points
    then feed the SAME `DtwTo`/`Plus`/`Div` Term shape as a `Lit`, never changing the
    comparison Terms or the caller's held-`Argmin` verdict, only WHAT is compared."""
    q_strokeq = _strokeq_map(query_sig)
    q_rel = _rel_map(query_sig)
    c_strokeq = _strokeq_map(candidate_sig)
    if not q_strokeq or set(q_strokeq) != set(c_strokeq):
        return None
    native = _native(sub) if (exemplar_true or junction_blend) else None
    order: list = []
    render_terms: list = []
    for k in sorted(q_strokeq):
        if k not in query_frame_slices or k not in q_rel:
            return None
        if exemplar_true:
            if candidate_stroke_points is None or k >= len(candidate_stroke_points):
                return None
            cand_seg = _exemplar_true_seg(native, candidate_stroke_points[k][0],
                                           segments=segments, turn_bins=turn_bins,
                                           len_bins=len_bins, grid=grid, scale_bins=scale_bins)
        else:
            cand_seg = _candidate_seg(sub, c_strokeq[k])
        if not cand_seg:
            return None
        goal = _render_goal(cand_seg, q_rel[k])
        render_term = _render_term(goal, n_points=n_points, bounds=query_bbox,
                                    turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                                    scale_bins=scale_bins)
        order.append(k)
        render_terms.append(render_term)
    if not render_terms:
        return None

    if not junction_blend:
        # UNCHANGED path -- byte-identical to every pre-existing call (no evaluate here at
        # all; the caller's own single outer evaluate resolves the whole nested Term).
        dtw_terms = [_dtw_term(render_terms[i], query_frame_slices[order[i]])
                     for i in range(len(order))]
    else:
        rendered_by_k = {}
        for i, k in enumerate(order):
            pts = native.evaluate(render_terms[i], {})
            if not pts:
                return None
            rendered_by_k[k] = pts
        blended = _junction_blend(rendered_by_k, junction_frac)
        dtw_terms = [_dtw_term({"type": "Lit", "value": blended[k]}, query_frame_slices[k])
                     for k in order]

    return {"type": "Div", "a": {"type": "Plus", "items": dtw_terms},
            "b": {"type": "Lit", "value": float(len(dtw_terms))}}


def pointset_compare_term(query_frame_slices: dict, candidate_frame_slices: dict) -> dict:
    """Whole-ink fallback (design: stroke-count mismatch): ONE held `PointSetDist` evaluate
    over the two ALREADY-OBSERVED (real, decoded) point clouds, each in its OWN character's
    normalized frame — order/count-INVARIANT by construction (`PointSetDist`'s own Rust
    docstring: "absorbs stroke-order / stroke-count mismatches"), so a genuine drawer
    pen-lift never breaks this comparison structurally. No `StrokeRender` needed for this
    path — the candidate's own REAL recorded ink is compared directly, not re-generated."""
    q_pts = [p for k in sorted(query_frame_slices) for p in query_frame_slices[k]]
    c_pts = [p for k in sorted(candidate_frame_slices) for p in candidate_frame_slices[k]]
    return {"type": "PointSetDist", "a": {"type": "Lit", "value": q_pts},
            "b": {"type": "Lit", "value": c_pts}}


# --------------------------------------------------------------------------- #
#  THE VERDICT — propose top-K, render-compare each, held Argmin.
# --------------------------------------------------------------------------- #
def abs_rerank(agent, query_sig: list, query_stroke_points: list, candidate_sigs: list,
               candidate_stroke_points: list, *, k: int = DEFAULT_TOPK,
               top_k: Optional[list[int]] = None,
               n_points: int = DEFAULT_RENDER_N_POINTS, turn_bins: int, len_bins: int,
               grid: int, scale_bins: int, segments: int = DEFAULT_SEGMENTS,
               exemplar_true: bool = False, junction_blend: bool = False,
               junction_frac: float = DEFAULT_JUNCTION_FRAC) -> dict[str, Any]:
    """THE re-rank verdict (design's S item): PROPOSE top-K by the existing strict coverage
    (`propose_top_k`, byte-identical to the control), then for each of the K proposed
    candidates build ONE held comparison Term (render-compare when stroke counts match,
    whole-ink `PointSetDist` otherwise) and pick the FINAL winner via ONE held `Argmin` over
    the K candidate scores — never a Python min/sort. `coverage_pick` (the first of the
    top-K, i.e. what the OLD single-`Argmax` control alone would have chosen) is returned
    alongside for the logged control the design asks for, plus `top_k` itself so a caller
    can report coverage@K (was the TRUE exemplar even in the shortlist — the proposal
    recall bound on what re-ranking can possibly achieve).

    `top_k` (PROPOSAL RECALL / VARIABLE-APERTURE DWELL, new): when given, OVERRIDES the
    internal fixed-K `propose_top_k` call with an ALREADY-DECIDED shortlist — e.g.
    `propose_variable_k`'s held-margin filter, or `list(range(len(candidate_sigs)))` for a
    "full dwell" arm (every candidate re-ranked, no proposal filter at all). Every other
    step (render-compare per candidate, held Argmin verdict) is UNCHANGED; `k` is then
    ignored for shortlist construction (kept only as the logged nominal-K field). Omitting
    `top_k` (the default, `None`) reproduces the PRE-EXISTING fixed-K behaviour byte-
    identically — additivity discipline, the K=5 control arm's own code path is untouched.

    `agent` accepts either a bare `Substrate` or a `WorldAdapter`-like wrapper (mirrors
    `stroke_codebook._sub`/`_native`'s own dispatch).

    `segments`/`exemplar_true` (INSTANCE-CONDITIONED QUANTA, LEVER A, both default to the
    byte-identical pre-existing behaviour): forwarded to `abs_render_compare_term` — see that
    function's own docstring for the exemplar-true-vs-global-quantum distinction.

    `junction_blend`/`junction_frac` (BRANCH B CONTINUOUS, both default to the byte-identical
    pre-existing behaviour): forwarded straight to `abs_render_compare_term` — see that
    function's own docstring / this module's top-of-file docstring for the full rationale."""
    sub = _sub(agent)
    native = _native(agent)
    if top_k is None:
        top_k = propose_top_k(native, query_sig, candidate_sigs, k)
    coverage_pick = top_k[0] if top_k else None
    q_bbox, q_slices = _stroke_frame_slices(query_stroke_points)

    pairs = []
    for ci in top_k:
        term = abs_render_compare_term(
            sub, query_sig, q_slices, q_bbox, candidate_sigs[ci], n_points=n_points,
            turn_bins=turn_bins, len_bins=len_bins, grid=grid, scale_bins=scale_bins,
            segments=segments, exemplar_true=exemplar_true,
            candidate_stroke_points=candidate_stroke_points[ci] if exemplar_true else None,
            junction_blend=junction_blend, junction_frac=junction_frac)
        if term is None:
            _, c_slices = _stroke_frame_slices(candidate_stroke_points[ci])
            term = pointset_compare_term(q_slices, c_slices)
        score = float(native.evaluate(term, {}) or 0.0)
        pairs.append((score, ci))

    winner = coverage_pick
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])

    return {"winner": winner, "coverage_pick": coverage_pick, "top_k": top_k, "k": k,
            "shortlist_size": len(top_k), "scores": pairs}


# --------------------------------------------------------------------------- #
#  TARGETED WIDEN + SECOND MODALITY (scratchpad/HANDWRITING_DESIGN.md's section of the same
#  name, the 6db362d1 residual) — see this module's own top-of-file docstring for the full
#  rationale. LEVER 1 (`widen_decision`/`abs_rerank_targeted`'s `use_widen`) and LEVER 2
#  (`propose_appearance_top_m`/`use_appearance`) are independent flags on ONE combinator.
# --------------------------------------------------------------------------- #
DEFAULT_WIDEN_TO = 10
DEFAULT_APPEARANCE_M = 3


def _min_score_term(pairs) -> dict:
    """HELD `MinOver`: the LOWEST (best) render-compare distance among an already-computed
    `(score, id)` list — the lower-is-better twin of `_max_score_term`."""
    return {"type": "MinOver", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}},
            "default": {"type": "Lit", "value": 0.0}}


def _widen_decision_term(best_score: float, runner_up_score: Optional[float],
                          margin_threshold: float, fit_threshold: float) -> dict:
    """HELD `Or(Lt(Minus(runner_up, best), margin_threshold), Gt(best, fit_threshold))` — the
    SECOND-STAGE ambiguity signal (design: "the widen decision a held Term over the render
    scores"). `runner_up_score=None` is a STRUCTURAL fact (the shortlist had fewer than 2
    candidates to compare — never itself a score value), so the margin clause is held at a
    literal `Lit(False)` in that case: only the ABSOLUTE fit clause can widen a singleton
    shortlist, never a fabricated runner-up comparison."""
    margin_clause = (
        {"type": "Lt",
         "a": {"type": "Minus", "a": {"type": "Lit", "value": float(runner_up_score)},
               "b": {"type": "Lit", "value": float(best_score)}},
         "b": {"type": "Lit", "value": float(margin_threshold)}}
        if runner_up_score is not None else {"type": "Lit", "value": False})
    fit_clause = {"type": "Gt", "a": {"type": "Lit", "value": float(best_score)},
                  "b": {"type": "Lit", "value": float(fit_threshold)}}
    return {"type": "Or", "items": [margin_clause, fit_clause]}


def widen_decision(native, pairs: list, margin_threshold: float, fit_threshold: float) -> bool:
    """THE widen decision (LEVER 1): `pairs` is a re-rank result's own `(render_score,
    candidate_index)` list (lower-is-better). Reads the BEST score (held `MinOver`) and the
    winning candidate's id (held `Argmin` — the SAME idiom `abs_rerank`'s own verdict already
    uses) to exclude it from the runner-up search — bookkeeping, not a ranking, mirrors
    `propose_top_k`'s own "removing an already-decided winner" idiom — then the RUNNER-UP
    score (held `MinOver` over what's left, or `None` if nothing is left). The actual yes/no
    widen verdict is ONE held `Or` evaluate (`_widen_decision_term`) over those two
    already-computed numbers — never a Python `if score > threshold`. Returns `False` (never
    widens) for an empty `pairs`."""
    if not pairs:
        return False
    best_score = float(native.evaluate(_min_score_term(pairs), {}))
    winner = native.evaluate(_argmin_pairs_term(pairs), {})
    winner_id = winner[1] if winner is not None else None
    remaining = [p for p in pairs if p[1] != winner_id]
    runner_up_score = float(native.evaluate(_min_score_term(remaining), {})) if remaining else None
    return bool(native.evaluate(
        _widen_decision_term(best_score, runner_up_score, margin_threshold, fit_threshold), {}))


def propose_appearance_top_m(native, query_frame_slices: dict,
                              candidate_frame_slices_list: list,
                              m: int = DEFAULT_APPEARANCE_M) -> list[int]:
    """LEVER 2 — SECOND PROPOSAL MODALITY: appearance proposals via held `PointSetDist`
    between the query's OWN observed ink (`query_frame_slices`, from the decode cache — no
    rendering, no new Rust) and each exemplar's own STORED observed ink
    (`candidate_frame_slices_list[i]`, the SAME `_stroke_frame_slices` projection applied to
    the exemplar's own cached `stroke_points`). Top-M via repeated held `Argmin` over a
    Python-managed "remaining" index list — `propose_top_k`'s OWN single-winner idiom, just
    `Argmin` (appearance distance, lower-is-better) instead of `Argmax` (coverage,
    higher-is-better). Returns candidate indices in best-appearance-first order — this
    ordering is never itself read as a rank by any caller, only the SET of returned indices is
    used (the union with the structural shortlist, `abs_rerank_targeted`'s `shortlist0`).
    Returns `[]` for an empty candidate list, never a crash."""
    n = len(candidate_frame_slices_list)
    if n == 0:
        return []
    remaining = list(range(n))
    order: list[int] = []
    for _ in range(min(m, n)):
        pairs = [(float(native.evaluate(
                      pointset_compare_term(query_frame_slices, candidate_frame_slices_list[i]),
                      {}) or 0.0), i)
                 for i in remaining]
        winner = native.evaluate(_argmin_pairs_term(pairs), {})
        if winner is None:
            break
        idx = int(winner[1])
        order.append(idx)
        remaining.remove(idx)
    return order


# --------------------------------------------------------------------------- #
#  INSTANCE-CONDITIONED QUANTA (scratchpad/HANDWRITING_DESIGN.md's section of the same name,
#  the a6c7740f endgame clause) — LEVER B, the instance-codebook query decode. See this
#  module's own top-of-file docstring for the full rationale. EPISODE-SCOPED: every function
#  below either builds or consumes a FRESH, throwaway `substrate_rs.Substrate()` local to ONE
#  caller — never the agent's own held graph, never persisted, no edge ever created between
#  the two graphs. "Nothing persists across episodes, and the LEARN codebook is untouched."
# --------------------------------------------------------------------------- #
INSTANCE_PREFIX = "inst"


def _instance_name(ci: int, k: int) -> str:
    return f"{INSTANCE_PREFIX}_{ci}_{k}"


def build_instance_codebook(candidate_stroke_points: list, *, segments: int, turn_bins: int,
                             len_bins: int, grid: int, scale_bins: int):
    """LEVER B, step 1: a FRESH `substrate_rs.Substrate()` — never the agent's own held
    substrate — carrying ONE `ShapeSignature{kind:"stroke"}` entry per EXEMPLAR STROKE
    (`_instance_name(ci, k)`), quantized DIRECTLY from that exemplar's own already-decoded raw
    points via the SAME held `StrokeQuantize` (`canonical_pose=True`) `_exemplar_true_seg`
    (LEVER A) already established — no re-decode, no Python geometry beyond one
    `StrokeQuantize` evaluate per exemplar stroke, no rule engine run on the scratch substrate
    at all (`add_node` only — a plain graph literal, not a live agent). The scratch substrate
    is a local Python object with no edge into the agent's own held graph: it is garbage-
    collected the instant the caller's episode finishes, so nothing can leak into the next
    episode or into the LEARN codebook — the structural guarantee the design's own "no
    cross-episode leakage" gate checks for.

    Returns `(scratch_substrate, names)` — `names` is `{(ci, k): name}`, the caller's own
    lookup for a candidate's trivial SELF-identity (a stroke always instance-matches itself by
    construction — no decode needed to establish that)."""
    import substrate_rs as srs
    scratch = srs.Substrate()
    native = scratch._inner
    names: dict[tuple[int, int], str] = {}
    for ci, stroke_points in enumerate(candidate_stroke_points):
        for k, item in enumerate(stroke_points):
            pts = np.asarray(item[0], dtype=float)
            if pts.ndim != 2 or pts.shape[0] < 2:
                continue
            q = _quantize(native, pts.tolist(), segments=segments, turn_bins=turn_bins,
                          len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                          canonical_pose=True)
            name = _instance_name(ci, k)
            scratch.add_node("ShapeSignature", {
                "name": name, "kind": "stroke",
                "signature": json.dumps([list(r) for r in q["signature"]])})
            names[(ci, k)] = name
    return scratch, names


def _instance_decode_term(native, span_sig) -> tuple[int, Optional[str]]:
    """ONE held `ShapeDecode` evaluate against the SCRATCH instance codebook — the SAME Occam
    `beam=1/max_steps=1/cand_k=1` pattern `ink_decode._score_span` already established.
    `covered_by` is only meaningful on a FULL invariant match (the same discipline
    `_score_span`'s own docstring names)."""
    goal = {"type": "Lit", "value": span_sig}
    base = {"goal": goal, "beam": 1, "max_steps": 1, "cand_k": 1, "wild_objects": False,
            "codebook_type": "ShapeSignature", "type": "ShapeDecode"}
    count = native.evaluate({**base, "field": "covered_count"}, {})
    name = native.evaluate({**base, "field": "covered_by"}, {})
    return int(count or 0), name


def instance_decode_query(scratch_native, query_stroke_points: list, *, segments: int,
                           turn_bins: int, len_bins: int, grid: int,
                           scale_bins: int) -> list[list]:
    """LEVER B, step 2: for each of the QUERY's own strokes (already decoded, raw points in
    the decode cache), re-quantize (invariant-only — pose must not hurt the match, the SAME
    convention `ink_decode._score_span`'s pre-lattice emission uses) and decode against
    `build_instance_codebook`'s scratch substrate via ONE held `ShapeDecode` evaluate
    (`_instance_decode_term`) per query stroke: an EXACT match names a SPECIFIC exemplar-
    stroke instance, read straight off `covered_by`, never searched/ranked in Python. Returns
    ONLY the ADDITIVE `["strokeq_instance", k, name]` relations for strokes that matched an
    instance quantum — an unmatched query stroke contributes nothing (no fabricated identity),
    `strokeq`/`strokeq_fine`/`rel`/`cpose` are never touched by this function at all."""
    out: list[list] = []
    for k, item in enumerate(query_stroke_points):
        pts = np.asarray(item[0], dtype=float)
        if pts.ndim != 2 or pts.shape[0] < 2:
            continue
        q = _quantize(scratch_native, pts.tolist(), segments=segments, turn_bins=turn_bins,
                      len_bins=len_bins, grid=grid, scale_bins=scale_bins, invariant_only=True)
        _count, name = _instance_decode_term(scratch_native, q["signature"])
        if name is not None:
            out.append(["strokeq_instance", k, name])
    return out


def instance_conditioned_signatures(query_sig: list, query_stroke_points: list,
                                     candidate_sigs: list, candidate_stroke_points: list, *,
                                     segments: int, turn_bins: int, len_bins: int, grid: int,
                                     scale_bins: int) -> tuple[list, list]:
    """LEVER B — THE FULL EPISODE-SCOPED combinator (design: "per episode, the 20 exemplars'
    per-stroke signatures form a TEMPORARY codebook... re-decode the query's strokes against
    global + instance quanta; composed signatures gain instance-conditioned strokeq
    identities... making the strict-coverage proposal CLASS-SPECIFIC"). Returns
    `(query_instance_sig, candidate_instance_sigs)` — the SAME `query_sig`/`candidate_sigs`
    with `["strokeq_instance", k, name]` relations ADDITIVELY spliced on (every pre-existing
    relation byte-identical; the EXISTING `_coverage_term`, unchanged, fed these sees the SAME
    hits as before PLUS any NEW instance-specific hits, `name` embedding the owning candidate
    index so only THAT candidate's own self-relation can ever match it).

    `build_instance_codebook`'s scratch substrate is a local variable of this call only — it
    goes out of scope (garbage-collected) the instant this function returns: no edge from it
    into the agent's own held graph is ever created, and the LEARN codebook (the agent's own
    `ShapeSignature` nodes) is never read or written by this function at all."""
    scratch, names = build_instance_codebook(
        candidate_stroke_points, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
        grid=grid, scale_bins=scale_bins)
    scratch_native = scratch._inner

    q_extra = instance_decode_query(scratch_native, query_stroke_points, segments=segments,
                                     turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                                     scale_bins=scale_bins)
    query_instance_sig = list(query_sig) + q_extra

    candidate_instance_sigs = []
    for ci, csig in enumerate(candidate_sigs):
        extra = [["strokeq_instance", k, name] for (cci, k), name in names.items() if cci == ci]
        candidate_instance_sigs.append(list(csig) + extra)
    return query_instance_sig, candidate_instance_sigs


def abs_rerank_targeted(agent, query_sig: list, query_stroke_points: list,
                         candidate_sigs: list, candidate_stroke_points: list, *,
                         delta: float = 0.0, use_widen: bool = False,
                         use_appearance: bool = False, use_exemplar_true: bool = False,
                         use_instance: bool = False,
                         margin_threshold: float = 0.0, fit_threshold: float = float("inf"),
                         widen_to: int = DEFAULT_WIDEN_TO,
                         appearance_m: int = DEFAULT_APPEARANCE_M,
                         n_points: int = DEFAULT_RENDER_N_POINTS, turn_bins: int,
                         len_bins: int, grid: int, scale_bins: int,
                         segments: int = DEFAULT_SEGMENTS, use_junction_blend: bool = False,
                         junction_frac: float = DEFAULT_JUNCTION_FRAC) -> dict[str, Any]:
    """THE run-12 combinator: ONE function realizes all four RUN 12 arms (delta=0 control /
    +targeted-widen / +second-modality / +both) via two independent flags, each additive over
    the delta=0 `propose_variable_k` control this design's own state line names ("38.8% @
    mean 2.05 renders").

    STAGE 0 (structural): `propose_variable_k(delta)` — UNCHANGED, byte-identical to RUN 11's
    own delta=0 arm.
    STAGE 0.5 (LEVER 2, `use_appearance`): `propose_appearance_top_m` off the SAME decode
    cache's own `query_stroke_points`/`candidate_stroke_points` (no rendering) — its result is
    UNIONED with the structural shortlist (`sorted(set(a) | set(b))`, mechanical bookkeeping
    over candidate INDICES, never a ranking of the union's members — "the shortlist union
    mechanical").
    STAGE 1: ONE `abs_rerank` render-compare + held-Argmin verdict over the (possibly
    appearance-widened) shortlist.
    STAGE 2 (LEVER 1, `use_widen`): `widen_decision` reads STAGE 1's own render-compare scores
    — if it fires, ONE further `abs_rerank` over `propose_top_k(k=widen_to)` (a FRESH
    structural shortlist at width `widen_to`, "proposal ranks up to W" per the design — no
    second appearance look, no iteration; "one widen iteration max").

    `use_widen=False, use_appearance=False, delta=0.0` (the control arm's own call) reduces
    EXACTLY to RUN 11's `propose_variable_k(0.0)` + `abs_rerank` pair — additivity, checked by
    `tests/test_character_composition_migrated.py`'s own control-reproduction gate. Omitted
    `margin_threshold`/`fit_threshold` default to values that NEVER widen (`0.0`/`+inf` — a
    non-negative margin can never be `< 0.0`, and no finite distance exceeds `+inf`), so
    `use_widen=True` with no calibrated thresholds is an honest no-op rather than a silently
    wrong guess; callers pass real DATA (see the Omniglot script's own calibration pass).

    Returns the FINAL stage's `abs_rerank` result dict, plus `widened` (bool),
    `structural0`/`appearance0`/`shortlist0` (STAGE 0/0.5's own shortlists, for per-arm
    attribution), and `budget` (total render-compare calls actually spent — `len(shortlist0)`
    plus, only when widened, the second stage's own shortlist size — "the widen fires only on
    uncertain verdicts, most queries never widen").

    INSTANCE-CONDITIONED QUANTA (`use_exemplar_true`/`use_instance`, both default `False` —
    every pre-existing call reproduces the byte-identical RUN 12 arms): `use_exemplar_true`
    (LEVER A) is forwarded straight to STAGE 1/STAGE 2's own `abs_rerank` calls (render-compare
    against each candidate's OWN stroke points, not the global codebook quantum — see
    `abs_render_compare_term`'s docstring). `use_instance` (LEVER B) runs `instance_
    conditioned_signatures` ONCE (an episode-scoped scratch substrate, freed the instant that
    call returns) and uses its `["strokeq_instance", ...]`-augmented query/candidate
    signatures for STAGE 0's structural proposal ONLY (`propose_variable_k`, and — when a
    widen fires — STAGE 2's `propose_top_k` re-shortlist too, for the same class-specific
    proposal signal); STAGE 1/2's own render-compare calls always use the ORIGINAL
    `query_sig`/`candidate_sigs` (rendering reads stroke IDENTITY/pose, never the
    proposal-only `strokeq_instance` relation).

    BRANCH B CONTINUOUS (`use_junction_blend`/`junction_frac`, both default to the
    byte-identical pre-existing behaviour — every pre-existing call reproduces the exact same
    arms): forwarded straight to STAGE 1/STAGE 2's own `abs_rerank` calls as
    `junction_blend`/`junction_frac` — see `abs_render_compare_term`'s docstring / this
    module's top-of-file docstring for the full rationale. Proposal stages (STAGE 0/0.5) are
    UNCHANGED (the design: "no context-conditioned quanta, no new discrete relations" — the
    blend lives ONLY in the render-compare comparison, never in the coverage-based shortlist)."""
    native = _native(agent)
    proposal_query_sig, proposal_candidate_sigs = query_sig, candidate_sigs
    if use_instance:
        proposal_query_sig, proposal_candidate_sigs = instance_conditioned_signatures(
            query_sig, query_stroke_points, candidate_sigs, candidate_stroke_points,
            segments=segments, turn_bins=turn_bins, len_bins=len_bins, grid=grid,
            scale_bins=scale_bins)
    structural0 = propose_variable_k(native, proposal_query_sig, proposal_candidate_sigs, delta)
    appearance0: list[int] = []
    shortlist0 = structural0
    if use_appearance:
        _, q_slices = _stroke_frame_slices(query_stroke_points)
        cand_slices_list = [_stroke_frame_slices(cp)[1] for cp in candidate_stroke_points]
        appearance0 = propose_appearance_top_m(native, q_slices, cand_slices_list, appearance_m)
        shortlist0 = sorted(set(structural0) | set(appearance0))

    res0 = abs_rerank(agent, query_sig, query_stroke_points, candidate_sigs,
                       candidate_stroke_points, top_k=shortlist0, n_points=n_points,
                       turn_bins=turn_bins, len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                       segments=segments, exemplar_true=use_exemplar_true,
                       junction_blend=use_junction_blend, junction_frac=junction_frac)

    widened = False
    final = res0
    if use_widen and res0["scores"]:
        if widen_decision(native, res0["scores"], margin_threshold, fit_threshold):
            widened = True
            shortlist_w = propose_top_k(native, proposal_query_sig, proposal_candidate_sigs,
                                         k=widen_to)
            final = abs_rerank(agent, query_sig, query_stroke_points, candidate_sigs,
                                candidate_stroke_points, top_k=shortlist_w, n_points=n_points,
                                turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                                scale_bins=scale_bins, segments=segments,
                                exemplar_true=use_exemplar_true,
                                junction_blend=use_junction_blend, junction_frac=junction_frac)

    budget = len(shortlist0) + (len(final["top_k"]) if widened else 0)
    return {**final, "widened": widened, "structural0": structural0, "appearance0": appearance0,
            "shortlist0": shortlist0, "budget": budget}


# --------------------------------------------------------------------------- #
#  RECONCILIATION -- SC+TPS CONTINUOUS VERDICT (RUN 16, scratchpad/HANDWRITING_DESIGN.md's
#  "RECONCILIATION" section, 2026-07-03): the EARLIER Family-A arc
#  (`domains/analysis_by_synthesis.py`, superseded 2026-07-02 for LEARN/decode but never
#  disproven as a VERDICT) hit 78-81.5% at matched protocol using FUSED CONTINUOUS comparators
#  (`ShapeContextDist` + `TpsDeformDist` [+ `SmoothDeformDist`], RAW un-quantized point sets, a
#  held `Argmax`/`Argmin`) -- this gate's own `DtwTo`-on-quantized-renders verdict
#  (`abs_render_compare_term`) is the WEAK comparator the K=20 full-dwell ablation (RUN 11)
#  already showed LOSES to K=5 (27.5% < 37.5% historical, i.e. more candidates through a weak
#  verdict HURTS) -- proof the bottleneck is the DECISION metric, not proposal recall alone.
#  RECONCILIATION HYPOTHESIS: earned quanta PROPOSE (unchanged -- the existing delta=0+
#  appearance shortlist, `abs_rerank_targeted`'s own `shortlist0`), strong continuous geometry
#  DECIDES (this section's new verdict, `analysis_by_synthesis.render_compare_score`'s SC+TPS
#  pattern lifted into ONE held Term per candidate + a held `Argmin` -- never a Python argmin,
#  the exact violation `analysis_by_synthesis.classify_render`'s own Python-numpy argmin call
#  committed and this transplant fixes while keeping its muscle).
#
#  `whole_figure_point_set` mirrors `analysis_by_synthesis.point_set` exactly (translation+scale
#  normalize, arc-length resample to `N`) but reads off the ALREADY-DECODED `stroke_points` this
#  module's own decode cache carries (`[(points, identity[, ...]), ...]` draw order) rather than
#  re-reading the raw file -- no second world-adapter load, same normalization convention
#  `_stroke_frame_slices` establishes for the quantized-render path (`_stroke_frame_slices` uses
#  `character_compose._character_frame`'s own bbox-normalize; this uses `point_set`'s own
#  centroid+abs-max normalize verbatim -- Family-A's OWN convention, unchanged, so the fused
#  comparator sees exactly the point-set shape it was built for). `N=80` is `point_set`'s own
#  default, reused verbatim (not re-guessed) -- every real call site in this codebase
#  (`conversion_loop.py`, the `*_gate.py` scripts) calls `point_set` at its default `N`.
#
#  `sctps_verdict_term` is the Family-A fusion pattern `domains/recognition_graph.py` already
#  established (`predict_smooth_render_sc_term`/`predict_recursive_sc_term`: a weighted-sum
#  `Plus` of held distance Terms, lower = better) -- here unweighted (`Plus([ShapeContextDist,
#  TpsDeformDist])`, `include_smooth` ADDS `SmoothDeformDist` -- one step toward Family-A's full
#  ensemble, additive/flag-gated, default `False`) over WHOLE-FIGURE point-sets rather than
#  per-part. `sctps_rerank` is the verdict: propose (shortlist supplied by the caller -- the
#  EXISTING `abs_rerank_targeted` shortlist, or `range(way)` for a full-dwell arm, never
#  recomputed here), ONE held comparison Term per shortlisted candidate, ONE held `Argmin`
#  (`_argmin_pairs_term`, the SAME idiom `abs_rerank`'s own verdict already uses) over the
#  already-computed (score, id) pairs -- no Python min/sort/argmin anywhere in this section.
# --------------------------------------------------------------------------- #
DEFAULT_SCTPS_N_POINTS = 80          # domains.analysis_by_synthesis.point_set's OWN default N,
                                      # reused verbatim -- every real caller in this codebase
                                      # invokes point_set at its default, never a re-guessed N.


def whole_figure_point_set(stroke_points: list, n_points: int = DEFAULT_SCTPS_N_POINTS
                            ) -> Optional[list]:
    """ADAPTER (mirrors `analysis_by_synthesis.point_set`'s own normalize+resample exactly, off
    the ALREADY-DECODED `stroke_points` this module's decode cache carries -- no second file
    read): concatenate every stroke's own points in draw order, centre+abs-max normalize
    (factors out position/size -- style; orientation KEPT, Family-A's own convention), then
    arc-length resample to `n_points`. Returns `None` (never a fabricated point-set) for
    degenerate input (<3 raw points or zero arc length) -- the SAME honest-miss discipline
    `point_set` itself establishes for a degenerate file."""
    pts: list = []
    for item in stroke_points:
        arr = np.asarray(item[0], dtype=float).reshape(-1, 2)
        pts.extend(arr.tolist())
    a = np.asarray(pts, dtype=float)
    if a.shape[0] < 3:
        return None
    a = a - a.mean(0)
    scale = float(np.abs(a).max())
    if scale < 1e-9:
        return None
    a = a / (scale + 1e-9)
    d = np.sqrt((np.diff(a, axis=0) ** 2).sum(1))
    cum = np.concatenate([[0.0], np.cumsum(d)])
    if cum[-1] == 0:
        return None
    u = np.linspace(0.0, cum[-1], n_points)
    return np.stack([np.interp(u, cum, a[:, 0]), np.interp(u, cum, a[:, 1])], 1).tolist()


def sctps_verdict_term(query_ps: list, candidate_ps: list, *, include_smooth: bool = False
                        ) -> dict:
    """ONE held comparison Term: `Plus([ShapeContextDist(a,b), TpsDeformDist(a,b)`
    `[, SmoothDeformDist(a,b)]])` -- the Family-A fused continuous verdict
    (`recognition_graph`'s own weighted-`Plus`-of-distances fusion pattern, here unweighted),
    over WHOLE-FIGURE point-sets. LOWER = the candidate's own observed ink better explains the
    query. `include_smooth` (default `False`, additive) appends `SmoothDeformDist` -- one step
    toward Family-A's full ensemble. No Python distance computation; the fused score is ONE
    nested Term, one `evaluate` call downstream."""
    a_lit = {"type": "Lit", "value": query_ps}
    b_lit = {"type": "Lit", "value": candidate_ps}
    items = [{"type": "ShapeContextDist", "a": a_lit, "b": b_lit},
             {"type": "TpsDeformDist", "a": a_lit, "b": b_lit}]
    if include_smooth:
        items.append({"type": "SmoothDeformDist", "a": a_lit, "b": b_lit})
    return {"type": "Plus", "items": items}


def sctps_rerank(native, query_ps: Optional[list], candidate_ps_list: list, shortlist: list, *,
                  include_smooth: bool = False) -> dict[str, Any]:
    """THE reconciliation verdict: for each candidate index in `shortlist` (PROPOSAL-ONLY --
    the caller's own already-decided shortlist, e.g. `abs_rerank_targeted`'s `shortlist0`, or
    `list(range(way))` for a full-dwell arm; never recomputed here), ONE held
    `sctps_verdict_term` evaluate between the query's own point-set and that candidate's own
    STORED point-set (Family-A's own "compare against the exemplar's actual observed ink"
    pattern -- no rendering, no codebook lookup). The winner is ONE held `Argmin`
    (`_argmin_pairs_term`) over the (score, id) pairs -- never a Python min/sort/argmin call
    (`analysis_by_synthesis.classify_render`'s own Python-numpy argmin call is the violation
    this transplant fixes). A candidate or query with a `None` point-set (degenerate ink) is
    skipped -- an honest non-crash, never a fabricated score. `shortlist[0]` is the fallback
    winner for an empty/query-degenerate pass (mirrors `abs_rerank`'s own `coverage_pick`
    fallback discipline)."""
    pairs: list = []
    if query_ps is not None:
        for ci in shortlist:
            cps = candidate_ps_list[ci] if ci < len(candidate_ps_list) else None
            if cps is None:
                continue
            term = sctps_verdict_term(query_ps, cps, include_smooth=include_smooth)
            score = float(native.evaluate(term, {}) or 0.0)
            pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


# --------------------------------------------------------------------------- #
#  RUN 17 -- CLOSE THE GAP (scratchpad/HANDWRITING_DESIGN.md's "RUN 17" section, 2026-07-03):
#  four levers off RUN 16's reconciled 73.5% [67.0, 79.1] toward the Family-A 81.5% anchor.
#  LEVER 2 (TUNED FUSION) and LEVER 3 (ENSEMBLE MEMBERS AT FULL DWELL) below are additive
#  verdict-builder extensions of the SAME `sctps_verdict_term`/`sctps_rerank` pattern this
#  module's own RECONCILIATION section established -- weights and the ensemble-member choice
#  are DATA, never a Python score branch, held Argmin unchanged.
# --------------------------------------------------------------------------- #
def sctps_verdict_term_weighted(query_ps: list, candidate_ps: list, *, sc_w: float = 1.0,
                                 tps_w: float = 1.0, smooth_w: float = 0.0) -> dict:
    """TUNED FUSION (LEVER 2): the SAME `sctps_verdict_term` fusion pattern, weights AS DATA
    (`sc_w`/`tps_w`/`smooth_w`, design: "winning weights become DATA passed into the verdict
    Term") in place of the unweighted `Plus([SC, TPS[, Smooth]])`. `sc_w=1.0, tps_w=1.0,
    smooth_w=0.0` (the defaults) is NUMERICALLY byte-identical to `sctps_verdict_term`'s own
    unweighted `include_smooth=False` form (`Times(Lit(1.0), x)` is the numeric identity) --
    gated by `tests/test_character_composition_migrated.py`'s own byte-identity-at-unit-weights
    test. `smooth_w=0.0` OMITS the `SmoothDeformDist` sub-term entirely rather than multiplying
    an evaluated distance by zero (no wasted evaluate, no degenerate-input risk on a term whose
    score is discarded anyway)."""
    a_lit = {"type": "Lit", "value": query_ps}
    b_lit = {"type": "Lit", "value": candidate_ps}
    items = [{"type": "Times", "items": [{"type": "Lit", "value": float(sc_w)},
                                          {"type": "ShapeContextDist", "a": a_lit, "b": b_lit}]},
             {"type": "Times", "items": [{"type": "Lit", "value": float(tps_w)},
                                          {"type": "TpsDeformDist", "a": a_lit, "b": b_lit}]}]
    if smooth_w != 0.0:
        items.append({"type": "Times",
                       "items": [{"type": "Lit", "value": float(smooth_w)},
                                 {"type": "SmoothDeformDist", "a": a_lit, "b": b_lit}]})
    return {"type": "Plus", "items": items}


def sctps_rerank_weighted(native, query_ps: Optional[list], candidate_ps_list: list,
                           shortlist: list, *, sc_w: float = 1.0, tps_w: float = 1.0,
                           smooth_w: float = 0.0) -> dict[str, Any]:
    """THE tuned-fusion verdict: `sctps_rerank`'s own combinator shape, `sctps_verdict_term_
    weighted` in place of the unweighted `sctps_verdict_term` -- weights threaded through as
    DATA, never re-derived per call. Same held-Argmin/honest-skip/`shortlist[0]`-fallback
    discipline as `sctps_rerank`."""
    pairs: list = []
    if query_ps is not None:
        for ci in shortlist:
            cps = candidate_ps_list[ci] if ci < len(candidate_ps_list) else None
            if cps is None:
                continue
            term = sctps_verdict_term_weighted(query_ps, cps, sc_w=sc_w, tps_w=tps_w,
                                                smooth_w=smooth_w)
            score = float(native.evaluate(term, {}) or 0.0)
            pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


def single_sctps_verdict_term(query_ps: list, candidate_ps: list) -> dict:
    """ENSEMBLE MEMBER (LEVER 3): `ScTpsDist` ALONE -- the FULL Shape-Contexts distance (SC
    correspondences feeding a TPS fit, `recognition_graph.sctps_error_term`'s own shape) as ONE
    Rust primitive, rather than the `Plus([ShapeContextDist, TpsDeformDist])` SUM of two
    separate distances `sctps_verdict_term` builds. Closes the "run 16 only tested smooth on
    the shortlist" gap for the OTHER named ensemble member, at full dwell."""
    return {"type": "ScTpsDist", "a": {"type": "Lit", "value": query_ps},
            "b": {"type": "Lit", "value": candidate_ps}}


def single_sctps_rerank(native, query_ps: Optional[list], candidate_ps_list: list,
                         shortlist: list) -> dict[str, Any]:
    """THE `ScTpsDist`-alone verdict -- same held-Argmin/honest-skip/fallback discipline as
    `sctps_rerank`/`sctps_rerank_weighted`."""
    pairs: list = []
    if query_ps is not None:
        for ci in shortlist:
            cps = candidate_ps_list[ci] if ci < len(candidate_ps_list) else None
            if cps is None:
                continue
            score = float(native.evaluate(single_sctps_verdict_term(query_ps, cps), {}) or 0.0)
            pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


# --------------------------------------------------------------------------- #
#  RUN 17 -- LEVER 4, PARSE MARGINALIZATION: canonical-parse hypotheses (`domains.
#  canonical_parse.canonical_parts` at a theta grid) marginalised via `recognition_graph.
#  predict_smooth_marginal_sc_term` -- Family A's OWN held Term, REUSED VERBATIM (no re-
#  derived scoring math, no new Argmax of this module's own). This module contributes ONLY
#  the mechanical STAGING: a fresh, throwaway scratch substrate per episode (the SAME
#  "episode-scoped, never the agent's own held graph" discipline `build_instance_codebook`
#  already established) carrying a query Mark + the shortlisted candidate Concept nodes, each
#  with the whole-figure AxS feature (`recognition_graph.SIGN_FEAT_ATTR`/`WORD_FEAT_ATTR`) and
#  K PARSE HYPOTHESES (`PARSE_EDGE` -> ParseHyp -> `STROKE_EDGE` -> Stroke{`PTS_ATTR`}) -- the
#  EXACT staging `scripts/jabberwock_marginal_inference.py`'s own `add()` established for
#  Family A's own marginal-parse verdict (78-81.5%), reused verbatim here. The classification
#  decision is `predict_smooth_marginal_sc_term`'s OWN held Argmax over every staged
#  Concept{is_word:1} candidate -- restricting the candidate SET to a shortlist is therefore a
#  STAGING choice (stage only the shortlist's own characters), never a post-hoc Python filter
#  of the Term's own verdict.
# --------------------------------------------------------------------------- #
DEFAULT_PARSE_THETAS = (55.0, 70.0, 85.0)     # Family A's own marginal-inference theta grid
DEFAULT_PARSE_WHOLE_N = 64                     # Family A's own axs whole-figure resample N
DEFAULT_PARSE_PER_PART = 12                    # Family A's own per-part resample length

# RUN 25 -- C1, FINER THETA GRID (scratchpad/HANDWRITING_DESIGN.md's "RUN 25" scope, "THE
# NUMBER"): a PURE hypothesis-count increase into the SAME `stage_parse_char`/`predict_smooth_
# marginal_sc_term` staging -- `predict_smooth_marginal_sc_term` already marginalises over
# EVERY `ParseHyp` under `has_parse` regardless of its `theta` value, so widening the grid
# needs no new machinery, only a wider DATA tuple passed as `thetas=` at the call site. No new
# weight, no tuning -- spans roughly 40-95 degrees at 10-degree steps, RUN 17b's own
# (55, 70, 85) grid subsumed as a subset.
DEFAULT_PARSE_THETAS_FINE = (40.0, 50.0, 60.0, 70.0, 80.0, 90.0)


DEFAULT_PARSE_EARNED_THETA = -1.0    # sentinel `theta` attr (never a real corner threshold) --
                                      # tags the EARNED-segmentation ParseHyp `stage_parse_char`
                                      # adds when `earned_stroke_points` is given, so a caller
                                      # scanning a scratch substrate's own ParseHyp nodes can
                                      # tell it apart from a theta-grid hypothesis at a glance.

DEFAULT_PARSE_NUISANCE_THETA = -2.0  # RUN 25 -- C3, EXEMPLAR-NUISANCE MARGINALIZATION: a
                                      # SECOND sentinel `theta` attr (distinct from the EARNED
                                      # sentinel above), tags each NUISANCE-VARIANT ParseHyp
                                      # `stage_parse_char` adds when `nuisance_variant_parts` is
                                      # given -- so a caller scanning a scratch substrate's own
                                      # ParseHyp nodes can tell a nuisance variant apart from
                                      # both a theta-grid hypothesis and the earned hypothesis.


def _earned_parts_from_stroke_points(stroke_points: list, per_part: int) -> list:
    """LEVER 1a: the EARNED-segmentation twin of `canonical_parse.canonical_parts` -- mirrors
    that function's OWN joint-normalize (one centroid + RMS over every sub-point, so stroke
    LAYOUT/relations are preserved) + per-part arc-length resample EXACTLY, the only difference
    being WHERE the parts come from: `stroke_points`'s own already-decoded per-stroke point
    lists (`ink_decode.decode_ink`'s lattice output, the SAME `[(points, name[, fine_child[,
    substroke_points]]), ...]` draw-order shape this module's decode cache carries everywhere
    else) rather than a fresh corner-split of the raw writer strokes. Returns a list of
    `per_part`-length point arrays, structurally identical to `canonical_parts`'s own return
    shape -- `stage_parse_char` stages them into `Stroke` nodes the SAME way either source.
    Degenerate (empty) input returns `[]`, never a fabricated part."""
    subs = [np.asarray(item[0], dtype=float).reshape(-1, 2) for item in stroke_points
            if len(item[0]) >= 1]
    if not subs:
        return []
    allp = np.concatenate(subs, axis=0)
    c = allp.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(((allp - c) ** 2).sum(axis=1).mean())) or 1.0
    out = []
    for s_ in subs:
        s_ = (s_ - c) / rms
        s_ = _resample_arclen(s_, per_part) if s_.shape[0] >= 2 else np.repeat(s_, per_part, axis=0)
        out.append(s_)
    return out


def stage_parse_char(scratch, path: str, *, is_query: bool, thetas=DEFAULT_PARSE_THETAS,
                      whole_n: int = DEFAULT_PARSE_WHOLE_N,
                      per_part: int = DEFAULT_PARSE_PER_PART, name: Optional[str] = None,
                      earned_stroke_points: Optional[list] = None,
                      nuisance_variant_parts: Optional[list] = None,
                      denoise: bool = False, denoise_kwargs: Optional[dict] = None) -> int:
    """Mechanical graph staging (mirrors `build_instance_codebook`'s own scratch-substrate,
    add-only discipline) for ONE character file: a query Mark (`is_query=True`) or a candidate
    Concept (`is_word=1.0`, optionally `name`-tagged for the caller's own read-off), carrying
    the whole-figure AxS feature (raw pen trajectory, `domains.omniglot_world.trajectory`,
    per-stroke-conditioned, Family A's own convention) PLUS K parse-hypothesis subtrees at
    `thetas` (`domains.canonical_parse.canonical_parts`, boundary geometry only -- no
    decision). Returns the staged node id.

    `earned_stroke_points` (LEVER 1a, new, default `None` -- every pre-existing call site
    reproduces the byte-identical theta-grid-only staging): when given (the caller's own
    ALREADY-DECODED `stroke_points`, e.g. `scripts/jabberwock_omniglot_dynamic_quantization.
    decode_char_signature`'s own cached decode -- no second ink-decode here), ONE ADDITIONAL
    `ParseHyp` (tagged `theta=DEFAULT_PARSE_EARNED_THETA`, `kind="earned"`) is staged from
    `_earned_parts_from_stroke_points` -- the codebook's own learned segmentation joining the
    theta-grid hypotheses in the SAME marginalization, unchanged elsewhere
    (`recognition_graph.predict_smooth_marginal_sc_term`'s held Term walks every `ParseHyp`
    under `has_parse` regardless of its `theta` value).

    `nuisance_variant_parts` (RUN 25 -- C3, EXEMPLAR-NUISANCE MARGINALIZATION, new, default
    `None` -- every pre-existing call site reproduces the byte-identical staging): a list of K
    variant part-lists (the caller's own `glyph_motor_world.write_with_hand`-perturbed re-parse
    of THIS candidate's own raw strokes -- structurally identical to `_earned_parts_from_
    stroke_points`'s / `canonical_parse.canonical_parts`'s own per-part-point-array return
    shape). Each variant is staged as ONE ADDITIONAL `ParseHyp` (tagged
    `theta=DEFAULT_PARSE_NUISANCE_THETA`, `kind="nuisance"`) under the SAME candidate Concept
    node, joining the theta-grid (and, if given, earned) hypotheses in the SAME
    marginalization -- the claim under test being that a candidate's OWN token-variability
    (BPL's "each concept instantiates as a token with re-drawn stroke detail") is partially
    SIMULABLE by re-drawing its own strokes with a nuisance hand, entering the verdict's
    hypothesis SET without any learned model. A degenerate (empty) variant is skipped (an
    honest non-crash, never a fabricated ParseHyp).

    RUN 34 (`denoise=False` default -- every pre-existing call site reproduces the byte-
    identical staging): when `True`, this file's own raw strokes are reconstructed via
    `mouse_model.denoise_path` (the mouse observation model's inverse) ONCE, and the SAME
    denoised strokes feed BOTH the whole-figure trajectory (`glyph_motor_world.
    to_trajectory_strokes` directly, rather than a second `ow.trajectory(path, ...)` disk
    re-read) and the theta-grid `canonical_parts` staging below -- the DENOISE-VERDICT arm's
    own wiring point (both exemplar and query call `stage_parse_char` the same way, so setting
    `denoise=True` for an episode denoises both sides identically)."""
    import domains.omniglot_world as ow
    from domains import canonical_parse as cp
    from domains import glyph_motor_world as gmw
    from domains import recognition_graph as rg
    strokes = ow.load_strokes(path)
    if denoise:
        from domains import mouse_model as mm
        strokes = [mm.denoise_path(s, **(denoise_kwargs or {})) for s in strokes]
        whole = gmw.to_trajectory_strokes(strokes, whole_n)
    else:
        whole = ow.trajectory(path, whole_n, per_stroke=True)
    if is_query:
        node = scratch.add_node("Mark", {})
        scratch.set_attr(node, rg.SIGN_FEAT_ATTR, whole.tolist())
    else:
        attrs = {"is_word": 1.0}
        if name is not None:
            attrs["name"] = name
        node = scratch.add_node("Concept", attrs)
        scratch.set_attr(node, rg.WORD_FEAT_ATTR, whole.tolist())
    for th in thetas:
        ph = scratch.add_node("ParseHyp", {"theta": float(th)})
        scratch.add_edge_unchecked(node, rg.PARSE_EDGE, ph)
        for part in cp.canonical_parts(strokes, th, per_part=per_part):
            st = scratch.add_node("Stroke", {rg.PTS_ATTR: part.tolist()})
            scratch.add_edge_unchecked(ph, rg.STROKE_EDGE, st)
    if earned_stroke_points:
        earned_parts = _earned_parts_from_stroke_points(earned_stroke_points, per_part)
        if earned_parts:
            ph = scratch.add_node("ParseHyp", {"theta": DEFAULT_PARSE_EARNED_THETA,
                                                "kind": "earned"})
            scratch.add_edge_unchecked(node, rg.PARSE_EDGE, ph)
            for part in earned_parts:
                st = scratch.add_node("Stroke", {rg.PTS_ATTR: part.tolist()})
                scratch.add_edge_unchecked(ph, rg.STROKE_EDGE, st)
    if nuisance_variant_parts:
        for variant_parts in nuisance_variant_parts:
            if not variant_parts:
                continue
            ph = scratch.add_node("ParseHyp", {"theta": DEFAULT_PARSE_NUISANCE_THETA,
                                                "kind": "nuisance"})
            scratch.add_edge_unchecked(node, rg.PARSE_EDGE, ph)
            for part in variant_parts:
                arr = np.asarray(part, dtype=float).reshape(-1, 2)
                st = scratch.add_node("Stroke", {rg.PTS_ATTR: arr.tolist()})
                scratch.add_edge_unchecked(ph, rg.STROKE_EDGE, st)
    return node


# RUN 18 -- PARSE MARGINALIZATION AT FULL DWELL: Family A's own fusion-weight recipe
# (`scripts/jabberwock_marginal_inference.py`'s historical constants, RUN 17 inlined them as
# script-local literals `PARSE_PART_W, PARSE_SC_W, PARSE_BETA = 0.25, 1.6, 2.0`) promoted to
# named module constants HERE, alongside `DEFAULT_PARSE_THETAS`/`_WHOLE_N`/`_PER_PART` -- the
# same "the recipe is DATA the module owns, not a script literal" discipline those three
# already established. `parse_marginal_verdict`'s own defaults now reference them (byte-
# identical values, no behaviour change).
DEFAULT_PARSE_PART_W = 0.25
DEFAULT_PARSE_SC_W = 1.6
DEFAULT_PARSE_BETA = 2.0


def parse_marginal_verdict(scratch, query_node: int, *, part_w: float = DEFAULT_PARSE_PART_W,
                            sc_w: float = DEFAULT_PARSE_SC_W,
                            beta: float = DEFAULT_PARSE_BETA) -> Optional[int]:
    """THE held verdict (LEVER 4): `recognition_graph.predict_smooth_marginal_sc_term`, REUSED
    VERBATIM -- one `evaluate` over the scratch substrate `stage_parse_char` staged. `scratch`
    accepts either a bare `Substrate` (mirrors `_sub`/`_native`'s own dispatch, since this
    module's other scratch substrates -- `build_instance_codebook` -- are always used via their
    own `._inner`) or the raw native binding. Returns the winning CANDIDATE NODE ID (or `None`,
    an honest non-crash, e.g. an empty candidate pool) -- never a fabricated result; callers
    read the winner's own `name`/attrs back to a candidate index, the SAME mechanical read-off
    every pre-existing Family-A script in this codebase already uses (`s.node(w)["attrs"].
    get("name")`)."""
    from domains import recognition_graph as rg
    term = rg.predict_smooth_marginal_sc_term(part_w, sc_w, beta)
    native = getattr(scratch, "_inner", scratch)
    return native.evaluate(term, {"s": query_node})


# --------------------------------------------------------------------------- #
#  RUN 19 -- LEVER 2, TOKEN-REFIT AbS: a GENERAL directional program-explains-observation
#  faculty, knowing NOTHING of characters -- see this module's own top-of-file docstring
#  ("RUN 19" section) for the full asymmetry rationale vs RUN 17/18's SYMMETRIC `marginal_
#  part_error_term`. `program_parts`/`observed_path_parts` are bare Python lists of point-set
#  arrays ("parts") -- never graph nodes, never Concept/ParseHyp/Stroke.
# --------------------------------------------------------------------------- #
DEFAULT_REFIT_BETA = 2.0    # reuses recognition_graph's OWN existing default (`marginal_part_
                             # error_term`'s `beta`, `_soft_directed_part_dist`'s `beta_corr`)
                             # verbatim -- no new weight, no tuning.


def _refit_soft_min_term(program_part, observed_parts: list, beta_corr: float) -> dict:
    """HELD soft-min (log-sum-exp): `-1/beta * log( sum_q exp(-beta * TpsDeformDist(program_
    part, q)) )` over `observed_parts` `q` -- ONE program part explained by its BEST-fitting
    observed part, the correspondence MARGINALISED (not committed), mirroring `recognition_
    graph._soft_directed_part_dist`'s own soft-min semantics (`beta_corr` -> inf recovers the
    hard min; a finite `beta_corr` averages over the plausible correspondences) -- composed
    here over Python-managed `Lit` point-set lists (no graph `Neighbours`, since this function
    never touches a graph at all)."""
    inner = {"type": "Plus", "items": [
        {"type": "Exp", "arg": {"type": "Times", "items": [
            {"type": "Lit", "value": -float(beta_corr)},
            {"type": "TpsDeformDist", "a": {"type": "Lit", "value": program_part},
             "b": {"type": "Lit", "value": obs_part}}]}}
        for obs_part in observed_parts]}
    return {"type": "Neg", "arg": {"type": "Div", "a": {"type": "Log", "arg": inner},
                                    "b": {"type": "Lit", "value": float(beta_corr)}}}


def program_refit_term(program_parts: list, observed_path_parts: list, *,
                        beta_corr: float = DEFAULT_REFIT_BETA) -> dict:
    """THE held Term (design: "a single held likelihood-style score"): mean over `program_
    parts` of `_refit_soft_min_term` against `observed_path_parts` -- ONE nested Plus/Exp/Log/
    Div composition, ONE `evaluate` call downstream. DIRECTIONAL by construction: only
    `program_parts` ever enters the OUTER average -- `observed_path_parts` supplies candidates
    for the INNER soft-min only, so an observed part with no counterpart in the program never
    contributes a term of its own (the asymmetry vs RUN 17/18's symmetric `_parse_pair_dist`,
    documented in full at this module's own top-of-file docstring)."""
    per_part = [_refit_soft_min_term(p, observed_path_parts, beta_corr) for p in program_parts]
    return {"type": "Div", "a": {"type": "Plus", "items": per_part},
            "b": {"type": "Lit", "value": float(len(program_parts))}}


def program_refit_verdict(native, program_parts: list, observed_path_parts: list, *,
                           beta_corr: float = DEFAULT_REFIT_BETA) -> Optional[float]:
    """ONE held evaluate of `program_refit_term` -- knows NOTHING of characters: a
    `program_part`/`observed_part` is just a `[[x, y], ...]` array, never a graph node. LOWER =
    the program (the candidate's own generative parts) better explains `observed_path_parts`
    (the query's own observed ink, as a list of parts). Returns `None` (never a fabricated
    score -- the SAME honest-miss discipline every other verdict in this module follows) for an
    empty `program_parts` or an empty `observed_path_parts` (the inner soft-min over zero
    candidates is undefined, `log(0)`)."""
    if not program_parts or not observed_path_parts:
        return None
    return float(native.evaluate(
        program_refit_term(program_parts, observed_path_parts, beta_corr=beta_corr), {}) or 0.0)


def program_refit_rerank(native, program_parts_list: list, observed_path_parts: list,
                          shortlist: list, *, beta_corr: float = DEFAULT_REFIT_BETA
                          ) -> dict[str, Any]:
    """THE multi-candidate verdict: for each candidate index in `shortlist`, `program_refit_
    verdict` treats that candidate's OWN parts (`program_parts_list[ci]`) as the program fitted
    to the SAME `observed_path_parts` -- ONE held `Argmin` (`_argmin_pairs_term`, the SAME idiom
    `sctps_rerank`/`abs_rerank` already use) over the (score, id) pairs, never a Python
    min/sort/argmin. A candidate with no usable parts is skipped (an honest non-crash);
    `shortlist[0]` is the fallback winner for an empty/all-degenerate pass, mirroring every
    other rerank verdict's own fallback discipline."""
    pairs: list = []
    for ci in shortlist:
        parts = program_parts_list[ci] if ci < len(program_parts_list) else None
        score = (program_refit_verdict(native, parts, observed_path_parts, beta_corr=beta_corr)
                  if parts else None)
        if score is not None:
            pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


# --------------------------------------------------------------------------- #
#  RUN 20 -- BIDIRECTIONAL COVERAGE-CONSTRAINED REFIT (results/omniglot_gate_run19_refit.log's
#  own diagnostic appendix + commit e43fba60's "NEXT (run 20)" paragraph): RUN 19's directional
#  `program_refit_verdict` is ACTIVELY HARMFUL (25.5% vs a 20-way parse-marginal control at
#  ~79-80%) -- its own per-episode diagnosis names the mechanism precisely: "an unpenalised
#  per-part soft-min, with no term at all for how well the CANDIDATE's own distinctiveness is
#  used or how much of the OBSERVATION a genuinely different candidate would leave unexplained,
#  rewards generic/matchable programs over genuinely correct ones." This is exactly BPL's own
#  image-space likelihood lesson (Lake et al. 2015): a generative program must explain the
#  OBSERVATION JOINTLY, not merely find SOME easy correspondence for its own parts.
#
#  THE FIX, in held-Term form, is purely COMPOSITIONAL -- no new machinery, no assignment
#  algorithm: `program_refit_term`'s own soft-min (`_refit_soft_min_term`, already GENERIC over
#  which list supplies the "from" part and which list supplies the "to" candidates) is invoked a
#  SECOND time with the two argument lists SWAPPED -- program->ink (RUN 19's own metric,
#  UNCHANGED and kept as the reproducing ablation control) PLUS ink->program (every OBSERVED
#  part's own best-fitting PROGRAM part, marginalised the SAME way) -- summed at UNIT WEIGHT (no
#  new tuned weight; this mirrors the SAME "symmetric sum of two directed soft-mins" shape
#  `recognition_graph._joint_pair_dist` already establishes for the UNRELATED symmetric family --
#  `_soft_directed_part_dist(from,to,...)` + `_soft_directed_part_dist(to,from,...)`, reused here
#  as PRECEDENT for the combination discipline, not as shared code: that module's parts are graph
#  `Neighbours`, this module's are bare Python `Lit` point-set lists). PART-COUNT NORMALIZATION
#  is the MEAN each direction already takes (`program_refit_term`'s own `Div` by
#  `len(program_parts)`, mirrored by the swapped call's own `Div` by `len(observed_path_parts)`)
#  -- "normalize per-part," the simplest of the design's two named options (the alternative, an
#  explicit `|parts|`-mismatch penalty, would need a NEW weight to reconcile units with the TPS
#  distance; the per-part mean needs none -- no new tuned weight, per the standing discipline).
#  A generic 2-part program that ignores half the observation's distinctive ink now pays for it
#  on the NEW ink->program side (those unmatched observed parts have no good program-side match),
#  so the earlier "fewer, easier parts always wins" pathology cannot recur by construction.
# --------------------------------------------------------------------------- #
def program_refit_bidir_term(program_parts: list, observed_path_parts: list, *,
                              beta_corr: float = DEFAULT_REFIT_BETA) -> dict:
    """THE held Term: `program_refit_term`'s own program->ink mean PLUS its ink->program twin
    (the SAME `program_refit_term`/`_refit_soft_min_term` builder, `program_parts`/`observed_
    path_parts` simply SWAPPED) -- a plain unweighted `Plus` of two `Div`-normalised soft-min
    means, ONE nested composition, ONE `evaluate` call downstream. Every observed part must now
    be explained by SOME program part (the new term) AND every program part must explain SOME
    observed part (RUN 19's own term, unchanged) -- BPL's own bidirectional image-likelihood,
    held."""
    program_to_ink = program_refit_term(program_parts, observed_path_parts, beta_corr=beta_corr)
    ink_to_program = program_refit_term(observed_path_parts, program_parts, beta_corr=beta_corr)
    return {"type": "Plus", "items": [program_to_ink, ink_to_program]}


def program_refit_bidir_verdict(native, program_parts: list, observed_path_parts: list, *,
                                 beta_corr: float = DEFAULT_REFIT_BETA) -> Optional[float]:
    """ONE held evaluate of `program_refit_bidir_term` -- the SAME honest-`None` discipline as
    `program_refit_verdict` for an empty side (either soft-min direction is undefined over zero
    candidates). LOWER = the candidate's own parts and the observation JOINTLY explain each
    other best (both directions), never merely "this program is cheap to fit somewhere\""""
    if not program_parts or not observed_path_parts:
        return None
    return float(native.evaluate(
        program_refit_bidir_term(program_parts, observed_path_parts, beta_corr=beta_corr), {})
        or 0.0)


def program_refit_bidir_rerank(native, program_parts_list: list, observed_path_parts: list,
                                shortlist: list, *, beta_corr: float = DEFAULT_REFIT_BETA
                                ) -> dict[str, Any]:
    """THE multi-candidate BIDIRECTIONAL verdict -- `program_refit_rerank`'s own combinator
    shape (held `Argmin` via `_argmin_pairs_term`, honest skip of a candidate with no usable
    parts, `shortlist[0]` fallback), `program_refit_bidir_verdict` in place of RUN 19's
    directional-only `program_refit_verdict`. `program_refit_rerank` itself is UNTOUCHED --
    both verdicts stay callable side by side (the ablation-control discipline)."""
    pairs: list = []
    for ci in shortlist:
        parts = program_parts_list[ci] if ci < len(program_parts_list) else None
        score = (program_refit_bidir_verdict(native, parts, observed_path_parts,
                                              beta_corr=beta_corr) if parts else None)
        if score is not None:
            pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


# RUN 20 -- ARM 3, THE FULL GENERATIVE STACK: bidirectional token-refit as an ADDITIONAL score
# inside the parse-hypothesis marginalization, rather than a search-only reconciliation metric.
# `recognition_graph.predict_smooth_marginal_sc_term`'s own fused error expression (smoothdeform
# + part_w*marginal_part + sc_w*shapecontext) is reused VERBATIM but WITHOUT its wrapping
# `Argmax` -- `parse_marginal_pair_error_term` is the SAME per-candidate quantity the Argmax
# already ranks by (`Argmax(-err)` == `Argmin(err)`), exposed as a per-PAIR score so a second,
# independently-computed score (`program_refit_bidir_term`) can be summed into ONE combined Term
# BEFORE the final decision -- `predict_smooth_marginal_sc_term`'s own Argmax has nowhere to
# plug an external score in. Both sub-terms are combined at UNIT WEIGHT (no new tuned weight);
# if the two error scales turn out to be badly mismatched (one term swamping the other), that is
# reported honestly as this arm's own finding, not patched with an ad hoc weight.
def parse_marginal_pair_error_term(part_w: float = DEFAULT_PARSE_PART_W,
                                    sc_w: float = DEFAULT_PARSE_SC_W,
                                    beta: float = DEFAULT_PARSE_BETA) -> dict:
    """`recognition_graph.predict_smooth_marginal_sc_term`'s own fused error expression, reused
    VERBATIM minus the wrapping `Argmax`/`NodesWhere` scan -- a per-(query,candidate)-PAIR score,
    `s`/`w` left as free `Var`s for the caller's own `evaluate(term, {"s": ..., "w": ...})` env,
    exactly as `parse_marginal_verdict`'s own `native.evaluate(term, {"s": query_node})` already
    binds `s` (the wrapping Argmax there binds `w` itself; here nothing does, so both must be
    bound by the caller)."""
    from domains import recognition_graph as rg
    return {"type": "Plus", "items": [
        rg.smoothdeform_error_term(),
        {"type": "Times", "items": [{"type": "Lit", "value": float(part_w)},
                                     rg.marginal_part_error_term(beta)]},
        {"type": "Times", "items": [{"type": "Lit", "value": float(sc_w)},
                                     rg.shapecontext_error_term()]}]}


def parse_marginal_pair_error(scratch, query_node: int, cand_node: int, *,
                               part_w: float = DEFAULT_PARSE_PART_W,
                               sc_w: float = DEFAULT_PARSE_SC_W,
                               beta: float = DEFAULT_PARSE_BETA) -> float:
    """ONE held evaluate of `parse_marginal_pair_error_term` for a SPECIFIC (query, candidate)
    pair already staged into `scratch` by `stage_parse_char` -- the per-candidate ingredient
    `refit_bidir_plus_marginal_rerank`'s own `joined_refit_marginal_term` sums with the
    bidirectional token-refit score, exposed standalone for callers that only need the
    parse-marginal side (e.g. the consistency check against `parse_marginal_verdict`'s own
    Argmax ranking)."""
    native = getattr(scratch, "_inner", scratch)
    return float(native.evaluate(parse_marginal_pair_error_term(part_w=part_w, sc_w=sc_w,
                                                                  beta=beta),
                                  {"s": query_node, "w": cand_node}) or 0.0)


def joined_refit_marginal_term(program_parts: list, observed_path_parts: list, *,
                                beta_corr: float = DEFAULT_REFIT_BETA,
                                part_w: float = DEFAULT_PARSE_PART_W,
                                sc_w: float = DEFAULT_PARSE_SC_W,
                                beta: float = DEFAULT_PARSE_BETA) -> dict:
    """ONE combined held Term for ONE (query, candidate) pair: `parse_marginal_pair_error_term`
    (needs `s`/`w` bound by the caller's `evaluate` env, staged graph nodes) PLUS `program_refit_
    bidir_term` (needs no graph at all, bare Python point-set lists) -- a single nested `Plus`,
    ONE `evaluate` call downstream, exactly this module's own "one nested composition, one
    evaluate" discipline (`program_refit_term`'s docstring) extended across the graph/non-graph
    boundary. LOWER = jointly better under BOTH the parse-marginal fusion and the bidirectional
    token-refit."""
    return {"type": "Plus", "items": [
        parse_marginal_pair_error_term(part_w=part_w, sc_w=sc_w, beta=beta),
        program_refit_bidir_term(program_parts, observed_path_parts, beta_corr=beta_corr)]}


def refit_bidir_plus_marginal_rerank(scratch, query_node: int, cand_nodes: dict[int, int],
                                      program_parts_list: list, observed_path_parts: list,
                                      shortlist: list, *, beta_corr: float = DEFAULT_REFIT_BETA,
                                      part_w: float = DEFAULT_PARSE_PART_W,
                                      sc_w: float = DEFAULT_PARSE_SC_W,
                                      beta: float = DEFAULT_PARSE_BETA) -> dict[str, Any]:
    """THE FULL-STACK joined verdict (design intent, commit e43fba60's "NEXT" paragraph: "refit
    as an additional score inside the parse-hypothesis soft-min -- the full generative stack"):
    for each candidate index in `shortlist`, ONE `joined_refit_marginal_term` evaluate combines
    the parse-marginal error (over `scratch`'s already-`stage_parse_char`-staged nodes) with the
    bidirectional token-refit score (over the caller's own raw/rich per-stroke point lists) --
    never two separately-evaluated scores added in Python; the `Plus` composition IS the held
    Term. `cand_nodes` maps candidate index -> the staged Concept node id (`stage_parse_char`'s
    own return value, collected by the caller exactly as every other multi-candidate staging in
    this module already does). Held `Argmin` (`_argmin_pairs_term`) over the resulting pairs, the
    SAME idiom every other rerank in this module uses; `shortlist[0]` fallback; a candidate
    missing a staged node or usable parts is skipped, never a crash."""
    native = getattr(scratch, "_inner", scratch)
    pairs: list = []
    for ci in shortlist:
        cand_node = cand_nodes.get(ci)
        parts = program_parts_list[ci] if ci < len(program_parts_list) else None
        if cand_node is None or not parts or not observed_path_parts:
            continue
        term = joined_refit_marginal_term(parts, observed_path_parts, beta_corr=beta_corr,
                                           part_w=part_w, sc_w=sc_w, beta=beta)
        score = float(native.evaluate(term, {"s": query_node, "w": cand_node}) or 0.0)
        pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


# --------------------------------------------------------------------------- #
#  RUN 25 -- C2, VERDICT FUSION AT DIFFERENT GRAINS (scratchpad/HANDWRITING_DESIGN.md's
#  "RUN 25" scope, "THE NUMBER"): never tested before -- prior runs (RUN 16/17) tried whole-
#  figure SC+TPS verdicts as ALTERNATIVES to the parse-marginal verdict, never FUSED with it.
#  `fused_grain_verdict_term` sums `parse_marginal_pair_error_term` (the PART-marginal error,
#  needs graph `s`/`w` bound -- the SAME per-pair quantity `parse_marginal_verdict`'s own
#  wrapping Argmax ranks by) with `sctps_verdict_term` (the WHOLE-FIGURE SC+TPS error, bare
#  point-set `Lit`s, no graph at all) at UNIT WEIGHT inside ONE held `Plus` -- exactly
#  `joined_refit_marginal_term`'s own graph/non-graph fusion precedent, a different second
#  term. `norm_a`/`norm_b` (both default `1.0`, the numeric identity -- `Div` by 1.0 is
#  literally skipped, never evaluated, mirroring `sctps_verdict_term_weighted`'s own
#  byte-identical-at-unit-weight discipline) let a caller apply MECHANICAL SCALE ALIGNMENT: if
#  staging data shows the two error magnitudes badly mismatched (one term swamping the other),
#  `fused_grain_rerank`'s `normalize=True` divides each sub-term by its OWN per-EPISODE
#  candidate-mean (a plain Python `sum(...)/len(...)` over an ALREADY-fully-computed list of
#  floats -- the SAME class of post-hoc bookkeeping `run17_close._grid_winner`'s own weighted
#  combination of already-Term-computed raw distances already establishes as legal, never
#  itself a ranking). This is a PRE-REGISTERED, DATA-INSPECTION-DRIVEN CHOICE OF COMPOSITION
#  (raw sum vs per-episode-normalized sum), decided from real staged numbers BEFORE any
#  accuracy is computed -- not a tuned weight chosen by outcome.
# --------------------------------------------------------------------------- #
def fused_grain_verdict_term(query_ps: list, candidate_ps: list, *,
                              part_w: float = DEFAULT_PARSE_PART_W,
                              sc_w: float = DEFAULT_PARSE_SC_W, beta: float = DEFAULT_PARSE_BETA,
                              include_smooth: bool = False, norm_a: float = 1.0,
                              norm_b: float = 1.0) -> dict:
    """ONE held Term for ONE (query, candidate) pair: `parse_marginal_pair_error_term` (needs
    `s`/`w` bound by the caller's `evaluate` env) PLUS `sctps_verdict_term` (needs no graph at
    all) -- a single nested `Plus`, ONE `evaluate` call downstream. `norm_a`/`norm_b` != 1.0
    wrap the respective sub-term in a `Div` by that literal constant (mechanical scale
    alignment; `== 1.0` -- the default -- reproduces the UNNORMALIZED unit-weight sum
    byte-identically, no `Div` node at all). LOWER = jointly better under both the part-marginal
    fusion and the whole-figure SC+TPS distance."""
    a = parse_marginal_pair_error_term(part_w=part_w, sc_w=sc_w, beta=beta)
    b = sctps_verdict_term(query_ps, candidate_ps, include_smooth=include_smooth)
    if norm_a != 1.0:
        a = {"type": "Div", "a": a, "b": {"type": "Lit", "value": float(norm_a)}}
    if norm_b != 1.0:
        b = {"type": "Div", "a": b, "b": {"type": "Lit", "value": float(norm_b)}}
    return {"type": "Plus", "items": [a, b]}


def fused_grain_rerank(scratch, query_node: int, cand_nodes: dict[int, int], query_ps: list,
                        candidate_ps_list: list, shortlist: list, *,
                        part_w: float = DEFAULT_PARSE_PART_W, sc_w: float = DEFAULT_PARSE_SC_W,
                        beta: float = DEFAULT_PARSE_BETA, include_smooth: bool = False,
                        normalize: bool = False) -> dict[str, Any]:
    """THE fused-grain verdict: for each candidate index in `shortlist`, ONE `fused_grain_
    verdict_term` evaluate combines the part-marginal error (over `scratch`'s already-`stage_
    parse_char`-staged nodes) with the whole-figure SC+TPS error (over the caller's own raw
    point-sets, `whole_figure_point_set`'s own output). `cand_nodes` maps candidate index ->
    the staged Concept node id, the SAME shape `refit_bidir_plus_marginal_rerank` already
    requires. Held `Argmin` (`_argmin_pairs_term`) over the resulting pairs -- the SAME idiom
    every other rerank in this module uses; `shortlist[0]` fallback; a candidate missing a
    staged node or point-set is skipped, never a crash.

    `normalize=False` (default, byte-identical unweighted unit sum): every sub-term evaluated
    ONCE via `fused_grain_verdict_term(norm_a=1.0, norm_b=1.0)`, ONE evaluate per candidate.
    `normalize=True`: a FIRST pass collects the raw (un-normalized) part-marginal and SC+TPS
    scores for every valid candidate in THIS episode (two more evaluates per candidate -- plain
    data collection, no decision), then `norm_a`/`norm_b` are this episode's own candidate-mean
    of each raw list (Python `sum(...)/len(...)`, mechanical bookkeeping over an
    ALREADY-fully-computed list of floats, never a ranking), and a SECOND pass builds+evaluates
    the normalized `fused_grain_verdict_term` per candidate for the final held-Argmin verdict."""
    native = getattr(scratch, "_inner", scratch)
    valid = [ci for ci in shortlist
             if cand_nodes.get(ci) is not None and ci < len(candidate_ps_list)
             and candidate_ps_list[ci] is not None and query_ps is not None]
    norm_a = norm_b = 1.0
    if normalize and valid:
        raw_a = [parse_marginal_pair_error(scratch, query_node, cand_nodes[ci], part_w=part_w,
                                            sc_w=sc_w, beta=beta) for ci in valid]
        raw_b = [float(native.evaluate(
                     sctps_verdict_term(query_ps, candidate_ps_list[ci],
                                         include_smooth=include_smooth), {}) or 0.0)
                 for ci in valid]
        # mechanical scale alignment, NOT a tuned weight -- a plain Python mean over an
        # ALREADY-fully-computed list of floats, computed fresh per episode.
        mean_a = sum(raw_a) / len(raw_a)
        mean_b = sum(raw_b) / len(raw_b)
        norm_a = mean_a if mean_a else 1.0
        norm_b = mean_b if mean_b else 1.0
    pairs = []
    for ci in valid:
        term = fused_grain_verdict_term(query_ps, candidate_ps_list[ci], part_w=part_w,
                                         sc_w=sc_w, beta=beta, include_smooth=include_smooth,
                                         norm_a=norm_a, norm_b=norm_b)
        score = float(native.evaluate(term, {"s": query_node, "w": cand_nodes[ci]}) or 0.0)
        pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(_argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs),
            "norm_a": norm_a, "norm_b": norm_b}


__all__ = ["DEFAULT_TOPK", "DEFAULT_RENDER_N_POINTS", "_stroke_render_live",
           "propose_top_k", "abs_render_compare_term", "pointset_compare_term",
           "abs_rerank", "_stroke_frame_slices", "_strokeq_map", "_rel_map",
           "_candidate_seg", "_exemplar_true_seg", "_render_goal", "_render_term", "_dtw_term",
           "propose_variable_k", "proposal_rank",
           "DEFAULT_WIDEN_TO", "DEFAULT_APPEARANCE_M", "widen_decision",
           "propose_appearance_top_m", "abs_rerank_targeted",
           "INSTANCE_PREFIX", "_instance_name", "build_instance_codebook",
           "instance_decode_query", "instance_conditioned_signatures",
           "DEFAULT_JUNCTION_FRAC", "_junction_blend",
           "DEFAULT_SCTPS_N_POINTS", "whole_figure_point_set", "sctps_verdict_term",
           "sctps_rerank", "sctps_verdict_term_weighted", "sctps_rerank_weighted",
           "single_sctps_verdict_term", "single_sctps_rerank",
           "DEFAULT_PARSE_THETAS", "DEFAULT_PARSE_WHOLE_N", "DEFAULT_PARSE_PER_PART",
           "DEFAULT_PARSE_PART_W", "DEFAULT_PARSE_SC_W", "DEFAULT_PARSE_BETA",
           "DEFAULT_PARSE_EARNED_THETA", "_earned_parts_from_stroke_points",
           "stage_parse_char", "parse_marginal_verdict",
           "DEFAULT_REFIT_BETA", "_refit_soft_min_term", "program_refit_term",
           "program_refit_verdict", "program_refit_rerank",
           "program_refit_bidir_term", "program_refit_bidir_verdict",
           "program_refit_bidir_rerank", "parse_marginal_pair_error_term",
           "parse_marginal_pair_error", "joined_refit_marginal_term",
           "refit_bidir_plus_marginal_rerank",
           "DEFAULT_PARSE_THETAS_FINE", "DEFAULT_PARSE_NUISANCE_THETA",
           "fused_grain_verdict_term", "fused_grain_rerank"]
