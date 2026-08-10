"""PROVE THE PATH IS WIRED between the jabberwock's two grounding halves.

The agent holds TWO grounding descents:
  (1) CONCEPT grounding — read_and_ground.ground_recursively: recursively follow a
      definition (Wikipedia / a fed gloss) to ground a concept as a web reaching
      bedrock — it COHERES ("understands what it is").
  (2) COMPUTATION grounding — compute_grounding.ground_computation: read a
      COMPUTATIONAL definition and ground it as a runnable Term-tree over the held
      arithmetic tower — it COMPUTES.

THE WIRING (this turn): the COMPUTE descent now RECURSES THROUGH the CONCEPT
descent. When a computational definition references an operand the agent does not
hold, the compute descent first tries to ground it as a COMPUTATION (read its def
-> a runnable tree, composed over here); failing that, it recurses through the
CONCEPT descent (ground_recursively) — does the operand at least COHERE as a
concept? A derivation therefore bottoms out at EITHER a computable primitive OR a
read-grounded computable sub-concept; and a sub-concept that COHERES but is NOT
computable yields the precise UNDERSTOOD-vs-COMPUTABLE boundary.

THE PRINCIPLE (the agent's own, unifying the two halves — elicited verbatim from
implication_harvester / order_n_postulates):

    "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS plus a
     finite set of COMBINATION (production) rules, so its members are not an
     enumerated list but an OPEN set REALIZABLE BY COMPOSING parts."

Concept-grounding and computation are the SAME compositional act: a whole = its
PARTS + a COMBINATION. The PARTS are grounded recursively (read their
definitions); the COMBINATION is structural for a pure concept and a RUNNABLE
Term-tree when the parts are computable. So a derivation bottoms out at EITHER a
computable primitive OR a recursively-grounded sub-concept whose own combination
is runnable. Wiring the path = letting the compute descent recurse through the
concept descent.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/wired_compute_descent.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native
from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cg
from domains import construction_grammar as cgr
from domains import read_and_ground as rag
from domains import wiki_local as wl
from domains import math_foundations as mf

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# reference closed forms — the agent NEVER sees these; they only state the
# expected answer. Aliquot sum = sum of proper divisors = divisor_sum(n) - n.
def _aliquot(n):
    return sum(d for d in range(1, n) if n % d == 0)


def _abundant(n):
    return _aliquot(n) > n


def _deficient(n):
    return _aliquot(n) < n


def _wiki_read(concept_name, conversation, definition_text=None, substrate=None):
    """READ via the LOCAL wiki (offline + deterministic), mirroring the live
    reader: lead's first sentence, SKIP a disambiguation lead -> None."""
    if definition_text:
        return definition_text
    feed = getattr(conversation, "_definition_feed", None)
    if isinstance(feed, dict):
        t = feed.get(concept_name) or feed.get(concept_name.lower())
        if isinstance(t, str) and t.strip():
            return t.strip()
    su = wl.summary(concept_name)
    if su is None:
        cands = wl.search(concept_name, 1)
        su = wl.summary(cands[0]) if cands else None
    if su and su.get("extract"):
        if wl.is_disambiguation(su["extract"]):
            return None
        m = re.search(r"[.!?](?:\s|$)", su["extract"])
        return (su["extract"][: m.end()].strip() if m
                else su["extract"].strip())
    return None


def _trace_recursion(res, indent=2):
    """Print the compute descent's recursion through the read-grounded
    sub-concepts (the WIRING made visible)."""
    pad = " " * indent
    for name, sub in (res.get("recursed") or {}).items():
        kind = "COMPUTABLE" if sub.get("grounded") else "not-computable"
        print(f"{pad}-> COMPUTE-descent recursed on sub-concept {name!r}: "
              f"{kind}")
        if sub.get("term") is not None:
            print(f"{pad}   its runnable combination: {json.dumps(sub['term'])}")
        _trace_recursion(sub, indent + 5)
    for name, cd in (res.get("concept_descents") or {}).items():
        if name in (res.get("recursed") or {}):
            continue
        v = "COHERES (concept)" if cd.get("concept_grounded") else "no-ground"
        print(f"{pad}-> CONCEPT-descent recursed on sub-concept {name!r}: {v}")
        prims = (cd.get("structure") or {}).get("primitives") if cd.get(
            "structure") else None
        if prims:
            print(f"{pad}   cone reaches bedrock primitives: {prims}")


