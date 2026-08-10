"""jabberwock_models_the_child — STANCE-RELATIVE LICENSING + the DECOUPLED
(embedded) reading: the reader MODELS the child's licensed belief WITHOUT
holding it, and the belief-world BOUNDARY is MAINTAINED.

The correction (creator): licensing is RELATIVE TO THE BELIEF-WORLD / STANCE.
The father's 'Beware the Jabberwock, my son!' yields TWO verdicts:

  * DETACHED (the reader's OWN belief-world) — UNLICENSED as objective fact: the
    reader cannot verify the warning, so the danger is UNDETERMINED and the goal
    is HELD OPEN (task 101, unchanged).
  * EMBEDDED-CHILD (the child's nested belief-world) — LICENSED: the child
    TRUSTS the father (a licensed source within the child's world), so 'the
    Jabberwock is dangerous' is established there and the quest to slay it is
    warranted. The child correctly believes the danger, GIVEN its model.

THE CAPABILITY = decoupling MODELING a belief from HOLDING it. The reader MODELS
that the child believes the danger (licensed within the child's world) WHILE NOT
HOLDING the danger itself — its own verdict stays detached. The belief-world
boundary is MAINTAINED: the danger-belief lives ONLY in the child's nested
belief_world (a modeled object indexed to the child), never in the reader's own
belief set. Immersion COLLAPSES that boundary (the child's belief becomes the
reader's); the mature reading MAINTAINS it — and immersion is most readers'
default.

The trust is GRAPH-NATIVE (a TrustLexicon codebook over the addressee vocative +
a `trusts` edge, reusing character_tom's belief_world idiom); the SAME warning
licenses within a trusting world and is held open detached. A source the child
does NOT trust (a foe) licenses nothing even embedded.

donkey = 0 (no LLM), no `import re`, NEVER git.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_models_the_child.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import inference_generation as ig                  # noqa: E402
from domains import reader_response as rr                       # noqa: E402
from domains import character_tom as ctom                       # noqa: E402


JABBERWOCKY = "Beware the Jabberwock, my son! He took his vorpal sword in hand."
UNTRUSTED = "Beware the Jabberwock, my foe! He took his vorpal sword in hand."
CROW = "The crow was thirsty. It found a pitcher."


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


def read(text: str) -> dict:
    agent = _fresh_agent()
    dl.warm_wordnet("en")
    r = ig.read_and_infer(agent, text)
    rr.model_reader_response(agent)
    decoupled = rr.model_decoupled_reading(agent)
    return {"agent": agent, "infer": r, "decoupled": decoupled}


def report() -> dict:
    _hr("JABBERWOCKY — BOTH stances (detached held-open + embedded-child licensed)")
    jw = read(JABBERWOCKY)
    ag = jw["agent"]
    r = jw["infer"]
    print("TEXT:", repr(JABBERWOCKY))

    print("\nDETACHED (the reader's OWN belief-world) — UNLICENSED, held open:")
    print("   warning held_open=%s licensed=%s" %
          (r["warning"][0]["held_open"], r["warning"][0]["licensed"]))
    print("   son.goal (reader's own) =", r["situation_model"].get("son", {}).get("goal"),
          "| OpenGoal nodes:", len(ag.s.nodes("OpenGoal")))
    print("   record:", ag.s.node(ag.s.nodes("OpenGoal")[0])["attrs"]["record"])

    print("\nEMBEDDED-CHILD (the child's nested belief-world) — LICENSED via trust:")
    e = r["embedded"][0]
    print("   trusted source=%s  threat=%r  licensed quest=%r" %
          (e["trusted"], e["threat"], e["remedy"]))
    print("   character_tom.character_belief_world(son):", ctom.character_belief_world(ag, "son"))
    print("   => the child correctly believes the danger GIVEN its model (trusted father).")

    print("\nSTANCE-RELATIVE PROOF — the SAME warning, TWO verdicts:")
    print("   detached: licensed =", r["warning"][0]["licensed"], "(held open)")
    print("   embedded: licensed =", e["licensed_within_world"], "(within the child's world)")

    print("\nDECOUPLING — model the child's belief WITHOUT holding it:")
    print("   reader MODELS child believes danger :", rr.reader_models_child_believes_danger(ag))
    print("   reader HOLDS the danger itself       :", rr.reader_holds_danger(ag))
    print("   reader asserts the heroic quest      :", rr.reader_asserts_heroic_quest(ag))
    dr = rr.decoupled_readings(ag)[0]
    print("   boundary_maintained=%s immersion=%s" % (dr["boundary_maintained"], dr["immersion"]))
    print("   note:", dr["note"])

    _hr("DISCRIMINATIVE — trust is the signal: an UNTRUSTED source licenses nothing")
    un = read(UNTRUSTED)
    ur = un["infer"]
    print("TEXT:", repr(UNTRUSTED))
    print("   detached: held_open =", ur["warning"][0]["held_open"], "(unchanged)")
    print("   embedded: embedded =", ur["embedded"][0]["embedded"],
          "trusted =", ur["embedded"][0]["trusted"])
    print("   reader models child believes danger :", rr.reader_models_child_believes_danger(un["agent"]))
    print("   => the source is not trusted; even embedded the warning licenses NOTHING.")

    _hr("AESOP CROW — a felt need is licensed regardless of stance (byte-identical)")
    cr = read(CROW)
    print("TEXT:", repr(CROW))
    print("   crow state:", cr["infer"]["situation_model"].get("crow"))
    print("   warning:", cr["infer"]["warning"], "embedded:", cr["infer"]["embedded"])
    print("   => thirst -> drink; no stance divergence, nothing modeled or held.")

    return {"jabberwocky": jw, "untrusted": un, "crow": cr}


def verdict() -> None:
    _hr("THE HONEST VERDICT — licensing is relative to the belief-world / stance")
    print(
        "The reader MODELS the child's licensed belief WITHOUT holding it — the\n"
        "belief-world boundary is MAINTAINED, not collapsed:\n"
        "\n"
        "  + STANCE-RELATIVE: 'Beware the Jabberwock, my son!' is UNLICENSED as\n"
        "    objective fact (the detached reader holds the danger OPEN) and LICENSED\n"
        "    within the child's belief-world (the child trusts the father, a licensed\n"
        "    source -> the danger is established there and the quest is warranted).\n"
        "    ONE warning, TWO verdicts — the STANCE decides, not the monster.\n"
        "\n"
        "  + DECOUPLED: the reader knows the child believes the danger (and is CORRECT\n"
        "    to within its own world) WHILE its OWN belief-world holds no such danger.\n"
        "    The child's belief stays a MODELED object, indexed to the child, never\n"
        "    leaking out. Immersion would COLLAPSE that boundary (hold the child's\n"
        "    belief as one's own); the mature reading maintains the nesting.\n"
        "\n"
        "  + DISCRIMINATIVE: a warning from a source the child does NOT trust licenses\n"
        "    nothing even embedded — trust is the graph signal, not a verse rule.\n"
        "\n"
        "  + CROW: a felt need-state (thirst) is licensed regardless of stance —\n"
        "    no divergence, byte-identical.")


def main() -> int:
    report()
    verdict()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
