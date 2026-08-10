"""Brick 6 — ORDER-N COLLAPSE: the fix for everything the order-0 guides missed.

THE DIAGNOSIS. Distance (turn-1), interference (turn-2) and salience (turn-3) all
rank candidates at ORDER-0 — raw residual, anti-correlation of the residual, or
variance of the raw output. And ORDER-0 is where the NOISE lives: trivial
constant / zero terms have huge order-0 presence (they sit AT the target value,
anti-correlate perfectly with -target) yet carry ZERO structure. By sheer
numerosity they swamp the real structural partners (a*a, b*b), which are FAR in
raw magnitude. Every order-0 metric is gamed by structureless background.

THE TRICK — COLLAPSE IN ORDER-N SPACE. A signal carries consistent HIGHER-ORDER
structure; noise is order-0-FLAT. Take the order-n finite difference along each
input axis and:
  - constants / input-independent terms -> all-zero differences above order 0
    (they VANISH — exactly the noise we wanted gone),
  - a*a -> constant nonzero 2nd difference over a (it PERSISTS), and that 2nd
    difference MATCHES the target's own a-curvature.
So the order-n structure is the SNR / salience filter done at the RIGHT order:
the same separation salience attempted with variance, but reading the term's
DYNAMICS over the input grid instead of its raw spread.

REUSE THE AGENT'S OWN OPERATOR. The finite difference is NOT reinvented here. It
is `order_n_concepts.nth_order_terms` — the agent's generic recursive-Minus nth
difference, the same operator it composes to read formant curvature (order-2-freq)
and formant transitions (order-1-time) in perception. Here it reads
SOLUTION-STRUCTURE out of candidate-noise. We feed it the candidate's grid-point
outputs as `Lit` samples; it returns the difference Term-trees; the substrate's
own evaluator computes them. Generic operator, reused across frames. Weightless:
finite differences of term behaviours, no net, no LLM.

THE GRID. Finite differences need a CONTIGUOUS sweep. The spec's scattered
example envs do not support clean axis differences, so we build a GRID from the
target: each input variable swept over a contiguous integer range while the
others are held at a base value (one axis-sweep per variable). The candidate and
the target are evaluated on this grid; per axis we take the order-n differences.
The ORDER PROFILE of a term = the concatenation of its order-n differences along
every axis. Order-n MATCH = how well a candidate's profile CONTRIBUTES to the
target's profile (cosine alignment of the order-n structure).

ADDITIVE, default-off. Reuses brick-6's `guide_select` hook exactly like
interference / salience. brick-6 + turn-1/2/3 + interference + salience unchanged.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from substrate_rs import Lit

# REUSE the agent's own order-N operator — do NOT reinvent the finite difference.
from domains.order_n_concepts import nth_order_terms


# ---------------------------------------------------------------------------
# Grid construction from the target.
#
# For each variable we sweep a contiguous integer range (default the GRID_SPAN
# integers starting at GRID_LO) while holding the other variables at GRID_BASE.
# This yields one axis-sweep per variable, each a contiguous run on which order-n
# finite differences along that axis are well-defined. Built once per target.
# ---------------------------------------------------------------------------

GRID_LO = 1          # axis sweep starts here (avoid 0 so Div-style terms behave)
GRID_SPAN = 6        # number of contiguous points per axis (supports up to order-5)
GRID_BASE = 2        # value held on the OTHER axes during a sweep


def build_grid(var_names: Sequence[str],
               lo: int = GRID_LO, span: int = GRID_SPAN,
               base: int = GRID_BASE) -> list[tuple[str, list[dict]]]:
    """One axis-sweep per variable: (var, [env, ...]) where `var` ranges over a
    contiguous integer run and the others are held at `base`. The grid is derived
    purely from the target's variable set — no peeking at the answer."""
    axes = []
    for v in var_names:
        envs = []
        for k in range(span):
            env = {u: float(base) for u in var_names}
            env[v] = float(lo + k)
            envs.append(env)
        axes.append((v, envs))
    return axes


# ---------------------------------------------------------------------------
# Order-N profile of a term over the grid.
#
# For each axis-sweep, evaluate the term at the contiguous grid points, wrap the
# outputs as Lit samples, and hand them to the agent's nth_order_terms operator.
# The substrate evaluates the resulting difference Term-trees. The order-n
# profile = the per-axis order-n difference values, concatenated. We ALSO keep
# the lower orders (1..N) so a degree-d target is matched at its own degree.
# ---------------------------------------------------------------------------

