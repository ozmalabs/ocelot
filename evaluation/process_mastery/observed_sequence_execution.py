"""Verify and execute native observed-sequence candidates at a bounded sink."""
from __future__ import annotations

from typing import Callable

from evaluation.process_mastery.target_learning_worlds import RequestRepairWorld


def _attrs(agent, node):
    return agent.s.node(node)["attrs"]


def _native(agent):
    return getattr(agent, "native", None) or getattr(agent, "inner", None)


def _root(agent):
    return getattr(agent, "ag", None) or getattr(agent, "agent", None)


def _step_nodes(agent, candidate):
    native = _native(agent)
    first = native.neighbours(candidate, "uses_first_primitive")
    second = native.neighbours(candidate, "uses_second_primitive")
    if len(first) != 1 or len(second) != 1:
        raise ValueError("sequence candidate has missing or ambiguous primitive steps")
    return first[0], second[0]


def _ordered_steps(agent, candidate):
    attrs = _attrs(agent, candidate)
    sequence = attrs.get("action_sequence")
    if not isinstance(sequence, (tuple, list)) or len(sequence) != 2 or sequence[0] != "seq":
        raise ValueError("unsupported observed sequence shape")
    nodes = _step_nodes(agent, candidate)
    operators = [_attrs(agent, node).get("operator") for node in nodes]
    if list(sequence[1]) != operators:
        raise ValueError("candidate sequence no longer matches linked primitive steps")
    for node in nodes:
        step = _attrs(agent, node)
        for epoch in ("source_epoch", "model_epoch", "frame_epoch"):
            if step.get(epoch) != attrs.get(epoch):
                raise ValueError(f"stale primitive epoch: {epoch}")
    return nodes, operators


def verify_observed_sequence_candidate(agent, candidate, *, world_factory=RequestRepairWorld):
    """Run graph-selected steps in a fresh independent world and record result."""
    attrs = _attrs(agent, candidate)
    if attrs.get("status") != "unverified_candidate":
        return {"status": "ABSTAIN", "reason": "candidate_not_unverified"}
    native = _native(agent)
    funding = native.neighbours(candidate, "has_verification_request")
    if len(funding) != 1:
        return {"status": "ABSTAIN", "reason": "missing_verification_funding"}
    request_attrs = _attrs(agent, funding[0])
    if (request_attrs.get("requester_kind") != "observed_sequence_validation"
            or request_attrs.get("status") != "approved"
            or request_attrs.get("debited_epoch") is None):
        return {"status": "ABSTAIN", "reason": "verification_not_funded"}
    try:
        _nodes, actions = _ordered_steps(agent, candidate)
    except ValueError as exc:
        return {"status": "ABSTAIN", "reason": str(exc)}
    world = world_factory(world_id=f"verify:{attrs['candidate_id']}",
                          case_id="fresh-case")
    try:
        for action in actions:
            world.apply(action)
        exact = world.solved
    except ValueError:
        exact = False
    status = "verified" if exact else "failed"
    receipt_id = f"sequence-verification:{attrs['candidate_id']}:{world.world_id}"
    receipt = agent.s.add_node("ObservedSequenceVerification", {
        "receipt_id": receipt_id, "candidate_id": attrs["candidate_id"],
        "status": status, "exact_effect_match": exact, "step_count": len(actions),
        "action_sequence": attrs["action_sequence"],
        "source_epoch": attrs.get("source_epoch"),
        "model_epoch": attrs.get("model_epoch"),
        "frame_epoch": attrs.get("frame_epoch"), "world_id": world.world_id,
        "world_receipt_ids": [item.event_id for item in world.receipts],
        "observed_state": world.state})
    agent.s.add_edge(candidate, "has_verification", receipt, {})
    for _ in range(16):
        if not native.run_rules(1000):
            break
    return {"status": status.upper(), "receipt_id": receipt_id,
            "world_receipts": list(world.receipts), "observed_state": world.state}


def execute_verified_observed_sequence(agent, candidate, *, world,
                                       authorize: Callable[[dict], bool]):
    """Execute only a current native candidate, one authorized step at a time."""
    attrs = _attrs(agent, candidate)
    if attrs.get("status") != "verified":
        return {"status": "ABSTAIN", "reason": "sequence_not_world_verified"}
    native = _native(agent)
    receipts = native.neighbours(candidate, "has_verification")
    if (len(receipts) != 1 or _attrs(agent, receipts[0]).get("status") != "verified"
            or _attrs(agent, receipts[0]).get("exact_effect_match") is not True):
        return {"status": "ABSTAIN", "reason": "verification_receipt_missing_or_stale"}
    try:
        _nodes, actions = _ordered_steps(agent, candidate)
    except ValueError as exc:
        return {"status": "ABSTAIN", "reason": str(exc)}
    own_receipts = []
    for index, action in enumerate(actions):
        request_id = f"own-sequence:{attrs['candidate_id']}:{index}"
        proposal = {"candidate_id": attrs["candidate_id"], "request_id": request_id,
                    "action": action, "sequence_index": index,
                    "owner_id": attrs.get("owner_id"),
                    "source_epoch": attrs.get("source_epoch"),
                    "model_epoch": attrs.get("model_epoch"),
                    "frame_epoch": attrs.get("frame_epoch")}
        action_request = agent.s.add_node("ActionRequest", {
            **proposal, "actor_id": attrs.get("owner_id"), "status": "pending"})
        agent.s.add_edge(_root(agent), "has_action_request", action_request, {})
        if not authorize(proposal):
            agent.s.set_attr(action_request, "status", "denied")
            return {"status": "ABSTAIN", "reason": "action_not_authorized",
                    "world_receipts": own_receipts}
        authorization = agent.s.add_node("ActionAuthorization", {
            "request_id": request_id, "source_epoch": attrs.get("source_epoch"),
            "status": "consumed", "action": action})
        agent.s.add_edge(action_request, "has_action_authorization", authorization, {})
        try:
            world_receipt = world.apply(action)
        except ValueError as exc:
            agent.s.set_attr(action_request, "status", "precondition_failed")
            return {"status": "FAILED", "reason": str(exc),
                    "world_receipts": own_receipts}
        agent.s.set_attr(action_request, "status", "emitted")
        agent.s.set_attr(action_request, "sink_receipt_id", world_receipt.event_id)
        own = agent.s.add_node("OwnTrialReceipt", {
            "receipt_id": world_receipt.event_id, "status": "observed",
            "actual_own_trial": True, "owner_id": attrs.get("owner_id"),
            "learner_body_owner_id": attrs.get("owner_id"),
            "source_epoch": attrs.get("source_epoch"),
            "model_epoch": attrs.get("model_epoch"),
            "frame_epoch": attrs.get("frame_epoch"),
            "action": action, "sequence_index": index,
            "before_value": world_receipt.before_value,
            "after_value": world_receipt.after_value,
            "sink_receipt_id": world_receipt.event_id})
        agent.s.add_edge(candidate, "has_own_trial_receipt", own, {})
        agent.s.add_edge(own, "binds_action_request", action_request, {})
        own_receipts.append(world_receipt)
    return {"status": "COMPLETED" if world.solved else "UNSOLVED",
            "world_receipts": own_receipts, "observed_state": world.state}
