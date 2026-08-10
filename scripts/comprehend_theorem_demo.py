"""comprehend_theorem_demo (cmsg129) — DEMONSTRATE the THEOREM-COMPREHENSION
faculty crossing the read-statement -> runnable-structure wall.

The wall (cmsg113/122/128): the agent READ each theorem but the COMPREHENSION —
turning the theorem PROSE into the (antecedent => consequent) ImplicationClause —
was HAND-WIRED in the builder functions (a human wrote the clauses). Here the
ImplicationClause is PRODUCED BY PARSING the read prose, by GRAMMAR (seed data),
and the SAME grammar parses a PARAPHRASE + a HELD-OUT theorem (the proof it is not
hand-wired). The cd/ends builders now CALL comprehend_theorem on the read
statement; the reductions still VERIFY vs KNOWN (8 groups) and the cd/ends question
is still 6/9.

NO LLM, NO Rust, NO per-theorem clause-list — a world-adapter shell over the held
machinery (the construction-grammar matcher over seed DATA; the cmsg128 held
predicates; the general reader's invariant typing).
"""
from __future__ import annotations

import os
import sys

ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_theorem as ct
from domains import ground_reductions as gr


def banner(s: str) -> None:
    print("\n" + "=" * 78 + "\n  " + s + "\n" + "=" * 78)


def show(statement: str, tag: str = "") -> None:
    c = ct.comprehend_theorem(statement)
    print(f"\n  [{tag}] PROSE: {statement!r}")
    if not c.comprehended:
        print(f"     -> NAMED RESIDUAL: {c.residual}")
        return
    p = c.provenance["parsed"]
    g = c.provenance["grounded"]
    print(f"     PARSED   : form={p['form']}  copula={p['copula']}  "
          f"subject={p['subject']!r}")
    print(f"                modifier={p['modifier']!r}  "
          f"subjphrase={p['subjphrase']!r}  predicate={p['predicate']!r}"
          + (f"  condition={p['condition']!r}" if p['condition'] else ""))
    print(f"     GROUNDED : antecedent -> {g['antecedent']}")
    print(f"                invariant  -> {g['invariant']}")
    print(f"                value      -> {g['value']}")
    print(f"     CLAUSE   : {c.clause.antecedent_name}  =>  value={c.clause.value!r}"
          f"   (invariant={c.invariant})")


