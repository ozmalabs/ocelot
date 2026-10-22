"""Independent finite target worlds for P20 native exploration.

Each world owns its transition function and returns an immutable observation
record only after a legal action. The learner adapter translates that record
into graph evidence; it does not calculate the effect.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldReceipt:
    event_id: str
    object_id: str
    object_type: str
    action_kind: str
    feature_key: str
    before_value: str
    after_value: str
    status: str
    action_authorized: bool
    world_epoch: int


class ThermalWorld:
    """Heating changes a cold sample to warm; other states remain unchanged."""

    family = "thermal"
    object_type = "ThermalSample"
    feature_key = "temperature"
    action_kind = "warm"

    def __init__(self, *, object_ids):
        self.states = {str(key): "cold" for key in object_ids}
        self.epoch = 0
        self.receipts: list[WorldReceipt] = []

    def apply(self, object_id: str, action: str) -> WorldReceipt:
        if object_id not in self.states:
            raise KeyError(f"unknown thermal sample: {object_id}")
        if action != "warm":
            raise ValueError(f"illegal thermal action: {action}")
        before = self.states[object_id]
        after = "warm" if before == "cold" else before
        self.states[object_id] = after
        self.epoch += 1
        receipt = WorldReceipt(
            f"thermal:{self.epoch}:{object_id}", object_id, self.object_type,
            action, self.feature_key, before, after, "observed", True, self.epoch)
        self.receipts.append(receipt)
        return receipt


class LatchWorld:
    """A separate mechanism: lifting a lowered latch raises it permanently."""

    family = "latch"
    object_type = "Latch"
    feature_key = "position"
    action_kind = "lift"

    def __init__(self, *, latch_ids):
        self.positions = {str(key): "lowered" for key in latch_ids}
        self.version = 0
        self.receipts: list[WorldReceipt] = []

    def operate(self, latch_id: str, control: str) -> WorldReceipt:
        if latch_id not in self.positions:
            raise KeyError(f"unknown latch: {latch_id}")
        if control != "lift":
            raise ValueError(f"unsupported latch control: {control}")
        previous = self.positions[latch_id]
        resulting = "raised" if previous == "lowered" else previous
        self.positions[latch_id] = resulting
        self.version += 1
        receipt = WorldReceipt(
            f"latch:{self.version}:{latch_id}", latch_id, self.object_type,
            control, self.feature_key, previous, resulting, "observed", True,
            self.version)
        self.receipts.append(receipt)
        return receipt


def development_worlds():
    """Return fresh, independently implemented development worlds."""
    return (
        ThermalWorld(object_ids=("thermal-a", "thermal-b", "thermal-c")),
        LatchWorld(latch_ids=("latch-a", "latch-b", "latch-c")),
    )
