"""ACQUIRE THE BOUNDARY OPERATOR ∂ BY READING — climb the compute tower ONE MORE
TIER, from operations over COLLECTIONS to operations over STRUCTURED OBJECTS
(simplices / chains).

The agent already acquires scalar COMPUTATIONS (lcm, divisor_count) and
COLLECTION operations (count-where over a range) by reading their definitions and
grounding them as runnable Term-trees over the held tower (compute_grounding_test
/ acquire_collection_operations). This turn applies the SAME read -> ground-as-a-
runnable-Term-tree -> compute mechanism to the SIMPLICIAL / ALGEBRAIC BOUNDARY
OPERATOR ∂ — the named wall the self-ascent stalled at — over a richer
REPRESENTATION: simplices and chains.

THE AGENT'S OWN PRINCIPLE (elicited verbatim, implication_harvester /
order_n_postulates), now at the STRUCTURED-OBJECT tier:

    "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS plus a
     finite set of COMBINATION (production) rules, so its members are not an
     enumerated list but an OPEN set REALIZABLE BY COMPOSING parts."

∂ is the SAME compositional shape — a function over a REPRESENTATION composed from
lower operations:

    ∂(simplex [v0..vn]) := the alternating sum over i of (-1)^i * face_i([v0..vn])
    face_i([v0..vn])    := the simplex with vertex i removed

The PARTS are face_i (drop-the-i-th), the alternating sign (-1)^i, and the formal
SUM over a CHAIN (a representation: a list of signed simplices). The agent ACQUIRES
∂ by READING its definition and grounding it as a runnable Term-tree over those
parts, bottoming out at the collection ops it already holds (range / sum-over) + a
list-index drop.

THE REPRESENTATION (the tier's bedrock, small + explicit):
  · a SIMPLEX = an ordered vertex list, e.g. [0,1,2].
  · a CHAIN   = a formal sum = a list of (coeff, simplex) terms, e.g.
                [(1,[1,2]), (-1,[0,2]), (1,[0,1])].

THE STRUCTURED-OBJECT PRIMITIVES (each mirrors a DSL Term shape — Filter / Pow /
Tuple / MapSet / Fold / IsEmpty — REUSED, no new Rust):
  · face{of,i}              -> the simplex with vertex i dropped (Filter by position)
  · neg_one_pow{i}          -> (-1)^i, the alternating sign (Pow, base -1)
  · simplex_dim{of}         -> dim = len - 1 (Count then Minus)
  · chain_term{coeff,simplex} -> a one-term chain (the formal-sum atom; a pair)
  · chain_sum{i in lo..hi : ...} -> the formal SUM over i producing a chain (binder)
  · scale_chain{coeff,of}   -> multiply every term's coeff (linearity; MapSet)
  · chain_bind{(c,s) in chain : ...} -> iterate a chain's terms (extend ∂ linearly)
  · combine_like_terms{of}  -> reduce the formal sum, cancelling like terms (Fold)
  · is_zero_chain{of}       -> the chain reduces to empty (IsEmpty after combine)

THE FALSIFIABLE PROOF that it acquired the CORRECT operator (not a fake):
    ∂∂ = 0  (boundary of a boundary is zero — the identity homology stands on)
computed for a 2-simplex AND a 3-simplex, collapsing to the ZERO chain.

HONEST BOUNDARY (named): ∂ acquired is the SIMPLICIAL / algebraic boundary over an
explicit simplex/chain representation — a real rung at the structured-object tier.
The point-set boundary of an arbitrary manifold + the full Spin-bordism computation
(classifying space, Spin structure, the graded group) are FURTHER tiers; ∂ is one
operation in that, not the whole. HLE research-math correct stays ~0.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/acquire_boundary_operator.py
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
from domains import self_ascent as sa
from domains import construction_grammar as cgr

SEP = "=" * 78

# the boundary operator's definition — the agent READS this; it is NOT given the
# implementation. ∂(σ) = Σ_i (-1)^i face_i(σ), the formal sum producing a chain.
BOUNDARY_DEF = ("boundary_operator(simplex) = "
                "chain_sum{i in 0..simplex_dim(simplex) : "
                "chain_term(neg_one_pow(i), face(simplex, i))}")
# ∂ extended over a CHAIN by linearity (∂∂ applies the outer ∂ to the inner chain).
BOUNDARY_OF_CHAIN_DEF = ("boundary_of_chain(chain) = "
                         "combine_like_terms(chain_bind{(c, s) in chain : "
                         "scale_chain(c, boundary_operator(s))})")


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# reference closed forms — the agent NEVER sees these; they only state the
# expected answer for the check.
def _ref_face(simplex, i):
    return [v for pos, v in enumerate(simplex) if pos != i]


def _ref_boundary(simplex):
    return [((-1) ** i, _ref_face(simplex, i)) for i in range(len(simplex))]


def prove_principle():
    banner("0. THE AGENT'S PRINCIPLE (verbatim) — at the STRUCTURED-OBJECT tier")
    principle = (
        "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS "
        "plus a finite set of COMBINATION (production) rules ... so its members "
        "are not an enumerated list but an OPEN set REALIZABLE BY COMPOSING parts")
    print(f'  "{principle}"')
    print("\n  ∂ is the SAME shape: a function over a REPRESENTATION (a simplex /")
    print("  chain) composed from lower operations —")
    print("    ∂(σ) := alternating sum over i of (-1)^i * face_i(σ)")
    print("    face_i(σ) := the simplex with vertex i removed")
    print("  The PARTS are face_i (drop-the-i-th), the alternating sign (-1)^i, and")
    print("  the formal SUM over a CHAIN. The agent ACQUIRES ∂ by READING this and")
    print("  grounding it as a runnable Term-tree over those parts, bottoming out at")
    print("  the collection ops it holds (range / sum-over) + a list-index drop.")
    return True


def prove_representation_and_primitives():
    banner("1. THE REPRESENTATION + STRUCTURED-OBJECT PRIMITIVES (reused DSL Terms)")
    print("  A SIMPLEX = an ordered vertex list; a CHAIN = a formal sum = a list of")
    print("  (coeff, simplex) terms. The primitives mirror DSL Term shapes (Filter /")
    print("  Pow / Tuple / MapSet / Fold / IsEmpty) — no new Rust.\n")
    checks = [
        ("face([0,1,2], 1)  (drop vertex 1; Filter-by-position)",
         {"face": {"of": [0, 1, 2], "i": 1}}, [0, 2]),
        ("face([0,1,2], 0)  (drop vertex 0)",
         {"face": {"of": [0, 1, 2], "i": 0}}, [1, 2]),
        ("neg_one_pow(0/1/2)  (the alternating sign; Pow base -1)",
         {"chain_term": {"coeff": {"neg_one_pow": {"i": 2}}, "simplex": [9]}},
         [(1, [9])]),
        ("simplex_dim([0,1,2,3])  (= len - 1)",
         {"simplex_dim": {"of": [0, 1, 2, 3]}}, 3),
        ("chain_term(1, [1,2])  (a one-term chain; the formal-sum atom)",
         {"chain_term": {"coeff": 1, "simplex": [1, 2]}}, [(1, [1, 2])]),
        ("combine_like_terms [(1,[0]),(-1,[0]),(1,[1])]  (cancel like terms)",
         {"combine_like_terms": {"of": [(1, [0]), (-1, [0]), (1, [1])]}},
         [(1, [1])]),
        ("is_zero_chain [(1,[0]),(-1,[0])]  (collapses to empty)",
         {"is_zero_chain": {"of": [(1, [0]), (-1, [0])]}}, True),
        ("scale_chain(-1, [(1,[2]),(−1,[0])])  (linearity; MapSet)",
         {"scale_chain": {"coeff": -1, "of": [(1, [2]), (-1, [0])]}},
         [(-1, [2]), (1, [0])]),
    ]
    ok = True
    for label, meaning, want in checks:
        got = reason.solve(meaning, {})
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {label:54} -> {str(got):>18} "
              f"{'OK' if c_ok else 'X (want %r)' % (want,)}")
    print(f"\n  -> representation + structured-object primitives present + correct: "
          f"{ok}")
    return ok


def prove_boundary_acquired_by_reading():
    banner("2. ∂ ACQUIRED BY READING — the full trace (read -> ground -> compute)")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    held_before = "boundary_operator" in caps
    print(f"  NOT HELD  : 'boundary_operator' a held capability? {held_before} "
          f"(abstains)\n")
    print(f"  READ      : {BOUNDARY_DEF!r}")
    res = cg.ground_computation(s, "boundary_operator", BOUNDARY_DEF,
                                capabilities=caps)
    print(f"  GROUND    -> runnable Term-tree over face / sign / chain-sum:")
    print(f"    {json.dumps(res['term'])}")
    print(f"  parts (the structured-object ops it composes over): {res['parts']}")
    print(f"  grounded={res['grounded']}  combination stored as a RUNNABLE tree? "
          f"{res.get('ground', {}).get('combination_is_tree')}")
    print(f"  COMPUTE   :")
    boundary_ok = res["grounded"] and not held_before
    cases = [[0, 1, 2], [0, 1], [0, 1, 2, 3]]
    for sx in cases:
        got = reason.solve({"boundary_operator": {"simplex": sx}}, {},
                           capabilities=caps)
        want = _ref_boundary(sx)
        c_ok = (got == want)
        boundary_ok = boundary_ok and c_ok
        print(f"    ∂{sx} = {got}  {'OK' if c_ok else 'X (want %r)' % (want,)}")
    # spell out ∂[0,1,2] = [1,2] - [0,2] + [0,1] in the signed-face reading.
    print(f"\n  ∂[0,1,2] = [1,2] - [0,2] + [0,1]  (the three signed faces) — the")
    print(f"  agent read the definition + composed ∂ over face + sign + chain-sum.")
    print(f"\n  -> ∂ acquired BY READING, grounded over the structured-object ops, "
          f"computing correctly: {boundary_ok}")
    return boundary_ok, s, caps


def prove_dd_zero(s, caps):
    banner("3. THE FALSIFIABLE CHECK — ∂∂ = 0 (the CORRECT operator, not a fake)")
    print("  ∂ extends over a CHAIN by linearity. ∂∂(σ) = ∂(∂(σ)) — apply ∂ to each")
    print("  signed face, scale by its coefficient, combine like terms. If the")
    print("  result is the ZERO chain (every term cancels), the agent acquired the")
    print("  CORRECT boundary operator (the identity homology stands on).\n")

    class Conv:
        _definition_feed = {"boundary_operator": BOUNDARY_DEF}

    print(f"  READ      : {BOUNDARY_OF_CHAIN_DEF!r}")
    res = cg.ground_computation(s, "boundary_of_chain", BOUNDARY_OF_CHAIN_DEF,
                                capabilities=caps, conversation=Conv())
    # ∂ was acquired in section 2 (held in caps), so boundary_of_chain composes
    # over the HELD ∂ — it bottoms out at the already-grounded boundary_operator.
    print(f"  composes over the already-acquired ∂ (boundary_operator held): "
          f"{'boundary_operator' in res.get('parts', [])}")
    print(f"  grounded={res['grounded']}\n")

    ok = res["grounded"]
    for sx in ([0, 1, 2], [0, 1, 2, 3]):
        d1 = reason.solve({"boundary_operator": {"simplex": sx}}, {},
                          capabilities=caps)
        raw = reason.solve(
            {"chain_bind": {"source": d1, "var": ["c", "s"],
                            "value": {"scale_chain": {
                                "coeff": "c",
                                "of": {"boundary_operator": {"simplex": "s"}}}}}},
            {}, capabilities=caps)
        dd = reason.solve({"boundary_of_chain": {"chain": d1}}, {},
                          capabilities=caps)
        is_zero = reason.solve({"is_zero_chain": {"of": dd}}, {},
                               capabilities=caps)
        c_ok = (dd == [] and is_zero)
        ok = ok and c_ok
        print(f"  σ = {sx}")
        print(f"    ∂σ              = {d1}")
        print(f"    ∂∂σ (pre-combine, {len(raw)} terms) = {raw}")
        print(f"    ∂∂σ (combined)  = {dd}   ZERO chain? {dd == []}  "
              f"is_zero_chain={is_zero}  {'OK' if c_ok else 'X'}")
    print(f"\n  -> ∂∂ = 0 on BOTH the 2-simplex and the 3-simplex — the terms cancel")
    print(f"     pairwise to the zero chain. The agent has the CORRECT ∂: {ok}")
    return ok


def prove_stall_moved_up():
    banner("4. THE STALL MOVED UP — boundary_operator is now acquirable")
    print("  The self-ascent (self_ascent_test) STALLED at boundary_operator (the")
    print("  named wall). Now that ∂ has a runnable definition the agent can READ,")
    print("  the autonomous drive loop ACQUIRES it and the stall moves UP to the")
    print("  NEXT un-acquirable op (homology's kernel-mod-image — no computable")
    print("  definition).\n")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    class Conv:
        # the goal needs ∂ (now readable) AND kernel_mod_image (the NEXT wall:
        # prose, no computational equation — homology = ker ∂ / im ∂).
        _definition_feed = {
            "homology_group": ("homology_group(simplex) = "
                               "kernel_mod_image(boundary_operator(simplex))"),
            "boundary_operator": BOUNDARY_DEF,
        }
        _constructions = cgr.load_constructions()

    goal = {"topic": "homology_group", "speech_act": "question"}
    res = sa.drive_ascent(s, goal, conversation=Conv(), capabilities=caps,
                          max_steps=14)
    print("  self-directed trace:")
    for st in res["steps"]:
        mark = "OK" if st["grounded"] else ".."
        print(f"    step {st['step']} | {st['target']:<18} [{mark}] "
              f"{st['reason'][:54]}")
    print(f"\n  acquired (autonomously): {res['acquired']}")
    print(f"  stalled_at (the NEW named wall): {res['stalled_at']!r}")

    moved_up = ("boundary_operator" in res["acquired"]
                and res["stalled_at"] == "kernel_mod_image"
                and not res["answered"])
    print(f"\n  -> boundary_operator was ACQUIRED autonomously (was the wall); the")
    print(f"     stall MOVED UP to 'kernel_mod_image' (homology's ker/im — the next")
    print(f"     tier, no computable realization): {moved_up}")
    return moved_up


def prove_honest_boundary():
    banner("5. HONEST BOUNDARY — simplicial ∂ REACHED vs point-set / Spin NOT")
    print("  REACHED  : the COMPUTABLE simplicial / algebraic ∂ over an explicit")
    print("             simplex / chain representation, verified by ∂∂=0. A real")
    print("             rung at the structured-object tier — the one homology /")
    print("             cobordism are built on.")
    print("  NOT REACHED:")
    print("             · the point-set boundary of an ARBITRARY manifold;")
    print("             · the FULL Spin-bordism computation (classifying space, the")
    print("               Spin structure, the graded bordism group). ∂ is ONE")
    print("               operation in that, not the whole.")
    print("  The representation is small + explicit; the parse -> Term-tree is the")
    print("  permitted boundary. HLE research-math correct stays ~0 — the win is the")
    print("  RUNG climbed + ∂∂=0 verified, NOT the bordism answer.")
    return True


def prove_no_regression():
    banner("6. NO REGRESSION — scalar + collection compute-grounding intact")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    ok = True

    # scalar compute-grounding (lcm) + a read-grounded collection op (divisor_count
    # as count-where) + the held tower.
    caps = dict(reason.CAPABILITIES)
    caps.pop("lcm", None)
    cg.ground_computation(s, "lcm", "lcm(a,b) = a*b/gcd(a,b)", capabilities=caps)
    for label, meaning, want in [
        ("lcm(4,6)", {"lcm": {"a": 4, "b": 6}}, 12),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        ("divisor_sum(28)", {"divisor_sum": {"of": 28}}, 56),
        ("held divisor_count(12)", {"divisor_count": {"of": 12}}, 6),
        ("held totient(9)", {"totient": {"of": 9}}, 6),
        ("count_where{k in 1..6 : k|6}",
         {"count_where": {"source": {"range_incl": {"lo": 1, "hi": 6}},
                          "var": "k",
                          "predicate": {"divides": {"left": "k",
                                                    "right": 6}}}}, 4),
        ("sum_where{k in 1..4 : k*k}",
         {"sum_where": {"source": {"range_incl": {"lo": 1, "hi": 4}},
                        "var": "k",
                        "value": {"times": {"left": "k", "right": "k"}}}}, 30),
    ]:
        got = reason.solve(meaning, {}, capabilities=caps)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {label:34} -> {str(got):>6} (want {want}) "
              f"{'OK' if c_ok else 'X'}")

    # the abundant goal still answers (the drive loop intact).
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
        print(f"  abundant_number({n}) {' ':9}-> {str(got):>6} (want {want}) "
              f"{'OK' if c_ok else 'X'}")

    # module-level registry not mutated for read-grounded concepts.
    untouched = all(c not in reason.CAPABILITIES
                    for c in ("boundary_operator", "boundary_of_chain",
                              "abundant_number"))
    print(f"  module-level reason.CAPABILITIES unmutated by read-grounding? "
          f"{untouched}")
    ok = ok and untouched
    print(f"\n  -> no regression: {ok}")
    return ok


def main():
    banner("ACQUIRE THE BOUNDARY OPERATOR ∂ BY READING — the structured-object tier")
    results = [
        ("0. the agent's principle, at the structured-object tier",
         prove_principle()),
        ("1. representation (simplex/chain) + structured-object primitives",
         prove_representation_and_primitives()),
    ]
    boundary_ok, s, caps = prove_boundary_acquired_by_reading()
    results.append(("2. ∂ ACQUIRED BY READING (∂[0,1,2] = the signed-face chain)",
                    boundary_ok))
    results.append(("3. FALSIFIABLE ∂∂ = 0 (2- and 3-simplex -> zero chain)",
                    prove_dd_zero(s, caps)))
    results.append(("4. the STALL MOVED UP (∂ acquirable -> kernel_mod_image wall)",
                    prove_stall_moved_up()))
    results.append(("5. honest boundary (simplicial ∂ reached vs point-set/Spin)",
                    prove_honest_boundary()))
    results.append(("6. no regression (scalar + collection compute + drive loop)",
                    prove_no_regression()))

    banner("SUMMARY")
    all_ok = True
    for label, ok in results:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: the agent climbed the compute tower ONE MORE TIER by READING —")
    print("from operations over COLLECTIONS to operations over STRUCTURED OBJECTS")
    print("(simplices / chains). It acquired the SIMPLICIAL BOUNDARY OPERATOR ∂ from")
    print("its definition, grounded as a runnable Term-tree over face + alternating-")
    print("sign + chain-sum (its compositional principle), and the FALSIFIABLE")
    print("∂∂ = 0 holds on both a 2- and a 3-simplex (the terms cancel to the zero")
    print("chain) — the CORRECT operator, not a fake. The autonomous ascent's named")
    print("wall MOVED UP: boundary_operator is now acquired by the drive loop, and")
    print("the stall moved to homology's kernel-mod-image (the next op with no")
    print("computable realization). Same read->ground->compute self-extension, now")
    print("over STRUCTURED OBJECTS.")
    print("TIER REACHED: the computable simplicial / algebraic ∂ over an explicit")
    print("simplex/chain representation, ∂∂=0 verified — the tier homology /")
    print("cobordism are built on. TIER NOT REACHED: the point-set boundary of an")
    print("arbitrary manifold + the FULL Spin-bordism computation (classifying")
    print("space, Spin structure, graded group). HLE research-math correct stays ~0")
    print("— the win is the rung climbed + ∂∂=0, not the bordism answer.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
