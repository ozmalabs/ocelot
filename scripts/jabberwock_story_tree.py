"""jabberwock_story_tree — MOVE 2a: the Jabberwock recognises a story's NESTED
structure as a StoryUnit TREE via a StoryBoundary collapse.

A real story is a TREE (episodes inside an arc, a tale inside a frame). The SAME
collapse that reads a clause's nested arguments and a sentence's story-grammar
role, lifted ONE level up: each inter-sentence SEAM is decoded against a
dedicated ShapeSignatureStoryBoundary codebook (seeds/story_boundary.json), and
a recognised boundary splits a root StoryUnit into child StoryUnits.

ADDITIVE RECOGNITION ONLY: this mints the tree; it does NOT unit-scope the
faculties or change any comprehension (that is MOVE 2b).

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_story_tree.py
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
from domains import story_tree as st


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


# The single-arc crow (no temporal shift, no embedding) — must stay ONE unit.
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

# A two-episode fable with a RECOGNISABLE temporal-shift seam ('Some time later').
LION_MOUSE = (
    "A lion caught a mouse. The lion let the mouse go. "
    "Some time later, the lion was caught in a net. "
    "The mouse gnawed the ropes. The mouse freed the lion."
)

# A FRAME narrative with an embedded-narrative marker ('He told the children').
FRAME = (
    "A traveller sat by the road. He told the children a story. "
    "Once a crow was thirsty. It dropped pebbles in a pitcher and drank. "
    "The children clapped."
)


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def recognise(text: str) -> dict:
    ag = _fresh()
    return st.recognize_story_tree(ag, text)


def print_tree(name: str, tree: dict) -> None:
    print("\n" + "=" * 78)
    print("STORY: %s" % name)
    print("=" * 78)
    for i, s in enumerate(tree["sentences"]):
        print("  [%d] %s" % (i, s))
    print("-" * 78)
    print("SEAMS (each decoded against the ShapeSignatureStoryBoundary codebook):")
    for sm in tree["seams"]:
        mark = "  BOUNDARY -> %s" % sm["boundary"] if sm["boundary"] else ""
        print("  seam %d|%d  token=%-18s fit=%d%s" %
              (sm["i"], sm["j"], sm["token"], sm["shape_fit"], mark))
    print("-" * 78)
    r = tree["root"]
    print("StoryUnit TREE (depth %d):" % tree["depth"])
    print("  ROOT  span[%d..%d]  (%d sentences)" %
          (r["span_start"], r["span_end"], r["n_sentences"]))
    if not tree["children"]:
        print("    (no recognised boundary -- a single-arc story stays ONE unit)")
    for c in tree["children"]:
        print("    +-- %-9s span[%d..%d]  signal=%s" %
              (c["kind"], c["span_start"], c["span_end"], c["boundary_signal"]))
        print("        %s" % " ".join(c["sentences"]))


def main() -> int:
    dl.warm_wordnet("en")
    print_tree("The Crow and the Pitcher (single arc)", recognise(CROW))
    print_tree("The Lion and the Mouse (two episodes, temporal-shift seam)",
               recognise(LION_MOUSE))
    print_tree("The Traveller's Tale (frame + embedded narrative)", recognise(FRAME))
    print("\n" + "=" * 78)
    print("MOVE 2a: the nested structure is RECOGNISED graph-natively -- each seam")
    print("collapsed against the story-boundary codebook, a boundary splitting the")
    print("root into child StoryUnits. The crow stays ONE unit (precision-safe).")
    print("This is ADDITIVE RECOGNITION: the tree is minted; NO comprehension")
    print("changes and NO faculty is unit-scoped yet (that is MOVE 2b).")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
