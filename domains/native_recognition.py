"""native_recognition -- RUN 55: NATIVE GRAPH RECOGNITION (the substrate-as-designed
realization of the loop-flip). The creator's spec, verbatim: "this is the entire point of log
indexes relative admissibility grammar based graphs."

THE DISEASE (runs 45/49/51/54/54b): the 80.5 verdict is an EXTERNAL Python scoring function
(SC+TPS computes a geometric scalar OUTSIDE the grammar). You cannot attach a graph-native
concept to an external scalar -- that is why every static bolt-on/reweight/grain-sum failed. THE
FIX = make recognition NATIVE: the concept is a Gamma-admissible subgraph; recognition of a query
is DECODED against it as an admissible DERIVATION; the derivation cost is weighted by the frame's
own LOG-RELATIVE PRECISION EDGES (run 30's log-odds weight edges, VALUED by run 50's tightness).

The four properties each do a job:
  * ADMISSIBILITY GRAMMAR (Gamma): the greedy per-stroke correspondence IS the admissible
    derivation -- ONE Gamma-pruned pass per (query, candidate), never a per-query MCMC search over
    concept parameters. Gamma prunes the derivation -> constrained/cheap (the amortization bet).
  * RELATIVE: per-INSTANCE precision. A relation's precision is read RELATIVE to its SIBLINGS in
    THIS derivation context (the log-weights CENTERED over the parts present in this one
    derivation), never a static per-TYPE constant -- the exact thing static grain weights
    (runs 50/54/54b) could not do. Because different candidates align to different stroke sets,
    the SAME relation slot gets a DIFFERENT effective precision across derivations.
  * LOG: precision composes ADDITIVELY -- the centering is a subtraction in log-space; each part's
    contribution is `exp(log_precision - mean_log_precision) * residual`.
  * GRAPHS: whole + strokes + relations COEXIST as parts of ONE derivation; recognition is a
    derivation IN the graph, and the precision is read from graph-resident FrameAxis edges (run 30).

WHAT THIS MODULE IS (CLAUDE.md legality): a WORLD-ADAPTER-LEGAL set of Term builders + mechanical
graph reads. `install_concept_frame` EMITS graph data (a Frame + one FrameAxis per relation,
`log_weight` = log of the run-50 tightness -- the run-30 precision-as-a-graph-edge representation);
`native_relation_residual` reads those log-weight EDGES back (`frame_weights.axis_log_weight`),
centers them per-instance (arithmetic over already-fetched scalars -- the SAME "representation
conversion, not a decision" `frame_weights.axis_weight`'s own `exp(log_weight)` is sanctioned as),
and composes the per-part residuals inside ONE HELD Term (`Plus`/`Times`/`Exp`/`Div`). The RANKING
DECISION stays the held `Argmin` in `compositional_verdict.verdict_pred` -- no Python
min/max/argmin/sort anywhere here. The geometry (SC+TPS) is DEMOTED to a per-part primitive
(`compositional_verdict.per_stroke_residual` / `abs_read.parse_marginal_pair_error`), never the
verdict.

THE ISOLATED EXPERIMENT (vs run 54b): run 54b's `relation_residual` used
`relational_variation.relational_distance` -- STATIC per-TYPE slot weights normalized to a GLOBAL
mean of 1. This module's `native_relation_residual` is byte-identical EXCEPT the slot precisions
are read from graph EDGES and CENTERED per-instance (relative to the relation parts present in THIS
derivation). Plugged into the SAME `compositional_verdict.verdict_pred` held-Argmin combination
with the SAME reliability level weights, the ONLY thing that changes from run 54b is per-TYPE ->
per-INSTANCE precision -- so the paired McNemar isolates EXACTLY the per-instance-precision
mechanism the creator's spec predicts fixes the run-50 geo-wrong conditional slice.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

from domains import abs_read as ar
from domains import frame_weights as fw
from domains import relational_variation as rv
from scripts import jabberwock_omniglot_run36_failures as run36
from scripts import jabberwock_omniglot_run39_motorplan as run39

REL_SLOTS = rv.REL_SLOTS          # rel_x, rel_y, rel_o, rel_s
CPOSE_SLOTS = rv.CPOSE_SLOTS       # cpose_x, cpose_y, cpose_o, cpose_s
_MIN_TIGHTNESS = 1e-6              # floor so log(tightness) never diverges (honest, documented).
_GEO_EPS = 1e-3                    # floor so log(geo_residual) never diverges on a perfect match.
_STROKE_N_POINTS = 24             # per-stroke SC+TPS resampling (matches compositional_verdict).
STRUCTURAL_UNMATCHED_UNITS = rv.STRUCTURAL_UNMATCHED_WEIGHT_UNITS   # reuse run 50's own convention.


# --------------------------------------------------------------------------- #
#  CONCEPT SUBGRAPH -- the candidate class as a Gamma-admissible frame subgraph.
#  Graph DATA EMISSION from an already-decoded exemplar signature (legal seed-builder work,
#  CLAUDE.md): one FrameAxis per arrangement relation the exemplar's composed signature carries,
#  `log_weight` = log of the run-50 PRECISION (tightness) for that slot's kind -- the run-30
#  "weights are edges, log scaled" representation, so the precision LIVES in the graph and the
#  derivation reads it back from an EDGE rather than a Python dict.
# --------------------------------------------------------------------------- #
def concept_frame_key(name: str) -> str:
    return f"concept_frame:{name}"


def _rel_axis_name(k, slot: str) -> str:
    return f"rel:{k}:{slot}"


def install_concept_frame(sub, name, cand_sig: list, tightness: dict) -> int:
    """Install candidate `name`'s arrangement as a Frame subgraph in `sub` (a scratch Substrate
    wrapper). `cand_sig` = the exemplar's composed signature (`gate.decode_char_signature(...)
    ["composed_sig"]`); `tightness` = run 50's frozen per-slot precision
    (`results/run50_checkpoints/learn_relational.json`'s `weights`, READ-ONLY -- 8 slots). One
    `FrameAxis` per `rel:<k>:<slot>` present in the signature plus one per present `cpose_*`; each
    axis's `log_weight` is SET to `log(max(tightness[slot], eps))` via `sub.set_attr` (mechanical
    graph write of an already-known precision, never a re-decision). Idempotent (find-or-create by
    key/name). Returns the Frame node id."""
    frame_node = fw.ensure_frame(sub, concept_frame_key(name))
    rel = rv.rel_by_k(cand_sig)                     # {k: (x_q, y_q, o_q, s_q)}
    for k in rel:
        for slot in REL_SLOTS:
            axis = fw.ensure_axis(sub, frame_node, _rel_axis_name(k, slot),
                                  scope="quantum", kind=slot)
            sub.set_attr(axis, "log_weight",
                         math.log(float(np.clip(tightness[slot], _MIN_TIGHTNESS, None))))
    cpose = rv.cpose_values(cand_sig)
    for slot in CPOSE_SLOTS:
        if slot in cpose:
            axis = fw.ensure_axis(sub, frame_node, slot, scope="quantum", kind=slot)
            sub.set_attr(axis, "log_weight",
                         math.log(float(np.clip(tightness[slot], _MIN_TIGHTNESS, None))))
    return frame_node


# --------------------------------------------------------------------------- #
#  PER-INSTANCE RELATIVE PRECISION -- the load-bearing distinction from static per-TYPE weights.
#  Centre the per-part log-precisions over the parts present in THIS derivation, then exponentiate:
#  `exp(log_precision_part - mean_log_precision_this_derivation)`. The geometric mean of these is
#  exactly 1, so a part more precise than this derivation's typical part reads > 1, a less-precise
#  part < 1 -- but the reference (the mean) is THIS derivation's own sibling set, so the SAME slot
#  gets a DIFFERENT effective precision when the surrounding matched parts differ (per-instance).
# --------------------------------------------------------------------------- #
def relative_precisions(log_precisions: list) -> list:
    """`[exp(lp - mean(lp)), ...]` -- per-instance relative precision (arithmetic over
    already-fetched log-weight EDGE values, the SAME class of representation conversion
    `frame_weights.axis_weight`'s own `exp(log_weight)` is documented to be, not a decision).
    An empty list returns `[]`."""
    if not log_precisions:
        return []
    mean_lp = float(np.mean(log_precisions))
    return [math.exp(lp - mean_lp) for lp in log_precisions]


def _derivation_parts(sub, native, frame_node, q_stroke_points: list, q_sig: list,
                      c_stroke_points: list, c_sig: list):
    """ONE admissible derivation pass. Normalize + greedy-match the query strokes to the concept's
    (`run36._normalize_glyph` + the FIXED falsy-zero-safe `run39.greedy_match` -- the SAME single
    pass `compositional_verdict.per_stroke_residual` uses; NO search over concept parameters), and
    for each matched stroke pair compute its GEOMETRIC ADMISSIBILITY (the per-stroke SC+TPS residual
    -- the strong geometry DEMOTED to a per-part primitive: 'is this query-stroke admissibly this
    concept-stroke'). Build the relation parts: each `rel:<c_idx>:<slot>` part's LOG-PRECISION is

        axis_log_weight(EDGE)  +  log_admissibility(this stroke pair)
        = base per-kind tightness (graph edge)  -  log(geo_residual + eps)

    -- so a relation ANCHORED ON A STROKE THAT ADMISSIBLY FITS the concept reads a HIGHER precision,
    and the SAME slot reads a DIFFERENT precision across derivations (per-INSTANCE: the generative
    concept 'predicts each part with instance-specific precision', run 54b's own licensed reading).
    LOG so it composes additively; the graph EDGE is the base, the admissibility is this derivation's
    own. cpose parts have no stroke pair -> base (edge) precision only. Returns
    `(parts, names, unmatched_frac)` with `parts = [(log_precision, mismatch), ...]` and `names` the
    parallel axis-name list (for the per-instance-precision diagnostic). Falsy-zero-safe throughout."""
    q_pts = rv.stroke_points_only(q_stroke_points)
    c_pts = rv.stroke_points_only(c_stroke_points)
    if not q_pts or not c_pts:
        return [], [], 0.0
    q_norm, _, _ = run36._normalize_glyph([np.asarray(s, dtype=float) for s in q_pts])
    c_norm, _, _ = run36._normalize_glyph([np.asarray(s, dtype=float) for s in c_pts])
    mapping = run39.greedy_match(native, q_norm, c_norm)     # {c_idx: q_idx}
    q_rel = rv.rel_by_k(q_sig)
    c_rel = rv.rel_by_k(c_sig)

    parts, names = [], []
    for c_idx, q_idx in mapping.items():
        qps = ar.whole_figure_point_set([(q_norm[q_idx], None)], _STROKE_N_POINTS)
        cps = ar.whole_figure_point_set([(c_norm[c_idx], None)], _STROKE_N_POINTS)
        if qps is None or cps is None:
            log_admiss = 0.0
        else:
            geo = float(native.evaluate(ar.sctps_verdict_term(qps, cps), {}) or 0.0)
            log_admiss = -math.log(geo + _GEO_EPS)          # low residual -> high precision.
        qv = q_rel.get(q_idx)
        cv = c_rel.get(c_idx)
        if qv is None or cv is None:
            continue
        for slot, a, b in zip(REL_SLOTS, qv, cv):
            nm = _rel_axis_name(c_idx, slot)
            lp = fw.axis_log_weight(sub, frame_node, nm) + log_admiss
            parts.append((lp, 1.0 if a != b else 0.0))
            names.append(nm)

    q_cpose = rv.cpose_values(q_sig)
    c_cpose = rv.cpose_values(c_sig)
    for slot in CPOSE_SLOTS:
        a, b = q_cpose.get(slot), c_cpose.get(slot)
        if a is None or b is None:
            continue
        lp = fw.axis_log_weight(sub, frame_node, slot)
        parts.append((lp, 1.0 if a != b else 0.0))
        names.append(slot)

    n_matched = len(mapping)
    n_unmatched = (len(q_norm) - n_matched) + (len(c_norm) - n_matched)
    n_total = len(q_norm) + len(c_norm)
    unmatched_frac = (n_unmatched / n_total) if n_total else 0.0
    return parts, names, unmatched_frac


def _relation_cost_term(parts: list, structural: float) -> dict:
    """ONE held Term: `Plus([ Div(Plus([Times([Exp(Plus([Lit(lp), Lit(-mean_lp)])), Lit(mm)]),
    ...]), Lit(n_parts)), Lit(structural) ])`. The `Exp(Plus(Lit(lp), Lit(-mean_lp)))` reads the
    per-instance LOG-RELATIVE precision INSIDE the Term (log-additive centering); the `Times`
    multiplies it by the part's mismatch residual; `Div` by the part count keeps the scale
    comparable to run 50's own mean-of-weighted-mismatch; the outer `Plus` adds the structural
    unmatched term. No ranking here -- pure composition (the ranking is the held `Argmin` in
    `compositional_verdict.verdict_pred`)."""
    if not parts:
        return {"type": "Lit", "value": float(structural)}
    mean_lp = float(np.mean([lp for lp, _mm in parts]))
    items = []
    for lp, mm in parts:
        items.append({"type": "Times", "items": [
            {"type": "Exp", "arg": {"type": "Plus", "items": [
                {"type": "Lit", "value": float(lp)},
                {"type": "Lit", "value": float(-mean_lp)}]}},
            {"type": "Lit", "value": float(mm)}]})
    mean_part = {"type": "Div", "a": {"type": "Plus", "items": items},
                 "b": {"type": "Lit", "value": float(len(parts))}}
    return {"type": "Plus", "items": [mean_part, {"type": "Lit", "value": float(structural)}]}


def native_relation_residual(sub, native, frame_node, query_stroke_points: list, query_sig: list,
                             cand_stroke_points: list, cand_sig: list) -> float:
    """THE NATIVE per-instance-precision arrangement residual (run 54b's `relation_residual`
    twin, but per-INSTANCE from graph edges). Align query strokes to the candidate's (`_derivation_
    parts` -> the FIXED, falsy-zero-safe `run39.greedy_match`, ONE pass, no search), collect the
    relation parts with their LOG-PRECISION read from the concept
    frame's graph EDGES (modulated per-instance by each part's own geometric admissibility), and
    evaluate the held per-instance-relative cost Term. `sub` holds the concept frame (its FrameAxis
    log_weight edges); `native` evaluates the Term + the alignment. Lower = the candidate's
    arrangement better explains the query's. Returns `structural` alone (still an honest
    non-fabricated value) when no relation part is usable."""
    parts, _names, unmatched_frac = _derivation_parts(
        sub, native, frame_node, query_stroke_points, query_sig, cand_stroke_points, cand_sig)
    structural = STRUCTURAL_UNMATCHED_UNITS * unmatched_frac
    return float(native.evaluate(_relation_cost_term(parts, structural), {}) or 0.0)


def relation_part_log_precisions(sub, native, frame_node, query_stroke_points: list,
                                 query_sig: list, cand_stroke_points: list, cand_sig: list) -> dict:
    """REPORTING/DIAGNOSTIC read (no decision): the per-part `(axis_name -> log_precision)` and the
    derived per-instance RELATIVE precisions for one (query, candidate) derivation -- used by the
    gate to PROVE the same relation slot gets different effective precision across derivations
    (the load-bearing per-instance evidence). Mirrors `native_relation_residual`'s own part
    collection exactly (admissibility-modulated log-precision included)."""
    parts, names, _uf = _derivation_parts(
        sub, native, frame_node, query_stroke_points, query_sig, cand_stroke_points, cand_sig)
    lps = [lp for lp, _mm in parts]
    rp = relative_precisions(lps)
    return {"axis_names": names, "log_precisions": lps,
            "relative_precisions": rp, "n_parts": len(names)}


__all__ = ["REL_SLOTS", "CPOSE_SLOTS", "STRUCTURAL_UNMATCHED_UNITS", "concept_frame_key",
           "install_concept_frame", "relative_precisions", "native_relation_residual",
           "relation_part_log_precisions"]
