"""Independent finite target worlds for P20 native exploration.

Each world owns its transition function and returns an immutable observation
record only after a legal action. The learner adapter translates that record
into graph evidence; it does not calculate the effect.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


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


class HeatSourceWorld:
    """Source-domain analogue of heating with a distinct vocabulary."""

    def __init__(self, *, sample_ids):
        self.states = {str(key): "chilled" for key in sample_ids}
        self.epoch = 0
        self.receipts: list[WorldReceipt] = []

    def apply_heat(self, sample_id: str, operation: str) -> WorldReceipt:
        if sample_id not in self.states:
            raise KeyError(f"unknown metal sample: {sample_id}")
        if operation != "apply_heat":
            raise ValueError(f"illegal heating operation: {operation}")
        before = self.states[sample_id]
        after = "tempered" if before == "chilled" else before
        self.states[sample_id] = after
        self.epoch += 1
        receipt = WorldReceipt(
            f"heat-source:{self.epoch}:{sample_id}", sample_id, "MetalSample",
            operation, "heat_level", before, after, "observed", True, self.epoch)
        self.receipts.append(receipt)
        return receipt


class LeverSourceWorld:
    """Source-domain analogue of a rising latch with distinct vocabulary."""

    def __init__(self, *, lever_ids):
        self.orientations = {str(key): "down" for key in lever_ids}
        self.revision = 0
        self.receipts: list[WorldReceipt] = []

    def raise_control(self, lever_id: str, operation: str) -> WorldReceipt:
        if lever_id not in self.orientations:
            raise KeyError(f"unknown control lever: {lever_id}")
        if operation != "raise_control":
            raise ValueError(f"illegal control operation: {operation}")
        before = self.orientations[lever_id]
        after = "up" if before == "down" else before
        self.orientations[lever_id] = after
        self.revision += 1
        receipt = WorldReceipt(
            f"lever-source:{self.revision}:{lever_id}", lever_id, "ControlLever",
            operation, "orientation", before, after, "observed", True, self.revision)
        self.receipts.append(receipt)
        return receipt


class RequestRepairWorld:
    """Fresh social task world with an ordered request→repair precondition."""

    family = "request_repair"
    object_type = "RepairCase"
    feature_key = "interaction_state"

    def __init__(self, *, world_id="repair-world", case_id="case-1", initial="idle"):
        self.world_id = world_id
        self.case_id = case_id
        self.state = initial
        self.epoch = 0
        self.receipts: list[WorldReceipt] = []

    def apply(self, action: str) -> WorldReceipt:
        before = self.state
        if action == "request" and before == "idle":
            self.state = "requested"
        elif action == "repair" and before == "requested":
            self.state = "repaired"
        else:
            raise ValueError(f"precondition_failed:{action}:{before}")
        self.epoch += 1
        receipt = WorldReceipt(
            f"{self.world_id}:{self.epoch}:{self.case_id}", self.case_id,
            self.object_type, action, self.feature_key, before, self.state,
            "observed", True, self.epoch)
        self.receipts.append(receipt)
        return receipt

    @property
    def solved(self):
        return self.state == "repaired"


def verify_categorical_effect_map(*, source_receipts, target_receipts, map_id,
                                  action_map, object_type_map, feature_map,
                                  value_map, object_map, target_frame_epoch):
    """Independently verify an exact categorical map on paired world receipts.

    At least two distinct source/target object pairs are required. The mapping
    is evaluated only from observed transitions and cannot see learner priors.
    """
    source_receipts, target_receipts = list(source_receipts), list(target_receipts)
    payload = {
        "map_id": map_id,
        "source_events": [row.event_id for row in source_receipts],
        "target_events": [row.event_id for row in target_receipts],
        "action_map": dict(action_map), "object_type_map": dict(object_type_map),
        "feature_map": dict(feature_map), "value_map": dict(value_map),
        "object_map": dict(object_map), "target_frame_epoch": int(target_frame_epoch),
    }
    pairs = {row.object_id: row for row in target_receipts}
    mismatches = []
    for source in source_receipts:
        target_id = object_map.get(source.object_id)
        target = pairs.get(target_id)
        if target is None:
            mismatches.append(f"missing_target_pair:{source.object_id}")
            continue
        if source.status != "observed" or target.status != "observed":
            mismatches.append(f"unobserved_pair:{source.object_id}")
        if not source.action_authorized or not target.action_authorized:
            mismatches.append(f"unauthorized_pair:{source.object_id}")
        projected = (
            action_map.get(source.action_kind),
            object_type_map.get(source.object_type),
            feature_map.get(source.feature_key),
            value_map.get(source.before_value),
            value_map.get(source.after_value),
        )
        observed = (target.action_kind, target.object_type, target.feature_key,
                    target.before_value, target.after_value)
        if projected != observed:
            mismatches.append(f"effect_mismatch:{source.object_id}")
    enough = (len(source_receipts) >= 2 and len(target_receipts) >= 2
              and len({row.object_id for row in source_receipts}) >= 2
              and len({object_map.get(row.object_id) for row in source_receipts}) >= 2)
    payload["witness_count"] = len(source_receipts)
    payload["status"] = "verified" if enough and not mismatches else "rejected"
    payload["mapping_kind"] = "exact_categorical_effect"
    payload["mismatches"] = mismatches if enough else ["insufficient_distinguishing_pairs"]
    payload["receipt_id"] = "map-receipt:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def induce_categorical_effect_map(*, source_receipts, target_receipts,
                                  object_pairs, map_id, target_frame_epoch):
    """Propose a categorical source→target map from paired interaction traces.

    Object correspondence is the experiment's paired-task identity; action,
    type, feature and value correspondences are inferred from observed legal
    transitions. Conflicting or many-to-one mappings are rejected before an
    independent verifier evaluates the proposal.
    """
    source_receipts, target_receipts = list(source_receipts), list(target_receipts)
    target_by_object = {}
    for receipt in target_receipts:
        target_by_object.setdefault(receipt.object_id, []).append(receipt)
    maps = {key: {} for key in ("action_map", "object_type_map", "feature_map", "value_map")}
    reverse = {key: {} for key in maps}
    errors = []

    def record(kind, source, target):
        prior, reverse_prior = maps[kind].get(source), reverse[kind].get(target)
        if prior is not None and prior != target:
            errors.append(f"conflicting_{kind}:{source}")
        if reverse_prior is not None and reverse_prior != source:
            errors.append(f"noninjective_{kind}:{target}")
        maps[kind][source], reverse[kind][target] = target, source

    for source_id, target_id in object_pairs.items():
        source_group = [row for row in source_receipts if row.object_id == source_id]
        target_group = target_by_object.get(target_id, [])
        if len(source_group) != len(target_group) or not source_group:
            errors.append(f"unpaired_interactions:{source_id}")
            continue
        for source, target in zip(source_group, target_group):
            if (source.status != "observed" or target.status != "observed"
                    or not source.action_authorized or not target.action_authorized):
                errors.append(f"unreceipted_pair:{source.event_id}")
                continue
            record("action_map", source.action_kind, target.action_kind)
            record("object_type_map", source.object_type, target.object_type)
            record("feature_map", source.feature_key, target.feature_key)
            record("value_map", source.before_value, target.before_value)
            record("value_map", source.after_value, target.after_value)

    return {
        "map_id": map_id, "status": "candidate" if not errors else "rejected",
        "mapping_kind": "induced_categorical_effect", "object_map": dict(object_pairs),
        **maps, "target_frame_epoch": int(target_frame_epoch),
        "paired_transition_count": sum(1 for row in source_receipts
                                        if row.object_id in object_pairs),
        "errors": errors,
    }


def verify_induced_map_candidate(*, candidate, source_receipts, target_receipts,
                                 object_pairs):
    """Independently check a native RepresentationMap candidate."""
    attrs = candidate.get("attrs", candidate)
    if attrs.get("status") != "candidate" or attrs.get("mapping_kind") != "induced_categorical_effect":
        return {"status": "rejected", "mismatches": ["not_native_map_candidate"]}
    values = {attrs.get("source_before"): attrs.get("target_before"),
              attrs.get("source_after"): attrs.get("target_after")}
    if None in values:
        return {"status": "rejected", "mismatches": ["incomplete_native_candidate"]}
    return verify_categorical_effect_map(
        source_receipts=source_receipts, target_receipts=target_receipts,
        map_id=attrs.get("map_id"),
        action_map={attrs.get("source_action"): attrs.get("target_action")},
        object_type_map={attrs.get("source_object_type"): attrs.get("target_object_type")},
        feature_map={attrs.get("source_feature"): attrs.get("target_feature")},
        value_map=values, object_map=object_pairs,
        target_frame_epoch=attrs.get("target_frame_epoch"))


def verify_source_prior_target_effect(*, prior_id, source_hypothesis, map_record,
                                      target_receipt):
    """Issue a candidate-specific receipt only for a mapped live target effect."""
    mapped = None
    if map_record.get("status") == "verified":
        mapped = (
            map_record.get("action_map", {}).get(source_hypothesis.get("action_kind")),
            map_record.get("object_type_map", {}).get(source_hypothesis.get("object_type")),
            map_record.get("feature_map", {}).get(source_hypothesis.get("feature_key")),
            map_record.get("value_map", {}).get(source_hypothesis.get("before_value")),
            map_record.get("value_map", {}).get(source_hypothesis.get("after_value")),
        )
    observed = (target_receipt.action_kind, target_receipt.object_type,
                target_receipt.feature_key, target_receipt.before_value,
                target_receipt.after_value)
    exact = (mapped == observed and target_receipt.status == "observed"
             and target_receipt.action_authorized)
    record = {
        "receipt_id": f"target-prior:{prior_id}:{target_receipt.event_id}",
        "source_prior_id": prior_id, "target_event_id": target_receipt.event_id,
        "map_receipt_id": map_record.get("receipt_id"),
        "status": "verified" if exact else "rejected",
        "exact_effect_match": bool(exact),
    }
    return record


def development_worlds():
    """Return fresh, independently implemented development worlds."""
    return (
        ThermalWorld(object_ids=("thermal-a", "thermal-b", "thermal-c")),
        LatchWorld(latch_ids=("latch-a", "latch-b", "latch-c")),
    )
