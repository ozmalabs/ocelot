"""test_conversation_loop — the COMPLETE conversational turn on the live converse
loop: the jabberwock ANSWERS a question, ACTS on an instruction (a conversation
drives a goal -> it does something it chose), and ASKS BACK on a comprehension
gap (a repair first-pair-part), instead of the old answer-or-acknowledge only.

The pieces already existed (comprehend_text, the self-model reflect, the self-
built describe faculty, the adjacency-pair repair vocabulary); this gates that
`WorldAdapter.converse` now WIRES them into one path via
`domains/conversation_action.py`. Every assertion drives the REAL converse loop.
donkey=0 throughout — the CONTENT is the agent's own faculties, not host prose.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import conversation_action as ca


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("I heard you.", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


@pytest.fixture(scope="module")
def agent():
    return _agent()


def _goals(a, kind):
    return [g for g in a.s.nodes("Goal")
            if a.inner.has_node(g) and a.s.node(g)["attrs"].get("kind") == kind]


def test_concept_name_index_tracks_late_additions_and_preserves_first_match(agent):
    name = "phase7_late_cache_probe"
    assert agent._concept_by_name(name) is None
    assert agent._concept_name_index_ready is True
    first = agent.s.add_node("Concept", {"name": name})
    assert agent._concept_by_name(name) == first

    duplicate = agent.s.add_node("Concept", {"name": name})
    assert agent._concept_by_name(name) == first
    assert duplicate != first


# ---------------------------------------------------------------------------
# REGRESSION — the existing converse behaviour is untouched.
# ---------------------------------------------------------------------------

def test_greeting_round_trip(agent):
    assert agent.converse("hello", "greeting") == "hello"


def test_statement_acknowledged(agent):
    assert agent.converse("the sky is blue", "statement") == \
        "ERROR: no communicative response could be generated."


def test_answer_is_terminal(agent):
    # A received answer has no second-pair-part. The dead-end is explicit and
    # diagnostic, never disguised as a dismissive register acknowledgement.
    reply = agent.converse("it is blue", "answer")
    assert reply == "ERROR: no communicative response could be generated."


# ---------------------------------------------------------------------------
# QUESTION — still answers in prose (unchanged path).
# ---------------------------------------------------------------------------

def test_question_still_answers(agent):
    ans = agent.converse("How are you organised?", "question")
    assert isinstance(ans, str) and "organis" in ans.lower()
    assert ans.strip().lower() not in ("noted", "acknowledgment")
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    commitment = trace["answer_commitment"]
    assert commitment["kind"] == "supported_event_bound_reflective_answer"
    assert commitment["graph_linked_to_turn"] is True
    assert commitment["faculty"] == "self_organisation"
    assert commitment["production_receipt_id"] == \
        trace["production_release"]["receipt_id"]
    assert trace["production_release"]["parse_back_mode"] == \
        "conversation_reflective_self_organisation_graph"
    assert trace["reply"] == ans
    assert trace["reply_from"] == "agent"
    assert trace["reply_id"] == commitment["message_id"]


def test_non_turn_fragment_trace_preserves_deliberate_silence(agent):
    reply = agent.converse(
        "Please—", "instruction",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    assert reply == ""
    assert trace["reply"] == ""
    assert trace["reply_id"] is None


def test_world_question_still_answers(agent):
    ans = agent.converse("Tell me about the rule hop_descend_gradient.", "question")
    assert isinstance(ans, str) and "hop_descend_gradient" in ans
    mid = agent._last_turn_inbound
    interpretation_id = agent.s.node(mid)["attrs"][
        "communication_interpretation_id"]
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation["selected_reflective_faculty"] == "self_model_rule"
    assert interpretation["cognitive_disposition"] == "answer"
    assert interpretation["arbitration_basis"] == \
        "supported_reflective_faculty_answer"
    assert interpretation["grounding_evidence_path"] == \
        "CommunicationInterpretation -> selected_graph_faculty"
    assert interpretation["reflective_answer_evidence_path"] == \
        "CommunicationInterpretation -> ReflectiveAnswerEvidence -> RuleSummary"
    evidence = [node for node in agent.inner.neighbours(
        interpretation_id, "has_reflective_answer_evidence")
        if agent.s.has_node(node)
        and agent.s.node(node)["attrs"].get("faculty") == "self_model_rule"]
    assert len(evidence) == 1
    evidence = evidence[0]
    evidence_attrs = agent.s.node(evidence)["attrs"]
    assert evidence_attrs["status"] == "supported"
    assert evidence_attrs["query"] == "hop_descend_gradient"
    summaries = agent.inner.neighbours(evidence, "supported_by")
    assert evidence_attrs["summary_count"] == len(summaries)
    assert summaries
    assert all(agent.s.node(node)["type"] == "RuleSummary"
               for node in summaries)
    assert any(agent.s.node(node)["attrs"].get("name")
               == "hop_descend_gradient" for node in summaries)
    assert agent._native_reflective_answer_selected(mid)
    assert any(
        mid in agent.responds_to(reply)
        and agent.s.node(reply)["attrs"].get(
            "native_reflective_answer_plan") == "self_model_rule"
        for reply in agent.agent_outbound_messages())
    assert any(
        agent.s.node(receipt)["attrs"].get("status") == "released"
        and agent.s.node(receipt)["attrs"].get("turn_message_id")
        == int(mid.value)
        and agent.s.node(receipt)["attrs"].get("parse_back_mode")
        == "conversation_reflective_self_model_rule_graph"
        and any(
            agent.s.node(reply)["attrs"].get(
                "native_reflective_answer_plan") == "self_model_rule"
            for reply in agent.inner.neighbours(receipt, "releases"))
        for receipt in agent.s.nodes("ProductionGateReceipt"))


# ---------------------------------------------------------------------------
# ACT — an instruction drives a goal -> the agent DOES something (self-report).
# ---------------------------------------------------------------------------

def test_act_self_report_mints_goal_and_produces(agent):
    before = len(_goals(agent, "report_self"))
    reply = agent.converse("report your organisation", "statement")
    assert isinstance(reply, str) and "organis" in reply.lower()
    assert reply.strip().lower() not in ("noted", "acknowledgment")
    # the ACTION happened: a report_self Goal was minted (graph evidence).
    assert len(_goals(agent, "report_self")) == before + 1


def test_act_tell_about_yourself(agent):
    reply = agent.converse("tell me about yourself", "question")
    assert isinstance(reply, str) and reply.strip()
    assert reply.strip().lower() not in ("noted", "acknowledgment")
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    assert any(goal.get("event_bound") and goal.get("kind") == "report_self"
               for goal in trace["goals"]), (
        "the reflexive self-report must be selected by its graph route, not by "
        "the legacy object parse ('me')")


# ---------------------------------------------------------------------------
# ACT — describe an ATTACHED scene via the self-built describe faculty.
# ---------------------------------------------------------------------------

def test_act_describe_scene(agent):
    ca.attach_scene(agent, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False}])
    reply = agent.converse("describe what you see", "statement")
    assert isinstance(reply, str) and reply.strip()
    assert reply.strip().lower() not in ("noted", "acknowledgment")
    # the agent's OWN authored rule minted a describe_scene Goal + produced text.
    assert _goals(agent, "describe_scene")
    assert len(reply.split()) >= 3          # produced multiple utterances, not a canned token


# ---------------------------------------------------------------------------
# ASK-BACK — a comprehension gap -> the agent ASKS, not acknowledges.
# ---------------------------------------------------------------------------

def test_ask_back_on_gap(agent):
    reply = agent.converse("quorplezap the door", "statement")
    assert isinstance(reply, str)
    assert "quorplezap" in reply            # quotes the real trouble source
    assert reply.rstrip().endswith("?")     # it ASKED
    assert reply.strip().lower() not in ("noted", "acknowledgment")


def test_ask_back_is_not_a_fabricated_answer(agent):
    # discriminative: the gap is NOT answered with invented content — the reply
    # is a repair question, and a clarification first-pair-part is recorded.
    reply = agent.converse("flar the glorp", "statement")
    assert reply.rstrip().endswith("?") and "flar" in reply
    clar = [m for m in agent.s.nodes("Message")
            if agent.s.node(m)["attrs"].get("from") == "agent"
            and agent.s.node(m)["attrs"].get("trouble_source")]
    assert clar, "expected a recorded clarification (repair) first-pair-part"
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    commitment = trace["reply_commitment"]
    assert commitment["graph_linked_to_turn"] is True
    assert commitment["expects_response"] is True
    assert commitment["speech_acts"] == ["clarification"]
    assert commitment["trouble_source"] == "flar"
    assert commitment["message_id"]


# ---------------------------------------------------------------------------
# The three behaviours are DISCRIMINATED, and it stays donkey=0.
# ---------------------------------------------------------------------------

def test_three_behaviours_discriminated(agent):
    q = agent.converse("How are you organised?", "question")          # ANSWER
    act = agent.converse("report your organisation", "statement")     # ACT
    act_trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    assert any(goal.get("event_bound") and goal.get("kind") == "report_self"
               for goal in act_trace["goals"])
    ask = agent.converse("blorptangle the widget", "statement")       # ASK-BACK
    assert "organis" in q.lower()
    assert act and act.strip().lower() not in ("noted",)
    assert ask.rstrip().endswith("?") and "blorptangle" in ask
    # ask-back is not an answer; answer is not a question.
    assert not q.rstrip().endswith("?")


def test_donkey_zero(agent):
    # every turn above ran without a single self-teacher (LLM) call.
    assert agent._donkey["n"] == 0
