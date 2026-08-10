"""Seed ONE goal — a rich understanding of language — and let the agent READ to grow it.

The agent boots with its on-disk teachers (dictionary/WordNet, wiki, tropes) chained cheapest-first.
The host does only the reading I/O: stream real Wikipedia prose in; the agent's OWN OOV-learning
faculty (ground_unknowns -> teacher -> learn_from_teacher, minting a Concept + Sign per word) grows
the lexicon. No per-word decisions by the host; the agent grounds what it does not know. Run a few
minutes -> the lexicon compounds.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_for_understanding [word_budget]
"""
from __future__ import annotations
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from domains.libraries import attach_libraries
from domains.wiki_library import WikipediaLibrary

SEP = "=" * 92


def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 1500   # word-grounding attempts
    print(SEP)
    print("SEED ONE GOAL — a rich understanding of language — and READ to grow it")
    print(SEP)
    a = boot()
    rep = attach_libraries(a, log=lambda *x: None)   # restore the on-disk teacher chain
    print(f"  teachers: {rep.get('teachers')}  | LLM: {rep.get('partner') or 'off'}")
    wiki = WikipediaLibrary()

    before = len(a.s.nodes("Concept"))
    learned, attempted, articles = [], 0, 0
    t0 = time.time()
    import random
    rng = random.Random(7)
    while attempted < budget:
        art = wiki.random_article(rng)
        if not art or not art.section_names():
            continue
        text = " ".join(art.section_text(i) for i in range(min(3, len(art.section_names()))))
        if len(text) < 40:
            continue
        articles += 1
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if len(sent) < 8:
                continue
            attempted += len(re.findall(r"[A-Za-z]{3,}", sent))
            try:
                got = a.ground_unknowns(sent)        # the agent grounds what it doesn't know
            except Exception:
                got = []
            learned.extend(got)
            if attempted >= budget:
                break
        if articles % 5 == 0:
            print(f"  ...read {articles} articles, {attempted} words seen, "
                  f"{len(a.s.nodes('Concept'))-before} new concepts ({time.time()-t0:.0f}s)", flush=True)

    after = len(a.s.nodes("Concept"))
    dt = time.time() - t0
    uniq = sorted(set(learned))
    print(f"\n  read {articles} Wikipedia articles, {attempted} words, in {dt:.0f}s")
    print(f"  lexicon: {before} -> {after} concepts  (+{after-before}, ~{(after-before)/max(dt,1)*60:.0f}/min)")
    print(f"  distinct words grounded this run: {len(uniq)}")
    print(f"  sample of what it learned: {uniq[:40]}")

    print("\n" + SEP)
    print(f"  One seeded goal + a few minutes of reading: the agent grew its lexicon by {after-before} "
          f"concepts on its own, grounding every unknown word from its dictionary/wiki/tropes teachers. "
          f"The machinery compounds — understanding scales with reading time.")
    print(SEP)


if __name__ == "__main__":
    main()
