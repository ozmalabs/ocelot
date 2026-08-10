"""ACQUIRE MATH OPERATIONS BY READING — climb the compute tower ONE TIER, from
scalar arithmetic to operations over DISCRETE STRUCTURES (collections / sets).

The agent already acquires scalar COMPUTATIONS by reading their definitions and
grounding them as runnable Term-trees over the held arithmetic tower (lcm,
is_perfect_number, aliquot_sum -> see compute_grounding_test / wired_compute_
descent). This turn applies the SAME read -> ground-as-computation -> compute
mechanism to OPERATIONS over COLLECTIONS — an operation is a composition of lower
operations over a REPRESENTATION (a range 1..n / a small explicit set), grounded
over the base collection/iteration primitives.

THE AGENT'S OWN PRINCIPLE (elicited verbatim, implication_harvester /
order_n_postulates), now applied to OPERATIONS:

    "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS plus a
     finite set of COMBINATION (production) rules, so its members are not an
     enumerated list but an OPEN set REALIZABLE BY COMPOSING parts."

An OPERATION is the same compositional shape — a function over a REPRESENTATION
composed from lower operations:
    cardinality(S)      := count of S's elements
    intersection(A,B)   := the elements in BOTH
    are_disjoint(A,B)   := intersection(A,B) is empty
    divisor_count(n)    := count{ k in 1..n : k | n }
    totient(n)          := count{ k in 1..n : gcd(k,n) = 1 }
Each grounds as a runnable Term-tree over the collection / iteration primitives
(range_incl, count_where / sum_where, cardinality, member, is_empty, intersection,
are_disjoint) + the held arithmetic. The boundary MOVES UP: a concept that needed
one of these operations (is_prime := divisor_count(n) = 2) now COMPUTES.

THE BASE COLLECTION / ITERATION PRIMITIVES (each mirrors a DSL Term — reused, no
new Rust): range_incl (range/iota), count_where / sum_where (Filter+Count / Fold
binders), cardinality (Count), member, is_empty (IsEmpty), intersection
(Intersect), are_disjoint. The iteration binders are realised by reason.solve's
binder evaluator (the Python-tower analogue of the DSL Fold/Filter evaluators);
the rest are CAPABILITIES lambdas, parallel to gt / lt / divisor_sum.

HONEST: the tier reached is COLLECTION / DISCRETE-STRUCTURE operations over range
/ explicit-set representations. The NEXT tier — topological / algebraic operations
on richer structures (a boundary operator / homology, what cobordism needs) — does
NOT compose over these primitives: the agent reads it, reports NOT computable,
naming the missing lower op. The parse -> Term-tree is the permitted boundary.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/acquire_collection_operations.py
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import _native
from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cg

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# reference closed forms — the agent NEVER sees these; they only state the
# expected answer for the check.
def _ref_divisor_count(n):
    return sum(1 for k in range(1, n + 1) if n % k == 0)


def _ref_totient(n):
    return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)


def _ref_is_prime(n):
    return _ref_divisor_count(n) == 2


def prove_principle():
    banner("0. THE AGENT'S PRINCIPLE (verbatim) — applied to OPERATIONS")
    principle = (
        "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS "
        "plus a finite set of COMBINATION (production) rules ... so its members "
        "are not an enumerated list but an OPEN set REALIZABLE BY COMPOSING parts")
    print(f'  "{principle}"')
    print("\n  An OPERATION is the SAME shape: a function over a REPRESENTATION")
    print("  composed from lower operations. cardinality(S) := count of S's")
    print("  elements; divisor_count(n) := count{k in 1..n : k|n}. The agent")
    print("  ACQUIRES the operation by READING its definition and grounding it as")
    print("  a runnable Term-tree over the COLLECTION / ITERATION primitives —")
    print("  climbing the tower ONE tier, from scalar arithmetic to discrete-")
    print("  structure operations. Same read->ground->compute mechanism.")
    return True


def prove_base_primitives():
    banner("1. THE BASE COLLECTION / ITERATION PRIMITIVES (reused DSL Terms)")
    print("  exposed in the compute tower the SAME way gt/lt/divisor_sum are; each")
    print("  mirrors a DSL Term variant (no new Rust). The collection OPERAND is a")
    print("  representation — a range 1..n or a small explicit set (a list).\n")
    checks = [
        ("range_incl 1..5   (range/iota)",
         {"range_incl": {"lo": 1, "hi": 5}}, [1, 2, 3, 4, 5]),
        ("cardinality {3,5,7} (Count)",
         {"cardinality": {"of": [3, 5, 7]}}, 3),
        ("member 4 in {1,2,4} (member)",
         {"member": {"elem": 4, "of": [1, 2, 4]}}, True),
        ("is_empty {}        (IsEmpty)",
         {"is_empty": {"of": []}}, True),
        ("intersection {1,2,3,4}&{2,4,6} (Intersect)",
         {"intersection": {"a": [1, 2, 3, 4], "b": [2, 4, 6]}}, [2, 4]),
        ("are_disjoint {1,2}&{3,4}",
         {"are_disjoint": {"a": [1, 2], "b": [3, 4]}}, True),
        ("count_where{k in 1..6 : k|6}  (Filter+Count binder)",
         {"count_where": {"source": {"range_incl": {"lo": 1, "hi": 6}},
                          "var": "k",
                          "predicate": {"divides": {"left": "k",
                                                    "right": 6}}}}, 4),
        ("sum_where{k in 1..4 : k}      (Fold binder)",
         {"sum_where": {"source": {"range_incl": {"lo": 1, "hi": 4}},
                        "var": "k", "value": "k"}}, 10),
    ]
    ok = True
    for label, meaning, want in checks:
        got = reason.solve(meaning, {})
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {label:45} -> {got!r:>12} (want {want!r}) "
              f"{'OK' if c_ok else 'X'}")
    print(f"\n  -> base collection / iteration primitives present + correct: {ok}")
    return ok


def _show_acquire(s, caps, name, definition, checks, ref, conversation=None):
    """READ an operation's definition -> GROUND as a runnable Term-tree over the
    collection primitives -> COMPUTE on examples. Returns (grounded_and_correct)."""
    print(f"  READ      : {definition!r}")
    res = cg.ground_computation(s, name, definition, capabilities=caps,
                                conversation=conversation)
    print(f"  COMPREHEND -> runnable Term-tree over the collection primitives:")
    print(f"    {json.dumps(res['term'])}")
    print(f"  parts (operations it composes over): {res['parts']}")
    if res.get("recursed"):
        for sub, sr in res["recursed"].items():
            print(f"  RECURSED on un-held operation {sub!r}: "
                  f"{'grounded-by-reading' if sr.get('grounded') else 'no'}")
    print(f"  GROUND    : grounded={res['grounded']}  "
          f"combination stored as a RUNNABLE tree? "
          f"{res.get('ground', {}).get('combination_is_tree')}")
    print(f"  COMPUTE   :")
    ok = res["grounded"]
    for n in checks:
        got = reason.solve({name: {"n": n}}, {}, capabilities=caps)
        want = ref(n)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"    {name}({n}) = {got!r:>6}  (want {want!r}) "
              f"{'OK' if c_ok else 'X'}")
    return ok


def prove_operations_acquired_by_reading():
    banner("2. OPERATIONS ACQUIRED BY READING (the tower climbs a tier)")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    # GENUINELY un-held: remove the closed-form divisor_count / totient so the
    # abstain -> acquire-by-reading flip is honest. The agent re-derives them as
    # count-where over a range — NOT the prime-factorisation closed form.
    caps.pop("divisor_count", None)
    caps.pop("totient", None)

    print("  divisor_count and totient REMOVED from the held tower (abstain).")
    print("  The agent re-derives them by READING — as a count over a range, not")
    print("  the held prime-factorisation closed form.\n")

    print("  --- OPERATION 1: divisor_count(n) := count{k in 1..n : k|n} ---")
    dc_ok = _show_acquire(
        s, caps, "divisor_count",
        "divisor_count(n) = count{k in 1..n : k|n}",
        [12, 7, 28, 1], _ref_divisor_count)

    print("\n  --- OPERATION 2: totient(n) := count{k in 1..n : gcd(k,n) = 1} ---")
    tot_ok = _show_acquire(
        s, caps, "totient",
        "totient(n) = count{k in 1..n : gcd(k,n) = 1}",
        [9, 12, 1, 7], _ref_totient)

    overall = dc_ok and tot_ok
    print(f"\n  -> at least 2 OPERATIONS acquired BY READING, grounded over the")
    print(f"     collection / iteration primitives, computing correctly: {overall}")
    return overall, s, caps


def prove_boundary_moved_up(s, caps):
    banner("3. THE BOUNDARY MOVED UP — a concept that NEEDED divisor_count now "
           "COMPUTES")
    print("  is_prime(n) := divisor_count(n) = 2. It was understood-not-computable")
    print("  (it needed the divisor_count OPERATION). Now divisor_count was")
    print("  acquired by reading -> is_prime composes over it and COMPUTES.\n")

    # Fresh substrate; divisor_count is itself un-held -> the compute descent
    # READS it (fed definition) and grounds it, THEN is_prime computes over it.
    s2 = _native.Substrate()
    gr.open_grounding_productions(s2)
    caps2 = dict(reason.CAPABILITIES)
    caps2.pop("divisor_count", None)
    caps2.pop("prime", None)

    class Conv:
        _definition_feed = {
            "divisor_count": "divisor_count(n) = count{k in 1..n : k|n}"}

    before = "is_prime" not in caps2
    print(f"  ABSTAIN   : 'is_prime' held? {not before}  (abstains)")
    res = cg.ground_computation(
        s2, "is_prime", "is_prime(n) = divisor_count(n) = 2",
        capabilities=caps2, conversation=Conv())
    print(f"  READ      : 'is_prime(n) = divisor_count(n) = 2'")
    print(f"  THE DESCENT recurses on the un-held OPERATION divisor_count, grounds")
    print(f"    it by reading its count-where definition, then composes is_prime:")
    recursed = list(res.get("recursed", {}).keys())
    print(f"    recursed on: {recursed}")
    print(f"  COMPUTE (was understood-not-computable):")
    ok = res["grounded"] and before and "divisor_count" in recursed
    for n in [7, 12, 2, 1, 13, 15]:
        got = reason.solve({"is_prime": {"n": n}}, {}, capabilities=caps2)
        want = _ref_is_prime(n)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"    is_prime({n}) = {got!r:>6}  (want {want!r}) "
              f"{'OK' if c_ok else 'X'}")
    print(f"\n  -> the boundary moved up: is_prime computes BECAUSE divisor_count")
    print(f"     was acquired by reading: {ok}")
    return ok


def prove_still_named_higher_boundary():
    banner("4. THE BOUNDARY IS STILL HONEST + NAMED — the NEXT tier does NOT "
           "compose over the collection primitives")
    print("  An operation over a RICHER structure — a boundary operator on a")
    print("  manifold (what a cobordism/homology invariant needs) — does NOT")
    print("  reduce to range / count / set primitives. The agent reads it, reports")
    print("  NOT computable, naming the missing lower operation.\n")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    class Conv:
        # 'boundary_operator' is the higher-structure op; its definition does NOT
        # compose over the collection primitives (no fed computational def, and no
        # relational template) -> the descent cannot ground it as a computation
        # nor (here, no wiki) as a cohering concept -> it is NOT a held collection
        # primitive: the parent is reported NOT computable, naming it.
        _definition_feed = {}

    res = cg.ground_computation(
        s, "homology_rank",
        "homology_rank(x) = boundary_operator(x) + 1",
        capabilities=caps, conversation=Conv())
    print(f"  READ      : 'homology_rank(x) = boundary_operator(x) + 1'")
    print(f"  grounded(computable)? {res['grounded']}")
    print(f"  reason: {res['reason']}")
    named = ("boundary_operator" in (res.get("understood_not_computable") or [])
             or "boundary_operator" in res.get("reason", ""))
    boundary_ok = (not res["grounded"]) and named
    print(f"\n  -> the higher-structure operation does NOT compose over the")
    print(f"     collection primitives; NOT computable, naming boundary_operator")
    print(f"     (the next tier — topological/algebraic ops): {boundary_ok}")
    print(f"  HONEST: the tower climbed ONE tier (collection / discrete-structure")
    print(f"  ops). Research-math ops are the next tier, same mechanism. HLE")
    print(f"  research-math correct stays ~0.")
    return boundary_ok


def prove_no_regression():
    banner("5. NO REGRESSION — scalar compute-grounding + held tower intact")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    caps.pop("lcm", None)
    ok = True

    # scalar compute-grounding (lcm / perfect / triangular / abundant) intact.
    cases = [
        ("lcm", "lcm(a,b) = a*b/gcd(a,b)", {"a": 4, "b": 6}, 12),
        ("is_perfect_number",
         "a perfect number is a number equal to the sum of its proper divisors",
         {"n": 28}, True),
        ("triangular_number",
         "the nth triangular number is the sum of the first n integers",
         {"n": 10}, 55),
    ]
    for concept, definition, args, want in cases:
        cg.ground_computation(s, concept, definition, capabilities=caps)
        got = reason.solve({concept: args}, {}, capabilities=caps)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {concept:18} {args} -> {got!r:>6} (want {want!r}) "
              f"{'OK' if c_ok else 'X'}")

    # abundant_number over a read-grounded aliquot_sum (the wired sub-concept
    # recursion intact).
    caps_a = dict(reason.CAPABILITIES)
    for c in ("aliquot_sum", "abundant_number"):
        caps_a.pop(c, None)

    class _Conv:
        _definition_feed = {"aliquot_sum": "aliquot_sum(n) = divisor_sum(n) - n"}

    cg.ground_computation(s, "abundant_number",
                          "abundant_number(n) = aliquot_sum(n) > n",
                          capabilities=caps_a, conversation=_Conv())
    for n, want in {12: True, 8: False, 18: True}.items():
        got = reason.solve({"abundant_number": {"n": n}}, {}, capabilities=caps_a)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  abundant_number({n}) -> {got!r:>6} (want {want!r}) "
              f"{'OK' if c_ok else 'X'}")

    # the held scalar tower (gcd / sumsq via divisor_sum / closed-form
    # divisor_count + totient on the MODULE registry untouched).
    tower = [
        ("gcd 48,36", {"gcd": {"a": 48, "b": 36}}, 12),
        ("sumsq via divisor_sum 28", {"divisor_sum": {"of": 28}}, 56),
        ("held divisor_count 12", {"divisor_count": {"of": 12}}, 6),
        ("held totient 9", {"totient": {"of": 9}}, 6),
        ("gt 5>3", {"gt": {"left": 5, "right": 3}}, True),
    ]
    for label, meaning, want in tower:
        got = reason.solve(meaning, {}, capabilities=reason.CAPABILITIES)
        t_ok = (got == want)
        ok = ok and t_ok
        print(f"  {label:26} -> {got!r:>6} (want {want!r}) "
              f"{'OK' if t_ok else 'X'}")

    # module-level registry not mutated for read-grounded concepts.
    untouched = all(c not in reason.CAPABILITIES
                    for c in ("is_prime", "abundant_number", "homology_rank"))
    print(f"  module-level reason.CAPABILITIES unmutated for read-grounded "
          f"concepts? {untouched}")
    ok = ok and untouched
    print(f"\n  -> no regression: {ok}")
    return ok


def main():
    banner("ACQUIRE COLLECTION OPERATIONS BY READING — climb the compute tower "
           "one tier")
    principle_ok = prove_principle()
    base_ok = prove_base_primitives()
    ops_ok, s, caps = prove_operations_acquired_by_reading()
    boundary_up_ok = prove_boundary_moved_up(s, caps)
    higher_ok = prove_still_named_higher_boundary()
    noregress_ok = prove_no_regression()

    banner("SUMMARY")
    rows = [
        ("0. the agent's principle, applied to operations", principle_ok),
        ("1. base collection / iteration primitives (reused DSL Terms)", base_ok),
        ("2. >=2 OPERATIONS acquired BY READING (divisor_count, totient)",
         ops_ok),
        ("3. boundary MOVED UP (is_prime computes via acquired divisor_count)",
         boundary_up_ok),
        ("4. higher boundary STILL NAMED (boundary_operator not computable)",
         higher_ok),
        ("5. no regression (scalar compute + wired recursion + held tower)",
         noregress_ok),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: the agent climbed the compute tower ONE TIER by READING — it")
    print("acquired math OPERATIONS over DISCRETE STRUCTURES (count-where /")
    print("divisor_count / totient / set ops) from their definitions, grounded as")
    print("runnable Term-trees over the collection / iteration primitives (range /")
    print("count / filter / member / intersection), and a concept that needed them")
    print("(is_prime) now COMPUTES — the understood-not-computable boundary moved")
    print("up. Same read->ground-as-computation->compute self-extension, now over")
    print("OPERATIONS not just scalar concepts.")
    print("TIER REACHED: collection / discrete-structure operations over range /")
    print("explicit-set representations. TIER NOT REACHED: topological / algebraic")
    print("operations on richer structures (a boundary operator / homology — what")
    print("cobordism needs); the agent reads them but reports NOT computable,")
    print("naming the missing lower op. HLE research-math correct stays ~0 —")
    print("honest; the boundary just moved up a tier.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
