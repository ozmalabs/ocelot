"""relational_shape — the agent's WHOLE-UNIT RELATIONAL representation of a spoken
word, composed from its OWN owned DSL ops and evaluated NATIVELY.

WHY THIS, AND WHY NOT THE TWO KNOWN FAILURES
--------------------------------------------
The agent is a RELATIONAL (G, Gamma) substrate, yet its speech perception has always
been SURFACE-ACOUSTIC trajectory matching (gammatone bands -> DtwTo). A change of
talker re-scales each band by a per-band gain and adds a per-frame channel level, so
the ABSOLUTE band coordinates are mangled cross-speaker. The fix the agent's own
invariant-theory shape dictates (iter-20..22): represent the unit by the invariant
RELATIONS among its parts, which survive the talker transform by construction.

Two things this is NOT (the directive's named failures):
  * NOT surface-acoustic DtwTo over raw bands (the transform-fragile baseline).
  * NOT a per-frame scalar shape descriptor bolted onto the absolute values
    (iter-11 added per-frame curvature/one-ratio ALONGSIDE the coordinates and it
    DILUTED — a surface chunk, not whole-unit relational structure).

WHAT THE AGENT COMPOSES (relational, whole-unit, owned ops)
----------------------------------------------------------
The representation is the agent's relational re-description of the unit, and it is
matched STRUCTURALLY (DtwTo over the relational trajectory). It has two relational
faces, both invariant by construction and both whole-unit:

  (1) ORDINAL BAND-RANK PROFILE per frame.  The relation among the spectral PARTS
      that survives a per-band gain change is their ORDER: which band is higher than
      which.  For each frame the agent composes the rank of every band =
      Sum_j IfThenElse(Gt(band_i, band_j), 1, 0).  If the talker multiplies every
      band by a positive gain and/or adds a level, the ORDERING of the bands within a
      frame is preserved -> the rank profile is invariant by construction.  This is
      the configuration of the parts (the full spectral-shape ARRANGEMENT), not a
      single descriptor.  Owned ops only: Gt, IfThenElse, Plus, Vec, Attr, Var.

  (2) WHOLE-UNIT SELF-SIMILARITY (recurrence) ROW.  How does each part of the unit
      relate to every OTHER part of the SAME unit?  For frame t the agent measures
      its ordinal-rank agreement with each of K fixed phase anchors of the unit
      (frames sampled at fixed proportional positions of the whole word).  Because
      the anchors are the unit's OWN frames, this row is a relation INTERNAL to the
      unit and is invariant to ANY transform applied uniformly to all frames (the
      transform cancels in a within-unit comparison).  This is the relational
      structure of the WHOLE unit — its internal recurrence texture — appended to
      every frame so the DtwTo match is over the unit's self-relations, not its
      surface acoustics.  Owned ops: the rank vector (above) compared by negative L1
      agreement, composed from Minus/Abs/Plus.

The per-frame rank profile carries the LOCAL part-arrangement; the self-similarity
row carries the GLOBAL whole-unit relation.  Their concatenation is the relational
trajectory the unit is recognised by.  Both are evaluated by substrate.evaluate over
Term-trees the agent composed — NO numpy in the recognition representation, NO fitted
model.  numpy appears only at the I/O boundary (laying the band matrix out as frame
nodes), exactly as cmvn.apply_cmvn / relational_representation.apply_relational do.

DISCIPLINE: the recognition DISTANCE itself is the native DtwTo Term over these
relational trajectories (built by the do-contrast driver) — counts not nets, no .fit.
"""
from __future__ import annotations

import numpy as np

from substrate_rs import (Substrate, Attr, Var, Gt, IfThenElse, Lit, Plus, Vec,
                          Minus, Abs)


# ---------------------------------------------------------------------------
# (1) ORDINAL BAND-RANK PROFILE — composed Term-trees, owned ops only.
# ---------------------------------------------------------------------------

def _band(i: int):
    return Attr(Var("s"), f"band{i}")


def rank_term(i: int, n_bands: int):
    """rank(band_i) = number of bands strictly below band_i in this frame.

    Sum_{j != i} IfThenElse(Gt(band_i, band_j), 1, 0).  Invariant to any
    order-preserving (positive-gain + level) talker transform by construction.
    Pure composition over the agent's owned ops: Gt, IfThenElse, Plus."""
    indicators = [IfThenElse(Gt(_band(i), _band(j)), Lit(1.0), Lit(0.0))
                  for j in range(n_bands) if j != i]
    return Plus(items=indicators)


def rank_vector_term(n_bands: int):
    """The whole-frame ordinal configuration: the rank of every band, as a Vec."""
    return Vec(items=[rank_term(i, n_bands) for i in range(n_bands)])


# ---------------------------------------------------------------------------
# I/O boundary — evaluate the agent's rank Terms natively over a band matrix.
# Mechanical translator only (matrix -> frame nodes -> substrate.evaluate).
# ---------------------------------------------------------------------------

