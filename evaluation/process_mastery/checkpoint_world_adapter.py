"""Read-only common-world evaluator for immutable native process checkpoints."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckpointExpression:
    checkpoint_id: str
    parent_digest: str
    expression_digest: str
    params: tuple[int, ...]
    declared_primitive_work: int


class CheckpointWorldAdapter:
    """Evaluate explicit finite-process expressions without arm-name dispatch."""

    def __init__(self, native, *, primitive_work_ceiling: int):
        if primitive_work_ceiling <= 0:
            raise ValueError("primitive work ceiling must be positive")
        self.native = native
        self.primitive_work_ceiling = int(primitive_work_ceiling)

    def score(self, checkpoint: CheckpointExpression, *, world_id: str,
              initial_state: list[int], goal_state: list[int]) -> dict:
        if not world_id:
            raise ValueError("world identity is required")
        if checkpoint.declared_primitive_work > self.primitive_work_ceiling:
            return {"world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                    "status": "work_denied", "score": None,
                    "primitive_work": checkpoint.declared_primitive_work}
        result = self.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": list(checkpoint.params), "state": list(initial_state)})
        return {"world_id": world_id, "checkpoint_id": checkpoint.checkpoint_id,
                "parent_digest": checkpoint.parent_digest,
                "expression_digest": checkpoint.expression_digest,
                "status": "scored", "score": int(result == goal_state),
                "primitive_work": checkpoint.declared_primitive_work,
                "initial_state": list(initial_state), "goal_state": list(goal_state),
                "result_state": result}

    def compare(self, checkpoints: tuple[CheckpointExpression, CheckpointExpression],
                worlds: list[dict]) -> dict:
        if len(checkpoints) != 2:
            raise ValueError("exactly two checkpoints are required")
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
                         "same_work": pair[0]["primitive_work"] == pair[1]["primitive_work"]})
        return {"status": "COMPLETED",
                "same_worlds": all(row["same_world"] for row in rows),
                "efficiency_comparable": all(row["same_work"] for row in rows)
                    and all(outcome["status"] == "scored"
                            for row in rows for outcome in row["outcomes"]),
                "rows": rows}
