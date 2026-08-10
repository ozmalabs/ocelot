"""jabberwock_produces_analysis_from_goal — THE HEADLINE: the Jabberwock is
SEEDED WITH A GOAL and the source as I/O, and PRODUCES a literary analysis. There
is NO Python orchestration between ingest and read-out — the comprehension->
analysis process fires to a `run_rules` FIXPOINT, driven by the goal + the
data-dependencies encoded in seeds/literary_analysis_driving.json. The analysis
emerges as graph state (`Claim` nodes) and is read back out.

The BODY of `analyse` below is the whole demonstration: boot -> INGEST the source
(mint a Source node) -> MINT the 'produce analysis' Goal -> PUMP (fire the seeded
reflex + run the seeded dispatch rules to fixpoint) -> READ the report off the
graph. No `faculty1(); faculty2(); ...` sequence exists between ingest and read.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_produces_analysis_from_goal.py
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


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


# --------------------------------------------------------------------------- #
#  THE WHOLE FLOW — seed a Goal + source, PUMP, read the report. There is NO
#  faculty-sequencing Python between INGEST and READ-OFF: the two lines that
#  matter are `run_reading_flow` (which only ingests, mints the goal, mints the
#  stages, and pumps the seeded rules/reflex) and `_read_report_off_graph`.
# --------------------------------------------------------------------------- #
def analyse(text: str) -> dict:
    s, node = boot_core()
    # 1..4 — INGEST the source, MINT the 'produce analysis' Goal, MINT the stages,
    #        and PUMP the seeded reflex + dispatch rules to a run_rules fixpoint.
    #        NOTHING in here sequences a faculty — the ORDER is the seed's rules.
    bb = rd.run_reading_flow(_Agent(s, node), text, report="analysis")
    # 5 — READ the report off the graph (mechanical I/O over the minted Claim nodes).
    report = _read_report_off_graph(s)
    return {"report": report, "claim_nodes": len(s.nodes("Claim")), "bb": bb}


def _read_report_off_graph(s) -> str:
    """Read the analysis back out of GRAPH STATE — the Claim nodes the production
    stages minted — and assemble section-ordered prose. Pure query; no decision."""
    titles = [("SUMMARY", "Summary"), ("STRUCTURE", "Narrative structure"),
              ("TECHNIQUE", "Technique"), ("THEME", "Theme")]
    by_section: dict[str, list] = {}
    for n in s.nodes("Claim"):
        at = s.node(n)["attrs"]
        by_section.setdefault(at.get("section"), []).append(
            (at.get("order"), at.get("sentence")))
    parts = []
    for sec, title in titles:
        rows = sorted(by_section.get(sec) or [])
        if rows:
            parts.append(title + ". " + " ".join(sent for _, sent in rows))
    return "\n\n".join(parts)


def _run(name: str, text: str) -> None:
    print("\n" + "=" * 78)
    print("THE FABLE (%s):\n  %s" % (name, text))
    print("=" * 78)
    out = analyse(text)
    print("\nTHE JABBERWOCK'S ANALYSIS (read off %d graph Claim nodes):\n"
          % out["claim_nodes"])
    print(out["report"])


def main() -> int:
    dl.warm_wordnet("en")
    _run("The Crow and the Pitcher", CROW)
    _run("The Mouse and the Stones (general — different trope)", MOUSE)
    print("\n" + "=" * 78)
    print("The Jabberwock was given ONE instruction — a Goal — and the source as")
    print("I/O. The comprehension->analysis process fired to a run_rules fixpoint,")
    print("sequenced by data-dependencies in seeds/literary_analysis_driving.json.")
    print("No Python orchestrated the faculties; the analysis is graph state.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
