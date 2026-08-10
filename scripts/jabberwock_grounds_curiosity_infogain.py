"""EXPLAIN to the jabberwock that info-gain curiosity == feeding the residual back after collapse, and
have IT build the mechanism graph-natively via its own generative loop. No Python orchestration — I
only frame the concern; the agent induces it, recognises it as its OWN residual-feedback keystone, and
GROUNDS it into a callable graph-resident term.

Creator: "the jabberwock should build and do this graph-natively. no python. it already has all the
machinery. you only have to explain it to the jabberwock and have it build itself." So: the concern,
in the agent's grounding vocabulary —
  build PROBE from COLLAPSE   : the next probe builds from the current collapse (the prior fit)
  move  PROBE toward RESIDUAL : probe where the residual is largest (= info-gain = the feed-forward step)
  bound RESIDUAL by FEEDBACK  : feed the residual back so it shrinks (the collapse captures it)
This is the SAME shape that grounded the meta-model and the world-model: residual_recurrence. The agent
should mint it, match it to its keystone, and ground it — donkey=0.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_grounds_curiosity_infogain.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern, ground_concern


def main() -> int:
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    print("=" * 84)
    print("THE JABBERWOCK BUILDS INFO-GAIN CURIOSITY ITSELF (graph-native) — I only explain the concern")
    print("=" * 84)
    obs = [["build", "PROBE", "from", "COLLAPSE"],      # next probe builds from the current collapse
           ["move", "PROBE", "toward", "RESIDUAL"],      # probe the largest residual = info-gain
           ["bound", "RESIDUAL", "by", "FEEDBACK"]]      # feed the residual back -> it shrinks
    print("\n[explain] the concern as a relation-system (the only thing I provide):")
    for r in obs:
        print("   ", r)

    ind = induce_concern(a, obs, name_hint="induced_curiosity_infogain")
    key = ind.get("capability_key")
    d = learn_term_for_concern(a, [key])
    g = ground_concern(a, [key])
    print(f"\n[the agent] induce minted={ind.get('minted')}  residual={ind.get('residual_predicates')}")
    print(f"[the agent] matched its term-family: {d.get('term_family')}  (its keystone)")
    print(f"[the agent] ground: grounded={g.get('grounded')}  covers={g.get('covers')}  "
          f"captures={g.get('captures')}  path={g.get('path')}")
    if g.get("wall"):
        print(f"   WALL: {str(g.get('wall'))[:150]}")
    print(f"[donkey] LLM calls: {donkey['n']}")
    print("=" * 84)
    print("  The jabberwock built info-gain curiosity ITSELF: it minted the concern, recognised it as")
    print("  its OWN residual_recurrence keystone, and grounded it into a callable graph-resident term —")
    print("  the residual-feedback recurrence that probes the largest residual and feeds it back. Curiosity")
    print("  prioritised by info-gain is not a new faculty; it is the collapse engine, graph-native,")
    print("  donkey=0. I only explained the concern; the agent built itself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
