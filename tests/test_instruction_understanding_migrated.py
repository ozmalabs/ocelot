"""Graph-native instruction understanding and graph-teacher learning.

The fixture deliberately supplies only external facts (a parsed instruction,
an observed local Concept match, or a teacher evidence record).  All choices --
hold/clarify, local verification, teacher tier, lesson staging, replay-gated
adoption, and goal activation -- are made by the seed's Rust-executed rules.
"""
from __future__ import annotations

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _fresh() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        manifest_for("instruction_understanding"), agent.agent)
    return agent


def _instruction(agent: WorldAdapter, *, predicate: str, content: str,
                 alternatives: int | None = None):
    attrs = {
        "from": "interlocutor",
        "comp_kind": "instruction",
        "comp_predicate": predicate,
        "comp_content": content,
    }
    if alternatives is not None:
        attrs["alternative_count"] = alternatives
    message = agent.s.add_node("Message", attrs)
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    # The lifecycle deliberately begins only for a predicate the graph already
    # recognises as an instruction route; unknown verbs retain the existing
    # instruction-gap path.  This is graph data, not a test-side classifier.
    predicate_mention = agent.s.add_node("Mention", {"text": predicate})
    predicate_concept = agent.s.add_node(
        "Concept", {"name": predicate, "instruction_route": "world_action"})
    agent.inner.add_edge_unchecked(message, "has_mention", predicate_mention)
    agent.inner.add_edge_unchecked(predicate_mention, "refers_to", predicate_concept)
    return message


def _attrs(agent: WorldAdapter, node_type: str):
    return [agent.s.node(n)["attrs"] for n in agent.s.nodes(node_type)]


def test_ambiguous_instruction_is_held_and_clarified_before_goal_activation():
    agent = _fresh()
    _instruction(agent, predicate="move", content="it", alternatives=2)
    agent.tick()

    interpretation = _attrs(agent, "InstructionInterpretation")
    assert len(interpretation) == 1
    assert interpretation[0]["status"] == "clarification_required"
    assert not _attrs(agent, "TeacherRequest")
    assert not _attrs(agent, "Goal"), "ambiguity must hold activation"
    replies = [a for a in _attrs(agent, "Message") if a.get("from") == "agent"]
    assert len(replies) == 1 and replies[0]["kind"] == "clarification"


def test_local_held_concept_verifies_without_any_llm_request():
    agent = _fresh()
    message = _instruction(agent, predicate="read", content="report")
    mention = agent.s.add_node("Mention", {"text": "report"})
    concept = agent.s.add_node("Concept", {"name": "report"})
    agent.inner.add_edge_unchecked(message, "has_mention", mention)
    agent.inner.add_edge_unchecked(mention, "refers_to", concept)
    agent.tick()

    assert _attrs(agent, "InstructionInterpretation")[0]["status"] == "verified"
    assert _attrs(agent, "UnderstandingCheck")[0]["status"] == "verified"
    assert not _attrs(agent, "TeacherRequest"), "held knowledge must win first"
    goals = _attrs(agent, "Goal")
    assert len(goals) == 1 and goals[0]["kind"] == "interpreted_instruction"
    metrics = _attrs(agent, "TeacherWeaningMetrics")[0]
    assert metrics["verified_without_llm"] == 1
    assert isinstance(metrics["verified_without_llm"], int)


