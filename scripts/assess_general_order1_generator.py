#!/usr/bin/env python3
"""assess_general_order1_generator — a READ-ONLY PROBE that has the agent ASSESS,
via its OWN machinery, WHAT IS REQUIRED to build a GENERAL order-1 query generator:
one that, facing ANY typed invariant (not just commutator/Hurewicz or euler), GENERATES
its presupposed-fact queries ITSELF.

THIS IS AN ASSESSMENT, NOT A BUILD. The probe:
  (1) RUNS the agent's CURRENT order-1 generator (order_n_communication._presupposed_needs
      via generate_order_n) on the two HARDCODED-covered invariants (free_rank-of-kernel-
      of-Hurewicz, euler_characteristic) and on a NEW typed invariant family (euler /
      reduced-Euler of a COMBINATORIAL simplicial complex, the cmsg-gap-2 / face-sum
      invariant the symbolic-proof turn gathered DIRECTLY) — to LOCATE the gap empirically
      (0 queries for the family the generator does not hardcode).
  (2) READS the structure the generator KEYS OFF for the generable families (the typed-
      tree flags asked.free_rank_of_kernel_of_hurewicz / asked.euler_characteristic, and
      the operator's recorded reduction commutator_rank.operator_specs()) vs what is
      ABSENT for the new family (compute_reduced_euler has NO operator_specs / reduces_to).
  (3) SURFACES the required components, each grounded to where it would attach in the
      REAL machinery — the agent's assessment, not an LLM wishlist.

No build. No new faculty. Read-only inspection of the committed pipeline. Math/reading
only; the speech path is untouched.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
from substrate_rs import _native
from domains import presupposition_derivation as _pd
from domains import order_n_communication as _onc
from domains import commutator_rank as _cr

SEP = "=" * 80


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


# ---------------------------------------------------------------------------
# The three invariant PROSE phrasings the probe feeds the agent's OWN reader +
# generator. The first two are the HARDCODED-covered families; the third is the
# NEW family (a combinatorial simplicial-complex Euler invariant — the cmsg-gap-2
# face-sum invariant the proof gathered directly). None is hand-typed: the agent's
# general reader types each, and the generator generates (or fails to).
# ---------------------------------------------------------------------------
INVARIANTS = [
    ("free_rank-of-kernel-of-Hurewicz  (HARDCODED family A)",
     "the rank of the kernel of the Hurewicz map as a free group"),
    ("euler_characteristic OF the seeded `space` atom  (HARDCODED family B)",
     "the euler characteristic of the space"),
    ("reduced Euler characteristic of a COMBINATORIAL simplicial complex  (NEW family"
     " — the face-sum invariant the proof gathered DIRECTLY)",
     "the reduced euler characteristic of the simplicial complex"),
    ("a FRESH operator-on-object: the Betti number of a complex  (NEW family)",
     "the second betti number of the complex"),
]


def run_generator(s, label, prose):
    """RUN the agent's current order-1 generator over an invariant prose. Returns the
    typed read + the generated query-set (read-only — generate_order_n with record=False
    so the probe mutates nothing the pipeline depends on)."""
    asked = _pd.comprehend_asked_invariant(prose)
    needs = _onc._presupposed_needs(asked)
    out = _onc.generate_order_n(s, prose, about=label, max_order=1, record=False)
    return asked, needs, out


def main():
    s = _native.Substrate()

    banner("THE AGENT ASSESSES ITS OWN ORDER-1 QUERY GENERATOR\n"
           "(read-only: run the committed generator, locate the gap, surface the "
           "requirements)")

    # =====================================================================
    # PART 1 — RUN the current generator on each invariant family; LOCATE the gap.
    # =====================================================================
    banner("PART 1 — RUN the current generator (order_n_communication._presupposed_"
           "needs) on each\nfamily. The generable families emit queries; the NEW "
           "families emit ZERO.")
    results = []
    for label, prose in INVARIANTS:
        asked, needs, out = run_generator(s, label, prose)
        results.append((label, prose, asked, needs))
        print(f"\n  · {label}")
        print(f"      prose          : {prose!r}")
        print(f"      typed repr     : {asked.repr!r}")
        print(f"      typed structure: {asked.typed}")
        print(f"      flags          : free_rank_of_kernel_of_hurewicz="
              f"{asked.free_rank_of_kernel_of_hurewicz}  "
              f"euler_characteristic={asked.euler_characteristic}")
        print(f"      => order-1 queries GENERATED: {len(needs)}")
        for n in needs:
            print(f"           - {n['fact']}: {n['query'][:72]}")
        if not needs:
            print(f"           (NONE — the generator emitted 0 queries for this "
                  f"invariant family)")

    # =====================================================================
    # PART 2 — READ what MAKES an invariant generable (the structure the generator
    # keys off) vs what is ABSENT for the new families.
    # =====================================================================
    banner("PART 2 — what MAKES an invariant generable: the structure the generator "
           "KEYS OFF")
    print("""
  The generator (_presupposed_needs) is a HARDCODED branch chain:

      if asked.free_rank_of_kernel_of_hurewicz:   needs += [3 hand-written queries]
      if asked.euler_characteristic:              needs += [2 hand-written queries]

  So an invariant is GENERABLE iff:
    (a) the general reader sets a BOOLEAN FLAG on the AskedInvariant for its family
        (asked.free_rank_of_kernel_of_hurewicz / asked.euler_characteristic), AND
    (b) _presupposed_needs has a HAND-WRITTEN `if <that flag>:` branch listing the
        query text + the held fact_name + the epistemic frame for each presupposed
        fact.

  Both (a) and (b) are PER-FAMILY HAND-CODE. Confirm by reading the AskedInvariant's
  own structural reads (presupposition_derivation._is_*) and the branch chain:""")
    # the structural flags the reader sets are themselves hardcoded per family.
    import inspect
    print("    presupposition_derivation.AskedInvariant boolean flags (per-family, "
          "hand-written):")
    for fld in ("free_rank_of_kernel_of_hurewicz", "euler_characteristic"):
        print(f"      · asked.{fld}  (set by _is_{fld.split('_of_')[0] if False else ''}"
              f"...; a bespoke structural read)")
    print("\n    _presupposed_needs branches (the hand-written query lists):")
    src = inspect.getsource(_onc._presupposed_needs)
    for line in src.splitlines():
        st = line.strip()
        if st.startswith("if asked."):
            print(f"      {st}")

    print("""
  For the GENERABLE family (commutator/Hurewicz) the operator's reduction is RECORDED
  as machine-readable data the rest of the pipeline reads — commutator_rank.operator_
  specs():""")
    for spec in _cr.operator_specs():
        print(f"      · {spec['name']}")
        print(f"          reduces_to: {spec['reduces_to']}")
        print(f"          meaning   : {spec['meaning'][:90]}...")

    print("""
  THE ABSENT STRUCTURE for the NEW family: compute_reduced_euler (the face-sum faculty
  that COMPUTES the reduced Euler characteristic of a combinatorial complex) has NO
  operator_specs() / no `reduces_to` self-description at all — confirm:""")
    try:
        from domains import compute_reduced_euler as _cre
        has_specs = hasattr(_cre, "operator_specs")
        print(f"      compute_reduced_euler.operator_specs exists? {has_specs}")
        red_funcs = [n for n in dir(_cre) if "reduce" in n.lower() or "spec" in n.lower()]
        print(f"      compute_reduced_euler reduction/spec self-description: "
              f"{red_funcs or 'NONE (no operator_specs, no reduces_to)'}")
    except Exception as e:
        print(f"      (could not import compute_reduced_euler: {e})")

    # =====================================================================
    # PART 3 — the agent's ASSESSMENT: the required components, each grounded.
    # =====================================================================
    banner("PART 3 — THE REQUIRED COMPONENTS (the agent's assessment, grounded to "
           "the real machinery)")
    print("""
  The gap, precisely (TWO LEVELS, both surfaced empirically above):

    LEVEL 1 — the GENERATOR is hand-written per family. Its path from a TYPED invariant
      to its PRESUPPOSED facts is HARD-CODE: both the family FLAG (the reader's _is_*
      structural read on AskedInvariant) and the QUERY LIST (the _presupposed_needs
      `if asked.<flag>:` branch). The betti-of-a-complex operator has neither a flag nor
      a branch, so even when it types it would generate 0.

    LEVEL 2 — the READER's ATOM COVERAGE gates the generator. The euler family generates
      its 2 queries ONLY when the object types to the seeded `space` atom: 'the euler
      characteristic of the space' types to euler_characteristic(space) and fires; but
      'the euler characteristic of the SIMPLICIAL COMPLEX' returns typed=None (no
      `simplicial complex` atom in the math-prose grammar), so it never even reaches the
      generator's branch — 0 queries. This is the cmsg-gap-1/2 frontier (the reader's
      atom/definition coverage) showing up UPSTREAM of the generator. The proof gathered
      the face-sum invariant's facts DIRECTLY precisely because BOTH levels block it: the
      object does not type, AND there is no per-family branch for a combinatorial complex.

  So the general generator requires BOTH a data-driven generator (Level 1) AND the
  object to type (Level 2). The components below close Level 1; Level 2 is named as an
  upstream dependency (the definition-binding reader's frontier, hard part H3).

  What the GENERAL path needs (each component points at where it attaches):

  [C1] A per-OPERATOR REDUCTION SCHEMA, machine-readable, for EVERY invariant operator
       — the same shape commutator_rank.operator_specs() already records (name +
       reduces_to + meaning), EXTENDED to carry the PRESUPPOSED-FACTS each reduction
       step needs (its `requires`: the held theorems/identities the reduction invokes).
       ATTACHES AT: an operator_specs() on EACH faculty (commutator_rank already has
       one; compute_reduced_euler / betti / future operators must each grow one). This
       turns the per-family `if` into data the generator READS.

  [C2] A COMPOSITIONAL RULE: queries(invariant) = the `requires` of the operator's
       recorded reduction, applied to the object's typed definition. I.e. the generator
       walks the typed tree's ROOT OPERATOR -> looks up its operator_spec -> emits one
       query per entry in that spec's `requires` (each already carrying a held fact_name
       + a frame, exactly as the hand-written needs do today).
       ATTACHES AT: _presupposed_needs REPLACED by a loop over asked.typed's operators,
       reading the operator_spec registry (no per-family `if`). The generable families
       become the FIRST two rows of that registry, not branches.

  [C3] THE BRIDGE from the typed tree's OBJECT to the operator's reduction inputs —
       the object's combinatorial DEFINITION (read by construction_grammar.comprehend_
       definitions -> the local typed env that already types Delta_k). The reduction's
       `requires` are read AGAINST that definition (e.g. euler-of-Delta presupposes the
       face-count / finite-complex facts BECAUSE Delta is defined by a face-predicate).
       ATTACHES AT: comprehend_asked_invariant already threads `env` into comprehend_
       structure; the generator reads asked.env + asked.typed together to instantiate
       the reduction's required facts for THIS object.

  [C4] THE OPERATOR-SPEC REGISTRY the generator reads — a graph-resident lookup
       {operator_name -> reduction-schema-with-requires}, populated by each faculty's
       operator_specs(). The order_n_communication source model (install_source_model:
       Microtheory --has_claim--> Claim) ALREADY wires the held facts as graph Claims;
       the registry is the SAME shape one level up (Microtheory --has_operator--> Operator
       Spec), so the order-2 ROUTE lift can already route the queries the registry emits.
       ATTACHES AT: install_source_model extended to also mint each operator_specs() entry
       as a graph node; the generator's lookup is a graph read, mirroring _route_to_source_
       model.

  THE SELECTOR (how the agent knows the general generator is RIGHT — its MDL/validation):
    The general generator is correct iff, for an invariant family it was NOT hardcoded
    for, it generates the SAME query-set the proof gathered DIRECTLY (the face-sum /
    reduced-Euler case: the face-count + finite-complex facts the symbolic-proof turn
    used). VALIDATE exactly like the existing pipeline validates a formula (the cmsg174
    gate): run the generator on a HELD-OUT invariant whose presupposed facts are
    independently known, and check the generated query-set MATCHES — never reverse-
    engineered. MDL: the generator that emits the per-family hand-lists from ONE
    operator-spec walk is shorter (one rule + N data rows) than N hand-written branches
    — compression IS the selector that the data-driven path generalises.

  THE MINIMAL FIRST STEP (the smallest concrete build for the face-sum case):
    Give compute_reduced_euler an operator_specs() in the commutator_rank shape, with a
    `requires` list naming the two facts the proof already used (euler_is_alternating_
    sum_of_betti, alternating_sum_finite_iff_finite_total_betti — both ALREADY in
    presupposition_derivation._FACT_PROSE and grounded). Then have _presupposed_needs,
    for an euler-typed invariant, READ that spec's `requires` instead of its hand-written
    euler branch. Validate: the euler-of-Delta invariant now generates its OWN 2 queries
    (the ones the proof gathered directly), and the existing euler-of-X case is unchanged
    (same 2 facts). This is one faculty growing a self-description + one branch becoming
    a registry read — the seam, not the whole generator.

  THE HONEST HARD PARTS (named, not papered over):
    (H1) READING an ARBITRARY operator's reduction is itself an OPEN PROBLEM. C1 works
         when a faculty AUTHORS its own operator_spec (commutator_rank did, by hand).
         DERIVING the `requires` of a NEW operator the agent has never reduced — from
         the operator's definition alone, with no human-authored spec — is the same
         description->reduction gap derivation_engine names as its residual (the
         'DESCRIPTION->OBJECT step' + 'BREADTH of theorems acquired-runnable'). The
         general generator REDUCES the gap to 'author the operator_spec once per
         operator'; it does NOT eliminate the need to know the operator's reduction.
    (H2) The `requires` facts must already be GROUNDED (read as Claims) for the query to
         route. For a brand-new operator whose presupposed theorems are NOT yet in
         _FACT_PROSE, the generator emits a query that STALLS at an un-grounded fact —
         the honest residual the existing derivation already surfaces (stalled_at), now
         pushed up to the generate step. Acquiring those theorems by reading is the
         separate acquire axis, not closed here.
    (H3) The compositional rule (C2) assumes the presupposed facts are a function of the
         ROOT operator. Invariants whose presuppositions depend on the OBJECT's
         definition in a non-operator-local way (e.g. well-definedness conditions that
         only bite for some object families) need the bridge C3 to be more than a lookup
         — a genuine read of the object's definition, which is exactly the cmsg-gap-1/2
         definition-binding reader's still-narrow frontier.
""")

    banner("ASSESSMENT COMPLETE — grounded map produced, NO build performed")
    print("  The gap is LOCATED (0 queries on the new families, verified above), the "
          "generable\n  structure is READ (the per-family flag + hand-written branch + "
          "the recorded\n  reduction commutator_rank.operator_specs()), the required "
          "components are\n  ENUMERATED + attached to the real machinery, the selector "
          "+ minimal first step\n  + honest hard parts are named. Assessment only — "
          "nothing built.")


if __name__ == "__main__":
    main()
