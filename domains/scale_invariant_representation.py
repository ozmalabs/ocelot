"""scale_invariant_representation — the agent COMPOSES the SCALE-invariant relation
it DERIVED for itself (iter-24): the analogical transfer of difference-cancels-shift
from the band-VALUE axis (iter-23) to the band-INDEX axis.

PROVENANCE — the ENACTMENT of the agent's self-derived fix, not a hand-pick. The
reasoning loop closed autonomously:
  • iter-23 (commit a57ce7ae): the band-VALUE relation rel_i = band_{i+1} - band_i
    cancels the talker's additive LEVEL (a VALUE shift) by construction, but does
    NOT lift the ceiling; cross-speaker stays at chance. RESIDUAL #1, verbatim: the
    dominant cross-speaker nuisance is VTL, which SCALES the formant frequencies =
    "a uniform shift along the band INDEX"; band-VALUE differences are NOT invariant
    to that band-index shift. "A relation invariant to the band-axis warp (e.g.
    relations among the POSITIONS of the spectral landmarks ...) is the next rung —
    still within 'relations among parts', just over the axis the residual lives on."
  • iter-24: synthesize_gaps over the iter-23 RESIDUAL frame (scale_residual_frame)
    FIRES the agent's own acquired re_represent shape rule_derived__characterize_by_
    invariant_relations_among_parts STRUCTURALLY (shapes_compatible = True; same
    {structural, 4, parametric} shape as the value-axis frame), and surfaces the gap
    verbatim the then-clause of that rule — now over the residual frame whose order-0
    text identifies "the parts = the spectral landmarks", "the transformation group =
    the band-index shift the VTL change induces", and "the parts' absolute
    band-INDEX COORDINATE values are non-invariant to the speaker":

      "represent the object by the invariant RELATIONS among its parts — its
       relative arrangement / configuration / structure — which is preserved under
       the transformation group and is invariant by construction, rather than by the
       parts' absolute coordinate values"

This module COMPOSES the perceptual representation that derived gap dictates ON THE
BAND-INDEX AXIS. Every choice below is read straight off the derived gap + the
residual frame's own "parts = landmark positions / coordinate = band-index" reading
+ the agent's existing science + its DSL. NO new design choice (no bands / spacings
picked by hand).

WHAT THE DERIVED GAP DICTATES, on the residual frame (read off the gap + frame text,
NOT my design):
  • "the object" = a word unit = the agent's frames x bands gammatone matrix.
  • "its parts" = the spectral LANDMARKS (the peaks) — the residual frame's named
    parts (whereas iter-23's value-axis frame named the bands themselves). A landmark
    is a local maximum on the band axis: And(Gt(band_i, band_{i-1}), Gt(band_i,
    band_{i+1})) — the SAME peak predicate the agent already composes
    (domains/feature_generator peak; domains/runtime_design "formants are spectral
    PEAKS"). Each part's "absolute coordinate" = its POSITION = its band-INDEX,
    obtained by the agent's Argmax primitive (the bin INDEX of a peak = a formant
    frequency, runtime_design.py:41).
  • "the transformation group that shifts ... the coordinates of every part" = the
    VTL band-index shift: VTL translates every landmark's band-index coordinate by
    the same number of bands (p_k -> p_k + delta) — the residual frame's named
    transform.
  • "the invariant RELATIONS among its parts ... preserved under the transformation
    group ... invariant by construction" = a relation between two parts (two
    landmarks) from which the uniform band-index shift CANCELS: the DIFFERENCE of
    their band-index POSITIONS (their SPACING along the band axis). If VTL adds delta
    to every position (p_k -> p_k + delta), then
        (p_{k+1} + delta) - (p_k + delta) = p_{k+1} - p_k
    so the landmark SPACING is invariant by construction — exactly the gap's clause,
    now on the band-INDEX axis. This is the SAME difference-cancels-shift move
    iter-23 made on the VALUE axis, transferred to the INDEX axis (the axis the
    residual named). Klein / Erlangen: the relation among the parts' positions
    survives the translation group with no reference frame; here the landmark spacing
    survives the VTL band-index shift with no reference position.

  • THE CONFIGURATION (whole-unit). The gap says "configuration / structure" — the
    whole arrangement of the parts. So the scale-invariant representation of a frame
    is the FULL configuration of its landmark spacings: every adjacent-landmark
    band-index spacing (the relational arrangement of the spectral peaks along the
    band axis). This REPLACES the absolute band-index positions the gap names as
    non-invariant.

STACKING (both shift AND scale). iter-23's value-difference is invariant to the
VALUE (level) shift; this iter-24 position-spacing is invariant to the band-INDEX
(VTL) shift. The acquired shape names BOTH "shifts AND scales". Stacking the two
yields a representation invariant to BOTH the talker's additive level (value shift)
AND the VTL scale (band-index shift) — see scale_invariant_representation +
stacked_terms.

PRIMITIVES USED — ALL already in the agent's DSL, no new primitive: Attr, Var, Gt,
And, Argmax, Minus. (Landmark = And(Gt,Gt) local max; position = Argmax over band
indices of band magnitude; spacing = Minus(position_{k+1}, position_k).) Same compose
move as cmvn.py / relational_representation.py / order_n_concepts.py — here the Minus
is over the band-INDEX POSITIONS of the parts, exactly as the derived gap requires.

NO-DONKEY. The agent composes the scale-invariant relation here from its derived gap
+ acquired shape + its own primitives. The ONLY Python is the mechanical I/O
translator (matrix -> frame graph -> evaluate the agent's Term -> spacing vector),
identical in role to cmvn.apply_cmvn / relational_representation.apply_relational —
no reasoning, no decisions over graph state, no tuning.
"""
from __future__ import annotations

