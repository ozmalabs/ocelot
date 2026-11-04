"""P20.04 sender→language→native receiver development panel."""
from __future__ import annotations

import json
import time

from domains.language_production import LanguageProduction
from domains.language_world import LanguageWorld, teacher_stub
from domains.process_explanation_language import (
    parse_ordered_explanation, produce_ordered_explanation,
)
from evaluation.process_mastery.explanation_rebuild import verify_rebuilt_composition
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.target_learning_worlds import WorldReceipt
from scripts.language_test import training_bank


class LoveSitWorld:
    """Independent ordered world with explicit preconditions and receipts."""

    family = "love_then_sit"

    def __init__(self, *, world_id, case_id, initial):
        self.world_id, self.case_id, self.state = world_id, case_id, initial
        self.epoch = 0
        self.receipts = []

    def apply(self, action):
        before = self.state
        if action == "love" and before == "idle":
            self.state = "loved"
        elif action == "sit" and before == "loved":
            self.state = "seated"
        else:
            raise ValueError(f"precondition_failed:{action}:{before}")
        self.epoch += 1
        receipt = WorldReceipt(
            f"{self.world_id}:{self.epoch}:{self.case_id}", self.case_id,
            "Composition", action, "state", before, self.state,
            "observed", True, self.epoch)
        self.receipts.append(receipt)
        return receipt

    @property
    def solved(self):
        return self.state == "seated"


def _settle(substrate, max_ticks):
    steps = 0
    for _ in range(max_ticks):
        count = substrate.tick(1000)
        steps += count
        if not count:
            break
    return steps


def _graph_bytes(substrate):
    return len(json.dumps([substrate.node(node) for node in substrate.nodes()],
                          sort_keys=True, default=str).encode())


