"""jabberwock_recognizes_tropes — DEMO: TROPE + THEME, one level up from the
story-grammar arc (`comprehension_reader.read_and_comprehend`'s step 10,
`domains/trope_theme.recognize_tropes_and_theme`), printed for four texts:

  1. THE CROW fable — instantiates BOTH seeded tropes at once:
     INGENUITY_OVER_STRENGTH (problem + an indirect physical-effect
     mechanism) and PERSISTENCE_PAYS (an incremental, plural-affected-entity
     action + a met resolution).
  2. THE MOUSE fable (general, NOT crow-tuned) — a DIFFERENT trope: pure
     PERSISTENCE_PAYS, no indirect/physical-effect mechanism at all (the
     mouse just grinds through stones one at a time; no cleverness signal).
  3. THE WOLF passage — an arc that never earns a problem/resolution role at
     all: an honest, discriminative NULL, no trope forced.
  4. A non-narrative event list — no arc, no trope, nothing to recognise.

Every trope name printed is `ShapeDecode`'s own set-cover verdict over the
`ShapeSignatureTrope` codebook (`seeds/narrative_tropes.json`); nothing here
is a Python if/else naming a trope. The label (TVTropes name/definition) is a
LOOKUP applied AFTER the decode already decided which trope fired
(`domains/tropes_teacher.py`). donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \
     scripts/jabberwock_recognizes_tropes.py
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
from domains import trope_theme as tt                        # noqa: E402

CROW_TEXT = (
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
MOUSE_TEXT = (
    "Stones blocked the path. A mouse was hungry. But the cheese was locked "
    "behind the stones, and the mouse could not reach it. The mouse took "
    "them away one by one. So the mouse ate the cheese."
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


def _print_tropes(label: str, text: str) -> None:
    agent = _fresh_agent()
    g = cr.read_and_comprehend(agent, text, window=2)
    _hr(label)
    print(text)
    print()
    for i, s in enumerate(g["sentences"]):
        print("  [%d] %s" % (i, s))
    print()

    results = g["trope_theme"]["results"]
    if not results:
        print("NO TROPE RECOGNISED (no narrative arc at all -- honest, "
              "discriminative null).")
        return

    for r in results:
        print("ENTITY: %s   mechanical tokens present: %s" % (r["entity"], r["tokens"]))
        if not r["tropes"]:
            print("  NO TROPE RECOGNISED -- %s" % r["reason"])
            continue
        for t in r["tropes"]:
            print("  TROPE: %s   (covers %s, shape_fit=%s)" %
                  (t["name"], t["covered_tokens"], t["shape_fit"]))
            print("    label: %r [%s]" % (t["label"]["name"], t["label"]["source"]))
            print("    theme: %s" % t["theme"])
            print("    graph-checkable evidence:")
            for ev in tt.trope_evidence(agent, t["_node_obj"]):
                if ev["kind"] == "NarrativeRole":
                    a = ev["attrs"]
                    print("      <- NarrativeRole[%d] role=%s token=%s :: %s" %
                          (a["order"], a["role"], a["token"], g["sentences"][a["order"]]))
                else:
                    print("      <- %s: %s" % (ev["kind"], ev["attrs"].get("record_json")))
        theme = r["theme"]
        print("  ARC THEME (all recognised tropes' own moral):")
        for line in theme["lines"]:
            print("    - %s" % line)


def main() -> None:
    dl.warm_wordnet("en")
    _print_tropes("THE CROW AND THE PITCHER (both seeded tropes fire)", CROW_TEXT)
    _print_tropes("THE MOUSE AND THE STONES (general, a DIFFERENT trope)", MOUSE_TEXT)
    _print_tropes("THE WOLF (discriminative null -- no problem/resolution roles)", WOLF_TEXT)
    _print_tropes("NON-NARRATIVE EVENT LIST (discriminative null -- no arc)", NONNARR_TEXT)


if __name__ == "__main__":
    main()
