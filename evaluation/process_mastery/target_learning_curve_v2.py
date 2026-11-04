"""P24 matched four-arm common-target development curves.

This is a development builder only. It records every stream and never reads
held-out allocations. All arms share one generated target receipt stream per
paired task; only source availability and map work differ.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.target_learning_curve import DOMAIN_PAIRS
from evaluation.process_mastery.target_learning_worlds import (
    verify_categorical_effect_map, verify_induced_map_candidate,
    verify_source_prior_target_effect,
)
from evaluation.process_mastery.target_learner import NativeTargetLearner

ARMS = ("fresh", "compatible_source", "wrong_source", "same_target_map_work")
CHECKPOINTS = (0, 1, 2)


def _map_view(pair_id, source_receipt, *, source_epoch=3):
    return {"pair_id": pair_id, "source_receipt": source_receipt,
            "source_epoch": source_epoch}


def _prediction(learner, pair, *, stream_id, arm, checkpoint, frame_epoch):
    row = learner.predict(query_id=f"{stream_id}:{arm}:{checkpoint}",
                          action_kind=pair.target_action,
                          object_type=pair.target_object_type,
                          feature_key=pair.target_feature,
                          before_value=pair.target_before,
                          object_id=f"{stream_id}:unseen",
                          frame_epoch=frame_epoch)
    world = pair.target_factory((f"{stream_id}:unseen:{checkpoint}",))
    actual = pair.target_step(world, f"{stream_id}:unseen:{checkpoint}")
    return {"target_interactions": checkpoint,
            "success": int(bool(row) and row.get("expected_after_value") == actual.after_value),
            "prediction_status": row.get("status") if row else "missing_or_ambiguous",
            "actual_after_value": actual.after_value,
            "predicted_after_value": row.get("expected_after_value") if row else None}


def _source_training(pair, stream_id, relation):
    ids = (f"{stream_id}:source-a", f"{stream_id}:source-b")
    if relation == "compatible":
        world = pair.source_factory(ids)
        step = pair.source_step
    else:
        world = pair.mismatch_source_factory(ids)
        step = pair.mismatch_source_step
    receipts = [step(world, key) for key in ids]
    learner = NativeTargetLearner(owner_id=f"p24-source:{stream_id}:{relation}")
    for receipt in receipts:
        learner.observe_world_receipt(receipt)
    learner.settle()
    hypotheses = learner.hypotheses()
    return receipts, hypotheses[0] if len(hypotheses) == 1 else None, learner


def _attempted_map_verification(pair, source_receipts, target_receipts, *, frame_epoch):
    """Retain verifier failure when native candidate induction abstains."""
    first_source, first_target = source_receipts[0], target_receipts[0]
    candidate = verify_categorical_effect_map(
        source_receipts=source_receipts, target_receipts=target_receipts,
        map_id="p24-attempted-map",
        action_map={first_source.action_kind: first_target.action_kind},
        object_type_map={first_source.object_type: first_target.object_type},
        feature_map={first_source.feature_key: first_target.feature_key},
        value_map={first_source.before_value: first_target.before_value,
                   first_source.after_value: first_target.after_value},
        object_map={source.object_id: target.object_id
                    for source, target in zip(source_receipts, target_receipts)},
        target_frame_epoch=frame_epoch)
    return candidate


def _run_stream(pair, stream_id, *, context_epoch):
    started = perf_counter()
    source_receipts, source_hypothesis, source_learner = ([], None, None)
    learners = {arm: CommonTargetLearner(
        owner_id=f"p24:{stream_id}", additive_transfer_enabled=arm != "fresh")
        for arm in ARMS}
    if "compatible_source" in learners:
        source_receipts, source_hypothesis, source_learner = _source_training(
            pair, stream_id, "compatible")
    wrong_receipts, wrong_hypothesis, wrong_learner = _source_training(
        pair, stream_id, "wrong")
    target = pair.target_factory((f"{stream_id}:target-a", f"{stream_id}:target-b"))
    target_receipts = []
    curves = {arm: [_prediction(learners[arm], pair, stream_id=stream_id,
                                arm=arm, checkpoint=0, frame_epoch=context_epoch)]
              for arm in ARMS}

    for index, suffix in enumerate(("a", "b")):
        receipt = pair.target_step(target, f"{stream_id}:target-{suffix}")
        target_receipts.append(receipt)
        for arm, learner in learners.items():
            map_view = None
            if arm == "compatible_source":
                map_view = _map_view(f"{stream_id}:compatible:{index}", source_receipts[index])
            elif arm == "wrong_source":
                map_view = _map_view(f"{stream_id}:wrong:{index}", wrong_receipts[index])
            elif arm == "same_target_map_work" and index == 1:
                # Two reciprocal views spend the same construction allowance
                # on the shared target events and import no external source.
                map_view = _map_view(f"{stream_id}:same-target:1", target_receipts[0])
            learner.observe_world_receipt(receipt, frame_epoch=context_epoch,
                                          map_view=map_view)
        if index == 1:
            learners["same_target_map_work"].observe_world_receipt(
                target_receipts[0], frame_epoch=context_epoch,
                map_view=_map_view(f"{stream_id}:same-target:2", target_receipts[1]))
        for learner in learners.values():
            learner.settle()
        if index == 0:
            for arm, learner in learners.items():
                curves[arm].append(_prediction(learner, pair, stream_id=stream_id,
                                               arm=arm, checkpoint=1,
                                               frame_epoch=context_epoch))

    transfer_records = {}
    compatible = learners["compatible_source"]
    for arm, srcs, source_hyp in (
            ("compatible_source", source_receipts, source_hypothesis),
            ("wrong_source", wrong_receipts, wrong_hypothesis)):
        learner = learners[arm]
        candidates = [learner.s.node(n) for n in learner.s.nodes("RepresentationMap")
                      if learner.s.node(n)["attrs"].get("mapping_kind")
                      == "induced_categorical_effect"]
        if len(candidates) == 1 and source_hyp is not None:
            mapping = verify_induced_map_candidate(
                candidate=candidates[0], source_receipts=srcs,
                target_receipts=target_receipts,
                object_pairs={srcs[i].object_id: target_receipts[i].object_id
                              for i in range(2)})
        else:
            mapping = _attempted_map_verification(
                pair, srcs, target_receipts, frame_epoch=context_epoch)
        if mapping.get("status") == "verified" and source_hyp is not None:
            effect = verify_source_prior_target_effect(
                prior_id=f"p24-prior:{stream_id}:{arm}", source_hypothesis=source_hyp,
                map_record=mapping, target_receipt=target_receipts[-1])
            learner.propose_source_model(
                prior_id=effect["source_prior_id"], source_id=f"p24-source:{stream_id}:{arm}",
                action_kind=mapping["action_map"].get(source_hyp["action_kind"]),
                object_type=mapping["object_type_map"].get(source_hyp["object_type"]),
                feature_key=mapping["feature_map"].get(source_hyp["feature_key"]),
                before_value=mapping["value_map"].get(source_hyp["before_value"]),
                after_value=mapping["value_map"].get(source_hyp["after_value"]),
                map_evidence=mapping, target_receipt=effect,
                frame_epoch=context_epoch)
            learner.settle()
        else:
            effect = {"status": "not_attempted_no_source_model"}
            # Preserve rejected map/effect evidence as a proposal. The native
            # importer rejects it and the common learner remains unchanged.
            if source_hyp is not None:
                effect = verify_source_prior_target_effect(
                    prior_id=f"p24-prior:{stream_id}:{arm}",
                    source_hypothesis=source_hyp, map_record=mapping,
                    target_receipt=target_receipts[-1])
                learner.propose_source_model(
                    prior_id=effect["source_prior_id"], source_id=f"p24-source:{stream_id}:{arm}",
                    action_kind=source_hyp["action_kind"],
                    object_type=source_hyp["object_type"],
                    feature_key=source_hyp["feature_key"],
                    before_value=source_hyp["before_value"],
                    after_value=source_hyp["after_value"],
                    map_evidence=mapping, target_receipt=effect,
                    frame_epoch=context_epoch)
                learner.settle()
        transfer_records[arm] = {"map_status": mapping.get("status"),
                                 "target_effect_status": effect.get("status")}

    for arm, learner in learners.items():
        curves[arm].append(_prediction(learner, pair, stream_id=stream_id,
                                       arm=arm, checkpoint=2,
                                       frame_epoch=context_epoch))
    receipts_by_arm = {
        arm: [learner.s.node(n)["attrs"].get("event_id")
              for n in learner.s.nodes("TransitionObservation")]
        for arm, learner in learners.items()}
    if any(values != receipts_by_arm[ARMS[0]] for values in receipts_by_arm.values()):
        raise RuntimeError("P24 arms did not assimilate identical target events")

    rows = {}
    for arm, learner in learners.items():
        map_requests = [n for n in learner.s.nodes("ThinkingBudgetRequest")
                        if learner.s.node(n)["attrs"].get("requester_kind")
                        == "target_map_observation"]
        source_count = (len(source_receipts) if arm == "compatible_source" else
                        len(wrong_receipts) if arm == "wrong_source" else 0)
        budgets = [learner.s.node(n)["attrs"] for n in learner.s.nodes("ThinkingBudget")]
        if len(budgets) != 1:
            raise RuntimeError("P24 arm must use exactly one shared native budget")
        budget_attrs = budgets[0]
        rows[arm] = {
            "arm": arm, "stream_id": stream_id, "family": pair.name,
            "context_epoch": context_epoch, "curve": curves[arm],
            "target_receipt_ids": list(receipts_by_arm[arm]),
            "target_actions": learner.accounting.target_actions,
            "source_action_count": source_count,
            "source_information_units": float(source_count),
            "map_pair_count": len(learner.s.nodes("TargetMapObservation")),
            "map_verification_queries": (5 if arm in {"compatible_source", "wrong_source"} else 0),
            "map_work_budget_debits": len([n for n in map_requests
                if learner.s.node(n)["attrs"].get("status") == "approved"]),
            "shared_budget_debits": len([n for n in learner.s.nodes("ThinkingBudgetRequest")
                if learner.s.node(n)["attrs"].get("status") == "approved"]),
            "native_rule_work": learner.accounting.native_rule_steps,
            "source_native_rule_work": (source_learner.accounting.native_rule_steps
                if arm == "compatible_source" and source_learner is not None else
                wrong_learner.accounting.native_rule_steps
                if arm == "wrong_source" and wrong_learner is not None else 0),
            "ordinary_evidence_signature": [
                {key: learner.s.node(n)["attrs"].get(key)
                 for key in ("owner_id", "event_id", "action_kind", "object_type",
                             "feature_key", "before_value", "after_value",
                             "source_epoch", "model_epoch", "frame_epoch")}
                for n in learner.s.nodes("TransitionObservation")],
            "graph": learner.graph_footprint(),
            "shared_budget": {key: budget_attrs.get(key) for key in
                              ("enabled", "remaining", "capacity", "capacity_ceiling",
                               "refill_per_epoch")},
            "transfer": transfer_records.get(arm, {"map_status": "not_attempted"}),
            "status": "complete",
        }
    rows["_meta"] = {"stream_id": stream_id, "family": pair.name,
                      "target_receipt_ids": [r.event_id for r in target_receipts],
                      "elapsed_seconds": perf_counter() - started,
                      "source_native_rule_work": sum(x.accounting.native_rule_steps
                          for x in (source_learner, wrong_learner) if x is not None)}
    return rows


def _auc(points):
    area = sum((points[i]["success"] + points[i + 1]["success"]) / 2
               for i in range(len(points) - 1))
    horizon = points[-1]["target_interactions"] - points[0]["target_interactions"]
    return area / horizon if horizon else 0.0


def run_development_panel(*, streams_per_pair=2, stream_prefix="p24-dev"):
    records = []
    for pair in DOMAIN_PAIRS:
        for index in range(streams_per_pair):
            stream_id = f"{stream_prefix}:{pair.name}:{index:04d}"
            context_epoch = 5 + (index % 2)
            rows = _run_stream(pair, stream_id, context_epoch=context_epoch)
            for arm in ARMS:
                rows[arm]["normalized_auc"] = _auc(rows[arm]["curve"])
                records.append(rows[arm])
    by_arm = {}
    for arm in ARMS:
        arm_rows = [row for row in records if row["arm"] == arm]
        by_arm[arm] = {"stream_count": len(arm_rows),
                       "mean_normalized_auc": (sum(r["normalized_auc"] for r in arm_rows)
                                               / len(arm_rows) if arm_rows else 0.0),
                       "all_streams_retained": True}
    return {"schema": "p24_additive_transfer_development_v2",
            "status": "development_only", "heldout_accessed": False,
            "arms": list(ARMS), "checkpoints": list(CHECKPOINTS),
            "task_design": {"families": [pair.name for pair in DOMAIN_PAIRS],
                            "context_epochs": [5, 6],
                            "streams_per_family": streams_per_pair,
                            "target_horizon": [0, 1, 2]},
            "records": records, "summary": by_arm}


def self_check():
    result = run_development_panel(streams_per_pair=2, stream_prefix="p24-selfcheck")
    assert len(result["records"]) == len(DOMAIN_PAIRS) * 2 * len(ARMS)
    for family in {pair.name for pair in DOMAIN_PAIRS}:
        rows = [row for row in result["records"] if row["family"] == family]
        for stream_id in {row["stream_id"] for row in rows}:
            stream_rows = [row for row in rows if row["stream_id"] == stream_id]
            assert len(stream_rows) == len(ARMS)
            assert len({tuple(row["target_receipt_ids"]) for row in stream_rows}) == 1
            assert all([point["target_interactions"] for point in row["curve"]]
                       == list(CHECKPOINTS) for row in stream_rows)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--streams-per-pair", type=int, default=2)
    parser.add_argument("--output", required=True)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    result = self_check() if args.self_check else run_development_panel(
        streams_per_pair=args.streams_per_pair)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
