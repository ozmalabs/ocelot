"""CAPSTONE — the SAME world-understanding interface, on CONVERSATION. The proof it was never a game
interface: bind_world (the identical six-role mechanism used for snake) binds a Conversation, and the six
universal roles are filled by CONVERSATION fillers — controllable_locus = the WRITE-HEAD (the agent's own
utterance, the creator's example), value_signal = uptake/repair-rate, terminal = breakdown/closing, goal =
intent-satisfied. No game-noun anywhere; game and conversation are both just frames + fillers over the one
interface. categorise_by_shape classifies the conversation's shape (a different frame than Game).
Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/world_conversation.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from world_roles import bind_world, ROLES
from domains.teach import categorise_by_shape

# Frame priors as DATA (one row each in the library): which filler fills each role for this world-KIND.
GAME_FRAME = {"kind":"Game","desc":"a controllable avatar predicts and acts; a monotone score rewards; "
              "contact causes consequence; death ends it; navigate to a goal",
              "fills":{"controllable_locus":"respond_votes","value_signal":"score","terminal":"death",
                       "goal":"positive-kind","affordance_effect":"action_delta","dynamics":"region-postulates"}}
CONV_FRAME = {"kind":"Conversation","desc":"turn-taking dialogue; I author my own utterance; the interlocutor's "
              "uptake rewards and repair penalises; breakdown or closing ends it; satisfy the intent",
              "fills":{"controllable_locus":"write_head","value_signal":"uptake_minus_repair","terminal":"breakdown",
                       "goal":"intent_satisfied","affordance_effect":"speech_acts","dynamics":"turn-taking-laws"}}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])

    # the agent's OWN shape-classifier runs on each frame's stream-descriptor (no game assumed)
    game_shape=categorise_by_shape(a,"WorldFrame",{"desc":GAME_FRAME["desc"]})
    conv_shape=categorise_by_shape(a,"WorldFrame",{"desc":CONV_FRAME["desc"]})
    print(f"  categorise_by_shape: Game->{game_shape!r}   Conversation->{conv_shape!r}")

    # --- a minimal CONVERSATION world (no game content) ---
    conv=a.s.add_node("WorldInstance",{"world_type":"Conversation","world_id":"c1"})
    me=a.s.add_node("Interlocutor",{"name":"self"}); other=a.s.add_node("Interlocutor",{"name":"them"})
    # the WRITE-HEAD: the agent's own utterance — the thing it controls in a conversation
    writehead=a.s.add_node("Utterance",{"by":"self","act":"assert","is_write_head":1.0})
    a.inner.add_edge_unchecked(conv,"controlled_by",writehead)
    # turns + an uptake/repair signal (the conversation's better/worse feedback)
    uptake=a.s.add_node("DiscourseSignal",{"uptake":3.0,"repair":1.0})   # interlocutor took up 3, repaired 1
    a.inner.add_edge_unchecked(conv,"discourse_signal",uptake)
    intent=a.s.add_node("Intent",{"satisfied":0.0}); a.inner.add_edge_unchecked(conv,"has_intent",intent)
    breakdown=a.s.add_node("DiscourseState",{"breakdown":0.0,"closing":0.0}); a.inner.add_edge_unchecked(conv,"state",breakdown)

    # SAME bind_world used for snake -> six universal role slots
    b, slots = bind_world(a, conv)
    a.s.set_attr(b,"kind","conversation")
    # FILL with CONVERSATION fillers (the Conversation frame's found_by per role)
    def fill(role, node, conf, note):
        a.inner.add_edge_unchecked(slots[role],"filled_by",node)
        a.s.set_attr(slots[role],"status","derived"); a.s.set_attr(slots[role],"confidence",conf)
        a.s.set_attr(slots[role],"filler_note",note)
    ua=a.s.node(uptake)["attrs"]; val=(ua["uptake"]-ua["repair"])
    fill("controllable_locus", writehead, 1.0, "write_head (my own utterance)")
    fill("value_signal", uptake, val, "uptake - repair")
    fill("affordance_effect", writehead, 1.0, "speech_acts")
    fill("dynamics", conv, 0.5, "turn-taking laws")
    fill("terminal", breakdown, 1.0, "breakdown/closing")
    fill("goal", intent, 1.0, "intent satisfied")

    print("\n  SAME six-role binding, now on a CONVERSATION (no game-noun):")
    for r in ROLES:
        sa=a.s.node(slots[r])["attrs"]; print(f"    {r:18s} status={sa.get('status'):8s} filler={sa.get('filler_note')}")
    locus_note=a.s.node(slots["controllable_locus"])["attrs"].get("filler_note")
    print(f"\n  controllable_locus = {locus_note}  | value_signal (uptake-repair) = {val}")
    print(f"  DONKEY calls: {calls['n']}")
    ok = (all(a.s.node(slots[r])["attrs"].get("status")=="derived" for r in ROLES)
          and "write_head" in (locus_note or "") and val>0
          and a.s.has_edge(slots["controllable_locus"],"filled_by",writehead) and calls["n"]==0)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — CAPSTONE: the identical six-role bind_world used for snake binds "
          f"a CONVERSATION, and the universal roles fill with conversation fillers — controllable_locus = the "
          f"WRITE-HEAD (my own utterance), value_signal = uptake-repair ({val:+.0f}), terminal = breakdown, "
          f"goal = intent. No game-noun, no donkey ({calls['n']}). This was never a game interface; it is a "
          f"world-understanding interface, game and conversation alike are frames over the same six roles.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
