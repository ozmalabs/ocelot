"""Phase 1 of the graph-native conversation migration (plan: 'comprehend ->
mint goal -> reply, no Python ladder').

'read this: <text>' is comprehended and MODELED INTERNALLY (its content is
tokenized into Mention nodes at ingest -- reading inline text needs no external
world), and the agent's OWN graph rule (seeds/comprehend_instruction.json) mints
a Goal{kind:comprehend_text} + a realized reply -- NOT the Python
conversation_action.act_on_instruction 'no attached world/faculty' floor. This
gates the FIRST instruction case moved off the Python decision ladder onto a
graph rule, and that non-migrated turns (questions) still route unchanged
through the Python fallback.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

READ_TEXT = "Read this: The knight rode into the dark forest, afraid but resolute."


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _goals(a, kind=None):
    out = []
    for g in a.s.nodes("Goal"):
        at = a.s.node(g)["attrs"]
        if kind is None or at.get("kind") == kind:
            out.append((g, at))
    return out


def test_read_instruction_reply_is_graph_produced_not_the_floor(agent):
    reply = agent.converse(READ_TEXT, speech_act=agent.classify_speech_act(READ_TEXT))
    assert isinstance(reply, str) and reply.strip()
    assert "no attached world" not in reply.lower(), (
        "the Python act_on_instruction goal-only floor must NOT be reached -- "
        "the graph rule should have produced the reply")
    assert "modeled it internally" in reply.lower()
    # grounded in the extracted content (the internal model), not a bare ack
    assert "knight" in reply.lower()
    receipts = agent.production_turn_evidence(
        agent._last_turn_inbound)["production_gate_receipts"]
    assert any(
        receipt["status"] == "released"
        and receipt["attrs"].get("parse_back_mode")
        == "conversation_comprehend_text_graph"
        and receipt["attrs"].get("surface") == reply
        for receipt in receipts)


def test_read_instruction_mints_comprehend_goal_via_rule(agent):
    agent.converse(READ_TEXT, speech_act=agent.classify_speech_act(READ_TEXT))
    goals = _goals(agent, "comprehend_text")
    assert goals, "the graph rule must mint a Goal{kind:comprehend_text}"
    g, at = goals[-1]
    assert at.get("source") == "conversation"
    assert at.get("predicate") == "read"
    # the goal is hung on the agent and linked to the message it read
    assert g in set(agent.inner.neighbours(agent.agent, "has_goal"))
    assert list(agent.inner.neighbours(g, "comprehends")), \
        "the Goal must link to the Message it comprehended"


def test_inline_content_is_modeled_as_mentions(agent):
    agent.converse(READ_TEXT, speech_act=agent.classify_speech_act(READ_TEXT))
    mention_texts = {agent.s.node(n)["attrs"].get("text") for n in agent.s.nodes("Mention")}
    assert {"knight", "forest", "resolute"} <= mention_texts, (
        "the inline content must be modeled internally as Mention nodes at "
        "ingest -- no external reading world needed")


def test_question_still_answers_through_python_fallback_no_regression(agent):
    q = "what are you?"
    reply = agent.converse(q, speech_act=agent.classify_speech_act(q))
    assert isinstance(reply, str) and reply.strip()
    assert "no attached world" not in reply.lower()


def test_read_instruction_keeps_leading_head_across_content_commas():
    from domains.comprehend_text import comprehend_text

    comp = comprehend_text(
        None, "Read this: The knight rode into the dark forest, afraid but resolute.")
    assert comp.kind == "instruction"
    assert comp.dispatch["predicate"].lower() == "read"


# --- Phase 2: the honest world-action floor, now a graph rule -------------

def test_world_action_instruction_floors_via_graph_rule(agent):
    # A physical/world-action verb with no world attached: the SAME honest
    # action-space-limit reply act_on_instruction produced, now minted by the
    # graph rule (instruction_world_action_floor) -- proven graph-produced by
    # the Goal{kind:instruction} it mints with a `comprehends` edge to the
    # message (the Python _mint_goal never adds that edge).
    reply = agent.converse("Run the script.", speech_act="request")
    assert isinstance(reply, str) and reply.strip()
    assert "run" in reply.lower() and "no world or faculty" in reply.lower()
    assert "run the script" in reply.lower()
    receipts = agent.production_turn_evidence(
        agent._last_turn_inbound)["production_gate_receipts"]
    assert any(receipt["status"] == "released"
               and receipt["attrs"].get("parse_back_mode")
               == "conversation_instruction_graph"
               and receipt["attrs"].get("surface") == reply
               for receipt in receipts)
    # graph-rule signature: an instruction Goal linked by `comprehends`
    run_goals = [g for g in agent.s.nodes("Goal")
                 if agent.s.node(g)["attrs"].get("kind") == "instruction"
                 and agent.s.node(g)["attrs"].get("predicate") == "run"
                 and list(agent.inner.neighbours(g, "comprehends"))]
    assert run_goals, "the world-action floor Goal must be minted by the graph rule (with a comprehends edge)"


def test_grounded_standalone_instruction_selects_act_without_claiming_execution(agent):
    signal = "Check the pressure."
    before = set(agent.s.nodes("Goal"))
    reply = agent.converse(
        signal, speech_act="request",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"})
    inbound = agent._last_turn_inbound
    attrs = dict(agent.s.node(inbound)["attrs"])
    interpretation = attrs.get("communication_interpretation_id")
    assert interpretation is not None
    interpretation_attrs = agent.s.node(interpretation)["attrs"]
    assert interpretation_attrs.get("cognitive_disposition") == "act"
    assert interpretation_attrs.get("arbitration_basis") == (
        "standalone_grounded_action_request")
    goals = [goal for goal in agent.s.nodes("Goal")
             if goal not in before
             and agent.s.node(goal)["attrs"].get("kind")
             == "interpreted_instruction"
             and str(agent.s.node(goal)["attrs"].get("predicate", "")).lower()
             == "check"]
    assert goals, "the held route must preserve the recognized instruction goal"
    assert list(agent.inner.neighbours(goals[-1], "comprehends")) == [inbound]
    assert "no attached world" in reply.lower() or "no world" in reply.lower()
    assert "checked the pressure" not in reply.lower()


def test_standalone_temporally_deferred_instruction_stays_deferred(agent):
    reply = agent.converse(
        "When ready, check the pressure.", speech_act="request",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"})
    inbound = agent._last_turn_inbound
    attrs = dict(agent.s.node(inbound)["attrs"])
    interpretation = attrs.get("communication_interpretation_id")
    assert interpretation is not None
    assert agent.s.node(interpretation)["attrs"].get(
        "cognitive_disposition") == "defer"
    assert reply


def test_self_report_instruction_still_routes_through_python(agent):
    # 'tell' is a self-report verb, DISJOINT from the world-action set, so the
    # graph rules do not fire and the working Python self-report path answers
    # (no regression -- the substantive self-report faculty is not yet migrated).
    reply = agent.converse("Tell me about yourself.", speech_act="request")
    assert isinstance(reply, str) and reply.strip()
    assert "no world or faculty" not in reply.lower()
    assert "no attached world" not in reply.lower()


# --- Phase 3: chat -> self-improvement connection point (safe, gated) -----

def test_confident_self_improvement_instruction_files_a_self_concern_gated(agent):
    # CONFIDENT case: the request's target resolves to a held Concept (the
    # agent understood WHAT to work on), so a graph rule mints a
    # Goal{kind:self_improvement} + a first-class SelfConcern wired to the
    # agent -- the connection point into the self-improvement spine -- and
    # replies honestly. The SelfConcern is status 'noted', NOT 'pending', so
    # the daemon's _concern_tick does NOT auto-run the experiment/adopt loop.
    before = len(list(agent.s.nodes("SelfConcern")))
    reply = agent.converse("Fix your grammar.", speech_act="request")   # 'grammar' is a held Concept
    assert isinstance(reply, str) and reply.strip()
    assert "self-concern" in reply.lower() and "review" in reply.lower()
    assert "grammar" in reply.lower(), "the confident reply names the grounded target"
    receipts = agent.production_turn_evidence(
        agent._last_turn_inbound)["production_gate_receipts"]
    assert any(receipt["status"] == "released"
               and receipt["attrs"].get("parse_back_mode")
               == "conversation_instruction_graph"
               and receipt["attrs"].get("surface") == reply
               for receipt in receipts)

    scs = list(agent.s.nodes("SelfConcern"))
    assert len(scs) == before + 1, "a confident self-directed instruction must mint a SelfConcern"
    sc = scs[-1]
    at = agent.s.node(sc)["attrs"]
    assert at.get("status") == "noted", "GATED: must be 'noted', never auto-'pending'"
    assert at.get("source") == "conversation"
    assert sc in set(agent.inner.neighbours(agent.agent, "has_self_concern"))
    gs = list(agent.inner.neighbours(sc, "from_goal"))
    assert gs and agent.s.node(gs[0])["attrs"].get("kind") == "self_improvement"


def test_uncertain_self_improvement_instruction_asks_for_clarification(agent):
    # UNCERTAIN case: the request's target does NOT resolve to any held Concept
    # (the agent is not confident it understands the request), so it asks for
    # clarification and mints NOTHING -- exactly the 'ask otherwise' behaviour,
    # decided graph-natively from the agent's own referent resolution.
    before = len(list(agent.s.nodes("SelfConcern")))
    reply = agent.converse("Improve your florbnax.", speech_act="request")   # 'florbnax' is not held
    assert isinstance(reply, str) and reply.strip()
    assert "sure i understand" in reply.lower() or "clarif" in reply.lower() or "which part" in reply.lower(), \
        "an ungrounded request must ask for clarification"
    receipts = agent.production_turn_evidence(
        agent._last_turn_inbound)["production_gate_receipts"]
    assert any(receipt["status"] == "released"
               and receipt["attrs"].get("parse_back_mode")
               == "conversation_instruction_graph"
               and receipt["attrs"].get("surface") == reply
               for receipt in receipts)
    after = len(list(agent.s.nodes("SelfConcern")))
    assert after == before, "an uncertain request must NOT file a self-concern"


def test_self_concern_does_not_auto_run_experiment_loop(agent):
    # Safety: filing a (confident) self-concern must not, on its own, mint a
    # StandingConcern in the 'pending' state the daemon's _concern_tick picks up.
    agent.converse("Fix your grammar.", speech_act="request")
    pending_standing = [n for n in agent.s.nodes("StandingConcern")
                        if agent.s.node(n)["attrs"].get("status") == "pending"
                        and agent.s.node(n)["attrs"].get("source") == "conversation"]
    assert not pending_standing, "a chat self-concern must NOT auto-arm the experiment/adopt loop"
