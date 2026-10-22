"""Source-specific adapters for the bounded P20 observed-sequence learner.

Adapters preserve the evidence object that supplied an ordered sequence. The
native learner consumes a common SocialEpisode envelope, but callers cannot
label a typed sequence as witnessed, demonstrated, or instructed without
providing the corresponding source evidence.
"""
from __future__ import annotations


def _add_episode(agent, *, episode_id, source_kind, action_sequence,
                 source_epoch, model_epoch, frame_epoch, source_node, source_edge,
                 owner_id="learner", actor_id="peer"):
    attrs = {
        "episode_id": episode_id, "status": "observed", "source_kind": source_kind,
        "observation_status": "complete", "interaction_kind": "request_repair",
        "owner_id": owner_id, "actor_id": actor_id,
        "source_epoch": source_epoch, "model_epoch": model_epoch,
        "frame_epoch": frame_epoch,
    }
    if action_sequence is not None:
        if (not isinstance(action_sequence, (tuple, list)) or len(action_sequence) != 2
                or action_sequence[0] != "seq"
                or list(action_sequence[1]) != ["request", "repair"]):
            raise ValueError("P20 adapter accepts only the declared two-step sequence")
        attrs["action_sequence"] = ["seq", ["request", "repair"]]
    episode = agent.s.add_node("SocialEpisode", attrs)
    agent.s.add_edge(agent.ag, "has_social_episode", episode, {})
    agent.s.add_edge(episode, source_edge, source_node, {})
    request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "observed_sequence_learning", "episode_id": episode_id,
        "source_key": f"sequence:{episode_id}", "source_epoch": source_epoch,
        "operation_id": f"observe-sequence:{episode_id}", "status": "pending",
        "cost": 1.0,
    })
    agent.s.add_edge(agent.ag, "has_thinking_budget_request", request, {})
    agent.s.add_edge(request, "draws_on_thinking_budget",
                     agent.s.nodes("ThinkingBudget")[0], {})
    return episode


def _sequence_from_receipts(receipts):
    if len(receipts) != 2:
        raise ValueError("complete two-step receipt sequence required")
    actions = [getattr(receipt, "action_kind", None) for receipt in receipts]
    if actions != ["request", "repair"]:
        raise ValueError("receipt sequence does not show request followed by repair")
    return ["seq", actions]


def witnessed_episode(agent, *, episode_id, receipts, source_epoch=4,
                      model_epoch=7, frame_epoch=9):
    """Adapt two independently witnessed world receipts into a learner input."""
    sequence = _sequence_from_receipts(receipts)
    trace = agent.s.add_node("ObservedInteractionTrace", {
        "trace_id": f"witness:{episode_id}", "status": "complete",
        "actor_id": "peer", "action_sequence": sequence,
        "receipt_ids": [getattr(row, "event_id", None) for row in receipts],
        "outcomes": [getattr(row, "after_value", None) for row in receipts],
    })
    agent.s.add_edge(agent.ag, "has_observed_interaction_trace", trace, {})
    return _add_episode(agent, episode_id=episode_id,
                        source_kind="witnessed_interaction", action_sequence=sequence,
                        source_epoch=source_epoch, model_epoch=model_epoch,
                        frame_epoch=frame_epoch, source_node=trace,
                        source_edge="derived_from_interaction_trace")


def demonstrated_episode(agent, *, episode_id, demonstration, source_epoch=4,
                         model_epoch=7, frame_epoch=9):
    """Adapt an explicit demonstration record; the actor remains distinct."""
    if (not isinstance(demonstration, dict)
            or demonstration.get("status") != "complete"
            or demonstration.get("actor_id") in (None, "learner")):
        raise ValueError("complete other-actor demonstration required")
    sequence = _sequence_from_receipts(demonstration.get("receipts", ()))
    node = agent.s.add_node("ProcessDemonstration", {
        "demonstration_id": f"demo:{episode_id}", "status": "complete",
        "actor_id": demonstration["actor_id"], "action_sequence": sequence,
        "receipt_ids": [getattr(row, "event_id", None)
                        for row in demonstration["receipts"]],
    })
    agent.s.add_edge(agent.ag, "has_process_demonstration", node, {})
    return _add_episode(agent, episode_id=episode_id, source_kind="demonstration",
                        action_sequence=sequence, source_epoch=source_epoch,
                        model_epoch=model_epoch, frame_epoch=frame_epoch,
                        source_node=node, source_edge="derived_from_demonstration",
                        actor_id=demonstration["actor_id"])


def instructed_episode(agent, *, episode_id, text, parsed, source_epoch=4,
                       model_epoch=7, frame_epoch=9):
    """Adapt independently parsed public language, never a supplied source AST."""
    if parsed.get("parse_status") != "parsed":
        raise ValueError("instruction did not parse")
    sequence = parsed.get("semantic_sequence")
    if sequence != ["seq", ["request", "repair"]]:
        raise ValueError("instruction parse does not express the declared sequence")
    instruction = agent.s.add_node("ParsedProcessInstruction", {
        "instruction_id": f"instruction:{episode_id}", "text": text,
        "parse_status": "parsed", "semantic_sequence": sequence,
        "required_preconditions": parsed.get("required_preconditions", []),
        "source_ast_included": False,
    })
    agent.s.add_edge(agent.ag, "has_parsed_process_instruction", instruction, {})
    return _add_episode(agent, episode_id=episode_id,
                        source_kind="parsed_instruction", action_sequence=sequence,
                        source_epoch=source_epoch, model_epoch=model_epoch,
                        frame_epoch=frame_epoch, source_node=instruction,
                        source_edge="derived_from_instruction")


def reward_only_episode(agent, *, episode_id, feedback, source_epoch=4,
                        model_epoch=7, frame_epoch=9):
    """Preserve scalar outcome evidence without inventing an action sequence."""
    if not isinstance(feedback, dict) or feedback.get("status") != "observed":
        raise ValueError("observed reward feedback required")
    evidence = agent.s.add_node("ScalarRewardEvidence", {
        "evidence_id": f"reward:{episode_id}", "status": "observed",
        "reward_value": feedback.get("reward_value"),
        "outcome": feedback.get("outcome"), "source_kind": "reward_only",
    })
    agent.s.add_edge(agent.ag, "has_scalar_reward_evidence", evidence, {})
    return _add_episode(agent, episode_id=episode_id, source_kind="reward_only",
                        action_sequence=None, source_epoch=source_epoch,
                        model_epoch=model_epoch, frame_epoch=frame_epoch,
                        source_node=evidence, source_edge="derived_from_reward_evidence")