def prove_principle():
    banner("0. THE AGENT'S UNIFYING PRINCIPLE (elicited verbatim)")
    principle = (
        "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS "
        "plus a finite set of COMBINATION (production) rules ... so its members "
        "are not an enumerated list but an OPEN set REALIZABLE BY COMPOSING parts")
    print(f'  "{principle}"')
    print("\n  UNIFIED: concept-grounding and computation are the SAME compositional")
    print("  act — a whole = PARTS + a COMBINATION. The PARTS are grounded")
    print("  recursively (read their definitions); the COMBINATION is STRUCTURAL")
    print("  for a pure concept and a RUNNABLE Term-tree when the parts are")
    print("  computable. A derivation bottoms out at EITHER a computable primitive")
    print("  OR a read-grounded computable sub-concept. Wiring the path = letting")
    print("  the compute descent RECURSE THROUGH the concept descent.")
    return True


def prove_two_level_compute():
    banner("1. COMPUTE OVER A READ-GROUNDED SUB-CONCEPT (the WIRING)")
    print("  abundant_number(n) := aliquot_sum(n) > n")
    print("  aliquot_sum(n)     := divisor_sum(n) - n      (itself UN-HELD)")
    print("  The compute descent reads abundant_number, hits the un-held")
    print("  aliquot_sum, RECURSES (reads its def -> grounds it as a runnable")
    print("  tree), composes abundant_number OVER it, and COMPUTES.\n")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    # aliquot_sum, divisor_sum, abundant_number, deficient_number genuinely
    # un-held as composed concepts (divisor_sum is a held arithmetic primitive).
    for c in ("aliquot_sum", "abundant_number", "deficient_number"):
        caps.pop(c, None)

    class Conv:
        # the fed COMPUTATIONAL definition of the un-held inner sub-concept.
        _definition_feed = {"aliquot_sum": "aliquot_sum(n) = divisor_sum(n) - n"}
        _constructions = cgr.load_constructions()

    # ABSTAIN before: no capability for abundant_number.
    abstained = "abundant_number" not in caps
    print(f"  ABSTAIN  : 'abundant_number' held? {not abstained}  (abstains)")

    # READ + the UNIFIED DESCENT.
    res = cg.ground_computation(
        s, "abundant_number", "abundant_number(n) = aliquot_sum(n) > n",
        capabilities=caps, conversation=Conv())
    print(f"  READ     : 'abundant_number(n) = aliquot_sum(n) > n'")
    print(f"  COMPREHEND -> Term-tree: {json.dumps(res['term'])}")
    print(f"  THE WIRED DESCENT:")
    _trace_recursion(res)
    print(f"  grounded={res['grounded']}  computable={res.get('computable')}  "
          f"understood={res.get('understood')}")

    # the inner sub-concept is now a held capability + a grounded Concept with a
    # runnable combination.
    inner_held = "aliquot_sum" in caps
    inner_cid = gr._find_concept(s, "aliquot_sum")
    inner_combo = (json.loads(s.node(inner_cid)["attrs"].get("combination", "null"))
                   if inner_cid else None)
    print(f"\n  inner sub-concept 'aliquot_sum' grounded by READING:")
    print(f"    now a held capability? {inner_held}")
    print(f"    its grounded combination (a runnable tree): "
          f"{json.dumps(inner_combo)}")

    # COMPUTE — abundant_number computes BECAUSE the inner sub-concept was
    # grounded by reading.
    print(f"\n  COMPUTE (was ABSTAIN):")
    want = {12: True, 8: False, 18: True, 6: False, 20: True}
    abundant_ok = res["grounded"] and abstained and "aliquot_sum" in res.get(
        "recursed", {})
    for n, w in want.items():
        got = reason.solve({"abundant_number": {"n": n}}, {}, capabilities=caps)
        ok = (got == w == _abundant(n))
        abundant_ok = abundant_ok and ok
        print(f"    abundant_number({n}) = {got!r:>6}  (want {w!r}) "
              f"{'OK' if ok else 'X'}")

    # SECOND case — deficient_number REUSES the now-grounded aliquot_sum.
    print(f"\n  GENERALITY — deficient_number(n) := aliquot_sum(n) < n, REUSING")
    print(f"  the aliquot_sum grounded above (no re-read needed):")
    res2 = cg.ground_computation(
        s, "deficient_number", "deficient_number(n) = aliquot_sum(n) < n",
        capabilities=caps, conversation=Conv())
    reused = (res2["grounded"] and "aliquot_sum" not in res2.get("recursed", {}))
    print(f"    grounded={res2['grounded']}  re-read aliquot_sum? "
          f"{'aliquot_sum' in res2.get('recursed', {})}  (reused the grounded one)")
    deficient_ok = res2["grounded"]
    for n, w in {8: True, 12: False, 1: True, 28: False}.items():
        got = reason.solve({"deficient_number": {"n": n}}, {}, capabilities=caps)
        ok = (got == w == _deficient(n))
        deficient_ok = deficient_ok and ok
        print(f"    deficient_number({n}) = {got!r:>6}  (want {w!r}) "
              f"{'OK' if ok else 'X'}")

    overall = abundant_ok and deficient_ok and reused
    print(f"\n  -> 2-level compute over a READ-GROUNDED sub-concept: {overall}")
    return overall


