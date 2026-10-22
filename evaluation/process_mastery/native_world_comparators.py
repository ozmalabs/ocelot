"""World-owned primitive interfaces and independent transition receipts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evaluation.process_mastery import puzzle_worlds


@dataclass
class NativeWorldAdapter:
    """Finite puzzle/tool world boundary shared by every comparator arm."""
    family: str
    state: tuple
    goal: tuple
    actions: dict[str, tuple]
    world_id: str
    epoch: int = 0
    legal_by_state: dict[tuple, tuple[str, ...]] | None = None

    @classmethod
    def from_task(cls, task: dict[str, Any], *, world_id: str | None = None):
        family = task.get("family")
        if family not in {"sliding_3x3", "cube_2x2x2", "tool_goal", "permutation",
                          "state_dependent_tool"}:
            raise ValueError("UNSUPPORTED world family")
        legal_map = task.get("legal_actions_by_state", {})
        return cls(family, tuple(task["initial_state"]), tuple(task["goal_state"]),
                   {k: tuple(v) for k, v in task["primitive_affordances"].items()},
                   world_id or f"{family}:{task.get('seed', 'fixture')}", 0,
                   {tuple(map(int, key.split(","))): tuple(value)
                    for key, value in legal_map.items()})

    def primitive_access(self) -> dict[str, Any]:
        """Return identical goal/action/legality data to baseline and treatment."""
        return {"world_id": self.world_id, "epoch": self.epoch, "goal": self.goal,
                "primitive_actions": tuple(sorted(self.actions)),
                "legal_actions": tuple(sorted(self.legal_actions(self.state)))}

    def legal_actions(self, state) -> tuple[str, ...]:
        state = tuple(state)
        if len(state) != len(self.state):
            return ()
        if self.legal_by_state is not None and state in self.legal_by_state:
            return tuple(sorted(action for action in self.legal_by_state[state]
                                if action in self.actions))
        if self.family == "sliding_3x3":
            blank = state.index(0)
            return tuple(sorted(name for name, perm in self.actions.items()
                                if blank in [i for i, target in enumerate(perm) if i != target]))
        return tuple(sorted(self.actions))

    def transition(self, state, action: str) -> dict[str, Any]:
        state = tuple(state)
        if action not in self.actions or action not in self.legal_actions(state):
            raise ValueError("illegal primitive action")
        after = self._apply(state, action)
        self.epoch += 1
        return {"world_id": self.world_id, "world_epoch": self.epoch,
                "before_state": state, "action": action, "observed_state": tuple(after)}

    def verify_receipt(self, receipt: dict[str, Any]) -> bool:
        if receipt.get("world_id") != self.world_id or receipt.get("world_epoch") != self.epoch:
            return False
        try:
            expected = self._apply(tuple(receipt["before_state"]), receipt["action"])
        except (KeyError, ValueError):
            return False
        return tuple(receipt.get("observed_state", ())) == expected

    def _apply(self, state, action):
        if action not in self.actions or action not in self.legal_actions(state):
            raise ValueError("illegal primitive action")
        if self.family == "sliding_3x3":
            return puzzle_worlds.sliding_apply(state, self.actions[action])
        return puzzle_worlds._apply_position_map(state, self.actions[action])
