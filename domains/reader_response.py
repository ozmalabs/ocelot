"""reader_response — READER-RESPONSE THEORY OF MIND: DECOUPLE modeling a
belief from HOLDING it, over a held-open goal.

The Jabberwocky correction, REFINED (creator): the heroic-quest reading is NOT
a compulsion this module should merely model as 'others' error' — and it is NOT
something the mature reader ADOPTS as its own frame either (that is IMMERSION,
the failure). The correct reading is DECOUPLED. The reader MODELS that the
CHILD believes the Jabberwock is dangerous — and is CORRECT to WITHIN the
child's belief-world: the child trusts the father, a LICENSED source inside the
child's world, so the danger is established there and the quest is warranted
(inference_generation.resolve_warning_embedded mints this as the child's NESTED
belief-world). SIMULTANEOUSLY the reader does NOT HOLD that belief itself — its
OWN belief-world does not contain 'the Jabberwock is dangerous'; its own verdict
stays detached, undetermined, held open (inference_generation.resolve_warning_
gap, UNCHANGED — task 101).

THE CAPABILITY = decoupling MODELING-a-belief from HOLDING-a-belief; the
achievement is the MAINTAINED belief-world BOUNDARY. Immersion COLLAPSES that
boundary (the child's licensed belief becomes the reader's own); the mature
reading MAINTAINS it (the child's belief stays a MODELED object, indexed to the
child by `belief_holder`, never leaking into the reader's own belief set). Most
readers CONFLATE modeling with holding (immersion is the default); even a reader
WITH the decoupling capability often does not engage it.

inference_generation does the belief-world layer:
  · resolve_warning_gap  -> the reader's OWN verdict: OpenGoal + Ambiguity
    'the goal/motivation is deliberately UNDETERMINED' (danger not held).
  · resolve_warning_embedded -> the CHILD's licensed belief: a NESTED
    `belief_world` danger-belief (character_tom idiom), indexed to the child,
    licensed via `trusts(child, source)`.

This module records the DECOUPLING itself:

  1. THE AMBIGUITY IS THE MEANING (reader's OWN verdict). For each held-open
     OpenGoal, mint an `OpenQuestion` ('was the quest warranted?') whose theme
     is the undetermined danger — the reader recognises the WITHHOLDING itself.

  2. MODEL WITHOUT HOLDING (legacy `ModeledReading`, retained for task 101). A
     `ReaderModel` (a modeled OTHER mind — character_tom's nested belief-world
     idiom) carries the heroic-quest reading in its belief-world, flagged
     `most_impose=1` / `asserted_by_reader=0`: the IMMERSIVE reader who HOLDS
     the heroic reading, modeled by the agent WITHOUT sharing it.

  3. THE DECOUPLED READING (the correction, `model_decoupled_reading`). Mint a
     `DecoupledReading` that pins BOTH facts against ONE held-open goal: the
     reader MODELS 'the child believes the danger, LICENSED within the child's
     world' (`models_child_believes_danger=1`, pointing at the child's nested
     belief node) AND does NOT HOLD it (`reader_holds_danger=0`; its own verdict
     is the detached OpenGoal). `boundary_maintained=1`, `immersion=0`. The two
     facts are DISTINCT and the nesting is maintained — the reader's achievement.

ARCHITECTURE (CLAUDE.md). Every node here is graph-resident (OpenQuestion /
ReaderModel / ModeledReading / DecoupledReading / ImposedReadingSchema); the
modeled-other / nested-belief idiom (belief_world edge from a modeled holder) is
character_tom's, reused; this module makes no agent decision — it reads the
held-open OpenGoal and the child's nested belief off the graph and records the
decoupling the theme requires. No `import re`; donkey = 0 (no LLM); NEVER git.
"""
from __future__ import annotations

from domains import situation_model_reader as smr


# --------------------------------------------------------------------------- #
#  resolution (mechanical adapter I/O — the same idiom every domains/*.py uses).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


# --------------------------------------------------------------------------- #
#  THE GRAPH-RESIDENT DEFAULT-READING MODEL — the compulsive reading a threat-
#  in-an-imperative evokes. A single ImposedReadingSchema node (installed once,
#  guarded by its own presence — the SAME idempotency idiom the seed installers
#  use); the reading label is DATA, not a Python branch.
# --------------------------------------------------------------------------- #
def ensure_seeds(agent) -> None:
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("ImposedReadingSchema"):
        if sub.node(n)["attrs"].get("trigger") == "threat_warning":
            return
    sub.add_node("ImposedReadingSchema",
                 {"trigger": "threat_warning", "reading": "heroic quest",
                  "note": "the reading most readers compulsively impose when a threat is "
                          "named in an imperative -- a monster is named, so there must be a "
                          "quest to slay it (the shave-and-a-haircut pull-to-close)"})


def _imposed_reading(agent) -> dict:
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("ImposedReadingSchema"):
        at = sub.node(n)["attrs"]
        if at.get("trigger") == "threat_warning":
            return {"reading": at.get("reading"), "note": at.get("note")}
    return {"reading": "heroic quest", "note": ""}


