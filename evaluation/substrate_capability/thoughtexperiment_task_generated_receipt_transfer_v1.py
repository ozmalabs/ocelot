#!/usr/bin/env python3
"""Replay a frozen task through direct, eager-receipt, and snapshot-receipt paths."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_TASK_GENERATED_RECEIPT_TRANSFER_V1_PREREG_20261001.md"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_common_ground_stress.json"
SEED = ROOT / "seeds/conversation_discourse_state.json"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_task_generated_receipt_transfer_v1_lock_20261001.json"
RAW = ROOT / "evaluation/reports/thoughtexperiment_task_generated_receipt_transfer_v1_raw_20261001.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_task_generated_receipt_transfer_v1_20261001.json"
ANALYZER = ROOT / "scripts/analyze_thoughtexperiment_task_generated_receipt_transfer_v1.py"
WORKERS = 8
CAP = 100_000
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_TASK_GENERATED_RECEIPT_TRANSFER_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_task_generated_receipt_transfer_v1.py",
    "scripts/analyze_thoughtexperiment_task_generated_receipt_transfer_v1.py",
    "tests/fixtures/conversational_manifold/phase3_common_ground_stress.json",
    "seeds/conversation_discourse_state.json",
    "domains/discourse_state.py", "domains/engine_provenance.py",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/rewrite.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.lock",
)
ARMS = ("direct", "eager_receipt", "shared_snapshot_receipt")
INTENDED = {4: 0, 5: 0, 6: 0, 7: 1, 8: 1, 9: 1}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints() -> dict:
    from domains.engine_provenance import build_is_stale
    from substrate_rs import _native
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "native_path": str(Path(_native.__file__).resolve()),
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "build_stale": build_is_stale(str(ROOT)),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                               text=True).strip()}


def canon_graph(graph: dict) -> dict:
    nodes = sorted(graph["nodes"], key=lambda row: int(row["id"]))
    edges = sorted(graph["edges"], key=lambda row:
                   (int(row["src"]), str(row["type"]), int(row["tgt"]),
                    json.dumps(row.get("attrs", {}), sort_keys=True, separators=(",", ":"))))
    return {"nodes": nodes, "edges": edges}


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def effect_counts(delta: dict) -> dict:
    return {key: len(delta.get(key, [])) for key in
            ("nodes_added", "nodes_changed", "nodes_removed", "edges_added",
             "edges_changed", "edges_removed")}


def episode(rep: int, arm: str) -> dict:
    started = time.perf_counter_ns()
    imports_start = time.perf_counter_ns()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_core import load_seeds_into
    from domains.discourse_state import (ensure_common_ground, ensure_discourse_state,
                                         open_goal, record_event)
    fixture = json.loads(FIXTURE.read_text())
    imports_ns = time.perf_counter_ns() - imports_start

    stage = {name: 0 for name in ("adapter_seed_setup_ns", "event_construction_ns",
                                  "branch_setup_ns", "rule_closure_ns",
                                  "journal_readout_ns", "receipt_adoption_ns",
                                  "terminal_probe_ns")}
    oracle_ns = 0
    t = time.perf_counter_ns()
    adapter = WorldAdapter(seeds=())
    loaded = load_seeds_into(adapter.s, adapter.agent, ["conversation_discourse_state"])
    person = adapter.attach_chat_world("shared_user")
    user = person["interlocutor"]
    state = ensure_discourse_state(adapter, conversation_id="common_ground_ordinary_task",
                                   addressee=user)
    ensure_common_ground(adapter, state, addressee=user)
    stage["adapter_seed_setup_ns"] = time.perf_counter_ns() - t

    rules = [row for row in adapter.inner.export_rules()
             if row.get("name") in {"discourse_goal_select", "discourse_goal_execute",
                                     "discourse_goal_resolve"} and row.get("active", True)]
    goals: list = []
    event_ids: list[int] = []
    event_indices: dict[int, int] = {}
    steps_by_event: list[int] = []
    event_states: list[dict] = []
    receipt_rows: list[dict] = []

    for row in fixture["events"]:
        i = int(row["index"])
        kind = row["kind"]
        topic = "calendar" if i < 5 else "location"
        t = time.perf_counter_ns()
        if kind == "request":
            payload = {"common_ground_delta": "calendar_request"} if i == 0 else None
            event = record_event(adapter, state, kind=kind, speaker=user, addressee=adapter.agent,
                                 topic=topic, expectation="action", interaction_mode=row["mode"],
                                 payload=payload)
            goal = open_goal(adapter, state, kind=f"task_{len(goals)}", origin_event=event,
                             addressee=user)
            goals.append(goal)
        elif kind == "observation":
            event = record_event(adapter, state, kind=kind, speaker=user, addressee=adapter.agent,
                                 topic=topic, interaction_mode=row["mode"])
        elif kind == "assertion":
            event = record_event(adapter, state, kind=kind, speaker=user, addressee=adapter.agent,
                                 topic=topic, interaction_mode=row["mode"],
                                 payload={"common_ground_delta": "calendar_shared"})
        elif kind in {"selection", "execution"}:
            event = record_event(adapter, state, kind=kind, speaker=adapter.agent,
                                 addressee=user, interaction_mode=row["mode"])
        elif kind == "action_result":
            claim = "calendar_checked" if i == 6 else "location_shared"
            event = record_event(adapter, state, kind=kind, speaker=adapter.agent,
                                 addressee=user, interaction_mode=row["mode"],
                                 payload={"common_ground_delta": claim})
        else:
            raise RuntimeError(f"unhandled event kind: {kind}")
        if i in INTENDED:
            adapter.inner.add_edge_unchecked(event, "for_goal", goals[INTENDED[i]])
        stage["event_construction_ns"] += time.perf_counter_ns() - t
        event_id = int(event.value)
        event_ids.append(event_id)
        event_indices[event_id] = i

        receipt = None
        branch = None
        revision = None
        if arm == "direct":
            t = time.perf_counter_ns()
            progress = int(adapter.inner.run_rules(CAP))
            stage["rule_closure_ns"] += time.perf_counter_ns() - t
        else:
            revision = adapter.s.experiment_graph_rule_revision()
            t = time.perf_counter_ns()
            if arm == "eager_receipt":
                branch = adapter.s.fork_full_copy_experiment()
            else:
                branch = adapter.s.snapshot().fork()
            stage["branch_setup_ns"] += time.perf_counter_ns() - t

            branch.begin_experiment_delta_journal()
            branch.checkpoint_experiment_delta_journal()
            t = time.perf_counter_ns()
            progress = int(branch._inner.run_rules(CAP))
            stage["rule_closure_ns"] += time.perf_counter_ns() - t
            t = time.perf_counter_ns()
            receipt = branch.finish_experiment_delta_journal()["conclusions"]
            stage["journal_readout_ns"] += time.perf_counter_ns() - t
            t = time.perf_counter_ns()
            adapter.s.apply_experiment_graph_delta(revision, receipt)
            stage["receipt_adoption_ns"] += time.perf_counter_ns() - t
            receipt_rows.append({"event_index": i, "revision": list(revision),
                                 "effect_counts": effect_counts(receipt)})

        steps_by_event.append(progress)
        t = time.perf_counter_ns()
        primary_graph = adapter.inner.graph_to_dict()
        canonical = canon_graph(primary_graph)
        wire_hash = digest(primary_graph)
        canonical_hash = digest(canonical)
        branch_match = None
        if branch is not None:
            branch_graph = branch._inner.graph_to_dict()
            branch_match = canon_graph(branch_graph) == canonical
        oracle_ns += time.perf_counter_ns() - t
        event_states.append({"event_index": i, "progress_steps": progress,
                             "canonical_graph_sha256": canonical_hash,
                             "wire_graph_sha256": wire_hash,
                             "adopted_primary_matches_branch": branch_match})

    pre_terminal_graph = adapter.inner.graph_to_dict()
    t = time.perf_counter_ns()
    if arm == "direct":
        terminal_progress = int(adapter.inner.run_rules(CAP))
        terminal_delta = None
    else:
        terminal_branch = (adapter.s.fork_full_copy_experiment() if arm == "eager_receipt"
                           else adapter.s.snapshot().fork())
        terminal_branch.begin_experiment_delta_journal()
        terminal_branch.checkpoint_experiment_delta_journal()
        terminal_progress = int(terminal_branch._inner.run_rules(CAP))
        terminal_delta = terminal_branch.finish_experiment_delta_journal()["conclusions"]
    stage["terminal_probe_ns"] = time.perf_counter_ns() - t
    terminal_counts = effect_counts(terminal_delta) if terminal_delta is not None else None
    final_graph = adapter.inner.graph_to_dict()
    final_canonical = canon_graph(final_graph)
    goal_paths = {
        str(index): sorted(event_indices[int(node.value)]
                           for node in adapter.inner.neighbours(goal, "transitioned_by")
                           if int(node.value) in event_indices)
        for index, goal in enumerate(goals)
    }
    common_grounds = sorted(tuple(sorted(adapter.s.node(node)["attrs"].get("claims", [])))
                            for node in adapter.s.nodes("CommonGround"))
    oracle_ns += time.perf_counter_ns() - t
    measured_route_ns = imports_ns + sum(stage.values())
    return {"replicate": rep, "pid": os.getpid(), "arm": arm,
            "loaded_seed_ids": sorted(loaded), "active_lifecycle_rules": sorted(str(r["name"]) for r in rules),
            "event_ids": event_ids, "event_progress_steps": steps_by_event,
            "goal_ids": [int(goal.value) for goal in goals],
            "event_states": event_states, "receipts": receipt_rows,
            "goal_paths": goal_paths, "common_grounds": common_grounds,
            "terminal_progress_steps": terminal_progress, "terminal_receipt_counts": terminal_counts,
            "final_canonical_graph_sha256": digest(final_canonical),
            "final_wire_graph_sha256": digest(final_graph),
            "final_node_count": len(final_graph["nodes"]),
            "final_edge_count": len(final_graph["edges"]),
            "oracle_serialization_wall_ns": oracle_ns,
            "measured_route_wall_ns": measured_route_ns,
            "full_episode_wall_ns": time.perf_counter_ns() - started,
            "stage_wall_ns": stage,
            "all_adopted_primaries_match_branch": all(
                row["adopted_primary_matches_branch"] for row in event_states
                if row["adopted_primary_matches_branch"] is not None),
            "terminal_graph_unchanged": digest(canon_graph(pre_terminal_graph)) ==
                digest(final_canonical) and terminal_progress == 0 and
                (terminal_counts is None or not any(terminal_counts.values()))}


def worker(rep: int) -> dict:
    before = fingerprints()
    order = list(ARMS)
    random.Random(20261001 + rep).shuffle(order)
    episodes = [episode(rep, arm) for arm in order]
    after = fingerprints()
    return {"replicate": rep, "pid": os.getpid(), "arm_order": order,
            "before": before, "after": after, "episodes": episodes}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True))
        return 0
    if sys.argv[1:] == ["--lock"]:
        current = fingerprints()
        if current["build_stale"]:
            raise SystemExit("native engine build is stale")
        LOCK.write_text(json.dumps({"locked_inputs": current}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0

    locked = fingerprints()
    if locked["build_stale"]:
        raise SystemExit("native engine build is stale")
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source/native lock; run with --lock after preregistration")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), env.get("PYTHONPATH", "")))
    env["PYTHONHASHSEED"] = "0"
    env["OZMA_NO_LLM"] = "1"
    env["OZMA_SEED_PERSIST_DISABLED"] = "1"
    reps = list(range(WORKERS))
    random.Random(20261001).shuffle(reps)
    runs = []
    for serial, rep in enumerate(reps, 1):
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)]
        done = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
        if done.returncode:
            runs.append({"replicate": rep, "worker_error": done.stderr[-5000:],
                         "returncode": done.returncode})
        else:
            runs.append(json.loads(done.stdout))
        partial = {"schema": "ThoughtexperimentTaskReceiptTransferV1Partial",
                   "locked_inputs": locked, "runs": runs}
        RAW.with_suffix(".partial.json").write_text(json.dumps(partial, indent=2, sort_keys=True) + "\n")
        print(f"worker {serial}/{WORKERS} replicate={rep} rc={done.returncode}", flush=True)

    post = fingerprints()
    capture = {"schema": "ThoughtexperimentTaskReceiptTransferV1Capture",
               "host": {"platform": platform.platform(), "machine": platform.machine(),
                        "logical_cpu_count": os.cpu_count()},
               "locked_inputs": locked, "post_run_inputs": post,
               "runner_sha256": sha(Path(__file__).resolve()),
               "analyzer_sha256": sha(ANALYZER), "worker_count": WORKERS,
               "arms": list(ARMS), "runs": runs}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    summary = {"schema": "ThoughtexperimentTaskReceiptTransferV1Summary",
               "raw_path": str(RAW.relative_to(ROOT)), "locked_inputs": locked,
               "post_run_inputs": post, "worker_count": WORKERS}
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if RAW.with_suffix(".partial.json").exists():
        RAW.with_suffix(".partial.json").unlink()
    subprocess.run([sys.executable, str(ANALYZER)], cwd=ROOT, env=env, check=True)
    print(json.dumps({"workers": len(runs), "source_stable": post == locked,
                      "raw": str(RAW.relative_to(ROOT))}, sort_keys=True))
    return 0 if len(runs) == WORKERS and all("worker_error" not in row for row in runs) and post == locked else 1


if __name__ == "__main__":
    raise SystemExit(main())
