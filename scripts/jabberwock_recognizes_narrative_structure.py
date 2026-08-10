"""jabberwock_recognizes_narrative_structure — DEMO: the story-grammar arc,
recognised over the comprehension graph (`comprehension_reader.
read_and_comprehend`'s step 9, `domains/narrative_structure.
recognize_narrative_structure`), printed for three texts:

  1. THE CROW fable — the full SETUP -> PROBLEM -> SOLUTION -> RESOLUTION arc.
  2. THE WOLF passage — a shorter, honestly partial arc (SETUP + ACTION,
     no forced problem/resolution).
  3. A non-narrative event list — no goal, no arc at all (the discriminative
     null).

Every role printed is `ShapeDecode`'s own verdict over the
`ShapeSignatureNarrative` codebook (`seeds/narrative_structure.json`);
nothing here is a Python if/else naming a role. donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \
     scripts/jabberwock_recognizes_narrative_structure.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                  # noqa: E402
from domains import dictionary_lexicon as dl                # noqa: E402
from domains import comprehension_reader as cr              # noqa: E402
from domains import narrative_structure as ns                # noqa: E402

FABLE_TEXT = (
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
WOLF_TEXT = "The wolf was hungry. It saw a lamb. It chased the lamb."
NONNARR_TEXT = "The sun rose. A car passed. It rained."


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh_agent():
    s, node = boot_core()
    return _Agent(s, node)


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _print_arc(label: str, text: str) -> None:
    agent = _fresh_agent()
    g = cr.read_and_comprehend(agent, text, window=2)
    _hr(label)
    print(text)
    print()
    for i, s in enumerate(g["sentences"]):
        print("  [%d] %s" % (i, s))
    print()
    arcs = g["narrative_arc"]["arcs"]
    if not arcs:
        print("NO ARC RECOGNISED (no character carries a minted goal -- honest, "
              "discriminative null).")
        return
    for arc in arcs:
        print("ENTITY: %s   GOAL: %s   REMEDY: %s   GOAL SENTENCE: [%d]" %
              (arc["entity"], arc.get("remedy"), arc.get("remedy"), arc["goal_sentence"]))
        for r in arc["roles"]:
            print("  [%d] %-12s <- token=%-14s schema=%-12s  %s" %
                  (r["order"], (r.get("role") or "(none)").upper(), r["token"],
                   r.get("schema"), r["note"]))
            print("        sentence: %s" % g["sentences"][r["order"]])


def main() -> None:
    dl.warm_wordnet("en")
    _print_arc("THE CROW AND THE PITCHER", FABLE_TEXT)
    _print_arc("THE WOLF (general, not crow-tuned)", WOLF_TEXT)
    _print_arc("NON-NARRATIVE EVENT LIST (discriminative null)", NONNARR_TEXT)


if __name__ == "__main__":
    main()
