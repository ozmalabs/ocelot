"""PROVE: language UNDERSTANDING is now ORDER-N (recursive construction
composition on iterate_to_n) and reading-constructions are ACQUIRED BY READING —
so COMPREHENSION self-ascends the SAME way COMPUTATION does (one mechanism). The
"comprehension is the one unsolved parameter" wall dissolves into order-N + acquire.

THE TWO MOVES
  1. ORDER-N COMPREHENSION — a construction's SLOT content is itself parsed by
     (sub-)constructions, RECURSIVELY, bottoming out at a comprehension-BEDROCK (a
     member-form leaf / atomic term). A COMPLEX prose form the FLAT matcher
     returned NONE on now COMPREHENDS by COMPOSING constructions order-N
     (aggregator OVER a value-map OVER a member-set UNDER a filter) -> a COMPOSED
     structure -> grounds + computes + (where an OEIS sequence matches) VERIFIES vs
     the source's real values. The recursion = the agent's iterate_to_n.
  2. READ ABOUT HOW TO READ — the agent ACQUIRES a comprehension construction by
     READING its meta-definition ('the cubes of a set means each member multiplied
     by itself three times') via the acquire() block -> the construction is
     grounded (graph data) -> it now PARSES a form it couldn't before
     (before NONE -> read-meta -> after parses + reproduces).

THE FRONTIER (honest): push 'the kernel of the boundary operator modulo its image'
— order-N comprehension COMPOSES the homology STRUCTURE
modulo(kernel(boundary_operator), image(boundary_operator)); the boundary operator
ATOM is HELD (acquired earlier); the kernel/image/modulo OPERATIONS are un-held —
the NAMED next acquire-by-reading instance. Comprehension is no longer the wall: it
composes the structure; the residual is the operations, acquired the same way.

Faithful (CLAUDE.md): comprehension is the agent's OWN order-N operator
(order_n_composition.iterate_to_n) applied to the construction grammar (COMBINATION
= comprehend-the-slot, BEDROCK = atomic/held); reading-constructions are acquired
via the agent's acquire() block. No LLM, no Rust, no per-form code — the
constructions are graph DATA, composed + acquired.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/order_n_comprehension.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import construction_grammar as cg
from domains import compute_grounding as cgnd
from domains import oeis_local as oe
from domains import reason

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _eval_form(formula, offset, n_vals):
    comp = cgnd.comprehend_computational_definition("a(n) = " + formula)
    if not comp:
        return None
    out = []
    for i in range(n_vals):
        try:
            out.append(int(reason.solve(comp["term"], {"n": offset + i})))
        except Exception:
            return None
    return out


# ===========================================================================
# MOVE 1 — ORDER-N COMPREHENSION (recursive construction composition).
# ===========================================================================

def move1_order_n():
    banner("MOVE 1 — ORDER-N COMPREHENSION: complex prose the FLAT matcher returned "
           "NONE on COMPOSES recursively + VERIFIES vs the source's real values")
    print("  The slot of a construction is filled by RECURSIVELY comprehending its")
    print("  content (the agent's iterate_to_n: COMBINATION = comprehend-the-slot,")
    print("  BEDROCK = a member-form leaf). 'sum of [squares of [divisors of n]]' =")
    print("  aggregator(sum) OVER value-map(square) OVER member-set(divisors).\n")

    # complex, MULTI-LEVEL number-theory forms (real OEIS sequences). The PROSE
    # is the dataset's; the VALUES are the dataset's — nothing hand-fed.
    targets = [
        ("A001157", "sum of squares of divisors of n",
         "aggregator(sum) / value-map(squares) / member-set(divisors) — 3 tiers"),
        ("A001065", "sum of divisors of n that are less than n",
         "aggregator(sum) / member-set(divisors) / filter(less than n) — 3 tiers"),
        ("A001227", "number of odd divisors of n",
         "aggregator(number) / pre-filter(odd) / member-set(divisors) — 3 tiers"),
        ("A000203", "sum of divisors of n",
         "aggregator(sum) / member-set(divisors) — 2 tiers"),
    ]
    ok = True
    for sid, prose, tiers in targets:
        d = oe.definition(sid)
        flat = cg.extract_function(prose)   # NB includes the recursive path now;
        # show the FLAT-ONLY result by calling comprehend_recursive vs the seeded
        # flat clauses: the flat clause path is the WHOLE-STRING match.
        flat_only = [c["formula"] for c in cg.load_math_prose().get("clauses", [])
                     if c.get("clause") and c["clause"] in prose.lower()]
        rec = cg.comprehend_recursive(prose)
        # SELECT the verified composition against the source's real values.
        verified = None
        for f in rec:
            got = _eval_form(f, d["offset"], 8)
            if got == [int(x) for x in d["values"][:8]]:
                verified = f
                break
        print(f"  {sid}  {prose!r}")
        print(f"      composition tiers : {tiers}")
        print(f"      FLAT whole-string match (the clause path) : "
              f"{flat_only if flat_only else 'NONE'}")
        print(f"      ORDER-N composed structure : {rec[0] if rec else 'NONE'}")
        if verified:
            print(f"      -> grounds + computes -> {_eval_form(verified, d['offset'], 8)}")
            print(f"      -> MATCHES the source's real values "
                  f"{[int(x) for x in d['values'][:8]]}  VERIFIED")
        else:
            print("      -> NOT verified")
            ok = False
        print()

    print("  KEY: A001157 'sum of squares of divisors of n' was FLAT-NONE (no")
    print("  whole-string clause). A001065's flat clause WRONGLY gives the all-")
    print("  divisors sum; the source's values REJECT it and SELECT the composed")
    print("  proper-divisor form. Order-N comprehension feeds order-N computation.")
    print(f"\n  [MOVE 1] complex prose COMPOSES recursively + verifies: {ok}")
    return ok


# ===========================================================================
# MOVE 2 — READ ABOUT HOW TO READ (acquire a construction by reading).
# ===========================================================================

def move2_acquire_by_reading():
    banner("MOVE 2 — READ ABOUT HOW TO READ: ACQUIRE a comprehension construction "
           "by READING its meta-definition (the acquire() mechanism)")
    print("  The agent reads a 'PATTERN means STRUCTURE' meta-definition (how a")
    print("  math form maps to an operation) -> grounds it as a construction (graph")
    print("  data) via acquire() -> extends what it can comprehend. SOURCE=meta-def,")
    print("  COMPREHEND=parse-a-construction, BEDROCK=held constructions/ops,")
    print("  VERIFY=it parses an example (+ reproduces its values).\n")

    # 'cubes of' is deliberately NOT seeded (see math_prose_constructions.json).
    sid = "A001158"   # sum of cubes of divisors of n.
    d = oe.definition(sid)
    meta = "the cubes of a set means each member multiplied by itself three times"

    before = cg.extract_function(d["name"])
    print(f"  TARGET {sid}  {d['name']!r}")
    print(f"  BEFORE reading the meta-def : extract_function -> "
          f"{before if before else 'NONE'}  (cannot read 'cubes of')")
    print(f"\n  READ THE META-DEFINITION (how to read 'cubes of'):")
    print(f"    {meta!r}")
    res = cg.acquire_construction(
        "cubes_of", meta, example=d["name"],
        example_values=[int(x) for x in d["values"][:8]])
    print(f"\n  ACQUIRE -> acquired={res['acquired']}")
    print(f"    grounded construction : {res['construction']}")
    print(f"    VERIFY                : {res['reason']}")
    after = cg.extract_function(d["name"])
    print(f"\n  AFTER reading the meta-def  : extract_function -> {after}")
    if after:
        print(f"    -> grounds + computes -> {_eval_form(after[0], d['offset'], 8)}")
        print(f"    -> MATCHES the source's real values "
              f"{[int(x) for x in d['values'][:8]]}")
    ok = (not before) and res["acquired"] and bool(after) and \
        _eval_form(after[0], d["offset"], 8) == [int(x) for x in d["values"][:8]]
    print(f"\n  [MOVE 2] before(NONE) -> read-meta -> after(parses+reproduces): {ok}")
    return ok


# ===========================================================================
# MOVE 3 — THE RESEARCH FRONTIER (honest, precise).
# ===========================================================================

def move3_frontier():
    banner("MOVE 3 — THE RESEARCH FRONTIER: 'the kernel of the boundary operator "
           "modulo its image' — order-N COMPOSES the homology STRUCTURE")
    print("  This is the homology group H = ker(∂)/im(∂). Order-N comprehension")
    print("  composes the STRUCTURE recursively: [A] modulo [B] OVER kernel of [X]")
    print("  + image of [X] OVER the boundary operator. The possessive 'its image'")
    print("  resolves to the SAME operand the sibling kernel reads.\n")

    prose = "the kernel of the boundary operator modulo its image"
    flat = cg.extract_function(prose)
    r = cg.comprehend_structure(prose)
    print(f"  PROSE : {prose!r}")
    print(f"  FLAT matcher (extract_function) -> {flat if flat else 'NONE'}\n")
    print(f"  ORDER-N COMPOSED STRUCTURE :")
    print(f"    {r['repr']}")
    print(f"    (the agent COMPOSED the homology structure from the constructions)")
    print(f"\n  THE PRECISE RESIDUAL (where it still stalls):")
    print(f"    atom 'boundary operator' HELD (acquired earlier)? {r['atoms_held']}")
    print(f"    UN-HELD operations (the named next acquire) : {r['unheld_ops']}")
    print(f"\n  So comprehension is NO LONGER the wall: it COMPOSES the structure.")
    print(f"  The remaining gap is the kernel/image/modulo OPERATIONS — acquirable")
    print(f"  the SAME way by reading their meta-definitions ('the kernel of a map")
    print(f"  is the set of inputs it sends to zero') — the next acquire instance.")
    ok = (not flat) and r is not None and \
        r["repr"] == "modulo(kernel(boundary_operator), image(boundary_operator))" \
        and r["atoms_held"] and set(r["unheld_ops"]) == {"modulo", "kernel", "image"}
    print(f"\n  [MOVE 3] composes the homology STRUCTURE + names the residual ops: {ok}")
    return ok, r


def main():
    banner("ORDER-N COMPREHENSION + ACQUIRE-BY-READING — comprehension self-ascends "
           "the SAME way computation does (one mechanism)")
    print("Language understanding is now ORDER-N (recursive construction composition")
    print("on iterate_to_n) and reading-constructions are ACQUIRED BY READING (the")
    print("acquire() block). A complex prose that was FLAT-NONE comprehends by")
    print("composition; the agent reads about how to read a form, then can read it;")
    print("the frontier moves from 'comprehension is unsolved' to 'comprehension")
    print("composes the structure; the operations are the next acquire-by-reading'.")

    m1 = move1_order_n()
    m2 = move2_acquire_by_reading()
    m3, _r = move3_frontier()

    banner("SUMMARY")
    rows = [
        ("MOVE 1: ORDER-N comprehension (complex prose composes recursively + "
         "verifies vs real OEIS values; flat = NONE)", m1),
        ("MOVE 2: READ ABOUT HOW TO READ (acquire a construction by reading its "
         "meta-def; before-NONE -> after-parses+reproduces)", m2),
        ("MOVE 3: FRONTIER pushed (composes the homology STRUCTURE "
         "modulo(kernel(∂),image(∂)); residual = un-held ops, named)", m3),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: comprehension self-ascends like computation — ONE order-N +")
    print("acquire mechanism. The comprehension wall ('the one unsolved parameter')")
    print("dissolves: complex prose COMPOSES (order-N over the construction grammar),")
    print("new reading-constructions are ACQUIRED BY READING (the acquire block), and")
    print("at the frontier comprehension COMPOSES the homology structure — the")
    print("residual is the operations, the SAME acquire-by-reading instance next.")
    print("HONEST: HLE research-math correct stays ~0 (the kernel/image/modulo")
    print("operations remain to be acquired as runnable primitives); the win is")
    print("dissolving the comprehension wall, NOT solving the research math. The")
    print("non-prose-reducible residual stays the frontier: notation / diagrams /")
    print("'computed by the spectral sequence' as a procedure (not a compositional")
    print("definition); the recursive matcher's ambiguity handling is greedy/bounded;")
    print("the meta-construction parse covers regular 'PATTERN means STRUCTURE' forms.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
