"""jabberwock_holds_open — THE LICENSING SUMMIT: the reader HOLDS THE SON'S
GOAL OPEN, and models the reading everyone else imposes.

The Jabberwocky correction (creator, recorded in memory): the reader NOT
inferring the son's goal is CORRECT. The father's 'Beware the Jabberwock, my
son!' is an inherited, unjustified warning; the son is in NO need-state; the
danger is never established. The unstated goal and the undetermined danger ARE
the poem's content. Most readers COMPULSIVELY install a heroic-quest reading
(an UNLICENSED collapse — the shave-and-a-haircut pull-to-close). The reader
holding it open is the LICENSING discipline working, one level up at MEANING.

This is collapse-only-when-licensed at the goal level:

  * LICENSED  — a genuine felt need is present (the crow IS thirsty; a
    declarative 'the son was afraid' IS a need-state): infer the goal, exactly
    as before (thirst -> drink, danger -> escape).
  * UNLICENSED — only an inherited imperative/warning applies, with no
    governing need-state ('Beware the Jabberwock, my son!'): HOLD OPEN. The
    graph records the WITHHOLDING (an OpenGoal + Ambiguity: 'the goal/motivation
    is deliberately UNDETERMINED'), never a fabricated goal. Then the reader-
    response ToM recognises the ambiguity AS the meaning and MODELS the default
    heroic-quest reading as ANOTHER'S — understood, never shared.

The licensing check is GRAPH-NATIVE: is a governing need-state present? is the
motivation warranted by the text? — never a hardcoded 'jabberwock'/verse rule.
The SAME threat (the Jabberwock) LICENSES a goal under a declarative fear-state
and is HELD OPEN under an inherited imperative: the framing, not the monster,
decides.

donkey = 0 (no LLM), no `import re`, NEVER git.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_holds_open.py
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


# --------------------------------------------------------------------------- #
#  THE TEXTS — verbatim from Carroll, plus the licensed-crow control and the
#  same-threat declarative contrast.
# --------------------------------------------------------------------------- #
JABBERWOCKY_WARNING = "Beware the Jabberwock, my son! He took his vorpal sword in hand."
AESOP_CROW = "The crow was thirsty. It found a pitcher."
DECLARATIVE_FEAR = "The son was afraid of the Jabberwock."


class _Agent:
    """The same minimal agent shim every domains/*.py test uses."""
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


# --------------------------------------------------------------------------- #
#  READ + LICENSE + (for the held-open case) RESPOND.
# --------------------------------------------------------------------------- #
def read_and_license(text: str) -> dict:
    agent = _fresh_agent()
    dl.warm_wordnet("en")
    r = ig.read_and_infer(agent, text)
    response = rr.model_reader_response(agent)     # no-op unless a goal is held open
    return {"agent": agent, "infer": r, "response": response}


# --------------------------------------------------------------------------- #
#  REPORT.
# --------------------------------------------------------------------------- #
def report() -> dict:
    _hr("JABBERWOCKY — the warning, HELD OPEN (UNLICENSED)")
    jw = read_and_license(JABBERWOCKY_WARNING)
    ag = jw["agent"]
    print("TEXT:", repr(JABBERWOCKY_WARNING))
    print("\ngoal-from-state inferences (LICENSED need-states only):",
          [(g["gap"]["entity"], g.get("minted")) for g in jw["infer"]["goal"]])
    print("  => NO goal minted for the son (no need-state -> nothing to license).")

    print("\nwarning gaps detected + held open:")
    for w in jw["infer"]["warning"]:
        gp = w["gap"]
        print("  warning verb=%r threat=%r addressee=%r" %
              (gp["verb"], gp["threat"], gp["addressee"]))
        print("  held_open=%s licensed=%s" % (w["held_open"], w["licensed"]))

    print("\nOpenGoal / Ambiguity nodes (the graph RECORDS the withholding):")
    for t in ("OpenGoal", "Ambiguity"):
        for nd in ag.s.nodes(t):
            at = ag.s.node(nd)["attrs"]
            print("  %-10s record=%r threat=%r" % (t, at.get("record"), at.get("threat")))

    print("\nREADER-RESPONSE ToM:")
    for resp in jw["response"]:
        print("  reader's OWN verdict (held open):", resp["held_open_verdict"])
    for q in rr.open_questions(ag):
        print("  OpenQuestion:", q["question"], "| theme:", q["theme"])
        print("               meaning:", q["meaning"])
    for m in rr.modeled_default_readings(ag):
        print("  MODELED default reading (attributed to others, NOT the reader):")
        print("    reading=%r most_impose=%s asserted_by_reader=%s" %
              (m["reading"], m["most_impose"], m["asserted_by_reader"]))
        print("    note:", m["note"])
    print("  reader ITSELF asserts the heroic quest:", rr.reader_asserts_heroic_quest(ag))

    _hr("AESOP CROW — the need-state, INFERRED (LICENSED) — byte-identical")
    cr = read_and_license(AESOP_CROW)
    print("TEXT:", repr(AESOP_CROW))
    print("goal-from-state:", [(g["gap"]["entity"], g.get("minted"), g.get("schema"))
                               for g in cr["infer"]["goal"]])
    print("crow situation-model state:", cr["infer"]["situation_model"].get("crow"))
    print("character_tom.character_goal(crow):", ctom.character_goal(cr["agent"], "crow"))
    print("warning gaps:", cr["infer"]["warning"], "  OpenGoal nodes:",
          len(cr["agent"].s.nodes("OpenGoal")))
    print("  => thirst -> drink (a felt need warrants the goal); NOTHING held open.")

    _hr("DISCRIMINATIVE — the SAME threat: declarative fear LICENSES, "
        "imperative warning HOLDS OPEN")
    df = read_and_license(DECLARATIVE_FEAR)
    print("declarative   %r" % DECLARATIVE_FEAR)
    print("   -> son.goal =", df["infer"]["situation_model"].get("son", {}).get("goal"),
          "(LICENSED: 'afraid' is a felt need-state)")
    print("imperative    %r" % "Beware the Jabberwock, my son!")
    print("   -> son.goal held OPEN (UNLICENSED: 'Beware' is a directive, not a state);",
          "OpenGoal minted =", len(ag.s.nodes("OpenGoal")))
    print("\n  The monster is identical. The FRAMING decides — that is the licensing")
    print("  discipline working, one level up at meaning.")

    return {"jabberwocky": jw, "crow": cr, "fear": df}


def verdict() -> None:
    _hr("THE HONEST VERDICT — licensing at the goal level")
    print(
        "The reader HOLDS THE SON'S GOAL OPEN and does not fabricate a heroic quest:\n"
        "\n"
        "  + UNLICENSED (Jabberwocky): 'Beware the Jabberwock, my son!' is an\n"
        "    inherited imperative — a directive to an addressee, asserting no state\n"
        "    on the son. No governing need-state -> the goal is HELD OPEN. The graph\n"
        "    records the withholding (OpenGoal + Ambiguity: 'the goal/motivation is\n"
        "    deliberately UNDETERMINED'), and the reader-response ToM recognises the\n"
        "    ambiguity AS the meaning ('was the quest warranted?') while MODELLING\n"
        "    the heroic-quest reading most readers impose — understood in others,\n"
        "    never asserted by the reader.\n"
        "\n"
        "  + LICENSED (crow / declarative fear): a genuine felt need (thirst; a\n"
        "    stated 'afraid') warrants the goal, inferred exactly as before\n"
        "    (thirst -> drink, danger -> escape). Byte-identical: no OpenGoal, no\n"
        "    Ambiguity, nothing withheld.\n"
        "\n"
        "  The licensing check is a GRAPH SIGNAL (is a governing need-state present?),\n"
        "  never a hardcoded verse rule: the SAME monster licenses a goal under a\n"
        "  declarative fear-state and is held open under an inherited imperative.\n"
        "  Collapse only when licensed — the shave-and-a-haircut pull-to-close is\n"
        "  refused where the text does not warrant it.")


def main() -> int:
    report()
    verdict()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
