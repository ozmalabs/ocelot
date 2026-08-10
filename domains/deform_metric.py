"""deform_metric — RUN 44 PHASE 2: A BACKGROUND-LEARNED DEFORMATION METRIC (the last untried
verdict-change class in the human-gap plan). Nine prior attempts (RUN 25's six nulls, RUN 34b
upstream denoise, RUN 39b orthogonal supplement, RUN 43 nuisance expansion) all changed the
EVIDENCE the comparator sees or its weighting; none changed the DISTANCE FUNCTION itself with
background discriminative information. This module changes what the comparator CHARGES for
deformation, not what it sees.

THE STANDING COMPARATOR (`domains.abs_read.parse_marginal_verdict` -> `recognition_graph.
predict_smooth_marginal_sc_term`, RUN 25/26's 80.5% [76.3, 84.1] @ n=400 GUARD): fuses THREE
sub-terms at fixed weights (`part_w=0.25`, `sc_w=1.6`):

    error(s, w) = smoothdeform_error(s, w)                    -- whole-figure SmoothDeformDist
                + part_w * marginal_part_error(s, w)          -- per-part PointSetDist, parse-
                                                                  hypothesis-marginalised
                + sc_w  * shapecontext_error(s, w)             -- whole-figure ShapeContextDist

CORRECTION TO THE LAUNCH BRIEF'S OWN PREMISE (stated up front, per this arc's standing honesty
law): the brief names `TpsDeformDist`/`ShapeContextDist` as "what the comparator sums." Reading
`domains/abs_read.py` + `domains/recognition_graph.py` + the Rust terms directly shows the
STANDING GUARD verdict's whole-figure warp term is `SmoothDeformDist` (a free-form-deformation
field, `runners/dsl/src/term.rs::smooth_deform_dist`), NOT `TpsDeformDist` -- `TpsDeformDist` is
used by OTHER, non-adopted verdicts this arc tried earlier (`sctps_rerank`, `program_refit_*`)
but never by the standing `parse_marginal_verdict`/C0 control. `SmoothDeformDist`'s own
distortion-cost term (`residual + 1.5 * dc`, `dc` = mean squared TOTAL per-point displacement)
prices EVERY direction of displacement identically -- a writer-typical global rotation/shear
costs exactly as much per unit displacement as a genuine non-affine bending distortion that
should discriminate a wrong class. THIS is the term this module reweights. `marginal_part_error`
(raw `PointSetDist`, no deformation at all) and `shapecontext_error` (a descriptor match, not a
warp) have no affine/bending structure to decompose -- both are OUT OF SCOPE and left BYTE-
IDENTICAL in the reweighted verdict (RUN 43's own "37A's law biases to supplement, not invent a
new lever where the decomposition doesn't cleanly separate" applied literally: here the
decomposition DOES cleanly separate for the warp term, so it REPLACES that one sub-term only).

THE MECHANISM: `runners/dsl/src/deform_metric.rs`'s new `SmoothDeformComponents` Term (additive,
`smooth_deform_dist` itself untouched -- see that Rust module's own doc) decomposes the SAME FFD
displacement field `SmoothDeformDist` already fits into a best-fit AFFINE part (rotation, shear,
log-scale, translation -- closed-form least squares) and the NON-AFFINE residual ("bending", the
part the affine fit does not explain). The reweighted term then prices:

    reweighted_smoothdeform(s, w) = residual
                                   + w_bend * bending
                                   + rotation^2 / sigma_rotation^2
                                   + shear^2   / sigma_shear^2

`residual` (does the warped candidate explain the query) is UNCHANGED -- this mechanism only
touches the DISTORTION-COST regularizer, never the match-quality term. `sigma_rotation`/
`sigma_shear` are BACKGROUND within-class pairwise stds (how much do two same-class glyphs from
different writers typically differ in each affine DOF, measured on the 5 LEARN alphabets via
THIS SAME `SmoothDeformComponents` term -- see `calibrate_affine_sigmas`) so a TYPICAL amount of
writer rotation/shear costs little (Mahalanobis-normalized) while an ATYPICAL amount still costs
something -- sharper than `TpsDeformDist`'s existing binary "affine is entirely free" stance.
`w_bend` is calibrated ONCE on BACKGROUND 20-way one-shot episodes (a small pre-registered grid,
frozen before the real eval ever runs) -- see `scripts/jabberwock_omniglot_run44_metric.py`.

WHY A FRESH PAIRWISE CALIBRATION, NOT A LITERAL REUSE OF RUN 43'S `calibration.json` NUMBERS:
the launch brief suggested reusing RUN 43's `shear_std`/`rotation_std` directly. Those numbers
are real and are READ (read-only) into this run's own report as a cross-reference, but they are
NOT the same quantity this mechanism needs: RUN 43's stds are `episode_style.estimate_shear`/
this module's `estimate_rotation_angle` PER-GLYPH residuals from a CLASS MEAN (a single-glyph
shape-asymmetry estimator, used to render synthetic nuisance variants), not a PAIRWISE
"how much does the best-fit affine warp between two ACTUAL same-class glyphs differ" measurement
via the SAME `SmoothDeformComponents` term this reweighting fires against. Reusing the RUN 43
numbers directly would risk a units mismatch (single-glyph-vs-class-mean std vs pairwise-
between-two-glyphs std -- related by roughly a factor of sqrt(2) under independence, but not
verified identical in construction). This module instead measures `sigma_rotation`/`sigma_shear`
FRESH, via THE EXACT SAME Term the eval uses, on same-class background PAIRS -- an internally
consistent calibration, at the cost of a small extra background pass (bounded: <=3 pairs per
class, ~150-200 classes across the 5 LEARN alphabets, `calibrate_affine_sigmas`'s own docstring
states the exact bound). RUN 43's numbers are reported alongside as a qualitative cross-check
(same story: shear/rotation writer-dim variance is real and non-trivial), not as this run's own
sigmas.

ARCHITECTURE (CLAUDE.md): every function here is either (1) mechanical Term construction (a
`SmoothDeformComponents` invocation, a `DictGet`/`Let`-wrapped reweighted error expression) or
(2) a plain numeric reduction (mean/std pooling over ALREADY-COMPUTED Term outputs, the SAME
"estimate/canonicalize here, verdict there" division of labour `exemplar_expand.py`'s own module
doc establishes) or (3) file I/O (freeze/load a calibration JSON). No decision (which candidate
wins) is made in this module -- that stays the gate script's own held `Argmin` over per-candidate
scores, exactly like every other verdict variant in `domains/abs_read.py`."""
from __future__ import annotations

