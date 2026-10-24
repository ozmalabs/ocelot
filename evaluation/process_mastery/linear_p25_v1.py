"""Frozen P25 persistent-retention panel, held-out runner version 1."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import substrate_rs
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.learning_memory_budget import (
    add_measured_content_item,
    apply_native_evictions,
    charge_persistent_summaries,
)
from evaluation.process_mastery.linear_p13_v1 import (
    _add_domain, _set_policy, _settle as _p13_settle, _sleep_input, _task,
)
from evaluation.process_mastery.persistent_retention_worlds import (
    CAPACITY_RATIOS,
    FAMILIES,
    PersistentRetentionWorld,
)
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import WorldReceipt
from substrate.seed_loader import manifest_for

PHASE = "linear-p25-v1"
PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P25_PREREG.md"
RAW_HELDOUT = "evaluation/process_mastery/results/p25_linear_v1_heldout_20261024.json"
HELDOUT_MARKER = "evaluation/process_mastery/results/.p25_v1_heldout_run_started"
ARMS = ("sleep_consolidation", "replay_only", "awake_matched", "no_offline")
HELDOUT_STREAMS_PER_CELL = 200
DEVELOPMENT_STREAMS_PER_CELL = 2
CONTROL_KINDS = ("eviction", "restart", "absent_source")
HELDOUT_CONTROLS_PER_KIND = 100
DEVELOPMENT_CONTROLS_PER_KIND = 2
INTERFERENCE_COUNT = 6
DELAY_GROUPS = ((0, 2), (2, 4), (4, 6))
PRIMARY_GAIN = 0.10
MAX_NEW_TASK_LOSS = 0.02
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 25_010_241
SEED_BASES = {"development": 110_000_000, "heldout": 120_000_000}
CONTROL_BASES = {"development": 130_000_000, "heldout": 131_000_000}
RESOURCE_LIMITS = {
    "target_actions_per_arm": 2,
    "interference_actions_per_arm": INTERFERENCE_COUNT,
    "external_model_queries": 0,
    "native_rule_steps_per_learner": 250_000,
    "graph_bytes_per_learner": 400_000,
    "shared_budget_capacity": 256.0,
    "capacity_ratios": list(CAPACITY_RATIOS),
    "delayed_test_queries": len(DELAY_GROUPS),
    "new_task_test_queries": 1,
}

PROFILE_SEEDS = (
    "thinking_budget", "extended_thinking", "process_induction",
    "target_learning", "sleep_regime", "learning_memory_budget",
    "persistent_consolidation", "process_schema", "invention_operators",
    "invention_round", "invariant_miner", "process_solving",
    "library_learning", "strategy_library",
)
PROVENANCE_FILES = (
    "evaluation/process_mastery/linear_p25_v1.py",
    "evaluation/process_mastery/analyze_linear_p25_v1.py",
    "evaluation/process_mastery/linear_p13_v1.py",
    "evaluation/process_mastery/developmental_memory.py",
    "evaluation/process_mastery/learning_memory_budget.py",
    "evaluation/process_mastery/persistent_retention_worlds.py",
    "evaluation/process_mastery/target_learner.py",
    "evaluation/process_mastery/target_learning_worlds.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "evaluation/process_mastery/harness.py",
    "scripts/gen_learning_memory_budget_seed.py",
    "seeds/learning_memory_budget.json",
    "scripts/gen_persistent_consolidation_seed.py",
    "seeds/persistent_consolidation.json",
    "scripts/gen_sleep_regime_seed.py", "seeds/sleep_regime.json",
    "scripts/gen_library_learning_seed.py", "seeds/library_learning.json",
    "substrate/boot_core.py", "substrate/boot_profiles.py",
    "substrate/seed_loader.py", "seeds/cognition_on_params.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
    "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/cognitive_cycle.rs", "runners/dsl/src/memory.rs",
    "docs/research/engine_substrate/COGNITION_PERSISTENT_RETENTION_CONTRACT.md",
    "docs/research/engine_substrate/COGNITION_SLEEP_STAGE_CONTRACT.md",
    "docs/research/engine_substrate/PMB_V1_SPEC.md",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, default=str).encode("utf-8"))


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def _node_records(learner, node_ids):
    return [{"type": learner.s.node(node)["type"],
             "attrs": learner.s.node(node)["attrs"]} for node in node_ids]


def _dynamic_nodes(learner, *, event_ids=(), query_ids=(), include_hypotheses=True):
    event_ids, query_ids = set(event_ids), set(query_ids)
    found = []
    evidence_types = ("TransitionObservation", "TransitionActionReceipt",
                      "TransitionOutcomeReceipt", "TransitionLearningRequest",
                      "TransitionModelReceipt", "CommonTargetEvidence")
    for node_type in evidence_types:
        for node in learner.s.nodes(node_type):
            attrs = learner.s.node(node)["attrs"]
            if attrs.get("event_id") in event_ids:
                found.append(node)
    if include_hypotheses:
        for node in learner.s.nodes("ProcessInductionHypothesis"):
            attrs = learner.s.node(node)["attrs"]
            if attrs.get("owner_id") != learner.owner_id or attrs.get("persistent_summary"):
                continue
            support_ids = {
                learner.s.node(support)["attrs"].get("event_id")
                for support in learner.s.neighbours(node, "supported_by_transition")
            }
            if not event_ids or support_ids.intersection(event_ids):
                found.append(node)
    for node_type in ("ProcessPredictionQuery", "ProcessPrediction"):
        for node in learner.s.nodes(node_type):
            if learner.s.node(node)["attrs"].get("query_id") in query_ids:
                found.append(node)
    return list(dict.fromkeys(found))


def _base_content_size(learner, receipts, pre_query_id):
    nodes = _dynamic_nodes(learner,
                           event_ids=[row.event_id for row in receipts],
                           query_ids=[pre_query_id])
    content = {"receipts": [asdict(row) for row in receipts],
               "native_learning_state": _node_records(learner, nodes)}
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return len(encoded) + 32 + len(b"p25:acquired") + 8 * len(nodes)


def allocation(split: str, *, streams_per_cell: int | None = None,
               controls_per_kind: int | None = None) -> dict:
    if split not in {"development", "heldout"}:
        raise ValueError("split must be development or heldout")
    if split == "heldout":
        if streams_per_cell not in {None, HELDOUT_STREAMS_PER_CELL}:
            raise ValueError("held-out stream allocation is frozen at 200 per cell")
        if controls_per_kind not in {None, HELDOUT_CONTROLS_PER_KIND}:
            raise ValueError("held-out controls are frozen at 100 per kind")
        streams_per_cell = HELDOUT_STREAMS_PER_CELL
        controls_per_kind = HELDOUT_CONTROLS_PER_KIND
    else:
        streams_per_cell = streams_per_cell or DEVELOPMENT_STREAMS_PER_CELL
        controls_per_kind = controls_per_kind or DEVELOPMENT_CONTROLS_PER_KIND
    stream_cells = []
    base = SEED_BASES[split]
    for family_index, family in enumerate(FAMILIES):
        for ratio_index, ratio in enumerate(CAPACITY_RATIOS):
            seeds = [base + family_index * 1_000_000 + ratio_index * 100_000 + i
                     for i in range(streams_per_cell)]
            stream_cells.append({
                "family": family, "capacity_ratio": ratio,
                "stream_ids": [f"p25:{split}:{seed}" for seed in seeds],
                "seeds": seeds, "arms": list(ARMS),
            })
    controls = {kind: [CONTROL_BASES[split] + kind_index * 10_000 + index
                       for index in range(controls_per_kind)]
                for kind_index, kind in enumerate(CONTROL_KINDS)}
    return {
        "phase": PHASE, "split": split, "families": list(FAMILIES),
        "capacity_ratios": list(CAPACITY_RATIOS), "arms": list(ARMS),
        "streams_per_family_capacity_cell": streams_per_cell,
        "stream_cells": stream_cells,
        "controls_per_kind": controls_per_kind, "control_seeds": controls,
        "primary": {"metric": "normalized_delayed_success_auc",
                    "comparison": "sleep_consolidation_minus_replay_only",
                    "minimum_gain": PRIMARY_GAIN,
                    "maximum_new_task_accuracy_loss": MAX_NEW_TASK_LOSS},
        "limits": dict(RESOURCE_LIMITS),
    }


def provenance() -> dict:
    hashes = {rel: _sha((ROOT / rel).read_bytes()) for rel in PROVENANCE_FILES}
    package_path = Path(substrate_rs.__file__).resolve().parent
    extension_path = Path(substrate_rs._native.__file__).resolve()
    receipt_path = package_path / "_native.build.json"
    return {
        "git_commit": _commit(), "source_file_sha256": hashes,
        "source_bundle_sha256": _digest([(rel, hashes[rel]) for rel in PROVENANCE_FILES]),
        "runner_sha256": hashes["evaluation/process_mastery/linear_p25_v1.py"],
        "analyzer_sha256": hashes["evaluation/process_mastery/analyze_linear_p25_v1.py"],
        "loaded_extension_path": str(extension_path),
        "loaded_extension_sha256": _sha(extension_path.read_bytes()),
        "build_receipt_path": str(receipt_path),
        "build_receipt_sha256": _sha(receipt_path.read_bytes()),
        "runtime_attestation": attest(package=substrate_rs,
                                       build_receipt=receipt_path,
                                       require_clean=True),
        "profile_seed_ids": list(PROFILE_SEEDS),
        "profile_seed_bundle_sha256": _digest([(rel, hashes[rel]) for rel in (
            "substrate/boot_core.py", "substrate/seed_loader.py",
            "scripts/gen_learning_memory_budget_seed.py", "seeds/learning_memory_budget.json",
            "scripts/gen_persistent_consolidation_seed.py", "seeds/persistent_consolidation.json",
            "scripts/gen_sleep_regime_seed.py", "seeds/sleep_regime.json")]),
        "python": sys.version.split()[0], "resource_limits": dict(RESOURCE_LIMITS),
    }


def _agent_for_arm(arm: str):
    if arm not in ARMS:
        raise ValueError(f"unknown P25 arm {arm}")
    agent = Agent(extra_seeds=PROFILE_SEEDS, track_i=False,
                  profile="p25-retention-v1",
                  budget={"enabled": 1.0, "capacity": 256.0,
                          "remaining": 256.0, "refill_per_epoch": 0.0,
                          "last_refill_epoch": -1.0},
                  policy_overrides={"ModelLearningPolicy": {"enabled": 1.0}})
    # Bind the P13 mechanical adapter interface to the same native substrate.
    agent.inner = agent.s._inner
    agent.agent = agent.ag
    agent.tick = lambda: agent.s.tick(100_000)
    settings = {
        "ModelLearningPolicy": True, "TargetLearningPolicy": False,
        "SleepRegimePolicy": arm == "sleep_consolidation",
        "ConsolidationSchedulerPolicy": arm in {"sleep_consolidation", "replay_only"},
        "LibraryLearningPolicy": arm == "sleep_consolidation",
        "StrategyLibraryPolicy": arm == "sleep_consolidation",
        "ProcessSchemaPolicy": True, "SolverPolicy": True,
        "InvariantMinerPolicy": True, "InventionPolicy": False,
        "LearningMemoryBudgetPolicy": True,
        "PersistentConsolidationPolicy": arm == "sleep_consolidation",
    }
    for policy_type, enabled in settings.items():
        nodes = agent.s.nodes(policy_type)
        if len(nodes) != 1:
            raise RuntimeError(f"P25 profile expected one {policy_type}, found {len(nodes)}")
        agent.inner.set_attr(nodes[0], "enabled", float(enabled))
    budget_nodes = agent.s.nodes("ThinkingBudget")
    if len(budget_nodes) != 1:
        raise RuntimeError("P25 profile requires one shared ThinkingBudget")
    budget = budget_nodes[0]
    agent.inner.set_attr(budget, "enabled", 1.0)
    for key, value in (("capacity", 256.0), ("remaining", 256.0),
                       ("refill_per_epoch", 0.0), ("last_refill_epoch", -1.0)):
        agent.inner.set_attr(budget, key, value)
    return agent, budget


def _interference_groups(world: PersistentRetentionWorld):
    rows = world.add_interference(INTERFERENCE_COUNT)
    return (rows[:2], rows[2:4], rows[4:6])


def _record_interference(learner, world, rows, *, item_id, admission_epoch):
    receipts = [world.deliver_interference(learner, row) for row in rows]
    native_steps = learner.settle()
    nodes = _dynamic_nodes(learner, event_ids=[row.event_id for row in receipts])
    item = add_measured_content_item(
        learner.agent, item_id=item_id, content_class="interference_experience",
        graph_nodes=nodes, admission_epoch=admission_epoch)
    learner.settle()
    evicted = apply_native_evictions(learner.agent)
    return {"event_ids": [row.event_id for row in receipts],
            "native_rule_steps": native_steps, "content_item": item,
            "evicted_item_ids": evicted}


def _awake_rehearsal(agent, stream_id: str, target_work: int) -> dict:
    seed = int(hashlib.sha256(stream_id.encode()).hexdigest()[:8], 16)
    domain = _add_domain(agent, seed, size=3, prefix="p25-awake")
    initial = [0, 1, 2]
    goal = agent.inner.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": [1, 2, 0], "state": initial})
    work = 0
    tasks = 0
    while work < max(1, int(target_work)):
        task = _task(agent, domain, f"p25-awake-{tasks}", initial, goal, seed + tasks)
        work += _p13_settle(agent, n=8)
        if agent.s.node(task)["attrs"].get("status") != "solved":
            raise RuntimeError("matched-work awake task did not solve natively")
        tasks += 1
        if tasks > 64:
            raise RuntimeError("matched-work awake rehearsal exceeded bounded task count")
    return {"native_rule_steps": work, "solved_tasks": tasks}


def _run_arm(*, stream_id: str, family: str, seed: int, ratio: float,
             arm: str, awake_target_work: int = 0) -> dict:
    started = time.perf_counter()
    agent, budget = _agent_for_arm(arm)
    learner = NativeTargetLearner(agent=agent, owner_id=f"p25:{stream_id}")
    world = PersistentRetentionWorld(stream_id=stream_id, family=family, seed=seed)
    training_receipts = world.acquire()
    for receipt in training_receipts:
        world.deliver(learner, receipt)
    learning_steps = learner.settle()
    pre_query_id = f"{stream_id}:pre-delay"
    pre_delay = world.delayed_score(learner, query_id=pre_query_id,
                                    object_id=f"{stream_id}:pre-target")
    pre_delay_steps = learner.accounting.native_rule_steps
    base_bytes = _base_content_size(learner, training_receipts, pre_query_id)
    capacity = max(1, math.ceil(base_bytes * ratio))
    memory_policy = learner.s.nodes("LearningMemoryBudgetPolicy")[0]
    learner.s.set_attr(memory_policy, "capacity_bytes", float(capacity))

    treatment = {"arm": arm, "sleep": None, "awake": None,
                 "consolidation": "not_run", "summary_charge": None}
    if arm in {"sleep_consolidation", "replay_only"}:
        from evaluation.process_mastery.linear_p21_v1 import _add_shared_episode
        _add_shared_episode(agent, stream_id)
        sleep_seed = int(hashlib.sha256(f"p25-sleep:{stream_id}".encode()).hexdigest()[:8], 16)
        sleep = _sleep_input(agent, sleep_seed)
        treatment["sleep"] = {
            "sleep_receipts": sleep["sleep_receipts"],
            "replay_traces": sleep["replay_traces"],
            "stages": sleep["stages"],
            "native_rule_steps": sleep["native_rule_steps"],
        }
    elif arm == "awake_matched":
        treatment["awake"] = _awake_rehearsal(agent, stream_id, awake_target_work)
    if arm == "sleep_consolidation":
        work = learner.s.add_node("PersistentConsolidationWork", {
            "work_id": f"{stream_id}:persistent-consolidation",
            "status": "requested", "interrupted": False,
            "foreground_demand": False,
        })
        learner.s.add_edge(learner.ag, "has_persistent_consolidation_work", work, {})
        consolidation_steps = learner.settle()
        measured = charge_persistent_summaries(agent)
        admission_steps = learner.settle()
        treatment["consolidation"] = learner.s.node(work)["attrs"].get("status")
        treatment["consolidation_native_rule_steps"] = consolidation_steps + admission_steps
        treatment["summary_charge"] = measured[0] if measured else None

    source_nodes = _dynamic_nodes(
        learner, event_ids=[row.event_id for row in training_receipts],
        query_ids=[pre_query_id])
    source_charge = add_measured_content_item(
        agent, item_id=f"{stream_id}:acquired", content_class="acquired_training",
        graph_nodes=source_nodes, admission_epoch=1.0)
    learner.settle()
    source_evictions = apply_native_evictions(agent)

    interference_groups = _interference_groups(world)
    curve = [{"delay_group": 0, "interference_actions": 0,
              "success": int(bool(pre_delay["correct"]))}]
    interference_records = []
    for group_index, group in enumerate(interference_groups, start=1):
        interference = _record_interference(
            learner, world, group, item_id=f"{stream_id}:interference:{group_index}",
            admission_epoch=float(group_index + 1))
        interference_records.append(interference)
        if group_index == 1:
            # First pair is the shared confusable new-task family.
            pass
        scored = world.delayed_score(
            learner, query_id=f"{stream_id}:delayed:{group_index}",
            object_id=f"{stream_id}:delayed:{group_index}")
        curve.append({"delay_group": group_index,
                      "interference_actions": group_index * 2,
                      "success": int(scored["correct"]),
                      "predicted_after": scored["predicted_after"],
                      "actual_after": scored["actual_after"]})

    new_task_prediction = learner.predict(
        query_id=f"{stream_id}:new-task", action_kind="press",
        object_type="ButtonWidget", feature_key="button_state",
        before_value="idle", object_id=f"{stream_id}:new-widget")
    new_task_correct = int(bool(new_task_prediction
                                and new_task_prediction.get("expected_after_value") == "clicked"))
    dynamic_nodes = [agent.s.node(node) for node in agent.s.nodes()]
    graph_bytes = len(json.dumps(dynamic_nodes, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False, default=str).encode("utf-8"))
    memory_attrs = learner.s.node(memory_policy)["attrs"]
    all_interference_ids = [event for group in interference_records
                            for event in group["event_ids"]]
    row = {
        "stream_id": stream_id, "seed": int(seed), "family": family,
        "capacity_ratio": ratio, "capacity_bytes": capacity,
        "capacity_basis_bytes": base_bytes, "arm": arm,
        "status": "complete", "target_receipt_ids": [r.event_id for r in training_receipts],
        "target_actions": len(training_receipts),
        "total_authorized_actions": learner.accounting.target_actions,
        "interference_receipt_ids": all_interference_ids,
        "interference_actions": sum(len(item["event_ids"]) for item in interference_records),
        "curve": curve, "normalized_auc": _auc(curve),
        "pre_delay": pre_delay, "pre_delay_learning_steps": pre_delay_steps,
        "learning_native_rule_steps": learning_steps,
        "interference_native_rule_steps": sum(r["native_rule_steps"]
                                              for r in interference_records),
        "treatment": treatment, "source_content_charge": source_charge,
        "source_evictions": source_evictions,
        "interference_content": interference_records,
        "persistent_summaries": [learner.s.node(n)["attrs"]
                                 for n in learner.s.nodes("PersistentLearnedSummary")],
        "resident_bytes": memory_attrs.get("resident_bytes"),
        "capacity_bytes_audit": memory_attrs.get("capacity_bytes"),
        "durable_read_bytes": memory_attrs.get("durable_read_bytes"),
        "budget_remaining": learner.s.node(budget)["attrs"].get("remaining"),
        "budget_debit": 256.0 - float(learner.s.node(budget)["attrs"].get("remaining", 0.0)),
        "new_task_accuracy": new_task_correct,
        "graph_nodes": len(dynamic_nodes), "graph_bytes": graph_bytes,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    if row["target_actions"] != 2 or row["interference_actions"] != INTERFERENCE_COUNT:
        row["status"] = "failed"
        row["failure"] = "interaction_count_mismatch"
    if graph_bytes > RESOURCE_LIMITS["graph_bytes_per_learner"]:
        row["status"] = "failed"
        row["failure"] = "graph_bytes_ceiling"
    if learner.accounting.native_rule_steps > RESOURCE_LIMITS["native_rule_steps_per_learner"]:
        row["status"] = "failed"
        row["failure"] = "native_rule_steps_ceiling"
    return row


def _auc(curve: list[dict]) -> float:
    if len(curve) < 2:
        raise ValueError("P25 AUC needs at least two delayed observations")
    xs = [float(row["delay_group"]) for row in curve]
    ys = [float(row["success"]) for row in curve]
    width = xs[-1] - xs[0]
    if width <= 0:
        raise ValueError("P25 curve has zero delay span")
    area = sum((xs[i] - xs[i - 1]) * (ys[i] + ys[i - 1]) / 2.0
               for i in range(1, len(xs)))
    return area / width


def _control(kind: str, seed: int) -> dict:
    control_id = f"p25-control:{kind}:{seed}"
    if kind == "absent_source":
        learner = NativeTargetLearner(owner_id=control_id)
        prediction = learner.predict(query_id=f"{control_id}:query", action_kind="warm",
                                     object_type="ThermalSample", feature_key="temperature",
                                     before_value="cold", object_id=f"{control_id}:unseen")
        return {"control_id": control_id, "kind": kind,
                "status": "PASS" if prediction is None else "FAIL",
                "prediction_absent": prediction is None,
                "source_receipt_count": 0}
    if kind == "eviction":
        agent, _budget = _agent_for_arm("no_offline")
        learner = NativeTargetLearner(agent=agent, owner_id=control_id)
        world = PersistentRetentionWorld(control_id, "thermal", seed)
        receipts = world.acquire()
        for receipt in receipts:
            world.deliver(learner, receipt)
        learner.settle()
        policy = learner.s.nodes("LearningMemoryBudgetPolicy")[0]
        learner.s.set_attr(policy, "capacity_bytes", 1.0)
        nodes = _dynamic_nodes(learner, event_ids=[r.event_id for r in receipts])
        item = add_measured_content_item(agent, item_id=f"{control_id}:source",
                                         content_class="target_training",
                                         graph_nodes=nodes, admission_epoch=1.0)
        learner.settle()
        apply_native_evictions(agent)
        prediction = learner.predict(query_id=f"{control_id}:query", action_kind="warm",
                                     object_type="ThermalSample", feature_key="temperature",
                                     before_value="cold", object_id=f"{control_id}:unseen")
        attrs = learner.s.node(item["item_node"])["attrs"]
        passed = (attrs.get("availability") in {"evicted", "rejected_capacity"}
                  and prediction is None and learner.s.nodes("TransitionObservation") == [])
        return {"control_id": control_id, "kind": kind,
                "status": "PASS" if passed else "FAIL",
                "availability": attrs.get("availability"),
                "prediction_absent": prediction is None}
    if kind == "restart":
        from substrate.boot_profiles import boot_cognition_on
        from substrate.world_adapter import WorldAdapter
        world_adapter = boot_cognition_on()
        try:
            from evaluation.process_mastery.common_target_learner import CommonTargetLearner
            learner = CommonTargetLearner(agent=world_adapter, owner_id="agent-root",
                                          enabled=True, policy_enabled=True)
            thermal = PersistentRetentionWorld(control_id, "thermal", seed)
            for receipt in thermal.acquire():
                thermal.deliver(learner, receipt)
            learner.settle()
            before = learner.predict(query_id=f"{control_id}:before", action_kind="warm",
                                     object_type="ThermalSample", feature_key="temperature",
                                     before_value="cold", object_id=f"{control_id}:test")
            with tempfile.TemporaryDirectory(prefix="p25-restart-") as directory:
                checkpoint = Path(directory) / "learner.json"
                world_adapter.save(checkpoint)
                world_adapter.close()
                resumed = WorldAdapter.load(checkpoint)
                try:
                    resumed_learner = CommonTargetLearner(
                        agent=resumed, owner_id="agent-root", enabled=True,
                        policy_enabled=True)
                    after = resumed_learner.predict(
                        query_id=f"{control_id}:after", action_kind="warm",
                        object_type="ThermalSample", feature_key="temperature",
                        before_value="cold", object_id=f"{control_id}:test")
                    passed = (before is not None and after is not None
                              and before.get("expected_after_value") ==
                              after.get("expected_after_value"))
                    return {"control_id": control_id, "kind": kind,
                            "status": "PASS" if passed else "FAIL",
                            "same_owner_id": resumed_learner.owner_id == "agent-root",
                            "prediction_before": before.get("expected_after_value") if before else None,
                            "prediction_after": after.get("expected_after_value") if after else None,
                            "checkpoint_sha256": _sha(checkpoint.read_bytes())}
                finally:
                    resumed.close()
        finally:
            if getattr(world_adapter, "_closed", False) is False:
                world_adapter.close()
    raise ValueError(f"unknown P25 control kind: {kind}")


def _run_controls(plan: dict) -> list[dict]:
    rows = []
    for kind in CONTROL_KINDS:
        rows.extend(_control(kind, seed) for seed in plan["control_seeds"][kind])
    return rows


def run_development(*, streams_per_cell: int = DEVELOPMENT_STREAMS_PER_CELL,
                    controls_per_kind: int = DEVELOPMENT_CONTROLS_PER_KIND) -> dict:
    plan = allocation("development", streams_per_cell=streams_per_cell,
                      controls_per_kind=controls_per_kind)
    rows = []
    for cell in plan["stream_cells"]:
        for stream_id, seed in zip(cell["stream_ids"], cell["seeds"]):
            paired = {}
            for arm in ARMS:
                paired[arm] = _run_arm(
                    stream_id=stream_id, family=cell["family"], seed=seed,
                    ratio=cell["capacity_ratio"], arm=arm,
                    awake_target_work=(paired.get("sleep_consolidation", {}).get(
                        "treatment", {}).get("sleep", {}).get("native_rule_steps", 1)
                                       if arm == "awake_matched" else 0))
                rows.append(paired[arm])
    controls = _run_controls(plan)
    return {
        "phase": PHASE, "split": "development", "status": "development_only",
        "heldout_accessed": False, "allocation_plan": plan,
        "allocation_sha256": _digest(plan), "provenance": provenance(),
        "streams": rows, "structural_controls": controls,
    }


def _verify_freeze(plan: dict) -> dict:
    prereg = ROOT / PREREGISTRATION
    freeze = json.loads(next(
        line[len("P25_FREEZE_JSON: "):]
        for line in prereg.read_text().splitlines()
        if line.startswith("P25_FREEZE_JSON: ")))
    prereg_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                            text=True).strip()
    parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=ROOT,
                                     text=True).strip()
    changed = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        cwd=ROOT, text=True).splitlines()
    if changed != [PREREGISTRATION]:
        raise RuntimeError("P25 preregistration is not an isolated latest commit")
    if freeze.get("freeze_parent_commit") != parent:
        raise RuntimeError("P25 preregistration parent does not match its frozen parent")
    if _digest(plan) != freeze.get("heldout_allocation_sha256"):
        raise RuntimeError("P25 concrete held-out allocation differs from freeze")
    current = provenance()
    for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                "loaded_extension_sha256", "build_receipt_sha256",
                "profile_seed_bundle_sha256"):
        if current.get(key) != freeze.get(key):
            raise RuntimeError(f"P25 frozen provenance mismatch: {key}")
    if current["runtime_attestation"].get("status") != "ATTESTED":
        raise RuntimeError("P25 runtime attestation is not ATTESTED")
    return {"freeze": freeze, "current_provenance": current,
            "preregistration_sha256": _sha(prereg.read_bytes()),
            "preregistration_commit": prereg_commit}


def run_heldout() -> dict:
    plan = allocation("heldout")
    freeze_record = _verify_freeze(plan)
    marker = ROOT / HELDOUT_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(json.dumps({"phase": PHASE, "started_unix": time.time(),
                                 "allocation_sha256": _digest(plan)}, sort_keys=True))
    rows = []
    for cell in plan["stream_cells"]:
        for stream_id, seed in zip(cell["stream_ids"], cell["seeds"]):
            paired = {}
            for arm in ARMS:
                target_work = (paired.get("sleep_consolidation", {}).get(
                    "treatment", {}).get("sleep", {}).get("native_rule_steps", 1)
                               if arm == "awake_matched" else 0)
                try:
                    row = _run_arm(stream_id=stream_id, family=cell["family"],
                                   seed=seed, ratio=cell["capacity_ratio"],
                                   arm=arm, awake_target_work=target_work)
                except Exception as exc:  # retain allocated failures rather than drop cells
                    row = {"stream_id": stream_id, "seed": seed,
                           "family": cell["family"], "capacity_ratio": cell["capacity_ratio"],
                           "arm": arm, "status": "failed", "failure": type(exc).__name__,
                           "failure_detail": str(exc)}
                paired[arm] = row
                rows.append(row)
    controls = _run_controls(plan)
    output = {
        "phase": PHASE, "split": "heldout", "status": "heldout_pending_analysis",
        "heldout_accessed": True, "allocation_plan": plan,
        "allocation_sha256": _digest(plan), "provenance": freeze_record["current_provenance"],
        "freeze": {"preregistration_sha256": freeze_record["preregistration_sha256"],
                   "preregistration_commit": freeze_record["preregistration_commit"],
                   "freeze_parent_commit": freeze_record["freeze"]["freeze_parent_commit"]},
        "streams": rows, "structural_controls": controls,
    }
    raw = ROOT / RAW_HELDOUT
    raw.write_text(json.dumps(output, sort_keys=True, indent=2, default=str) + "\n",
                    encoding="utf-8")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--streams-per-cell", type=int, default=DEVELOPMENT_STREAMS_PER_CELL)
    parser.add_argument("--controls-per-kind", type=int, default=DEVELOPMENT_CONTROLS_PER_KIND)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.split == "heldout":
        result = run_heldout()
    else:
        result = run_development(streams_per_cell=args.streams_per_cell,
                                 controls_per_kind=args.controls_per_kind)
    encoded = json.dumps(result, sort_keys=True, indent=2, default=str) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps({"phase": PHASE, "split": args.split,
                      "status": result["status"],
                      "streams": len(result["streams"]),
                      "controls": len(result["structural_controls"]),
                      "allocation_sha256": result["allocation_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
