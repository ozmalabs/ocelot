"""Bounded native reconstruction of two-step parsed explanations."""
from __future__ import annotations

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.explanation_rebuild import verify_rebuilt_composition
from evaluation.process_mastery.target_learning_worlds import WorldReceipt
from domains.language_production import LanguageProduction
from domains.language_world import LanguageWorld, teacher_stub
from domains.process_explanation_language import (parse_ordered_explanation,
                                                   produce_ordered_explanation)
from scripts.language_test import training_bank


def _receiver(*, events=("request", "repair"), preconditions=("idle", "requested"),
              vocabulary=("ask", "fix"), parse_status="parsed", text="Ask, then fix after the request."):
    receiver = Agent(extra_seeds=("process_explanation",),
                     policy_overrides={"ProcessExplanationPolicy": {"enabled": 1.0}},
                     budget={"enabled": 1.0, "remaining": 8.0,
                             "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    s, ag = receiver.s, receiver.ag
    primitives = []
    for event, precondition, token in zip(events, preconditions, vocabulary):
        primitive = s.add_node("ProcessPrimitiveVocabulary", {
            "primitive_id": f"shared-{event}", "semantic_event": event,
            "public_token": token, "precondition": precondition,
            "native_effect": ["finite_action", event],
            "vocabulary_status": "shared", "model_epoch": 8, "frame_epoch": 3})
        s.add_edge(ag, "has_process_primitive_vocabulary", primitive, {})
        primitives.append(primitive)
    explanation_id = "public-request-then-repair"
    explanation = s.add_node("ProcessExplanationInput", {
        "explanation_id": explanation_id, "text": text,
        "language": "en", "parse_status": parse_status,
        "explanation_kind": "ordered_two_step",
        "semantic_sequence": ["seq", list(events)],
        "required_preconditions": list(preconditions), "supported_vocabulary": list(vocabulary),
        "model_epoch": 8, "frame_epoch": 3,
    })
    s.add_edge(ag, "has_process_explanation_input", explanation, {})
    request = s.add_node("ProcessExplanationRequest", {
        "explanation_id": explanation_id, "status": "requested"})
    s.add_edge(ag, "has_process_explanation_request", request, {})
    funding = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_rebuild", "explanation_id": explanation_id,
        "source_key": explanation_id, "source_epoch": 1,
        "operation_id": f"rebuild:{explanation_id}", "status": "pending", "cost": 1.0})
    s.add_edge(request, "funded_by", funding, {})
    budget = list(s.neighbours(ag, "has_thinking_budget"))[0]
    s.add_edge(funding, "draws_on_thinking_budget", budget, {})
    for _ in range(24):
        if not s.tick(1000):
            break
    return receiver, explanation, request, primitives


def test_receiver_rebuilds_novel_composition():
    receiver, explanation, request, primitives = _receiver()
    s = receiver.s
    candidates = s.nodes("RebuiltProcessCandidate")
    assert len(candidates) == 1
    candidate = candidates[0]
    attrs = s.node(candidate)["attrs"]
    assert attrs["action_sequence"] == ["request", "repair"]
    assert attrs["required_preconditions"] == ["idle", "requested"]
    assert attrs["status"] == "unverified_candidate"
    assert set(s.neighbours(candidate, "uses_first_shared_primitive")) == {primitives[0]}
    assert set(s.neighbours(candidate, "uses_second_shared_primitive")) == {primitives[1]}
    assert s.neighbours(candidate, "from_explanation") == [explanation]
    assert s.node(request)["attrs"]["status"] == "candidate_created"


def test_source_ids_cannot_leak():
    receiver, explanation, _request, _primitives = _receiver()
    attrs = receiver.s.node(explanation)["attrs"]
    forbidden = {"source_schema_id", "source_actor_id", "source_process_id", "source_ast",
                 "params", "fingerprint", "candidate_strategy", "target_answer"}
    assert forbidden.isdisjoint(attrs)
    candidate = receiver.s.nodes("RebuiltProcessCandidate")[0]
    candidate_attrs = receiver.s.node(candidate)["attrs"]
    assert candidate_attrs["source_ast_included"] is False
    assert candidate_attrs["source_actor_id_included"] is False
    assert candidate_attrs["source_process_id_included"] is False
    assert candidate_attrs["source_fingerprint_included"] is False
    assert not receiver.s.nodes("ProcessSchema")


def test_missing_precondition_causes_unknown():
    receiver, _explanation, request, _primitives = _receiver(preconditions=("idle",))
    assert not receiver.s.nodes("RebuiltProcessCandidate")
    assert receiver.s.node(request)["attrs"]["status"] == "unknown_missing_precondition"


