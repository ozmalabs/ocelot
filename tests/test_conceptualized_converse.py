"""test_conceptualized_converse — PHASE 3 of the CONCEPTUALIZER: the pipeline is WIRED into
the LIVE converse reply path (`WorldAdapter.converse` + `domains.conversation_action`). A reply
now FORMS a communicative intent (Searle force + perlocutionary goal), SHAPES it for THIS
interlocutor (audience design over common ground), MONITORS it (imagine reception, reground,
revise if the intent is not recoverable), and only then speaks — instead of reacting straight to
produce.

HOW EACH REPLY TYPE FLOWS (see the module docstrings of substrate/world_adapter.py's PHASE-3
block + domains/conversation_action._act_describe_scene):
  • social ack (hello / noted) + honest fallback (I don't know X / no world) → AROUND the
    pipeline (phatic / dead-end floor, unchanged);
  • self-model prose + world/self answer → FORM intent + MONITOR-gate; the PROSE renderer
    (`_surface_self_state` / `answer_question`) is UNCHANGED (rich prose not downgraded);
  • describe-scene (concept-level content) → FULLY through the pipeline: the committed,
    audience-designed conveyed subset of lines is smoothed into fluent prose;
  • ask-back → forms a directive (request) intent, delivers the repair first-pair-part.

Every DECISION (which force, which focus/ground, whether recoverable) is the jabberwock's own
composer-authored rules' (seeds/conceptualizer.json, authored via induce_concern->ground_concern);
the converse wiring only forms + gates + reads back. donkey=0 throughout.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter                          # noqa: E402
from substrate.boot_all import load_all_seeds                             # noqa: E402
from domains import conversation_action as ca                             # noqa: E402
import domains.conceptualizer as cc                                       # noqa: E402

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


def _describe_agent(known=None, observed=False):
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


# ===========================================================================
# 1. FORMED INTENT IN THE LIVE PATH — a live reply has an associated
#    CommunicativeIntent (force + perlocutionary_goal) formed BEFORE the utterance.
# ===========================================================================
def test_formed_intent_in_live_answer_path():
    a = _agent()
    n_before = len(list(a.s.nodes("CommunicativeIntent")))
    reply = a.converse("How are you organised?", "question")
    assert isinstance(reply, str) and "organis" in reply.lower()

    res = a._last_reply_intent
    assert res is not None, "the live reply formed a communicative intent"
    assert res["intent"]["intent"] is not None, "a CommunicativeIntent graph node exists"
    assert res["intent"]["force"] == "assertive"
    assert res["intent"]["perlocutionary_goal"] == "hearer_knows"
    # the intent was FORMED (a new node), and the monitor CLEARED a Committed utterance.
    assert len(list(a.s.nodes("CommunicativeIntent"))) > n_before
    assert res["committed"]["committed"] is not None, "the self-monitor cleared the commit gate"
    print("FORMED INTENT (live answer):",
          {k: res["intent"][k] for k in ("force", "perlocutionary_goal", "informative_content")})
    assert a._donkey["n"] == 0


def test_instruction_and_askback_form_intents_too():
    a = _agent()
    # a self-report INSTRUCTION forms an inform intent (assertive -> hearer_knows)
    a.converse("report your organisation", "statement")
    inst = a._last_reply_intent
    assert inst is not None and inst["intent"]["force"] == "assertive"
    # an ASK-BACK forms a directive (request) intent (hearer_does)
    ask = a.converse("quorplezap the door", "statement")
    assert ask.rstrip().endswith("?")
    rb = a._last_reply_intent
    assert rb is not None and rb["intent"]["force"] == "directive"
    assert rb["intent"]["perlocutionary_goal"] == "hearer_does"
    print("ASK-BACK intent:", {k: rb["intent"][k] for k in ("force", "perlocutionary_goal")})
    assert a._donkey["n"] == 0


# ===========================================================================
# 2. AUDIENCE-DESIGNED DELIVERY — SAME describe instruction, GROUNDED vs
#    UNGROUNDED interlocutor -> terser vs more explicit, via the pipeline.
# ===========================================================================
def test_audience_designed_describe_grounded_terser_than_ungrounded():
    grounded = _describe_agent(known=["grey"], observed=True)
    ungrounded = _describe_agent(known=None, observed=False)

    g_reply = grounded.converse("describe what you see", "statement")
    u_reply = ungrounded.converse("describe what you see", "statement")
    print("GROUNDED   describe:", repr(g_reply))
    print("UNGROUNDED describe:", repr(u_reply))

    assert g_reply and u_reply
    assert g_reply != u_reply, "same input, different audience -> different delivery"
    assert len(g_reply.split()) < len(u_reply.split()), "grounded audience -> terser"
    # the credited-known percept (grey) is DROPPED for the grounded audience, RESTATED
    # for the ungrounded one — the shape is the pipeline's residual-vs-audience, not a
    # host decision.
    assert "grey" not in g_reply
    assert "grey" in u_reply
    # both replies are the described-scene concept path, and both formed an intent.
    assert grounded._last_reply_intent is not None
    assert ungrounded._last_reply_intent is not None
    assert grounded._donkey["n"] == 0 and ungrounded._donkey["n"] == 0


# ===========================================================================
# 3. MONITOR GATES A REVISION — a terse formulation for a credited-grounded
#    audience whose ground turns out NOT to hold at commit time is REVISED to
#    explicit BEFORE the commit gate clears (the committed utterance is the
#    revision, not the pre-monitor terse form). Driven on the LIVE WorldAdapter
#    agent through the same conceptualizer entry the converse path uses — the
#    belief-correction between formulation and commit cannot occur inside a single
#    atomic converse call, so the pipeline steps are driven explicitly to inject it.
# ===========================================================================
def test_monitor_gates_a_revision_on_the_live_agent():
    a = _agent()
    cc.ensure_conceptualizer_rules(a)
    g = cc.mint_communicative_goal(
        a, "inform", CONTENT, {"id": "user", "observed": True, "known_concepts": ["grey"]})
    a.inner.run_rules(2000)
    res = cc.scan_and_conceptualize(a, LEX)
    initial = res[0]["result"]["utterance"]
    assert res[0]["result"]["grounded_used"] is True, "starts GROUNDED (terse) to be a real catch"
    a.inner.run_rules(2000)

    # a corrected belief: this interlocutor was NOT actually observed after all.
    aud = next(iter(a.inner.neighbours(res[0]["intent"], "for_audience")))
    a.inner.set_attr(aud, "observed", False)

    cc.run_pipeline(a, LEX, rounds=4)
    committed = cc.read_committed(a, g)
    print("INITIAL (terse)   :", repr(initial))
    print("COMMITTED (revised):", repr(committed["utterance"]))

    assert committed["committed"] is not None, "the monitor eventually clears a committed utterance"
    assert committed["utterance"] != initial, "the monitor REVISED before commit"
    assert committed["grounded_used"] is False, "revision fell back to the explicit fallback"
    assert len(committed["utterance"].split()) > len(initial.split()), "the revision is MORE explicit"
    assert "grey" in committed["utterance"], "the revision restates the ground no longer credited"
    # exactly one revision cycle: caught (False) then cleared (True).
    verdicts = [a.s.node(n)["attrs"] for n in a.s.nodes("Verdict")]
    assert sorted(v["recoverable"] for v in verdicts) == [False, True]
    assert a._donkey["n"] == 0


# ===========================================================================
# 4. NO REGRESSION of prior behaviour + RICH PROSE NOT DOWNGRADED.
# ===========================================================================
def test_no_regression_and_rich_prose_intact():
    a = _agent()
    # register-matched social surfaces + plain statement ack (AROUND the pipeline)
    assert a.converse("hello", "greeting") == "hello"
    assert a.converse("the sky is blue", "statement") == "noted"
    # honest fallbacks
    unans = a.converse("what is a borogove", "question")
    assert unans.lower().startswith("i don't") and "borogove" in unans
    # ask-back still asks, quoting the trouble source
    ask = a.converse("flar the glorp", "statement")
    assert ask.rstrip().endswith("?") and "flar" in ask
    # RICH SELF-MODEL PROSE not downgraded: the facts are present in fluent prose.
    rule = a.converse("Tell me about the rule hop_descend_gradient.", "question")
    assert "hop_descend_gradient" in rule
    assert len(rule.split()) >= 5, "fluent prose, not a bag of concept tokens"
    org = a.converse("How are you organised?", "question")
    assert "organis" in org.lower()
    assert a._donkey["n"] == 0


# ===========================================================================
# 5. NO PYTHON DECISION — the converse wiring calls the pipeline + reads back;
#    it does not branch on graph content to decide force / shape / recoverable.
# ===========================================================================
def _src(func):
    import inspect
    return inspect.getsource(func)


def test_no_python_decision_in_the_wiring():
    # the three wiring helpers on WorldAdapter + the describe concept-path bridge.
    wiring = "\n".join(_src(f) for f in (
        WorldAdapter._interlocutor_snapshot, WorldAdapter._content_concepts,
        WorldAdapter._form_reply_intent, WorldAdapter._form_reply_intent_for_text,
        ca._conceptualize_scene_lines))
    # the wiring NEVER computes the pipeline's decisions itself.
    assert "recoverable" not in wiring, "recoverability is the jabberwock's rules', never the wiring's"
    assert "perlocutionary_goal" not in wiring, "the perlocutionary goal is read from the ForceTemplate, never assigned here"
    # it never branches on the audience-design outcome to pick delivery — the conveyed
    # subset is read off the committed utterance the rules produced (membership test only).
    assert not re.search(r"if\b[^\n]*grounded_used", wiring)
    assert not re.search(r"if\b[^\n]*\bfocus\b", wiring)
    assert not re.search(r"if\b[^\n]*\bresidual\b", wiring)

    # the force each path forms is a CONSTANT string literal fixed by the reply's speech
    # act, not a value read from graph state.
    import inspect
    converse_src = inspect.getsource(WorldAdapter.converse)
    assert '_form_reply_intent_for_text("inform"' in converse_src
    assert '_form_reply_intent_for_text("answer"' in converse_src
    assert '_form_reply_intent_for_text("request"' in converse_src
    assert '_cc.conceptualize_reply(agent, "inform"' in _src(ca._conceptualize_scene_lines)
