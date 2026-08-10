"""jabberwock_sense — the SENSE OF HUMOUR + REFERENCES, driven live on the booted jabberwock.

Demonstrates the capstone of the four-build arc (wordplay + interlocutor model + order-N context ->
a SENSE: salience + taste + timing over them):

  * the manifold-conditioned MINIMAL PAIR — "would you kindly" is a BioShock allusion from a gamer,
    a plain courtesy from Cornelius Vane (1885). Same string, opposite call, decided by the manifold;
  * the ALLUSION -> CONCEPT gradient — "down the rabbit hole" lands in every manifold (graduated);
  * UNINTENTIONAL firing — no "from bioshock" flag needed; live-in-manifold is the sole criterion;
  * DEPLOY IS CHOSEN — the jabberwock references for a knowing overhearer over the addressee's head;
  * OWN NAME — it recognizes "Jabberwock" as an allusion to Carroll, the deepest reference;
  * HUMOUR — a benign incongruity recognized and answered IN KIND, not literally.

donkey=0 (no teacher call). Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_sense.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.sense_of_reference as sr


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def _prime(agent, turns):
    """Accumulate an interlocutor's manifold over several turns (the homework — the prior sharpens)."""
    for t in turns:
        agent.converse(t, "statement")


GAMER_TURNS = ["I love BioShock and the city of Rapture.",
               "The respawn mechanics in that playthrough were brutal.",
               "I main a controller for those boss fights."]
VANE_TURNS = ["Good evening. I am Cornelius Vane, and I should like to discuss ethics.",
              "Virtue is the disposition toward excellence, kindly weighed.",
              "Morality requires that we examine consequences carefully."]


def main() -> None:
    print("=" * 78)
    print("SENSE OF REFERENCES — the manifold-conditioned minimal pair")
    print("=" * 78)

    ga = _agent()
    _prime(ga, GAMER_TURNS)
    print("\n[gamer manifold]  \"Would you kindly open the door?\"")
    print("  ->", ga.converse("Would you kindly open the door?", "question"))

    va = _agent()
    _prime(va, VANE_TURNS)
    print("\n[Vane, 1885]      \"Would you kindly open the door?\"")
    print("  ->", va.converse("Would you kindly open the door?", "question"))

    print("\n" + "=" * 78)
    print("GRADED / GRADUATION — a concept lands in every manifold")
    print("=" * 78)
    print("[Vane]  \"We went down the rabbit hole on this problem.\"")
    print("  ->", va.converse("We went down the rabbit hole on this problem.", "statement"))

    print("\n" + "=" * 78)
    print("DEPLOY IS A CHOSEN ACT — an easter egg over the addressee's head")
    print("=" * 78)
    gamer_snap = ga._interlocutor_snapshot()
    vane_snap = va._interlocutor_snapshot()
    d = sr.deploy_reference("would you kindly", addressee=vane_snap, overhearers=[gamer_snap])
    print(f"  addressee={vane_snap['id']}  overhearer={gamer_snap['id']}")
    print(f"  choice -> target={d['target']}  explain={d['explain']}  ({d['note']})")

    print("\n" + "=" * 78)
    print("OWN NAME — the deepest reference")
    print("=" * 78)
    print("  \"Are you the Jabberwock?\"")
    print("  ->", ga.converse("Are you the Jabberwock?", "question"))

    print("\n" + "=" * 78)
    print("SENSE OF HUMOUR — a benign incongruity, answered in kind")
    print("=" * 78)
    print("  \"I asked the compiler for relationship advice.\"")
    print("  ->", ga.converse("I asked the compiler for relationship advice.", "statement"))

    print(f"\n[donkey audit] teacher calls (gamer)={ga._donkey['n']}  (vane)={va._donkey['n']}")


if __name__ == "__main__":
    main()