def test_unseen_world_effects_match():
    receiver, _explanation, _request, _primitives = _receiver()
    candidate = receiver.s.nodes("RebuiltProcessCandidate")[0]
    attrs = receiver.s.node(candidate)["attrs"]
    validation = receiver.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_rebuild_validation",
        "candidate_id": attrs["candidate_id"], "source_key": "fresh-rebuild-check",
        "source_epoch": 1, "operation_id": "validate:composition",
        "status": "pending", "cost": 2.0})
    receiver.s.add_edge(receiver.ag, "has_thinking_budget_request", validation, {})
    receiver.s.add_edge(candidate, "has_verification_request", validation, {})
    receiver.s.add_edge(validation, "draws_on_thinking_budget",
                        receiver.s.nodes("ThinkingBudget")[0], {})
    for _ in range(16):
        if not receiver.s.tick(1000):
            break
    assert receiver.s.node(validation)["attrs"]["status"] == "approved"
    assert receiver.s.node(validation)["attrs"]["debited_epoch"] is not None
    result = verify_rebuilt_composition(receiver, candidate)
    assert result["status"] == "VERIFIED"
    assert [r.after_value for r in result["world_receipts"]] == ["requested", "repaired"]
    assert result["counterexample_rejected"] is True
    assert receiver.s.node(candidate)["attrs"]["status"] == "adopted"
    schemas = [n for n in receiver.s.nodes("ProcessSchema")
               if receiver.s.node(n)["attrs"].get("provenance") == "rebuilt_from_explanation"]
    assert len(schemas) == 1
    assert receiver.s.node(schemas[0])["attrs"]["params"] == ["seq", ["request", "repair"]]


class _LoveSitWorld:
    def __init__(self, *, world_id, case_id, initial):
        self.world_id, self.case_id, self.state = world_id, case_id, initial
        self.receipts = []

    def apply(self, action):
        before = self.state
        if action == "love" and before == "idle":
            self.state = "loved"
        elif action == "sit" and before == "loved":
            self.state = "seated"
        else:
            raise ValueError("precondition_failed")
        item = WorldReceipt(f"{self.world_id}:{len(self.receipts) + 1}", self.case_id,
                            "Composition", action, "state", before, self.state,
                            "observed", True, len(self.receipts) + 1)
        self.receipts.append(item)
        return item

    @property
    def solved(self):
        return self.state == "seated"


def test_receiver_rebuilds_language_produced_composition():
    bank = [row for row in training_bank() if row["language"] == "en"]
    source = Agent()
    source_world = LanguageWorld(source.native, bank, teacher_stub)
    source_world.run()
    source_production = LanguageProduction(source_world)
    authored = produce_ordered_explanation("en", [
        {"precondition": "idle", "frame": {"event": "love", "agent": "Mary",
                                             "patient": "John", "tense": "present",
                                             "speech_act": "inform"}},
        {"precondition": "loved", "frame": {"event": "sit", "agent": "cat",
                                             "location": "mat", "tense": "past",
                                             "speech_act": "inform"}},
    ], source_production)
    assert authored["status"] == "produced"
    receiver_agent = Agent()
    receiver_world = LanguageWorld(receiver_agent.native, bank, teacher_stub)
    receiver_world.run()
    parsed = parse_ordered_explanation(
        authored["text"], "en", LanguageProduction(receiver_world))
    assert parsed["parse_status"] == "parsed"
    assert parsed["semantic_sequence"] == ["seq", ["love", "sit"]]
    receiver, explanation, _request, primitives = _receiver(
        events=tuple(parsed["semantic_sequence"][1]),
        preconditions=tuple(parsed["required_preconditions"]),
        vocabulary=("love", "sit"), text=authored["text"])
    attrs = receiver.s.node(explanation)["attrs"]
    assert attrs["text"] == authored["text"]
    assert {"source_ast", "source_schema_id", "source_process_id"}.isdisjoint(attrs)
    candidate = receiver.s.nodes("RebuiltProcessCandidate")[0]
    validation = receiver.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_rebuild_validation",
        "candidate_id": receiver.s.node(candidate)["attrs"]["candidate_id"],
        "source_key": "language-fresh-verification", "source_epoch": 1,
        "operation_id": "verify:language-composition", "status": "pending", "cost": 2.0})
    receiver.s.add_edge(receiver.ag, "has_thinking_budget_request", validation, {})
    receiver.s.add_edge(candidate, "has_verification_request", validation, {})
    receiver.s.add_edge(validation, "draws_on_thinking_budget",
                        receiver.s.nodes("ThinkingBudget")[0], {})
    for _ in range(16):
        if not receiver.s.tick(1000):
            break
    result = verify_rebuilt_composition(receiver, candidate, world_factory=_LoveSitWorld)
    assert result["status"] == "VERIFIED"
    assert receiver.s.node(candidate)["attrs"]["status"] == "adopted"
    assert [frame["event"] for frame in parsed["semantic_frames"]] == ["love", "sit"]

