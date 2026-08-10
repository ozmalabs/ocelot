"""Brick 6 — SIGN-PHASE INTERFERENCE as a synthesis beam (the steal-list test).

The DERIVED LAW (from a concurrent recognition session that built recognition as
a genuine quantum process — Born |psi|^2, complex amplitudes): INTERFERENCE PAYS
WHERE FEATURES ARE RELIABLE, HURTS WHERE NOISY. On a noisy cross-speaker task,
interference AMPLIFIED unreliable features (you want to AVERAGE on noise, not
interfere). Exact arithmetic synthesis is the RELIABLE-feature regime — every
term's output signature is exact, deterministic, noiseless. So this is the one
regime that meets the law's condition: the principled test of whether sign-phase
interference is a real synthesis lever.

THE EUCLIDEAN-FRAME RESIDUE OF COMPLEX PHASE. The ear resolves complex phase via
a path integral. The generator works in a real (Euclidean) frame: the analog of
phase is the SIGN PATTERN / DIRECTION of a term's SIGNED RESIDUAL
  r(t) = [ t(x_i) - target_i ]  over the spec inputs.
Magnitude |r| = how far. DIRECTION of r = the "phase". Two terms whose residuals
point in COMPLEMENTARY (anti-correlated) directions can CANCEL when composed
(t1 + t2 -> residual shrinks), even when BOTH are far in magnitude.

THE FOIL (turn-1 distance guide). The distance guide keeps the K terms of
SMALLEST |r| (closest). Its measured failure mode (generator_self_improve.py):
at small K it PRUNES a*a and b*b for a*a+b*b — each is far (dist ~0.45), so the
beam drops them in favour of closer-but-useless terms, and the needed
far-but-cancelling partner never survives to be combined.

INTERFERENCE (this module) keeps a PHASE-DIVERSE set: terms whose residuals are
ANTI-CORRELATED with the target's own residual-direction and with the
already-kept set, so a far-but-sign-complementary partner SURVIVES the cap. For
a*a+b*b: res(a*a) and res(b*b) are anti-correlated (corr ~ -0.50) and sum to
exactly -target -> both MUST be retained; interference keeps them, distance does
not.

GENUINELY different from distance: the test is the a*a+b*b recovery at the small
K where distance MISSES. If interference can't keep b*b there, the implementation
is wrong.

Weightless: signed residual patterns + a beam rule. No complex amplitudes, no
net, no LLM. Additive, default-off (a `guide_select` hook over brick 6).
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from domains.generator_self_improve import _sig_to_nums


# ---------------------------------------------------------------------------
# Residual = the Euclidean-frame "phase carrier". r(t) = sig(t) - target.
# ---------------------------------------------------------------------------

def _residual(sig: tuple, target: tuple) -> tuple | None:
    """Signed residual of a term's outputs against the target. None if the term
    has a non-finite output (inadmissible as an interference partner)."""
    nums = _sig_to_nums(sig)
    if len(nums) != len(target):
        return None
    r = []
    for got, want in zip(nums, target):
        if got != got or got in (float("inf"), float("-inf")):
            return None
        r.append(got - want)
    return tuple(r)


def _norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _cos(u: Sequence[float], v: Sequence[float]) -> float:
    """Cosine similarity of two residual vectors. +1 = same direction (redundant,
    both miss the same way), -1 = opposite direction (CANCELLING partners)."""
    nu, nv = _norm(u), _norm(v)
    if nu == 0.0 or nv == 0.0:
        return 0.0
    dot = sum(a * b for a, b in zip(u, v))
    return dot / (nu * nv)


# ---------------------------------------------------------------------------
# THE INTERFERENCE SELECTOR (form (a): phase-diverse / anti-correlation beam).
#
# Given the candidate terms at one size (each with its signature) and the
# target, choose K to KEEP. The rule is NOT "smallest |r|". It is:
#
#   1. Seed with the single CLOSEST term (smallest |r|) — the anchor; a beam
#      that kept only cancelling-far terms and never the close ones would never
#      converge, so we keep one close anchor.
#   2. Greedily add the term that is MOST COMPLEMENTARY to the kept set: the
#      term whose residual is most ANTI-CORRELATED (most negative cosine) with
#      the SUM of kept residuals — i.e. the term that best CANCELS the kept
#      set's collective residual. This is a destructive-interference / matching-
#      pursuit step in residual space. A LARGE-magnitude term that points
#      opposite the kept residual is PREFERRED (it cancels a lot), the exact
#      thing the distance guide throws away.
#   3. Break near-ties toward smaller |r| (Occam) and smaller term size.
#
# This keeps a*a (anchor or complement) AND b*b (its sign-complement) at small K,
# where the distance guide keeps neither.
# ---------------------------------------------------------------------------

def _sign_key(r) -> tuple:
    """The 'phase' of a residual = its per-input SIGN pattern (-1/0/+1). Two
    terms in the same sign-cluster miss the target the same way (redundant);
    DIFFERENT clusters are phase-diverse and can cancel each other."""
    return tuple((0 if x == 0 else (1 if x > 0 else -1)) for x in r)


def select_interference(scored, target, k):
    """`scored`: list of (term, signature). Return the K kept (term, signature)
    pairs by phase-diverse selection: cluster terms by residual SIGN-pattern
    (the Euclidean 'phase'), keep the best (closest) representative of each
    distinct phase, so far-but-sign-complementary partners ALL survive the cap.
    Pure ranking; no eval.

    This is form (a) of the steal-list: phase-diverse beam. Unlike distance
    (keep K smallest |r|, which collapses to one corner of output space), this
    spreads the K across DISTINCT residual directions — so a*a (residual all
    one sign) and b*b (its complement) land in different clusters and both
    survive, exactly the pair distance prunes.
    """
    items = []
    for term, sig in scored:
        r = _residual(sig, target)
        if r is None:
            continue
        items.append((term, sig, r, _norm(r)))
    if len(items) <= k:
        return [(t, s) for (t, s, _r, _n) in items]

    # Cluster by residual sign-pattern (phase). Within each cluster keep the
    # closest (smallest |r|) as the representative.
    clusters: dict[tuple, Any] = {}
    for it in items:
        key = _sign_key(it[2])
        cur = clusters.get(key)
        if cur is None or it[3] < cur[3]:
            clusters[key] = it
    reps = sorted(clusters.values(), key=lambda it: it[3])

    if len(reps) >= k:
        # More phase-classes than the budget: keep the K closest representatives
        # (still phase-DIVERSE — one term per distinct direction).
        kept = reps[:k]
    else:
        # Fewer phase-classes than K: keep every representative (full phase
        # coverage), then BACKFILL the remaining slots with the next-closest
        # terms overall (so we don't waste budget). The representatives guarantee
        # the complementary partners are present; the backfill keeps close terms.
        kept = list(reps)
        rep_ids = {id(it) for it in reps}
        extra = sorted((it for it in items if id(it) not in rep_ids),
                       key=lambda it: it[3])
        kept.extend(extra[: k - len(reps)])

    return [(t, s) for (t, s, _r, _n) in kept]


# ---------------------------------------------------------------------------
# A distance selector with the SAME interface, so brick 6's guide_select hook
# can run distance and interference through one identical code path (the only
# thing that differs is the ranking — a clean A/B).
# ---------------------------------------------------------------------------

def select_distance(scored, target, k):
    """Keep the K terms of smallest residual magnitude (the turn-1 foil)."""
    items = []
    for term, sig in scored:
        r = _residual(sig, target)
        nrm = _norm(r) if r is not None else float("inf")
        items.append((term, sig, nrm))
    items.sort(key=lambda it: it[2])
    return [(t, s) for (t, s, _n) in items[:k]]
