"""DISCOURSE COHERENCE (RST) + ARGUMENT — jabberwock-designed (composed from machinery already held).

RST = the DIALOGUE relation with the speaker held constant: type clause->clause edges as cause/contrast/
concession/elaboration/sequence from the connective (+ referent-overlap fallback). ARGUMENT = a Toulmin
frame (claim/evidence/warrant) judged by the inference engine: SOUND iff the warrant licenses a firing
implication; named FALLACY (circular / ad hominem / affirming-the-consequent) otherwise. Both are graph
rules over existing primitives.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_discourse_argument
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
    print("DISCOURSE COHERENCE (RST) + ARGUMENT — relations between clauses, and valid vs fallacious")
    print(SEP)
    a = boot()
    for s in ("dialogue_intertext", "event_reasoning", "discourse_argument"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # 1. RST — type the relation between adjacent clauses from the connective.
    print("\n  1) DISCOURSE COHERENCE — clause->clause relation from the connective:")
    pairs = [("the bridge collapsed", "the bolts had rusted", "because", 0),
             ("she trained for months", "she lost the race", "but", 0),
             ("he failed the exam", "he had not studied", "although", 0),
             ("birds migrate far", "the arctic tern flies pole to pole", "for_example", 1),
             ("he woke at dawn", "he set out", "then", 0)]
    for c1, c2, conn, overlap in pairs:
        n1 = a.s.add_node("Clause", {"text": c1}); n2 = a.s.add_node("Clause", {"text": c2})
        r = a.s.add_node("Relation", {"conn": conn, "overlap": overlap})
        a.inner.add_edge_unchecked(r, "relates", n2); a.inner.add_edge_unchecked(r, "from_clause", n1)
        a.inner.run_rules(10000)
        print(f"    {c1!r} --[{conn}]--> {c2!r}   relation = {a.s.node(r)['attrs']['relation'].upper()}")

    # 2. ARGUMENT — Toulmin frame judged by the inference engine + belief scoring.
    print("\n  2) ARGUMENT — sound vs fallacious (Toulmin frame + entailment + belief):")
    args = [
        ("All metals conduct; copper is a metal; so copper conducts",
         dict(warrant_licenses=1)),
        ("The ground is wet, so it rained (but sprinklers also wet the ground)",
         dict(affirms_consequent=1)),
        ("The bible is true because it is the word of God, which we know from the bible",
         dict(warrant_circular=1)),
        ("His argument is wrong because he is a fool",
         dict(evidence_ad_hominem=1)),
    ]
    for text, sig in args:
        g = a.s.add_node("Argument", dict(sig))
        a.inner.add_edge_unchecked(g, "has_claim", a.s.add_node("Claim", {}))
        a.inner.run_rules(10000)
        print(f"    {text!r}")
        print(f"        -> {a.s.node(g)['attrs']['verdict']}")

    print("\n" + SEP)
    print("  Discourse coherence is the dialogue relation with one speaker (clause->clause, connective-")
    print("  typed); argument is that relation plus a truth obligation — a Toulmin frame whose warrant must")
    print("  license a FIRING implication to be sound, with circular / ad hominem / affirming-the-consequent")
    print("  falling out of the same inference + suspect-witness machinery. No new primitives, just composed.")
    print(SEP)


if __name__ == "__main__":
    main()