def rank_profile(M, sub=None):
    """frames x bands  ->  frames x bands ordinal-rank profile, every value out of
    the substrate evaluator (the agent's composed rank Terms run natively)."""
    M = np.asarray(M, dtype=np.float64)
    n_frames, n_bands = M.shape
    if n_bands < 2:
        return M.astype(np.float32)
    s = sub if sub is not None else Substrate()
    terms = [rank_term(i, n_bands) for i in range(n_bands)]
    out = np.empty((n_frames, n_bands), dtype=np.float64)
    for r in range(n_frames):
        fid = s.add_node("Frame", {f"band{b}": float(M[r, b])
                                   for b in range(n_bands)})
        env = {"s": fid}
        for i in range(n_bands):
            out[r, i] = float(s.evaluate(terms[i], env))
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# (2) WHOLE-UNIT SELF-SIMILARITY ROW — relation of each part to K phase anchors
#     of the SAME unit, composed natively (negative L1 rank disagreement).
# ---------------------------------------------------------------------------

def _selfsim_agreement_term(n_bands: int):
    """Agreement between the current frame's rank vector (env var 's') and an anchor
    frame's rank vector (env var 'anchor'): - Sum_b |rank_s(b) - rank_anchor(b)|.

    Higher = the two parts of the unit are arranged more alike.  Composed from the
    rank Terms + Minus/Abs/Plus — owned ops only."""
    diffs = []
    for i in range(n_bands):
        rs = rank_term_on(i, n_bands, "s")
        ra = rank_term_on(i, n_bands, "anchor")
        diffs.append(Abs(Minus(rs, ra)))
    # negate so larger = more similar (a relation, not a distance)
    total = Plus(items=diffs)
    return Minus(Lit(0.0), total)


def rank_term_on(i: int, n_bands: int, varname: str):
    node = Var(varname)
    indicators = [IfThenElse(Gt(Attr(node, f"band{i}"), Attr(node, f"band{j}")),
                             Lit(1.0), Lit(0.0))
                  for j in range(n_bands) if j != i]
    return Plus(items=indicators)


def selfsim_row(M, n_anchors=6, sub=None):
    """frames x bands -> frames x n_anchors whole-unit recurrence texture.

    For each frame t, its ordinal-rank AGREEMENT with each of n_anchors frames
    sampled at fixed proportional phases of the WHOLE unit.  Because the anchors are
    the unit's own frames, this is a relation internal to the unit and survives any
    uniform talker transform.  Evaluated natively via the agent's Term."""
    M = np.asarray(M, dtype=np.float64)
    n_frames, n_bands = M.shape
    if n_frames < 2 or n_bands < 2:
        return np.zeros((max(n_frames, 1), n_anchors), dtype=np.float32)
    s = sub if sub is not None else Substrate()
    # frame nodes
    fids = [s.add_node("Frame", {f"band{b}": float(M[r, b])
                                 for b in range(n_bands)})
            for r in range(n_frames)]
    # anchors at fixed proportional phases of the whole unit
    anchor_idx = [min(n_frames - 1, int(round(k * (n_frames - 1) / (n_anchors - 1))))
                  for k in range(n_anchors)] if n_anchors > 1 else [n_frames // 2]
    term = _selfsim_agreement_term(n_bands)
    out = np.empty((n_frames, n_anchors), dtype=np.float64)
    for r in range(n_frames):
        for a, ai in enumerate(anchor_idx):
            env = {"s": fids[r], "anchor": fids[ai]}
            out[r, a] = float(s.evaluate(term, env))
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# The full relational-shape trajectory: local part-arrangement (rank profile) ++
# whole-unit recurrence (self-similarity row), each column z-scaled to comparable
# magnitude so DtwTo weights them evenly (z-scaling is I/O boundary normalisation,
# not a fitted parameter).
# ---------------------------------------------------------------------------

def relational_shape(M, n_anchors=6, sub=None):
    """frames x bands  ->  the agent's whole-unit relational trajectory
    (frames x (n_bands + n_anchors)) evaluated natively.  This is the
    representation recognition matches over with the native DtwTo Term."""
    M = np.asarray(M, dtype=np.float64)
    if M.shape[0] < 2 or M.shape[1] < 2:
        return M.astype(np.float32)
    s = sub if sub is not None else Substrate()
    ranks = rank_profile(M, sub=s)
    recur = selfsim_row(M, n_anchors=n_anchors, sub=s)

    def _z(A):
        mu = A.mean(axis=0, keepdims=True)
        sd = A.std(axis=0, keepdims=True) + 1e-6
        return (A - mu) / sd

    return np.concatenate([_z(ranks), _z(recur)], axis=1).astype(np.float32)


__all__ = ["rank_term", "rank_vector_term", "rank_profile", "selfsim_row",
           "relational_shape"]
