"""PROVE the jabberwock SOLVES ITS OWN PROBLEM (Gap 3): a math question it
ABSTAINS on (an ungrounded computational concept) is solved by its OWN machinery.

The agent's OWN derived principle — a compositional WHOLE = grounded PARTS + a
finite set of COMBINATION rules — EXTENDED to COMPUTATION: a computation is
grounded operands + grounded operations composed into a Term-tree that EVALUATES.

The self-directed solve CHAINS the agent's own machinery:

    ABSTAIN (concept ungrounded -> no capability)
      -> DIAGNOSE (the concept is not in the held tower)
      -> READ (its computational definition)
      -> GROUND AS AN EXECUTABLE COMPOSITION (parse -> a meaning-Term over the
         GROUNDED reason tower; ground_concept stores the RUNNABLE Term-tree as
         the concept's `combination`, closing the loose end; recurse on un-held
         operands)
      -> COMPUTE (reason.solve evaluates the tree over the bound operands)
      -> ANSWER (the abstain flips to a correct answer)

This script proves it on 3 concepts the agent ACQUIRES BY READING — lcm,
is_perfect_number, triangular_number — shows the executable combination is a
RUNNABLE tree (not a named string), shows the recursive descent, and names the
HONEST research-math frontier (a definition that won't compose over held
primitives -> abstain). NO regression on the held tower.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/compute_grounding_test.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import _native
from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cg


SEP = "=" * 76


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# reference closed forms — used ONLY to state the expected answer (the agent
# never sees these; it computes from the parsed definition).
def _ref_lcm(a, b):
    import math
    return math.lcm(a, b)


def _ref_perfect(n):
    return sum(d for d in range(1, n) if n % d == 0) == n


def _ref_triangular(n):
    return n * (n + 1) // 2


def main():
    s = _native.Substrate()
    gr.open_grounding_productions(s)

    # The agent's LIVE held tower, copied so the demo is additive. lcm ships in
    # the tower; we REMOVE it from the working copy so the abstain->solve flip is
    # HONEST (the agent genuinely lacks it, then acquires it by reading).
    caps = dict(reason.CAPABILITIES)
    caps.pop("lcm", None)

    # ------------------------------------------------------ 0. THE PRINCIPLE
    banner("0. THE AGENT'S OWN PRINCIPLE (elicited verbatim) — extended to "
           "COMPUTATION")
    principle = (
        "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS "
        "plus a finite set of COMBINATION (production) rules ... so its members "
        "are not an enumerated list but an OPEN set REALIZABLE BY COMPOSING parts")
    print("  derived principle (implication_harvester / order_n_postulates):")
    print(f"    \"{principle}\"")
    print("  EXTENDED to computation: a COMPUTATION is the SAME shape — grounded")
    print("  OPERANDS + grounded OPERATIONS composed into a Term-tree that")
    print("  EVALUATES. Grounding a computational concept = reading its")
    print("  definition + composing it as an EXECUTABLE Term-tree over the held")
    print("  computable primitives, then evaluating.")

    # ------------------------------------------ 1. THE SELF-DIRECTED SOLVE x3
    cases = [
        ("lcm", "lcm(a,b) = a*b/gcd(a,b)",
         [({"a": 4, "b": 6}, _ref_lcm(4, 6)),
          ({"a": 21, "b": 6}, _ref_lcm(21, 6)),
          ({"a": 8, "b": 12}, _ref_lcm(8, 12))]),
        ("is_perfect_number",
         "a perfect number is a number equal to the sum of its proper divisors",
         [({"n": 6}, _ref_perfect(6)), ({"n": 28}, _ref_perfect(28)),
          ({"n": 12}, _ref_perfect(12))]),
        ("triangular_number",
         "the nth triangular number is the sum of the first n integers",
         [({"n": 5}, _ref_triangular(5)), ({"n": 10}, _ref_triangular(10)),
          ({"n": 100}, _ref_triangular(100))]),
    ]

    all_ok = True
    for concept, definition, checks in cases:
        banner(f"1. SELF-DIRECTED SOLVE — '{concept}'")

        # ABSTAIN: before, the concept has no capability -> solve raises (the
        # agent abstains, cannot answer).
        a0, _b0 = checks[0]
        abstained = concept not in caps
        before_err = None
        try:
            reason.solve({concept: a0}, {}, capabilities=caps)
        except KeyError as e:
            before_err = str(e)
        print(f"  ABSTAIN  : '{concept}' in held tower? {concept in caps}  "
              f"-> solve raises: {before_err}")

        # READ + GROUND-AS-EXECUTABLE-COMPOSITION + INSTALL.
        print(f"  READ     : {definition!r}")
        res = cg.ground_computation(s, concept, definition, capabilities=caps)
        print(f"  COMPREHEND -> executable Term-tree (a meaning-Term over held "
              f"primitives):")
        print(f"    {json.dumps(res['term'])}")
        print(f"  parts (operand primitives) : {res['parts']}   "
              f"params (Var leaves) : {res['params']}")
        print(f"  GROUND   : grounded={res['grounded']}  "
              f"combination stored as a RUNNABLE TREE? "
              f"{res['ground']['combination_is_tree']}  "
              f"built_from edges +{res['ground']['edges_added']}")

        # COMPUTE + ANSWER: the abstain flips to a correct answer.
        print(f"  COMPUTE + ANSWER (was ABSTAIN):")
        concept_ok = res["grounded"]
        for args, want in checks:
            got = reason.solve({concept: args}, {}, capabilities=caps)
            ok = (got == want)
            concept_ok = concept_ok and ok
            print(f"    {concept}({args}) = {got!r:>8}  (want {want!r}) "
                  f"{'OK' if ok else 'X'}")
        all_ok = all_ok and abstained and concept_ok
        print(f"  -> abstain FLIPPED to a correct answer by the agent's own "
              f"read->ground-as-computation->compute? {abstained and concept_ok}")

    # ----------------------------------------- 2. EXECUTABLE COMBINATION CLOSED
    banner("2. THE LOOSE END CLOSED — a grounded concept's `combination` is now "
           "a RUNNABLE Term-tree, not a named string")
    cid = gr._find_concept(s, "lcm")
    combo = s.node(cid)["attrs"].get("combination")
    combo_tree = json.loads(combo)
    print(f"  lcm.combination (graph data): {combo}")
    print(f"  is a Term-tree dict (not a 'rel(a,b)' string)? "
          f"{isinstance(combo_tree, dict)}")
    # evaluate the STORED tree directly (read off the node) over fresh operands.
    direct = cg.run_combination(combo_tree, {"a": 9, "b": 15}, caps)
    want = _ref_lcm(9, 15)
    print(f"  evaluate the STORED tree over {{a:9, b:15}} = {direct} (want {want})")
    combo_ok = isinstance(combo_tree, dict) and direct == want
    all_ok = all_ok and combo_ok

    # ------------------------------------------------ 3. RECURSIVE DESCENT
    banner("3. RECURSIVE DESCENT — an operand that is itself an un-held "
           "computational concept is grounded first")
    s3 = _native.Substrate()
    gr.open_grounding_productions(s3)
    caps3 = dict(reason.CAPABILITIES)
    caps3.pop("lcm", None)

    class _Conv:
        # lcm3 composes over lcm, which is ITSELF un-held here — read its def.
        _definition_feed = {"lcm": "lcm(a,b) = a*b/gcd(a,b)"}

    res3 = cg.ground_computation(s3, "lcm3", "lcm3(a,b,c) = lcm(lcm(a,b),c)",
                                 capabilities=caps3, conversation=_Conv())
    print(f"  lcm3 references the un-held 'lcm' -> RECURSE -> ground 'lcm' first")
    print(f"  recursed on: {list(res3.get('recursed', {}).keys())}")
    print(f"  lcm3 grounded: {res3['grounded']}")
    got3 = reason.solve({"lcm3": {"a": 4, "b": 6, "c": 10}}, {},
                        capabilities=caps3)
    want3 = 60
    print(f"  lcm3(4,6,10) = {got3} (want {want3})")
    descent_ok = (res3["grounded"] and "lcm" in res3.get("recursed", {})
                  and got3 == want3)
    all_ok = all_ok and descent_ok

    # ------------------------------------------------ 4. HONEST FRONTIER
    banner("4. HONEST RESEARCH-MATH FRONTIER — a definition that won't compose "
           "over held primitives -> grounds=False -> the agent ABSTAINS")
    bordism_def = ("a bordism is an equivalence that relates manifolds whose "
                   "disjoint union is the boundary of a higher manifold")
    res_b = cg.ground_computation(s, "bordism", bordism_def, capabilities=caps)
    print(f"  READ     : {bordism_def!r}")
    print(f"  grounded : {res_b['grounded']}")
    print(f"  reason   : {res_b['reason']}")
    print(f"  bordism in tower (still abstains)? {'bordism' not in caps}")
    frontier_ok = (not res_b["grounded"]) and ("bordism" not in caps)
    all_ok = all_ok and frontier_ok

    # ------------------------------------------------ 5. NO REGRESSION
    banner("5. NO REGRESSION — the held tower still dispatches; the module-level "
           "registry is untouched (additive on a copy)")
    checks = [
        ("gcd of 48,36", {"gcd": {"a": 48, "b": 36}}, 12),
        ("sum_first_n_squares not asserted here (tower base)", None, None),
        ("91 prime", {"prime": {"arg": 91}}, False),
        ("factorial 6", {"factorial": {"of": 6}}, 720),
        ("13th fibonacci", {"nth_fibonacci": {"of": 13}}, 233),
        ("divisor_sum 28", {"divisor_sum": {"of": 28}}, 56),
    ]
    reg_ok = True
    for label, meaning, want in checks:
        if meaning is None:
            continue
        got = reason.solve(meaning, {}, capabilities=caps)
        ok = (got == want)
        reg_ok = reg_ok and ok
        print(f"  {label:22} -> {got!r:>8} (want {want!r}) {'OK' if ok else 'X'}")
    # the held arithmetic primitives just added are present + correct.
    for label, meaning, want in [
            ("minus 10-3", {"minus": {"left": 10, "right": 3}}, 7),
            ("div 12/4", {"div": {"left": 12, "right": 4}}, 3),
            ("mod 17%5", {"mod": {"left": 17, "right": 5}}, 2),
            ("eq 6==6", {"eq": {"left": 6, "right": 6}}, True)]:
        got = reason.solve(meaning, {}, capabilities=reason.CAPABILITIES)
        ok = (got == want)
        reg_ok = reg_ok and ok
        print(f"  {label:22} -> {got!r:>8} (want {want!r}) {'OK' if ok else 'X'}")
    # module-level registry never mutated for the read-grounded concepts.
    untouched = all(c not in reason.CAPABILITIES
                    for c in ("triangular_number", "is_perfect_number", "lcm3"))
    print(f"  module-level reason.CAPABILITIES unmutated for read-grounded "
          f"concepts? {untouched}")
    reg_ok = reg_ok and untouched
    all_ok = all_ok and reg_ok

    # ------------------------------------------------------------- SUMMARY
    banner("SUMMARY")
    rows = [
        ("1. self-directed solve x3 (abstain -> read -> ground-as-computation "
         "-> compute -> correct)", all_ok),
        ("2. executable combination CLOSED (runnable Term-tree, not a string)",
         combo_ok),
        ("3. recursive DESCENT (un-held operand grounded first)", descent_ok),
        ("4. honest research-math FRONTIER (won't compose -> abstain)",
         frontier_ok),
        ("5. NO REGRESSION (held tower + added primitives; registry untouched)",
         reg_ok),
    ]
    ok_all = True
    for label, ok in rows:
        ok_all = ok_all and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if ok_all else 'FAILURES ABOVE'}")
    print()
    print("LEARNING: the agent SOLVED a problem it COULDN'T — self-directed. It")
    print("read a computational concept it lacked (lcm / is_perfect_number /")
    print("triangular_number), grounded it AS A COMPUTATION over what it holds,")
    print("and answered. The mechanism (read -> ground-as-computation -> compute)")
    print("is the agent EXTENDING ITS OWN compositional principle to derivation.")
    print("HONEST: research-math definitions don't compose over the held basis")
    print("(primitive-scope + grounding-depth frontier) — correct, not optimised.")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
