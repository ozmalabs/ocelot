"""discrimination -- RUN 57: THE GRAPH-NATIVE DISCRIMINATION FACULTY. The creator's directive,
verbatim: "Building a richer discrimination capability graph native is its own reward. Have the
jabberwock do that."

THE CAPABILITY (a GENERAL recognition faculty, not Omniglot-specific): TRUST THE FEATURES THAT
SEPARATE CLASSES, not just the ones consistent WITHIN a class. Run 56's exact failure: its
precision was `1 / within-TRUE-class variance` (TIGHTNESS). Tightness OVER-TRUSTS a relation that
is tight for the true class but ALSO tight for FALSE classes -- within-class tightness is NOT
discriminative power (run 44b's law, now at the precision level). A feature that is identical for
every class carries ZERO information about WHICH class an instance is, yet tightness rates it
maximally trustworthy.

THE FIX = DISCRIMINABILITY as precision (FISHER's ratio): a feature's weight = its SEPARATING
power = BETWEEN-class variance / WITHIN-class variance.
  * A feature that varies BETWEEN classes but is tight WITHIN each  -> high between / low within ->
    HIGH discriminability -> trustworthy (it tells the classes apart).
  * A feature tight WITHIN the true class AND across FALSE classes  -> low between / low within  ->
    LOW discriminability -> distrust (run 56's failure case: tight but non-separating).
  * A feature that is noisy within a class                          -> large within -> low Fisher.

This module is PURE STATISTICS + held-Term/graph-edge storage (the SAME class of mechanical
reduction `unified_verdict.part_precision`, `relational_variation.slot_weights`, and
`compositional_verdict.reliability_weights` already are -- a variance ratio over already-collected
background residuals, never a ranking DECISION). The verdict ranking stays the held `Argmin`
(`unified_verdict.unified_verdict_pred`), fed these discriminability precisions INSTEAD of run 56's
tightness precisions -- "reuse the unified log-odds machinery verbatim; ONLY the precision VALUES
change" (the directive). The discriminability values are stored as graph-resident `log_weight`
EDGES (a `PartPrecision` frame + one `PartAxis` per part-type / one FrameAxis per relation slot),
the SAME run-30 precision-as-a-graph-edge representation `native_recognition.install_concept_frame`
uses -- so the precision the verdict reads is GRAPH DATA, not an external Python dict.

RICHER RELATIONS (component 2 -- more for the discrimination faculty to FIND): coarse pairwise pose
(`rel_x/y/o/s`, `cpose_x/y/o/s`) may simply not SEPARATE mouse-Omniglot classes. This module also
derives ATTACHMENT / JUNCTION structure -- WHERE two strokes physically connect (endpoint-to-
endpoint vs endpoint-to-midpoint vs no-contact, the topological connection BPL's relations encode),
purely from the stroke point arrays a decode already produced (the SAME mechanical re-packaging
`relational_variation.rel_by_k` performs). The discrimination faculty (component 1) then measures
WHICH of these richer relations separate.
"""
from __future__ import annotations

import math

import numpy as np

_VAR_EPS = 1e-9    # floor so a variance ratio never divides by an exact zero.


# --------------------------------------------------------------------------------------------- #
#  COMPONENT 1 -- FISHER DISCRIMINABILITY. Between-class variance / within-class variance. The
#  precision VALUE that replaces run 56's tightness. Pure arithmetic over already-computed
#  residuals -- the SAME reduction class as `unified_verdict.part_precision`, NOT a decision.
# --------------------------------------------------------------------------------------------- #
def fisher_ratio(groups: list) -> float:
    """Multi-class Fisher discriminability = BETWEEN-class variance / WITHIN-class variance over a
    list of per-class value groups (`groups[c]` = the values that class `c` takes for one feature).

        between = sum_c n_c (mean_c - grand_mean)^2 / N          (spread of the class MEANS)
        within  = sum_c n_c var_c              / N              (pooled spread WITHIN classes)
        fisher  = between / max(within, eps)

    A feature whose class means are far apart relative to its within-class scatter has a high ratio
    (it SEPARATES the classes); a feature whose class means coincide -- even if every class is
    razor-tight -- has between ~= 0 -> ratio ~= 0 (it does NOT separate, so it is untrustworthy).
    Empty / single-value groups contribute nothing. Fewer than two non-empty groups -> 0.0 (nothing
    to separate)."""
    arrs = [np.asarray(g, dtype=float) for g in groups if g is not None and len(g) > 0]
    if len(arrs) < 2:
        return 0.0
    ns = np.array([a.size for a in arrs], dtype=float)
    means = np.array([a.mean() for a in arrs], dtype=float)
    variances = np.array([a.var() for a in arrs], dtype=float)
    total_n = float(ns.sum())
    grand = float((ns * means).sum() / total_n)
    between = float((ns * (means - grand) ** 2).sum() / total_n)
    within = float((ns * variances).sum() / total_n)
    return between / max(within, _VAR_EPS)


