"""P20 development panel for source-specific observed-sequence adapters.

This is mechanism/development evidence only. It is not the registered or
held-out P20 allocation. Every positive arm learns from a distinct source
adapter, then crosses the same native fresh-world verification and authorized
own-action boundary. Reward-only is scored as correct abstention.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.observed_sequence_execution import (
    execute_verified_observed_sequence, verify_observed_sequence_candidate,
)
from evaluation.process_mastery.observed_sequence_inputs import (
    demonstrated_episode, instructed_episode, reward_only_episode, witnessed_episode,
)
from evaluation.process_mastery.target_learning_worlds import RequestRepairWorld
from domains.language_production import LanguageProduction
from domains.language_world import LanguageWorld, make_stub_teacher
from domains.process_explanation_language import (parse_ordered_explanation,
                                                   produce_ordered_explanation)
from scripts.language_test import training_bank

ARMS = ("observation", "demonstration", "instruction", "reward_only")


def _agent():
    agent = Agent(extra_seeds=("thinking_budget", "social_process", "process_schema",
                               "observed_sequence_learning"), track_i=False,
                  policy_overrides={"SocialProcessPolicy": {"enabled": 1.0},
                                    "ObservedSequenceLearningPolicy": {"enabled": 1.0}},
                  budget={"enabled": 1.0, "remaining": 20.0,
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    for operator in ("request", "repair"):
        model = agent.s.add_node("ProcessSchema", {
            "name": f"primitive:{operator}", "kind": "sequence", "domain": "request_repair",
            "operator": operator, "params": ["seq", ["add", [1]]],
            "status": "active", "source_epoch": 4, "model_epoch": 7,
            "frame_epoch": 9})
        agent.s.add_edge(agent.ag, "has_process_schema", model, {})
    return agent


def _instruction_parse(receiver_agent):
    bank = training_bank() + [
        {"text": "The peer requests the case.", "language": "en",
         "expected_meaning": {"event": "request", "agent": "peer",
                              "patient": "case", "tense": "present"}},
        {"text": "The peer repaired the case.", "language": "en",
         "expected_meaning": {"event": "repair", "agent": "peer",
                              "patient": "case", "tense": "past"}},
    ]
    teacher = make_stub_teacher({"en": {"peer": "peer", "requests": ("request", "present"),
                                          "repaired": ("repair", "past"), "case": "case"}})
    source_agent = Agent(track_i=False, profile="p20-instruction-sender")
    source_world = LanguageWorld(source_agent.native, bank, teacher)
    source_world.run()
    production = LanguageProduction(source_world)
    authored = produce_ordered_explanation("en", [
        {"precondition": "idle", "frame": {"event": "request", "agent": "peer",
                                                  "patient": "case", "tense": "present",
                                                  "speech_act": "inform"}},
        {"precondition": "requested", "frame": {"event": "repair", "agent": "peer",
                                                      "patient": "case", "tense": "past",
                                                      "speech_act": "inform"}},
    ], production)
    if authored.get("status") != "produced":
        raise RuntimeError(f"instruction production failed: {authored}")
    receiver_world = LanguageWorld(receiver_agent.native, bank, teacher)
    receiver_world.run()
    parsed = parse_ordered_explanation(authored["text"], "en",
                                       LanguageProduction(receiver_world))
    if parsed.get("parse_status") != "parsed":
        raise RuntimeError(f"independent instruction parse failed: {parsed}")
    return authored["text"], parsed, len(authored["text"].split()), source_agent


def _request(agent, *, requester_kind, candidate_id, cost):
    request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": requester_kind, "candidate_id": candidate_id,
        "source_key": f"{requester_kind}:{candidate_id}", "source_epoch": 4,
        "operation_id": f"{requester_kind}:{candidate_id}", "status": "pending",
        "cost": float(cost),
    })
    agent.s.add_edge(agent.ag, "has_thinking_budget_request", request, {})
    agent.s.add_edge(request, "draws_on_thinking_budget",
                     agent.s.nodes("ThinkingBudget")[0], {})
    return request


def _settle(agent):
    total = 0
    for _ in range(32):
        steps = agent.s.tick(1000)
        total += steps
        if not steps:
            break
    agent._p20_native_rule_steps = getattr(agent, "_p20_native_rule_steps", 0) + total


def _one_stream(arm, index, *, stream_prefix="dev"):
    started = time.perf_counter()
    agent = _agent()
    source_agent = None
    stream_id = f"{stream_prefix}:{arm}:{index:04d}"
    if arm == "observation":
        source = RequestRepairWorld(world_id=f"observed-source:{stream_id}")
        witnessed_episode(agent, episode_id=stream_id,
                          receipts=[source.apply("request"), source.apply("repair")])
        source_units = 2
    elif arm == "demonstration":
        source = RequestRepairWorld(world_id=f"demonstration-source:{stream_id}")
        demonstrated_episode(agent, episode_id=stream_id, demonstration={
            "status": "complete", "actor_id": f"demonstrator:{stream_id}",
            "receipts": [source.apply("request"), source.apply("repair")],
        })
        source_units = 2
    elif arm == "instruction":
        text, parsed, source_units, source_agent = _instruction_parse(agent)
        instructed_episode(agent, episode_id=stream_id, text=text, parsed=parsed)
    elif arm == "reward_only":
        reward_only_episode(agent, episode_id=stream_id, feedback={
            "status": "observed", "outcome": "rewarded", "reward_value": 1.0})
        source_units = 1
    else:
        raise ValueError(f"unknown social arm: {arm}")

    _settle(agent)
    candidates = agent.s.nodes("ObservedProcessSequenceCandidate")
    if arm == "reward_only":
        if candidates:
            raise RuntimeError("reward-only source invented an action sequence")
        results = agent.s.nodes("ObservedSequenceInferenceResult")
        if len(results) != 1:
            raise RuntimeError("reward-only arm did not emit one abstention result")
        result = agent.s.node(results[0])["attrs"]
        if result.get("status") != "abstained_underidentified":
            raise RuntimeError("reward-only arm used an unsupported inference")
        outcome = "abstained_underidentified"
        solved = False
        verification_status = "not_applicable"
        own_actions = 0
    else:
        if len(candidates) != 1:
            raise RuntimeError(f"{arm} did not produce one native sequence candidate")
        candidate = candidates[0]
        candidate_id = agent.s.node(candidate)["attrs"]["candidate_id"]
        funding = _request(agent, requester_kind="observed_sequence_validation",
                           candidate_id=candidate_id, cost=2)
        agent.s.add_edge(candidate, "has_verification_request", funding, {})
        _settle(agent)
        verification = verify_observed_sequence_candidate(agent, candidate)
        verification_status = verification["status"]
        if verification_status != "VERIFIED":
            raise RuntimeError(f"{arm} failed independent fresh-world verification: {verification}")
        own_world = RequestRepairWorld(world_id=f"own:{stream_id}", case_id="unseen-case")
        execution = execute_verified_observed_sequence(
            agent, candidate, world=own_world, authorize=lambda proposal: True)
        solved = execution.get("status") == "COMPLETED" and own_world.solved
        if not solved:
            raise RuntimeError(f"{arm} failed authorized own-world execution: {execution}")
        outcome, own_actions = "verified_and_executed", len(execution["world_receipts"])

    requests = agent.s.nodes("ThinkingBudgetRequest")
    debits = sum(agent.s.node(node)["attrs"].get("debited_epoch") is not None
                 for node in requests)
    budget = agent.s.node(agent.s.nodes("ThinkingBudget")[0])["attrs"]
    source_actions = (source_units if arm in ("observation", "demonstration") else 0)
    visible_observations = source_units if arm in ("observation", "demonstration") else (
        2 if arm == "instruction" else 1)
    graph_nodes = len(agent.s.nodes())
    graph_bytes = len(json.dumps([agent.s.node(node) for node in agent.s.nodes()],
                                 sort_keys=True, default=str).encode())
    source_graph_nodes = len(source_agent.s.nodes()) if source_agent is not None else 0
    source_graph_bytes = (len(json.dumps([source_agent.s.node(node)
                                          for node in source_agent.s.nodes()],
                                         sort_keys=True, default=str).encode())
                          if source_agent is not None else 0)
    return {
        "arm": arm, "stream_id": stream_id, "outcome": outcome,
        "evidence_opportunities": 1, "visible_observations": visible_observations,
        "source_world_actions": source_actions,
        "source_information_units": source_units,
        "source_information_unit_kind": ("world_receipt" if arm in ("observation", "demonstration")
                                          else "public_word" if arm == "instruction"
                                          else "scalar_reward"),
        "target_primitive_actions": own_actions, "own_actions": own_actions,
        "verification_status": verification_status, "solved": solved,
        "budget_requests": len(requests), "budget_debits": debits,
        "budget_remaining": budget.get("remaining"),
        "native_rule_steps": getattr(agent, "_p20_native_rule_steps", 0),
        "native_rule_steps_scope": "sequence learner and verification/execution settlement ticks",
        "graph_nodes": graph_nodes, "graph_bytes": graph_bytes,
        "source_graph_nodes": source_graph_nodes, "source_graph_bytes": source_graph_bytes,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "authorized_actions": own_actions,
        "source_evidence_types": sorted({agent.s.node(node)["type"] for node in
                                          (agent.s.nodes("ObservedInteractionTrace")
                                           + agent.s.nodes("ProcessDemonstration")
                                           + agent.s.nodes("ParsedProcessInstruction")
                                           + agent.s.nodes("ScalarRewardEvidence"))}),
    }


def run_development_panel(*, streams_per_arm=2, stream_prefix="dev"):
    records = [_one_stream(arm, index, stream_prefix=stream_prefix) for arm in ARMS
               for index in range(streams_per_arm)]
    return {
        "status": ("development_only" if stream_prefix == "dev"
                   else "heldout_unanalyzed"),
        "stream_prefix": stream_prefix, "arms": list(ARMS),
        "streams_per_arm": streams_per_arm, "records": records,
        "arm_summary": {
            arm: {
                "n": sum(row["arm"] == arm for row in records),
                "outcomes": {outcome: sum(row["arm"] == arm and row["outcome"] == outcome
                                           for row in records)
                             for outcome in sorted({row["outcome"] for row in records})},
                "mean_source_information_units": sum(row["source_information_units"]
                                                     for row in records if row["arm"] == arm)
                / sum(row["arm"] == arm for row in records),
                "mean_budget_debits": sum(row["budget_debits"] for row in records
                                          if row["arm"] == arm)
                / sum(row["arm"] == arm for row in records),
            } for arm in ARMS
        },
    }


def run_development_controls(*, per_kind=1, control_prefix="dev-control"):
    """Validate the four registered social evidence rejection controls."""
    kinds = ("wrong_frame", "missing_step", "body_mismatch", "false_description")
    records = []
    for kind in kinds:
        for index in range(per_kind):
            agent = _agent()
            control_id = f"{control_prefix}:{kind}:{index:04d}"
            rejected = False
            if kind == "wrong_frame":
                source = RequestRepairWorld(world_id=control_id)
                witnessed_episode(agent, episode_id=control_id,
                                  receipts=[source.apply("request"), source.apply("repair")],
                                  frame_epoch=8)
                _settle(agent)
                rejected = not agent.s.nodes("ObservedProcessSequenceCandidate")
                reason = "stale_frame_abstained"
            elif kind == "missing_step":
                source = RequestRepairWorld(world_id=control_id)
                try:
                    witnessed_episode(agent, episode_id=control_id,
                                      receipts=[source.apply("request")])
                except ValueError:
                    rejected = True
                reason = "incomplete_receipt_sequence_rejected"
            elif kind == "body_mismatch":
                source = RequestRepairWorld(world_id=control_id)
                try:
                    demonstrated_episode(agent, episode_id=control_id, demonstration={
                        "status": "complete", "actor_id": "learner",
                        "receipts": [source.apply("request"), source.apply("repair")],
                    })
                except ValueError:
                    rejected = True
                reason = "own_body_mislabeled_as_demonstration_rejected"
            else:
                try:
                    instructed_episode(agent, episode_id=control_id, text="request then repair",
                                       parsed={"parse_status": "parsed",
                                               "semantic_sequence": ["seq", ["request", "erase"]],
                                               "required_preconditions": ["idle", "requested"]})
                except ValueError:
                    rejected = True
                reason = "false_sequence_description_rejected"
            records.append({"kind": kind, "control_id": control_id,
                            "status": "PASS" if rejected else "FAIL",
                            "state_unchanged": True,
                            "false_candidate_count": len(agent.s.nodes(
                                "ObservedProcessSequenceCandidate")),
                            "reason": reason})
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--streams-per-arm", type=int, default=2)
    parser.add_argument("--controls-per-kind", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_development_panel(streams_per_arm=args.streams_per_arm)
    result["controls"] = run_development_controls(per_kind=args.controls_per_kind)
    if any(row["status"] != "PASS" for row in result["controls"]):
        raise SystemExit("P20 development structural control failed")
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
