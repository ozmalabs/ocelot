"""P12.04 monitored language explanation and isolated native rebuild fixtures."""
from __future__ import annotations

import pytest

from evaluation.process_mastery.harness import Agent
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank


def _tick(agent, n=20):
    for _ in range(n):
        agent.s.tick(1000)


@pytest.fixture(scope="module")
def public_explanation():
    source = Agent(extra_seeds=("process_explanation",),
                   policy_overrides={"ProcessExplanationPolicy": {"enabled": 1.0}},
                   budget={"enabled": 1.0, "remaining": 8.0,
                           "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    world = LanguageWorld(source.native,
                          [row for row in training_bank() if row["language"] == "en"],
                          teacher_stub)
    world.run()
    source_schema = source.s.add_node("ProcessSchema", {
        "name": "private-source-schema", "kind": "sequence", "domain": "private-source",
        "operator": "love", "params": ["seq", ["add", [1]]],
        "public_explanation_frame": {"event": "love", "agent": "Mary",
                                     "patient": "John", "tense": "present",
                                     "speech_act": "inform"},
        "public_vocabulary": ["love", "Mary", "John", "primitive-love"],
        "source_epoch": 1, "model_epoch": 8, "frame_epoch": 3, "status": "active"})
    source.s.add_edge(source.ag, "has_process_schema", source_schema, {})
    explanation_request = source.s.add_node("ProcessExplanationRequest", {
        "request_id": "explain-request-1", "status": "requested", "language": "en"})
    source.s.add_edge(source.ag, "has_process_explanation_request", explanation_request, {})
    source.s.add_edge(explanation_request, "explains_process", source_schema, {})
    funding = source.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_authoring", "source_key": "explain-request-1",
        "source_epoch": 1, "operation_id": "explain:source:1", "status": "pending", "cost": 1.0})
    source.s.add_edge(explanation_request, "funded_by", funding, {})
    budget = list(source.s.neighbours(source.ag, "has_thinking_budget"))[0]
    source.s.add_edge(funding, "draws_on_thinking_budget", budget, {})
    _tick(source)
    drafts = list(source.s.nodes("ProcessExplanationDraft"))
    assert len(drafts) == 1
    draft = source.s.node(drafts[0])["attrs"]
    produced = LanguageProduction(world).produce("en", draft["public_frame"])
    assert produced["accepted"] and produced["self_monitor"]["match"]
    recovered = LanguageProduction(world)._comprehend("en", produced["overt_speech"])
    assert recovered["event"] == "love"
    return {
        "explanation_id": "public-love-explanation",
        "text": produced["overt_speech"],
        "language": "en",
        "vocabulary": list(draft["supported_vocabulary"]),
        "semantic_frame": recovered,
        "production_receipt": {"accepted": produced["accepted"],
                               "self_monitor_match": produced["self_monitor"]["match"],
                               "recovered_frame": recovered},
    }


def _receiver(packet, *, parse_status="parsed"):
    receiver = Agent(extra_seeds=("process_explanation",),
                     policy_overrides={"ProcessExplanationPolicy": {"enabled": 1.0}},
                     budget={"enabled": 1.0, "remaining": 8.0,
                             "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    s, ag = receiver.s, receiver.ag
    # Only a language-level primitive is shared; no source process or trace is
    # installed in the receiver graph.
    primitive = s.add_node("ProcessPrimitiveVocabulary", {
        "primitive_id": "primitive-love", "semantic_event": "love",
        "public_token": "primitive-love",
        "native_effect": ["seq", ["add", [1]]], "vocabulary_status": "shared",
        "model_epoch": 8, "frame_epoch": 3})
    s.add_edge(ag, "has_process_primitive_vocabulary", primitive, {})
    semantic = packet["semantic_frame"]
    explanation_input = s.add_node("ProcessExplanationInput", {
        "explanation_id": packet["explanation_id"], "text": packet["text"],
        "language": packet["language"], "parse_status": parse_status,
        "semantic_event": semantic.get("event"),
        "supported_vocabulary": packet["vocabulary"],
        "model_epoch": 8, "frame_epoch": 3})
    s.add_edge(ag, "has_process_explanation_input", explanation_input, {})
    request = s.add_node("ProcessExplanationRequest", {
        "explanation_id": packet["explanation_id"], "status": "requested"})
    s.add_edge(ag, "has_process_explanation_request", request, {})
    funding = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_rebuild",
        "explanation_id": packet["explanation_id"], "source_key": packet["explanation_id"],
        "source_epoch": 1, "operation_id": f"rebuild:{packet['explanation_id']}",
        "status": "pending", "cost": 1.0})
    s.add_edge(request, "funded_by", funding, {})
    budget = list(s.neighbours(ag, "has_thinking_budget"))[0]
    s.add_edge(funding, "draws_on_thinking_budget", budget, {})
    _tick(receiver)
    return receiver, explanation_input, request