import os
from typing import Optional

import numpy as np

DEFAULT_LEARN_N = 5                    # SAME 5 LEARN alphabets as `exemplar_expand.DEFAULT_LEARN_N`
                                        # / RUN 43's own calibration (`ow.alphabets("background")[:5]`).
DEFAULT_WHOLE_N = 64                    # `abs_read.DEFAULT_PARSE_WHOLE_N`, reused verbatim -- the
                                        # SAME whole-figure trajectory feature the standing GUARD
                                        # verdict's own `smoothdeform_error_term` compares.
MAX_PAIRS_PER_CLASS = 3                 # PRE-REGISTERED bound: drawer 0 vs drawers 1..3 (whichever
                                        # exist) -- keeps the background pass cheap (<=~470 pairs
                                        # across ~156 classes in the 5 LEARN alphabets) while pooling
                                        # more than a single pair per class.
SIGMA_FLOOR = 1e-4                      # honest safety floor against a degenerate (near-zero) std
                                        # collapsing the Mahalanobis term to a divide-by-~0 blowup --
                                        # an engineering safety valve, never a tuned weight.

# ===================================================================================================
# TERM BUILDERS -- SmoothDeformComponents + the reweighted whole-figure error, held Terms only.
# ===================================================================================================
def smooth_deform_components_term(a, b) -> dict:
    """`SmoothDeformComponents(a, b)` -- `a`/`b` are already-built Term dicts (an `Attr` read off
    a graph node, or a `Lit` point-set) evaluating to `[[x,y], ...]` point lists. Returns the
    Rust Term dict; NOT yet evaluated."""
    return {"type": "SmoothDeformComponents", "a": a, "b": b}


