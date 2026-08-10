"""Brick 6 — SALIENCE pre-filter (the decisive re-test of the guide).

DIAGNOSIS (turn 1 distance + turn 2 interference). Both guides ranked over a
candidate pool POLLUTED by non-salient terms:
  - the DISTANCE guide (keep smallest |residual|) over-pruned and MISSED
    a*a+b*b — each structural partner a*a / b*b is FAR (large |r|), so the
    closest-K slots filled with closer-but-structureless terms and the
    far-but-cancelling partner never survived the cap.
  - the INTERFERENCE guide (keep most anti-correlated residual) was BURIED:
    ~150 trivial constant/zero terms have residual ~ -target (cos -1, the most
    anti-correlated thing in the pool) yet carry NO input-dependent structure;
    they swamped the real structural partners a*a (rank #157) and b*b (#166).

An independent neural paper (GESC) names the SAME failure: ranking over a pool
of NON-SALIENT candidates lets structureless terms game any naive metric by
sheer NUMEROSITY.

THE FIX — a SALIENCE PRE-FILTER. Select on a term's STRUCTURAL CONTRIBUTION
(does its output carry input-dependent structure?), NOT on its raw proximity /
anti-correlation to the target. A constant / zero / input-independent term is
the redundant-by-count background; demote it OUT of the ranked candidate slots
so the salient structural terms (a*a, b*b) survive the per-size cap.

SALIENCE (weightless, MDL / information-grounded — a property of the term's
BEHAVIOUR computed once from its signature, frame-relative to THIS target's
inputs):
  salience(term) = output VARIANCE across the example inputs.
  - a constant (Lit 5) or zero term has variance 0 -> salience 0 (non-salient).
  - an input-independent term (same output on every input) -> variance 0.
  - a*a, b*b vary strongly across the inputs -> high variance -> salient.
  We additionally expose `is_salient` (variance > eps AND >1 distinct value):
  the cheap binary "does this term's output DEPEND on the input variables".

This is the SAME shape as perceptual salience (the ear / navigation: attend to
what affords the goal, suppress flat redundancy). Weightless: variance /
distinct-value count over the term signature — an MDL / information quantity.
No net, no LLM. Distinct from EXCLUSION (Gamma = admissible-or-not); salience
ranks the INFORMATIVE among the admissible (constants STAY as building blocks
for composition; they are only DEMOTED as ranked candidates).

ADDITIVE, default-off. Reuses brick-6's `guide` / `guide_select` hooks: a
salience pre-filter wraps EITHER selector (distance or interference) and feeds
it only the salient candidates (back-filling with non-salient terms ONLY if too
few salient ones exist, so the cap is never wasted).
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from domains.generator_self_improve import _sig_to_nums, output_distance
from domains.generator_interference import select_interference, select_distance


# ---------------------------------------------------------------------------
# The salience measure: output variance / input-dependence over the signature.
# ---------------------------------------------------------------------------

def salience(sig: tuple) -> float:
    """Structural salience of a term = VARIANCE of its outputs across the spec
    inputs. A constant / zero / input-independent term -> 0.0 (non-salient).
    A term whose output varies with the input vars -> > 0 (salient). Computed
    once from the signature brick-6 already holds; weightless, MDL-grounded.

    Non-finite outputs (inf/nan) make a term inadmissible as a salient
    candidate -> 0.0 salience (it cannot be a clean structural partner).
    """
    nums = _sig_to_nums(sig)
    n = len(nums)
    if n == 0:
        return 0.0
    for v in nums:
        if v != v or v in (float("inf"), float("-inf")):
            return 0.0
    mean = sum(nums) / n
    return sum((v - mean) ** 2 for v in nums) / n


def distinct_count(sig: tuple) -> int:
    """Number of DISTINCT output values across the spec inputs. 1 = constant
    (input-independent), >1 = input-dependent structure."""
    nums = _sig_to_nums(sig)
    return len({round(v, 9) for v in nums
                if v == v and v not in (float("inf"), float("-inf"))})


def is_salient(sig: tuple, eps: float = 1e-12) -> bool:
    """Binary: does this term's output DEPEND on the input variables? True iff
    variance > eps AND it takes more than one distinct value. The cheap
    'contains real structure, not flat background' test."""
    return salience(sig) > eps and distinct_count(sig) > 1


# ---------------------------------------------------------------------------
# THE SALIENCE PRE-FILTER over a selector.
#
# Partition the per-size candidate cohort into SALIENT (input-dependent) and
# NON-SALIENT (constant / zero / input-independent). Run the inner selector
# (distance or interference) over the SALIENT candidates only; back-fill the
# remaining K slots with non-salient terms ONLY if fewer than K salient ones
# exist (so a target that genuinely needs a constant component still gets it,
# and the cap is never wasted). Constants are NEVER removed as building blocks
# — `synthesize` keeps the full by_size frontier for composition; this only
# governs which terms occupy the RANKED candidate slots.
# ---------------------------------------------------------------------------

def make_salience_select(
    inner_select: Callable[[list, tuple, int], list],
) -> Callable[[list, tuple, int], list]:
    """Wrap a `guide_select`-style selector with a salience pre-filter."""

    def _select(scored, target, k):
        salient = [(t, s) for (t, s) in scored if is_salient(s)]
        nonsalient = [(t, s) for (t, s) in scored if not is_salient(s)]
        if len(salient) >= k:
            # Enough structural candidates: rank ONLY the salient ones.
            return inner_select(salient, target, k)
        # Too few salient candidates: keep them all, then back-fill the
        # remaining slots from the non-salient pool via the same inner
        # selector (so a genuine constant component can still be retained).
        kept = list(salient)
        need = k - len(kept)
        if need > 0 and nonsalient:
            kept.extend(inner_select(nonsalient, target, need))
        return kept

    return _select


# Salience-wrapped selectors for brick-6's guide_select hook.
select_distance_salient = make_salience_select(select_distance)
select_interference_salient = make_salience_select(select_interference)


# ---------------------------------------------------------------------------
# RANK-CHECK instrumentation (the mechanism proof). Given the candidate cohort
# at a size and the target, report where the trivial constant/zero terms land
# and where named structural partners (e.g. a*a, b*b) land — BEFORE and AFTER
# the salience pre-filter — so we can show the filter does what it claims.
# ---------------------------------------------------------------------------

def rank_by(scored, target, key_fn, reverse=False):
    """Return [(rank, term, sig, score)] sorted by key_fn(sig, target)."""
    items = [(t, s, key_fn(s, target)) for (t, s) in scored]
    items.sort(key=lambda it: it[2], reverse=reverse)
    return [(i + 1, t, s, sc) for i, (t, s, sc) in enumerate(items)]


def anticorrelation_score(sig: tuple, target: tuple) -> float:
    """The interference ranking key: cosine of the residual with -target (the
    fully-cancelling direction). MORE anti-correlated (residual ~ -target) =>
    score near +1. A trivial term with residual exactly -target scores ~+1."""
    from domains.generator_interference import _residual, _cos
    r = _residual(sig, target)
    if r is None:
        return -2.0
    # the ideal single-term cancel of the target is residual == -target
    neg_target = tuple(-t for t in target)
    return _cos(r, neg_target)
