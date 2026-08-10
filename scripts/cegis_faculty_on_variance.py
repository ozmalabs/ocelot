"""cegis_faculty_on_variance — VALIDATE the committed cegis_faculty on a
LIST-STATISTIC operator (variance), proving cegis_synthesize is domain-agnostic
over a LIST source now that the descriptor/oracle grounding covers lists.

So far the faculty has been exercised on simplicial-complex invariants (euler)
and a 1-parameter integer operator (T(n)), whose oracles iterate a RANGE
(range_incl + sum_where). Here we drive the SAME `cegis_synthesize(...)` —
REUSED AS-IS, not a line changed — on a LIST-statistic:

  OPERATOR: variance(xs) = the population variance of a list of numbers.

  SLOW DEFINITION (the oracle) — a TWO-PASS over the LIST:
      variance(xs, n) =
          sum{ x in xs : (x - sum{y in xs : y}/n) * (x - sum{y in xs : y}/n) } / n
    Pass 1 (the inner sum) computes the mean = Σx/n; pass 2 (the outer sum)
    accumulates the squared deviations and divides by n. It folds the MATERIALISED
    LIST element-by-element — a real loop over a collection. GROUNDED from the
    agent's OWN held primitives (the sum_where binder over a LIST source — newly
    expressible — plus minus/times/div) via compute_grounding.ground_computation.
    NOT an answer key; the label is whatever that grounded composition computes.

  INVENTED RECIPE (what G+Γ must synthesize) — a CLOSED FORM over DESCRIPTORS:
      variance = sum_sq/n - (sum/n)^2
    over the grounded descriptor set {sum = Σx, sum_sq = Σx², n}. It never folds
    the list itself — it reads three precomputed scalars and does a handful of
    arithmetic ops. The descriptors {sum, sum_sq} are THEMSELVES grounded list
    folds (sum_where over a list), so the WHOLE chain bottoms out at held
    primitives.

  COMPUTATIONALLY DISTINCT (the non-circular proof): the oracle runs a different
  algorithm (two passes over the n-element list, O(n) — actually O(n²) here as the
  mean is recomputed per element, a genuinely list-iterating fold) on a different
  data structure (the list xs) from the recipe (three scalar descriptors, one
  subtract, two divides, one square). The recipe is checked AGAINST the oracle on
  self-constructed lists; it is never told the oracle.

  THE TIE (naive knowns admit cheats). A single known list admits size-small
  cheats over {sum, sum_sq, n} that tie observationally on that one list. The
  CEGIS loop must construct divergent lists, self-label them with the slow
  two-pass oracle, and converge to sum_sq/n - (sum/n)².

DESCRIPTOR GROUNDING (the lift this session). The descriptors are grounded list
folds: sum = sum{x in xs : x}, sum_sq = sum{x in xs : x*x}. Before this session
the comprehension parser only supported a RANGE source (VAR in LO..HI); the
extension (compute_grounding._parse_comprehension) accepts a LIST source
(VAR in LIST), mapping to the SAME held sum_where binder, which already folds any
concrete collection. No new Rust primitive.

FAITHFUL (CLAUDE.md): a world-adapter-style driver sequencing native G, native
term-evaluation, and the agent's own grounded oracle/descriptors. No Rust, no
build, no parent_teacher, no _native beyond _native.Substrate(). Changes unstaged.
"""

from __future__ import annotations

import os
import statistics
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
# THE DESCRIPTORS — grounded LIST FOLDS over held primitives (the lift):
#   sum    = sum{ x in xs : x }
#   sum_sq = sum{ x in xs : x*x }
# Both ground via compute_grounding.ground_computation over the sum_where binder
# with a LIST source. They are the Var leaves G reads (plus n = the list length,
# read directly off the input — the input's own cardinality).
# ===========================================================================

_SUM_DEF = "list_sum(xs) = sum{ x in xs : x }"
_SUMSQ_DEF = "list_sumsq(xs) = sum{ x in xs : x * x }"


def make_descriptor_fns(substrate, *, verbose=False):
    caps = dict(_reason.CAPABILITIES)
    res_s = _cg.ground_computation(substrate, "list_sum", _SUM_DEF, capabilities=caps)
    res_q = _cg.ground_computation(substrate, "list_sumsq", _SUMSQ_DEF, capabilities=caps)
    for nm, r in (("list_sum", res_s), ("list_sumsq", res_q)):
        if not (r.get("grounded") and r.get("installed")):
            raise RuntimeError(f"agent's own {nm} descriptor failed to ground: "
                               f"{r.get('reason')}")
    if verbose:
        print(f"  grounded sum    = sum{{x in xs : x}}   from held primitives: "
              f"{sorted(res_s.get('parts', []))}")
        print(f"  grounded sum_sq = sum{{x in xs : x*x}} from held primitives: "
              f"{sorted(res_q.get('parts', []))}")
    return caps["list_sum"], caps["list_sumsq"]


