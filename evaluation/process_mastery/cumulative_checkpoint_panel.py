"""Read-only common-world scoring for immutable scheduled learner snapshots."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Callable

from evaluation.process_mastery.scheduled_learning_checkpoints import (
    CHECKPOINTS, ScheduledLearningCheckpoint, verify_scheduled_checkpoint,
)


CAUSAL_COMPONENTS = frozenset({
    "learned_distinctions", "shared_transfer_priors",
    "consolidated_representations", "new_processes",
})
_COMPONENT_NODE_TYPES = {
    "learned_distinctions": {"CommonTargetEvidence", "TransitionObservation",
        "TransitionHypothesis", "TransitionModelReceipt", "ProcessInductionHypothesis"},
    "shared_transfer_priors": {"AdditiveTransferHypothesis", "SourceProcessPrior",
        "MappedProcessPrior"},
    "consolidated_representations": {"LearningMemoryItem", "ConsolidatedRepresentation",
        "LearningMemoryCache"},
    "new_processes": {"ProcessSchema", "ProcessCandidate", "OpenProcessCandidate"},
}
SEALED_SPLITS = frozenset({"development", "validation", "heldout"})


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False, default=str).encode()).hexdigest()


def world_allocation_digest(worlds: list[dict]) -> str:
    """Hash exact world records in stable ID order for checkpoint binding."""
    ordered = sorted(worlds, key=lambda row: row.get("world_id", ""))
    return _digest(ordered)


def _graph(checkpoint: ScheduledLearningCheckpoint) -> dict:
    if not verify_scheduled_checkpoint(checkpoint):
        raise ValueError("panel requires an intact immutable scheduled checkpoint")
    return json.loads(checkpoint.graph_snapshot_json)


def score_common_world_panel(*, checkpoints: dict[str, tuple[ScheduledLearningCheckpoint, ...]],
        worlds: list[dict], native_predictor: Callable[[dict, dict], object],
        allocation_sha256: str | None = None) -> dict:
    """Query each frozen state on identical sealed worlds; never return scores to it."""
    if not checkpoints or not worlds or not (callable(native_predictor)
            or isinstance(native_predictor, dict)):
        raise ValueError("checkpoints, worlds and a native predictor are required")
    world_ids = [world.get("world_id") for world in worlds]
    if any(not isinstance(x, str) or not x for x in world_ids) or len(set(world_ids)) != len(world_ids):
        raise ValueError("sealed world IDs must be present and unique")
    for world in worlds:
        if world.get("split") not in SEALED_SPLITS:
            raise ValueError("scoring panel accepts registered nontraining worlds only")
        if not isinstance(world.get("goal_state", world.get("expected_after_value")),
                          (list, tuple, str, int, float, bool)):
            raise ValueError("scored world must have an external expected outcome")
    expected_allocation_sha = allocation_sha256 or world_allocation_digest(worlds)
    rows = []
    for arm, sequence in sorted(checkpoints.items()):
        predictor = (native_predictor.get(arm) if isinstance(native_predictor, dict)
                     else native_predictor)
        if not callable(predictor):
            raise ValueError(f"missing native predictor for arm {arm}")
        valid_sequence = (len(sequence) == len(CHECKPOINTS)
            and tuple(cp.checkpoint for cp in sequence) == CHECKPOINTS) or (
                len(sequence) == 1 and sequence[0].checkpoint == "g3")
        if not arm or not valid_sequence:
            raise ValueError("each arm must provide g0-g3 or the registered final g3 checkpoint")
        if any(cp.arm != arm for cp in sequence):
            raise ValueError("checkpoint arm and schedule identity mismatch")
        allocation_hashes = {cp.world_allocation_sha256 for cp in sequence}
        if allocation_hashes != {expected_allocation_sha}:
            raise ValueError("checkpoint ancestry does not bind the exact scored worlds")
        for checkpoint in sequence:
            graph = _graph(checkpoint)
            before = _digest(graph)
            for world in worlds:
                # The native query receives a private read-only copy. The scorer
                # owns success labels and runs after the prediction is captured.
                query_world = {key: copy.deepcopy(value) for key, value in world.items()
                    if key not in {"goal_state", "expected_after_value", "score",
                                   "solvable", "witness", "relation_class"}}
                prediction = predictor(copy.deepcopy(graph), query_world)
                raw_prediction = copy.deepcopy(prediction)
                expected = world.get("expected_after_value", world.get("goal_state"))
                if isinstance(prediction, dict):
                    prediction = (prediction.get("expected_after_value")
                        if prediction.get("status") == "predicted" else None)
                score = (None if prediction is None else
                    int(list(prediction) == list(expected)
                        if isinstance(expected, (list, tuple)) else prediction == expected))
                rows.append({"arm": arm, "checkpoint": checkpoint.checkpoint,
                    "checkpoint_sha256": checkpoint.checkpoint_sha256,
                    "world_id": world["world_id"], "split": world["split"],
                    "prediction_missing": prediction is None, "score": score,
                    "prediction": raw_prediction, "expected_outcome": expected,
                    "primitive_work": checkpoint.cumulative["primitive_work"],
                    "source_exposure": checkpoint.cumulative["source_exposure"],
                    "native_rule_steps": checkpoint.cumulative["native_rule_steps"],
                    "graph_bytes": checkpoint.cumulative["graph_bytes"],
                    "approval_pending": checkpoint.interval_status == "authorization_pending"})
            if _digest(graph) != before:
                raise RuntimeError("read-only panel mutated its checkpoint graph")
    return {"status": "COMPLETED", "rows": rows,
        "score_feedback_to_training": False,
        "world_ids": world_ids, "world_allocation_sha256": expected_allocation_sha}


def ablate_component(graph: dict, component: str) -> dict:
    """Copy a snapshot while removing only explicitly tagged component nodes."""
    if component not in CAUSAL_COMPONENTS:
        raise ValueError("unknown causal component")
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        raise ValueError("native graph snapshot must contain a nodes list")
    result = copy.deepcopy(graph)
    removed_ids = set()
    kept = []
    for node in result["nodes"]:
        attrs = node.get("attrs", {}) if isinstance(node, dict) else {}
        if (attrs.get("p27_component") == component
                or node.get("type") in _COMPONENT_NODE_TYPES[component]):
            removed_ids.add(str(node.get("id")))
        else:
            kept.append(node)
    result["nodes"] = kept
    if isinstance(result.get("edges"), list):
        result["edges"] = [edge for edge in result["edges"]
            if str(edge.get("from", edge.get("src"))) not in removed_ids
            and str(edge.get("to", edge.get("tgt"))) not in removed_ids]
    return result


def run_component_knockouts(*, graph: dict, world: dict,
        native_predictor: Callable[[dict, dict], object]) -> dict:
    """Report baseline versus single-component ablations on development only."""
    if world.get("split") != "development":
        raise ValueError("causal knockout controls are development-only")
    before = _digest(graph)
    baseline = native_predictor(copy.deepcopy(graph), copy.deepcopy(world))
    outcomes = {}
    for component in sorted(CAUSAL_COMPONENTS):
        ablated = ablate_component(graph, component)
        prediction = native_predictor(ablated, copy.deepcopy(world))
        outcomes[component] = {"prediction": prediction,
            "removed_nodes": len(graph.get("nodes", [])) - len(ablated["nodes"]),
            "prediction_changed": prediction != baseline,
            "status": "path_perturbed" if prediction != baseline else "no_effect_observed"}
    if _digest(graph) != before:
        raise RuntimeError("causal knockout mutated the source checkpoint")
    return {"status": "COMPLETED", "baseline_prediction": baseline,
        "outcomes": outcomes, "source_graph_unchanged": True,
        "world_split": "development", "actionable": False}


def make_native_common_target_predictor(*, owner_id: str, agent_factory):
    """Bind a read-only prediction query to the actual restored cognition graph.

    The world record carries query inputs only; its expected outcome is removed
    by the panel before this adapter is called. The returned closure boots a
    fresh profile, restores the checkpoint graph, disables learning policies,
    and asks the native common-target learner for one prediction.
    """
    if not isinstance(owner_id, str) or not owner_id or not callable(agent_factory):
        raise ValueError("native predictor requires a checkpoint owner and agent factory")

    agent = agent_factory()
    loaded_graph_sha = None
    loaded_split = None

    def predict(graph: dict, world: dict):
        nonlocal loaded_graph_sha, loaded_split
        required = {"action_kind", "object_type", "feature_key", "before_value",
                    "object_id", "world_id", "split"}
        if not required.issubset(world):
            raise ValueError("native target query is missing registered fields")
        if world["split"] not in {"development", *SEALED_SPLITS}:
            raise ValueError("native target prediction requires a nontraining split")
        from evaluation.process_mastery.common_target_learner import CommonTargetLearner
        native = getattr(agent, "inner", None) or getattr(agent, "native", None)
        if native is None:
            raise TypeError("agent factory must return a native cognition profile")
        graph_sha = _digest(graph)
        if graph_sha != loaded_graph_sha or world["split"] != loaded_split:
            native.graph_from_dict(copy.deepcopy(graph))
            loaded_graph_sha, loaded_split = graph_sha, world["split"]
        learner = CommonTargetLearner(agent=agent, owner_id=owner_id,
            enabled=True, policy_enabled=False, additive_transfer_enabled=False)
        return learner.predict(query_id=f"p27:{world['world_id']}",
            action_kind=world["action_kind"], object_type=world["object_type"],
            feature_key=world["feature_key"], before_value=world["before_value"],
            object_id=world["object_id"], source_epoch=world.get("source_epoch", 3),
            model_epoch=world.get("model_epoch", 2),
            frame_epoch=world.get("frame_epoch", 5), split=world["split"])

    predict.close = agent.close

    return predict
