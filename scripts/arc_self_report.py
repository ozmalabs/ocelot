"""WORLD LANGUAGE-RECEIVER -> REASONING -> the jabberwock SELF-REPORTS -> printed.

The correct architecture (not forced utterances). We spent a long time giving the agent the ability to set its
OWN goal to describe what it does, in its own voice, FROM AN INSTRUCTION. So the host must NOT call produce()
with a hand-picked verb map. Instead: the WORLD provides a LANGUAGE RECEIVER — it ingests an instruction
("Describe what you are doing.") as a Message the agent perceives; that goes into REASONING — the agent's OWN
comprehension rule mints a describe-Goal, its OWN communicate rule mints a produce-utterance subgoal per
recognised thing; the jabberwock SELF-REPORTS — its language faculty speaks each; and the report is PRINTED.
The host only RECEIVES the instruction and PRINTS the report. donkey=0; nothing forced.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/arc_self_report.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank

def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Holds(name, node): return {"type": "Holds", "concept": name, "node": node}

GAMING = ["the_thing_i_control", "a_thing_that_moves_itself", "a_thing_that_stays_put",
          "a_counter", "a_barrier_i_cannot_pass", "a_way_i_can_pass"]


def build_describe_faculty(a):
    """The agent BUILDS its own comprehend + communicate rules (I only frame the concerns). Recognition rules
    are graph-native. This is the held self-report machinery — not host code that emits sentences."""
    I = a.inner
    for name in GAMING:
        I.add_rule({"name": f"recognise_{name}",
                    "match": [["scene", "has_percept", "p"], ["gmt", "has_concept", "con"]],
                    "where": And(Eq(Attr(V("con"), "name"), L(name)), Holds(name, V("p"))),
                    "effects": [["add_edge", "p", "is_a", "con"]]})
    cA = induce_concern(a, [["hear", "the", "describe", "DIRECTIVE"], ["mint", "a", "GOAL"]],
                        name_hint="comprehend_describe")
    if cA.get("capability_key"):
        ground_concern(a, [cA["capability_key"]])
    cB = induce_concern(a, [["told", "DESCRIBE", "what", "SEEN"], ["for_each", "PERCEPT", "mint", "SUBGOAL"],
                            ["SUBGOAL", "produces", "UTTERANCE"], ["source", "UTTERANCE", "from", "PERCEPT"]],
                        name_hint="communicate_what_i_see")
    if cB.get("capability_key"):
        ground_concern(a, [cB["capability_key"]])
    # GROUND WHAT I CONTROL (from interaction, over the WHOLE body): the jabberwock authors the agency rule
    # itself from this concern (the composer's control path), not a hand-written rule.
    cC = induce_concern(a, [["control", "the", "WHOLE", "BODY"], ["responds", "to", "my", "ACTION"]],
                        name_hint="ground_control")
    if cC.get("capability_key"):
        ground_concern(a, [cC["capability_key"]])
    # COMPOSE the order-N WHOLE object: the jabberwock fuses its co-moving body parts into ONE object so the
    # whole has a single shape (authored via the composer's grouping path, not a hand rule).
    cD = induce_concern(a, [["co-move", "PARTS", "into", "WHOLE"], ["group", "WHOLE", "from", "PARTS"]],
                        name_hint="compose_whole_body")
    if cD.get("capability_key"):
        ground_concern(a, [cD["capability_key"]])


def world_receive(a, scene, instruction):
    """THE WORLD'S LANGUAGE RECEIVER — translate an external instruction into a Message the agent perceives
    (about the current scene). Mechanical ingest; no decision, no utterance authored here."""
    msg = a.s.add_node("Message", {"text": instruction})
    a.inner.add_edge_unchecked(msg, "about", scene)
    for w in instruction.lower().replace(".", "").replace("?", "").split():
        a.inner.add_edge_unchecked(msg, "has_mention", a.s.add_node("Mention", {"text": w}))


def world_receive_intent(a, game, instruction="What are you doing, and why?"):
    """THE WORLD'S LANGUAGE RECEIVER for GOALS — translate a 'what are you doing?' instruction into a Message the
    agent perceives ABOUT THE GAME (its drive state). Mechanical ingest; the goal report is reasoned in-graph."""
    msg = a.s.add_node("Message", {"text": instruction})
    a.inner.add_edge_unchecked(msg, "intent_about", game)
    for w in instruction.lower().replace(".", "").replace("?", "").replace(",", "").split():
        a.inner.add_edge_unchecked(msg, "has_mention", a.s.add_node("Mention", {"text": w}))


def self_report(a, prod, parent_kind="describe_scene"):
    """EMIT a self-report. The utterance frame on each produce_utterance subgoal was ASSEMBLED by graph rules
    from graph state — for OBSERVATIONS (parent describe_scene): the perceived shape/noun, verb, colour; for
    GOALS (parent report_intent): the aim verb, and the curiosity (watch the unpredicted mover). The host makes
    NO decision: it reads the frame {say_agent, say_agent_adj, say_event, say_patient, say_patient_adj} and
    speaks it through the production faculty, deduping identical utterances. donkey=0."""
    s, I = a.s, a.inner
    # node ids recycle from a freelist (no generation), so guard every raw id with has_node before node().
    gs = [g for g in s.nodes("Goal") if I.has_node(g) and s.node(g)["attrs"].get("kind") == parent_kind]
    subgoals = [sg for g in gs for sg in I.neighbours(g, "has_subgoal")]
    lines, seen = [], set()
    for sg in subgoals:
        if not I.has_node(sg):
            continue
        at = s.node(sg)["attrs"]
        agent_w = at.get("say_agent")
        if not agent_w:
            continue
        ev, ag_adj = at.get("say_event"), at.get("say_agent_adj")
        pat, pat_adj = at.get("say_patient"), at.get("say_patient_adj")
        ob_role, ob, ob_adj = at.get("say_oblique_role"), at.get("say_oblique"), at.get("say_oblique_adj")
        key = (agent_w, ag_adj, ev, pat, pat_adj, ob_role, ob, ob_adj)
        if key in seen:
            continue
        seen.add(key)
        goal = {"agent": agent_w, "tense": "present", "intent": "inform"}
        if ev:
            goal["event"] = ev
        if pat:
            goal["patient"] = pat
        if ob_role and ob:                          # an oblique (e.g. topic 'about', goal 'to')
            goal[ob_role] = ob
        adj = {}
        if ag_adj:
            adj["agent"] = ag_adj
        if pat_adj:
            adj["patient"] = pat_adj
        if ob_role and ob_adj:
            adj[ob_role] = ob_adj
        if adj:
            goal["adjectives"] = adj
        lines.append(prod.produce("en", goal)["overt_speech"])
    return len(gs), len(subgoals), lines


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    print("=" * 94)
    print("WORLD LANGUAGE-RECEIVER -> REASONING -> the jabberwock SELF-REPORTS -> printed (nothing forced)")
    print("=" * 94)

    build_describe_faculty(a)
    # production faculty (the agent's voice). The describe vocabulary (concept noun/verb attrs, shape labels,
    # colour LexEntries) is GRAPH DATA loaded by the seeds (describe_lexicon / gaming / shape_library) — the
    # host grounds nothing here.
    world = LanguageWorld(I, training_bank(), teacher_stub); world.run()
    world.teacher_disabled = True
    prod = LanguageProduction(world)

    # the agent's current perception (a scene of things it is among), each with a perceived colour. Shaped like
    # the LIVE eye's Features: kind + colour only (the eye does not supply passable/responds, so the relational
    # concepts barrier/way/control don't fire here either — matching what the agent actually perceives live).
    scene = s.add_node("Scene", {})
    for ctx in ({"kind": "static", "colour": "grey"},
                {"kind": "meter", "colour": "yellow"},
                {"kind": "mover", "colour": "blue", "responds_to_my_action": False}):
        I.add_edge_unchecked(scene, "has_percept", s.add_node("Percept", ctx))
    I.run_rules()

    # THE WORLD RECEIVES an instruction (the language receiver) -> it goes into REASONING (tick).
    instruction = "Describe what you see."
    print(f"\n  world receives (language receiver): {instruction!r}")
    world_receive(a, scene, instruction)
    I.run_rules()                                          # the instruction enters reasoning; the agent acts on it

    ng, nsg, lines = self_report(a, prod)
    print(f"  -> reasoning: the agent minted {ng} describe-Goal and {nsg} utterance subgoals from the instruction")
    print("\n  THE JABBERWOCK SELF-REPORTS (per-percept produced pieces):")
    for ln in lines:
        print(f"    {ln!r}")
    # SMOOTH: connect the agent's own produced pieces into one fluent sentence
    # (mechanical connective join — authors no new content). Register-shaped.
    from domains.conversation_action import smooth_scene_prose
    print("\n  SMOOTHED (connected prose, the agent's own pieces joined):")
    print(f"    {smooth_scene_prose(lines)!r}")

    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = ng >= 1 and len(lines) >= 1 and donkey["n"] == 0
    print(f"  {'PASS' if ok else 'FAIL'} — the host did NOT author any utterance: the WORLD received the")
    print("  instruction, it went into REASONING (the agent's own comprehend->describe-Goal->communicate rules),")
    print("  the JABBERWOCK SELF-REPORTED via its language faculty, and the host only PRINTED it. Not forced.")
    print("  (arc_run's _speak_* forced-utterance voices should be replaced by exactly this receiver->report.)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