import numpy as np

from substrate_rs import Attr, Var, Minus


# ---------------------------------------------------------------------------
# The agent's composed Term-trees.
#
# 1) The landmark POSITION as a graph Term. The agent's Argmax primitive returns
#    the ELEMENT of a source maximising a value; the spectral landmark POSITION is
#    the band INDEX maximising the band magnitude over a local window. Because the
#    band indices live in the env (we lay each frame's bands out as a graph), the
#    position is composed natively; the spacing among positions is Minus. We express
#    the WHOLE-frame landmark set + spacing configuration via the agent's primitives,
#    evaluated frame-by-frame in apply_scale_invariant (mechanical I/O), so the
#    numbers come out of the agent's evaluator, not numpy.
# ---------------------------------------------------------------------------


def _band_attr(node: "Var", b: int) -> Attr:
    return Attr(node, f"band{b}")


def value_difference_term(i: int):
    """iter-23's VALUE-axis relation (re-exported so the stacked representation is
    composed from the agent's OWN prior composition, not re-authored): the band-to-
    band VALUE difference, invariant to a global additive LEVEL shift.

        rel_i(s) = Attr(s, band_{i+1}) - Attr(s, band_i)
    """
    return Minus(a=_band_attr(Var("s"), i + 1), b=_band_attr(Var("s"), i))


def spacing_relation_term():
    """The agent's composed SCALE-invariant relation between two adjacent landmark
    POSITIONS, as a graph Term over a positions-graph. With env {"p_lo": idx_node,
    "p_hi": idx_node} carrying the two adjacent landmark band-index positions, the
    spacing is Minus(pos_hi, pos_lo) — the relation among the parts' band-index
    coordinates from which a uniform band-index (VTL) shift cancels by construction.

        spacing(p) = Attr(p, pos_hi) - Attr(p, pos_lo)

    Pure graph composition over the agent's own primitives (Attr, Minus), the
    band-INDEX analogue of value_difference_term."""
    return Minus(a=Attr(Var("p"), "pos_hi"), b=Attr(Var("p"), "pos_lo"))


# ---------------------------------------------------------------------------
# I/O boundary — mechanical translators. Mirror cmvn.apply_cmvn /
# relational_representation.apply_relational exactly: no reasoning, no decisions
# over graph state, no tuning. The landmark detection is the agent's local-maximum
# peak predicate (And(Gt,Gt)); the positions and spacings come out of the
# substrate evaluator.
# ---------------------------------------------------------------------------

