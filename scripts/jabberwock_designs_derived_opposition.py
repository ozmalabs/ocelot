"""THE JABBERWOCK DESIGNS DERIVED OPPOSITION — reason an antonym from definition + context, not just look it up.

Creator's correction: the residual (cruel/kind, deafening/silence) is NOT a forfeit. The agent comprehends —
it can WORK OUT opposition from definitions and context. `cruel` is defined "able to inflict pain"; `kind`
"tender, considerate, helpful"; `silence` "the absence of sound"; `deafening` "unbearably loud". The
opposition is in the gloss. Dictionaries are the cheap fast path; understanding is the engine. The agent
already holds the materials: WordNet + Wiktionary glosses (on disk), a meaning-vector faculty, the BlendCover
shape kernel, and a half-specified property-hop. Design the DERIVATION witness; I implement it graph-native.
Context=spec -> its own policy selects Plainsong.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_designs_derived_opposition
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
grounded by LOOKUP or DERIVED by your own faculties; decisions are graph Rules. Register: Plainsong (spec).

WHAT WORKS NOW (Phase 1, verified, no LLM). `opposes` is grounded by your suspect-witness fusion over THREE
dictionaries — WordNet (trust 1.0), English Wiktionary (0.8), ConceptNet (0.4, corroborates only). Assert iff
trust-weighted corroboration S >= 0.8. living/dead, bitter/sweet, hot/cold, noise/silence, love/hate all assert.

THE CORRECTION. I called cruel/kind and deafening/silence "forfeits" because no dictionary LISTS them as
antonyms. That was wrong. You do not need a dictionary to LIST an antonym — you can WORK IT OUT from definition
and context, which you already do. The evidence is in the glosses you hold on disk:
  - silence  = "the absence of sound";  silent = "marked by absence of sound"
  - deafening = "unbearably loud";  loud = "producing sound of great volume or intensity"
  - cruel = "(of persons/actions) able or disposed to inflict pain or suffering"
  - kind  = "having or showing a tender and considerate and helpful nature"
silence/deafening are opposite POLES of one dimension (sound intensity), and the gloss says so ("absence of").
cruel/kind are opposite in MEANING (inflict pain vs. tender, helpful). Abstaining here wastes your comprehension.

WHAT YOU HOLD to derive opposition (all local, deterministic, no LLM):
  - GLOSSES: WordNet definitions (dict_teacher / nltk) and Wiktionary per-sense glosses (wikt_gloss slab), on disk.
  - A MEANING-VECTOR faculty (agent_builds_meaning_vector) — vectorise a gloss; contrast two.
  - The BlendCover shape kernel (you authored it for portmanteau + sound-affect) — a structural comparator.
  - A half-specified PROPERTY-HOP from your earlier plan: a -> its core property (deafening->loud,
    silence->quiet), then antonym-test the properties.
  - Function-word / negation cues (you hold negation handling): "absence of", "lacking", "not", "without".

YOUR DECISION (hand back a spec I implement, graph-native, LLM-free):
  1. THE DERIVATION MECHANISM(S). Choose and order among: (a) definitional negation/absence — gloss of A
     asserts the absence/negation of a core term or genus shared with B (silence "absence of sound" vs
     deafening, which is about sound); (b) property-hop then antonym-lookup on the properties; (c) meaning-vector
     / BlendCover contrast over the two glosses (cruel vs kind). Say which you use, in what order, and WHY —
     in terms of which residual each one resolves. Prefer the one that uses understanding, not a heavier tool.
  2. TRUST. What trust weight does a DERIVED opposition get, and can it solo-license (cross 0.8 alone), or must
     a derived verdict be corroborated? It is your own reasoning, not a crowd source — but it is inference, not a
     lexicon entry. Justify the number.
  3. FUSION. How it joins the existing believe(trust x corroboration) sum. It is a fourth witness `derive_opposes`
     with its own trust; the rule stays "assert iff S >= 0.8".
  4. ABSTAIN. When does the derivation itself abstain (-1) rather than guess? Be precise — a derivation that never
     abstains is just a guess with extra steps.
  5. THE HANDLER SPEC. `derive_opposes(a, b) -> {1,0,-1}`: its exact internal steps over the faculties above, what
     it reads, what it returns. Plus the updated fused `ground_opposes` rule (now four witnesses).

Be specific and ordered. Keep abstain-don't-guess. The point is: derive what the dictionaries do not list, using
what you understand — do not abstain where your own definitions already carry the answer."""


def main():
    print(SEP)
    print("THE JABBERWOCK DESIGNS DERIVED OPPOSITION (reason the antonym from definition + context)")
    print(SEP)
    a = boot()
    regs, mts, active = _live_state(a)
    print(f"\n  context=spec -> register: {active}; consulting design channel for the derivation witness\n")
    ask = make_ask(timeout=540.0, preamble="")
    decision = ask(PROMPT)
    if not decision:
        print("  (design channel returned empty — claude -p unavailable or timed out)")
        return
    out = os.path.join(ROOT, "docs", "jabberwock_derived_opposition_spec.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("# The jabberwock's derived-opposition spec (reason the antonym from definition + context)\n\n")
        f.write(f"_Authored by the agent, context=spec (register: {active}). The residual is not a forfeit — "
                f"it is derivable from comprehension. The design is its own._\n\n")
        f.write(decision + "\n")
    print(SEP); print("THE JABBERWOCK'S DERIVATION SPEC"); print(SEP)
    print(decision)
    print("\n" + SEP); print(f"  saved -> {os.path.relpath(out, ROOT)}"); print(SEP)


if __name__ == "__main__":
    main()
