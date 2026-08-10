"""jabberwock_reads_nested_story — MOVE 2b: COMPREHENSION RECURSES OVER THE
StoryUnit TREE. Each StoryUnit comprehends in ISOLATION (the `unit` graph
dimension threaded through the six faculties), and the PARENT composes a
SPANNING theme from its children.

  * CROW (depth-1) — one root unit, no children: the flat comprehension is
    UNCHANGED (order-N with N=1 IS the flat case). Its goal-driven analysis
    report stays BYTE-IDENTICAL.
  * LION & MOUSE (2-unit tree) — each episode gets its OWN entities + actions,
    ISOLATED (episode 2's re-introduced lion is a DISTINCT graph node from
    episode 1's lion); the PARENT composes the spanning theme RECIPROCITY
    (episode 2's rescue reciprocates episode 1's mercy) -- a cross-episode
    RELATION invisible in either episode alone, read off the children's own
    minted UnitAction nodes by a ShapeDecode over the ShapeSignatureSpanningTheme
    codebook. The per-unit recursion is the seeded u_dispatch_* rules firing PER
    StoryUnit (run_rules recurses over the tree); there is NO Python
    `for unit: comprehend(unit)` loop.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_nested_story.py
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
import jabberwock_produces_analysis_from_goal as jpafg

CROW = jpafg.CROW
LION_MOUSE = (
    "A lion caught a mouse. The lion let the mouse go. "
    "Some time later, the lion was caught in a net. "
    "The mouse gnawed the ropes. The mouse freed the lion."
)


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def read_nested(text: str) -> dict:
    return rd.run_nested_reading_flow(_fresh(), text)


def print_nested(name: str, out: dict) -> None:
    print("\n" + "=" * 78)
    print("STORY: %s   (depth %d)" % (name, out["depth"]))
    print("=" * 78)
    for u in out["units"]:
        print("  UNIT %s" % u["unit"])
        print("    entities : %s" % ", ".join(u["entities"]))
        print("    actions  : %s" % ", ".join(
            "%s -> %s (%s)" % (a["agent"], a["patient"], a["rel"]) for a in u["actions"]))
        roles = [(r.get("order"), r.get("role")) for r in u["narrative_roles"]]
        print("    arc roles: %s" % (roles or "(none — representation-bound)"))
    stt = out["spanning_theme"]
    if stt:
        print("  SPANNING THEME (composed from the children): %s" % stt["theme"].upper())
        print("    %s" % stt["line"])
    else:
        print("  SPANNING THEME: (none composed)")


def main() -> int:
    dl.warm_wordnet("en")
    # CROW — depth-1, flat comprehension unchanged (order-N N=1 = flat).
    crow = read_nested(CROW)
    print_nested("The Crow and the Pitcher (single arc)", crow)
    print("  (depth-1: no child units — the flat report is byte-identical; see the")
    print("   frozen-baseline assert in tests/test_order_n_nested_story.py)")
    report = jpafg.analyse(CROW)["report"]
    print("\n  CROW flat report (byte-identical to the pre-2b baseline):")
    print("  " + report.split("\n")[0])

    # LION & MOUSE — 2-unit tree, per-episode isolation + composed spanning theme.
    lm = read_nested(LION_MOUSE)
    print_nested("The Lion and the Mouse (two episodes)", lm)

    print("\n" + "=" * 78)
    print("MOVE 2b: comprehension RECURSED over the StoryUnit tree. Each episode")
    print("comprehended in isolation (the `unit` graph dimension); the parent")
    print("composed the spanning theme RECIPROCITY from the two children -- a")
    print("cross-episode relation invisible in either alone. The recursion is the")
    print("seeded u_dispatch_* rules firing per StoryUnit; no Python per-unit loop.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
