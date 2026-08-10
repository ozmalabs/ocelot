"""jabberwock_full_conversation — a COMPLETE conversation on the live converse
loop: the jabberwock ANSWERS questions, ACTS on instructions (a conversation
drives a goal -> it does something it chose), and ASKS BACK on a comprehension
gap (a repair first-pair-part) — all through one path, turn after turn.

The creator's target: "it has a conversation mode ... knows about turn-taking and
asking questions ... should be able to have a complete conversation and PERFORM
ARBITRARY ACTIONS from that conversation if it chooses." The pieces existed;
`WorldAdapter.converse` now wires them (via domains/conversation_action.py):

    comprehend (general: comprehend_text)  ->  answer | act | ask-back  ->  produce

donkey=0: the CONTENT is the agent's own faculties (self-model reflect, the self-
built describe faculty, its production voice), never host-authored replies. The
host only routes comprehend_text's derived intent to the held faculty and prints.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_full_conversation.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import conversation_action as ca


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    # the world attaches a small perceivable scene (the live eye's Feature shape:
    # kind + colour) so a 'describe what you see' instruction can be ACTED on.
    ca.attach_scene(a, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False}])

    print("=" * 92)
    print("A COMPLETE CONVERSATION — the jabberwock answers, acts, and asks back (one path)")
    print("=" * 92)

    # (behaviour label is just for the transcript; the AGENT decides via comprehend_text)
    turns = [
        ("greeting",    "Hello.",                          "greeting"),
        ("QUESTION",    "How are you organised?",          None),
        ("INSTRUCTION", "Describe what you see.",           None),   # -> ACT (describe faculty)
        ("INSTRUCTION", "Report your organisation.",        None),   # -> ACT (self-report)
        ("GAP",         "Quorplezap the door.",             None),   # -> ASK BACK (repair)
        ("QUESTION",    "Tell me about the rule hop_descend_gradient.", None),
    ]

    for label, text, forced_sa in turns:
        sa = forced_sa or a.classify_speech_act(text)
        reply = a.converse(text, sa)
        print(f"\n  USER  [{label:11}] {text}")
        if reply is None:
            print(f"  JABB              (no response expected — terminal act)")
        else:
            print(f"  JABB              {reply}")

    # honest read-off of what the conversation drove in the graph
    def _goals(kind):
        return [g for g in a.s.nodes("Goal")
                if a.inner.has_node(g) and a.s.node(g)["attrs"].get("kind") == kind]
    report_self = _goals("report_self")
    describe = _goals("describe_scene")
    clar = [m for m in a.s.nodes("Message")
            if a.s.node(m)["attrs"].get("from") == "agent"
            and a.s.node(m)["attrs"].get("trouble_source")]

    print("\n" + "=" * 92)
    print("  WHAT THE CONVERSATION DROVE IN THE GRAPH (the actions, not just replies):")
    print(f"    report_self Goals minted (self-report acts):   {len(report_self)}")
    print(f"    describe_scene Goals minted (the agent's rule): {len(describe)}")
    print(f"    clarification first-pair-parts (repair asks):   {len(clar)}")
    print(f"    donkey (LLM self-teacher calls):                {donkey['n']}")

    ok = (len(report_self) >= 1 and len(describe) >= 1 and len(clar) >= 1
          and donkey["n"] == 0)
    print("\n  " + ("PASS" if ok else "FAIL") +
          " — a complete multi-turn conversation: the jabberwock ANSWERED (self + world"
          " questions),")
    print("  ACTED (minted a describe-Goal via its own authored rule and a self-report Goal, and"
          " SPOKE the")
    print("  results through its production faculty), and ASKED BACK on a gap (a repair first-pair-"
          "part")
    print("  quoting the trouble source) — all through one converse path, donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