def _dict_get(dict_term: dict, key: str) -> dict:
    return {"type": "DictGet", "dict": dict_term, "key": {"type": "Lit", "value": key}}


def reweighted_smoothdeform_term(a, b, *, w_bend: float, sigma_rotation: float,
                                  sigma_shear: float) -> dict:
    """THE reweighted distortion-cost term (design's central formula): `residual + w_bend *
    bending + rotation^2/sigma_rotation^2 + shear^2/sigma_shear^2` -- a held `Let` binds ONE
    `SmoothDeformComponents(a, b)` evaluate to `sdc`, and every component is read off via
    `DictGet(Var(sdc), <key>)` so the expensive FFD field fit runs EXACTLY ONCE per pair
    (never once per component read) -- the SAME "evaluate once, bind, reuse" idiom `TermNode::
    Let`'s own Rust doc describes, its first user in this codebase's Python side. `sigma_*` are
    floored at `SIGMA_FLOOR` (an honest divide-by-~0 guard, not a tuned parameter) -- callers
    pass ALREADY-floored values (this function floors again defensively)."""
    sigma_rotation = max(float(sigma_rotation), SIGMA_FLOOR)
    sigma_shear = max(float(sigma_shear), SIGMA_FLOOR)
    comp = smooth_deform_components_term(a, b)
    var = {"type": "Var", "name": "sdc"}
    residual = _dict_get(var, "residual")
    bending = _dict_get(var, "bending")
    rotation = _dict_get(var, "rotation")
    shear = _dict_get(var, "shear")
    body = {"type": "Plus", "items": [
        residual,
        {"type": "Times", "items": [{"type": "Lit", "value": float(w_bend)}, bending]},
        {"type": "Div", "a": {"type": "Times", "items": [rotation, rotation]},
         "b": {"type": "Lit", "value": sigma_rotation ** 2}},
        {"type": "Div", "a": {"type": "Times", "items": [shear, shear]},
         "b": {"type": "Lit", "value": sigma_shear ** 2}},
    ]}
    return {"type": "Let", "name": "sdc", "value": comp, "body": body}