def _eval_on(term, env, substrate):
    try:
        out = term.evaluate(env, substrate)
    except Exception:
        return None
    if isinstance(out, bool):
        return 1.0 if out else 0.0
    if isinstance(out, (int, float)):
        f = float(out)
        if f != f or f in (float("inf"), float("-inf")):
            return None
        return f
    return None


def _axis_diffs(outputs: list[float], order: int, substrate) -> list[float] | None:
    """The order-N finite differences of a contiguous output run, via the agent's
    OWN nth_order_terms operator (recursive Minus), evaluated natively. Returns
    None if any sample is missing (term inadmissible on the grid)."""
    if any(o is None for o in outputs):
        return None
    samples = [Lit(float(o)) for o in outputs]
    diff_terms = nth_order_terms(samples, order)
    vals = []
    for d in diff_terms:
        try:
            vals.append(float(substrate.evaluate(d, {})))
        except Exception:
            return None
    return vals


def order_n_profile(term, grid, order: int, substrate,
                    orders: Sequence[int] | None = None):
    """The term's ORDER-N STRUCTURE over the grid: for every axis and every order
    in `orders` (default just `order`), the finite-difference values along that
    axis. Returned as a flat tuple (the order-n signature) keyed parallel for the
    target and every candidate, so they can be aligned. None if inadmissible on
    any grid point."""
    use_orders = list(orders) if orders is not None else [order]
    prof: list[float] = []
    for _v, envs in grid:
        outs = [_eval_on(term, e, substrate) for e in envs]
        for o in use_orders:
            d = _axis_diffs(outs, o, substrate)
            if d is None:
                return None
            prof.extend(d)
    return tuple(prof)


# ---------------------------------------------------------------------------
# Order-N MATCH: alignment of a candidate's order-n profile with the target's.
#
# A constant / input-independent term has an ALL-ZERO order-n profile (its
# differences above order 0 vanish) -> match 0 (it is order-0 noise, correctly
# demoted). a*a has a nonzero constant 2nd difference matching the target's
# a-curvature -> high match (it carries the target's order-n structure). We use
# cosine alignment so a term that carries the RIGHT structure (even scaled) ranks
# high, and add a tiny tie-break toward the term that supplies MORE of the
# magnitude the target needs.
# ---------------------------------------------------------------------------

def _norm(v):
    return math.sqrt(sum(x * x for x in v))


def order_n_match(cand_prof, target_prof) -> float:
    """How well the candidate's order-n structure aligns with the target's.
    cosine(cand, target) in [-1, 1]; higher = the candidate carries more of the
    target's higher-order structure. An all-zero (order-0-flat / constant) profile
    -> 0.0 (demoted to the bottom). None profile -> -2.0 (inadmissible)."""
    if cand_prof is None or target_prof is None:
        return -2.0
    if len(cand_prof) != len(target_prof):
        return -2.0
    nc, nt = _norm(cand_prof), _norm(target_prof)
    if nt == 0.0:
        return 0.0
    if nc == 0.0:
        return 0.0  # constant / order-0-flat -> no higher-order structure
    dot = sum(a * b for a, b in zip(cand_prof, target_prof))
    return dot / (nc * nt)


# ---------------------------------------------------------------------------
# THE ORDER-N COLLAPSE SELECTOR (a guide_select hook for brick 6).
#
# Given the candidate terms at one size and the target, KEEP the K whose order-n
# structure best matches / contributes to the target's order-n structure. The
# collapse is in ORDER-N space: constants sink (zero profile), structural partners
# rise (they carry the target's curvature). To keep COMPLEMENTARY partners (a*a
# AND b*b each supply HALF of the target's profile and individually align only
# partially), we use a greedy matching-pursuit in order-n space: repeatedly add
# the candidate that best reduces the RESIDUAL of the target profile not yet
# explained by the kept set. This surfaces BOTH halves, where a pure top-K-by-
# cosine would take many copies of one half.
# ---------------------------------------------------------------------------

