"""Phase B1 -- the INSTRUCTION subsystem finds its own gaps, graph-natively.

No more silent instruction dead-ends: an instruction whose verb no rule covers
used to fall through every instruction rule (no Goal, no substantive reply --
just the generic honest floor). Now:

  * The adapter MECHANICALLY records what happened to an instruction turn
    (world_adapter._record_instruction_outcome -- the _answer_topic_reply
    outcome precedent): instruction_outcome='handled' iff some rule claimed
    the turn (the `comprehended` marker) or minted a Goal comprehending it,
    else 'unhandled'. A datum, never a decision.
  * The rule seeds/gap_awareness.json::note_unhandled_instruction_gap DECIDES
    an unhandled instruction is a capability gap: it files
    SelfConcern{status:'noted', source:'implicit', kind:'instruction',
    content:'<predicate> <content>'} (content-deduped + mint-once) and mints
    the honest in-turn reply naming what it understood.
  * VERBS ARE GRAPH DATA (comprehend_instruction v2.0.0 /
    conversation_self_concern v2.1.0 / conversation_self_reply v1.2.0): each
    covered verb is a held Concept{name:<verb>, instruction_route:<route>};
    the rules match the predicate Mention resolving (intent's
    rule_mention_resolves_to_concept) to a route-carrying Concept -- no
    in-body verb lists. Coverage is therefore teach-extensible at runtime:
    adding a Concept with an instruction_route routes a previously-unhandled
    verb with NO rule edit.
  * The orphaned self-report verbs (describe/tell/... -- previously only in
    the dead-code Python act_on_instruction) are re-homed: a REFLEXIVE
    self-report instruction ('describe yourself') answers from the held
    substrate identity (conversation_self_reply::instruction_self_report_identity).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _self_concerns(a, kind=None):
    out = []
    for sc in a.inner.neighbours(a.agent, "has_self_concern"):
        if not a.inner.has_node(sc):
            continue
        at = a.s.node(sc)["attrs"]
        if kind is None or at.get("kind") == kind:
            out.append(at)
    return out


def _goals_comprehending(a, mid):
    out = []
    for g in a.inner.neighbours(a.agent, "has_goal"):
        if not a.inner.has_node(g):
            continue
        if mid in list(a.inner.neighbours(g, "comprehends")):
            out.append(a.s.node(g)["attrs"])
    return out


def test_unhandled_instruction_files_a_gap_and_replies_honestly(agent):
    # No rule covers 'summarise' -> the adapter records instruction_outcome=
    # 'unhandled' (a datum), and the gap rule files EXACTLY ONE SelfConcern
    # naming what it understood + an honest in-turn reply -- never a silent
    # dead-end or the bare generic floor.
    reply = agent.converse("Summarise the report.", speech_act="request")
    mid = agent._last_turn_inbound
    at = agent.s.node(mid)["attrs"]
    assert at.get("comp_kind") == "instruction" and at.get("comp_predicate") == "summarise"
    assert at.get("instruction_outcome") == "unhandled", (
        "the adapter must mechanically record the unhandled outcome")
    assert isinstance(reply, str) and "instruction to summarise" in reply.lower() \
        and "filed it as a gap" in reply.lower(), (
        "the gap rule's honest reply must land in the SAME turn")
    gaps = [c for c in _self_concerns(agent, kind="instruction")
            if c.get("content") == "summarise report"]
    assert len(gaps) == 1, "exactly one instruction gap filed"
    assert gaps[0].get("status") == "noted" and gaps[0].get("source") == "implicit"


def test_resent_unhandled_instruction_dedups(agent):
    agent.converse("Summarise the report.", speech_act="request")
    agent.converse("Summarise the report.", speech_act="request")
    agent.comprehend()  # extra fixpoint must not duplicate either
    gaps = [c for c in _self_concerns(agent, kind="instruction")
            if c.get("content") == "summarise report"]
    assert len(gaps) == 1, "the content-dedup guard must file each distinct gap once"


def test_covered_read_instruction_is_handled_no_gap(agent):
    # 'read' routes via its Concept{instruction_route:'comprehend_text'} --
    # byte-parity with the pre-verbs-as-data reply -- and files NO gap.
    reply = agent.converse("Read this: The sky is blue.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "i read it and modeled it internally" in reply.lower()
    assert "the sky is blue" in reply.lower()
    assert not _self_concerns(agent, kind="instruction"), "a covered verb files no gap"


def test_covered_world_action_instruction_is_handled_no_gap(agent):
    # 'run' routes via its Concept{instruction_route:'world_action'} to the
    # SAME honest action-space-limit floor as before (parity), minting the
    # Goal{kind:instruction} with a comprehends edge; no gap.
    reply = agent.converse("Run the script.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "goal to run" in reply.lower() and "no world or faculty" in reply.lower()
    goals = _goals_comprehending(agent, mid)
    assert any(g.get("kind") == "instruction" and g.get("predicate") == "run"
               for g in goals)
    assert not _self_concerns(agent, kind="instruction"), "a covered verb files no gap"


def test_grounded_self_improvement_still_mints_concern_parity(agent):
    # PARITY: a self-improvement verb whose target resolves to a held Concept
    # still mints the human-gated SelfConcern{source:'conversation'} + the
    # confident reply (conversation_self_concern v2.1.0, verbs as data).
    agent._ensure_concept("grammar")   # the grounded target (mechanical find-or-create)
    reply = agent.converse("Fix your grammar.", speech_act="request")
    assert "self-concern" in reply.lower() and "review" in reply.lower()
    assert "grammar" in reply.lower()
    scs = [c for c in _self_concerns(agent)
           if c.get("kind") == "self_improvement" and c.get("source") == "conversation"]
    assert len(scs) == 1 and scs[0].get("status") == "noted"
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert not _self_concerns(agent, kind="instruction"), (
        "a handled self-improvement instruction must not ALSO file an "
        "unhandled-instruction gap")


def test_ungrounded_self_improvement_still_clarifies_parity(agent):
    # PARITY: an ungrounded target still asks for clarification and mints
    # NOTHING -- and clarification counts as handled (no spurious gap).
    before = len(list(agent.s.nodes("SelfConcern")))
    reply = agent.converse("Improve your florbnax.", speech_act="request")
    assert "sure i understand" in reply.lower() or "clarif" in reply.lower() \
        or "which part" in reply.lower()
    assert len(list(agent.s.nodes("SelfConcern"))) == before, (
        "an uncertain request must not file any concern/gap")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"


def test_taught_verb_concept_routes_without_rule_edit(agent):
    # VERBS AS DATA: teaching a Concept{name:'juggle',
    # instruction_route:'world_action'} makes a previously-unhandled verb
    # route through the UNCHANGED rules -- handled, no gap, the world-action
    # floor reply.
    reply0 = agent.converse("Juggle the plates.", speech_act="request")
    assert "filed it as a gap" in reply0.lower(), "before teaching: unhandled -> gap"
    agent.s.add_node("Concept", {"name": "juggle", "instruction_route": "world_action"})
    reply = agent.converse("Juggle the plates again.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "goal to juggle" in reply.lower() and "no world or faculty" in reply.lower()
    gaps = [c for c in _self_concerns(agent, kind="instruction")
            if "juggle" in str(c.get("content"))]
    assert len(gaps) == 1, "only the pre-teaching turn filed a gap"


def test_reflexive_self_report_instruction_answers_identity(agent):
    # Task-3 re-home: the orphaned self-report verbs answer a REFLEXIVE
    # instruction from the held substrate identity -- handled, no gap.
    reply = agent.converse("Describe yourself.", speech_act="request")
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("instruction_outcome") == "handled"
    assert "i am jabberwock" in reply.lower()
    goals = _goals_comprehending(agent, mid)
    assert any(g.get("kind") == "report_self" for g in goals)
    assert not _self_concerns(agent, kind="instruction")
