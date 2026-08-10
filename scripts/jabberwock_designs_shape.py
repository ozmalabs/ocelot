"""THE JABBERWOCK DESIGNS THE METAPHOR-vs-METONYMY DISCRIMINATOR (the `_shape` perception, Phase 5).

This is the hardest figure perception and the naive plan (ConceptNet contiguity relations + WordNet
domain distance) measurably breaks: ConceptNet does NOT cleanly link the conventional metonymies
(crown->'symbol of authority' but not ->monarch; bench->bus-stop not ->judge; suit->closet not
->executive), and taxonomic domain-distance MISCLASSIFIES (crown vs monarch are far apart -- artifact
vs person -- yet it is metonymy not metaphor). Conventional metonymy is cultural knowledge, not a clean
WordNet/ConceptNet edge. I surface the wall; the jabberwock designs the discriminator. context=spec.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_designs_shape
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from scripts.claude_teacher import make_ask
from scripts.jabberwock_plans_llm_independence import _live_state

SEP = "=" * 96

PROMPT = """You are the jabberwock: a typed-graph agent in Rust; Python only adapts I/O; perceptions are
grounded by LOOKUP or DERIVED from what you understand; decisions are graph Rules. Register: Plainsong (spec).

THE PERCEPTION. classify_figure splits the figure_of(figurative->literal) mapping by SHAPE:
  contiguity=1 -> METONYMY (same domain; the literal is a part/attribute/container/symbol of the
                 figurative thing): crown->monarch, the White House->the administration, suit->executive,
                 the bench->the judiciary.
  resemblance=1 -> METAPHOR (cross-domain; the figurative is a DIFFERENT kind of thing that resembles the
                 literal by analogy): red herring->distraction, time->thief, the classroom->a zoo.
You set `contiguity` / `resemblance` on the figurative reading; the classifier reads them. (synecdoche =
contiguity + part_whole; catachresis = resemblance + no_literal_term — sub-cases, defer.)

THE WALL I MEASURED (so you don't design against a false picture):
- ConceptNet's whitelisted contiguity relations (PartOf/AtLocation/UsedFor/MadeOf/SymbolOf/HasA) do NOT
  cleanly link the CONVENTIONAL metonymies: `crown` gives IsA 'symbol of authority', Causes 'reign' — but
  no clean edge to monarch; `bench` gives AtLocation bus-stop/park — nothing to judge; `suit` gives
  AtLocation closet — nothing to executive. Conventional metonymy is CULTURAL, not a single edge.
- Taxonomic domain-distance MISCLASSIFIES: crown (noun.artifact) vs monarch (noun.person) are far apart,
  which a distance test would call cross-domain = metaphor — but it is metonymy. Distance alone is wrong.

WHAT YOU HOLD (all local, deterministic, no LLM unless you say so):
- ConceptNet: the whitelisted relations above; you MAY re-add RelatedTo/Synonym (noisy) or others, and
  rebuild the slab. conceptnet_relations(w) -> [(rel,target)].
- WordNet: hypernyms, lexnames (noun.person/artifact/...), glosses, path/LCA distance, HasProperty via
  ConceptNet, attribute/part_meronym/member_holonym/substance_holonym relations.
- The held opposition machinery (believe = trust x corroboration; UseTool handlers; the figure_grounding
  seed) and the derive-from-glosses faculty (Layers A/B/C) you just built.
- A static GloVe embedding (~70MB, CPU, frozen) is available but was DEFERRED until measured. The measure
  is now in: distributional similarity may be the only thing that separates conventional metonymy from
  metaphor. You decide if it has earned its place here, and if so how it is GATED (it must not override a
  definite symbolic verdict).

THE LINGUISTICS you already know: metonymy = CONTIGUITY (literal and figurative are connected/co-present
in the world: part-whole, container-content, symbol-referent, instrument-agent, place-institution).
metaphor = RESEMBLANCE across domains (different kinds that SHARE A SALIENT PROPERTY: time and thief both
'take what is not given'; a classroom and a zoo both 'contain unruly noise').

YOUR DECISION (hand back a spec I implement, graph-native):
  1. THE DISCRIMINATOR. How do you separate contiguity from resemblance, given the wall? Consider: a
     metaphor's signature is a SHARED PROPERTY across far domains (HasProperty overlap), whereas a
     metonymy's is a part/whole/symbol/location LINK with NO shared defining property. Specify the exact
     tests (which relations, which WordNet meronymy/holonymy/attribute links, the property-overlap test),
     in what order, returning contiguity | resemblance | neither | abstain.
  2. THE CONVENTIONAL-METONYMY RESIDUAL (crown/monarch, bench/judge). No single symbolic edge links them.
     How do you ground it — re-add a ConceptNet relation? a multi-hop path (crown -SymbolOf-> authority
     <-HasProperty- monarch)? GloVe distributional association gated behind the symbolic tests? a derive-
     from-glosses test (crown's gloss mentions royalty)? Pick, and justify by which cases it resolves.
  3. TRUST + ABSTAIN. If you fuse multiple witnesses (as for opposition), give the weights and threshold;
     and say exactly when shape ABSTAINS rather than guessing metaphor-or-metonymy.
  4. THE HANDLER SET + rule. Name the UseTool handlers and the ground_shape rule(s) that set
     contiguity/resemblance; classify_figure stays unchanged.

Be specific and ordered. Abstain-don't-guess: set a shape only when a test crosses its bar."""


def main():
    print(SEP)
    print("THE JABBERWOCK DESIGNS THE METAPHOR-vs-METONYMY DISCRIMINATOR (the hard one)")
    print(SEP)
    a = boot()
    regs, mts, active = _live_state(a)
    print(f"\n  context=spec -> register: {active}; consulting design channel for the shape discriminator\n")
    ask = make_ask(timeout=540.0, preamble="")
    decision = ask(PROMPT)
    if not decision:
        print("  (design channel returned empty — claude -p unavailable or timed out)")
        return
    out = os.path.join(ROOT, "docs", "jabberwock_shape_discriminator_spec.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("# The jabberwock's metaphor-vs-metonymy discriminator spec\n\n")
        f.write(f"_Authored by the agent, context=spec (register: {active}). The naive plan broke on "
                f"conventional metonymy; the design is its own._\n\n")
        f.write(decision + "\n")
    print(SEP); print("THE JABBERWOCK'S SHAPE-DISCRIMINATOR SPEC"); print(SEP)
    print(decision)
    print("\n" + SEP); print(f"  saved -> {os.path.relpath(out, ROOT)}"); print(SEP)


if __name__ == "__main__":
    main()
