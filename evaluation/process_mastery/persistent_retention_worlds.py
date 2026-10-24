"""Independent P25 task worlds and evaluator/learner boundary helpers."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import random

from evaluation.process_mastery.target_learning_worlds import (
    LatchWorld,
    ThermalWorld,
    WorldReceipt,
)


WORLD_VERSION = "p25_persistent_retention_worlds_v1"
CAPACITY_RATIOS = (0.5, 1.0, 2.0)
FAMILIES = ("thermal", "latch")


def _stable_seed(stream_id: str, namespace: str) -> int:
    digest = hashlib.sha256(f"{namespace}:{stream_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _canonical_bytes(record: dict) -> int:
    return len(json.dumps(record, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8"))


def serialized_learning_content_bytes(records: list[dict], *, overhead_bytes: int = 32) -> int:
    """Frozen sizing basis: serialized receipts plus key and entry overhead."""
    total = 0
    for index, record in enumerate(records):
        key = f"learning:{index}"
        total += _canonical_bytes(record) + overhead_bytes + len(key.encode("utf-8"))
    return total


def capacity_for_ratio(records: list[dict], ratio: float) -> int:
    if ratio not in CAPACITY_RATIOS:
        raise ValueError(f"unregistered P25 capacity ratio: {ratio}")
    basis = serialized_learning_content_bytes(records)
    return max(1, math.ceil(basis * ratio))


@dataclass
class PersistentRetentionWorld:
    """One deterministic stream; evaluator archives never enter agent input."""

    stream_id: str
    family: str
    seed: int
    external_history: list[WorldReceipt] = field(default_factory=list)
    delivered_event_ids: list[str] = field(default_factory=list)
    interference_records: list[dict] = field(default_factory=list)
    _external_interference_labels: list[dict] = field(default_factory=list, repr=False)
    pre_delay_records: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if self.family not in FAMILIES:
            raise ValueError(f"unsupported P25 mechanism family: {self.family}")
        if not self.stream_id:
            raise ValueError("stream_id must be nonempty")
        if int(self.seed) < 0:
            raise ValueError("seed must be nonnegative")
        object_ids = [f"{self.stream_id}:learn:{i}" for i in range(2)]
        self.world = (ThermalWorld(object_ids=object_ids) if self.family == "thermal"
                      else LatchWorld(latch_ids=object_ids))

    def acquire(self) -> list[WorldReceipt]:
        receipts = []
        for object_id in (f"{self.stream_id}:learn:0", f"{self.stream_id}:learn:1"):
            receipt = (self.world.apply(object_id, "warm") if self.family == "thermal"
                       else self.world.operate(object_id, "lift"))
            receipts.append(receipt)
            self.external_history.append(receipt)
        return receipts

    def deliver(self, learner, receipt: WorldReceipt) -> None:
        if receipt not in self.external_history:
            raise ValueError("only a receipt in this evaluator world may be delivered")
        if receipt.event_id in self.delivered_event_ids:
            raise ValueError("P25 receipt delivery must be once-owned")
        learner.observe_world_receipt(receipt)
        self.delivered_event_ids.append(receipt.event_id)

    def add_interference(self, count: int = 4) -> list[dict]:
        """Generate unrelated/confusable tasks from an independent stream seed."""
        if count < 2:
            raise ValueError("P25 interference needs two confusable training tasks")
        rng = random.Random(_stable_seed(self.stream_id, f"p25-interference:{self.seed}"))
        actions = ("tap", "rotate", "toggle", "press")
        outcomes = ("unchanged", "released", "latched", "clicked")
        rows = []
        for index in range(count):
            confusable = index < 2
            action = "press" if confusable else actions[(index - 2) % len(actions)]
            outcome = "clicked" if confusable else outcomes[rng.randrange(len(outcomes))]
            row = {
                "event_id": f"{self.stream_id}:interference:{index}",
                "object_type": "ButtonWidget" if confusable else "UnrelatedWidget",
                "object_id": f"{self.stream_id}:widget:{index}",
                "action_kind": action,
                "feature_key": "button_state" if confusable else f"unrelated_feature_{index}",
                "before_value": "idle",
                "legal_actions": [action], "answer_fields_absent": True,
            }
            rows.append(row)
            self._external_interference_labels.append({
                "event_id": row["event_id"], "expected_outcome": outcome,
            })
        self.interference_records.extend(rows)
        return rows

    def deliver_interference(self, learner, row: dict) -> WorldReceipt:
        """Execute one public task in the independent world and deliver only its receipt."""
        if row not in self.interference_records:
            raise ValueError("interference task is not from this world allocation")
        if row["event_id"] in self.delivered_event_ids:
            raise ValueError("P25 interference receipt delivery must be once-owned")
        label = next((item for item in self._external_interference_labels
                      if item["event_id"] == row["event_id"]), None)
        if label is None:
            raise RuntimeError("interference outcome missing from external evaluator")
        receipt = WorldReceipt(
            row["event_id"], row["object_id"], row["object_type"],
            row["action_kind"], row["feature_key"], row["before_value"],
            label["expected_outcome"], "observed", True,
            len(self.external_history) + 1)
        self.external_history.append(receipt)
        learner.observe_world_receipt(receipt)
        self.delivered_event_ids.append(receipt.event_id)
        return receipt

    def record_pre_delay(self, learner, *, query_id: str, object_id: str) -> dict:
        if object_id not in getattr(self.world, "states", getattr(self.world, "positions", {})):
            if self.family == "thermal":
                self.world.states[object_id] = "cold"
            else:
                self.world.positions[object_id] = "lowered"
        if self.family == "thermal":
            query = {"action_kind": "warm", "object_type": "ThermalSample",
                     "feature_key": "temperature", "before_value": "cold"}
        else:
            query = {"action_kind": "lift", "object_type": "Latch",
                     "feature_key": "position", "before_value": "lowered"}
        result = learner.predict(query_id=query_id, object_id=object_id, **query)
        row = {"query_id": query_id, "prediction_status":
               "predicted" if result else "not_predicted",
               "predicted_after": result.get("expected_after_value") if result else None,
               "stream_id": self.stream_id, "family": self.family}
        self.pre_delay_records.append(row)
        return row

    def delayed_score(self, learner, *, query_id: str, object_id: str) -> dict:
        result = self.record_pre_delay(learner, query_id=query_id, object_id=object_id)
        receipt = (self.world.apply(object_id, "warm") if self.family == "thermal"
                   else self.world.operate(object_id, "lift"))
        self.external_history.append(receipt)
        expected = receipt.after_value
        correct = (result["prediction_status"] == "predicted"
                   and result["predicted_after"] == expected)
        return {**result, "actual_after": expected, "correct": bool(correct),
                "delayed_event_id": receipt.event_id}

    def evaluator_archive(self) -> list[dict]:
        return ([asdict(receipt) for receipt in self.external_history]
                + list(self._external_interference_labels))

    def learner_input_audit(self) -> dict:
        return {"stream_id": self.stream_id, "family": self.family,
                "delivered_event_ids": list(self.delivered_event_ids),
                "interference_records": list(self.interference_records),
                "evaluator_archive_accessible": False}
