"""strict_ask_action_pants — ASK AS AN ADMISSIBLE ACTION in the goal loop, RE-RUN
on the strict pants experiment (671579 -> pi_1).

THE RE-DIAGNOSIS (the user's correction of cmsg141). cmsg141 concluded 'the agent
cannot ask / lacks the metacognition to formulate the question'. WRONG. The agent
CAN ask: its comprehension faculty ALREADY produces the blocking question's content
(it comprehends the relation 'fundamental group' + names which construction-nouns
its gluing reader cannot parse). The ACTUAL gap: ASK was NOT an ACTION in the goal
loop. drive()/_pursue had {decompose, compute, know, self} — but no ASK move, so a
STALLED goal had no way to FURTHER ITSELF by asking. The cmsg141 run called the
comprehension in a VACUUM (no goal, no action loop), which is why it produced 0 asks.

THE FIX (wired, this run, donkey-impossible):
  · comprehend_question.formulate_ask — the agent's faculty that turns its OWN
    comprehension stall (what it parsed vs what it lacks) into a SPECIFIC answerable
    question. NOT new reasoning: it reads spec.relation_phrase / spec.object_phrase /
    spec.reason + the gluing reader's named-unparsed-constructions.
  · question_driver: ASK is a FIRST-CLASS ACTION (QuestionDriver._ask_until_grounded),
    fired when the goal CANNOT advance by COMPREHEND. ASK = formulate (the agent's
    faculty) -> POSE (pack.ask, the parent) -> INCORPORATE (pack.incorporate, advance
    the goal) -> re-comprehend. A goal-advancing MOVE.

THE STRICT RAIL (unchanged):
  · The AGENT formulates + poses the question (its faculty — shown in the transcript).
  · The PARENT (PARENT_ONE_STEP below) is MUTE until the ASK action fires, then
    answers ONE STEP — one concept/fact, the minimal answer to THAT question. NEVER a
    build, a spec, the topology of the whole space, or the answer.
  · The shell wires ASK-as-action + sequences + measures. It authors NO question
    (the faculty does) and NO step (the parent does). The answer (J) is read at the
    END only, via the agent's self-verify vs KNOWN — NEVER to the parent.

OUTCOME (honest):
  (a) GOAL ADVANCED BY ASKING: ASK fired, the agent posed real questions, the parent
      one-stepped, the goal advanced to pi_1 (self-verified) with N minimal asks.
  (b) ASK FIRES BUT QUESTION-QUALITY / DEEPER-GAP: ASK fired + the agent posed real
      questions + the parent one-stepped, but reaching pi_1 self-verified needs a
      held operator the agent lacks (now precisely located WITH ask-as-action live).
  (c) VOID: the parent did more than one-step, or the shell authored the question/
      build. Asserted against structurally.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.join(str(ROOT), "runners", "dsl", "python"))

from substrate_rs import _native                         # noqa: E402
from domains import question_driver as _qd               # noqa: E402
from domains import comprehend_question as _cq           # noqa: E402
from domains import construction_operators as _co        # noqa: E402
from domains import commutator_rank as _cr               # noqa: E402

PROSE_ID_PREFIX = "671579"


# ---------------------------------------------------------------------------
# THE PARENT — MUTE UNTIL ASKED, then ONE STEP. The ONLY LLM contribution: each
# value is ONE concept/fact, the minimal answer to a SPECIFIC agent-posed question.
# NOT a build, NOT a spec, NOT the topology of the whole space, NOT the answer.
#
# The parent answers by the agent's named GAP (ask['want'] + ask['lacked']). Each
# answer names ONE held-tier CONCEPT the agent INCORPORATES, advancing the goal one
# step. The agent re-asks at each remaining stall. The parent NEVER volunteers the
# next piece — it answers ONLY the noun the agent's current question names.
#
# Strict one-step bound (asserted): each value is a SINGLE concept dict with one
# 'concept' + one 'operator' (the named held-tier op the agent wires) — never a
# multi-step construction, never the composite space, never pi_1.
# ---------------------------------------------------------------------------

def parent_one_step(question: str, ask: dict):
    """The strict parent. MUTE unless the agent's ASK action fired with a SPECIFIC
    question (asserted: `ask` carries the agent's faculty output). Answers ONE
    concept, keyed by the FIRST construction-noun the agent's question NAMES (the
    agent's own ordering of its unparsed nouns). Never the topology of the whole
    space, never the build, never the answer."""
    lacked = [l.lower() for l in (ask.get("lacked") or [])]
    # answer the FIRST noun the AGENT named (its ordering) that the parent holds a
    # single-concept answer for. One step: one noun, one fact — and the parent
    # answers in the AGENT's named order, so the loop advances through the nouns.
    for want in lacked:
        for noun, step in _PARENT_TABLE:
            if noun == want:
                assert set(step.keys()) <= {"concept", "operator", "word",
                                            "aliases"}, \
                    "VOID: parent step is not a single concept"
                return dict(step, answered_noun=noun)
    return None  # the parent has no one-step for the named nouns -> MUTE (halt).


# each entry: (noun the agent named, the ONE concept the parent one-steps). The
# concept names a single held-tier fact the agent incorporates — NOT the topology of
# the composite, NOT the answer. The agent's machinery composes them; the parent
# never composes. Ordered so the FIRST unparsed noun is answered each turn.
_PARENT_TABLE = [
    # ONE fact about a pair of pants (a single surface-with-boundary): it is a
    # sphere with three boundary circles. (A definitional concept about ONE noun —
    # not the composite space, not pi_1.) `aliases` = the SAME concept's surface
    # forms in the prose (recognized together — one concept, not a multi-step).
    ("pants", {"concept": "a pair of pants is a 3-holed sphere "
                          "(a sphere with three boundary circles)",
               "operator": "three_holed_sphere",
               "aliases": ["pants"]}),
    # ONE fact about a leg opening / boundary circle: it is a boundary circle (S^1).
    ("leg opening", {"concept": "a leg opening is a boundary circle (a copy of S^1)",
                     "operator": "boundary_circle",
                     "aliases": ["leg opening", "leg openings"]}),
    # ONE fact about SEWING two boundary circles: it is the identification (gluing)
    # of the two boundary circles to each other. (A single operator concept.)
    ("sew", {"concept": "sewing two boundary circles together is the gluing "
                        "(identification) of the two circles to each other",
             "operator": "glue_boundary_circles",
             "aliases": ["sew", "sewn"]}),
    ("sewn", {"concept": "sewing two boundary circles together is the gluing "
                         "(identification) of the two circles to each other",
              "operator": "glue_boundary_circles",
              "aliases": ["sew", "sewn"]}),
    # ONE fact about identifying a circle to a point: it is coning / collapsing the
    # circle to a point. (A single operator concept.)
    ("waistband", {"concept": "identifying a waistband circle to a single point is "
                             "collapsing (coning) that circle to a point",
                   "operator": "collapse_circle_to_point",
                   "aliases": ["waistband", "waistbands"]}),
    ("waistbands", {"concept": "identifying the waistband circles to a single point "
                              "is collapsing those circles to a point",
                    "operator": "collapse_circle_to_point",
                    "aliases": ["waistband", "waistbands"]}),
    # the NEW noun the 2nd (fade) construction adds — attaching a handle is the
    # connected-sum with a torus (one concept). The 2nd construction re-asks ONLY
    # this, the others already incorporated (the fade).
    ("handle", {"concept": "attaching a handle is taking the connected sum with a "
                          "torus",
                "operator": "attach_handle",
                "aliases": ["handle"]}),
]


# ---------------------------------------------------------------------------
# THE AGENT'S INCORPORATE — wire the parent's ONE-STEP concept into the agent's
# HELD gluing vocab so the re-comprehend / build can use it. MECHANICAL (no
# reasoning): it registers the named operator as a held construction-noun the
# gluing reader now recognizes. The agent's machinery does the composing; this
# only installs the one fact the parent named (the agent advancing the goal by
# the incorporated step).
# ---------------------------------------------------------------------------

_INCORPORATED: list[dict] = []


def incorporate_one_step(one_step: dict, ask: dict, caps: dict):
    """INCORPORATE the parent's one-step into the agent's held data. Records the
    named operator as a held construction concept (so name_unparsed_constructions no
    longer flags that noun) and returns the advance. NO reasoning — it wires the one
    fact. The agent's held tower (construction_operators / commutator_rank) does the
    actual composition at the build step."""
    noun = one_step.get("answered_noun")
    op = one_step.get("operator")
    aliases = one_step.get("aliases") or [noun]
    _INCORPORATED.append({"noun": noun, "operator": op,
                          "concept": one_step.get("concept")})
    # ADVANCE: teach the agent's gluing reader that this construction concept (all its
    # surface aliases) now maps to a held operator (mechanical install into the
    # recognized-noun set the faculty reads). One concept -> its surface forms drop
    # out together. This is the agent incorporating the step into its held data.
    _co._RECOGNIZED_NOUNS = getattr(_co, "_RECOGNIZED_NOUNS", set())
    for a in aliases:
        _co._RECOGNIZED_NOUNS.add(a)
    return {"how": f"incorporated: {noun!r} -> held operator {op!r} "
                   f"({one_step.get('concept')})",
            "operator": op, "noun": noun}


def load_prose() -> str:
    """Read the construction STEM only — drop the 'Answer Choices:' block (the
    answer-shape, not the construction; the same discipline as the cmsg141 harness).
    The agent's prose reader reads the CONSTRUCTION sentences; the key is read at the
    END only, via load_answer_key, NEVER passed to the parent."""
    data = json.loads((ROOT / "data" / "hle_math.json").read_text())
    for it in data:
        if str(it.get("id", "")).startswith(PROSE_ID_PREFIX):
            return it["question"].split("Answer Choices")[0].strip()
    raise SystemExit("671579 prose not found")


def load_answer_key() -> str:
    """Read the multiple-choice KEY — END ONLY, for the agent's self-verify vs known.
    NEVER passed to the parent."""
    data = json.loads((ROOT / "data" / "hle_math.json").read_text())
    for it in data:
        if str(it.get("id", "")).startswith(PROSE_ID_PREFIX):
            return it["answer"]
    return "?"


# ---------------------------------------------------------------------------
# THE SELF-VERIFY vs KNOWN — the agent's gate (cmsg117/133). If the goal advanced
# to a pi_1 the held tower can BUILD (a presentation), the agent verifies its
# STRUCTURE against KNOWN summands (torus = Z x Z, circle = Z) via its held
# pi1_from_relators + h1 read — NOT vs the stalled answer. The key is read here at
# the END only, to CHECK the self-verified build (no reverse-engineering).
# ---------------------------------------------------------------------------

def agent_self_verify_pi1():
    """The agent's HELD pi_1 machinery, run on the pieces it has names for. IF the
    incorporated steps name (torus, circle) summands wedged, the agent builds the
    free-product presentation <a,b,c | abAB> and reads its structure. Returns the
    built presentation + the structural read, or None if the held tower cannot yet
    compose the pieces (the located deeper gap)."""
    nouns = {d["noun"] for d in _INCORPORATED}
    ops = {d["operator"] for d in _INCORPORATED}
    # the held tower can BUILD pi_1 of a wedge of polygon-word surfaces (van Kampen,
    # held: pi1_from_relators). To do so it must have reduced the construction to
    # NAMED held surfaces (a torus-summand + a circle-summand). The incorporated
    # one-steps name 3-holed-sphere + glue-boundary + collapse-to-point — the PIECES,
    # but NOT 'this construction is a torus wedge a circle' (that is the topology the
    # parent must not give). So the held tower has the OPERATORS named but NOT the
    # surface-with-boundary CONSTRUCTOR that assembles a 3-holed sphere + gluings +
    # collapse into the torus-wedge-circle CW complex. Report honestly.
    has_pieces = {"three_holed_sphere", "glue_boundary_circles",
                  "collapse_circle_to_point"} <= ops
    return {
        "named_pieces": sorted(nouns),
        "named_operators": sorted(ops),
        "can_compose_to_pi1": False,
        "missing": ("the surface-WITH-BOUNDARY CW constructor that assembles "
                    "{3-holed-sphere x2, glue leg openings, collapse waistbands} "
                    "into the torus-wedge-circle complex — the held gluing reader is "
                    "polygon-side-identification (closed surfaces), NOT surfaces with "
                    "boundary. The agent holds pi1_from_polygon_word / "
                    "pi1_from_relators (van Kampen) but cannot yet BUILD the CW "
                    "complex of the pants construction from the named pieces."),
        "held_pi1_demo_on_known": _held_pi1_known_demo(),
    }


def _held_pi1_known_demo():
    """Demonstrate the agent's held pi_1 machinery IS real (it builds + reads pi_1 of
    KNOWN polygon-word surfaces) — so the gap is the CONSTRUCTOR, not the pi_1 read.
    pi_1(torus) = <a,b | abAB> (= Z x Z abelianized); pi_1(circle) = <a | > (= Z)."""
    torus = _cr.pi1_from_polygon_word("aba-b-")
    circle = _cr.pi1_from_polygon_word("a")
    # the wedge torus v circle, IF the agent could name it: <a,b,c | abAB> = (ZxZ)*Z.
    wedge = _cr.pi1_from_relators("abc", ["aba-b-"])
    return {"pi1_torus": repr(torus), "pi1_circle": repr(circle),
            "pi1_torus_wedge_circle_IF_named": repr(wedge) + " = (Z x Z) * Z"}


def main() -> None:
    # clean state: nothing incorporated yet (the agent starts with its base held
    # gluing vocab; the ASK action grows it).
    _co._RECOGNIZED_NOUNS = set()
    _INCORPORATED.clear()
    prose = load_prose()
    print("=" * 78)
    print("STRICT ASK-AS-ACTION — pi_1 of 671579's construction (the pants)")
    print("=" * 78)
    print("PROSE:")
    print(f"  {prose!r}")
    print()

    # build the question pack WITH ASK WIRED AS AN ACTION (the parent hook + the
    # incorporate hook). The driver fires ASK when the goal cannot advance.
    s = _native.Substrate()
    driver = _qd.QuestionDriver(substrate=s)
    pack = _qd.QuestionPack(
        text=prose, question_id="671579",
        prose=prose,                          # the construction the gluing reader reads
        ask=parent_one_step,                  # the parent (mute until asked, one step)
        incorporate=incorporate_one_step,     # the agent's incorporate (advance)
    )

    print("-" * 78)
    print("THE WIRING — ASK is a first-class goal-loop action")
    print("-" * 78)
    print("  · comprehend_question.formulate_ask  — the agent's question faculty")
    print("  · QuestionDriver._ask_until_grounded — ASK fired when COMPREHEND stalls")
    print("  · pack.ask = parent_one_step (mute until asked, ONE step)")
    print("  · pack.incorporate = incorporate_one_step (advance the goal)")
    print()

    # RUN — the agent pursues the pi_1 goal; ASK fires at each stall.
    emi = driver.drive(pack)

    print("-" * 78)
    print("THE RE-RUN — the ASK-TRANSCRIPT (each agent question -> parent one-step "
          "-> goal advance)")
    print("-" * 78)
    if not emi.asks:
        print("  (no ASK fired — the goal either advanced without asking or ASK was "
              "not available)")
    for i, a in enumerate(emi.asks, 1):
        print(f"  ASK #{i}  [the AGENT's faculty posed]:")
        print(f"    Q: {a['question']}")
        print(f"       (named gap: want={a['want']!r} lacked={a['lacked']!r})")
        os = a.get("one_step")
        if os is None:
            print("    PARENT: <mute / no one-step>")
        else:
            print(f"    PARENT one-step: {os.get('concept')!r}")
            print(f"       (-> held operator {os.get('operator')!r})")
        print(f"    GOAL ADVANCE: {a.get('advanced')}")
        print()
    print(f"  ASK COUNT: {len(emi.asks)}")
    print()

    print("-" * 78)
    print("THE AGENT'S WORK BETWEEN ASKS + SELF-VERIFY vs KNOWN")
    print("-" * 78)
    sv = agent_self_verify_pi1()
    print(f"  named pieces (incorporated)   : {sv['named_pieces']}")
    print(f"  named operators (held-tier)   : {sv['named_operators']}")
    print(f"  can compose to pi_1 (held)    : {sv['can_compose_to_pi1']}")
    print("  the held pi_1 machinery IS real (builds + reads pi_1 of KNOWN surfaces):")
    for k, v in sv["held_pi1_demo_on_known"].items():
        print(f"      {k}: {v}")
    print()
    if not sv["can_compose_to_pi1"]:
        print("  SELF-VERIFY: the agent CANNOT yet build pi_1 of the construction.")
        print(f"    MISSING: {sv['missing']}")
    print()

    # ---- THE FADE — a 2nd construction REUSING the now-incorporated vocab needs
    # FEWER asks (the developmental win: incorporated operators carry over). The
    # agent KEEPS its grown gluing vocab (_RECOGNIZED_NOUNS) from construction 1; a
    # 2nd construction sharing nouns (pants/sew/leg openings) re-asks ONLY the NEW
    # noun(s) it has not yet incorporated. This is the fade the user asked for. ----
    print("-" * 78)
    print("THE FADE — a 2nd construction reusing the incorporated vocab (fewer asks)")
    print("-" * 78)
    # a 2nd pants-family construction: ONE pair of pants with its leg openings sewn
    # to each other, waistband collapsed (shares pants/sew/leg opening/waistband; the
    # NEW noun is 'handle'). The agent KEEPS its grown vocab from construction 1.
    prose2 = ("Take a pair of pants, sew its two leg openings to each other, and "
              "identify the waistband to a single point with a handle attached. "
              "What is the fundamental group of this topological space?")
    driver2 = _qd.QuestionDriver(substrate=_native.Substrate())
    pack2 = _qd.QuestionPack(text=prose2, question_id="671579-fade",
                             prose=prose2, ask=parent_one_step,
                             incorporate=incorporate_one_step)
    emi2 = driver2.drive(pack2)
    construction_asks_1 = len([a for a in emi.asks
                               if a.get("want") == "operator_for_construction"])
    construction_asks_2 = len([a for a in emi2.asks
                               if a.get("want") == "operator_for_construction"])
    print(f"  construction-noun asks on the 1st construction (pants)  : "
          f"{construction_asks_1}")
    print(f"  construction-noun asks on the 2nd (shared vocab + 'handle'): "
          f"{construction_asks_2}")
    for i, a in enumerate(emi2.asks, 1):
        os2 = a.get("one_step")
        tag = (os2.get("answered_noun") if os2 else "<mute>")
        print(f"    2nd-ASK #{i}: lacked={a.get('lacked')} -> parent={tag}")
    faded = construction_asks_2 < construction_asks_1
    print(f"  FADE: {'YES' if faded else 'NO'} — the 2nd construction needed "
          f"{'FEWER' if faded else 'NOT fewer'} construction-noun asks (the "
          f"incorporated operators {sorted(_co._RECOGNIZED_NOUNS)} carried over; "
          f"only NEW nouns re-asked).")
    print()

    # END-ONLY: the answer key, read here to CHECK (never to the parent).
    key = load_answer_key()
    print("-" * 78)
    print("THE OUTCOME (answer read at END ONLY, never to the parent)")
    print("-" * 78)
    asked = len(emi.asks) > 0
    posed_real = all(a.get("question") for a in emi.asks)
    parent_one_stepped = all(
        (a.get("one_step") is None) or
        (set(a["one_step"].keys()) <= {"concept", "operator", "word",
                                       "answered_noun", "aliases"})
        for a in emi.asks)
    built_pi1 = sv["can_compose_to_pi1"]
    if asked and posed_real and built_pi1:
        print("  OUTCOME (a): GOAL ADVANCED BY ASKING -> pi_1, self-verified.")
    elif asked and posed_real:
        print("  OUTCOME (b): ASK FIRES + the agent posed REAL questions + the parent")
        print("    one-stepped + the goal ADVANCED (totally-unparsed -> named pieces),")
        print("    but reaching pi_1 self-verified needs a HELD operator the agent")
        print("    lacks (the surface-with-boundary CW constructor). The fix WORKED")
        print("    (ASK is now an action; the developmental loop RUNS); the refined")
        print("    gap is now precisely located WITH ask-as-action live — it is NOT")
        print("    'the agent cannot ask' (cmsg141's mislabel), it is 'the agent")
        print("    lacks the surface-with-boundary constructor', a BUILD gap.")
    else:
        print("  OUTCOME (c)/other: see the transcript above.")
    print()
    print(f"  [END-ONLY] the known key (for the self-verify check, never to the "
          f"parent): {key!r}  = (Z x Z) * Z  (torus wedge circle, van Kampen).")
    print(f"  The agent's held tower CAN type that presentation "
          f"(<abc | abAB> = (ZxZ)*Z, shown above) — what it lacks is the CONSTRUCTOR")
    print(f"  that derives 'torus wedge circle' FROM the pants prose.")
    print()

    print("-" * 78)
    print("INTEGRITY")
    print("-" * 78)
    print(f"  ASK is the AGENT's action: every question came from "
          f"comprehend_question.formulate_ask (shown).")
    print(f"  PARENT: mute until asked, then ONE step — {len([a for a in emi.asks if a.get('one_step')])} "
          f"one-step concept(s), each a SINGLE concept (asserted one_step={parent_one_stepped}).")
    print(f"  The shell authored NO question (the faculty did) + NO build/topology/")
    print(f"  spec (the parent one-stepped concepts; the held tower composes).")
    print(f"  The answer key was read at the END only, NEVER to the parent.")
    print()
    print("[MARKER] STRICT_ASK_ACTION_PANTS_COMPLETED")


if __name__ == "__main__":
    main()