def part_discriminability(true_residuals: list, false_residuals: list) -> float:
    """The recognition-time TWO-class Fisher over a part-type's residuals: how well does this part's
    residual SEPARATE the true candidate from the false candidates? `true_residuals` = the TRUE
    candidate's residual for one part-type across background episodes; `false_residuals` = the
    NON-true candidates' residuals (pooled). This is the drop-in replacement for
    `unified_verdict.part_precision` (which used `1/var(true_residuals)` -- tightness). Distrusts a
    part whose true-vs-false residuals OVERLAP (run 56's failure: `rel` tight for true but small for
    false too), even when the true-class residuals are razor-tight."""
    return fisher_ratio([true_residuals, false_residuals])


def tightness(true_residuals: list) -> float:
    """Run 56's precision, kept HERE for the falsifier's side-by-side ranking comparison only:
    `1 / max(var(true_residuals), eps)`. NOT used in the ARM-D verdict."""
    arr = np.asarray(true_residuals, dtype=float)
    if arr.size == 0:
        return 1.0 / _VAR_EPS
    return float(1.0 / max(float(np.var(arr)), _VAR_EPS))


def slot_discriminability(per_class_slot_values: dict) -> dict:
    """Per-SLOT Fisher over the codebook. `per_class_slot_values` = `{slot: {class: [values...]}}`
    -- for each slot the values every drawer of every class takes. Returns `{slot: fisher_ratio}`.
    The discriminability twin of `relational_variation.slot_weights` (which returned 1/pooled-within
    -- tightness). Reuse verbatim, ONLY the ratio changes (add the between term)."""
    return {slot: fisher_ratio(list(byclass.values()))
            for slot, byclass in per_class_slot_values.items()}


# --------------------------------------------------------------------------------------------- #
#  GRAPH-NATIVE STORAGE -- the precision as a graph EDGE (run 30 / native_recognition pattern).
#  The verdict reads the precision from a `log_weight` edge, NOT an external Python float. Storing
#  is mechanical host I/O (one node + one set_attr, the SAME as `install_concept_frame`); reading
#  is `exp(log_weight)` (the sanctioned "unit conversion, not a decision").
# --------------------------------------------------------------------------------------------- #
_PART_FRAME = "part_precision:discriminability"
_LOG_EPS = 1e-12


def install_part_precisions(sub, precisions: dict):
    """Write each part-type's discriminability precision as a graph-resident FrameAxis `log_weight`
    EDGE, via the SAME `frame_weights` Frame/FrameAxis vocabulary `native_recognition.
    install_concept_frame` (run 30/55) uses -- one `Frame` node + one `FrameAxis` per part-type
    (`whole`/`stroke`/`rel`), `log_weight` SET to `log(max(precision, eps))`. Returns the frame node
    id. Mechanical host I/O (find-or-create + set_attr), never arithmetic-on-a-decision."""
    from domains import frame_weights as fw
    frame = fw.ensure_frame(sub, _PART_FRAME)
    for part, prec in precisions.items():
        axis = fw.ensure_axis(sub, frame, part, scope="part", kind=part)
        sub.set_attr(axis, "log_weight", float(math.log(max(float(prec), _LOG_EPS))))
    return frame


def read_part_precisions(sub, frame, parts=("whole", "stroke", "rel")) -> dict:
    """Read the discriminability precisions BACK from the graph FrameAxis `log_weight` edges as
    `{part: exp(log_weight)}` -- the value the verdict actually consumes comes from GRAPH DATA, not
    the Python dict passed to `install_part_precisions`. `exp(log_weight)` is the sanctioned unit
    conversion (`frame_weights.axis_weight`'s own idiom), not a decision."""
    from domains import frame_weights as fw
    return {part: float(math.exp(fw.axis_log_weight(sub, frame, part))) for part in parts}


# --------------------------------------------------------------------------------------------- #
#  COMPONENT 2 -- RICHER RELATIONS: attachment / junction structure. WHERE two strokes connect,
#  the topological content coarse pairwise pose cannot carry. Pure geometry over the stroke point
#  arrays a decode already produced (the SAME re-packaging `relational_variation.stroke_points_only`
#  does) -- emitted as ShapeSignature-format relation entries alongside the existing `rel`/`cpose`.
# --------------------------------------------------------------------------------------------- #
# Attachment class codes (the junction TYPE, a small discrete alphabet -- the discriminable content):
#   0 = no contact          (strokes do not touch)
#   1 = endpoint-endpoint    (two stroke ENDS meet -- a corner / chain join)
#   2 = endpoint-midpoint    (one stroke's END lands on the OTHER's interior -- a T-junction)
#   3 = midpoint-midpoint    (interiors cross -- an X-crossing)
ATTACH_NONE, ATTACH_EE, ATTACH_EM, ATTACH_MM = 0, 1, 2, 3
_ENDPOINT_FRAC = 0.20      # a contact within this arc-length fraction of a stroke's end is "at the
                           # endpoint"; beyond it is "at the midpoint/interior". Documented, not tuned.


