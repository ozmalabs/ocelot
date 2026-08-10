"""jabberwock_writes_an_analysis — DEMO: the agent WRITES a short literary
analysis of a fable, rendered from its OWN comprehension graph. donkey = 0,
graph-native, GRAPH-CHECKABLE.

The whole analysis is a SURFACE REALISATION of the comprehension graph
`domains.comprehension_reader.read_and_comprehend` builds: the SUMMARY from the
causal-weighted centrality, the NARRATIVE STRUCTURE from the story-grammar arc
(setup/problem/solution/resolution `NarrativeRole` nodes), the TECHNIQUE from
the recognised TROPES (MacGyvering / Determinator), the THEME from the trope-
derived moral. Affirmative event clauses are realised by the agent's OWN
production faculty (`LanguageProduction.produce`, no LLM); negation + abstract
trope/theme attribution are fixed connectives filled from graph nodes. Every
sentence carries a CLAIM -> GRAPH-FACT pointer — the anti-hallucination trace.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_writes_an_analysis.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import literary_analysis as la


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


CROW = (
    "In a spell of dry weather, when the Birds could find very little to "
    "drink, a thirsty Crow found a pitcher with a little water in it. "
    "But the pitcher was high and had a narrow neck, and no matter how he "
    "tried, the Crow could not reach the water. "
    "The poor thing felt as if he must die of thirst. "
    "Then an idea came to him. "
    "Picking up some small pebbles, he dropped them into the pitcher one by "
    "one. "
    "With each pebble the water rose a little higher until at last it was "
    "near enough so he could drink."
)
MOUSE = (
    "Stones blocked the path. A mouse was hungry. But the cheese was locked "
    "behind the stones, and the mouse could not reach it. The mouse took "
    "them away one by one. So the mouse ate the cheese."
)


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _run(title: str, text: str) -> bool:
    print("\n" + "=" * 78)
    print("THE FABLE (%s):" % title)
    print("  " + text)
    print("=" * 78)
    agent = _fresh()
    res = la.produce_analysis(agent, text)

    print("\nTHE JABBERWOCK'S ANALYSIS:\n")
    print(res["text"])

    print("\n" + "-" * 78)
    print("CLAIM -> GRAPH-FACT MAP (every sentence traces to a graph node):")
    print("-" * 78)
    for sent, info in res["claim_map"].items():
        tag = "produced" if info["kind"] == "produced" else "framed  "
        print("  [%s | %-9s] nodes=%s" % (tag, info["section"], info["pointers"]))
        print("      %s" % sent)

    ver = la.verify_grounding(agent, res)
    print("-" * 78)
    print("GRAPH-CHECKABLE: %s (%d pointer checks, %d unresolved)"
          % ("PASS" if ver["ok"] else "FAIL", ver["checked"], len(ver["unresolved"])))
    print("  produced (faculty) sentences: %d | framed (graph-filled connective): %d"
          % (res["produced_count"], res["framed_count"]))
    return ver["ok"]


def main() -> int:
    dl.warm_wordnet("en")
    ok_crow = _run("The Crow and the Pitcher", CROW)
    ok_mouse = _run("The Mouse and the Stones (general — different trope)", MOUSE)
    print("\n" + "=" * 78)
    ok = ok_crow and ok_mouse
    print("ALL GRAPH-CHECKABLE" if ok else "**FAILED** — an ungrounded claim appeared")
    print("Every content word was read off a graph node; the event clauses were")
    print("realised by the agent's OWN production faculty (no LLM). The analysis is")
    print("a graph-grounded fable reading — coherence AND correctness, by construction.")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