def test_corrected_lesson_is_replayed_and_adopted_without_manual_replay_node():
    agent = _fresh()
    _instruction(agent, predicate="calibrate", content="sensor")
    agent.tick()
    request = list(agent.s.nodes("TeacherRequest"))[0]
    evidence = agent.s.add_node("TeacherEvidence", {
        "verdict": "corrected",
        "lesson_key": "sensor-calibration-relation",
        # This represents an untrusted transport field.  It must not be rendered.
        "teacher_prose": "This must never be sent to the user.",
    })
    proposal = agent.s.add_node("TeacherConceptCandidate", {
        "status": "proposed", "name": "sensor", "definition": "a calibrated sensor"})
    agent.inner.add_edge_unchecked(request, "has_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "proposes_concept", proposal)
    agent.tick()

    lesson = list(agent.s.nodes("LessonCandidate"))[0]
    concerns = _attrs(agent, "SelfConcern")
    assert len(concerns) == 1 and concerns[0]["status"] == "noted"
    assert concerns[0]["kind"] == "lesson_adoption"
    tasks = _attrs(agent, "CognitiveTask")
    assert any(t["kind"] == "teacher_lesson_replay" and
               t["status"] == "done" for t in tasks)
    replays = _attrs(agent, "LessonReplay")
    assert replays == [{"outcome": "passed",
                        "validation_kind": "aligned_teacher_proposal"}]

    assert agent.s.node(lesson)["attrs"]["status"] == "adopted"
    assert agent.s.node(proposal)["attrs"]["status"] == "adopted"
    assert proposal in agent.inner.neighbours(lesson, "tests_concept_proposal")
    assert _attrs(agent, "InstructionInterpretation")[0]["status"] == "verified"
    assert len(_attrs(agent, "Goal")) == 1
    metrics = _attrs(agent, "TeacherWeaningMetrics")[0]
    assert metrics["independent_replays"] == 1
    assert isinstance(metrics["independent_replays"], int)


def test_agent_originates_dictionary_question_from_its_own_residual():
    agent = _fresh()
    _instruction(agent, predicate="calibrate", content="novel apparatus")
    agent.tick()

    requests = _attrs(agent, "TeacherRequest")
    assert len(requests) == 1
    assert requests[0]["origin"] == "agent"
    assert requests[0]["teacher_tier"] == "dictionary"
    assert requests[0]["question_kind"] == "resolve_instruction_gap"
    tasks = _attrs(agent, "CognitiveTask")
    assert tasks[0]["kind"] == "instruction_understanding"
    assert tasks[0]["status"] == "awaiting_teacher"


def test_teacher_prose_never_becomes_an_outbound_message_and_tiers_are_ordered():
    agent = _fresh()
    _instruction(agent, predicate="repair", content="new mechanism")
    agent.tick()
    dictionary = list(agent.s.nodes("TeacherRequest"))[0]
    agent.inner.add_edge_unchecked(dictionary, "has_evidence", agent.s.add_node(
        "TeacherEvidence", {"verdict": "insufficient", "teacher_prose": "dictionary prose"}))
    agent.tick()
    wikipedia = [n for n in agent.s.nodes("TeacherRequest")
                 if agent.s.node(n)["attrs"].get("teacher_tier") == "wikipedia"][0]
    agent.inner.add_edge_unchecked(wikipedia, "has_evidence", agent.s.add_node(
        "TeacherEvidence", {"verdict": "unavailable", "teacher_prose": "wiki prose"}))
    agent.tick()

    tiers = [a["teacher_tier"] for a in _attrs(agent, "TeacherRequest")]
    assert tiers == ["dictionary", "wikipedia", "llm"]
    requests = _attrs(agent, "TeacherRequest")
    assert all(r["question_predicate"] == "repair" and
               r["question_content"] == "new mechanism" for r in requests)
    outbound = [a.get("text", "") for a in _attrs(agent, "Message")
                if a.get("from") == "agent"]
    assert all("prose" not in text for text in outbound)
    metrics = _attrs(agent, "TeacherWeaningMetrics")[0]
    assert metrics["llm_requests"] == 1 and isinstance(metrics["llm_requests"], int)


def test_mismatched_teacher_proposal_stops_at_a_bounded_graph_task():
    agent = _fresh()
    _instruction(agent, predicate="calibrate", content="sensor")
    agent.tick()
    request = list(agent.s.nodes("TeacherRequest"))[0]
    evidence = agent.s.add_node("TeacherEvidence", {"verdict": "supported"})
    proposal = agent.s.add_node("TeacherConceptCandidate", {
        "status": "proposed", "name": "unrelated", "definition": "not the held target"})
    agent.inner.add_edge_unchecked(request, "has_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "proposes_concept", proposal)
    agent.tick()

    lesson = _attrs(agent, "LessonCandidate")[0]
    assert lesson["status"] == "blocked"
    assert lesson["unresolved_reason"] == "no_aligned_teacher_proposal"
    assert _attrs(agent, "UnderstandingCheck")[0]["status"] == "replay_unavailable"
    replay_tasks = [t for t in _attrs(agent, "CognitiveTask")
                    if t["kind"] == "teacher_lesson_replay"]
    assert replay_tasks[0]["status"] == "blocked"
    assert not _attrs(agent, "Goal")


def test_full_boot_recognises_a_route_bearing_imperative_but_not_a_declarative():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse("Fix your grammar.",
                           speech_act=agent.classify_speech_act("Fix your grammar."))
    message = agent._last_turn_inbound
    attrs = agent.s.node(message)["attrs"]
    assert attrs["comp_kind"] == "instruction"
    assert attrs["comp_predicate"] == "fix"
    assert "self-concern" in reply.lower()
    assert _attrs(agent, "InstructionInterpretation")

    agent.converse("I fix grammar.",
                   speech_act=agent.classify_speech_act("I fix grammar."))
    declarative = agent.s.node(agent._last_turn_inbound)["attrs"]
    assert declarative["comp_kind"] == "statement"


def test_full_boot_hypothesises_unknown_initial_head_before_instruction_activation():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse("Calibrate the sensor.",
                           speech_act=agent.classify_speech_act("Calibrate the sensor."))
    request = [agent.s.node(n)["attrs"] for n in agent.s.nodes("TeacherRequest")
               if agent.s.node(n)["attrs"].get("question_kind") == "classify_instruction_head"]
    assert len(request) == 1
    assert request[0]["teacher_tier"] == "dictionary"
    assert request[0]["question_predicate"] == "calibrate"
    assert request[0]["question_content"] == "calibrate"
    assert request[0]["instruction_context"] == "Calibrate the sensor."
    message = agent.s.node(agent._last_turn_inbound)["attrs"]
    assert message["comp_kind"] == "statement", "a hypothesis is not activation"
    assert "checking" in reply.lower()
    assert reply.lower() != "noted"


def test_dictionary_verb_evidence_promotes_a_held_unknown_head_with_full_context():
    agent = _fresh()
    message = agent.s.add_node("Message", {
        "from": "interlocutor", "text": "Calibrate the sensor.", "comp_kind": "statement"})
    head = agent.s.add_node("Mention", {"text": "calibrate"})
    target = agent.s.add_node("Mention", {"text": "sensor"})
    sensor = agent.s.add_node("Concept", {"name": "sensor"})
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    agent.inner.add_edge_unchecked(message, "has_mention", head)
    agent.inner.add_edge_unchecked(message, "has_mention", target)
    agent.inner.add_edge_unchecked(head, "next_mention", target)
    agent.inner.add_edge_unchecked(target, "prev_mention", head)
    agent.inner.add_edge_unchecked(target, "refers_to", sensor)
    agent.tick()

    request = list(agent.s.nodes("TeacherRequest"))[0]
    evidence = agent.s.add_node("TeacherEvidence", {"verdict": "supported"})
    proposal = agent.s.add_node("TeacherConceptCandidate", {
        "status": "proposed", "name": "calibrate",
        "definition": "adjust precisely without relying on a POS word in this gloss"})
    category = agent.s.add_node("TeacherLexicalCategoryCandidate", {
        "status": "proposed", "lexeme": "calibrate", "category": "verb"})
    agent.inner.add_edge_unchecked(request, "has_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "proposes_concept", proposal)
    agent.inner.add_edge_unchecked(evidence, "proposes_lexical_category", category)
    agent.tick()

    attrs = agent.s.node(message)["attrs"]
    assert attrs["comp_kind"] == "instruction"
    assert attrs["comp_predicate"] == "calibrate"
    interpretation = _attrs(agent, "InstructionInterpretation")[0]
    assert interpretation["content"] == "Calibrate the sensor."
    assert interpretation["status"] == "verified"


def test_supervisory_weaning_removes_routine_llm_and_reopens_on_surprise_and_correction():
    agent = _fresh()
    metrics = list(agent.s.nodes("TeacherWeaningMetrics"))[0]
    agent.inner.set_attr(metrics, "independent_replays", 1)
    agent.tick()
    assert agent.s.node(metrics)["attrs"]["mode"] == "shadow"
    agent.inner.set_attr(metrics, "independent_replays", 2)
    agent.tick()
    assert agent.s.node(metrics)["attrs"]["mode"] == "surprise_only"
    agent.inner.set_attr(metrics, "independent_replays", 3)
    agent.tick()
    assert agent.s.node(metrics)["attrs"]["mode"] == "autonomous"

    _instruction(agent, predicate="repair", content="new mechanism")
    agent.tick()
    dictionary = list(agent.s.nodes("TeacherRequest"))[0]
    agent.inner.add_edge_unchecked(dictionary, "has_evidence", agent.s.add_node(
        "TeacherEvidence", {"verdict": "insufficient"}))
    agent.tick()
    wikipedia = [n for n in agent.s.nodes("TeacherRequest")
                 if agent.s.node(n)["attrs"].get("teacher_tier") == "wikipedia"][0]
    agent.inner.add_edge_unchecked(wikipedia, "has_evidence", agent.s.add_node(
        "TeacherEvidence", {"verdict": "unavailable"}))
    agent.tick()
    assert not [n for n in agent.s.nodes("TeacherRequest")
                if agent.s.node(n)["attrs"].get("teacher_tier") == "llm"]

    interpretation = list(agent.s.nodes("InstructionInterpretation"))[0]
    agent.inner.set_attr(interpretation, "surprise", 1)
    agent.tick()
    llm = [n for n in agent.s.nodes("TeacherRequest")
           if agent.s.node(n)["attrs"].get("teacher_tier") == "llm"]
    assert len(llm) == 1
    assert agent.s.node(llm[0])["attrs"]["blocking"] == 0
    assert agent.s.node(metrics)["attrs"]["mode"] == "surprise_only"

    agent.inner.add_edge_unchecked(llm[0], "has_evidence", agent.s.add_node(
        "TeacherEvidence", {"verdict": "corrected"}))
    agent.tick()
    assert agent.s.node(metrics)["attrs"]["mode"] == "blocking"
    assert agent.s.node(metrics)["attrs"]["llm_corrections"] == 1
