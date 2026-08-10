#!/usr/bin/env python3
"""jabberwock_reads_discourse — demo driver for domains/discourse_coherence.py.

Prints, verbatim:
  1. MARKED coherence relations (cause via 'therefore', contrast via 'however').
  2. UNMARKED coherence relation (situation-model-style signal, no connective).
  3. MARKED == UNMARKED convergence proof (same two events, same relation).
  4. DISCRIMINATIVE (unrelated sentences -> no spurious relation).
  5. CENTRALITY ranking over a short causal chain (the crow-and-pitcher story) —
     the summary substrate: the causal hinge ranked above peripheral detail.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_discourse.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core             # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import discourse_coherence as dc          # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def fresh():
    s, node = boot_core()
    return _Agent(s, node)


def show_pair(label, span_a, span_b):
    ag = fresh()
    r = dc.coherence_between(ag, span_a, span_b)
    print("\n[%s]" % label)
    print("  spanA:    %r" % span_a)
    print("  spanB:    %r" % span_b)
    print("  trigger:  %s" % r["trigger"])
    print("  skeleton: %s" % r["skeleton"])
    print("  construction: %s  (shape_fit=%d)" % (r["construction"], r["shape_fit"]))
    print("  RELATION: %s" % r["relation"])
    print("  note: %s" % r["note"])
    return r


def main():
    dl.warm_wordnet("en")

    print("=" * 78)
    print("1. MARKED coherence relations")
    print("=" * 78)
    show_pair("cause / therefore", "It was raining.", "Therefore the match was cancelled.")
    show_pair("contrast / however", "The house was cheap.", "However, it was far.")
    show_pair("condition / if", "It might rain today.", "If it rains, we will cancel the match.")

    print("\n" + "=" * 78)
    print("2. UNMARKED coherence relation (no connective)")
    print("=" * 78)
    show_pair("unmarked cause (telic-result verb)", "She trained daily.", "She won the race.")

    print("\n" + "=" * 78)
    print("3. MARKED == UNMARKED convergence — same two events, same relation")
    print("=" * 78)
    r_unmarked = show_pair("unmarked", "She trained daily.", "She won the race.")
    r_marked = show_pair("marked", "She trained daily.", "Therefore she won the race.")
    print("\n  unmarked relation = %r, marked relation = %r -> CONVERGE: %s"
          % (r_unmarked["relation"], r_marked["relation"], r_unmarked["relation"] == r_marked["relation"]))

    print("\n" + "=" * 78)
    print("4. DISCRIMINATIVE — unrelated sentences mint NO spurious relation")
    print("=" * 78)
    show_pair("unrelated", "The cat slept on the mat.", "Stock prices rose sharply in Tokyo.")

    print("\n" + "=" * 78)
    print("5. CENTRALITY — causal-network summary substrate")
    print("=" * 78)
    story = (
        "The crow was thirsty. "
        "The crow found a pitcher. "
        "The pitcher held water. "
        "The crow dropped pebbles in the pitcher. "
        "The water in the pitcher rose. "
        "The crow was able to drink."
    )
    ag = fresh()
    read = dc.read_discourse(ag, story, window=2)
    print("\nSTORY: %r" % story)
    print("\nSPAN-PAIR DECODES:")
    for p in read["pairs"]:
        print("  (%d,%d) %-28s -> relation=%-10s  [%s]"
              % (p["i"], p["j"], p["trigger"], p["relation"], p["note"][:90]))

    ranking = dc.centrality_ranking(ag)
    print("\nCENTRALITY RANKING (Argmax-picked winner first; display order = sorted()):")
    for row in ranking["ranking"]:
        marker = "  <== ARGMAX WINNER" if row["node"] == ranking["argmax_winner"] else ""
        print("  degree=%d   %r%s" % (row["degree"], row["label"], marker))
    print("\nargmax_winner node id: %s   matches top-of-sort: %s"
          % (ranking["argmax_winner"], ranking["argmax_matches_top_of_sort"]))
    print("\n=> the SUMMARY SUBSTRATE is the top-ranked event(s): the causal hinge")
    print("   ('dropped pebbles' / 'water rose'), not the orientation/resolution detail.")


if __name__ == "__main__":
    main()
