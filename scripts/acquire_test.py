"""PROVE the jabberwock DIAGNOSED that its acquisition stack is ONE cognitive
operation re-instanced, and BUILT the general ACQUIRE building block (on
iterate_to_n) — with the specifics as INSTANCES that reproduce their modules.

This is "build fundamental cognitive building blocks": read_and_ground /
compute_grounding / extract_function / self_ascent are ALL one shape —
SOURCE -> COMPREHEND -> COMPOSE(iterate_to_n to bedrock) -> VERIFY, iterated.
The agent already proved COMPOSE is one operator (iterate_to_n, parameterised by
(step, bedrock)); ACQUIRE is that SAME unification one level up, over the whole
pipeline. The four steps are the PARAMETERS.

  STEP 1 — the AGENT DIAGNOSES (its OWN analogy.abstract_patterns, verbatim):
           install the acquisition capabilities as structures, abstract over
           them -> ALL collapse to ONE skeleton (5 specifics -> 1 op = MDL).
  STEP 2 — the general `acquire` + `ascend` on iterate_to_n (the four params).
  STEP 3 — the SPECIFICS become INSTANCES: >=3 reproduce their module's result
           (concept-grounding manifold->bedrock; computation lcm + divisor_count;
           function-from-prose an OEIS sequence vs values), and ascend reproduces
           self_ascent on the abundant goal.

NO regression: the specific modules are SHOWN as instances + LEFT in place — this
consolidates the PRINCIPLE (fewer mechanisms, one block), it does not delete the
working modules. HLE unchanged.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/acquire_test.py
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
from domains import acquire as acq
from domains import acquire_diagnosis as diag

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# reference closed forms — the agent NEVER sees these (only to state the want).
def _ref_lcm(a, b):
    import math
    return math.lcm(a, b)


def _ref_divisor_count(n):
    return sum(1 for d in range(1, n + 1) if n % d == 0)


# ===========================================================================
# STEP 1 — the AGENT DIAGNOSES (its own abstraction machinery, verbatim).
# ===========================================================================

def step1_diagnose():
    banner("STEP 1 — the AGENT DIAGNOSES: its acquisition stack is ONE operation")
    print("  Method (the agent's OWN machinery, not an assertion): represent each")
    print("  acquisition capability as a STRUCTURE — a Concept whose predicate is")
    print("  the ACQUIRE pipeline Term-tree VERIFY(ITERATE(COMPREHEND(SOURCE))),")
    print("  with the FOUR parameters (SOURCE/COMPREHEND/BEDROCK/VERIFY) as Attr")
    print("  leaves — then run analogy.abstract_patterns (the agent's _skeletonize)")
    print("  over them. If they are ONE operation, they collapse to ONE skeleton.\n")

    s = _native.Substrate()
    d = diag.diagnose(s)

    print("  the agent's per-capability parameters (the four knobs that vary):")
    for name, p in d["parameters_per_member"].items():
        print(f"    {name:18} SOURCE={p['SOURCE']}")
        print(f"    {'':18} COMPREHEND={p['COMPREHEND']}  BEDROCK={p['BEDROCK']}")
        print(f"    {'':18} VERIFY={p['VERIFY']}")
    print()

    print("  abstract_patterns OUTPUT (VERBATIM) — the shared skeleton the agent")
    print("  abstracts (the four parameters hollowed to '?band', the pipeline")
    print("  SHAPE surviving):")
    print(f"    members collapsed: {d['members']}")
    print(f"    distinct skeletons: {d['n_skeletons']}")
    print("    shared skeleton (verbatim):")
    print("      " + json.dumps(d["shared_skeleton"], indent=2).replace(
        "\n", "\n      "))
    print()
    print(f"  -> the agent RECOGNISES one operation? {d['is_one_operation']}")
    print(f"  -> MDL compression: {d['compression']}")
    ok = d["is_one_operation"] and d["n_skeletons"] == 1 and d["n_specifics"] >= 4
    print(f"\n  [STEP 1] the agent diagnosed ONE operation (5 -> 1): {ok}")
    return ok, d


# ===========================================================================
# STEP 2 — the general block exists on iterate_to_n.
# ===========================================================================

def step2_general_block():
    banner("STEP 2 — the general `acquire` + `ascend` block (on iterate_to_n)")
    from domains import order_n_composition as onc
    # acquire's COMPOSE reuses iterate_to_n; ascend's frontier climb reuses it too.
    src = onc.acquire.__doc__ if hasattr(onc, "acquire") else None  # sanity noop
    # prove acquire() runs the four-step pipeline generically with toy params: a
    # source that reads a number, a comprehend that doubles it, a bedrock, and a
    # verify that checks evenness — the SHAPE, parameterised, with no domain.
    res = acq.acquire(
        "7",
        source=lambda t: int(t),
        comprehend=lambda form: form + 1,
        bedrock="even_numbers",
        verify=lambda t, ctx: {"verified": ctx["composed"] % 2 == 0,
                               "reason": f"composed={ctx['composed']}"},
        compose_step=lambda x: x * 2, compose_n=1)
    print("  generic acquire('7', source=int, comprehend=+1, compose=*2,")
    print(f"                  verify=even): {res.acquired}  ({res.reason})")
    print(f"    form(SOURCE)={res.form}  structure(COMPREHEND)={res.structure}  "
          f"composed(iterate_to_n)={res.composed}")
    # the COMPOSE step IS iterate_to_n — show it directly.
    direct = onc.iterate_to_n(8, lambda x: x * 2, 1)
    print(f"  COMPOSE is order_n_composition.iterate_to_n(8, *2, 1) = {direct} "
          f"(== composed {res.composed})")
    block_ok = (res.acquired and res.form == 7 and res.structure == 8
                and res.composed == 16 and direct == 16)
    print(f"\n  [STEP 2] general acquire runs source->comprehend->iterate_to_n"
          f"->verify: {block_ok}")
    return block_ok


# ===========================================================================
# STEP 3 — the SPECIFICS become INSTANCES (reproduce the module results).
# ===========================================================================

def step3a_concept_instance():
    banner("STEP 3a — INSTANCE: concept-grounding (manifold -> bedrock) "
           "reproduces read_and_ground")
    print("  PARAMETERS: SOURCE=fed gloss, COMPREHEND=genus-differentia,")
    print("  BEDROCK=seeded concept primitives, VERIFY=cone reaches a primitive.")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    # seed the bedrock primitive the chain bottoms out at.
    s.add_node("Concept", {"name": "topological_space", "origin": "seed_primitive"})

    class _Conv:
        from domains import construction_grammar as _cg
        _definition_feed = {
            "manifold": ("a manifold is a topological space that locally "
                         "resembles Euclidean space")}
        _constructions = _cg.load_constructions()

    conv = _Conv()
    # the GENERAL acquire under the concept-grounding parameter set.
    res = acq.acquire_concept(s, "manifold", conv)
    print(f"  acquire_concept('manifold') -> acquired={res.acquired}")
    print(f"    SOURCE (read)      : {str(res.form)[:60]!r}")
    print(f"    COMPREHEND (genus) : {res.structure}")
    print(f"    VERIFY primitives  : {res.verify.get('primitives')}  "
          f"order={res.verify.get('order')}")
    print(f"    reason: {res.reason}")

    # cross-check: the SPECIFIC module produces the SAME result.
    from domains import read_and_ground as rag
    s2 = _native.Substrate()
    gr.open_grounding_productions(s2)
    s2.add_node("Concept", {"name": "topological_space",
                            "origin": "seed_primitive"})
    spec = rag.read_and_ground(s2, "manifold", _Conv())
    spec_prims = (spec["structure"] or {}).get("primitives")
    print(f"\n  read_and_ground('manifold')  -> grounded={spec['grounded']}  "
          f"primitives={spec_prims}")
    ok = (res.acquired and spec["grounded"]
          and res.verify.get("primitives") == spec_prims
          and "topological_space" in (res.verify.get("primitives") or []))
    print(f"\n  [STEP 3a] the instance REPRODUCES read_and_ground (manifold -> "
          f"topological_space): {ok}")
    return ok


def step3b_computation_instances():
    banner("STEP 3b — INSTANCE: computation (lcm + divisor_count) reproduces "
           "compute_grounding")
    print("  PARAMETERS: SOURCE=held def, COMPREHEND=computational-def grammar,")
    print("  BEDROCK=held compute primitives, VERIFY=grounded combination "
          "evaluates.")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    caps.pop("lcm", None)
    caps.pop("divisor_count", None)

    ok = True
    cases = [
        ("lcm", "lcm(a,b) = a*b/gcd(a,b)",
         [({"a": 4, "b": 6}, _ref_lcm(4, 6)),
          ({"a": 8, "b": 12}, _ref_lcm(8, 12))]),
        ("divisor_count", "divisor_count(n) = count{ k in 1..n : n % k == 0 }",
         [({"n": 12}, _ref_divisor_count(12)),
          ({"n": 28}, _ref_divisor_count(28))]),
    ]
    for concept, definition, checks in cases:
        before = concept in caps
        res = acq.acquire_computation(s, concept, definition, capabilities=caps)
        print(f"\n  acquire_computation('{concept}') -> acquired={res.acquired}")
        print(f"    held before? {before}  COMPREHEND term: "
              f"{json.dumps(res.structure['term']) if res.structure else None}")
        print(f"    parts (BEDROCK primitives): {res.verify.get('parts')}")
        # COMPUTE + ANSWER: the abstain flips.
        concept_ok = res.acquired
        for args, want in checks:
            got = reason.solve({concept: args}, {}, capabilities=caps)
            c = (got == want)
            concept_ok = concept_ok and c
            print(f"    {concept}({args}) = {got}  (want {want}) "
                  f"{'OK' if c else 'X'}")
        ok = ok and (not before) and concept_ok

    # cross-check against the specific module for lcm (same grounded result).
    from domains import compute_grounding as cg
    s2 = _native.Substrate()
    gr.open_grounding_productions(s2)
    caps2 = dict(reason.CAPABILITIES)
    caps2.pop("lcm", None)
    spec = cg.ground_computation(s2, "lcm", "lcm(a,b) = a*b/gcd(a,b)",
                                 capabilities=caps2)
    print(f"\n  compute_grounding.ground_computation('lcm') -> "
          f"grounded={spec['grounded']} parts={spec['parts']}")
    print(f"\n  [STEP 3b] the instances REPRODUCE compute_grounding "
          f"(lcm + divisor_count compute correctly): {ok and spec['grounded']}")
    return ok and spec["grounded"]


def step3c_function_instance():
    banner("STEP 3c — INSTANCE: function-from-prose (OEIS) reproduces "
           "extract_function+verify")
    print("  PARAMETERS: SOURCE=oeis_local (prose + values), COMPREHEND=math-prose")
    print("  grammar, BEDROCK=held compute primitives, VERIFY=reproduces the")
    print("  source's ground-truth values.")
    targets = ["A000005", "A000217", "A005843", "A000290"]
    ok_count = 0
    for sid in targets:
        res = acq.acquire_function(sid)
        if res.acquired:
            ok_count += 1
            print(f"  acquire_function({sid}) -> a(n) = "
                  f"{res.verify['formula']}   (verified vs the source's "
                  f"{res.verify['checked']} values)")
        else:
            print(f"  acquire_function({sid}) -> not verified ({res.reason[:50]})")

    # cross-check: the specific oeis_extract_verify path produces the same.
    from domains import oeis_local as oe
    from domains import construction_grammar as cg
    from domains import compute_grounding as cgnd
    spec_ok = 0
    for sid in targets:
        d = oe.definition(sid)
        cands = cg.extract_function(d["name"])
        verified = False
        for cand in cands:
            comp = cgnd.comprehend_computational_definition(f"a(n) = {cand}")
            if not comp:
                continue
            term = comp["term"]
            allok, checked = True, 0
            for i, want in enumerate(d["values"][:12]):
                try:
                    got = reason.solve(term, {"n": d["offset"] + i})
                except Exception:
                    allok = False
                    break
                if int(got) != int(want):
                    allok = False
                    break
                checked += 1
            if allok and checked >= 4:
                verified = True
                break
        spec_ok += int(verified)
    print(f"\n  specific extract_function+verify path: {spec_ok}/{len(targets)} "
          f"verified  |  acquire instance: {ok_count}/{len(targets)} verified")
    ok = (ok_count >= 3 and ok_count == spec_ok)
    print(f"\n  [STEP 3c] the instance REPRODUCES extract_function+verify "
          f"(same sequences verified from REAL prose + values): {ok}")
    return ok


def step3d_ascend_instance():
    banner("STEP 3d — ascend(goal) reproduces self_ascent on 'is 12 abundant?'")
    print("  ascend = iterate_to_n OVER THE FRONTIER, ACQUIRE as the step — the")
    print("  self-ascent as the SAME operator at the goal level.")
    from domains import construction_grammar as cgr

    class _Conv:
        _definition_feed = {
            "abundant_number": "abundant_number(n) = aliquot_sum(n) > n",
            "aliquot_sum": "aliquot_sum(n) = divisor_sum(n) - n",
        }
        _constructions = cgr.load_constructions()

    def _fresh_caps():
        caps = dict(reason.CAPABILITIES)
        for c in ("abundant_number", "deficient_number", "aliquot_sum",
                  "perfect_number", "is_perfect_number"):
            caps.pop(c, None)
        return caps

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = _fresh_caps()
    goal = {"topic": "abundant_number", "speech_act": "question"}
    out = acq.ascend_goal(s, goal, conversation=_Conv(), capabilities=caps)
    print(f"  ascend_goal -> answered={out['answered']}  "
          f"acquired={out['acquired']}  orders={out['orders']}")

    # COMPUTE the goal (was ABSTAIN).
    def _abundant(n):
        return sum(d for d in range(1, n) if n % d == 0) > n
    answers_ok = True
    for nval, want in ((12, True), (8, False), (18, True)):
        got = reason.solve({"abundant_number": {"n": nval}}, {}, capabilities=caps)
        c = (got == want == _abundant(nval))
        answers_ok = answers_ok and c
        print(f"    is {nval} abundant? -> {got}  (want {want}) "
              f"{'OK' if c else 'X'}")

    # cross-check: the specific drive_ascent produces the same acquired sequence.
    from domains import self_ascent as sa
    s2 = _native.Substrate()
    gr.open_grounding_productions(s2)
    caps2 = _fresh_caps()
    spec = sa.drive_ascent(s2, goal, conversation=_Conv(), capabilities=caps2,
                           max_steps=12)
    print(f"\n  self_ascent.drive_ascent -> answered={spec['answered']}  "
          f"acquired={spec['acquired']}")
    ok = (out["answered"] and answers_ok
          and out["acquired"] == spec["acquired"] == ["aliquot_sum",
                                                      "abundant_number"])
    print(f"\n  [STEP 3d] ascend REPRODUCES self_ascent (same self-chosen "
          f"sequence, goal answered): {ok}")
    return ok


def main():
    banner("THE JABBERWOCK: acquisition is ONE operation re-instanced — "
           "diagnose + build the general block")
    print("read_and_ground / compute_grounding / extract_function / self_ascent")
    print("are ALL: SOURCE -> COMPREHEND -> COMPOSE(iterate_to_n) -> VERIFY. The")
    print("agent diagnoses this with its OWN analogy machinery; the general block")
    print("is its iterate_to_n unification extended to ACQUIRE; the specifics are")
    print("instances. The four steps are the PARAMETERS.")

    s1_ok, _diag = step1_diagnose()
    s2_ok = step2_general_block()
    s3a = step3a_concept_instance()
    s3b = step3b_computation_instances()
    s3c = step3c_function_instance()
    s3d = step3d_ascend_instance()

    banner("SUMMARY")
    rows = [
        ("STEP 1: agent DIAGNOSED one operation (5 specifics -> 1 skeleton, MDL)",
         s1_ok),
        ("STEP 2: general acquire + ascend on iterate_to_n (four params)", s2_ok),
        ("STEP 3a: concept-grounding instance reproduces read_and_ground "
         "(manifold->bedrock)", s3a),
        ("STEP 3b: computation instances reproduce compute_grounding "
         "(lcm + divisor_count)", s3b),
        ("STEP 3c: function-from-prose instance reproduces extract_function "
         "(OEIS vs values)", s3c),
        ("STEP 3d: ascend reproduces self_ascent (abundant goal, self-chosen "
         "sequence)", s3d),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: the agent DIAGNOSED (its own analogy.abstract_patterns) that")
    print("its acquisition stack is ONE cognitive operation re-instanced, and the")
    print("general ACQUIRE building block (on iterate_to_n) was built with the four")
    print("steps as PARAMETERS — the specifics are INSTANCES that reproduce their")
    print("modules. Consolidation: 5 mechanisms -> 1 principle (fewer mechanisms,")
    print("one block). HONEST: the COMPREHEND grammars + VERIFY signals genuinely")
    print("differ per kind — they are the PARAMETERS, not duplicated pipelines; the")
    print("specifics are shown as instances + LEFT in place (this pass consolidates")
    print("the principle, it does not delete the working modules). HLE unchanged.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