class OrderNCollapse:
    """Stateful selector closure (caches the target profile + grid per target).
    Instantiate per target/run: `sel = OrderNCollapse(substrate, var_names,
    examples_target, order=2)` then pass `guide_select=sel`.
    """

    def __init__(self, substrate, var_names, order=2, use_orders=None,
                 greedy=True):
        self.s = substrate
        self.order = order
        self.use_orders = (list(use_orders) if use_orders is not None
                           else list(range(1, order + 1)))
        self.greedy = greedy
        self.grid = build_grid(var_names)
        # target profile is set lazily from the first call's `target` if needed;
        # but we can build it directly from the spec target function only if we
        # have it. We instead reconstruct it from the SOLUTION-FREE target by
        # evaluating the actual target outputs on the grid — supplied via
        # set_target_outputs. If not set, fall back to residual-free cosine on
        # the candidate profiles against the provided `target` tuple is NOT
        # possible (different grid), so set_target_profile is required.
        self.target_prof = None

    # The target's order-n profile must be computed on the SAME grid as the
    # candidates. The world adapter supplies a callable for the true target value
    # (it already has the target function for the spec) so the grid target outputs
    # are well-defined. This is the only place the true function is read, and only
    # to build the grid reference profile — the SELECTOR itself sees only profiles.
    def set_target_fn(self, target_fn):
        prof: list[float] = []
        for _v, envs in self.grid:
            outs = [float(target_fn(**{k: v for k, v in e.items()})) for e in envs]
            for o in self.use_orders:
                d = _axis_diffs(outs, o, self.s)
                prof.extend(d if d is not None else [])
        self.target_prof = tuple(prof)
        return self

    def profile(self, term):
        return order_n_profile(term, self.grid, self.order, self.s,
                               orders=self.use_orders)

    def __call__(self, scored, target, k):
        if self.target_prof is None:
            # No target profile -> cannot collapse; passthrough (no pruning of the
            # frontier beyond the natural cap). Keep the first k arbitrarily.
            return scored[:k]
        profs = []
        for term, sig in scored:
            profs.append((term, sig, self.profile(term)))

        if not self.greedy:
            # simple top-K by order-n cosine match
            profs.sort(key=lambda it: order_n_match(it[2], self.target_prof),
                       reverse=True)
            return [(t, s) for (t, s, _p) in profs[:k]]

        # GREEDY matching-pursuit in order-n space: keep the partner that best
        # explains the still-unexplained part of the target's order-n profile.
        tp = list(self.target_prof)
        residual = list(tp)
        kept = []
        pool = [it for it in profs]
        # seed: the single best-aligned term (largest projection onto target)
        for _ in range(min(k, len(pool))):
            best = None
            best_gain = None
            for it in pool:
                p = it[2]
                if p is None or _norm(p) == 0.0:
                    gain = -1.0  # order-0-flat: explains nothing
                else:
                    # projection of residual onto this candidate's profile:
                    # how much of the unexplained structure it supplies.
                    dot = sum(a * b for a, b in zip(residual, p))
                    gain = dot / _norm(p)
                if best_gain is None or gain > best_gain:
                    best_gain, best = gain, it
            if best is None or best_gain is None or best_gain <= 0.0:
                break
            kept.append(best)
            # subtract the projection (deflate the residual by the kept term)
            p = best[2]
            np2 = sum(x * x for x in p)
            if np2 > 0:
                coef = sum(a * b for a, b in zip(residual, p)) / np2
                residual = [r - coef * pi for r, pi in zip(residual, p)]
            pool.remove(best)

        # backfill any remaining slots with the next-best-aligned salient terms
        if len(kept) < k:
            rest = sorted(
                (it for it in pool),
                key=lambda it: order_n_match(it[2], self.target_prof),
                reverse=True)
            kept.extend(rest[: k - len(kept)])
        return [(t, s) for (t, s, _p) in kept]


# ---------------------------------------------------------------------------
# RANK-CHECK instrumentation: rank a cohort by order-n match (mechanism proof).
# ---------------------------------------------------------------------------

def rank_by_order_n(scored, collapse: "OrderNCollapse"):
    """[(rank, term, sig, match)] sorted by order-n match (best first)."""
    items = []
    for term, sig in scored:
        p = collapse.profile(term)
        items.append((term, sig, order_n_match(p, collapse.target_prof)))
    items.sort(key=lambda it: it[2], reverse=True)
    return [(i + 1, t, s, m) for i, (t, s, m) in enumerate(items)]


__all__ = ["build_grid", "order_n_profile", "order_n_match",
           "OrderNCollapse", "rank_by_order_n",
           "GRID_LO", "GRID_SPAN", "GRID_BASE"]