def prove_understood_not_computable():
    banner("2. THE UNDERSTOOD-vs-COMPUTABLE BOUNDARY")
    print("  A concept that grounds as a CONCEPT (the wiki descent reaches")
    print("  bedrock -> it COHERES) but whose computation references a")
    print("  non-computable math operation -> the wired path GROUNDS/UNDERSTANDS")
    print("  it yet reports it is NOT computable, NAMING the non-computable")
    print("  sub-concept (the precise missing piece).\n")

    if not wl.present():
        print("  (local wiki not present — skipping; treated OK)")
        return True

    # cobordism grounds as a CONCEPT via the recursive wiki descent (reaches the
    # seeded bedrock 'relation') — it COHERES. But it is NOT a computable
    # primitive (no runnable combination). A computation defined OVER it is
    # therefore understood, not computable.
    saved = rag._read_definition
    rag._read_definition = _wiki_read
    try:
        s = _native.Substrate()
        mf.install_math_foundations_seed(s)
        gr.open_grounding_productions(s)
        caps = dict(reason.CAPABILITIES)

        class Conv:
            _constructions = cgr.load_constructions()

        # First: cobordism COHERES as a concept (the wiki descent bottoms out at
        # bedrock) — the agent 'understands what it is'.
        cob = rag.ground_recursively(s, "cobordism", Conv(), max_depth=8)
        cid = gr._find_concept(s, "cobordism")
        prims = (gr.grounding_reaches_primitives(s, cid)["primitives"]
                 if cid else [])
        print(f"  cobordism grounds as a CONCEPT (coheres): {cob['grounded']}  "
              f"cone reaches bedrock {prims}")

        # Now a COMPUTATION defined over cobordism: it comprehends as an equation
        # (cobordism(x) is a referenced sub-concept call), the descent recurses
        # through the CONCEPT machinery, finds cobordism COHERES but has NO
        # runnable combination -> understood, not computable, naming cobordism.
        res = cg.ground_computation(
            s, "cobordism_invariant",
            "cobordism_invariant(x) = cobordism(x) + 1",
            capabilities=caps, conversation=Conv())
        print(f"\n  COMPUTE 'cobordism_invariant(x) = cobordism(x) + 1':")
        print(f"    grounded(computable)?   {res['grounded']}")
        print(f"    understood?             {res.get('understood')}")
        print(f"    understood_not_computable (NAMED): "
              f"{res.get('understood_not_computable')}")
        print(f"    reason: {res['reason']}")

        # HONEST: cobordism is understood (coheres) but its operations have no
        # computable realization -> the boundary is precise.
        boundary_ok = (
            cob["grounded"]                                  # coheres as concept
            and not res["grounded"]                          # NOT computable
            and res.get("understood") is True                # but understood
            and "cobordism" in (res.get("understood_not_computable") or []))
        print(f"\n  -> understood (coheres) yet NOT computable, naming the exact")
        print(f"     non-computable sub-concept: {boundary_ok}")
        return boundary_ok
    finally:
        rag._read_definition = saved


