"""jabberwock_reads_a_multiarc_story — THROUGHLINES: a PERSISTENT thread woven
through N (3+) arcs of a multi-arc story, one level up from nested_reading's
SPANNING THEME (a single cross-episode relation between TWO units).

The test story is four arcs -- three helping arcs (dog / bird / child) and the
castle PAYOFF arc -- with deliberate throughlines:

  * MIRA, the recurring PROTAGONIST across every arc (kind:character).
  * the help->thank recurring BEAT across arcs 1-3 (kind:pattern).
  * the whistle/feather/lantern gifts PAYING OFF in arc 4 (kind:payoff).
  * the whole-story META-THEME the threads compose into ('kindness returned').

MOVE 2b made the per-arc entity/actor nodes DISTINCT (unit-scoping); the
throughline RE-LINKS them. Each throughline is a CROSS-UNIT COLLAPSE: a token
read mechanically off the children's own UnitAction nodes, decoded against a
ShapeSignatureThroughline codebook -- exactly the nested_reading spanning-theme
collapse, one level up. The recursion + dispatch is the seeded u_dispatch_* rules
firing per StoryUnit inside cognitive_tick; there is NO Python per-unit loop
deciding a throughline.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_a_multiarc_story.py
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
from domains import throughlines as thr

STORY = (
    "Mira left home to seek her fortune. On the road she met a starving dog. "
    "She gave the dog her bread. The dog thanked her and gave her a whistle. "
    "The next day she met a shivering bird. She wrapped the bird in her scarf. "
    "The bird thanked her and gave her a feather. Later she met a lost child. "
    "She led the child home. The family thanked her and gave her a lantern. "
    "At last Mira reached a dark castle. "
    "She blew the whistle, and a pack of dogs came to help her. "
    "She waved the feather, and a flock of birds lit her way. "
    "She raised the lantern, and its light broke the castle spell. "
    "Mira won her fortune, because every kindness she gave had returned to her."
)


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _v(x):
    return x.value if hasattr(x, "value") else x


def main() -> int:
    dl.warm_wordnet("en")
    ag = _fresh()
    out = rd.run_nested_reading_flow(ag, STORY)

    print("=" * 78)
    print("THE MULTI-ARC STORY — 4 arcs, threaded by throughlines")
    print("=" * 78)
    tree = out["tree"]
    print("StoryUnit tree: depth %d, %d arcs" % (out["depth"], len(out["units"])))
    for c in tree["children"]:
        span = "s%d-s%d" % (c["span_start"], c["span_end"])
        print("  ARC %s [%s] opened_by=%s" % (c["node"], span, c["boundary_signal"]))

    print("\nTHROUGHLINES (each a cross-unit collapse, a Throughline node +")
    print("spans_unit edges to each arc it threads):")
    for t in out["throughlines"]:
        print("  [%-9s] %-16s spans arcs %s" % (t["kind"], repr(t["name"]), t["spans"]))
        print("      %s" % t["line"])
    if not any(t["kind"] == "payoff" for t in out["throughlines"]):
        print("  [payoff   ] (none) — the gifts whistle/feather/lantern appear ONLY")
        print("      in the payoff arc: the conjoined gift clause ('...thanked her AND")
        print("      gave her a whistle') drops the gift in arcs 1-3, so no early->late")
        print("      object link forms. Payoff is PARSE-BLIND (an honest partial).")

    print("\nMETA-THEME (composed from the SET of throughlines, minted on the root):")
    mt = out["meta_theme"]
    if mt:
        print("  theme: %r  (token %s, threads %s)" % (mt["theme"], mt["token"], mt["kinds"]))
        print("  %s" % mt["line"])

    # SYNTHETIC PROOF the mechanism is complete: with a payoff throughline present,
    # the SAME compose collapses to 'kindness returned' (CHAR_BEAT_PAYOFF).
    root = next(r for r in ag.s.nodes("StoryUnit")
                if ag.s.node(r)["attrs"].get("kind") == "root")
    thr._mint_throughline(ag, root, "payoff", "whistle", "CAUSAL_PAYOFF",
                          "synthetic payoff (proof the loop closes)", [_v(root)])
    for m in list(ag.s.nodes("MetaTheme")):
        ag.inner.remove_node(m)
    proof = thr.compose_meta_theme(ag, root)
    print("\n  [synthetic] add a payoff throughline -> meta-theme recomposes to %r"
          % proof["theme"])

    print("\n" + "=" * 78)
    print("A THROUGHLINE is one level up from the spanning theme: not a single")
    print("cross-episode relation between two units, but a PERSISTENT thread woven")
    print("through N arcs. MIRA threads all four; the help->thank beat threads three;")
    print("the payoff would thread the gifts if the parser kept them. The threads")
    print("compose into the whole-story theme. NO Python per-unit loop decides any of")
    print("it — every throughline is a ShapeDecode verdict over the arcs' own nodes.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
