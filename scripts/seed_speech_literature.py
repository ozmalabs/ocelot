"""SEED THE JABBERWOCK WITH THE REPRESENTATION-LEARNING LITERATURE.

The real-speech ceiling is architectural: the agent SELECTS and NORMALISES features but never uses
the labels to LEARN a discriminative representation. So seed it with the literature for exactly that
capability — a linear discriminant (LDA, closed-form, composable) and a learned non-linear embedding
(metric learning / x-vector, which the agent can ASSEMBLE as a net). The agent reads each paper
(domains/paper_reader) and HOLDS it as theory-under-test: it ingests the axioms/theorems/hypotheses
as typed graph nodes it can introspect and EMPIRICALLY TEST (its operational behaviour is the test),
without committing to their truth. The hypotheses become its next experiments.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.seed_speech_literature
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
from domains.paper_reader import install_paper_as_theory

SEP = "=" * 88

_TYPES = ("Microtheory", "Concept", "Rule", "Paper", "PaperSection", "PaperAxiom",
          "PaperTheorem", "PaperConjecture", "PaperHypothesis")
_EDGES = ("owns_paper", "has_section", "states", "contains_claim", "has_rule",
          "has_concept", "implements", "refers_to")


def fresh_substrate():
    """A substrate with the paper vocabulary declared so the reader's edges are admissible."""
    s = srs.Substrate()
    for st in _TYPES:
        for tt in _TYPES:
            for et in _EDGES:
                try:
                    s.add_production({"src": {"type": st, "var": "src"}, "edge_type": et,
                                      "tgt": {"type": tt, "var": "tgt"}, "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "literature"})
                except Exception:
                    pass
    return s
PAPERS = [
    ("discriminative_linear_transforms",
     "docs/literature/discriminative_linear_transforms.md"),
    ("learned_discriminative_embeddings",
     "docs/literature/learned_discriminative_embeddings.md"),
    ("cognitive_representation_learning",
     "docs/literature/cognitive_representation_learning.md"),
]


def main():
    print(SEP)
    print("SEED THE JABBERWOCK WITH THE REPRESENTATION-LEARNING LITERATURE (held as theory-under-test).")
    print(SEP)
    s = fresh_substrate()
    for pid, rel in PAPERS:
        mt = install_paper_as_theory(s, Path(os.path.join(ROOT, rel)), pid)
        ok = mt is not None
        print(f"  read '{rel}'  ->  {'ingested as theory' if ok else 'FAILED'}")

    counts = {t: len(s.nodes(t)) for t in
              ("Paper", "PaperSection", "PaperAxiom", "PaperTheorem", "PaperHypothesis", "Microtheory")}
    print(f"\n  ingested graph: " + "  ".join(f"{t}={n}" for t, n in counts.items() if n))

    print(f"\n  THE AGENT NOW HOLDS THESE TESTABLE CLAIMS (its next experiments):")
    for h in s.nodes("PaperHypothesis"):
        a = s.node(h)["attrs"]
        lbl = a.get("label") or a.get("title") or ""
        txt = (a.get("text", "") or "").replace("\n", " ")
        # first sentence of the hypothesis
        first = txt.split(". ")[0][:200]
        print(f"    - Hypothesis {lbl}: {first}.")
    print(f"\n  AXIOMS/THEOREMS it can introspect and enact:")
    for t in ("PaperAxiom", "PaperTheorem"):
        for n in s.nodes(t):
            a = s.node(n)["attrs"]
            print(f"    - {t[5:]} {a.get('label','')}: {a.get('title','')}")

    print(f"\n{SEP}")
    print("  The agent has read the literature for the transforms it lacked. The hypotheses are its")
    print("  roadmap: fit LDA on labelled exemplars (linear, closed-form) -> if residual, ASSEMBLE a")
    print("  learned embedding (its net machinery). It holds these as theory to TEST, not assume.")
    print(SEP)


if __name__ == "__main__":
    main()