# --------------------------------------------------------------------------- #
#  READ THE HELD-OPEN GOALS (minted by inference_generation.resolve_warning_gap).
# --------------------------------------------------------------------------- #
def held_open_goals(agent) -> list:
    """Every `OpenGoal` node the goal-level licensing gate held open (a warning
    with no governing need-state). Pure graph read."""
    sub, _, _ = _resolve(agent)
    out = []
    for n in sub.nodes("OpenGoal"):
        at = sub.node(n)["attrs"]
        if at.get("held_open"):
            out.append({"node": n, "threat": at.get("threat"),
                        "protagonist": at.get("protagonist"),
                        "warning_verb": at.get("warning_verb"), "record": at.get("record")})
    return out


# --------------------------------------------------------------------------- #
#  THE READER-RESPONSE — the ambiguity IS the meaning; the default reading is
#  MODELLED as another's, never asserted.
# --------------------------------------------------------------------------- #
_DEFAULT_NOTE = "most readers would impose a heroic-quest reading; the ambiguity is the point"


def _respond_one(agent, og: dict) -> dict:
    sub, native, _ = _resolve(agent)
    threat = og.get("threat") or "unspecified"
    imposed = _imposed_reading(agent)

    # 1. THE AMBIGUITY IS THE MEANING — the reader's OWN verdict, held open.
    question = sub.add_node("OpenQuestion",
                            {"question": "was the quest warranted?",
                             "theme": "the undetermined danger",
                             "meaning": "the ambiguity is the meaning -- the withheld goal "
                                        "and the undetermined danger ARE the content",
                             "threat": threat, "held_open": 1, "asserted_by_reader": 0,
                             "source": "reader_response"})
    smr._edge(native, og["node"], "raises", question)

    # 2. MODEL THE DEFAULT READING AS ANOTHER MIND'S — never the agent's own.
    #    ReaderModel is the modeled holder (character_tom's nested belief-world
    #    idiom); ModeledReading is the imposed reading in its belief-world.
    reader = sub.add_node("ReaderModel",
                          {"name": "default_reader", "nested": 1,
                           "note": "the generic reader whose compulsion the agent MODELS "
                                   "without sharing", "source": "reader_response"})
    modeled = sub.add_node("ModeledReading",
                           {"reading": imposed["reading"], "threat": threat,
                            "note": _DEFAULT_NOTE, "most_impose": 1,
                            "asserted_by_reader": 0, "imposed_by": "default_reader",
                            "basis": imposed["note"], "source": "reader_response"})
    smr._edge(native, reader, "belief_world", modeled)      # modelled, NOT asserted
    smr._edge(native, og["node"], "modeled_default_reading", modeled)

    return {"open_goal": smr._v(og["node"]), "threat": threat,
            "open_question": smr._v(question), "reader_model": smr._v(reader),
            "modeled_reading": smr._v(modeled), "default_note": _DEFAULT_NOTE,
            "held_open_verdict": og.get("record")}


