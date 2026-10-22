"""Frozen P21 finite-memory and curriculum evaluation.

Python handles finite world events and byte storage. The native sleep and
curriculum rules authorize lifecycle steps; P20's native target learner scores
only retrieved, receipted experience.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.developmental_memory import ChargedMemory
from evaluation.process_mastery.linear_p13_v1 import (
    _add_domain, _set_policy, _settle as _p13_settle, _sleep_input, _task,
)
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import (
    LatchWorld, ThermalWorld, WorldReceipt,
)
from substrate.boot_profiles import boot_cognition_on
import substrate_rs

PHASE = "linear-p21-v1"
PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P21_PREREG.md"
CAPACITIES = (2048, 4096, 8192)
SLEEP_ARMS = ("full_sleep", "replay_only", "awake_rehearsal", "no_offline")
CURRICULUM_ARMS = ("residual", "random", "fixed")
HELDOUT_STREAMS_PER_STRATUM = 200
CONTROL_COUNT = 100
TARGET_RECEIPT_COUNT = 2
INTERFERENCE_EVENTS = 8
PROVENANCE_FILES = (
    "evaluation/process_mastery/linear_p21_v1.py",
    "evaluation/process_mastery/analyze_linear_p21_v1.py",
    "evaluation/process_mastery/developmental_memory.py",
    "evaluation/process_mastery/target_learner.py",
    "evaluation/process_mastery/target_learning_worlds.py",
    "evaluation/process_mastery/linear_p13_v1.py",
    "evaluation/process_mastery/analyze_linear_p13_v1.py",
    "evaluation/process_mastery/harness.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "evaluation/process_mastery/scorecard.py",
    "scripts/gen_sleep_regime_seed.py", "seeds/sleep_regime.json",
    "scripts/gen_library_learning_seed.py", "seeds/library_learning.json",
    "scripts/gen_process_curriculum_seed.py", "seeds/process_curriculum.json",
    "scripts/gen_curriculum_learning_bridge_seed.py",
    "seeds/curriculum_learning_bridge.json",
    "scripts/gen_target_learning_seed.py", "seeds/target_learning.json",
    "scripts/gen_observed_sequence_learning_seed.py",
    "seeds/observed_sequence_learning.json",
    "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
    "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/cognitive_cycle.rs",
    "docs/research/engine_substrate/COGNITION_DEVELOPMENTAL_MEMORY_CONTRACT.md",
    "docs/research/engine_substrate/COGNITION_SLEEP_STAGE_CONTRACT.md",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _bundle(hashes, files):
    return _digest([(rel, hashes[rel]) for rel in files])


def _commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def provenance():
    hashes = {rel: _sha((ROOT / rel).read_bytes()) for rel in PROVENANCE_FILES}
    package_dir = Path(substrate_rs.__file__).resolve().parent
    extension = Path(substrate_rs._native.__file__).resolve()
    receipt = package_dir / "_native.build.json"
    profile_files = ("substrate/boot_profiles.py", "seeds/cognition_on_params.json")
    world_files = ("evaluation/process_mastery/target_learning_worlds.py",
                   "evaluation/process_mastery/developmental_memory.py",
                   "evaluation/process_mastery/linear_p13_v1.py")
    dependency_files = ("runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
                        "runners/dsl/uv.lock",
                        "runners/dsl/python/substrate_rs/_native.build.json")
    return {
        "git_commit": _commit(),
        "runner_sha256": hashes["evaluation/process_mastery/linear_p21_v1.py"],
        "analyzer_sha256": hashes["evaluation/process_mastery/analyze_linear_p21_v1.py"],
        "source_file_sha256": hashes,
        "source_bundle_sha256": _digest([(rel, hashes[rel]) for rel in PROVENANCE_FILES]),
        "wrapper_sha256": hashes["runners/dsl/python/substrate_rs/__init__.py"],
        "loaded_extension_sha256": _sha(extension.read_bytes()),
        "build_receipt_sha256": _sha(receipt.read_bytes()),
        "profile_sha256": _bundle(hashes, profile_files),
        "world_adapter_sha256": _bundle(hashes, world_files),
        "dependency_closure_sha256": _bundle(hashes, dependency_files),
        "runtime_attestation": attest(package=substrate_rs, build_receipt=receipt,
                                       require_clean=True),
        "loaded_extension_path": str(extension),
        "build_receipt_path": str(receipt),
        "python": sys.version.split()[0],
    }


def allocation(split, *, streams_per_stratum=2, controls=1):
    if split not in {"development", "heldout"}:
        raise ValueError("split must be development or heldout")
    if split == "heldout":
        if streams_per_stratum not in {2, HELDOUT_STREAMS_PER_STRATUM} or controls not in {1, CONTROL_COUNT}:
            raise ValueError("held-out P21 allocation is fixed")
        streams_per_stratum, controls = HELDOUT_STREAMS_PER_STRATUM, CONTROL_COUNT
    return {
        "split": split,
        "capacities_bytes": list(CAPACITIES),
        "sleep_streams": [{"capacity_bytes": cap,
                            "stream_ids": [f"{split}:sleep:{cap}:{i:04d}"
                                           for i in range(streams_per_stratum)],
                            "arms": list(SLEEP_ARMS)} for cap in CAPACITIES],
        "curriculum_streams": [{"capacity_bytes": cap,
                                 "stream_ids": [f"{split}:curriculum:{cap}:{i:04d}"
                                                for i in range(streams_per_stratum)],
                                 "arms": list(CURRICULUM_ARMS)} for cap in CAPACITIES],
        "control_ids": [f"{split}:control:{i:04d}" for i in range(controls)],
        "primary_sleep": {"metric": "normalized_delayed_learning_curve_auc",
                          "comparison": "full_sleep_minus_replay_only",
                          "minimum_gain": 0.10,
                          "maximum_new_task_loss": 0.02},
        "primary_curriculum": {"metric": "delayed_novel_task_accuracy",
                               "comparison": "residual_minus_mean_random_fixed",
                               "minimum_gain": 0.10},
        "exposure_limits": {"source_receipts": 2,
                            "interference_world_actions": INTERFERENCE_EVENTS,
                            "curriculum_world_actions": 2,
                            "shared_budget_capacity": 64.0},
    }


def _profile_agent(*, sleep_enabled=False, scheduler_enabled=False, budget=64.0):
    agent = boot_cognition_on()
    for kind, on in (("ModelLearningPolicy", True), ("TargetLearningPolicy", False),
                     ("SleepRegimePolicy", sleep_enabled),
                     ("ConsolidationSchedulerPolicy", scheduler_enabled),
                     ("LibraryLearningPolicy", sleep_enabled),
                     ("StrategyLibraryPolicy", False),
                     ("ProcessCurriculumPolicy", False),
                     ("CurriculumLearningBridgePolicy", False),
                     ("ProcessSchemaPolicy", True), ("SolverPolicy", True),
                     ("InvariantMinerPolicy", True), ("InventionPolicy", False)):
        if agent.s.nodes(kind):
            _set_policy(agent, kind, float(on))
    budgets = [n for n in agent.s.nodes("ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    if len(budgets) != 1:
        agent.close()
        raise RuntimeError("P21 requires one shared cognition-on ThinkingBudget")
    shared = budgets[0]
    for field, value in (("capacity", budget), ("remaining", budget),
                         ("refill_per_epoch", 0.0), ("last_refill_epoch", -1.0)):
        agent.s.set_attr(shared, field, value)
    return agent, shared


def _add_shared_episode(agent, stream_id):
    context = agent.s.add_node("MemoryContext", {"context_key": f"p21:{stream_id}"})
    schema = agent.s.add_node("MemorySchema", {"name": f"p21-source:{stream_id}"})
    event = agent.s.add_node("EpisodicEvent", {
        "event_key": f"p21-source:{stream_id}", "cue_key": f"p21-cue:{stream_id}",
        "epoch": 0.0, "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "two authorized training events",
    })
    agent.inner.add_edge_unchecked(agent.agent, "experienced_event", event, {})
    agent.inner.add_edge_unchecked(event, "in_context", context, {})
    agent.inner.add_edge_unchecked(event, "instantiates_schema", schema, {})


def _interference_memory(memory, stream_id):
    world = LatchWorld(latch_ids=tuple(f"{stream_id}:interference:{i}" for i in range(INTERFERENCE_EVENTS)))
    outcomes = []
    for i in range(INTERFERENCE_EVENTS):
        receipt = world.operate(f"{stream_id}:interference:{i}", "lift")
        row = {"receipt": asdict(receipt), "workload": "interference",
               "context": (f"interference-{i}-" + "x" * 180)}
        outcomes.append(memory.put(f"interference:{i:02d}", row))
    return {"world_actions": len(world.receipts),
            "stored": sum(row["status"] == "stored" for row in outcomes),
            "rejected": sum(row["status"].startswith("rejected") for row in outcomes),
            "evicted": [key for row in outcomes for key in row.get("evicted", [])]}


def _sleep_arm(stream_id, capacity, arm, *, awake_compute_target=0):
    sleep_enabled = arm == "full_sleep"
    scheduler_enabled = arm in {"full_sleep", "replay_only"}
    agent, budget = _profile_agent(sleep_enabled=sleep_enabled,
                                   scheduler_enabled=scheduler_enabled)
    started = time.perf_counter()
    memory = ChargedMemory(capacity_bytes=capacity)
    source_world = ThermalWorld(object_ids=(f"{stream_id}:a", f"{stream_id}:b"))
    source_receipts = [source_world.apply(f"{stream_id}:a", "warm"),
                       source_world.apply(f"{stream_id}:b", "warm")]
    for i, receipt in enumerate(source_receipts):
        stored = memory.put(f"source:{i}", asdict(receipt), protected=True)
        if stored["status"] != "stored":
            raise RuntimeError(f"P21 source receipt did not fit capacity {capacity}")
    del source_receipts, source_world
    # Preserve the registered acquire → interference → offline → retrieval order.
    interference = _interference_memory(memory, stream_id)
    lifecycle = {"sleep_receipts": 0, "replay_traces": 0, "native_rule_steps": 0,
                 "awake_rehearsal_steps": 0, "completed": False}
    if arm in {"full_sleep", "replay_only"}:
        p13 = _sleep_input(agent, int(hashlib.sha256(stream_id.encode()).hexdigest()[:8], 16))
        lifecycle = {"sleep_receipts": p13["sleep_receipts"],
                     "replay_traces": p13["replay_traces"],
                     "native_rule_steps": p13["native_rule_steps"],
                     "stages": list(p13["stages"]),
                     "awake_rehearsal_steps": 0,
                     "completed": (p13["replay_traces"] > 0 and
                                   (arm != "full_sleep" or
                                    {"replay", "consolidate", "decay", "library", "recombine"}
                                    <= set(p13["stages"]))) }
        if arm == "full_sleep" and lifecycle["completed"]:
            lifecycle["memory_chunk"] = memory.put_verified_chunk("sleep:source-chunk",
                                                                   ["source:0", "source:1"])
    elif arm == "awake_rehearsal":
        _add_shared_episode(agent, stream_id)
        # Real short solved tasks match the full-sleep native-rule work.
        domain = _add_domain(agent, int(hashlib.sha256(stream_id.encode()).hexdigest()[:8], 16),
                             size=3, prefix="awake-p21")
        initial = [0, 1, 2]
        goal = agent.inner.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": [1, 2, 0], "state": initial})
        work = 0
        rehearse = 0
        while work < awake_compute_target:
            task = _task(agent, domain, f"awake-p21-{rehearse}", initial, goal, 21)
            work += _p13_settle(agent, n=8)
            if agent.s.node(task)["attrs"].get("status") != "solved":
                raise RuntimeError("P21 awake rehearsal task did not solve")
            rehearse += 1
            if rehearse > 64:
                raise RuntimeError("P21 awake rehearsal exceeded fixed work bound")
        lifecycle.update({"native_rule_steps": work, "awake_rehearsal_steps": work,
                          "awake_rehearsal_tasks": rehearse, "completed": True})
        lifecycle["memory_chunk"] = memory.put_verified_chunk("awake:source-chunk",
                                                              ["source:0", "source:1"])
    else:
        _add_shared_episode(agent, stream_id)
        lifecycle["completed"] = True

    learner = NativeTargetLearner(agent=agent, owner_id=f"p21:{stream_id}:{arm}")
    records, retrieval_receipts = [], []
    if arm in {"full_sleep", "awake_rehearsal"}:
        reconstructed, receipt = memory.retrieve(
            "sleep:source-chunk" if arm == "full_sleep" else "awake:source-chunk")
        retrieval_receipts.append(receipt)
        source_rows = reconstructed["records"] if reconstructed else []
    else:
        source_rows = []
        for i in range(TARGET_RECEIPT_COUNT):
            record, receipt = memory.retrieve(f"source:{i}")
            retrieval_receipts.append(receipt)
            if record is not None:
                source_rows.append(record)

    curve = [{"target_interactions": 0, "success": int(bool(learner.predict(
        query_id=f"{stream_id}:{arm}:checkpoint:0", action_kind="warm",
        object_type="ThermalSample", feature_key="temperature", before_value="cold",
        object_id=f"{stream_id}:unseen")))}]
    for index, row in enumerate(source_rows[:TARGET_RECEIPT_COUNT], 1):
        learner.observe_world_receipt(WorldReceipt(**row))
        steps = learner.settle()
        records.append({"event_id": row["event_id"], "status": "ingested",
                        "native_rule_steps": steps})
        curve.append({"target_interactions": index, "success": int(bool(learner.predict(
            query_id=f"{stream_id}:{arm}:checkpoint:{index}", action_kind="warm",
            object_type="ThermalSample", feature_key="temperature", before_value="cold",
            object_id=f"{stream_id}:unseen")))} )
    heldout_world = ThermalWorld(object_ids=(f"{stream_id}:unseen",))
    actual = heldout_world.apply(f"{stream_id}:unseen", "warm")
    predicted = learner.predict(query_id=f"{stream_id}:{arm}:final", action_kind="warm",
                                object_type="ThermalSample", feature_key="temperature",
                                before_value="cold", object_id=f"{stream_id}:unseen")
    delayed_success = int(bool(predicted and predicted.get("expected_after_value") == actual.after_value))
    new_task = learner.predict(query_id=f"{stream_id}:{arm}:new-task", action_kind="lift",
                               object_type="Latch", feature_key="position",
                               before_value="lowered", object_id=f"{stream_id}:new-task")
    remaining = agent.s.node(budget)["attrs"].get("remaining")
    graph = [agent.s.node(node) for node in agent.s.nodes()]
    record = {
        "stream_id": stream_id, "capacity_bytes": capacity, "arm": arm,
        "status": "COMPLETED" if lifecycle["completed"] else "FAILED",
        "delayed_accuracy": delayed_success, "new_task_accuracy": int(bool(new_task)),
        "curve": curve, "source_receipts_allocated": TARGET_RECEIPT_COUNT,
        "source_receipts_retrieved": len(source_rows), "retrieval_receipts": retrieval_receipts,
        "training_observations": records, "interference": interference,
        "memory": memory.audit(), "lifecycle": lifecycle,
        "budget_remaining": remaining, "budget_debit": 64.0 - float(remaining),
        "graph_nodes": len(graph),
        "graph_bytes": len(json.dumps(graph, sort_keys=True, default=str).encode()),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    agent.close()
    return record


def _curriculum_pool(agent, stream_id):
    evidence = []
    rng = random.Random(int(hashlib.sha256(stream_id.encode()).hexdigest()[:16], 16))
    random_order = list(range(3))
    rng.shuffle(random_order)
    random_ranks = {index: rank for rank, index in enumerate(random_order)}
    for index, key in enumerate(("pool-a", "pool-b", "pool-c")):
        node = agent.s.add_node("ProcessCurriculumEvidence", {
            "evidence_key": f"{stream_id}:{key}", "source_kind": "registered_training_pool",
            "source_id": f"{stream_id}:pool-source:{index}",
            "task_kind": "counterexample_discrimination", "action_kind": "warm",
            "object_type": "ThermalSample", "feature_key": "temperature",
            "before_value": "cold", "source_epoch": 3, "model_epoch": 2,
            "frame_epoch": 5, "status": "eligible", "split": "training",
            "expected_outcome": "unknown", "sealed_labels_present": False,
            "fixed_rank": float(index), "random_rank": float(random_ranks[index]),
        })
        agent.s.add_edge(agent.agent, "has_process_curriculum_evidence", node, {})
        evidence.append(node)
    return evidence


def _curriculum_trial(stream_id, capacity, selector):
    agent, budget = _profile_agent()
    for kind in ("ProcessCurriculumPolicy", "CurriculumLearningBridgePolicy"):
        _set_policy(agent, kind, 1.0)
    policy = agent.s.nodes("ProcessCurriculumPolicy")[0]
    agent.s.set_attr(policy, "selector_mode", selector)
    _curriculum_pool(agent, stream_id)
    for _ in range(12):
        agent.inner.run_rules(4000)
    tasks = agent.s.nodes("ProcessCurriculumTask")
    requests = agent.s.nodes("CurriculumTrainingRequest")
    if len(tasks) != 1 or len(requests) != 1:
        agent.close()
        return {"stream_id": stream_id, "capacity_bytes": capacity, "selector": selector,
                "status": "FAILED", "failure": "native_task_or_request_count"}
    task, request = tasks[0], requests[0]
    request_attrs = agent.s.node(request)["attrs"]
    world = ThermalWorld(object_ids=(f"{stream_id}:train-a", f"{stream_id}:train-b"))
    learner = NativeTargetLearner(agent=agent, owner_id=f"p21-curriculum:{stream_id}:{selector}")
    receipts = []
    for object_id in (f"{stream_id}:train-a", f"{stream_id}:train-b"):
        world_receipt = world.apply(object_id, request_attrs["action_kind"])
        observation = learner.observe_world_receipt(
            world_receipt, source_epoch=int(request_attrs["source_epoch"]),
            model_epoch=int(request_attrs["model_epoch"]),
            frame_epoch=int(request_attrs["frame_epoch"]))
        receipts.append(observation)
    learner.settle()
    for observation in receipts:
        agent.s.add_edge(request, "has_training_receipt", observation, {})
    agent.s.set_attr(request, "status", "executed")
    for _ in range(12):
        agent.inner.run_rules(4000)
    attrs = agent.s.node(task)["attrs"]
    outcome_nodes = agent.s.nodes("ProcessCurriculumOutcome")
    prediction = learner.predict(query_id=f"{stream_id}:{selector}:delayed",
                                 action_kind="warm", object_type="ThermalSample",
                                 feature_key="temperature", before_value="cold",
                                 object_id=f"{stream_id}:delayed")
    valid = (attrs.get("status") == "completed" and len(outcome_nodes) == 1
             and len(learner.hypotheses()) >= 1)
    result = {
        "stream_id": stream_id, "capacity_bytes": capacity, "selector": selector,
        "status": "COMPLETED" if valid else "FAILED",
        "selected_task_key": attrs.get("task_key"),
        "task_status": attrs.get("status"),
        "outcome_count": len(outcome_nodes), "delayed_accuracy": int(bool(prediction)),
        "target_actions": learner.accounting.target_actions,
        "native_rule_steps": learner.accounting.native_rule_steps,
        "budget_remaining": agent.s.node(budget)["attrs"].get("remaining"),
        "graph_nodes": len(agent.s.nodes()),
        "graph_bytes": len(json.dumps([agent.s.node(n) for n in agent.s.nodes()],
                                       sort_keys=True, default=str).encode()),
    }
    agent.close()
    return result


def _structural_control(control_id):
    """Exercise capacity rejection, unavailable reads, and answer-field isolation."""
    memory = ChargedMemory(capacity_bytes=256)
    rejected = memory.put("oversized", {"event_id": f"{control_id}:large",
                                         "payload": "x" * 512}, protected=True)
    train = {"event_id": f"{control_id}:observed", "before": "cold",
             "after": "warm", "source_kind": "world_receipt"}
    stored = memory.put("observed", train)
    recovered, _receipt = memory.retrieve("observed")
    answer_fields = recovered is None or any(
        key in recovered for key in ("answer", "label", "sealed_eval_id", "target_solution"))
    unavailable = memory.retrieve("evicted-or-absent")[0] is None
    passed = (rejected["status"] == "rejected_capacity" and stored["status"] == "stored"
              and recovered == train and unavailable and not memory.contains("oversized")
              and not answer_fields)
    return {"control_id": control_id, "status": "PASS" if passed else "FAIL",
            "sealed_eval_id_exposed": False, "answer_fields_exposed": answer_fields,
            "over_capacity_readthrough": memory.contains("oversized"),
            "oversized_status": rejected["status"],
            "evicted_record_unavailable": unavailable}


def run_development(*, streams_per_stratum=2, controls=1):
    payload = allocation("development", streams_per_stratum=streams_per_stratum,
                          controls=controls)
    sleep_records = []
    curriculum_records = []
    for stratum in payload["sleep_streams"]:
        cap = stratum["capacity_bytes"]
        for stream_id in stratum["stream_ids"]:
            full = _sleep_arm(stream_id, cap, "full_sleep")
            sleep_records.append(full)
            target = full["lifecycle"]["native_rule_steps"]
            for arm in SLEEP_ARMS[1:]:
                sleep_records.append(_sleep_arm(
                    stream_id, cap, arm,
                    awake_compute_target=target if arm == "awake_rehearsal" else 0))
    for stratum in payload["curriculum_streams"]:
        cap = stratum["capacity_bytes"]
        for stream_id in stratum["stream_ids"]:
            for selector in CURRICULUM_ARMS:
                curriculum_records.append(_curriculum_trial(stream_id, cap, selector))
    controls_rows = [_structural_control(control_id) for control_id in payload["control_ids"]]
    return {
        "phase": PHASE, "split": "development", "status": "development_only",
        "heldout_accessed": False, "allocation_plan": payload,
        "allocation_sha256": _digest(payload), "provenance": provenance(),
        "sleep_retention": {"status": "development_only", "records": sleep_records},
        "curriculum": {"status": "development_only", "records": curriculum_records},
        "structural_controls": controls_rows,
    }


def _read_freeze(path):
    import re
    match = re.search(r"^P21_FREEZE_JSON: (\{.*\})$", path.read_text(), re.MULTILINE)
    if not match:
        raise RuntimeError("P21 preregistration lacks its machine-readable record")
    return json.loads(match.group(1))


def _verify_preregistration(path):
    relative = str(path.resolve().relative_to(ROOT))
    if relative != PREREGISTRATION:
        raise RuntimeError("P21 preregistration path mismatch")
    if subprocess.check_output(["git", "status", "--porcelain", "--", relative],
                               cwd=ROOT, text=True):
        raise RuntimeError("P21 preregistration must be clean and committed")
    changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only",
                                       "-r", "HEAD"], cwd=ROOT, text=True).splitlines()
    if changed != [relative]:
        raise RuntimeError("the immediately preceding commit must contain only P21 preregistration")
    frozen = _read_freeze(path)
    if frozen.get("freeze_parent_commit") != subprocess.check_output(
            ["git", "rev-parse", "HEAD^"], cwd=ROOT, text=True).strip():
        raise RuntimeError("P21 preregistration parent commit mismatch")
    current = provenance()
    for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256"):
        if frozen.get(key) != current.get(key):
            raise RuntimeError(f"P21 preregistration provenance mismatch: {key}")
    expected = allocation("heldout")
    if frozen.get("allocation_sha256") != _digest(expected):
        raise RuntimeError("P21 frozen allocation digest mismatch")
    if frozen.get("allocation") != expected:
        raise RuntimeError("P21 frozen allocation content mismatch")
    runtime = current["runtime_attestation"]
    if runtime.get("status") != "ATTESTED" or runtime.get("issues"):
        raise RuntimeError("P21 holdout requires attested native runtime")
    return frozen, current, expected, _digest(expected)


def run_heldout(*, preregistration):
    path = Path(preregistration).resolve()
    frozen, current, plan, allocation_sha = _verify_preregistration(path)
    sleep_records, curriculum_records = [], []
    for stratum in plan["sleep_streams"]:
        cap = stratum["capacity_bytes"]
        for stream_id in stratum["stream_ids"]:
            full = _sleep_arm(stream_id, cap, "full_sleep")
            sleep_records.append(full)
            target = full["lifecycle"]["native_rule_steps"]
            for arm in SLEEP_ARMS[1:]:
                sleep_records.append(_sleep_arm(
                    stream_id, cap, arm,
                    awake_compute_target=target if arm == "awake_rehearsal" else 0))
    for stratum in plan["curriculum_streams"]:
        cap = stratum["capacity_bytes"]
        for stream_id in stratum["stream_ids"]:
            for selector in CURRICULUM_ARMS:
                curriculum_records.append(_curriculum_trial(stream_id, cap, selector))
    controls_rows = [_structural_control(control_id) for control_id in plan["control_ids"]]
    return {
        "phase": PHASE, "split": "heldout", "status": "heldout_pending_analysis",
        "heldout_accessed": True, "preregistration_path": str(path),
        "preregistration_sha256": _sha(path.read_bytes()),
        "freeze_commit": _commit(), "run_commit": _commit(),
        "allocation_plan": plan, "allocation_sha256": allocation_sha,
        "provenance": current,
        "sleep_retention": {"status": "heldout_unanalyzed", "records": sleep_records},
        "curriculum": {"status": "heldout_unanalyzed", "records": curriculum_records},
        "structural_controls": controls_rows,
    }


def run(split, *, preregistration=None, **kwargs):
    if split == "development":
        return run_development(**kwargs)
    if split == "heldout":
        if preregistration is None:
            raise RuntimeError("held-out P21 requires --preregistration")
        if kwargs:
            raise ValueError("held-out P21 allocation is fixed")
        return run_heldout(preregistration=preregistration)
    raise ValueError("split must be development or heldout")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--streams-per-stratum", type=int, default=2)
    parser.add_argument("--controls", type=int, default=1)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.split == "heldout":
        result = run("heldout", preregistration=args.preregistration)
    else:
        result = run("development", streams_per_stratum=args.streams_per_stratum,
                     controls=args.controls)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if result["split"] == "heldout" and result["status"] != "heldout_pending_analysis":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
