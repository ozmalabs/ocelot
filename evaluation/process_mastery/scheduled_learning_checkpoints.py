"""Immutable, scheduled snapshots for the P27 cumulative-learning study.

This module only captures a supplied native graph and accounting markers. It
does not train, adopt candidates, issue approvals, or execute simulator actions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


CHECKPOINTS = ("g0", "g1", "g2", "g3")
DEFAULT_CUMULATIVE_WORK_THRESHOLDS = (0, 1_000, 2_000, 4_000)
COUNTER_KEYS = (
    "primitive_work", "source_exposure", "native_rule_steps", "graph_bytes",
    "budget_debits", "task_world_accesses",
)
INTERVAL_STATUSES = frozenset({
    "initial", "progress", "no_change", "search_failed",
    "no_candidate_qualified", "authorization_pending", "error",
})


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class ScheduledLearningCheckpoint:
    schema: str
    arm: str
    checkpoint: str
    parent_checkpoint_sha256: str | None
    world_allocation_sha256: str
    state_sha256: str
    graph_snapshot_json: str
    graph_bytes: int
    cumulative: dict[str, int]
    interval_delta: dict[str, int]
    interval_status: str
    pending_candidate_ids: tuple[str, ...]
    approval_ids: tuple[str, ...]
    receipt_ids: tuple[str, ...]
    actionable: bool
    captured_state_changed: bool
    checkpoint_sha256: str


def checkpoint_ready(cumulative_primitive_work: int, next_checkpoint: str,
                     thresholds: tuple[int, ...] = DEFAULT_CUMULATIVE_WORK_THRESHOLDS
                     ) -> bool:
    """Return readiness at a predeclared work marker, independent of outcomes."""
    if next_checkpoint not in CHECKPOINTS:
        raise ValueError("unknown scheduled checkpoint")
    if len(thresholds) != len(CHECKPOINTS) or any(
            isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in thresholds):
        raise ValueError("thresholds must be four nonnegative integer work markers")
    if tuple(sorted(thresholds)) != thresholds:
        raise ValueError("thresholds must be monotonic")
    if isinstance(cumulative_primitive_work, bool) or not isinstance(
            cumulative_primitive_work, int) or cumulative_primitive_work < 0:
        raise ValueError("cumulative work must be a nonnegative integer")
    return cumulative_primitive_work >= thresholds[CHECKPOINTS.index(next_checkpoint)]


def snapshot_native_graph(agent) -> dict:
    """Read the actual native graph only while the profile checkpoint policy is off."""
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    store = getattr(agent, "s", None)
    if native is None or store is None:
        raise TypeError("agent must expose native substrate and typed graph store")
    policies = store.nodes("ScheduledLearningCheckpointPolicy")
    if len(policies) != 1:
        raise ValueError("agent must have exactly one scheduled-checkpoint policy")
    if store.node(policies[0])["attrs"].get("enabled") != 0.0:
        raise ValueError("host checkpoint capture requires the native policy to remain disabled")
    graph = native.graph_to_dict()
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        raise ValueError("native graph export is malformed")
    return graph


def capture_scheduled_checkpoint(*, arm: str, checkpoint: str,
        native_graph: dict, cumulative: dict[str, int], interval_status: str,
        parent: ScheduledLearningCheckpoint | None = None,
        world_allocation_sha256: str,
        pending_candidate_ids: tuple[str, ...] = (),
        approval_ids: tuple[str, ...] = (), receipt_ids: tuple[str, ...] = (),
        thresholds: tuple[int, ...] = DEFAULT_CUMULATIVE_WORK_THRESHOLDS,
        max_graph_bytes: int = 2_000_000,
        max_native_rule_steps: int = 250_000) -> ScheduledLearningCheckpoint:
    """Capture the actual supplied state, retaining unchanged and failed intervals."""
    if not isinstance(arm, str) or not arm:
        raise ValueError("arm identity is required")
    if not isinstance(world_allocation_sha256, str) or len(world_allocation_sha256) != 64:
        raise ValueError("common world allocation SHA-256 is required")
    try:
        int(world_allocation_sha256, 16)
    except ValueError as exc:
        raise ValueError("common world allocation digest must be hexadecimal") from exc
    if checkpoint not in CHECKPOINTS:
        raise ValueError("unknown scheduled checkpoint")
    index = CHECKPOINTS.index(checkpoint)
    if (checkpoint == "g0") != (parent is None):
        raise ValueError("g0 has no parent; later checkpoints require their arm parent")
    if parent is not None:
        if parent.arm != arm or CHECKPOINTS.index(parent.checkpoint) != index - 1:
            raise ValueError("checkpoint ancestry must be consecutive and arm-local")
    if interval_status not in INTERVAL_STATUSES:
        raise ValueError("unknown interval status")
    if not isinstance(native_graph, dict):
        raise ValueError("native graph snapshot must be an object")
    if set(cumulative) != set(COUNTER_KEYS):
        raise ValueError("cumulative counters must include the complete registered set")
    for key, value in cumulative.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"counter {key} must be a nonnegative integer")
    if not checkpoint_ready(cumulative["primitive_work"], checkpoint, thresholds):
        raise ValueError("scheduled checkpoint work marker has not been reached")
    if cumulative["graph_bytes"] > max_graph_bytes:
        raise ValueError("complete dynamic graph exceeds memory ceiling")
    if cumulative["native_rule_steps"] > max_native_rule_steps:
        raise ValueError("native-rule work exceeds ceiling")
    if parent is not None:
        for key in COUNTER_KEYS:
            if key == "graph_bytes":
                continue  # Footprint is a gauge and may shrink after eviction.
            if cumulative[key] < parent.cumulative[key]:
                raise ValueError(f"cumulative {key} regressed across restored branch")
    graph_json = _canonical(native_graph)
    graph_bytes = len(graph_json.encode())
    if cumulative["graph_bytes"] != graph_bytes:
        raise ValueError("graph_bytes counter must equal the complete serialized graph size")
    if graph_bytes > max_graph_bytes:
        raise ValueError("serialized native graph exceeds memory ceiling")
    state_hash = hashlib.sha256(graph_json.encode()).hexdigest()
    changed = parent is None or parent.state_sha256 != state_hash
    if interval_status == "no_change" and changed:
        raise ValueError("no_change status must retain the identical native state hash")
    if interval_status in {"search_failed", "no_candidate_qualified", "authorization_pending"}:
        # These are report labels, not permissions. Preserve provenance, never action.
        actionable = False
    else:
        actionable = False
    delta = {key: value - (parent.cumulative[key] if parent else 0)
             for key, value in cumulative.items()}
    fields = dict(schema="scheduled_learning_checkpoint_v1", arm=arm,
        checkpoint=checkpoint,
        parent_checkpoint_sha256=parent.checkpoint_sha256 if parent else None,
        world_allocation_sha256=world_allocation_sha256,
        state_sha256=state_hash, graph_snapshot_json=graph_json,
        graph_bytes=graph_bytes, cumulative=dict(cumulative), interval_delta=delta,
        interval_status=interval_status,
        pending_candidate_ids=tuple(sorted(pending_candidate_ids)),
        approval_ids=tuple(sorted(approval_ids)), receipt_ids=tuple(sorted(receipt_ids)),
        actionable=actionable, captured_state_changed=changed)
    digest = _sha(fields)
    return ScheduledLearningCheckpoint(**fields, checkpoint_sha256=digest)


def verify_scheduled_checkpoint(checkpoint: ScheduledLearningCheckpoint) -> bool:
    if not isinstance(checkpoint, ScheduledLearningCheckpoint):
        return False
    try:
        graph = json.loads(checkpoint.graph_snapshot_json)
    except (TypeError, ValueError):
        return False
    if _canonical(graph) != checkpoint.graph_snapshot_json:
        return False
    if hashlib.sha256(checkpoint.graph_snapshot_json.encode()).hexdigest() != checkpoint.state_sha256:
        return False
    fields = asdict(checkpoint)
    digest = fields.pop("checkpoint_sha256")
    return digest == _sha(fields)


def verify_common_world_allocation(checkpoints: tuple[ScheduledLearningCheckpoint, ...]
                                   ) -> bool:
    """Require all arms/checkpoints to bind the same sealed task allocation."""
    if not checkpoints or any(not verify_scheduled_checkpoint(x) for x in checkpoints):
        return False
    return len({x.world_allocation_sha256 for x in checkpoints}) == 1