def _as_xy(points: list) -> np.ndarray:
    """Accept `[(x,y), ...]` or `[[x,y,...], ...]` (both list and tuple, the standing gotcha) and
    return an `(n,2)` float array of just the x,y coordinates."""
    out = []
    for p in points:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append((float(p[0]), float(p[1])))
    return np.asarray(out, dtype=float) if out else np.zeros((0, 2), dtype=float)


def _endpoint_or_mid(idx: int, n: int) -> bool:
    """True if arc-position `idx` (0..n-1) is within `_ENDPOINT_FRAC` of EITHER end -> an ENDPOINT
    contact; False -> an interior/MIDPOINT contact."""
    if n <= 1:
        return True
    frac = idx / (n - 1)
    return frac <= _ENDPOINT_FRAC or frac >= (1.0 - _ENDPOINT_FRAC)


def attachment_class(points_a: list, points_b: list, contact_frac: float = 0.12) -> int:
    """The junction TYPE between two strokes, computed from their point arrays: find the closest
    pair of points; if their separation exceeds `contact_frac` of the two strokes' combined
    diagonal, there is NO contact; otherwise classify by whether each contact point sits at its
    stroke's ENDPOINT or MIDPOINT. Pure geometry -- one nearest-pair scan, no decision.

    `contact_frac` is scale-relative (fraction of the bounding diagonal of the two strokes
    together), so the class is translation/scale-invariant like the pose relations."""
    a = _as_xy(points_a)
    b = _as_xy(points_b)
    if a.shape[0] == 0 or b.shape[0] == 0:
        return ATTACH_NONE
    both = np.vstack([a, b])
    diag = float(np.hypot(*(both.max(0) - both.min(0)))) or 1.0
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)     # (na, nb) pairwise distances.
    ia, ib = np.unravel_index(int(np.argmin(d)), d.shape)         # nearest pair (a SELECTION).
    if float(d[ia, ib]) > contact_frac * diag:
        return ATTACH_NONE
    a_end = _endpoint_or_mid(int(ia), a.shape[0])
    b_end = _endpoint_or_mid(int(ib), b.shape[0])
    if a_end and b_end:
        return ATTACH_EE
    if a_end != b_end:
        return ATTACH_EM
    return ATTACH_MM


def attachment_relations(stroke_point_arrays: list) -> list:
    """ShapeSignature-format ATTACHMENT relations for one character: for every unordered stroke
    pair `(i, j)`, one `["attach", i, j, cls]` relation carrying the junction class. Emitted
    ALONGSIDE the existing `rel`/`cpose` relations (strictly additive), so the discrimination
    faculty can measure whether junction structure separates classes the coarse pose relations do
    not. `stroke_point_arrays` = `[points_i, ...]` (the `relational_variation.stroke_points_only`
    output). Deterministic pair order; no decision."""
    rels = []
    n = len(stroke_point_arrays)
    for i in range(n):
        for j in range(i + 1, n):
            cls = attachment_class(stroke_point_arrays[i], stroke_point_arrays[j])
            rels.append(["attach", i, j, cls])
    return rels


def attach_by_pair(sig_or_rels: list) -> dict:
    """`{(i, j): cls}` from a list of `["attach", i, j, cls]` relations (both list and tuple)."""
    out = {}
    for r in sig_or_rels:
        if isinstance(r, (list, tuple)) and len(r) >= 4 and r[0] == "attach":
            out[(int(r[1]), int(r[2]))] = int(r[3])
    return out


def junction_profile(stroke_point_arrays: list) -> dict:
    """A character's ALIGNMENT-FREE junction feature: the FRACTION of its stroke pairs in each
    attachment class (`{"frac_none": .., "frac_ee": .., "frac_em": .., "frac_mm": ..}`). Order- and
    stroke-count-invariant (a histogram over pairs), so it pools across drawers with different
    stroke segmentations WITHOUT the per-pair alignment coarse pose needs -- the topological content
    as a small fixed feature vector the discrimination faculty can score. A lone stroke (no pairs)
    yields all-zero fractions."""
    rels = attachment_relations(stroke_point_arrays)
    n = len(rels)
    counts = {ATTACH_NONE: 0, ATTACH_EE: 0, ATTACH_EM: 0, ATTACH_MM: 0}
    for r in rels:
        counts[int(r[3])] += 1
    denom = float(n) if n else 1.0
    return {"frac_none": counts[ATTACH_NONE] / denom, "frac_ee": counts[ATTACH_EE] / denom,
            "frac_em": counts[ATTACH_EM] / denom, "frac_mm": counts[ATTACH_MM] / denom}


JUNCTION_SLOTS = ("frac_none", "frac_ee", "frac_em", "frac_mm")


__all__ = ["fisher_ratio", "part_discriminability", "tightness", "slot_discriminability",
           "install_part_precisions", "read_part_precisions", "attachment_class",
           "attachment_relations", "attach_by_pair", "junction_profile", "JUNCTION_SLOTS",
           "ATTACH_NONE", "ATTACH_EE", "ATTACH_EM", "ATTACH_MM"]