def _verify_rebuild(receiver, candidate):
    s = receiver.s
    attrs = s.node(candidate)["attrs"]
    request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_rebuild_validation", "candidate_id": attrs["candidate_id"],
        "source_key": f"verify:{attrs['candidate_id']}", "source_epoch": 1,
        "operation_id": f"verify:{attrs['candidate_id']}", "status": "pending", "cost": 1.0})
    s.add_edge(candidate, "has_verification_request", request, {})
    budget = list(s.neighbours(receiver.ag, "has_thinking_budget"))[0]
    s.add_edge(request, "draws_on_thinking_budget", budget, {})
    term = {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
            "state": {"type": "Var", "name": "state"}}
    exact = all(receiver.native.evaluate(term, {"p": attrs["params"], "state": state}) == [x + 1]
                for state, x in (([0], 0), ([3], 3), ([-2], -2)))
    receipt = s.add_node("RebuildVerification", {
        "candidate_id": attrs["candidate_id"], "verification_kind": "fresh_native_rebuild",
        "status": "verified" if exact else "failed", "exact_effect_match": exact,
        "model_epoch": attrs["model_epoch"], "frame_epoch": attrs["frame_epoch"],
        "probe_count": 3, "receipt_id": f"rebuild-receipt:{attrs['candidate_id']}"})
    s.add_edge(candidate, "has_rebuild_verification", receipt, {})
    _tick(receiver)
    return exact


def test_rebuild_from_explanation_only(public_explanation):
    receiver, _input, _request = _receiver(public_explanation)
    candidates = list(receiver.s.nodes("RebuiltProcessCandidate"))
    assert len(candidates) == 1
    assert _verify_rebuild(receiver, candidates[0])
    rebuilt = [n for n in receiver.s.nodes("ProcessSchema")
               if receiver.s.node(n)["attrs"].get("provenance") == "rebuilt_from_explanation"]
    assert len(rebuilt) == 1
    assert receiver.s.node(rebuilt[0])["attrs"]["params"] == ["seq", ["add", [1]]]
    assert not [n for n in receiver.s.nodes("ProcessSchema")
                if receiver.s.node(n)["attrs"].get("name") == "private-source-schema"]


def test_source_ast_not_visible(public_explanation):
    receiver, explanation_input, _request = _receiver(public_explanation)
    packet = public_explanation
    assert packet["production_receipt"]["accepted"] is True
    assert packet["production_receipt"]["self_monitor_match"] is True
    assert packet["text"] == "Mary loves John."
    assert set(packet) == {"explanation_id", "text", "language", "vocabulary",
                           "semantic_frame", "production_receipt"}
    attrs = receiver.s.node(explanation_input)["attrs"]
    forbidden = {"source_schema_id", "source_actor_id", "source_process_id", "source_ast",
                 "params", "fingerprint", "candidate_strategy", "target_answer"}
    assert forbidden.isdisjoint(attrs)
    assert not receiver.s.nodes("ProcessSchema")


def test_ambiguous_explanation_abstains(public_explanation):
    receiver, _input, request = _receiver(public_explanation, parse_status="ambiguous")
    assert not receiver.s.nodes("RebuiltProcessCandidate")
    assert receiver.s.node(request)["attrs"]["status"] == "abstained_ambiguous"


def test_second_agent_rebuilds_novel_process(public_explanation):
    receiver, explanation_input, _request = _receiver(public_explanation)
    assert not receiver.s.nodes("ProcessSchema")
    assert len(receiver.s.nodes("ProcessPrimitiveVocabulary")) == 1
    candidate = receiver.s.nodes("RebuiltProcessCandidate")[0]
    assert _verify_rebuild(receiver, candidate)
    schemas = [n for n in receiver.s.nodes("ProcessSchema")
               if receiver.s.node(n)["attrs"].get("provenance") == "rebuilt_from_explanation"]
    assert len(schemas) == 1
    assert schemas[0] in receiver.s.neighbours(receiver.ag, "has_process_schema")
    assert receiver.s.node(explanation_input)["attrs"]["text"] == public_explanation["text"]
