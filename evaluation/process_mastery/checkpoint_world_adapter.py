"""Read-only common-world evaluator for immutable native process checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import time

from evaluation.process_mastery.native_process_execution import (
    open_process_candidate_digest, params_digest,
)
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world, generate_d4_world_v2,
    generate_loopover_world, generate_loopover_world_v2,
)
from evaluation.process_mastery.p22_resource_accounting import (
    NativeRuleWorkCapture, compare_resource_snapshots,
    merge_native_rule_work_snapshots, native_rule_work_digest_valid,
    resource_snapshot_digest_valid,
    snapshot_native_resources,
)


def score_unapproved_candidate_on_validation(agent, candidate: int,
                                             world: dict) -> dict:
    """Score one training-derived proposal on a fresh validation world.

    This is a read-only algebra check. It deliberately rejects held-out worlds,
    candidates without a verified digest receipt, and anything already on an
    approval or world-action path.
    """
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    store = getattr(agent, "s", None)
    if native is None or store is None:
        raise TypeError("agent must expose native substrate and graph store")
    if not isinstance(world, dict) or world.get("split") != "validation":
        raise ValueError("unapproved candidates may be scored only on validation worlds")
    family_generators = {
        "pmb_generated_loopover_v1": generate_loopover_world,
        "pmb_generated_d4_corner_v1": generate_d4_world,
        "pmb_generated_loopover_v2": generate_loopover_world_v2,
        "pmb_generated_d4_corner_v2": generate_d4_world_v2,
    }
    generator = family_generators.get(world.get("family"))
    if generator is None:
        raise ValueError("validation world family is unsupported")
    expected_world = agent_view(generator(split="validation", draw=world.get("draw")))
    if world != expected_world:
        raise ValueError("validation world must match the registered answer-free generator view")
    required_world = ("world_id", "initial_state", "goal_state")
    if any(key not in world for key in required_world) or not world["world_id"]:
        raise ValueError("validation world identity and task states are required")

    attrs = store.node(candidate)["attrs"]
    if attrs.get("status") != "unapproved_candidate" or attrs.get("approval_required") != 1.0:
        raise ValueError("candidate is not an unapproved non-actionable proposal")
    if native.neighbours(candidate, "approved_by_open_process_adoption"):
        raise ValueError("candidate already has an approval event")
    if native.neighbours(candidate, "has_world_execution_receipt"):
        raise ValueError("candidate already has a world execution receipt")
    digest_receipts = native.neighbours(candidate, "has_expression_digest_receipt")
    if len(digest_receipts) != 1:
        raise ValueError("candidate requires one verified expression digest receipt")
    digest = open_process_candidate_digest(agent, candidate)
    receipt = store.node(digest_receipts[0])["attrs"]
    if (attrs.get("expression_digest_status") != "verified"
            or attrs.get("expression_digest") != digest
            or receipt.get("status") != "verified"
            or receipt.get("expression_digest") != digest):
        raise ValueError("candidate expression digest receipt does not verify")

    attempts = native.neighbours(candidate, "derived_from_attempt")
    if len(attempts) != 1:
        raise ValueError("candidate must have one native source attempt")
    attempt = store.node(attempts[0])["attrs"]
    tasks = native.neighbours(attempts[0], "about_task")
    if len(tasks) != 1:
        raise ValueError("candidate source attempt must identify one training task")
    task = store.node(tasks[0])["attrs"]
    if (attempt.get("status") != "verified" or task.get("split") != "training"
            or attempt.get("split", "training") != "training"):
        raise ValueError("candidate source must be a native-verified training task")
    params = attrs.get("params")
    initial = world["initial_state"]
    goal = world["goal_state"]
    if (not isinstance(params, list) or len(params) < 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in params)
            or sorted(params) != list(range(len(params)))):
        raise ValueError("candidate parameters must be a finite permutation")
    if attrs.get("guard_state") != initial:
        raise ValueError("validation initial state does not match the candidate guard")
    for label, state in (("initial", initial), ("goal", goal)):
        if (not isinstance(state, list) or len(state) != len(params)
                or any(isinstance(value, bool) or not isinstance(value, int) for value in state)
                or sorted(state) != list(range(len(params)))):
            raise ValueError(f"validation {label} state must match candidate domain")
    if (attrs.get("domain") != attempt.get("domain")
            or task.get("domain") != attrs.get("domain")):
        raise ValueError("candidate domain differs from its verified source attempt")

    result = native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": list(params), "state": list(initial)})
    return {"status": "nonactionable_candidate_scored",
            "actionable": False, "approval_created": False,
            "world_receipt_created": False, "candidate_id": str(candidate),
            "expression_digest": digest, "world_id": world["world_id"],
            "split": "validation", "score": int(result == goal),
            "initial_state": list(initial), "goal_state": list(goal),
            "result_state": result}


def score_unapproved_candidate_validation_panel(agent, candidate: int,
                                                 worlds: list[dict]) -> dict:
    """Report every outcome for one proposal over a common generated validation panel."""
    if not worlds:
        raise ValueError("at least one validation world is required")
    world_ids = [world.get("world_id") for world in worlds]
    if any(not world_id for world_id in world_ids) or len(world_ids) != len(set(world_ids)):
        raise ValueError("validation world IDs must be present and unique")
    families = {world.get("family") for world in worlds}
    if len(families) != 1:
        raise ValueError("one candidate validation panel must use exactly one family")
    outcomes = [score_unapproved_candidate_on_validation(agent, candidate, world)
                for world in worlds]
    attrs = agent.s.node(candidate)["attrs"]
    payload = {"schema": "p22_unapproved_candidate_validation_panel_v1",
        "candidate_id": str(candidate), "expression_digest": attrs["expression_digest"],
        "family": next(iter(families)), "world_ids": world_ids,
        "scores": [outcome["score"] for outcome in outcomes]}
    panel_digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return {"status": "nonactionable_validation_panel_scored",
        "actionable": False, "approval_created": False,
        "world_receipts_created": False, "candidate_id": str(candidate),
        "expression_digest": attrs["expression_digest"],
        "family": next(iter(families)), "split": "validation",
        "world_ids": world_ids,
        "world_count": len(outcomes), "successes": sum(x["score"] for x in outcomes),
        "mean_score": sum(x["score"] for x in outcomes) / len(outcomes),
        "panel_digest": panel_digest, "outcomes": outcomes}


@dataclass(frozen=True)
class CheckpointExpression:
    checkpoint_id: str
    parent_digest: str
    expression_digest: str
    params: tuple[int, ...]
    declared_primitive_work: int
    generation: int = 0
    checkpoint_digest: str = ""
    approval_id: str | None = None
    receipt_id: str | None = None
    cumulative_primitive_work: int | None = None
    resource_snapshot_json: str | None = None
    # Complete graph state captured alongside the compact resource summary.
    # The latter is sufficient for accounting, but cannot restore a learner's
    # active portfolio or provenance graph for a later generation.
    native_graph_snapshot_json: str | None = None


def _native_graph_snapshot(agent) -> str:
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    if native is None:
        raise TypeError("agent must expose a native substrate")
    graph = native.graph_to_dict()
    return json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str)


def _native_graph_snapshot_digest(snapshot_json: str | None) -> str | None:
    if not isinstance(snapshot_json, str):
        return None
    try:
        graph = json.loads(snapshot_json)
    except (TypeError, ValueError):
        return None
    canonical = json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str)
    if canonical != snapshot_json:
        return None
    return hashlib.sha256(canonical.encode()).hexdigest()


def _native_graph_contains_expression(snapshot_json: str, expression_digest: str,
                                     params: tuple[int, ...], generation: int) -> bool:
    try:
        graph = json.loads(snapshot_json)
        nodes = graph["nodes"]
    except (TypeError, ValueError, KeyError):
        return False
    expected_params = list(params)
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("attrs"), dict):
            continue
        attrs = node["attrs"]
        graph_params = attrs.get("params")
        if isinstance(graph_params, dict) and set(graph_params) == {"__list__"}:
            graph_params = graph_params["__list__"]
        if node.get("type") == "ProcessSchema":
            if (attrs.get("status") == "active"
                    and attrs.get("source_digest") == expression_digest
                    and graph_params == expected_params):
                return True
        if generation > 0 and node.get("type") == "OpenProcessCandidate":
            if (attrs.get("status") == "adopted_candidate"
                    and attrs.get("adoption_status") == "approved"
                    and attrs.get("adopted_expression_digest") == expression_digest
                    and graph_params == expected_params):
                return True
    return False


def _checkpoint_graph_params(checkpoint: CheckpointExpression) -> tuple[int, ...]:
    """Resolve the scored process from the checkpoint's immutable native graph.

    ``CheckpointExpression.params`` is retained as a compact manifest field,
    but it is not the source of truth for a strict evaluation. Generation zero
    resolves an active ProcessSchema; descendants resolve their approved,
    adopted candidate. A graph with no matching process, or one whose stored
    process disagrees with the manifest, is not scoreable.
    """
    if checkpoint.native_graph_snapshot_json is None:
        raise ValueError("checkpoint has no native graph process")
    try:
        graph = json.loads(checkpoint.native_graph_snapshot_json)
        nodes = graph["nodes"]
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("checkpoint native graph is malformed") from exc
    matches = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("attrs"), dict):
            continue
        kind, attrs = node.get("type"), node["attrs"]
        if checkpoint.generation == 0 or checkpoint.receipt_id is None:
            # Passive controls preserve the ancestor expression without an
            # adoption receipt, even after advancing the checkpoint generation.
            matches_expression = (kind == "ProcessSchema"
                and attrs.get("status") == "active"
                and attrs.get("source_digest") == checkpoint.expression_digest)
        else:
            matches_expression = (kind == "OpenProcessCandidate"
                and attrs.get("status") == "adopted_candidate"
                and attrs.get("adoption_status") == "approved"
                and attrs.get("adopted_expression_digest") == checkpoint.expression_digest)
        if not matches_expression:
            continue
        params = attrs.get("params")
        if isinstance(params, dict) and set(params) == {"__list__"}:
            params = params["__list__"]
        if (isinstance(params, list)
                and all(not isinstance(value, bool) and isinstance(value, int)
                        for value in params)):
            matches.append(tuple(params))
    if not matches or any(params != tuple(checkpoint.params) for params in matches):
        raise ValueError("checkpoint native graph process does not match its manifest")
    return matches[0]


def restore_native_checkpoint_graph(agent, checkpoint: CheckpointExpression) -> str:
    """Restore a captured graph into a freshly booted agent and verify identity.

    Seed/rule loading belongs to the normal agent boot path. This function
    restores only the checkpointed native graph state, then checks an exact
    canonical round trip before the caller resumes native execution.
    """
    if not _checkpoint_digest_valid(checkpoint):
        raise ValueError("cannot restore an unattested native checkpoint")
    if checkpoint.native_graph_snapshot_json is None:
        raise ValueError("checkpoint is missing its immutable native graph snapshot")
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    if native is None:
        raise TypeError("agent must expose a native substrate")
    graph = json.loads(checkpoint.native_graph_snapshot_json)
    native.graph_from_dict(graph)
    restored = json.dumps(native.graph_to_dict(), sort_keys=True,
                          separators=(",", ":"), default=str)
    if restored != checkpoint.native_graph_snapshot_json:
        raise ValueError("restored native checkpoint graph differs from its snapshot")
    return _native_graph_snapshot_digest(restored)


def _checkpoint_digest_valid(checkpoint: CheckpointExpression) -> bool:
    if (isinstance(checkpoint.cumulative_primitive_work, bool)
            or not isinstance(checkpoint.cumulative_primitive_work, int)
            or checkpoint.cumulative_primitive_work < checkpoint.declared_primitive_work):
        return False
    if not isinstance(checkpoint.resource_snapshot_json, str):
        return False
    try:
        resource_snapshot = json.loads(checkpoint.resource_snapshot_json)
    except (TypeError, ValueError):
        return False
    if not resource_snapshot_digest_valid(resource_snapshot):
        return False
    graph_snapshot_digest = _native_graph_snapshot_digest(
        checkpoint.native_graph_snapshot_json)
    if checkpoint.native_graph_snapshot_json is not None and graph_snapshot_digest is None:
        return False
    if (graph_snapshot_digest is not None and not _native_graph_contains_expression(
            checkpoint.native_graph_snapshot_json, checkpoint.expression_digest,
            checkpoint.params, checkpoint.generation)):
        return False
    if checkpoint.generation == 0:
        payload = {"schema": "p22_native_checkpoint_v1",
            "checkpoint_id": checkpoint.checkpoint_id, "generation": 0,
            "source_digest": checkpoint.expression_digest,
            "params": list(checkpoint.params),
            "primitive_work": checkpoint.declared_primitive_work,
            "cumulative_primitive_work": checkpoint.cumulative_primitive_work,
            "resource_snapshot_sha256": resource_snapshot["snapshot_sha256"]}
        if graph_snapshot_digest is not None:
            payload["native_graph_snapshot_sha256"] = graph_snapshot_digest
    elif checkpoint.generation > 0:
        payload = {"schema": "p22_native_checkpoint_v1",
            "checkpoint_id": checkpoint.checkpoint_id,
            "parent_digest": checkpoint.parent_digest,
            "generation": checkpoint.generation,
            "expression_digest": checkpoint.expression_digest,
            "params": list(checkpoint.params),
            "primitive_work": checkpoint.declared_primitive_work,
            "cumulative_primitive_work": checkpoint.cumulative_primitive_work,
            "resource_snapshot_sha256": resource_snapshot["snapshot_sha256"]}
        if graph_snapshot_digest is not None:
            payload["native_graph_snapshot_sha256"] = graph_snapshot_digest
        if checkpoint.approval_id and checkpoint.receipt_id:
            payload["approval_id"] = checkpoint.approval_id
            payload["receipt_id"] = checkpoint.receipt_id
        elif checkpoint.approval_id or checkpoint.receipt_id:
            return False
    else:
        return False
    expected = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return checkpoint.checkpoint_digest == expected


def _validate_descendant_runtime_counters(parent: CheckpointExpression,
                                          runtime_counters: dict | None,
                                          native_rule_work: dict | None = None) -> None:
    """Prevent a descendant snapshot from dropping/regressing cumulative work."""
    if not parent.resource_snapshot_json:
        return
    parent_snapshot = json.loads(parent.resource_snapshot_json)
    previous = parent_snapshot.get("runtime_counters")
    if previous is not None:
        if not isinstance(runtime_counters, dict):
            raise ValueError("descendant checkpoint must retain cumulative runtime counters")
        for key in ("native_rule_steps", "native_model_calls",
                    "search_attempts_reserved", "process_peak_rss_bytes"):
            if key not in previous:
                continue
            value = runtime_counters.get(key)
            if (isinstance(value, bool) or not isinstance(value, int)
                    or value < previous[key]):
                raise ValueError(f"descendant checkpoint runtime counter regressed: {key}")
        if "wall_time_seconds" in previous:
            value = runtime_counters.get("wall_time_seconds")
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < previous["wall_time_seconds"]):
                raise ValueError("descendant checkpoint runtime counter regressed: wall_time_seconds")
    previous_rule_work = parent_snapshot.get("native_rule_work")
    if previous_rule_work is not None:
        if native_rule_work is None or not native_rule_work_digest_valid(native_rule_work):
            raise ValueError("descendant checkpoint must retain cumulative native rule work")
        prior_totals = previous_rule_work.get("totals_by_metric", {})
        current_totals = native_rule_work.get("totals_by_metric", {})
        for key, prior in prior_totals.items():
            current = current_totals.get(key)
            if (isinstance(current, bool) or not isinstance(current, int)
                    or current < prior):
                raise ValueError(f"descendant checkpoint native rule work regressed: {key}")


def capture_held_process_checkpoint(agent, process_schema: int, *,
                                    checkpoint_id: str,
                                    declared_primitive_work: int = 0,
                                    runtime_counters: dict | None = None,
                                    native_rule_work: dict | None = None) -> CheckpointExpression:
    """Create generation-zero evidence and bind any measured runtime counters.

    Callers that track cumulative native work should pass those measured
    counters here and to every descendant capture. The immutable resource
    snapshot then carries the counters into checkpoint scoring/comparison.
    """
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    store = getattr(agent, "s", None)
    if native is None or store is None:
        raise TypeError("agent must expose native substrate and graph store")
    if not checkpoint_id:
        raise ValueError("checkpoint identity is required")
    if (isinstance(declared_primitive_work, bool)
            or not isinstance(declared_primitive_work, int)
            or declared_primitive_work < 0):
        raise ValueError("checkpoint primitive work must be a nonnegative integer")
    node = store.node(process_schema)
    if node["type"] != "ProcessSchema":
        raise ValueError("ancestor must be a native ProcessSchema")
    attrs = node["attrs"]
    params = attrs.get("params")
    if (attrs.get("status") != "active" or not isinstance(params, list)
            or not all(isinstance(x, int) for x in params)
            or attrs.get("source_digest") != params_digest(params)):
        raise ValueError("ancestor process is inactive or has an invalid source digest")
    work = declared_primitive_work
    resource_snapshot = snapshot_native_resources(agent,
        runtime_counters=runtime_counters, native_rule_work=native_rule_work)
    resource_json = json.dumps(resource_snapshot, sort_keys=True,
                               separators=(",", ":"))
    graph_json = _native_graph_snapshot(agent)
    payload = {"schema": "p22_native_checkpoint_v1", "checkpoint_id": checkpoint_id,
        "generation": 0, "source_digest": attrs["source_digest"],
        "params": params, "primitive_work": work,
        "cumulative_primitive_work": work,
        "resource_snapshot_sha256": resource_snapshot["snapshot_sha256"],
        "native_graph_snapshot_sha256": _native_graph_snapshot_digest(graph_json)}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return CheckpointExpression(checkpoint_id, "", attrs["source_digest"],
        tuple(params), work, 0, digest,
        cumulative_primitive_work=work, resource_snapshot_json=resource_json,
        native_graph_snapshot_json=graph_json)


def capture_passive_checkpoint(agent, *, checkpoint_id: str,
                               parent: CheckpointExpression, generation: int,
                               declared_primitive_work: int,
                               runtime_counters: dict | None = None,
                               native_rule_work: dict | None = None) -> CheckpointExpression:
    """Record a no-adoption descendant while preserving its exact expression.

    This supports unchanged and adaptive-only evaluation arms. It creates no
    approval, candidate adoption, or world-action receipt.
    """
    if (not checkpoint_id or not _checkpoint_digest_valid(parent)
            or generation < 1 or generation != parent.generation + 1):
        raise ValueError("passive checkpoint must extend its frozen parent by one generation")
    if (isinstance(declared_primitive_work, bool)
            or not isinstance(declared_primitive_work, int)
            or declared_primitive_work < 0):
        raise ValueError("checkpoint primitive work must be a nonnegative integer")
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    store = getattr(agent, "s", None)
    if native is None or store is None:
        raise TypeError("agent must expose native substrate and graph store")
    work = declared_primitive_work
    cumulative_work = parent.cumulative_primitive_work + work
    _validate_descendant_runtime_counters(parent, runtime_counters,
                                          native_rule_work)
    resource_snapshot = snapshot_native_resources(agent,
        runtime_counters=runtime_counters, native_rule_work=native_rule_work)
    resource_json = json.dumps(resource_snapshot, sort_keys=True,
                               separators=(",", ":"))
    graph_json = _native_graph_snapshot(agent)
    params = list(parent.params)
    payload = {"schema": "p22_native_checkpoint_v1",
        "checkpoint_id": checkpoint_id, "parent_digest": parent.checkpoint_digest,
        "generation": int(generation), "expression_digest": parent.expression_digest,
        "params": params, "primitive_work": work,
        "cumulative_primitive_work": cumulative_work,
        "resource_snapshot_sha256": resource_snapshot["snapshot_sha256"],
        "native_graph_snapshot_sha256": _native_graph_snapshot_digest(graph_json)}
    frozen_digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return CheckpointExpression(checkpoint_id, parent.checkpoint_digest,
        parent.expression_digest, parent.params, work, int(generation),
        frozen_digest, cumulative_primitive_work=cumulative_work,
        resource_snapshot_json=resource_json,
        native_graph_snapshot_json=graph_json)


def capture_adopted_checkpoint(agent, candidate: int, *, checkpoint_id: str,
                               parent: CheckpointExpression, generation: int,
                               declared_primitive_work: int,
                               runtime_counters: dict | None = None,
                               native_rule_work: dict | None = None) -> CheckpointExpression:
    """Freeze an adopted candidate only after its exact approval and world receipt.

    This captures graph-authored expression provenance into an immutable value;
    it does not create approval or turn a proposal into an actionable candidate.
    """
    if (not checkpoint_id or not _checkpoint_digest_valid(parent) or generation < 1
            or generation != parent.generation + 1):
        raise ValueError("checkpoint must extend a frozen immediate parent by one generation")
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    store = getattr(agent, "s", None)
    if native is None or store is None:
        raise TypeError("agent must expose native substrate and graph store")
    attrs = store.node(candidate)["attrs"]
    if attrs.get("status") != "adopted_candidate" or attrs.get("adoption_status") != "approved":
        raise ValueError("checkpoint candidate is not adopted")
    current_digest = open_process_candidate_digest(agent, candidate)
    if (current_digest != attrs.get("expression_digest")
            or current_digest != attrs.get("adopted_expression_digest")):
        raise ValueError("checkpoint expression no longer matches its adopted digest")
    approvals = list(native.neighbours(candidate, "approved_by_open_process_adoption"))
    receipts = list(native.neighbours(candidate, "has_world_execution_receipt"))
    if len(approvals) != 1 or len(receipts) != 1:
        raise ValueError("checkpoint requires one exact approval and one execution receipt")
    approval = store.node(approvals[0])["attrs"]
    if approval.get("status") != "consumed" or approval.get("approval_kind") != "human":
        raise ValueError("checkpoint approval is not consumed human approval")
    for key in ("expression_digest", "expression_key", "expression_tree", "effect_digest",
                "params", "guard_state", "domain", "source_epoch", "model_epoch", "frame_epoch"):
        if approval.get(key) != attrs.get(key):
            raise ValueError("checkpoint approval binding changed")
    receipt = store.node(receipts[0])["attrs"]
    if (receipt.get("status") != "verified"
            or receipt.get("expression_digest") != current_digest
            or receipt.get("params_digest") != params_digest(attrs.get("params"))
            or receipt.get("effect_digest") != attrs.get("effect_digest")):
        raise ValueError("checkpoint requires a matching verified execution receipt")
    params = attrs.get("params")
    if not isinstance(params, list) or not all(isinstance(x, int) for x in params):
        raise ValueError("checkpoint expression is outside supported integer permutation domain")
    if (isinstance(declared_primitive_work, bool)
            or not isinstance(declared_primitive_work, int)
            or declared_primitive_work < 0):
        raise ValueError("checkpoint primitive work must be a nonnegative integer")
    work = declared_primitive_work
    cumulative_work = parent.cumulative_primitive_work + work
    _validate_descendant_runtime_counters(parent, runtime_counters,
                                          native_rule_work)
    resource_snapshot = snapshot_native_resources(agent,
        runtime_counters=runtime_counters, native_rule_work=native_rule_work)
    resource_json = json.dumps(resource_snapshot, sort_keys=True,
                               separators=(",", ":"))
    graph_json = _native_graph_snapshot(agent)
    payload = {"schema": "p22_native_checkpoint_v1", "checkpoint_id": checkpoint_id,
        "parent_digest": parent.checkpoint_digest, "generation": int(generation),
        "expression_digest": current_digest, "params": params,
        "primitive_work": work, "cumulative_primitive_work": cumulative_work,
        "resource_snapshot_sha256": resource_snapshot["snapshot_sha256"],
        "native_graph_snapshot_sha256": _native_graph_snapshot_digest(graph_json),
        "approval_id": str(approvals[0]), "receipt_id": str(receipts[0])}
    frozen_digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return CheckpointExpression(checkpoint_id, parent.checkpoint_digest, current_digest,
        tuple(params), work, int(generation), frozen_digest,
        str(approvals[0]), str(receipts[0]), cumulative_work, resource_json, graph_json)


class CheckpointWorldAdapter:
    """Evaluate explicit finite-process expressions without arm-name dispatch."""

    def __init__(self, native, *, primitive_work_ceiling: int,
                 allow_unattested_fixtures: bool = False):
        if primitive_work_ceiling <= 0:
            raise ValueError("primitive work ceiling must be positive")
        self.native = native
        self.primitive_work_ceiling = int(primitive_work_ceiling)
        self.allow_unattested_fixtures = bool(allow_unattested_fixtures)

    @staticmethod
    def _checkpoint_digest_valid(checkpoint: CheckpointExpression) -> bool:
        return _checkpoint_digest_valid(checkpoint)

    def score(self, checkpoint: CheckpointExpression, *, world_id: str,
              initial_state: list[int], goal_state: list[int]) -> dict:
        if not world_id:
            raise ValueError("world identity is required")
        work = checkpoint.declared_primitive_work
        if isinstance(work, bool) or not isinstance(work, int) or work < 0:
            raise ValueError("declared primitive work must be a nonnegative integer")
        cumulative_work = checkpoint.cumulative_primitive_work
        if cumulative_work is None and self.allow_unattested_fixtures:
            cumulative_work = work
        if (isinstance(cumulative_work, bool) or not isinstance(cumulative_work, int)
                or cumulative_work < work):
            raise ValueError("cumulative primitive work must include nonnegative checkpoint work")
        params = checkpoint.params
        if (not isinstance(params, tuple) or len(params) < 2
                or any(isinstance(value, bool) or not isinstance(value, int)
                       for value in params)
                or sorted(params) != list(range(len(params)))):
            raise ValueError("checkpoint parameters must be a finite permutation")
        for label, state in (("initial", initial_state), ("goal", goal_state)):
            if (not isinstance(state, list) or len(state) != len(params)
                    or any(isinstance(value, bool) or not isinstance(value, int)
                           for value in state)
                    or sorted(state) != list(range(len(params)))):
                raise ValueError(f"{label} state must match the finite permutation domain")
        if (not self._checkpoint_digest_valid(checkpoint)
                and not self.allow_unattested_fixtures):
            raise ValueError("checkpoint is not an intact attested native snapshot")
        if (checkpoint.native_graph_snapshot_json is None
                and not self.allow_unattested_fixtures):
            raise ValueError("checkpoint is missing its immutable native graph snapshot")
        if cumulative_work > self.primitive_work_ceiling:
            return {"world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                    "status": "work_denied", "score": None,
                    "primitive_work": work,
                    "cumulative_primitive_work": cumulative_work,
                    "resource_snapshot": (json.loads(checkpoint.resource_snapshot_json)
                        if checkpoint.resource_snapshot_json else None)}
        execution_params = (tuple(checkpoint.params)
            if checkpoint.native_graph_snapshot_json is None
            and self.allow_unattested_fixtures
            else _checkpoint_graph_params(checkpoint))
        result = self.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": list(execution_params), "state": list(initial_state)})
        return {"world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                "parent_digest": checkpoint.parent_digest,
                "expression_digest": checkpoint.expression_digest,
                "status": "scored", "score": int(result == goal_state),
                "execution_source": ("native_checkpoint_graph"
                    if checkpoint.native_graph_snapshot_json is not None
                    else "development_fixture_params"),
                "primitive_work": work,
                "cumulative_primitive_work": cumulative_work,
                "resource_snapshot": (json.loads(checkpoint.resource_snapshot_json)
                    if checkpoint.resource_snapshot_json else None),
                "initial_state": list(initial_state), "goal_state": list(goal_state),
                "result_state": result}

    def compare(self, checkpoints: tuple[CheckpointExpression, CheckpointExpression],
                worlds: list[dict]) -> dict:
        if len(checkpoints) < 2:
            raise ValueError("at least two checkpoints are required")
        checkpoint_ids = [checkpoint.checkpoint_id for checkpoint in checkpoints]
        if any(not checkpoint_id for checkpoint_id in checkpoint_ids):
            raise ValueError("checkpoint identities are required")
        if len(checkpoint_ids) != len(set(checkpoint_ids)):
            raise ValueError("checkpoint identities must be unique")
        if not worlds:
            raise ValueError("at least one common world is required")
        ids = [world["world_id"] for world in worlds]
        if len(ids) != len(set(ids)):
            raise ValueError("world IDs must be unique within a checkpoint block")
        rows = []
        for world in worlds:
            pair = [self.score(checkpoint, world_id=world["world_id"],
                               initial_state=world["initial_state"],
                               goal_state=world["goal_state"])
                    for checkpoint in checkpoints]
            resource_snapshots = {outcome["checkpoint_id"]: outcome["resource_snapshot"]
                for outcome in pair if outcome["resource_snapshot"] is not None}
            same_resources = (len(resource_snapshots) == len(pair)
                and compare_resource_snapshots(resource_snapshots)[
                    "all_resource_dimensions_match"] if resource_snapshots else
                self.allow_unattested_fixtures)
            rows.append({"world_id": world["world_id"], "outcomes": pair,
                         "same_world": all(x["world_id"] == world["world_id"] for x in pair),
                         "same_work": len({x["cumulative_primitive_work"]
                                            for x in pair}) == 1,
                         "same_resource_usage": same_resources})
        return {"status": "COMPLETED",
                "same_worlds": all(row["same_world"] for row in rows),
                "efficiency_comparable": all(row["same_work"] for row in rows)
                    and all(row["same_resource_usage"] for row in rows)
                    and all(outcome["status"] == "scored"
                            for row in rows for outcome in row["outcomes"]),
                "rows": rows}


def score_restored_checkpoint_task(checkpoint: CheckpointExpression, *,
                                  world: dict,
                                  agent_factory,
                                  cumulative_primitive_ceiling: int = 30_000,
                                  native_rule_progress_ceiling: int = 20_000) -> dict:
    """Run a fresh native learner graph restored from a checkpoint on one task.

    This is a development continuation primitive, distinct from the finite
    expression scorer above. The caller supplies the normal learner boot path;
    this function restores only the immutable graph and lets its native rules
    process the task. It creates no approval or simulated-world receipt.
    """
    if not _checkpoint_digest_valid(checkpoint):
        raise ValueError("cannot evaluate an unattested native checkpoint")
    if checkpoint.native_graph_snapshot_json is None:
        raise ValueError("checkpoint is missing its immutable native graph snapshot")
    if not isinstance(world, dict):
        raise ValueError("a registered training-world view is required")
    generators = {
        "pmb_generated_d4_corner_v2": generate_d4_world_v2,
        "pmb_generated_loopover_v2": generate_loopover_world_v2,
    }
    generator = generators.get(world.get("family"))
    draw = world.get("draw")
    if (generator is None or world.get("split") != "train"
            or isinstance(draw, bool) or not isinstance(draw, int)
            or not 0 <= draw < 1000):
        raise ValueError("checkpoint continuation accepts only registered training worlds")
    expected_world = agent_view(generator(split="train", draw=draw))
    if world != expected_world:
        raise ValueError("task must exactly match its registered training-world view")
    world_id = world["world_id"]
    initial_state = world["initial_state"]
    goal_state = world["goal_state"]
    if (isinstance(cumulative_primitive_ceiling, bool)
            or not isinstance(cumulative_primitive_ceiling, int)
            or not 1 <= cumulative_primitive_ceiling <= 120_000):
        raise ValueError("cumulative primitive ceiling must be an integer in [1, 120000]")
    if checkpoint.cumulative_primitive_work > cumulative_primitive_ceiling:
        raise ValueError("checkpoint cumulative work exceeds the shared primitive ceiling")
    if (isinstance(native_rule_progress_ceiling, bool)
            or not isinstance(native_rule_progress_ceiling, int)
            or not 1 <= native_rule_progress_ceiling <= 10_000_000):
        raise ValueError("native rule-progress ceiling must be an integer in [1, 10000000]")
    params = _checkpoint_graph_params(checkpoint)
    if (not isinstance(initial_state, list) or not isinstance(goal_state, list)
            or any(isinstance(value, bool) or not isinstance(value, int)
                   for value in initial_state + goal_state)
            or len(initial_state) != len(params) or len(goal_state) != len(params)
            or sorted(initial_state) != list(range(len(params)))
            or sorted(goal_state) != list(range(len(params)))):
        raise ValueError("task states must be permutations matching checkpoint domain")

    agent = agent_factory()
    rule_capture = None
    try:
        restore_native_checkpoint_graph(agent, checkpoint)
        native = getattr(agent, "inner", None) or getattr(agent, "native", None)
        store = getattr(agent, "s", None)
        root = getattr(agent, "agent", None) or getattr(agent, "ag", None)
        if native is None or store is None or root is None:
            raise TypeError("agent factory must return a native graph learner")
        solver_policies = store.nodes("SolverPolicy")
        if len(solver_policies) != 1:
            raise ValueError("checkpoint learner requires exactly one native SolverPolicy")
        solver_policy = solver_policies[0]
        if store.node(solver_policy)["attrs"].get("enabled") != 1.0:
            raise ValueError("checkpoint learner SolverPolicy must be explicitly enabled")
        solver_step_allowance = (cumulative_primitive_ceiling
                                 - checkpoint.cumulative_primitive_work)
        store.set_attr(solver_policy, "max_steps", float(solver_step_allowance))
        baseline_approvals = len(store.nodes("OpenProcessAdoptionApproval"))
        baseline_receipts = len(store.nodes("OpenProcessWorldReceipt"))
        task_key = f"p22-checkpoint-eval:{world_id}"
        graph_nodes = json.loads(checkpoint.native_graph_snapshot_json)["nodes"]
        domain_names = [node.get("attrs", {}).get("domain") for node in graph_nodes
            if node.get("type") == "ProcessSchema"
            and node.get("attrs", {}).get("status") == "active"
            and node.get("attrs", {}).get("source_digest") == checkpoint.expression_digest
            and node.get("attrs", {}).get("domain")]
        if len(set(domain_names)) > 1:
            raise ValueError("checkpoint expression resolves to multiple native domains")
        domain_name = domain_names[0] if domain_names else f"p22-checkpoint-domain:{len(params)}"
        domains = [node for node in store.nodes("ProcessDomain")
                   if store.node(node)["attrs"].get("name") == domain_name]
        if len(domains) > 1:
            raise ValueError("checkpoint learner graph has duplicate native domain identities")
        domain = domains[0] if domains else store.add_node("ProcessDomain", {
            "name": domain_name, "kind": "permutation", "domain_kind": "permutation",
            "object_count": float(len(params)), "probes": [list(initial_state)],
            "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
            "probe_epoch": 0})
        if not domains:
            store.add_edge(root, "has_process_domain", domain, {})
        held_process_nodes = [node for node in store.nodes("ProcessSchema")
            if store.node(node)["attrs"].get("domain") == domain_name]
        for process_name, process_params in sorted(world["held_processes"].items()):
            matches = [node for node in held_process_nodes
                if store.node(node)["attrs"].get("name") == process_name]
            if matches:
                if any(store.node(node)["attrs"].get("params") != process_params
                       or store.node(node)["attrs"].get("status") != "active"
                       or store.node(node)["attrs"].get("source_digest")
                          != params_digest(process_params) for node in matches):
                    raise ValueError("checkpoint domain conflicts with registered world process")
                continue
            schema = store.add_node("ProcessSchema", {
                "name": process_name, "kind": "permutation",
                "domain": domain_name, "domain_kind": "permutation",
                "params": list(process_params),
                "source_digest": params_digest(list(process_params)),
                "cost": 1.0, "status": "active", "provenance": "world_affordance",
                "invariants": [], "owner_agent": root, "source_epoch": 0,
                "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0,
                "source_probe_epoch": 0})
            store.add_edge(root, "has_process_schema", schema, {})
            store.add_edge(domain, "has_held_process", schema, {})
        if any(store.node(node)["attrs"].get("task_key") == task_key
               for node in store.nodes("SolveTask")):
            raise ValueError("checkpoint graph already contains this evaluation task identity")
        task = store.add_node("SolveTask", {
            "task_key": task_key, "domain": domain_name,
            "initial_state": list(initial_state), "state": list(initial_state),
            "goal": list(goal_state), "object_count": float(len(params)),
            "status": "active", "trace": [], "steps": 0, "moves": 0.0,
            "stuck_count": 0, "split": "training",
            "training_trial_key": world_id})
        store.add_edge(root, "has_solve_task", task, {})
        store.add_edge(task, "about_domain", domain, {})
        fired_total = 0
        rounds = 0
        quiescent = False
        rule_progress_limit_respected = True
        started = time.perf_counter()
        rule_capture = NativeRuleWorkCapture(native).start()
        while fired_total < native_rule_progress_ceiling:
            remaining = native_rule_progress_ceiling - fired_total
            fired = int(native.run_rules(min(20_000, remaining)))
            if fired < 0:
                raise RuntimeError("native rule runner returned negative progress")
            fired_total += fired
            rounds += 1
            if fired > remaining:
                rule_progress_limit_respected = False
                break
            if fired == 0:
                quiescent = True
                break
        attrs = store.node(task)["attrs"]
        wall_time = time.perf_counter() - started
        increment_rule_work = rule_capture.finish()
        rule_capture = None
        checkpoint_snapshot = json.loads(checkpoint.resource_snapshot_json)
        parent_runtime = checkpoint_snapshot.get("runtime_counters") or {}
        parent_rule_work = checkpoint_snapshot.get("native_rule_work")
        native_rule_work = (merge_native_rule_work_snapshots(
            parent_rule_work, increment_rule_work) if parent_rule_work is not None
            else increment_rule_work)
        runtime_counters = {
            "native_rule_steps": int(parent_runtime.get("native_rule_steps", 0))
                + fired_total,
            "native_model_calls": int(parent_runtime.get("native_model_calls", 0)),
        }
        search_policies = store.nodes("OpenProcessSearchPolicy")
        if len(search_policies) == 1:
            reserved = store.node(search_policies[0])["attrs"].get("attempts_reserved", 0)
            if (isinstance(reserved, bool) or not isinstance(reserved, (int, float))
                    or not math.isfinite(reserved) or reserved < 0
                    or not float(reserved).is_integer()):
                raise ValueError("restored search reservation counter is invalid")
            runtime_counters["search_attempts_reserved"] = int(reserved)
        if "native_candidate_validation_evaluations" in parent_runtime:
            runtime_counters["native_candidate_validation_evaluations"] = int(
                parent_runtime["native_candidate_validation_evaluations"])
        resource_snapshot = snapshot_native_resources(agent,
            runtime_counters=runtime_counters, native_rule_work=native_rule_work)
        cumulative_resources = resource_snapshot["cumulative_resources"]
        cumulative_primitive_value = (
            cumulative_resources.get("native_solver_primitive_work", 0)
            + cumulative_resources.get("search_declared_primitive_work", 0))
        if (isinstance(cumulative_primitive_value, bool)
                or not isinstance(cumulative_primitive_value, (int, float))
                or not math.isfinite(cumulative_primitive_value)
                or cumulative_primitive_value < 0
                or not float(cumulative_primitive_value).is_integer()):
            raise ValueError("restored learner primitive-work total is invalid")
        cumulative_primitive_work = int(cumulative_primitive_value)
        if cumulative_primitive_work < checkpoint.cumulative_primitive_work:
            raise ValueError("restored learner resource totals regress checkpoint primitive work")
        primitive_budget_respected = cumulative_primitive_work <= cumulative_primitive_ceiling
        terminal = attrs.get("status") in {"solved", "stuck"}
        status = ("PRIMITIVE_BUDGET_OVERRUN" if not primitive_budget_respected else
            "RULE_PROGRESS_LIMIT_OVERRUN" if not rule_progress_limit_respected else
            "COMPLETED" if terminal else "RULE_BUDGET_EXHAUSTED")
        return {"status": status,
                "world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                "task_status": attrs.get("status"),
                "score": int(attrs.get("status") == "solved"),
                "native_rule_steps": fired_total,
                "native_rule_progress_ceiling": native_rule_progress_ceiling,
                "rule_progress_limit_respected": rule_progress_limit_respected,
                "evaluation_wall_time_seconds": wall_time,
                "cumulative_primitive_work": cumulative_primitive_work,
                "cumulative_primitive_ceiling": cumulative_primitive_ceiling,
                "primitive_budget_respected": primitive_budget_respected,
                "rule_rounds": rounds,
                "quiescent": quiescent,
                "approval_events_added": (len(store.nodes("OpenProcessAdoptionApproval"))
                                           - baseline_approvals),
                "world_receipts_added": (len(store.nodes("OpenProcessWorldReceipt"))
                                          - baseline_receipts),
                "resource_snapshot": resource_snapshot}
    finally:
        if rule_capture is not None:
            rule_capture.close()
        close = getattr(agent, "close", None)
        if close is not None:
            close()


def compare_restored_checkpoint_panel(checkpoints: dict[str, CheckpointExpression],
                                      worlds: list[dict], *, agent_factory,
                                      cumulative_primitive_ceiling: int = 30_000,
                                      native_rule_progress_ceiling: int = 20_000) -> dict:
    """Compare restored checkpoints on common registered training tasks.

    Each checkpoint/world cell receives a fresh learner, the same cumulative
    primitive-work ceiling, and the same native rule-progress limit. The
    native scheduler can exceed a requested progress limit within one call;
    such overruns are retained explicitly. Equal limits are not treated as
    equal realized resource use.
    """
    if not isinstance(checkpoints, dict) or len(checkpoints) < 2:
        raise ValueError("at least two named checkpoints are required")
    if any(not isinstance(name, str) or not name for name in checkpoints):
        raise ValueError("checkpoint comparison names must be nonempty strings")
    checkpoint_ids = [checkpoint.checkpoint_id for checkpoint in checkpoints.values()]
    if any(not identity for identity in checkpoint_ids) or len(set(checkpoint_ids)) != len(checkpoint_ids):
        raise ValueError("checkpoint identities must be present and unique")
    if not isinstance(worlds, list) or not worlds:
        raise ValueError("at least one common registered training world is required")
    world_ids = [world.get("world_id") if isinstance(world, dict) else None
                 for world in worlds]
    if any(not identity for identity in world_ids) or len(set(world_ids)) != len(world_ids):
        raise ValueError("training world identities must be present and unique")
    if (isinstance(cumulative_primitive_ceiling, bool)
            or not isinstance(cumulative_primitive_ceiling, int)
            or not 1 <= cumulative_primitive_ceiling <= 120_000):
        raise ValueError("cumulative primitive ceiling must be an integer in [1, 120000]")
    if (isinstance(native_rule_progress_ceiling, bool)
            or not isinstance(native_rule_progress_ceiling, int)
            or not 1 <= native_rule_progress_ceiling <= 10_000_000):
        raise ValueError("native rule-progress ceiling must be an integer in [1, 10000000]")

    arms = {name: [] for name in checkpoints}
    rows = []
    for world in worlds:
        outcomes = {}
        for name, checkpoint in checkpoints.items():
            outcome = score_restored_checkpoint_task(checkpoint, world=world,
                agent_factory=agent_factory,
                cumulative_primitive_ceiling=cumulative_primitive_ceiling,
                native_rule_progress_ceiling=native_rule_progress_ceiling)
            arms[name].append(outcome)
            outcomes[name] = outcome
        resource_match = compare_resource_snapshots({name: outcome["resource_snapshot"]
            for name, outcome in outcomes.items()})
        rows.append({"world_id": world["world_id"], "outcomes": outcomes,
            "same_world": all(outcome["world_id"] == world["world_id"]
                              for outcome in outcomes.values()),
            "same_native_rule_progress_ceiling": all(outcome[
                "native_rule_progress_ceiling"] == native_rule_progress_ceiling
                for outcome in outcomes.values()),
            "rule_progress_limits_respected": all(outcome[
                "rule_progress_limit_respected"] for outcome in outcomes.values()),
            "primitive_budgets_respected": all(outcome[
                "primitive_budget_respected"] for outcome in outcomes.values()),
            "same_cumulative_primitive_work": len({outcome[
                "cumulative_primitive_work"] for outcome in outcomes.values()}) == 1,
            "resource_comparison": resource_match})
    return {"status": "COMPLETED",
        "split": "training", "world_ids": world_ids,
        "native_rule_progress_ceiling": native_rule_progress_ceiling,
        "cumulative_primitive_ceiling": cumulative_primitive_ceiling,
        "same_worlds": all(row["same_world"] for row in rows),
        "same_native_rule_progress_ceiling": all(
            row["same_native_rule_progress_ceiling"] for row in rows),
        "rule_progress_limits_respected": all(row[
            "rule_progress_limits_respected"] for row in rows),
        "primitive_budgets_respected": all(row["primitive_budgets_respected"]
                                             for row in rows),
        "same_cumulative_primitive_work": all(
            row["same_cumulative_primitive_work"] for row in rows),
        "resource_matched": all(row["resource_comparison"][
            "all_resource_dimensions_match"] for row in rows),
        "efficiency_comparable": all(row["same_cumulative_primitive_work"]
            and row["primitive_budgets_respected"]
            and row["rule_progress_limits_respected"]
            and row["resource_comparison"]["all_resource_dimensions_match"]
            and all(outcome["status"] == "COMPLETED"
                    for outcome in row["outcomes"].values()) for row in rows),
        "arms": {name: {"outcomes": outcomes,
            "solved_count": sum(outcome["score"] for outcome in outcomes),
            "completed_count": sum(outcome["status"] == "COMPLETED"
                                    for outcome in outcomes),
            "native_rule_steps": sum(outcome["native_rule_steps"]
                                      for outcome in outcomes),
            "approval_events_added": sum(outcome["approval_events_added"]
                                         for outcome in outcomes),
            "world_receipts_added": sum(outcome["world_receipts_added"]
                                        for outcome in outcomes)}
            for name, outcomes in arms.items()},
        "rows": rows, "efficacy_established": False}