def model_reader_response(agent) -> list:
    """For every HELD-OPEN OpenGoal, mint the reader-response: the OpenQuestion
    (the ambiguity is the meaning — the reader's own verdict) and the modeled
    default heroic-quest reading (attributed to a modeled reader, flagged
    `most_impose`, `asserted_by_reader=0`). Idempotent per OpenGoal (skips one
    already responded to). Returns one record per held-open goal."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    out = []
    for og in held_open_goals(agent):
        if sub.neighbours(og["node"], "raises"):        # already responded — idempotent
            continue
        out.append(_respond_one(agent, og))
    return out


# --------------------------------------------------------------------------- #
#  THE DECOUPLED READING — the correction. The reader MODELS the child's
#  licensed belief WITHOUT holding it; the belief-world boundary is MAINTAINED.
# --------------------------------------------------------------------------- #
def _child_danger_beliefs(agent) -> list:
    """Every NESTED belief node carrying `danger=1` and a `belief_holder` — the
    child's licensed danger-belief that inference_generation.resolve_warning_
    embedded minted inside the child's belief-world (character_tom idiom). A
    MODELED object, indexed to the child. Pure graph read."""
    sub, _, _ = _resolve(agent)
    out = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("nested") and at.get("danger") == 1 and at.get("belief_holder"):
            out.append({"node": n, "referent": at.get("referent"),
                        "belief_holder": at.get("belief_holder"),
                        "licensed_within_world": at.get("licensed_within_world"),
                        "licensed_by": at.get("licensed_by")})
    return out


def _respond_decoupled(agent, og: dict, belief: dict) -> dict:
    sub, native, _ = _resolve(agent)
    threat = og.get("threat") or belief.get("referent") or "unspecified"
    imposed = _imposed_reading(agent)
    reading = sub.add_node(
        "DecoupledReading",
        {"reading": imposed["reading"], "threat": threat,
         "belief_holder": belief.get("belief_holder"),
         # the MODELED fact about the child (licensed within the child's world).
         "models_child_believes_danger": 1,
         "child_belief_licensed_within_world": belief.get("licensed_within_world") or 1,
         "child_belief_licensed_by": belief.get("licensed_by") or "trusts",
         # the reader's OWN, decoupled verdict — the danger is NOT held.
         "reader_holds_danger": 0,
         "reader_asserts_heroic_quest": 0,
         "reader_own_verdict": og.get("record"),
         # the achievement: the nesting is maintained, not collapsed.
         "boundary_maintained": 1, "immersion": 0,
         "via": "decoupled modeling / maintained nesting",
         "note": ("the reader MODELS that the child believes the danger (CORRECT within the "
                  "child's belief-world -- trusted source licenses it) WHILE NOT HOLDING the "
                  "danger itself; the child's belief stays a modeled object indexed to the "
                  "child and never leaks into the reader's own belief set"),
         "source": "reader_response"})
    smr._edge(native, og["node"], "decoupled_reading", reading)
    smr._edge(native, reading, "models", belief["node"])      # points AT the child's nested belief
    return {"open_goal": smr._v(og["node"]), "threat": threat,
            "belief_holder": belief.get("belief_holder"),
            "decoupled_reading": smr._v(reading),
            "models_child_believes_danger": True, "reader_holds_danger": False,
            "boundary_maintained": True, "reader_own_verdict": og.get("record")}


def model_decoupled_reading(agent) -> list:
    """For every held-open OpenGoal that has a MATCHING child danger-belief
    (belief_holder == the OpenGoal's protagonist), mint a `DecoupledReading`
    that pins BOTH facts: the reader MODELS the child's licensed danger-belief
    (pointing at the child's nested node) AND does NOT HOLD the danger (its own
    verdict is the detached OpenGoal). Idempotent per OpenGoal. Returns one
    record per decoupled reading. When the source is UNTRUSTED (no child belief
    was minted) there is nothing to model -> honest empty (the discriminative
    case)."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    beliefs = _child_danger_beliefs(agent)
    out = []
    for og in held_open_goals(agent):
        if sub.neighbours(og["node"], "decoupled_reading"):    # idempotent
            continue
        prot = og.get("protagonist")
        match = next((b for b in beliefs if b["belief_holder"] == prot), None)
        if match is None:
            continue                                           # untrusted / no child belief
        out.append(_respond_decoupled(agent, og, match))
    return out


# --------------------------------------------------------------------------- #
#  QUERY HELPERS — pure graph reads.
# --------------------------------------------------------------------------- #
def reader_holds_danger(agent) -> bool:
    """Does the READER ITSELF hold 'the threat is dangerous'? The reader's OWN
    belief set is the ACTUAL-world (non-nested) SmEntity states. A `danger=1`
    that lives only on a NESTED belief node (indexed to the child) is a MODELED
    object, NOT the reader's belief. True iff some NON-nested entity carries
    danger — which the decoupled reading must NEVER produce (the boundary is
    maintained). Always False on the Jabberwocky read: the danger is the child's
    modeled belief only."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if not at.get("nested") and at.get("danger") == 1:
            return True
    return False


def reader_models_child_believes_danger(agent) -> bool:
    """Does the reader MODEL that the child believes the danger? True iff a
    NESTED danger-belief indexed to a `belief_holder` is resident (the child's
    licensed belief-world). The reader knows this FACT ABOUT THE CHILD without
    holding the danger — the two are distinct (`reader_holds_danger` is False)."""
    return bool(_child_danger_beliefs(agent))


def decoupled_readings(agent) -> list:
    """The DecoupledReading nodes — each records the reader modeling the child's
    licensed belief WITHOUT holding it, boundary maintained."""
    sub, _, _ = _resolve(agent)
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("DecoupledReading")]


def open_questions(agent) -> list:
    sub, _, _ = _resolve(agent)
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("OpenQuestion")]


def modeled_default_readings(agent) -> list:
    """The heroic-quest readings the agent MODELS as others' — each flagged
    `most_impose=1` / `asserted_by_reader=0` (understood, never shared)."""
    sub, _, _ = _resolve(agent)
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("ModeledReading")]


def reader_asserts_heroic_quest(agent) -> bool:
    """Does the READER ITSELF assert the heroic-quest reading? Always False —
    every modeled reading is flagged `asserted_by_reader=0`, and the agent's own
    verdict is the held-open OpenGoal/OpenQuestion. The compulsion is modelled
    in others, never adopted."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("ModeledReading"):
        if sub.node(n)["attrs"].get("asserted_by_reader"):
            return True
    return False


__all__ = ["ensure_seeds", "held_open_goals", "model_reader_response",
           "model_decoupled_reading", "open_questions", "modeled_default_readings",
           "reader_asserts_heroic_quest", "reader_holds_danger",
           "reader_models_child_believes_danger", "decoupled_readings"]
