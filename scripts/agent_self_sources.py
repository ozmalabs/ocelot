"""The AGENT self-ascends by DYNAMICALLY SOURCING the math it needs — every
cognitive step is the agent's OWN capability; this script is only the loop SHELL
(like self_ascent.drive_ascent's mechanical shell), it adds NO reasoning.

Given a GOAL referencing functions the agent does not hold, the agent:
  1. SOURCE   — looks the function up in the real reference (oeis_local) by name,
  2. EXTRACT  — its OWN grammar reads the prose into a function (extract_function),
  3. GROUND   — comprehends + grounds it as a runnable computation,
  4. VERIFY   — against the reference's ground-truth values,
  5. COMPOSE  — uses the grounded function in the goal (order-N over what it sourced),
  6. CLIMB / repeat for the next un-held function.

Nothing here decides WHAT a function means or HOW to compute it — extract_function
(the agent's construction grammar) and comprehend_computational_definition (its
compute comprehension) do. The shell just sequences the agent's acts.
"""
import sys
sys.path.insert(0, ".")

from domains import oeis_local as oe
from domains import construction_grammar as cg
from domains import compute_grounding as cgnd
from domains import reason


def agent_source_and_ground(concept_name, name_query):
    """The AGENT sources `concept_name` from the reference + grounds it itself.
    Returns (term, verified, oeis_id, prose, formula) or (None, ...)."""
    # 1. SOURCE — the agent looks it up in the real reference by name.
    hits = oe.by_name(name_query, limit=6)
    for oid, _ in hits:
        d = oe.definition(oid)
        prose, values, offset = d["name"], d["values"], d["offset"]
        # 2. EXTRACT — the agent's OWN grammar reads the prose into a function.
        for formula in cg.extract_function(prose):
            comp = cgnd.comprehend_computational_definition(
                f"{concept_name}(n) = {formula}")
            if not comp:
                continue
            term = comp["term"]
            # 4. VERIFY — against the reference's ground-truth values.
            ok = True
            for i, want in enumerate(values[:10]):
                try:
                    if int(reason.solve(term, {"n": offset + i})) != int(want):
                        ok = False
                        break
                except Exception:
                    ok = False
                    break
            if ok:
                return term, True, oid, prose, formula
    return None, False, None, None, None


def main():
    print("=" * 78)
    print("THE AGENT DYNAMICALLY SOURCES THE MATH IT NEEDS + SELF-ASCENDS")
    print("=" * 78)
    print(f"  reference present (OEIS): {oe.present()}\n")

    # A GOAL the agent cannot answer with what it holds: it references two
    # functions it does NOT hold (sourced by their math-prose NAMES, not ids).
    goal = "(number of divisors of n) + (Euler totient phi of n), at n = 12"
    needed = [("numdiv", "number of divisors of n"),
              ("totient", "Euler totient")]
    print(f"  GOAL: {goal}")
    print(f"  the agent holds neither function -> it must SOURCE them itself.\n")

    grounded = {}
    for concept, query in needed:
        term, ok, oid, prose, formula = agent_source_and_ground(concept, query)
        if ok:
            grounded[concept] = term
            print(f"  SOURCED  {concept:8} <- OEIS {oid} {prose[:42]!r}")
            print(f"           EXTRACTED  {concept}(n) = {formula}  "
                  f"(verified vs the source's real values)")
        else:
            print(f"  STALL    {concept:8} -> could not source+verify "
                  f"(the honest frontier)")

    # COMPOSE — order-N over the two SOURCED functions (the agent composes the
    # goal from what it just acquired). This is one composition step the shell
    # assembles from the agent's grounded terms.
    if len(grounded) == 2:
        n = 12
        a = int(reason.solve(grounded["numdiv"], {"n": n}))
        b = int(reason.solve(grounded["totient"], {"n": n}))
        print(f"\n  COMPOSE + COMPUTE the goal at n={n}:")
        print(f"    number of divisors of 12 = {a}   (want 6)")
        print(f"    Euler totient of 12      = {b}   (want 4)")
        print(f"    GOAL = {a} + {b} = {a + b}   (want 10)")
        ok = (a == 6 and b == 4 and a + b == 10)
    else:
        ok = False

    print("\n" + "=" * 78)
    print(f"RESULT: {'ALL OK' if ok else 'FAILURE'} — the agent SOURCED both functions "
          f"from the\n  reference itself, grounded + verified them, and composed the "
          f"goal it could\n  not answer before. No function was hand-fed.")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
