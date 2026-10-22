"""Development learning curves for the native P20 fresh/mapped target learner.

This is a development adapter, not the frozen P20 held-out runner. It uses
actual independent finite worlds and includes every stream in its output.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import (
    HeatSourceWorld, InconsistentHeatSourceWorld, InconsistentLeverSourceWorld,
    LatchWorld, LeverSourceWorld, ThermalWorld,
    verify_induced_map_candidate, verify_source_prior_target_effect,
)


@dataclass(frozen=True)
class DomainPair:
    name: str
    source_factory: object
    target_factory: object
    source_step: object
    target_step: object
    target_action: str
    target_object_type: str
    target_feature: str
    target_before: str
    mismatch_source_factory: object
    mismatch_source_step: object


DOMAIN_PAIRS = (
    DomainPair("heat_to_thermal",
               lambda ids: HeatSourceWorld(sample_ids=ids),
               lambda ids: ThermalWorld(object_ids=ids),
               lambda world, key: world.apply_heat(key, "apply_heat"),
               lambda world, key: world.apply(key, "warm"),
               "warm", "ThermalSample", "temperature", "cold",
               lambda ids: InconsistentHeatSourceWorld(sample_ids=ids),
               lambda world, key: world.apply_heat(key, "apply_heat")),
    DomainPair("lever_to_latch",
               lambda ids: LeverSourceWorld(lever_ids=ids),
               lambda ids: LatchWorld(latch_ids=ids),
               lambda world, key: world.raise_control(key, "raise_control"),
               lambda world, key: world.operate(key, "lift"),
               "lift", "Latch", "position", "lowered",
               lambda ids: InconsistentLeverSourceWorld(lever_ids=ids),
               lambda world, key: world.raise_control(key, "raise_control")),
)


def _prediction_success(learner, pair, *, stream_id, checkpoint):
    predicted = learner.predict(
        query_id=f"{stream_id}:{checkpoint}",
        action_kind=pair.target_action,
        object_type=pair.target_object_type,
        feature_key=pair.target_feature,
        before_value=pair.target_before,
        object_id=f"{stream_id}:unseen")
    if not predicted:
        return False
    test_world = pair.target_factory((f"{stream_id}:unseen",))
    actual = pair.target_step(test_world, f"{stream_id}:unseen")
    return (predicted.get("status") == "predicted"
            and predicted.get("expected_after_value") == actual.after_value)


def _fresh_stream(pair, stream_id):
    learner = NativeTargetLearner(owner_id=f"fresh:{stream_id}")
    target = pair.target_factory((f"{stream_id}:train-a", f"{stream_id}:train-b"))
    curve = [{"target_interactions": 0, "success": int(
        _prediction_success(learner, pair, stream_id=stream_id, checkpoint=0))}]
    first = pair.target_step(target, f"{stream_id}:train-a")
    learner.observe_world_receipt(first)
    learner.settle()
    curve.append({"target_interactions": 1, "success": int(
        _prediction_success(learner, pair, stream_id=stream_id, checkpoint=1))})
    second = pair.target_step(target, f"{stream_id}:train-b")
    learner.observe_world_receipt(second)
    learner.settle()
    curve.append({"target_interactions": 2, "success": int(
        _prediction_success(learner, pair, stream_id=stream_id, checkpoint=2))})
    return {"arm": "fresh", "stream_id": stream_id, "curve": curve,
            "target_actions": learner.accounting.target_actions,
            "source_information_units": learner.accounting.source_information_units,
            "native_rule_steps": learner.accounting.native_rule_steps,
            "graph": learner.graph_footprint()}


def _mapped_stream(pair, stream_id):
    source = pair.source_factory((f"{stream_id}:source-a", f"{stream_id}:source-b"))
    target = pair.target_factory((f"{stream_id}:target-a", f"{stream_id}:target-b",
                                 f"{stream_id}:target-confirm"))
    source_receipts = [pair.source_step(source, f"{stream_id}:source-a"),
                       pair.source_step(source, f"{stream_id}:source-b")]
    source_learner = NativeTargetLearner(owner_id=f"source-model:{stream_id}")
    for receipt in source_receipts:
        source_learner.observe_world_receipt(receipt)
    source_learner.settle()
    hypotheses = source_learner.hypotheses()
    if len(hypotheses) != 1:
        raise RuntimeError(f"mapped development arm failed source learner: {stream_id}")
    source_hypothesis = hypotheses[0]

    learner = NativeTargetLearner(owner_id=f"mapped:{stream_id}", transfer_enabled=True)
    learner.s.set_attr(learner.s.nodes("TargetLearningPolicy")[0], "enabled", 1.0)
    target_pairs = []
    curve = [{"target_interactions": 0, "success": int(
        _prediction_success(learner, pair, stream_id=stream_id, checkpoint=0))}]
    for index, (source_receipt, target_id) in enumerate(
            zip(source_receipts, (f"{stream_id}:target-a", f"{stream_id}:target-b")), 1):
        target_receipt = pair.target_step(target, target_id)
        target_pairs.append(target_receipt)
        learner.observe_map_pair(pair_id=f"{stream_id}:pair:{index}",
                                 source=source_receipt, target=target_receipt)
        learner.settle()
        curve.append({"target_interactions": index, "success": int(
            _prediction_success(learner, pair, stream_id=stream_id,
                               checkpoint=index))})
    candidates = [learner.s.node(node) for node in learner.s.nodes("RepresentationMap")
                  if learner.s.node(node)["attrs"].get("mapping_kind")
                  == "induced_categorical_effect"]
    if len(candidates) != 1:
        raise RuntimeError(f"mapped development arm failed native map proposal: {stream_id}")
    object_pairs = {source_receipts[i].object_id: target_pairs[i].object_id for i in range(2)}
    map_record = verify_induced_map_candidate(
        candidate=candidates[0], source_receipts=source_receipts,
        target_receipts=target_pairs, object_pairs=object_pairs)
    if map_record.get("status") != "verified":
        raise RuntimeError(f"mapped development arm map verification failed: {stream_id}")
    validation = pair.target_step(target, f"{stream_id}:target-confirm")
    effect = verify_source_prior_target_effect(
        prior_id=f"prior:{stream_id}", source_hypothesis=source_hypothesis,
        map_record=map_record, target_receipt=validation)
    if effect.get("status") != "verified":
        raise RuntimeError(f"mapped development arm target confirmation failed: {stream_id}")
    mapped = lambda name, value: map_record.get(name, {}).get(value)
    learner.import_source_prior(
        prior_id=f"prior:{stream_id}", source_id=f"source:{stream_id}",
        action_kind=mapped("action_map", source_hypothesis["action_kind"]),
        object_type=mapped("object_type_map", source_hypothesis["object_type"]),
        feature_key=mapped("feature_map", source_hypothesis["feature_key"]),
        before_value=mapped("value_map", source_hypothesis["before_value"]),
        after_value=mapped("value_map", source_hypothesis["after_value"]),
        map_evidence=map_record, target_receipt=effect)
    learner.observe_world_receipt(validation)
    learner.settle()
    curve.append({"target_interactions": 3, "success": int(
        _prediction_success(learner, pair, stream_id=stream_id, checkpoint=3))})
    return {"arm": "mapped_source", "stream_id": stream_id, "curve": curve,
            "target_actions": learner.accounting.target_actions,
            "source_information_units": learner.accounting.source_information_units,
            "native_rule_steps": (source_learner.accounting.native_rule_steps
                                   + learner.accounting.native_rule_steps),
            "graph": learner.graph_footprint(),
            "map_status": map_record["status"], "target_effect_status": effect["status"]}


def _mismatched_stream(pair, stream_id):
    source = pair.mismatch_source_factory((f"{stream_id}:source-a", f"{stream_id}:source-b"))
    target = pair.target_factory((f"{stream_id}:target-a", f"{stream_id}:target-b"))
    learner = NativeTargetLearner(owner_id=f"mismatch:{stream_id}", transfer_enabled=True)
    learner.s.set_attr(learner.s.nodes("TargetLearningPolicy")[0], "enabled", 1.0)
    curve = [{"target_interactions": 0, "success": int(
        _prediction_success(learner, pair, stream_id=stream_id, checkpoint=0))}]
    target_receipts = []
    for index, suffix in enumerate(("a", "b"), 1):
        source_receipt = pair.mismatch_source_step(source, f"{stream_id}:source-{suffix}")
        target_receipt = pair.target_step(target, f"{stream_id}:target-{suffix}")
        target_receipts.append(target_receipt)
        learner.observe_map_pair(pair_id=f"{stream_id}:mismatch-pair:{index}",
                                 source=source_receipt, target=target_receipt)
        # The same target action receipt becomes fresh evidence after the
        # source mismatch is visible; it is not charged as a second action.
        learner.observe_world_receipt(target_receipt, action_occurred=False)
        learner.settle()
        curve.append({"target_interactions": index, "success": int(
            _prediction_success(learner, pair, stream_id=stream_id,
                               checkpoint=index))})
    candidates = [node for node in learner.s.nodes("RepresentationMap")
                  if learner.s.node(node)["attrs"].get("mapping_kind")
                  == "induced_categorical_effect"]
    if candidates:
        raise RuntimeError(f"mismatched source produced a map candidate: {stream_id}")
    return {"arm": "mismatched_source", "stream_id": stream_id, "curve": curve,
            "target_actions": learner.accounting.target_actions,
            "source_information_units": learner.accounting.source_information_units,
            "native_rule_steps": learner.accounting.native_rule_steps,
            "graph": learner.graph_footprint(),
            "map_status": "abstained_conflicting_source"}


def run_development_panel(*, streams_per_pair=4, stream_prefix="dev"):
    """Run a disjointly named panel; split authorization belongs to caller."""
    records = []
    for pair in DOMAIN_PAIRS:
        for index in range(streams_per_pair):
            stream_id = f"{stream_prefix}:{pair.name}:{index:04d}"
            records.append(_fresh_stream(pair, stream_id))
            records.append(_mapped_stream(pair, stream_id))
            records.append(_mismatched_stream(pair, stream_id))
    checkpoints = sorted({point["target_interactions"] for row in records
                          for point in row["curve"]})
    curves = {}
    arms = ("fresh", "mapped_source", "mismatched_source")
    for arm in arms:
        curves[arm] = {}
        for point in checkpoints:
            values = []
            for row in records:
                if row["arm"] != arm:
                    continue
                observed = [item for item in row["curve"]
                            if item["target_interactions"] <= point]
                values.append(max(observed, key=lambda item: item["target_interactions"])["success"])
            curves[arm][point] = mean(values)
    auc = {arm: sum((curves[arm][left] + curves[arm][right]) / 2.0
                    * (right - left)
                    for left, right in zip(checkpoints, checkpoints[1:]))
           / (checkpoints[-1] - checkpoints[0]) for arm in curves}
    resources = {
        arm: {
            "mean_target_actions": mean(row["target_actions"] for row in records
                                         if row["arm"] == arm),
            "mean_source_information_units": mean(
                row["source_information_units"] for row in records if row["arm"] == arm),
            "mean_native_rule_steps": mean(row["native_rule_steps"] for row in records
                                            if row["arm"] == arm),
            "mean_graph_nodes": mean(row["graph"]["nodes"] for row in records
                                      if row["arm"] == arm),
            "mean_graph_bytes": mean(row["graph"]["bytes"] for row in records
                                      if row["arm"] == arm),
        } for arm in curves
    }
    return {"status": ("development_only" if stream_prefix == "dev"
                        else "heldout_unanalyzed"),
            "stream_prefix": stream_prefix, "streams_per_pair": streams_per_pair,
            "domain_pairs": [pair.name for pair in DOMAIN_PAIRS],
            "checkpoints": checkpoints, "curves": curves, "normalized_auc": auc,
            "paired_auc_difference_mapped_minus_fresh": auc["mapped_source"] - auc["fresh"],
            "resources": resources, "records": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams-per-pair", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_development_panel(streams_per_pair=args.streams_per_pair)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"},
                     indent=2, sort_keys=True))
