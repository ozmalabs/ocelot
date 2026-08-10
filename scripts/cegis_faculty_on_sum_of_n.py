"""cegis_faculty_on_sum_of_n — VALIDATE the committed cegis_faculty on a
NON-TOPOLOGY operator, proving cegis_synthesize is genuinely domain-agnostic.

So far the faculty has only been exercised on simplicial-complex invariants
(dimension, euler), whose descriptors come from the topology primitive tower.
Here we drive the SAME `cegis_synthesize(...)` — REUSED AS-IS, not a line
changed — on a number-theory operator:

  OPERATOR: T(n) = the sum of the first n integers (the triangular number).

  SLOW DEFINITION (the oracle) — a RANGE-ITERATION:
      T(n) = sum{ k in 0..n : k }
    It builds the inclusive range 0..n (a list) and accumulates a running total,
    element by element — O(n) work, a real loop over a materialised collection.
    GROUNDED from the agent's OWN held primitives (range_incl + the sum_where
    binder) via compute_grounding.ground_computation — NOT an answer key. The
    label is whatever that grounded composition computes.

  INVENTED RECIPE (what G+Γ must synthesize) — a CLOSED FORM:
      T(n) = n * (n + 1) / 2
    THREE arithmetic ops over the single scalar descriptor n. It never builds a
    range, never iterates, never sums a list. O(1).

  COMPUTATIONALLY DISTINCT (the non-circular proof): the oracle runs a different
  algorithm (materialise 0..n, fold-sum) on a different data structure (a list of
  n+1 integers) from the recipe (one scalar, two mults/add, one divide). The
  recipe is checked AGAINST the oracle on self-constructed inputs; it is never
  told the recipe.

  THE TIE (naive knowns admit cheats). KNOWN = {n=1} -> T=1. On that spec the
  truth n(n+1)/2 is OBSERVATIONALLY TIED with the size-1 cheat `n` (and the
  literal `1`, n*n, ...). The native G, ordering by MDL size, returns the cheat.
  G is RIGHT to: the spec contains no discriminator. The CEGIS loop must
  construct divergences, self-label them with the slow oracle, and converge.

DESCRIPTOR GROUNDING (the same shape as the topology case, honestly). The
topology instance has a primitive-grounded descriptor FAMILY
(ground_cell_count_descriptors): cell_count(K,k) over k. The analogue for a
1-parameter integer operator is trivial — the operator's argument n IS the only
descriptor, read directly off the input (a single integer). There is no derived
descriptor family to ground here (n is the input), so `describe` is the identity
n -> {"n": n}. This is the honest difference: the topology case grounds a
descriptor FAMILY because its input is a structured complex; the sum-of-n input
is already the scalar descriptor. The ORACLE, however, IS grounded from held
primitives exactly as in the topology case — that is the load-bearing parallel.

NATIVE vs GAP (unchanged from the faculty docstring):
  NATIVE, reused as-is: G+Γ (domains.generator.synthesize), term evaluation,
    grounding (compute_grounding.ground_computation over reason.CAPABILITIES).
  GENUINELY ABSENT, supplied by the faculty: the CEGIS driver (construct-a-
    divergence + feed-the-labelled-row-back). Carries no math about T(n).

FAITHFUL (CLAUDE.md): a world-adapter driver sequencing native G, native term-
evaluation, and the agent's own grounded oracle. No Rust, no build, no
parent_teacher, no _native beyond _native.Substrate(). Changes left unstaged.

Run:
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. timeout 600 python3 scripts/cegis_faculty_on_sum_of_n.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import _native
from domains import reason as _reason
from domains import compute_grounding as _cg

# THE COMMITTED FACULTY — reused AS-IS, not a line changed.
from domains.cegis_faculty import cegis_synthesize


def banner(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


# ===========================================================================
# THE ORACLE — the agent's OWN slow definition of T(n), grounded into a callable
# from held primitives (range_incl + the sum_where binder). The RANGE-ITERATION:
# materialise 0..n and fold-sum it. COMPUTATIONALLY DISTINCT from n(n+1)/2.
# Grounded the SAME way ground_euler_oracle grounds χ — NOT an answer key.
# ===========================================================================

_SUM_OF_N_DEF = "triangular(n) = sum{ k in 0..n : k }"


def make_oracle(substrate, *, verbose=False):
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(substrate, "triangular", _SUM_OF_N_DEF,
                                 capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        raise RuntimeError("agent's own triangular oracle failed to ground: "
                           f"{res.get('reason')}")
    fn = caps["triangular"]
    if verbose:
        print(f"  grounded T(n)=sum{{k in 0..n:k}} oracle from held primitives: "
              f"{sorted(res.get('parts', []))}")

    def oracle(n):
        return int(fn({"n": n}))

    return oracle


# ===========================================================================
# THE WORLD ADAPTER — input -> scalar descriptor. The sum-of-n input IS the
# scalar descriptor n, so `describe` is the identity n -> {"n": n}. It does NOT
# expose T(n) (that is the answer); the recipe must be REBUILT from n alone.
# ===========================================================================

def describe(n):
    return {"n": n}


# ===========================================================================
# THE DIVERGENCE FAMILY — a bounded, mechanically-generated set of inputs (a
# range of n) the loop searches for the first divergence. Nothing about T(n) is
# encoded; these are just "more than the single known".
# ===========================================================================

def family():
    return [(f"n={n}", n) for n in range(2, 13)]


# ===========================================================================
# KNOWNS — the naive seed: a SINGLE input n=1 (T=1), where n(n+1)/2 is
# observationally TIED with the size-1 cheat `n`.
# ===========================================================================

KNOWNS = [("n=1", 1)]

OPS = ("Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
       "Gt", "Lt", "Eq", "IfThenElse")


def main():
    banner("CEGIS FACULTY on a NON-TOPOLOGY OPERATOR — T(n) = 0+1+...+n")
    print("""\
  Reusing the COMMITTED cegis_synthesize(...) AS-IS on a number-theory operator.
  ORACLE (slow def) = T(n) = sum{k in 0..n : k} — a RANGE-ITERATION grounded from
  the agent's held primitives (range_incl + sum_where), COMPUTATIONALLY DISTINCT
  from the closed form n(n+1)/2 (one scalar, no list). Known = {n=1} (T=1): the
  truth is TIED with the size-1 cheat `n`. The loop must construct divergences,
  self-label them with the oracle, and converge to the closed form.""")

    s = _native.Substrate()

    banner("GROUND THE ORACLE (the agent's own slow T(n), the range-iteration)")
    oracle = make_oracle(s, verbose=True)
    print("  oracle samples:", {n: oracle(n) for n in range(7)})

    banner("DRIVE THE COMMITTED FACULTY — cegis_synthesize(...) UNCHANGED")
    result = cegis_synthesize(
        s, describe, oracle, family, KNOWNS,
        ops=OPS, max_size=9, timeout_s=120.0, max_rounds=16, verbose=True,
    )

    # --- non-circularity restated ---
    banner("THE INVENTED RECIPE vs THE SLOW ORACLE (non-circularity)")
    print(f"  invented recipe (G+Γ over descriptor n) = {result.final_term_str!r}")
    print(f"  slow oracle (grounded)                  = "
          f"T(n) = sum{{k in 0..n : k}}  (materialise 0..n, fold-sum)")
    big = 1000
    print(f"  distinctness: on n={big} the oracle materialises a {big + 1}-element "
          f"range and folds {big + 1} adds;")
    print(f"                the recipe reads 1 scalar {describe(big)} and does "
          f"2 mults/add + 1 divide. DIFFERENT algorithm, DIFFERENT data structure.")

    # --- held-out generalisation: never-in-spec n ---
    banner("HELD-OUT — confirm the survivor is the real invariant (never in spec)")
    used = {nm for nm, _ in result.rows}
    held = [n for n in (17, 23, 50, 99, 100, 250) ]
    all_ok = True
    for n in held:
        got = result.evaluate(describe, n, s)
        tru = oracle(n)
        ok = abs(float(got) - float(tru)) < 1e-9
        all_ok = all_ok and ok
        print(f"     n={n:<5} recipe={got:>8.1f}  oracle T(n)={tru:>8}  ok={ok}")

    # --- verdict ---
    banner("VERDICT")
    closed_forms = {
        "(n * ((n + 1) / 2))", "(n * ((1 + n) / 2))",
        "((n * (n + 1)) / 2)", "((n * (1 + n)) / 2)",
        "(((n + 1) * n) / 2)", "(((1 + n) * n) / 2)",
        "(((n + 1) / 2) * n)", "(((1 + n) / 2) * n)",
    }
    is_closed = result.final_term_str in closed_forms
    rounds = sum(1 for r in result.rounds if r.counterexample is not None)
    cheats = result.discriminated
    print(f"""\
  OPERATOR: T(n) = sum of the first n integers (triangular number).
  ORACLE (slow def): T(n) = sum{{k in 0..n : k}} — a RANGE-ITERATION grounded from
    the agent's own held primitives (range_incl + sum_where). The RECIPE G invents
    is n(n+1)/2 (one scalar, O(1)). They are COMPUTATIONALLY DISTINCT (different
    algorithm + data structure); the non-circular proof above.
  STEP 0 (knowns only): native MDL recipe = {result.step0_term_str!r} — a CHEAT,
    because T(1)=1=n on the single known; the spec held nothing to separate it.
  DISCRIMINATING ROUNDS: {rounds}. Cheats discriminated, in order: {cheats}.
  FINAL invented recipe = {result.final_term_str!r}  (size {result.final_size}).
  Converged on the family = {result.converged}.  Held-out all correct = {all_ok}.

  SELF-CONVERGED ON THE CLOSED FORM n(n+1)/2 (cheats excluded) =
    {result.converged and is_closed and all_ok}.

  FACULTY REUSE: cegis_synthesize(...) was driven UNCHANGED — only the four
    domain pieces (describe, oracle, family, knowns) were supplied. The CEGIS core
    carries no math about T(n); proven domain-agnostic on a NON-topology operator.

  HONEST NOTE on descriptor grounding: the topology case grounds a descriptor
    FAMILY (cell_count(K,k) over k) because its input is a structured complex. The
    sum-of-n INPUT is already the scalar descriptor n, so `describe` is the
    identity (n -> {{n}}); there is no derived descriptor family to ground. The
    load-bearing parallel — a slow ORACLE grounded from held primitives, a closed-
    form RECIPE invented over the descriptor — holds exactly.""")


if __name__ == "__main__":
    main()