def run_explanation_trial(index, *, stream_prefix="dev"):
    started = time.perf_counter()
    trial_id = f"{stream_prefix}:explanation:{index:04d}"
    bank = [row for row in training_bank() if row["language"] == "en"]
    source = Agent(extra_seeds=("process_explanation",), track_i=False,
                   policy_overrides={"ProcessExplanationPolicy": {"enabled": 1.0}},
                   budget={"enabled": 1.0, "remaining": 10.0,
                           "refill_per_epoch": 0.0, "last_refill_epoch": 0.0},
                   profile="p20-explanation-sender")
    steps = [
        {"precondition": "idle", "frame": {"event": "love", "agent": "Mary",
                                               "patient": "John", "tense": "present",
                                               "speech_act": "inform"}},
        {"precondition": "loved", "frame": {"event": "sit", "agent": "cat",
                                               "location": "mat", "tense": "past",
                                               "speech_act": "inform"}},
    ]
    source_schema = source.s.add_node("ProcessSchema", {
        "name": f"private-composed-source:{trial_id}", "kind": "sequence",
        "domain": "private-source", "params": ["seq", [["add", [1]], ["add", [1]]]],
        "status": "active", "source_epoch": 1, "model_epoch": 7, "frame_epoch": 9,
        "public_explanation_frame": None, "public_explanation_steps": steps,
        "public_vocabulary": ["love", "sit"],
    })
    source.s.add_edge(source.ag, "has_process_schema", source_schema, {})
    request_id = f"p20-explanation-author:{trial_id}"
    author = source.s.add_node("ProcessExplanationRequest", {
        "request_id": request_id, "status": "requested", "language": "en"})
    source.s.add_edge(source.ag, "has_process_explanation_request", author, {})
    source.s.add_edge(author, "explains_process", source_schema, {})
    author_funding = source.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_authoring", "source_key": request_id,
        "source_epoch": 1, "operation_id": request_id, "status": "pending", "cost": 1.0})
    source.s.add_edge(author, "funded_by", author_funding, {})
    source.s.add_edge(author_funding, "draws_on_thinking_budget",
                      source.s.neighbours(source.ag, "has_thinking_budget")[0], {})
    source_rule_steps = _settle(source.s, 24)
    drafts = source.s.nodes("ProcessExplanationDraft")
    if len(drafts) != 1:
        raise RuntimeError("native source did not create one funded public-step draft")
    draft_attrs = source.s.node(drafts[0])["attrs"]
    source_world = LanguageWorld(source.native, bank, teacher_stub)
    source_world.run()
    authored = produce_ordered_explanation(
        "en", draft_attrs["public_steps"], LanguageProduction(source_world))
    if authored.get("status") != "produced":
        raise RuntimeError(f"source explanation production failed: {authored}")

    receiver = Agent(extra_seeds=("process_explanation",), track_i=False,
                     policy_overrides={"ProcessExplanationPolicy": {"enabled": 1.0}},
                     budget={"enabled": 1.0, "remaining": 10.0,
                             "refill_per_epoch": 0.0, "last_refill_epoch": 0.0},
                     profile="p20-explanation-receiver")
    receiver_world = LanguageWorld(receiver.native, bank, teacher_stub)
    receiver_world.run()
    parsed = parse_ordered_explanation(
        authored["text"], "en", LanguageProduction(receiver_world))
    if parsed.get("parse_status") != "parsed":
        raise RuntimeError(f"receiver failed independent parse: {parsed}")
    primitives = []
    for event, precondition, token in zip(
            parsed["semantic_sequence"][1], parsed["required_preconditions"],
            authored["supported_vocabulary"]):
        primitive = receiver.s.add_node("ProcessPrimitiveVocabulary", {
            "primitive_id": f"shared:{index}:{event}", "semantic_event": event,
            "public_token": token, "precondition": precondition,
            "native_effect": ["finite_action", event], "vocabulary_status": "shared",
            "model_epoch": 8, "frame_epoch": 3,
        })
        receiver.s.add_edge(receiver.ag, "has_process_primitive_vocabulary", primitive, {})
        primitives.append(primitive)
    explanation_id = f"p20-explanation-receiver:{trial_id}"
    explanation = receiver.s.add_node("ProcessExplanationInput", {
        "explanation_id": explanation_id, "text": authored["text"], "language": "en",
        "parse_status": "parsed", "explanation_kind": "ordered_two_step",
        "semantic_sequence": parsed["semantic_sequence"],
        "required_preconditions": parsed["required_preconditions"],
        "supported_vocabulary": authored["supported_vocabulary"],
        "model_epoch": 8, "frame_epoch": 3,
    })
    receiver.s.add_edge(receiver.ag, "has_process_explanation_input", explanation, {})
    rebuild_request = receiver.s.add_node("ProcessExplanationRequest", {
        "explanation_id": explanation_id, "status": "requested"})
    receiver.s.add_edge(receiver.ag, "has_process_explanation_request", rebuild_request, {})
    rebuild_funding = receiver.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_rebuild", "explanation_id": explanation_id,
        "source_key": explanation_id, "source_epoch": 1,
        "operation_id": f"rebuild:{trial_id}", "status": "pending", "cost": 1.0})
    receiver.s.add_edge(rebuild_request, "funded_by", rebuild_funding, {})
    receiver.s.add_edge(rebuild_funding, "draws_on_thinking_budget",
                        receiver.s.nodes("ThinkingBudget")[0], {})
    receiver_rule_steps = _settle(receiver.s, 24)
    candidates = receiver.s.nodes("RebuiltProcessCandidate")
    if len(candidates) != 1:
        raise RuntimeError("receiver native reconstruction did not create one candidate")
    candidate = candidates[0]
    candidate_attrs = receiver.s.node(candidate)["attrs"]
    validation = receiver.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_rebuild_validation",
        "candidate_id": candidate_attrs["candidate_id"],
        "source_key": f"verify:{trial_id}", "source_epoch": 1,
        "operation_id": f"verify:{trial_id}", "status": "pending", "cost": 2.0})
    receiver.s.add_edge(candidate, "has_verification_request", validation, {})
    receiver.s.add_edge(validation, "draws_on_thinking_budget",
                        receiver.s.nodes("ThinkingBudget")[0], {})
    validation_rule_steps = _settle(receiver.s, 16)
    verification = verify_rebuilt_composition(
        receiver, candidate, world_factory=LoveSitWorld)
    adoption_steps = _settle(receiver.s, 16)
    adopted = [node for node in receiver.s.nodes("ProcessSchema")
               if receiver.s.node(node)["attrs"].get("provenance")
               == "rebuilt_from_explanation"]
    input_attrs = receiver.s.node(explanation)["attrs"]
    forbidden = {"source_schema_id", "source_actor_id", "source_process_id", "source_ast",
                 "params", "fingerprint", "source_fingerprint", "candidate_strategy",
                 "target_answer"}
    leakage = bool(forbidden.intersection(input_attrs))
    receipts = verification.get("world_receipts", [])
    fidelity = (verification.get("status") == "VERIFIED" and len(receipts) == 2
                and [row.action_kind for row in receipts] == ["love", "sit"]
                and [row.before_value for row in receipts] == ["idle", "loved"]
                and [row.after_value for row in receipts] == ["loved", "seated"]
                and verification.get("counterexample_rejected") is True)
    if not fidelity or len(adopted) != 1 or leakage:
        raise RuntimeError("P20.04 explanation failed fidelity, adoption or leakage check")
    source_budget = source.s.node(source.s.nodes("ThinkingBudget")[0])["attrs"]
    receiver_budget = receiver.s.node(receiver.s.nodes("ThinkingBudget")[0])["attrs"]
    source_debits = sum(source.s.node(node)["attrs"].get("debited_epoch") is not None
                        for node in source.s.nodes("ThinkingBudgetRequest"))
    receiver_debits = sum(receiver.s.node(node)["attrs"].get("debited_epoch") is not None
                          for node in receiver.s.nodes("ThinkingBudgetRequest"))
    return {
        "trial_id": trial_id, "status": "verified_and_adopted",
        "language": "en", "explanation_words": len(authored["text"].split()),
        "explanation_characters": len(authored["text"]),
        "semantic_steps": len(parsed["semantic_sequence"][1]),
        "required_preconditions": len(parsed["required_preconditions"]),
        "source_ast_included": draft_attrs.get("source_ast_included"),
        "receiver_source_leakage": leakage, "fidelity_match": fidelity,
        "counterexample_rejected": verification["counterexample_rejected"],
        "adopted_process_count": len(adopted),
        "fresh_world_actions": len(receipts), "counterexample_attempts": 1,
        "source_budget_debits": source_debits,
        "receiver_budget_debits": receiver_debits,
        "source_budget_remaining": source_budget.get("remaining"),
        "receiver_budget_remaining": receiver_budget.get("remaining"),
        "source_native_rule_steps": source_rule_steps,
        "receiver_native_rule_steps": receiver_rule_steps + validation_rule_steps + adoption_steps,
        "source_graph_nodes": len(source.s.nodes()),
        "receiver_graph_nodes": len(receiver.s.nodes()),
        "source_graph_bytes": _graph_bytes(source.s),
        "receiver_graph_bytes": _graph_bytes(receiver.s),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def run_development_panel(*, streams=2, stream_prefix="dev"):
    records = [run_explanation_trial(index, stream_prefix=stream_prefix)
               for index in range(streams)]
    return {
        "status": ("development_only" if stream_prefix == "dev"
                   else "heldout_unanalyzed"),
        "stream_prefix": stream_prefix, "streams": streams, "records": records,
        "summary": {
            "verified_and_adopted": sum(row["status"] == "verified_and_adopted"
                                         for row in records),
            "fidelity_rate": sum(row["fidelity_match"] for row in records) / streams,
            "mean_words": sum(row["explanation_words"] for row in records) / streams,
            "mean_total_budget_debits": sum(row["source_budget_debits"]
                                             + row["receiver_budget_debits"]
                                             for row in records) / streams,
            "mean_fresh_world_actions": sum(row["fresh_world_actions"] for row in records)
            / streams,
        },
    }