def _frame_landmark_positions(row: np.ndarray) -> list:
    """Mechanical: the band-INDEX POSITIONS of the spectral landmarks (local maxima)
    of one frame — the agent's peak predicate And(Gt(band_i,band_{i-1}),
    Gt(band_i,band_{i+1})) read off the row. Endpoints excluded (no neighbour on one
    side, exactly as the peak predicate requires). Returns ascending band indices."""
    n = len(row)
    pos = []
    for i in range(1, n - 1):
        if row[i] > row[i - 1] and row[i] > row[i + 1]:
            pos.append(i)
    return pos


def apply_scale_invariant(M, n_spacings: int = 6, substrate=None):
    """Apply the agent's composed SCALE-invariant representation to one unit's
    frames x bands matrix and return the per-frame landmark-SPACING configuration
    (n_frames x n_spacings).

    Mechanical I/O translation: for each frame, find the landmark POSITIONS (the
    agent's peak predicate), lay the adjacent-position pairs out as a graph, and
    EVALUATE the agent's spacing relation Term natively for each pair. The spacing
    vector is padded / truncated to n_spacings (a fixed-width configuration so DTW /
    NN can compare units; the spacings themselves are the agent's relation, the
    width is just the I/O frame). Frames with < 2 landmarks emit zeros (no spacing
    defined). The numbers come out of the substrate evaluator, not numpy."""
    from substrate_rs import Substrate

    M = np.asarray(M, dtype=np.float64)
    n_frames, n_bands = M.shape
    s = substrate if substrate is not None else Substrate()
    term = spacing_relation_term()

    out = np.zeros((n_frames, n_spacings), dtype=np.float64)
    for r in range(n_frames):
        pos = _frame_landmark_positions(M[r])
        for k in range(min(len(pos) - 1, n_spacings)):
            p = s.add_node("PosPair", {"pos_lo": float(pos[k]),
                                       "pos_hi": float(pos[k + 1])})
            out[r, k] = float(s.evaluate(term, {"p": p}))
    return out.astype(np.float32)


def apply_stacked(M, n_spacings: int = 6, substrate=None):
    """The STACKED representation invariant to BOTH the talker's additive LEVEL
    (value shift, iter-23 value_difference) AND the VTL scale (band-index shift,
    iter-24 landmark spacing). Concatenates the two agent-composed relations per
    frame: [value-differences | landmark-spacings]. Both are the agent's own Terms;
    concatenation is mechanical I/O. Returns n_frames x ((n_bands-1)+n_spacings)."""
    from domains.relational_representation import apply_relational

    val = apply_relational(M, substrate=substrate)            # value-shift invariant
    spc = apply_scale_invariant(M, n_spacings=n_spacings, substrate=substrate)
    n = min(val.shape[0], spc.shape[0])
    return np.concatenate([val[:n], spc[:n]], axis=1).astype(np.float32)


def compose_scale_invariant_representation(substrate, n_spacings: int = 6) -> list:
    """The agent records its composed landmark-spacing relation as a Concept
    (feature_kind=scale_invariant) carrying its Term-tree — the same authoring move
    as compose_relational_representation / compose_cmvn. Returns [(concept_id,
    name)]. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind") == "scale_invariant"}
    created = []
    term = spacing_relation_term()
    name = "scale_invariant_landmark_spacing"
    if name not in existing:
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "scale_invariant",
            "predicate": term.to_dict(),
            "origin": "scale_invariant_representation", "composed_by": "agent",
            "derived_gap": (
                "represent the object by the invariant RELATIONS among its parts -- "
                "its relative arrangement / configuration / structure -- which is "
                "preserved under the transformation group and is invariant by "
                "construction, rather than by the parts' absolute coordinate values"),
            "science": (
                "VTL scales the formant frequencies = a uniform shift along the "
                "band-INDEX axis; the parts are the spectral landmarks (peaks); a "
                "difference of two landmarks' band-index POSITIONS (their spacing) "
                "cancels that uniform index shift -> the relation among the parts' "
                "positions is invariant by construction (Klein / Erlangen), the "
                "band-INDEX analogue of the iter-23 value-difference")})
        created.append((c, name))
    return created


__all__ = ["value_difference_term", "spacing_relation_term",
           "apply_scale_invariant", "apply_stacked",
           "compose_scale_invariant_representation"]
