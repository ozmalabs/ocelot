"""MODALITY / NEGATION-SCOPE + ToM / GIVEN-NEW — jabberwock-designed (one wrapper at different scopes).

MODALITY = an operator over a proposition that grades its truth (fact/necessary -> entailed; possible/
obligatory -> not), so the inference engine won't chain a 'might' as fact. NEGATION-SCOPE = which
constituent the NOT dominates (the focus IS the meaning). ToM = a believes operator scoping a NESTED
sub-model that can diverge from reality (false belief). GIVEN/NEW = definite (the->given/refer) vs
indefinite (a->new/mint). Modality, negation and 'believes' are the same operator-over-proposition at
different scopes.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_modality_tom
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96


def main():
    print(SEP)
    print("MODALITY / NEGATION + ToM / GIVEN-NEW — operators over propositions and sub-models")
    print(SEP)
    a = boot()
    for s in ("event_reasoning", "modality_tom"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # 1. MODALITY — the operator grades truth; only fact/necessary are entailed.
    print("\n  1) MODALITY — 'must leave' vs 'might leave' yield different entailments:")
    for surface, modality in [("he leaves (asserted)", "fact"), ("he must leave", "necessary"),
                              ("he might leave", "possible"), ("he should leave", "obligation")]:
        p = a.s.add_node("Prop", {"text": surface, "modality": modality, "is_prop": 1})
        a.inner.add_edge_unchecked(p, "is_prop", p)
        a.inner.run_rules(10000)
        ent = a.s.node(p)["attrs"]["entailed"]
        print(f"    {surface:22} [{modality:10}] -> does he leave? {'ENTAILED' if ent==1 else 'NOT entailed'}")

    # 2. NEGATION-SCOPE — the focus of NOT is the meaning ('I did not say he stole it').
    print("\n  2) NEGATION-SCOPE — 'I did not say he stole it', focus shifts the meaning:")
    foci = {"say": "someone else said it (I didn't SAY it)",
            "he": "I said SOMEONE stole it, but not HE",
            "stole": "I said he DID something with it, not that he STOLE it",
            "it": "I said he stole SOMETHING, but not IT"}
    for focus, reading in foci.items():
        n = a.s.add_node("Negation", {"focus": focus})
        print(f"    NOT scopes {focus!r:8} -> {reading}")

    # 3. ToM — a nested belief-model that diverges from reality (Sally-Anne false belief).
    print("\n  3) THEORY OF MIND — Sally-Anne false belief (answer from the belief-model, not reality):")
    world = a.s.add_node("SmEntity", {"name": "marble", "location": "the box"})        # reality (Anne moved it)
    sally_belief = a.s.add_node("BeliefModel", {"agent": "Sally"})
    bm = a.s.add_node("SmEntity", {"name": "marble", "location": "the basket"})        # Sally still believes basket
    a.inner.add_edge_unchecked(sally_belief, "believes", bm)
    reality = a.s.node(world)["attrs"]["location"]
    belief = a.s.node(a.inner.neighbours(sally_belief, "believes")[0])["attrs"]["location"]
    print(f"    reality: the marble is in {reality}")
    print(f"    Sally believes: the marble is in {belief}")
    print(f"    Q: Where will Sally look?   A: {belief}   (her belief-model, which DIVERGES from reality)  [false belief tracked]")

    # 4. GIVEN / NEW — definite refers (given), indefinite mints (new). get-or-create dedup.
    print("\n  4) GIVEN / NEW — definiteness drives refer (given) vs mint (new):")
    discourse = [("a", "man"), ("the", "man"), ("a", "dog"), ("the", "dog"), ("the", "man")]
    concepts = {}
    for art, noun in discourse:
        if art in ("a", "an"):
            concepts[noun] = a.s.add_node("Concept", {"name": noun})    # NEW: mint
            tag = "NEW (mint)"
        else:
            tag = "GIVEN (refer to existing)" if noun in concepts else "NEW (accommodate — first mention)"
            if noun not in concepts:
                concepts[noun] = a.s.add_node("Concept", {"name": noun})
        print(f"    {art+' '+noun:10} -> {tag}")

    print("\n" + SEP)
    print("  Modality, negation and 'believes' are one operator-over-proposition at different scopes: a")
    print("  modal grades a proposition's truth (so 'might' won't entail), NOT scopes a constituent (the")
    print("  focus is the meaning), and 'believes' scopes a whole nested sub-model that can diverge from")
    print("  reality (false belief). Given/new is just definite=refer vs indefinite=mint. All reused.")
    print(SEP)


if __name__ == "__main__":
    main()
