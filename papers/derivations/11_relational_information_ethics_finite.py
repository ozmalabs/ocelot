"""Finite reference functions for Relational Information Accounting, Paper 11.

States and outcomes are hashable. Edges encode admissible transitions.
Encode clocks, remaining budgets, and identity in states when they matter.
A missing outcome (None) contributes no continuing outcome for that frame.
No evaluator weight appears in reachability or the consequence account.
Arithmetic overflow raises an error rather than reporting a measured infinity.
"""
from heapq import heappop, heappush
from itertools import count
from math import isclose, isfinite, log2
from statistics import NormalDist


def _finite_result(value, quantity):
    """Reject arithmetic overflow without confusing it with a model result."""
    if not isfinite(value):
        raise ValueError(f"{quantity} exceeds finite arithmetic range")
    return value


def reachable(edges, starts, horizon, outcome, *, exact=True):
    """Distinct outcomes at exactly horizon steps, or up to that horizon.

    Terminal persistence requires explicit self-loops in edges. Transition
    nondeterminism represents possible reachability, not assured control.
    Finite adjacency iterables are materialised for repeated visits.
    """
    if not isinstance(horizon, int) or horizon < 0:
        raise ValueError("horizon must be a nonnegative integer")
    edges = {state: tuple(steps) for state, steps in edges.items()}
    frontier = set(starts)
    visited = set(frontier)
    for _ in range(horizon):
        frontier = {v for u in frontier for v in edges.get(u, ())}
        visited.update(frontier)
    states = frontier if exact else visited
    return frozenset(y for s in states if (y := outcome(s)) is not None)


def compare_futures(baseline, action, masses=None):
    """Aligned outcome identities; optional nonnegative grounded masses."""
    baseline, action = frozenset(baseline), frozenset(action)
    lost, gained = baseline - action, action - baseline
    def measure(items):
        if masses is None:
            return len(items)
        values = [masses[x] for x in items]
        if any(not isfinite(v) or v < 0 for v in values):
            raise ValueError("outcome masses must be finite and nonnegative")
        return _finite_result(sum(values), "outcome mass")
    return {"lost": lost, "gained": gained,
            "loss": measure(lost), "gain": measure(gained)}


def resource_difference(baseline, action):
    """Keys are (payer, resource unit); absent keys mean measured zero."""
    keys = baseline.keys() | action.keys()
    values = list(baseline.values()) + list(action.values())
    if any(not isfinite(v) or v < 0 for v in values):
        raise ValueError("expenditures must be finite and nonnegative")
    return {k: action.get(k, 0) - baseline.get(k, 0) for k in keys}


def consequence_account(baseline, action, resources_b, resources_a,
                        masses=None):
    """Frame IDs map to measured reachable sets, including extinct IDs.

    An absent ID means a known empty set, never an unmeasured frame.
    Use a common grounding for outcome masses within each frame.
    """
    ids = baseline.keys() | action.keys()
    accounts = {i: compare_futures(baseline.get(i, ()),
                                 action.get(i, ()),
                                 None if masses is None else masses[i])
                for i in ids}
    return {"frames": accounts,
            "resources": resource_difference(resources_b, resources_a)}


def _change_profile(baseline_series, action_series, durations, masses, kind):
    if not (len(baseline_series) == len(action_series) == len(durations)):
        raise ValueError("series must have aligned intervals")
    if any(not isfinite(dt) or dt < 0 for dt in durations):
        raise ValueError("durations must be finite and nonnegative")
    profile = [compare_futures(b, a, masses)[kind]
               for b, a in zip(baseline_series, action_series)]
    exposure = sum(dt * value for dt, value in zip(durations, profile))
    return profile, _finite_result(exposure, f"{kind} exposure")


def loss_profile(baseline_series, action_series, durations, masses=None):
    """Piecewise constant loss, with a shared clock and interval lengths."""
    return _change_profile(baseline_series, action_series, durations,
                           masses, "loss")


def gain_profile(baseline_series, action_series, durations, masses=None):
    """Piecewise constant gain; keep separate from loss and its exposure."""
    return _change_profile(baseline_series, action_series, durations,
                           masses, "gain")


def deterministic_capacity(outcomes):
    """Capacity for distinct attainable outputs of a deterministic channel.

    The caller establishes that each output is attainable by a legal input.
    Empty outputs describe no channel, rather than a numerical log(0).
    """
    size = len(set(outcomes))
    return None if size == 0 else log2(size)


