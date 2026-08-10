"""jabberwock_reads_the_moral — RICH SEMANTIC TROPES: the moral from CONTENT
RELATIONS, not arc shape.

THE CEILING (generic-reading): a trope LEARNED from a residual arc-STRUCTURE is
COARSE. LEARNED_PROBLEM / LEARNED_INCREMENTAL name a SHAPE (a problem is faced,
repeated small effort), not a MORAL (gratitude / flattery / foresight). A rich
trope needs the CONTENT RELATIONS — who acts on whom (the participant-relation
pattern read off the situation model's own events) + the outcome VALENCE (which
protagonist ends acting/gaining vs passive) — not the arc shape alone.

THE FIX (graph-native, reuse the sd loop): when the reader has a situation
model, decode its CONTENT signature — a small set of participant-relation tokens
(REVERSAL = an earlier deed A->B, a later reversed deed B->A, reusing
nested_reading's own RETURN_ACTION reversal; SPEECH_DEED = an actor turns words
to another into a deed; STORE_CONSUME = an actor provides then consumes its own
store; MUTUAL_SPEECH = two parties trade words with no deed returned) — against a
ShapeSignatureSemanticTrope codebook that GROWS via the sd_mint_quantum loop (one
axis ACROSS from narrative_tropes' arc-shape codebook). A seeded content pattern
decodes to a RICH moral (reciprocity/flattery/foresight, read off the winning
schema's own theme); a content relation NO seeded pattern covers MINTS a LEARNED
semantic quantum (the general novel-content path). tropes_teacher NAMES the
already-decided trope. No moral-name literal drives the mint — the WHICH-moral
decision is ShapeDecode's own verdict.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_the_moral.py
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
from domains import reading_drive as rd
from domains import trope_theme as tt
import jabberwock_produces_analysis_from_goal as jpafg
import jabberwock_reads_nested_story as jrns


CROW = jpafg.CROW
LION_MOUSE = jrns.LION_MOUSE

# FLATTERY (Fox and Crow): A flatters B to get B's cheese — praise-as-means. The
# content relation is SPEECH_DEED (fox speaks to crow, then fox converts talk
# into a deed), the valence asymmetric (fox acts/gains, crow left passive).
FLATTERY = ("A crow had a piece of cheese. A fox praised the crow. "
            "The crow sang a song. The fox snatched the cheese.")

# FORESIGHT (Ant and Grasshopper): A prepares, B doesn't, A survives. The content
# relation is STORE_CONSUME (the ant stores the grain then consumes its own
# store), the valence split (the ant provident, the grasshopper idle/passive).
FORESIGHT = ("The ant stored the grain. The grasshopper played all summer. "
             "Then the winter came. The ant ate the grain.")

# GENERAL — a NOVEL content relation OUTSIDE every seeded semantic pattern: mutual
# flattery (both trade words, neither returns a deed). MUTUAL_SPEECH is not a
# seeded moral -> the sd loop LEARNS it (mints a learned semantic quantum).
NOVEL = "The fox flattered the crow. The crow praised the fox."


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def read_moral_flat(text: str) -> dict:
    ag = _fresh()
    rd.comprehension_result(ag, text)
    return {"agent": ag, "semantic": tt.recognize_semantic_trope(ag)}


def read_moral_nested(text: str) -> dict:
    ag = _fresh()
    rd.run_nested_reading_flow(ag, text)
    return {"agent": ag, "semantic": tt.recognize_semantic_trope(ag)}


def _print(label, res):
    sem = res["semantic"]
    print("  tokens: %s | learned quantum: %s" % (
        sem["tokens"], (sem.get("learned") or {}).get("name")))
    for t in sem["tropes"]:
        src = t.get("label", {}).get("source")
        print("  MORAL: %s%s" % (t["name"], "  (LEARNED)" if t.get("learned") else ""))
        print("    theme   : %r" % t.get("theme"))
        print("    line    : %s" % t.get("line"))
        print("    valence : %s | outcome: %s" % (t.get("valence"), t.get("outcome")))
        print("    named   : %s (%s)" % (t.get("label", {}).get("name"), src))
        for ev in tt.semantic_trope_evidence(res["agent"], t["_node_obj"]):
            print("       evidence <- SmEvent %s->%s (%s)" % (ev["agent"], ev["patient"], ev["verb"]))


def main() -> None:
    dl.warm_wordnet("en")

    print("=" * 78)
    print("1. LION AND MOUSE — RECIPROCITY (a kindness is repaid), not LEARNED_INCREMENTAL")
    print("=" * 78)
    _print("lion-mouse", read_moral_nested(LION_MOUSE))

    print("\n" + "=" * 78)
    print("2. FOX AND CROW — FLATTERY (praise used to gain another's loss)")
    print("=" * 78)
    _print("fox-crow", read_moral_flat(FLATTERY))

    print("\n" + "=" * 78)
    print("3. ANT AND GRASSHOPPER — FORESIGHT (the provident outlast the idle)")
    print("=" * 78)
    _print("ant-grasshopper", read_moral_flat(FORESIGHT))

    print("\n" + "=" * 78)
    print("4. GENERAL — a NOVEL content relation mints a LEARNED semantic trope")
    print("=" * 78)
    _print("novel", read_moral_flat(NOVEL))

    print("\n" + "=" * 78)
    print("5. CROW — semantic recogniser is an honest null (no content-relation signal);")
    print("   the arc-shape tropes (INGENUITY/PERSISTENCE) are UNCHANGED.")
    print("=" * 78)
    crow = read_moral_flat(CROW)
    print("  semantic tokens: %s (%s)"
          % (crow["semantic"]["tokens"], crow["semantic"].get("reason")))


if __name__ == "__main__":
    main()
