"""Fresh-world verification for bounded explanation-rebuilt compositions."""
from __future__ import annotations

from evaluation.process_mastery.target_learning_worlds import RequestRepairWorld


def _attrs(agent, node):
    return agent.s.node(node)["attrs"]


def _native(agent):
    return getattr(agent, "native", None) or getattr(agent, "inner", None)


def verify_rebuilt_composition(agent, candidate, *, world_factory=RequestRepairWorld):
    """Verify a parsed two-step candidate and record a provenance-bound receipt.

    Verification checks the graph's two shared primitive links against the
    candidate sequence/preconditions, executes on a fresh target world, and
    probes the first step from an invalid precondition state to ensure it fails
    closed. It never reads source-process data.
    """
    attrs = _attrs(agent, candidate)
    if attrs.get("status") != "unverified_candidate":
        return {"status": "ABSTAIN", "reason": "candidate_not_unverified"}
    funding = agent.s.neighbours(candidate, "has_verification_request")
    if len(funding) != 1:
        return {"status": "ABSTAIN", "reason": "missing_verification_funding"}
    request = _attrs(agent, funding[0])
    if (request.get("requester_kind") != "process_rebuild_validation"
            or request.get("candidate_id") != attrs.get("candidate_id")
            or request.get("status") != "approved"
            or request.get("debited_epoch") is None):
        return {"status": "ABSTAIN", "reason": "verification_not_funded"}
    first = agent.s.neighbours(candidate, "uses_first_shared_primitive")
    second = agent.s.neighbours(candidate, "uses_second_shared_primitive")
    sequence = attrs.get("action_sequence")
    preconditions = attrs.get("required_preconditions")
    if (len(first) != 1 or len(second) != 1
            or not isinstance(sequence, list) or len(sequence) != 2
            or any(not isinstance(action, str) or not action for action in sequence)
            or not isinstance(preconditions, list) or len(preconditions) != 2
            or any(not isinstance(state, str) or not state for state in preconditions)
            or preconditions[0] == preconditions[1]):
        return {"status": "ABSTAIN", "reason": "unsupported_or_incomplete_composition"}
    primitive_attrs = [_attrs(agent, first[0]), _attrs(agent, second[0])]
    if ([item.get("semantic_event") for item in primitive_attrs] != sequence
            or [item.get("precondition") for item in primitive_attrs] != preconditions
            or any(item.get("model_epoch") != attrs.get("model_epoch")
                   or item.get("frame_epoch") != attrs.get("frame_epoch")
                   for item in primitive_attrs)):
        return {"status": "ABSTAIN", "reason": "primitive_binding_or_epoch_mismatch"}

    world = world_factory(world_id=f"explanation-verify:{attrs['candidate_id']}",
                          case_id="fresh-idle-case", initial="idle")
    try:
        receipts = [world.apply(action) for action in sequence]
        positive = (world.solved and [r.action_kind for r in receipts] == sequence
                    and [r.before_value for r in receipts] == preconditions)
    except ValueError:
        positive = False
        receipts = list(world.receipts)

    counterexample = world_factory(
        world_id=f"explanation-counterexample:{attrs['candidate_id']}",
        case_id="invalid-first-precondition", initial=preconditions[1])
    rejected = False
    try:
        counterexample.apply(sequence[0])
    except ValueError:
        rejected = not counterexample.receipts
    exact = positive and rejected
    status = "verified" if exact else "failed"
    receipt_id = f"rebuild-verification:{attrs['candidate_id']}:{world.world_id}"
    receipt = agent.s.add_node("RebuildVerification", {
        "candidate_id": attrs["candidate_id"], "receipt_id": receipt_id,
        "verification_kind": "fresh_native_rebuild", "status": status,
        "exact_effect_match": exact, "model_epoch": attrs.get("model_epoch"),
        "frame_epoch": attrs.get("frame_epoch"), "probe_count": 3,
        "action_sequence": sequence, "required_preconditions": preconditions,
        "fresh_world_id": world.world_id,
        "world_receipt_ids": [r.event_id for r in receipts],
        "counterexample_world_id": counterexample.world_id,
        "counterexample_rejected": rejected,
    })
    agent.s.add_edge(candidate, "has_rebuild_verification", receipt, {})
    for _ in range(16):
        if not _native(agent).run_rules(1000):
            break
    return {"status": status.upper(), "receipt_id": receipt_id,
            "world_receipts": receipts, "counterexample_rejected": rejected}