def least_repair(edges, start, goals):
    """Minimum scalar repair expenditure, or infinity if unreachable.

    edges[state] contains (successor, cost). Costs must share one grounded
    unit and be nonnegative. The goal set specifies restoration conditions.
    An overflowing explored path raises an error; infinity means unreachable.
    """
    edges = {state: tuple(steps) for state, steps in edges.items()}
    for steps in edges.values():
        if any(not isfinite(c) or c < 0 for _, c in steps):
            raise ValueError("repair costs must be finite and nonnegative")
    goals = set(goals)
    serial = count()
    queue = [(0, next(serial), start)]
    best = {start: 0}
    while queue:
        cost, _, state = heappop(queue)
        if cost != best[state]:
            continue
        if state in goals:
            return cost
        for successor, spend in edges.get(state, ()):
            candidate = _finite_result(cost + spend, "repair path cost")
            if candidate < best.get(successor, float("inf")):
                best[successor] = candidate
                heappush(queue, (candidate, next(serial), successor))
    return float("inf")


def evaluate(features, weights):
    """Explicit weighted decision score, following consequence calculation.

    Keys agree exactly; losses and resource burdens have positive feature
    signs, gains negative signs. Weights declare the chosen conversion.
    """
    if features.keys() != weights.keys():
        raise ValueError("each measured feature requires an explicit weight")
    if any(not isfinite(x) for x in list(features.values())
           + list(weights.values())):
        raise ValueError("features and weights must be finite")
    score = sum(weights[k] * features[k] for k in features)
    return _finite_result(score, "decision score")


def shadow_price_bounds(observations):
    """Bounds on lambda from (avoided_loss, extra_resource, accepted).

    Assumes lambda >= 0 and fixed score extra_resource - lambda * avoided_loss,
    with other effects held fixed. Bounds allow indifference at ties.
    No accepted/rejected choices give bounds 0/infinity respectively.
    """
    lower, upper = 0.0, float("inf")
    for avoided, resource, accepted in observations:
        if not (isfinite(avoided) and avoided > 0
                and isfinite(resource) and resource >= 0):
            raise ValueError("positive avoided loss and nonnegative cost required")
        if not isinstance(accepted, bool):
            raise ValueError("accepted must be a boolean")
        threshold = resource / avoided
        if not isfinite(threshold):
            raise ValueError("threshold exceeds finite arithmetic range")
        if accepted:
            lower = max(lower, threshold)
        else:
            upper = min(upper, threshold)
    return {"lower": lower, "upper": upper,
            "consistent": lower <= upper}


def policy_distance(first, second):
    """Total variation of two aligned finite action distributions.

    Absent action keys mean known zero probability. The caller supplies
    matched conditions; this function does not establish causal matching.
    Normalisation uses tolerance 1e-12; outputs have floating-point error.
    """
    for distribution in (first, second):
        if any(not isfinite(p) or p < 0 for p in distribution.values()):
            raise ValueError("probabilities must be finite and nonnegative")
        if not isclose(sum(distribution.values()), 1.0,
                       rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("each distribution must sum to one")
    keys = first.keys() | second.keys()
    return 0.5 * sum(abs(first.get(k, 0) - second.get(k, 0)) for k in keys)


def valuation_gap(operative_candidates, model_admitted):
    """Finite-grid mismatch: operative valuation vs admitted self-description.

    Operative candidates satisfy the stated choice model. Admission status
    is known for every operative candidate; unknowns cannot be omissions.
    The rejection fraction is a uniform grid-count summary, not aversion.
    An empty operative set gives an undefined gap, not a measured mismatch.
    """
    operative = frozenset(operative_candidates)
    admitted = frozenset(model_admitted)
    excluded = operative - admitted
    if not operative:
        return {"excluded": excluded, "incompatible": None,
                "rejection_fraction": None}
    return {"excluded": excluded,
            "incompatible": not bool(operative & admitted),
            "rejection_fraction": len(excluded) / len(operative)}


def normal_response(mean, spread, shift=0.0, ambivalence_width=None):
    """Conditional fractions for a normally distributed decision margin.

    Positive margin favours the comparison action over the harmful action.
    A common nonnegative shift lowers the margin, holding other terms fixed.
    Width defines a near-zero-margin proxy, not psychological ambivalence.
    Parameters are declared, not fitted; outputs use floating-point CDFs.
    """
    if not (isfinite(mean) and isfinite(spread) and spread > 0
            and isfinite(shift) and shift >= 0):
        raise ValueError("finite mean, positive spread, nonnegative shift required")
    if ambivalence_width is not None and not (
            isfinite(ambivalence_width) and ambivalence_width > 0):
        raise ValueError("ambivalence width must be finite and positive")
    standard = NormalDist()

    def cdf_at(value):
        difference = value - mean
        if isfinite(difference):
            z = difference / spread
        else:
            # Opposite-sign finite operands can overflow subtraction.
            # Divide first in that case; an infinite z is a valid tail.
            z = value / spread - mean / spread
        return standard.cdf(z)

    near = None
    if ambivalence_width is not None:
        near = cdf_at(ambivalence_width) - cdf_at(-ambivalence_width)
    baseline = cdf_at(0.0)
    shifted = cdf_at(shift)
    return {"baseline_fraction": baseline,
            "shifted_fraction": shifted,
            "newly_selected_fraction": shifted - baseline,
            "near_zero_fraction": near}
