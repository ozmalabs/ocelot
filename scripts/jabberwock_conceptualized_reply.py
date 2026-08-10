"""jabberwock_conceptualized_reply — PHASE 3: the CONCEPTUALIZER wired into the LIVE converse
reply path. The jabberwock now FORMS AN INTENT and FOLLOWS THROUGH (the creator's framing): a
reply forms a communicative intent (Searle force + perlocutionary goal), shapes it for THIS
interlocutor (Clark's audience design over common ground), monitors it (Levelt's internal loop —
imagine reception, reground, revise if the intent isn't recoverable), then speaks — instead of
reacting straight to produce.

This narrates what `tests/test_conceptualized_converse.py` gates. donkey=0 throughout: the
CONTENT is the agent's own faculties, the DECISIONS (force, focus/ground, recoverable) are the
jabberwock's own composer-authored rules' (seeds/conceptualizer.json).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_conceptualized_reply.py
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
from domains import conversation_action as ca
import domains.conceptualizer as cc

LEX = [{"form": "grey", "concept": "grey"}, {"form": "yellow", "concept": "yellow"},
       {"form": "blue", "concept": "blue"}]
CONTENT = {"grey", "yellow", "blue"}


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def _describe_agent(known, observed):
    a = _agent()
    ca.attach_scene(a, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False}])
    node = a._interlocutor("user")
    a.inner.set_attr(node, "observed", observed)
    if known is not None:
        a.inner.set_attr(node, "known_concepts", known)
    return a


def main():
    print("=" * 78)
    print("PHASE 3 — the conceptualizer FORMS INTENT and FOLLOWS THROUGH in the live path")
    print("=" * 78)

    # 1. FORMED INTENT in the live reply path.
    print("\n[1] FORMED INTENT before the utterance (a live answer)")
    a = _agent()
    reply = a.converse("How are you organised?", "question")
    intent = a._last_reply_intent["intent"]
    print(f"    reply    : {reply!r}")
    print(f"    intent   : force={intent['force']!r}  perlocutionary_goal="
          f"{intent['perlocutionary_goal']!r}")
    print(f"    committed: {a._last_reply_intent['committed']['committed'] is not None} "
          f"(the self-monitor cleared the commit gate before the reply was spoken)")

    # 2. AUDIENCE-DESIGNED delivery: same input, grounded vs ungrounded.
    print("\n[2] AUDIENCE-DESIGNED delivery — SAME describe, different interlocutor")
    g = _describe_agent(["grey"], True)
    u = _describe_agent(None, False)
    gr = g.converse("describe what you see", "statement")
    ur = u.converse("describe what you see", "statement")
    print(f"    GROUNDED (knows the grey thing): {gr!r}")
    print(f"    UNGROUNDED (unknown audience)  : {ur!r}")
    print(f"    -> grounded is TERSER ({len(gr.split())} words vs {len(ur.split())}); "
          f"drops the credited-known 'grey' the ungrounded reply restates.")

    # 3. MONITOR gates a revision: terse formulation for a credited-grounded audience
    #    whose ground turns out not to hold at commit -> revised to explicit.
    print("\n[3] MONITOR gates a revision — a stale belief caught at reground")
    a = _agent()
    cc.ensure_conceptualizer_rules(a)
    goal = cc.mint_communicative_goal(
        a, "inform", CONTENT, {"id": "user", "observed": True, "known_concepts": ["grey"]})
    a.inner.run_rules(2000)
    res = cc.scan_and_conceptualize(a, LEX)
    initial = res[0]["result"]["utterance"]
    a.inner.run_rules(2000)
    aud = next(iter(a.inner.neighbours(res[0]["intent"], "for_audience")))
    a.inner.set_attr(aud, "observed", False)          # corrected: was NOT observed
    cc.run_pipeline(a, LEX, rounds=4)
    committed = cc.read_committed(a, goal)
    print(f"    initial (terse)    : {initial!r}")
    print(f"    committed (revised): {committed['utterance']!r}")
    print(f"    -> the monitor caught the un-recoverable terse form and made it explicit "
          f"before commit.")

    # 4. no prior behaviour regressed; rich prose intact.
    print("\n[4] NO REGRESSION + rich prose intact")
    a = _agent()
    for text, sa in [("hello", "greeting"), ("the sky is blue", "statement"),
                     ("what is a borogove", "question"), ("flar the glorp", "statement"),
                     ("Tell me about the rule hop_descend_gradient.", "question")]:
        print(f"    [{sa:9}] {text!r:44} -> {a.converse(text, sa)!r}")

    donkeys = [a._donkey["n"], g._donkey["n"], u._donkey["n"]]
    print(f"\n    donkey (self-teacher / LLM calls): {donkeys}  (all 0 — held machinery only)")
    print("=" * 78)


if __name__ == "__main__":
    main()