def main() -> None:
    banner("THE FACULTY — prose -> parsed -> grounded ImplicationClause "
           "(the grammar = seed data: seeds/theorem_constructions.json)")
    print("  A theorem statement: [quantifier] [SUBJECT class] [MODIFIER property] "
          "[COPULA has/is/iff] [PREDICATE invariant + value].")
    print("  PARSE (seeded statement constructions) -> GROUND (property -> held "
          "predicate; invariant -> typed; value -> consequent) -> EMIT the clause.")

    banner("(1) THE READ cd/ends THEOREMS — PARSED (un-gifting cmsg128's hand-wire)")
    show("a group with torsion has cohomological dimension infinite", "cd / Brown")
    show("a free group has cohomological dimension 1", "cd / Stallings-Swan")
    show("a finite group has 0 ends", "ends / Stallings")
    show("a virtually Z group has two ends", "ends / D_inf")
    show("a nontrivial free product has infinitely many ends", "ends / Stallings")

    banner("(2) GENERALITY — the SAME grammar parses a PARAPHRASE + a HELD-OUT "
           "theorem (different invariant/form) it was NOT tuned for")
    print("  PARAPHRASE of the cd theorem (different surface, SAME implication):")
    show("a group that contains an element of finite order has infinite "
         "cohomological dimension", "PARAPHRASE-cd")
    print("\n  HELD-OUT theorems (a DIFFERENT form / a SYMBOLIC value / a "
          "biconditional) — NEVER tuned for, parsed via the SAME grammar:")
    show("a free abelian group of rank n has cohomological dimension n",
         "HELD-OUT rank-n (symbolic value)")
    show("a finitely generated group has more than one end if and only if it "
         "splits over a finite subgroup", "HELD-OUT iff (biconditional)")
    # the symbolic value computes the rank (cd of Z^n = n) — a runnable structure.
    held = ct.comprehend_theorem(
        "a free abelian group of rank n has cohomological dimension n")
    vc = getattr(held.clause, "value_compute", None)
    if callable(vc):
        vals = {f"rank {r}": vc({"rank": r}) for r in (1, 2, 3)}
        print(f"     RUNNABLE (symbolic n -> the object's rank): {vals}")

    banner("(3) UN-GIFTED cd/ends — the builders now CALL comprehend_theorem; "
           "VERIFY vs KNOWN (8 groups)")
    gr._GROUNDED = None
    all_ok = True
    for inv in ("cohomological_dimension", "virtual_cohomological_dimension",
                "ends"):
        v = gr.verify_grounded(inv)
        all_ok = all_ok and v["ok"]
        print(f"\n  {inv}: verify vs KNOWN = {'OK' if v['ok'] else 'FAIL'}")
        print(f"     got     : {v['got']}")
        red = gr.grounded_reductions()[inv]
        for ch in red.grounding_chains():
            if ch.startswith("PARSE"):
                print(f"     PROVENANCE (parsed, not hand-wired): {ch[:160]}")
    print(f"\n  ALL reductions verify vs KNOWN (8 groups): {all_ok}")

    banner("(3b) FULL-MODIFIER ACCOUNTING (cmsg131) — a known property atom grounds "
           "the antecedent ONLY IF the WHOLE phrase is accounted; ANY unaccounted "
           "contentful word (a known atom buried in a LARGER unknown qualifier) -> "
           "MISS, NOT a partial substring match. ALL below MUST MISS (no false ground)")
    # the SUB-TOKEN / SUB-PHRASE traps (a known atom — 'finite' / 'torsion-free' —
    # buried inside an UNKNOWN qualifier) + UNKNOWN BARE CLASSES. Every one MUST MISS:
    # a false grounding here is the failure; a MISS is CORRECT.
    adversarial = [
        ("residually finite", "a residually finite group has cohomological "
                              "dimension 1"),
        ("locally finite", "a locally finite group has cohomological dimension 1"),
        ("virtually torsion-free", "a virtually torsion-free group has "
                                   "cohomological dimension 1"),
        ("finitely generated and solvable", "a finitely generated and solvable "
                                            "group has cohomological dimension 1"),
        ("profinite", "a profinite group has cohomological dimension 1"),
        ("almost free", "an almost free group has cohomological dimension 1"),
        ("solvable (bare)", "a solvable group has cohomological dimension 1"),
        ("nilpotent (bare)", "a nilpotent group has cohomological dimension 1"),
        ("amenable (bare)", "an amenable group has cohomological dimension 1"),
        ("with-modifier unknown", "a group with a normal subgroup has "
                                  "cohomological dimension 1"),
        ("that-is unknown", "a group that is solvable has cohomological dimension 1"),
        ("iff-condition unknown", "a hyperbolic group has more than one end if and "
                                  "only if it is solvable"),
    ]
    all_miss = True
    for tag, stmt in adversarial:
        c = ct.comprehend_theorem(stmt)
        verdict = "FALSE-GROUND!!" if c.comprehended else "MISS (correct)"
        if c.comprehended:
            all_miss = False
            verdict += f"  -> {c.clause.antecedent_name}"
        print(f"\n  [{tag}] {stmt!r}\n     -> {verdict}")
    print(f"\n  ALL adversarial probes MISS (no false grounding): {all_miss}")

    banner("(3c) THE CANONICAL THEOREMS STILL GROUND (the principle did NOT break "
           "the real theorems — full-accounting MISSes ONLY the unaccounted phrase)")
    canonical = [
        ("torsion=>cd inf", "a group with torsion has cohomological dimension "
                            "infinite", "some_factor_finite_cyclic", "inf"),
        ("free=>cd 1", "a free group has cohomological dimension 1",
         "all_factors_infinite_cyclic_nonempty", 1),
        ("torsion-free=>cd 1", "a torsion-free group has cohomological dimension 1",
         "all_factors_infinite_cyclic_nonempty", 1),
        ("finite=>0 ends", "a finite group has 0 ends", "is_finite_group", 0),
        ("free-product=>inf ends", "a nontrivial free product has infinitely many "
                                   "ends", "splits_over_finite_nontrivially", "inf"),
        ("ends iff (antecedent=iff-condition, not ambient 'finitely generated')",
         "a finitely generated group has more than one end if and only if it splits "
         "over a finite subgroup", "splits_over_finite_nontrivially", ">1"),
    ]
    all_ground = True
    for tag, stmt, want_pred, want_val in canonical:
        c = ct.comprehend_theorem(stmt)
        if not c.comprehended:
            all_ground = False
            print(f"\n  [{tag}] {stmt!r}\n     -> MISS!! (should GROUND): "
                  f"{c.residual[:90]}")
            continue
        ok = want_pred in c.clause.antecedent_name and c.clause.value == want_val
        all_ground = all_ground and ok
        print(f"\n  [{tag}] {stmt!r}\n     -> GROUND{'[OK]' if ok else '[WRONG]'}: "
              f"{c.clause.antecedent_name.split()[0]} => {c.clause.value!r} "
              f"(inv={c.invariant})")
    print(f"\n  ALL canonical theorems still GROUND correctly: {all_ground}")

    banner("(3d) SELF-VERIFY WIRED INTO THE FACULTY (cmsg133) — every grounded "
           "clause is a CHECKABLE CLAIM, run against the SAME verify-vs-known the "
           "reduction store holds (ground_reductions.KNOWN_OBJECTS / KNOWN_VALUES). "
           "The check that did NOT fire on the cmsg130/131 false groundings (the "
           "faculty's output bypassed verify-vs-known) now fires from INSIDE.")
    print("  WHY the agent's checks were silent: verify_grounded ran only DOWNSTREAM "
          "on the\n  ASSEMBLED reduction's canonical clauses; the admissibility gate "
          "is on the\n  CONSTRUCTOR's object path. comprehend_theorem emitted its "
          "clause + set\n  comprehended=True with NO reference to KNOWN — so every "
          "per-grounding output\n  bypassed verify-vs-known. NOW it is wired into the "
          "faculty's output path.")

    print("\n  (i) THE cmsg130/131 FALSE GROUNDINGS — re-injected as the equivalent "
          "bad clauses;\n      the faculty's OWN self-verify REJECTS them vs known "
          "(no external probe):")
    bad_clauses = [
        ("cmsg130: always-true => cd=inf",
         (lambda o: True), "cohomological_dimension", "inf"),
        ("cmsg131: is_finite_group => cd=1 (from 'residually finite')",
         gr.is_finite_group, "cohomological_dimension", 1),
    ]
    all_reject = True
    for tag, ante, inv, val in bad_clauses:
        verdict, note = ct.self_verify_clause(ante, inv, val)
        rejected = verdict == "rejected"
        all_reject = all_reject and rejected
        print(f"\n  [{tag}]\n     -> {'SELF-REJECTED (correct)' if rejected else 'PASSED!!'}"
              f": {note[:150]}")
    print(f"\n  Both cmsg130/131 false groundings self-REJECT from inside the "
          f"faculty: {all_reject}")

    print("\n  (ii) DEFENSE IN DEPTH — a clause the MATCHER (cmsg132 full-modifier "
          "accounting)\n       LETS THROUGH (a real held predicate, fully accounted) "
          "but whose asserted\n       VALUE is WRONG. The matcher cannot catch this "
          "(the antecedent is sound);\n       the SELF-VERIFY does (the systemic "
          "check is the real guard, not the patch):")
    matcher_passes_wrong = [
        ("free => cd INFINITE (free groups have cd 1)",
         "a free group has cohomological dimension infinite"),
        ("finite => 1 end (finite groups have 0 ends)",
         "a finite group has 1 ends"),
        ("virtually Z => 0 ends (virtually-Z has 2 ends)",
         "a virtually Z group has 0 ends"),
    ]
    all_caught = True
    for tag, stmt in matcher_passes_wrong:
        c = ct.comprehend_theorem(stmt)
        caught = not c.comprehended
        all_caught = all_caught and caught
        print(f"\n  [{tag}] {stmt!r}")
        if caught:
            print(f"     -> SELF-REJECTED by the wired self-verify: "
                  f"{c.residual.split('failed self-verification vs known: ')[-1][:130]}")
        else:
            print(f"     -> PASSED!! (matcher let it through AND self-verify missed it)")
    print(f"\n  All matcher-passing-but-wrong clauses caught by the wired self-verify: "
          f"{all_caught}")

    print("\n  (iii) The CANONICAL groundings face a known and REPRODUCE it -> "
          "verified=True\n        (the check does NOT break the real theorems):")
    canon_verified = True
    for stmt in ("a group with torsion has cohomological dimension infinite",
                 "a free group has cohomological dimension 1",
                 "a finite group has 0 ends",
                 "a virtually Z group has two ends",
                 "a nontrivial free product has infinitely many ends"):
        c = ct.comprehend_theorem(stmt)
        ok = c.comprehended and c.verified
        canon_verified = canon_verified and ok
        print(f"     [{'VERIFIED' if ok else 'NOT-VERIFIED!!'}] {stmt!r}")
    print(f"\n  All canonical groundings self-verify vs known (verified=True): "
          f"{canon_verified}")

    banner("(4) THE NAMED RESIDUAL — theorem-forms NO construction parses (honest, "
           "each an addable construction; NOT hand-wired to fake coverage)")
    show("whenever a group acts properly on a tree its cohomological dimension "
         "is at most one", "RESIDUAL: unseeded form ('at most one' / 'whenever')")
    show("a group with property T has finite abelianization",
         "RESIDUAL: unseeded property + invariant")

    banner("(5) GREW BY READING (cmsg133 residual closed) — NEW vocabulary FETCHED "
           "from the corpus, COMPREHENDED, GROUNDED to held predicates/computes, and "
           "SELF-VERIFIED (the cmsg133 guard makes growing-by-reading SAFE: a WRONG "
           "read-grounding self-REJECTS instead of polluting the faculty). NOT "
           "hand-authored — each atom carries its read-cite + held-compute + a PASSED "
           "self-verify (in seeds/theorem_constructions.json).")
    grew = [
        ("virtually cyclic", "a virtually cyclic group has two ends",
         "Virtually (Wikipedia): virtually-P = P holds for a finite-index subgroup; "
         "the infinite virtually-cyclic group is virtually Z",
         "is_virtually_Z (held: the infinite cyclic Z, or D_inf = C_2*C_2)"),
        ("first betti number", "a free group of rank n has first betti number n",
         "Betti number (Wikipedia): b_n = rank of H_n, torsion excluded -> b_1 = "
         "rank of the abelianization",
         "first_betti_number = count of infinite-cyclic free factors (held abelianization)"),
        ("rank of the abelianization", "a free group of rank n has rank of the "
         "abelianization n",
         "Betti number (Wikipedia): b_1 = rank of H_1 = rank of the abelianization",
         "first_betti_number (the SAME held compute; a synonym surface for b_1)"),
    ]
    print("\n  BEFORE: each previously MISSED (the faculty grounded only the seeded "
          "atoms). AFTER: GROUND + self-VERIFY (each from READING, not hand-wired):")
    all_grew = True
    for tag, stmt, cite, ground in grew:
        c = ct.comprehend_theorem(stmt)
        ok = c.comprehended and c.verified
        all_grew = all_grew and ok
        print(f"\n  [{tag}] {stmt!r}")
        print(f"     READ-CITE : {cite}")
        print(f"     GROUNDING : {ground}")
        if ok:
            print(f"     AFTER     : GROUND+VERIFIED -> "
                  f"{c.clause.antecedent_name.split()[0]} => value={c.clause.value!r} "
                  f"(inv={c.invariant})  [self-verify PASSED]")
        else:
            print(f"     AFTER     : {'GROUND but UNVERIFIED' if c.comprehended else 'MISS'}!!")
    print(f"\n  ALL grew-by-reading vocab GROUND + self-VERIFY: {all_grew}")

    print("\n  ADVERSARIAL SELF-TEST (my own traps) — the new vocab in FALSE "
          "statements MUST self-REJECT (the cmsg133 guard holds for the new vocab):")
    false_new = [
        ("virtually cyclic => 0 ends (WRONG: 2)",
         "a virtually cyclic group has 0 ends"),
        ("virtually cyclic => infinitely many ends (WRONG: 2)",
         "a virtually cyclic group has infinitely many ends"),
        ("free rank n => first betti 1 (WRONG: n)",
         "a free group of rank n has first betti number 1"),
        ("free rank n => first betti 0 (WRONG: n)",
         "a free group of rank n has first betti number 0"),
    ]
    all_rej = True
    for tag, stmt in false_new:
        c = ct.comprehend_theorem(stmt)
        rej = not c.comprehended
        all_rej = all_rej and rej
        print(f"\n  [{tag}] {stmt!r}\n     -> "
              f"{'SELF-REJECTED (correct)' if rej else 'FALSE-GROUND!!'}")
    print(f"\n  ALL false new-vocab statements self-REJECT (zero false groundings): "
          f"{all_rej}")

    banner("(5b) THE HONEST RESIDUAL — read-but-does-NOT-reduce (the held-structure-"
           "reach limit). These READ fine, but the held free-product representation "
           "CANNOT express them: either no held predicate composes, OR a faithful "
           "grounding FAILS self-verify (cmsg133). Correctly NOT added.")
    residual = [
        ("solvable", "a solvable group has cohomological dimension 1"),
        ("nilpotent", "a nilpotent group has cohomological dimension 1"),
        ("amenable", "an amenable group has cohomological dimension 1"),
        ("residually finite", "a residually finite group has cohomological "
                              "dimension 1"),
        ("hyperbolic", "a hyperbolic group has more than one end"),
        ("virtually free", "a virtually free group has virtual cohomological "
                           "dimension 1"),
    ]
    all_miss = True
    for tag, stmt in residual:
        c = ct.comprehend_theorem(stmt)
        miss = not c.comprehended
        all_miss = all_miss and miss
        print(f"  [{tag:18s}] MISS (correct — no held predicate composes / out of "
              f"the held structure's reach)" if miss
              else f"  [{tag}] GROUND!! (should be residual)")
    print(f"\n  ALL residual candidates MISS (read-but-don't-reduce): {all_miss}")
    print("  NOTE: 'virtually free' is the sharpest case — a FAITHFUL is_virtually_"
          "free predicate is TRUE on ALL held objects incl the trivial group (vcd=0), "
          "so the clause 'virtually free => vcd 1' FAILS self-verify (fires on trivial "
          "where vcd=0 != 1) -> cmsg133 REJECTS it. The bare theorem lacks the "
          "'infinite' qualifier the held structure needs. read != reduce.")

    banner("RESULT")
    print("  The faculty PARSES the read theorem PROSE into a grounded "
          "ImplicationClause BY GRAMMAR (seed data), GENERALLY (the SAME parser on "
          "the cd theorem AND a paraphrase AND a held-out theorem). The cd/ends "
          "builders now CALL comprehend_theorem on the read statement (the "
          "hand-wired clause-lists REPLACED by the parse); the reductions VERIFY vs "
          "KNOWN. The long tail of unparsed theorem-forms is the NAMED residual.")
    print("\n[MARKER] COMPREHEND_THEOREM_FACULTY_DEMONSTRATED")


if __name__ == "__main__":
    main()
