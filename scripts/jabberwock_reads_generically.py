"""jabberwock_reads_generically — READING WITHOUT SEEDED CODEBOOKS.

The reader learns a story's categories FROM the story, via the sd loop. Two
levers make the recognition absolutely generic:

  1. CHANGE-OF-STATE -> GENERIC EVENTIVE. situation_model_reader used to mint an
     SmEvent only for a SEEDED change-of-state verb class (drop/rise/break/... +
     their canonical state-delta rule). A mercy/rescue verb (caught/let/gnawed/
     freed/spared) was in NO seeded class, so it minted NOTHING -> the per-episode
     arcs of 'The Lion and the Mouse' were EMPTY. Now a predication whose verb is
     EVENTIVE (a dynamic action/change) mints an SmEvent; a STATIVE (be/seem/
     resemble/...) does not. The eventive-vs-stative decision is WordNet's OWN verb
     lexicographer-file classification (`eventive_membership` -> the dominant
     sense's lexname; `verb.stative` is the only stative class), NOT a seeded verb
     list. ANY action verb mints an event -> the L&M per-episode arcs FILL, and a
     goalless tale gets a generic event-sequence arc (setup + actions).

  2. TROPE/THEME -> GENERIC (sd-loop LEARNING). trope_theme matched a SEEDED trope
     codebook one-shot; an arc no seeded trope covered got a bare honest null. Now,
     when an arc instantiates NO seeded trope yet carries structural signal tokens,
     the reader MINTS a LEARNED ShapeSignatureTrope quantum FROM that residual (the
     `sd_mint_quantum` precedent, one level up -- dynamic quantization at the trope
     level) and mints its Trope; the THEME is abstracted GENERICALLY from the arc's
     own structure (a coarse structural moral, not a canned per-trope gloss).
     tropes_teacher (TVTropes) is used ONLY to NAME a learned structural trope --
     the RECOGNITION/MINT is generic. So a fable OUTSIDE every seeded trope still
     gets a learned trope, read from its own structure.

The crow stays byte-identical: its COS verbs still resolve to their canonical
delta rules, and its arc is fully covered by the seeded tropes, so nothing is
learned/minted for it.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_generically.py
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
from domains import narrative_structure as ns
import jabberwock_produces_analysis_from_goal as jpafg
import jabberwock_reads_nested_story as jrns


CROW = jpafg.CROW
LION_MOUSE = jrns.LION_MOUSE

# A NOVEL fable OUTSIDE every seeded trope (a hunger/obstacle tale that reaches no
# physical-displacement solution, so it instantiates none of INGENUITY_OVER_
# STRENGTH / PERSISTENCE_PAYS / NECESSITY_INVENTION) -- the reader must LEARN its
# trope from structure. Written on the crow's own prose skeleton so the goal +
# problem role form, but with a locked door (no pebble-drop mechanism, no remedy
# met) so the seeded tropes cannot fire.
FOX_HEN = (
    "In a spell of cold weather, a hungry Fox found a henhouse with a fat hen in it. "
    "But the henhouse was locked and had a strong door, and no matter how he tried, "
    "the Fox could not reach the hen. The poor thing felt as if he must die of hunger."
)


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def read_lion_mouse():
    return rd.run_nested_reading_flow(_fresh(), LION_MOUSE)


def read_novel_fable(text: str = FOX_HEN) -> dict:
    ag = _fresh()
    graph = rd.comprehension_result(ag, text)
    roles = [(r.get("role"), r.get("order"), r.get("entity"))
             for r in ns.read_narrative_roles(ag)]
    tt_results = (graph.get("trope_theme") or {}).get("results") or []
    return {"agent": ag, "roles": roles, "trope_theme": tt_results}


def main() -> None:
    dl.warm_wordnet("en")

    print("=" * 78)
    print("1. GENERIC EVENTIVE — 'The Lion and the Mouse' per-episode arcs FILL")
    print("=" * 78)
    out = read_lion_mouse()
    for i, u in enumerate(out["units"], start=1):
        roles = [(r.get("role"), r.get("order")) for r in u["narrative_roles"]]
        print("  episode %d (%s): arc roles = %s"
              % (i, "mercy" if i == 1 else "rescue", roles))
    stt = out["spanning_theme"]
    print("  spanning theme: %r (token %s)" % (stt["theme"], stt["token"]))

    print("\n" + "=" * 78)
    print("2. GENERIC TROPE LEARNING — a NOVEL fable outside every seeded codebook")
    print("=" * 78)
    nov = read_novel_fable()
    print("  arc roles = %s" % (nov["roles"],))
    for r in nov["trope_theme"]:
        learned = r.get("learned")
        print("  entity %r: tokens %s" % (r["entity"], r.get("tokens")))
        print("    learned trope: %s" % (learned and learned.get("name")))
        for tr in r["tropes"]:
            print("    trope %r  label=%s (%s)"
                  % (tr.get("name"), tr.get("label", {}).get("name"),
                     tr.get("label", {}).get("source")))
        if r.get("theme"):
            print("    theme: %s" % (r["theme"].get("lines")))

    print("\n" + "=" * 78)
    print("3. CROW — byte-identical (COS canon + seeded tropes still cover it)")
    print("=" * 78)
    rep = jpafg.analyse(CROW)["report"]
    print(rep)


if __name__ == "__main__":
    main()
