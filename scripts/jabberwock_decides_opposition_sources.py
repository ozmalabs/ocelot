"""THE JABBERWOCK RATIFIES THE OPPOSITION-SOURCE POLICY — multiple trust-differentiated dictionaries.

The creator's correction: on-disk is NOT the boundary. A one-time download that lands as a static
local file is still LLM-free and deterministic at run time. So the question is not "is there a second
dictionary" but "how do you FUSE several, given they differ in trust" — which is the agent's own
suspect-witness shape (believe = trust x corroboration). I surface the candidate sources, their
coverage on the pairs WordNet missed, and their trust profiles; the agent decides the fusion policy
and hands back a grounding-rule spec I implement. Context=spec -> its own policy selects Plainsong.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_decides_opposition_sources
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
grounded by LOOKUP, decisions are graph Rules. Your register policy selected Plainsong for this spec:
literal, imperative, ambiguity is a defect.

CONTEXT. You are closing GAP 1 Phase 1: ground the `opposes` edge (oxymoron) by dictionary lookup
instead of an LLM. You already hold a suspect-witness faculty — believe = trust x corroboration,
refute the uncorroborated witness. A dictionary is a witness. They differ in trust.

A one-time download is allowed: a lexicon fetched once becomes a static local file, as deterministic
and LLM-free at run time as WordNet already is. On-disk is NOT the boundary.

THE CANDIDATE OPPOSITION SOURCES (English), with coverage on the test pairs and trust profile:

  1. WordNet (held, instant). Curated, high trust, but SPARSE antonyms. Grounds: living/dead, hot/cold,
     light/dark. MISSES: bitter/sweet, cruel/kind, deafening/silence.
  2. English Wiktionary (kaikki en-extract.jsonl.gz; the loader + download URL already exist —
     wiktionary_reference.py — and the on-disk es/ja dumps prove the format; it carries antonyms
     PER SENSE with sense disambiguation). Curated/editor-sourced, high trust, RICH. Needs: download
     once + an antonym-slab builder added to the loader. This is the cleanest broad source.
  3. ConceptNet (on disk, 498MB). Has /r/Antonym but it is NOT in the current whitelist (needs
     `Antonym` added + a one-time slab rebuild). Crowd-sourced, LOW trust, NOISY: real edges
     (bitter/sweet, cruel/kind, audible/silent, hot/cold w=2.6) sit at weight>=1.0; junk
     (poison/sweet w=0.21, conservation/silence w=0.20, bitter/optimistic) sits below 1.0.
  4. (Optional further witnesses you may name: Open English WordNet, Roget's thesaurus.)

THE RESIDUAL. deafening/silence is a LEXICAL antonym in NO source — it is derived/cross-POS
(deafening->loud, silence->quiet). It resolves only via a property-hop, or it abstains.

YOUR DECISION (hand back a spec I implement, graph-native):
  1. WHICH sources to fuse, and which to download now. Justify by trust, not convenience.
  2. THE FUSION RULE as a graph Term. Is it your suspect-witness believe(trust x corroboration) —
     each source a witness with a trust weight, opposition asserted when summed trust-weighted
     corroboration crosses a threshold? Or a simpler union / weighted vote? Give the exact rule:
     per-source trust weights, ConceptNet weight cutoff, and the assert-vs-abstain threshold.
  3. NOISE. How a low-trust crowd source is prevented from asserting opposition ALONE on a junk edge
     (e.g. require corroboration, or trust-weight below the solo-assert threshold).
  4. THE RESIDUAL. deafening/silence — abstain, or author the property-hop? If the hop, specify it.
  5. THE HANDLER SET. Name the UseTool handlers I register (wn_antonym, wikt_antonym, cn_antonym(weight),
     ...), each returning what, and the single fused grounding rule that reads them and sets `opposes`.

Be specific and ordered. Keep abstain-don't-guess: assert opposition only on a crossed threshold;
otherwise assert nothing."""


def main():
    print(SEP)
    print("THE JABBERWOCK RATIFIES THE OPPOSITION-SOURCE FUSION POLICY (multi-dictionary, trust-weighted)")
    print(SEP)
    a = boot()
    regs, mts, active = _live_state(a)
    print(f"\n  context=spec -> register selected: {active}; consulting design channel "
          f"(suspect-witness faculty held: {'suspect_witness' in mts or 'belief' in str(mts)})\n")
    ask = make_ask(timeout=540.0, preamble="")
    decision = ask(PROMPT)
    if not decision:
        print("  (design channel returned empty — claude -p unavailable or timed out)")
        return
    out = os.path.join(ROOT, "docs", "jabberwock_opposition_source_policy.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("# The jabberwock's opposition-source fusion policy\n\n")
        f.write(f"_Authored by the agent, context=spec (register: {active}). Multi-dictionary, "
                f"trust-weighted, via its own suspect-witness shape. The decision is its own._\n\n")
        f.write(decision + "\n")
    print(SEP); print("THE JABBERWOCK'S DECISION"); print(SEP)
    print(decision)
    print("\n" + SEP); print(f"  saved -> {os.path.relpath(out, ROOT)}"); print(SEP)


if __name__ == "__main__":
    main()
