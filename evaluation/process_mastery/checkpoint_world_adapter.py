"""Read-only common-world evaluator for immutable native process checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from evaluation.process_mastery.native_process_execution import (
    open_process_candidate_digest, params_digest,
)


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


def _checkpoint_digest_valid(checkpoint: CheckpointExpression) -> bool:
    if (isinstance(checkpoint.cumulative_primitive_work, bool)
            or not isinstance(checkpoint.cumulative_primitive_work, int)
            or checkpoint.cumulative_primitive_work < checkpoint.declared_primitive_work):
        return False
    if checkpoint.generation == 0:
        payload = {"schema": "p22_native_checkpoint_v1",
            "checkpoint_id": checkpoint.checkpoint_id, "generation": 0,
            "source_digest": checkpoint.expression_digest,
            "params": list(checkpoint.params),
            "primitive_work": checkpoint.declared_primitive_work,
            "cumulative_primitive_work": checkpoint.cumulative_primitive_work}
    elif checkpoint.generation > 0 and checkpoint.approval_id and checkpoint.receipt_id:
        payload = {"schema": "p22_native_checkpoint_v1",
            "checkpoint_id": checkpoint.checkpoint_id,
            "parent_digest": checkpoint.parent_digest,
            "generation": checkpoint.generation,
            "expression_digest": checkpoint.expression_digest,
            "params": list(checkpoint.params),
            "primitive_work": checkpoint.declared_primitive_work,
            "cumulative_primitive_work": checkpoint.cumulative_primitive_work,
            "approval_id": checkpoint.approval_id,
            "receipt_id": checkpoint.receipt_id}
    else:
        return False
    expected = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return checkpoint.checkpoint_digest == expected


def capture_held_process_checkpoint(agent, process_schema: int, *,
                                    checkpoint_id: str,
                                    declared_primitive_work: int = 0) -> CheckpointExpression:
    """Create generation-zero parent evidence from an active native process source."""
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
    payload = {"schema": "p22_native_checkpoint_v1", "checkpoint_id": checkpoint_id,
        "generation": 0, "source_digest": attrs["source_digest"],
        "params": params, "primitive_work": work,
        "cumulative_primitive_work": work}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return CheckpointExpression(checkpoint_id, "", attrs["source_digest"],
        tuple(params), work, 0, digest,
        cumulative_primitive_work=work)


def capture_adopted_checkpoint(agent, candidate: int, *, checkpoint_id: str,
                               parent: CheckpointExpression, generation: int,
                               declared_primitive_work: int) -> CheckpointExpression:
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
    payload = {"schema": "p22_native_checkpoint_v1", "checkpoint_id": checkpoint_id,
        "parent_digest": parent.checkpoint_digest, "generation": int(generation),
        "expression_digest": current_digest, "params": params,
        "primitive_work": work, "cumulative_primitive_work": cumulative_work,
        "approval_id": str(approvals[0]), "receipt_id": str(receipts[0])}
    frozen_digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    return CheckpointExpression(checkpoint_id, parent.checkpoint_digest, current_digest,
        tuple(params), work, int(generation), frozen_digest,
        str(approvals[0]), str(receipts[0]), cumulative_work)


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
        if cumulative_work > self.primitive_work_ceiling:
            return {"world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                    "status": "work_denied", "score": None,
                    "primitive_work": work,
                    "cumulative_primitive_work": cumulative_work}
        result = self.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": list(checkpoint.params), "state": list(initial_state)})
        return {"world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                "parent_digest": checkpoint.parent_digest,
                "expression_digest": checkpoint.expression_digest,
                "status": "scored", "score": int(result == goal_state),
                "primitive_work": work,
                "cumulative_primitive_work": cumulative_work,
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
            rows.append({"world_id": world["world_id"], "outcomes": pair,
                         "same_world": all(x["world_id"] == world["world_id"] for x in pair),
                         "same_work": len({x["cumulative_primitive_work"]
                                            for x in pair}) == 1})
        return {"status": "COMPLETED",
                "same_worlds": all(row["same_world"] for row in rows),
                "efficiency_comparable": all(row["same_work"] for row in rows)
                    and all(outcome["status"] == "scored"
                            for row in rows for outcome in row["outcomes"]),
                "rows": rows}
