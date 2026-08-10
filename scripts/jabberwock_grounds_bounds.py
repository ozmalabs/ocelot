"""STEP 1 — THE JABBERWOCK LOOKS UP + GROUNDS THE 'BOUNDS' CONCEPT CLUSTER.

A THIN WORLD-ADAPTER / TEACHER SHELL (CLAUDE.md). It owns NO reasoning. It points
the agent's grounding-loop READ step at its OWN reference world (Wikipedia via
wiki_local / WordNet via wordnet_genus — "it has wikipedia, it should be able to
look up most of what it needs") and runs the agent's OWN recursive grounding
(read_and_ground.ground_recursively) on the cluster of concepts needed to perceive
"an arbitrary-shaped area that is a thing": region, boundary, interior, enclosure,
figure/ground, perimeter, containment, shape.

The agent READS each term's article/genus, COMPREHENDS its genus-differentia, and
GROUNDS it down the genus chain to a SEEDED PRIMITIVE — so the resulting concept is
graph-native and the agent UNDERSTANDS what it is (it can name the genus it bottoms
out on). The shell prints the agent's verdict VERBATIM; it authors no definition.

This is the foundation the figure/ground DSL concept (step 2) composes ON: the
agent can only author "area = a bounded region that encloses things" in its own
grounded vocabulary once it has GROUNDED region / boundary / enclosure.

Reuses the proven wiring from jabberwock_reads_arc_agi_3 (ground_terms + the
semantic-prime / lexical-ontology-root floors) — nothing re-authored here.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.jabberwock_reads_arc_agi_3 import ground_terms  # noqa: E402

SEP = "=" * 78

# The concept cluster the agent needs to perceive "an arbitrary-shaped area that
# is a thing" (figure/ground over the grid). These are the WORDS it looks up — the
# meaning comes from its reference world, not from this list.
CLUSTER = [
    "region",       # the genus: a connected area of space
    "boundary",     # what separates an area from its outside
    "interior",     # the inside of a bounded region
    "enclosure",    # an area shut in by a boundary
    "containment",  # one thing being inside another
    "perimeter",    # the edge path bounding an area
    "figure",       # (figure-ground) the thing that stands out from its ground
    "shape",        # the form of a bounded region
]


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--via", choices=["lexicon", "wiki"], default="lexicon",
                    help="READ source: WordNet genus ladder (most reliable for "
                         "abstract spatial nouns) or Wikipedia article leads")
    ap.add_argument("--concepts", nargs="*", default=None,
                    help="override the cluster")
    args = ap.parse_args(argv)

    cluster = args.concepts or CLUSTER
    freq = Counter({c: 1 for c in cluster})

    print(SEP)
    print("STEP 1 — THE JABBERWOCK LOOKS UP THE 'BOUNDS' CLUSTER + GROUNDS IT")
    print(f"  source = {args.via}   concepts = {cluster}")
    print("  (the agent reads + comprehends + grounds each to a seeded primitive;")
    print("   the shell only points the READ step at its reference world)")
    print(SEP)

    res = ground_terms(freq, via_wiki=(args.via == "wiki"),
                       via_lexicon=(args.via == "lexicon"),
                       limit=len(cluster))

    n_ground = 0
    for r in res:
        ok = r["grounded"]
        n_ground += ok
        print(f"\n  · {r['term']}")
        print(f"      grounded : {ok}")
        print(f"      genus    : {r.get('genus')}")
        print(f"      cone->   : {r.get('cone')}")
        if not ok:
            print(f"      reason   : {r.get('reason')}")

    print(f"\n{SEP}")
    print(f"  grounded {n_ground}/{len(cluster)} of the bounds cluster")
    print("  -> the vocabulary the agent will COMPOSE 'area = bounded region that")
    print("     encloses things' from, in step 2 (graph-native DSL it authors).")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