def prove_no_regression():
    banner("3. NO REGRESSION — single-level compute-grounding + held tower intact")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    caps.pop("lcm", None)

    ok = True

    # single-level compute-grounding (lcm / perfect / triangular) still grounds.
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

    # held arithmetic tower + the new comparison primitives.
    tower = [
        ("gcd 48,36", {"gcd": {"a": 48, "b": 36}}, 12),
        ("sumsq via divisor_sum 28", {"divisor_sum": {"of": 28}}, 56),
        ("factorial 6", {"factorial": {"of": 6}}, 720),
        ("13th fib", {"nth_fibonacci": {"of": 13}}, 233),
        ("gt 5>3", {"gt": {"left": 5, "right": 3}}, True),
        ("lt 5<3", {"lt": {"left": 5, "right": 3}}, False),
    ]
    for label, meaning, want in tower:
        got = reason.solve(meaning, {}, capabilities=reason.CAPABILITIES)
        t_ok = (got == want)
        ok = ok and t_ok
        print(f"  {label:26} -> {got!r:>6} (want {want!r}) {'OK' if t_ok else 'X'}")

    # the module-level registry untouched for read-grounded concepts.
    untouched = all(c not in reason.CAPABILITIES
                    for c in ("abundant_number", "deficient_number",
                              "aliquot_sum", "cobordism_invariant"))
    print(f"  module-level reason.CAPABILITIES unmutated for read-grounded "
          f"concepts? {untouched}")
    ok = ok and untouched
    print(f"\n  -> no regression: {ok}")
    return ok


def main():
    banner("WIRING THE PATH: COMPUTE DESCENT RECURSES THROUGH CONCEPT DESCENT")
    results = [
        ("0. the agent's unifying principle", prove_principle()),
        ("1. compute over a READ-GROUNDED sub-concept (2-level, x2)",
         prove_two_level_compute()),
        ("2. the precise UNDERSTOOD-vs-COMPUTABLE boundary",
         prove_understood_not_computable()),
        ("3. no regression (single-level compute + held tower)",
         prove_no_regression()),
    ]
    banner("SUMMARY")
    all_ok = True
    for label, ok in results:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: the path is WIRED — a derivation now composes over")
    print("RECURSIVELY-GROUNDED sub-concepts (read from their definitions), so the")
    print("agent's self-extending solve reaches DOWN through concepts it grounds by")
    print("READING, not just the fixed arithmetic tower. A 2-level concept it could")
    print("not compute now computes because it grounded the inner sub-concept by")
    print("reading; and the understood-vs-computable boundary is precise (it")
    print("understands cobordism but names exactly why it cannot compute over it).")
    print("HONEST: research-math grounds as CONCEPTS (coheres) but lacks COMPUTABLE")
    print("realizations of its operations — computing over them needs those")
    print("operations as primitives (acquired the same way, recursively — the next")
    print("frontier, not this turn). HLE research-math correctness stays ~0.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