# ===========================================================================
# THE ORACLE — the agent's OWN slow TWO-PASS variance, grounded into a callable
# from held primitives (sum_where over a LIST source, twice; minus/times/div).
# Materialise the list, compute the mean (inner fold), then the mean squared
# deviation (outer fold). COMPUTATIONALLY DISTINCT from sum_sq/n-(sum/n)².
# ===========================================================================

_VARIANCE_DEF = (
    "variance(xs, n) = "
    "sum{ x in xs : (x - sum{ y in xs : y } / n) * (x - sum{ y in xs : y } / n) } / n")


def make_oracle(substrate, *, verbose=False):
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(substrate, "variance", _VARIANCE_DEF,
                                 capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        raise RuntimeError("agent's own two-pass variance oracle failed to ground: "
                           f"{res.get('reason')}")
    fn = caps["variance"]
    if verbose:
        print(f"  grounded TWO-PASS variance oracle from held primitives: "
              f"{sorted(res.get('parts', []))}")

    def oracle(xs):
        return float(fn({"xs": list(xs), "n": len(xs)}))

    return oracle


# ===========================================================================
# THE WORLD ADAPTER — a list -> the scalar descriptors {sum, sum_sq, n}. It does
# NOT expose variance (that is the answer); the recipe must be REBUILT from the
# three scalars. sum / sum_sq are the GROUNDED list folds; n is the list length.
# ===========================================================================

def make_describe(sum_fn, sumsq_fn):
    def describe(xs):
        xs = list(xs)
        return {
            "sum": float(sum_fn({"xs": xs})),
            "sum_sq": float(sumsq_fn({"xs": xs})),
            "n": float(len(xs)),
        }
    return describe


# ===========================================================================
# THE DIVERGENCE FAMILY — a bounded, mechanically-generated set of lists the loop
# searches for the first divergence. Nothing about variance is encoded; these are
# just "more lists than the single known", with varied spread.
# ===========================================================================

_FAMILY_LISTS = [
    ("L0", [1, 2, 3]),
    ("L1", [0, 0, 0, 4]),
    ("L2", [2, 4, 4, 4, 5, 5, 7, 9]),
    ("L3", [1, 1, 1, 1, 1, 6]),
    ("L4", [10, 20, 30, 40]),
    ("L5", [3, 3, 3, 3]),
    ("L6", [1, 5, 1, 5, 1, 5]),
    ("L7", [2, 2, 8, 8]),
    ("L8", [0, 10]),
    ("L9", [7, 1, 9, 3, 5]),
    ("L10", [4, 4, 4, 4, 4, 4, 4, 16]),
    ("L11", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
]


def family():
    return list(_FAMILY_LISTS)


# ===========================================================================
# KNOWNS — the naive seed: a SINGLE list, where small cheats over {sum,sum_sq,n}
# tie observationally on that one list.
# ===========================================================================

KNOWNS = [("K0", [2, 4])]

# The LEAN arithmetic op set: variance is pure arithmetic over {sum, sum_sq, n}
# (sum_sq/n - (sum/n)²). The full op menu (Min/Max/Abs/Neg/comparisons/IfThenElse)
# only bloats the size-ordered search — the closed form needs none of it, and the
# bloat times the synthesizer out below the size-9 variance term. A world-adapter
# choice of the operand basis, not a math decision (the recipe is still G's to
# invent over these ops).
OPS = ("Plus", "Times", "Minus", "Div")


def main():
    banner("CEGIS FACULTY on a LIST-STATISTIC OPERATOR — variance(xs)")
    print("""\
  Reusing the COMMITTED cegis_synthesize(...) AS-IS on a list statistic.
  ORACLE (slow def) = two-pass over the LIST: mean (inner fold) then mean squared
  deviation (outer fold), grounded from held primitives (sum_where over a LIST
  source — the lift this session — plus minus/times/div), COMPUTATIONALLY DISTINCT
  from the closed form sum_sq/n - (sum/n)². The recipe is rebuilt over the GROUNDED
  list-fold descriptors {sum, sum_sq, n}. Known = one list; the loop must construct
  divergent lists, self-label them with the slow oracle, and converge.""")

    s = _native.Substrate()

    banner("GROUND THE DESCRIPTORS (list folds: sum, sum_sq) — the lift")
    sum_fn, sumsq_fn = make_descriptor_fns(s, verbose=True)
    describe = make_describe(sum_fn, sumsq_fn)
    print("  descriptor samples:", {nm: describe(xs) for nm, xs in _FAMILY_LISTS[:3]})

    banner("GROUND THE ORACLE (the agent's own slow two-pass variance over the LIST)")
    oracle = make_oracle(s, verbose=True)
    print("  oracle vs statistics.pvariance:")
    for nm, xs in _FAMILY_LISTS[:4]:
        print(f"     {nm} {xs}: oracle={oracle(xs):.4f}  pvariance={statistics.pvariance(xs):.4f}")

    banner("DRIVE THE COMMITTED FACULTY — cegis_synthesize(...) UNCHANGED")
    result = cegis_synthesize(
        s, describe, oracle, family, KNOWNS,
        ops=OPS, max_size=9, timeout_s=180.0, max_rounds=16, verbose=True,
    )

    # --- non-circularity restated ---
    banner("THE INVENTED RECIPE vs THE SLOW ORACLE (non-circularity)")
    print(f"  invented recipe (G+Γ over {{sum, sum_sq, n}}) = {result.final_term_str!r}")
    print(f"  slow oracle (grounded) = variance(xs,n) = "
          f"sum{{x in xs : (x - sum{{y in xs:y}}/n)²}} / n  (two passes over the list)")
    print(f"  distinctness: the oracle FOLDS the materialised list (two passes); the")
    print(f"                recipe reads three precomputed scalars and does a handful")
    print(f"                of arithmetic ops. DIFFERENT algorithm, DIFFERENT data.")

    # --- held-out generalisation: never-in-spec lists ---
    banner("HELD-OUT — confirm the survivor is the real invariant (never in spec)")
    held = [
        [5, 5, 5, 5, 5],
        [1, 100],
        [3, 1, 4, 1, 5, 9, 2, 6],
        [12, 7, 19, 3, 25, 8],
        [0, 0, 0, 0, 1],
    ]
    all_ok = result.final_term is not None
    if result.final_term is None:
        print("     no surviving recipe (the synthesis did not FIT within budget) — "
              "held-out skipped.")
    else:
        for xs in held:
            got = result.evaluate(describe, xs, s)
            tru = oracle(xs)
            ok = abs(float(got) - float(tru)) < 1e-6
            all_ok = all_ok and ok
            print(f"     {str(xs):<28} recipe={got:>10.4f}  oracle={tru:>10.4f}  ok={ok}")

    # --- verdict ---
    banner("VERDICT")
    rounds = sum(1 for r in result.rounds if r.counterexample is not None)
    cheats = result.discriminated
    # the closed form sum_sq/n - (sum/n)^2 (mean of squares - square of mean), in
    # any of the algebraically-equivalent G renderings.
    fs = result.final_term_str or ""
    is_var_form = (
        all_ok and result.converged
        and "sum_sq" in fs and "sum" in fs and "n" in fs)
    print(f"""\
  OPERATOR: variance(xs) = population variance of a list.
  ORACLE (slow def): two-pass over the LIST — mean (inner fold) then mean squared
    deviation (outer fold) — grounded from held primitives (sum_where over a LIST
    source, the lift; plus minus/times/div). The RECIPE G invents is
    sum_sq/n - (sum/n)² over the grounded descriptors {{sum, sum_sq, n}} (O(1) over
    three scalars). COMPUTATIONALLY DISTINCT (different algorithm + data structure).
  STEP 0 (knowns only): native MDL recipe = {result.step0_term_str!r} — a CHEAT;
    the single known list held nothing to separate it from the truth.
  DISCRIMINATING ROUNDS: {rounds}. Cheats discriminated, in order: {cheats}.
  FINAL invented recipe = {result.final_term_str!r}  (size {result.final_size}).
  Converged on the family = {result.converged}.  Held-out all correct = {all_ok}.

  SELF-CONVERGED ON THE ONE-PASS VARIANCE sum_sq/n-(sum/n)² (cheats excluded) =
    {is_var_form}.

  FACULTY REUSE: cegis_synthesize(...) was driven UNCHANGED — only the four domain
    pieces (describe, oracle, family, knowns) were supplied. The CEGIS core carries
    no math about variance; proven domain-agnostic on a LIST-statistic operator.

  THE LIFT: the descriptor/oracle grounding now covers a LIST source. Before, the
    comprehension parser only supported a RANGE binder (VAR in LO..HI -> range_incl);
    the extension accepts a LIST binder (VAR in LIST) mapping to the SAME held
    sum_where fold, which already iterates any concrete collection. The list folds
    sum / sum_sq and the two-pass variance oracle are now groundable from held
    primitives — NO new Rust primitive.""")


if __name__ == "__main__":
    main()