def reweighted_smoothdeform_error_term(*, w_bend: float, sigma_rotation: float,
                                        sigma_shear: float, sign_attr: str = "axs_heard_feat",
                                        word_attr: str = "axs_synth_feat") -> dict:
    """GRAPH-NATIVE twin of `recognition_graph.smoothdeform_error_term` -- reads the SAME `s`/
    `w` free `Var`s (bound by the caller's own `evaluate(term, {"s": ..., "w": ...})` env,
    exactly like `abs_read.parse_marginal_pair_error_term`'s own binding contract) off the SAME
    `axs_heard_feat`/`axs_synth_feat` node attrs `stage_parse_char` already populates -- NO new
    staging, only a different Term over the EXISTING graph data."""
    a = {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": sign_attr}
    b = {"type": "Attr", "node": {"type": "Var", "name": "w"}, "key": word_attr}
    return reweighted_smoothdeform_term(a, b, w_bend=w_bend, sigma_rotation=sigma_rotation,
                                         sigma_shear=sigma_shear)


def reweighted_pair_error_term(*, w_bend: float, sigma_rotation: float, sigma_shear: float,
                                part_w: float, sc_w: float, beta: float) -> dict:
    """THE full reweighted fused pair-error -- `abs_read.parse_marginal_pair_error_term`'s OWN
    `Plus([smoothdeform, part_w*marginal_part, sc_w*shapecontext])` shape, with ONLY the first
    sub-term replaced by `reweighted_smoothdeform_error_term`; `marginal_part_error_term`/
    `shapecontext_error_term` are `recognition_graph`'s OWN held Terms, reused VERBATIM (out of
    this mechanism's scope -- see this module's own top-of-file doc for why). Needs `s`/`w`
    bound by the caller, exactly like `parse_marginal_pair_error_term`."""
    from domains import recognition_graph as rg
    return {"type": "Plus", "items": [
        reweighted_smoothdeform_error_term(w_bend=w_bend, sigma_rotation=sigma_rotation,
                                            sigma_shear=sigma_shear),
        {"type": "Times", "items": [{"type": "Lit", "value": float(part_w)},
                                     rg.marginal_part_error_term(beta)]},
        {"type": "Times", "items": [{"type": "Lit", "value": float(sc_w)},
                                     rg.shapecontext_error_term()]}]}


def reweighted_pair_error(scratch, query_node: int, cand_node: int, *, w_bend: float,
                           sigma_rotation: float, sigma_shear: float,
                           part_w: float, sc_w: float, beta: float) -> float:
    """ONE held evaluate of `reweighted_pair_error_term` for a SPECIFIC (query, candidate) pair
    already staged into `scratch` by `abs_read.stage_parse_char` -- the EXACT staging GUARD
    itself uses (same theta grid, same graph shape); only the comparator Term differs. Mirrors
    `abs_read.parse_marginal_pair_error`'s own signature/dispatch exactly."""
    native = getattr(scratch, "_inner", scratch)
    term = reweighted_pair_error_term(w_bend=w_bend, sigma_rotation=sigma_rotation,
                                       sigma_shear=sigma_shear, part_w=part_w, sc_w=sc_w,
                                       beta=beta)
    return float(native.evaluate(term, {"s": query_node, "w": cand_node}) or 0.0)


# ===================================================================================================
# RUN 44b -- SPREAD-MATCHED SUPPLEMENT (the 34a->34b principled redesign of 44a's Mahalanobis
# metric). 44a's own diagnosis (commit 4990c69e): the idea was directionally right (TRUE 0.460 vs
# WRONG 7.101 on the reweighted term alone) but harmed catastrophically because REPLACING the
# whole-figure smoothdeform term with a Mahalanobis-normalized one let its across-candidate
# SPREAD (~6.64) drown the balanced recipe's other two terms (0.13-0.31) -- scale dominance, not
# a wrong direction. 44b's fix is TWO-FOLD, both binding rules from that diagnosis: (a) SUPPLEMENT
# rather than replace (`ar.parse_marginal_pair_error_term`'s own three-term fused error stays
# BYTE-IDENTICAL; a new affine-only Mahalanobis term is ADDED at a weight `w_aff` derived from
# background spread-matching, never a bare "1.0 implicit weight" the way 44a's replacement
# silently carried); (b) BACKGROUND-SANITY GATED before any eval spend (an arm catastrophically
# below the unmodified recipe's OWN background accuracy is stopped here, exactly where 44a's own
# w_bend curve -- 41% vs ~83% baseline -- would have caught it before a single real eval episode
# ran). `mahalanobis_affine_term` below carries NO `residual`/`bending` (unlike `reweighted_
# smoothdeform_term` above, which is 44a's REPLACE-shaped mechanism) -- it is a pure, standalone
# rotation/shear Mahalanobis cost, meant to be ADDED on top of the untouched recipe, not
# substituted into it.
# ===================================================================================================
def mahalanobis_affine_term(a, b, *, sigma_rotation: float, sigma_shear: float) -> dict:
    """The pure Mahalanobis affine-cost term: `rotation^2/sigma_rotation^2 + shear^2/sigma_
    shear^2` -- no `residual`, no `bending` (contrast `reweighted_smoothdeform_term`, which
    fuses all four and is meant to REPLACE the standing smoothdeform sub-term). This term is
    meant to be ADDED, at a caller-supplied weight, alongside the UNTOUCHED existing recipe --
    RUN 44b's supplement design, the opposite compositional choice from 44a's replace, licensed
    by 44a's own diagnosis (scale dominance, not wrong direction). Same `Let`-bound "evaluate
    `SmoothDeformComponents` once" idiom as `reweighted_smoothdeform_term`, a distinct bound
    name (`sdc_aff`) so the two never collide if ever nested in the same expression."""
    sigma_rotation = max(float(sigma_rotation), SIGMA_FLOOR)
    sigma_shear = max(float(sigma_shear), SIGMA_FLOOR)
    comp = smooth_deform_components_term(a, b)
    var = {"type": "Var", "name": "sdc_aff"}
    rotation = _dict_get(var, "rotation")
    shear = _dict_get(var, "shear")
    body = {"type": "Plus", "items": [
        {"type": "Div", "a": {"type": "Times", "items": [rotation, rotation]},
         "b": {"type": "Lit", "value": sigma_rotation ** 2}},
        {"type": "Div", "a": {"type": "Times", "items": [shear, shear]},
         "b": {"type": "Lit", "value": sigma_shear ** 2}},
    ]}
    return {"type": "Let", "name": "sdc_aff", "value": comp, "body": body}


def mahalanobis_affine_error_term(*, sigma_rotation: float, sigma_shear: float,
                                   sign_attr: str = "axs_heard_feat",
                                   word_attr: str = "axs_synth_feat") -> dict:
    """GRAPH-NATIVE twin of `mahalanobis_affine_term`, reading the same `s`/`w` free `Var`s off
    the same staged attrs `reweighted_smoothdeform_error_term` reads -- the caller binds `s`/`w`
    exactly as `abs_read.parse_marginal_pair_error_term`'s own contract requires."""
    a = {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": sign_attr}
    b = {"type": "Attr", "node": {"type": "Var", "name": "w"}, "key": word_attr}
    return mahalanobis_affine_term(a, b, sigma_rotation=sigma_rotation, sigma_shear=sigma_shear)


def supplement_pair_error_term(*, w_aff: float, sigma_rotation: float, sigma_shear: float,
                                part_w: float, sc_w: float, beta: float) -> dict:
    """THE 44b SUPPLEMENT recipe: `d' = existing_fused + w_aff * mahalanobis_affine`.
    `existing_fused` is `abs_read.parse_marginal_pair_error_term` reused VERBATIM (byte-identical
    to the standing GUARD's own three-term fusion -- smoothdeform + part_w*marginal_part +
    sc_w*shapecontext, ALL untouched) -- only a FOURTH additive term is introduced, at
    `w_aff` (derived from background spread-matching, never a bare unit weight). Needs `s`/`w`
    bound by the caller, the identical contract every verdict variant in this arc shares."""
    from domains import abs_read as ar
    return {"type": "Plus", "items": [
        ar.parse_marginal_pair_error_term(part_w=part_w, sc_w=sc_w, beta=beta),
        {"type": "Times", "items": [
            {"type": "Lit", "value": float(w_aff)},
            mahalanobis_affine_error_term(sigma_rotation=sigma_rotation,
                                           sigma_shear=sigma_shear)]}]}


def supplement_pair_error(scratch, query_node: int, cand_node: int, *, w_aff: float,
                           sigma_rotation: float, sigma_shear: float, part_w: float, sc_w: float,
                           beta: float) -> float:
    """ONE held evaluate of `supplement_pair_error_term` for a SPECIFIC (query, candidate) pair
    already staged into `scratch` by `abs_read.stage_parse_char` -- mirrors `reweighted_pair_
    error`'s own signature/dispatch exactly, the SUPPLEMENT arm's per-pair scorer."""
    native = getattr(scratch, "_inner", scratch)
    term = supplement_pair_error_term(w_aff=w_aff, sigma_rotation=sigma_rotation,
                                       sigma_shear=sigma_shear, part_w=part_w, sc_w=sc_w,
                                       beta=beta)
    return float(native.evaluate(term, {"s": query_node, "w": cand_node}) or 0.0)


def component_breakdown_term(*, sigma_rotation: float, sigma_shear: float, part_w: float,
                              sc_w: float, beta: float, sign_attr: str = "axs_heard_feat",
                              word_attr: str = "axs_synth_feat") -> dict:
    """ONE held evaluate returning the FOUR raw per-pair term values AS THEY ENTER a fused
    recipe -- `smoothdeform` (unit weight, the standing recipe's own first term), `part`
    (already `part_w`-scaled), `sc` (already `sc_w`-scaled), and `affine` (UNWEIGHTED -- the
    spread-matching stage applies its own derived `w_aff`, this breakdown reports the raw
    quantity) -- the exact four ingredients RUN 44b's spread-matching needs to measure. The
    `smoothdeform` value is read off `SmoothDeformComponents.total` (proven byte-identical to a
    live `SmoothDeformDist` evaluate by this module's own `test_smooth_deform_components_total_
    matches_live_smooth_deform_dist`), so the FFD fit the affine decomposition already performs
    is REUSED for the smoothdeform component rather than re-fit from scratch. `part`/`sc` are
    separate Rust ops (soft-min `PointSetDist` / `ShapeContextDist`) with no shared computation
    to reuse -- evaluated directly. A single `MkDict` (this codebase's alternating-[Lit(key),
    value] dict-literal Term, `ast_to_rule.py`'s own construction) bundles all four into ONE
    `evaluate()` call -- a mechanical Term composition, no Python-side score computed."""
    from domains import recognition_graph as rg
    sigma_rotation = max(float(sigma_rotation), SIGMA_FLOOR)
    sigma_shear = max(float(sigma_shear), SIGMA_FLOOR)
    a = {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": sign_attr}
    b = {"type": "Attr", "node": {"type": "Var", "name": "w"}, "key": word_attr}
    comp = smooth_deform_components_term(a, b)
    var = {"type": "Var", "name": "sdc_bd"}
    total = _dict_get(var, "total")
    rotation = _dict_get(var, "rotation")
    shear = _dict_get(var, "shear")
    affine = {"type": "Plus", "items": [
        {"type": "Div", "a": {"type": "Times", "items": [rotation, rotation]},
         "b": {"type": "Lit", "value": sigma_rotation ** 2}},
        {"type": "Div", "a": {"type": "Times", "items": [shear, shear]},
         "b": {"type": "Lit", "value": sigma_shear ** 2}},
    ]}
    part = {"type": "Times", "items": [{"type": "Lit", "value": float(part_w)},
                                        rg.marginal_part_error_term(beta)]}
    sc = {"type": "Times", "items": [{"type": "Lit", "value": float(sc_w)},
                                      rg.shapecontext_error_term()]}
    body = {"type": "MkDict", "items": [
        {"type": "Lit", "value": "smoothdeform"}, total,
        {"type": "Lit", "value": "part"}, part,
        {"type": "Lit", "value": "sc"}, sc,
        {"type": "Lit", "value": "affine"}, affine,
    ]}
    return {"type": "Let", "name": "sdc_bd", "value": comp, "body": body}


def component_breakdown(scratch, query_node: int, cand_node: int, *, sigma_rotation: float,
                         sigma_shear: float, part_w: float, sc_w: float, beta: float) -> dict:
    """ONE held evaluate of `component_breakdown_term` for a staged (query, candidate) pair --
    returns `{"smoothdeform": ..., "part": ..., "sc": ..., "affine": ...}`, all plain floats."""
    native = getattr(scratch, "_inner", scratch)
    term = component_breakdown_term(sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
                                     part_w=part_w, sc_w=sc_w, beta=beta)
    out = native.evaluate(term, {"s": query_node, "w": cand_node})
    return {k: float(v) for k, v in out.items()} if out else {}


def derive_w_aff(spread_smoothdeform: float, spread_part: float, spread_sc: float,
                  spread_affine: float) -> float:
    """THE spread-matching arithmetic (RUN 44b's central formula, design step 1): `w_aff =
    median(spread_smoothdeform, spread_part, spread_sc) / spread_affine` -- a MECHANICAL
    statistic derived from BACKGROUND measurement (a plain median/divide over already-computed
    numbers, mirrors this module's own `_std`/`_mean` reduction discipline in `calibrate_affine_
    sigmas`), never a tuned weight chosen against any eval outcome. `spread_affine` is floored at
    `SIGMA_FLOOR` -- an honest divide-by-~0 guard, not a tuned parameter, exactly like every
    other sigma floor in this module."""
    target = float(np.median([float(spread_smoothdeform), float(spread_part), float(spread_sc)]))
    denom = max(float(spread_affine), SIGMA_FLOOR)
    return target / denom


def save_waff(waff: dict, path: str) -> None:
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(waff, f, indent=1)


def load_waff(path: str) -> dict:
    import json
    with open(path) as f:
        return json.load(f)


# ===================================================================================================
# COMPONENT DECOMPOSITION -- a direct (non-Let) read of all fields for diagnostics/calibration
# (the calibration pass wants the RAW rotation/shear/bending numbers themselves, not a fused
# reweighted scalar -- a separate, simpler Term is clearer than unpacking a fused Plus).
# ===================================================================================================
def smooth_deform_components(native, a_points: list, b_points: list) -> dict:
    """ONE held `SmoothDeformComponents` evaluate over two already-computed point lists --
    returns the native Dict (`total`/`residual`/`dc`/`bending`/`rotation`/`shear`/`log_scale`/
    `tx`/`ty`/`n`) directly, no DictGet unwrapping needed since the caller wants every field."""
    term = {"type": "SmoothDeformComponents", "a": {"type": "Lit", "value": a_points},
            "b": {"type": "Lit", "value": b_points}}
    return native.evaluate(term, {})


# ===================================================================================================
# BACKGROUND CALIBRATION -- pairwise same-class affine-difference stds, THE SAME Term the eval
# fires, over the 5 LEARN alphabets (mirrors `exemplar_expand.calibrate_background`'s own
# "background = 5 LEARN alphabets, ALL classes" scope, but pairwise rather than per-glyph-vs-
# class-mean -- see this module's own top-of-file doc for why).
# ===================================================================================================
def calibrate_affine_sigmas(native, *, learn_n: int = DEFAULT_LEARN_N,
                             whole_n: int = DEFAULT_WHOLE_N,
                             max_pairs_per_class: int = MAX_PAIRS_PER_CLASS) -> dict:
    """For every character class in the first `learn_n` `omniglot_world.alphabets("background")`
    alphabets (>=2 drawers), evaluate `SmoothDeformComponents` on up to `max_pairs_per_class`
    pairs (drawer 0 vs drawers 1..`max_pairs_per_class`, whichever exist) of the SAME whole-
    figure trajectory feature (`omniglot_world.trajectory(path, whole_n, per_stroke=True)`,
    BYTE-IDENTICAL to what `abs_read.stage_parse_char` stages as `axs_heard_feat`/
    `axs_synth_feat`) -- pools the raw (signed) `rotation`/`shear` components across every pair
    into one population per dimension; the population's STANDARD DEVIATION is `sigma_rotation`/
    `sigma_shear`. A degenerate pair (`n == 0`, the Rust term's own honest-empty sentinel) is
    skipped. Mechanical aggregation only -- no decision, mirrors `exemplar_expand.calibrate_
    background`'s own "plain mean/std reduction" discipline. Returns a flat, JSON-serializable
    dict (`calibrate_or_load` freezes it)."""
    import domains.omniglot_world as ow

    alphs = ow.alphabets("background")[:learn_n]
    rotations, shears, bendings = [], [], []
    n_classes = 0
    n_pairs = 0

    for alph in alphs:
        for cdir in ow.characters(alph, "background"):
            files = ow.drawings(cdir)
            if len(files) < 2:
                continue
            n_classes += 1
            traj0 = ow.trajectory(files[0], whole_n, per_stroke=True)
            for j in range(1, min(len(files), max_pairs_per_class + 1)):
                trajj = ow.trajectory(files[j], whole_n, per_stroke=True)
                out = smooth_deform_components(native, traj0.tolist(), trajj.tolist())
                if not out or int(out.get("n", 0)) == 0:
                    continue
                n_pairs += 1
                rotations.append(float(out["rotation"]))
                shears.append(float(out["shear"]))
                bendings.append(float(out["bending"]))

    def _std(lst):
        return float(np.std(lst)) if lst else 0.0

    def _mean(lst):
        return float(np.mean(lst)) if lst else 0.0

    return dict(
        learn_alphabets=list(alphs), n_classes=n_classes, n_pairs=n_pairs,
        rotation_std=_std(rotations), rotation_mean=_mean(rotations),
        shear_std=_std(shears), shear_mean=_mean(shears),
        bending_mean=_mean(bendings), bending_std=_std(bendings),
        max_pairs_per_class=max_pairs_per_class, whole_n=whole_n,
    )


def save_calibration(calib: dict, path: str) -> None:
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(calib, f, indent=1)


def load_calibration(path: str) -> dict:
    import json
    with open(path) as f:
        return json.load(f)


def calibrate_or_load(native, path: str, *, learn_n: int = DEFAULT_LEARN_N,
                       whole_n: int = DEFAULT_WHOLE_N,
                       max_pairs_per_class: int = MAX_PAIRS_PER_CLASS) -> dict:
    """PRE-REGISTRATION FREEZE (mirrors `exemplar_expand.calibrate_or_load` exactly): read `path`
    back VERBATIM if it already exists (never recomputed, never adjusted against any later eval
    outcome); only computes+saves on the first, genuinely-absent call."""
    if os.path.exists(path):
        return load_calibration(path)
    calib = calibrate_affine_sigmas(native, learn_n=learn_n, whole_n=whole_n,
                                     max_pairs_per_class=max_pairs_per_class)
    save_calibration(calib, path)
    return calib


def sigma_from_calibration(calib: dict) -> tuple:
    """`(sigma_rotation, sigma_shear)`, each floored at `SIGMA_FLOOR` -- the ONLY read-off this
    module's callers need from a frozen calibration dict."""
    return (max(float(calib["rotation_std"]), SIGMA_FLOOR),
            max(float(calib["shear_std"]), SIGMA_FLOOR))


__all__ = [
    "DEFAULT_LEARN_N", "DEFAULT_WHOLE_N", "MAX_PAIRS_PER_CLASS", "SIGMA_FLOOR",
    "smooth_deform_components_term", "reweighted_smoothdeform_term",
    "reweighted_smoothdeform_error_term", "reweighted_pair_error_term", "reweighted_pair_error",
    "smooth_deform_components", "calibrate_affine_sigmas", "save_calibration",
    "load_calibration", "calibrate_or_load", "sigma_from_calibration",
    # RUN 44b -- spread-matched supplement.
    "mahalanobis_affine_term", "mahalanobis_affine_error_term", "supplement_pair_error_term",
    "supplement_pair_error", "component_breakdown_term", "component_breakdown",
    "derive_w_aff", "save_waff", "load_waff",
]
