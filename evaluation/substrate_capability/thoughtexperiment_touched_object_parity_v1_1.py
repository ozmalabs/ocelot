#!/usr/bin/env python3
"""Compare journal-touched-node validation with full-state parity audits."""
from __future__ import annotations

import copy
import gc
import hashlib
import importlib.util
import itertools
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
COST_PATH = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_touched_object_parity_v1_1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_TOUCHED_OBJECT_PARITY_V1_1_AMENDMENT_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_touched_object_parity_v1_1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_touched_object_parity_v1_1_20261004.json"
BASE_CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_20261004.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_1_analysis_20261004.json"
SIZES, BACKENDS, REPLICATES = (10_000, 100_000, 200_000), ("full_copy", "shared_graph_pages"), range(3)
SEED = 20261008


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def configurations():
    rows = [dict(frames=4, topology="independent_states", fanout=4, noise_nodes=size,
                 backend=backend, replicate=rep) for size, backend, rep in itertools.product(SIZES, BACKENDS, REPLICATES)]
    random.Random(SEED).shuffle(rows)
    return rows


CONFIGS = configurations()


def locked_inputs():
    cost = load_module("touched_parity_cost_lock", COST_PATH)
    return {"cost_breakdown_locked_inputs": cost.locked_inputs(), "runner_sha256": sha(Path(__file__)),
            "analyzer_sha256": sha(ANALYZER), "protocol_sha256": sha(PREREG),
            "baseline_capture_sha256": sha(BASE_CAPTURE), "baseline_analysis_sha256": sha(BASE_ANALYSIS)}


def validate_touched_projection(substrate, delta, before_nodes, NodeID):
    """Rebuild each touched node's expected complete state from its preimage+patch."""
    conclusions = delta.get("conclusions", delta)
    unsupported = {}
    for key in ("nodes_added", "nodes_removed", "edges_added", "edges_removed", "edges_changed"):
        rows = conclusions.get(key, [])
        if rows: unsupported[key] = len(rows)
    changed = conclusions.get("nodes_changed", [])
    if unsupported or not changed:
        return {"supported": False, "matched": False, "unsupported": unsupported,
                "changed_nodes": len(changed), "checked_attributes": 0}
    checked = 0
    for row in changed:
        nid = int(row["id"])
        before = before_nodes[nid]
        before_attrs = dict(before["attrs"])
        patch_before, patch_after = row.get("attrs_before", {}), row.get("attrs_after", {})
        for key, value in patch_before.items():
            if key not in before_attrs or before_attrs[key] != value:
                return {"supported": True, "matched": False, "reason": "journal-before-image-mismatch",
                        "unsupported": {}, "changed_nodes": len(changed), "checked_attributes": checked}
        expected_attrs = dict(before_attrs)
        for key in patch_before:
            if key not in patch_after: expected_attrs.pop(key, None)
        expected_attrs.update(patch_after)
        expected_type = row.get("type_after", before["type"])
        if "type_before" in row and row["type_before"] != before["type"]:
            return {"supported": True, "matched": False, "reason": "journal-before-type-mismatch",
                    "unsupported": {}, "changed_nodes": len(changed), "checked_attributes": checked}
        actual = substrate.node(NodeID(nid))
        checked += len(set(before_attrs) | set(expected_attrs))
        if actual["type"] != expected_type or actual["attrs"] != expected_attrs:
            return {"supported": True, "matched": False, "reason": "full-touched-node-mismatch",
                    "unsupported": {}, "changed_nodes": len(changed), "checked_attributes": checked}
    return {"supported": True, "matched": True, "unsupported": {},
            "changed_nodes": len(changed), "checked_attributes": checked}


def instrument(base, cfg):
    from substrate_rs import Substrate, _native

    state = {"export_ns": [], "digest_ns": [], "primary": None, "selected_branch": None,
             "delta": None, "before_nodes": {}, "touched": None, "preimage_ns": 0,
             "projection_ns": 0, "apply_ns": 0, "apply_calls": 0}
    original_export = Substrate.graph_to_dict
    original_digest = base.canonical_graph_digest
    original_apply = Substrate.apply_experiment_graph_delta

    def graph_export(self):
        started = time.perf_counter_ns(); graph = original_export(self); elapsed = time.perf_counter_ns() - started
        state["export_ns"].append(elapsed)
        # Before lifecycle baseline is export 1; then primary-unchanged, selected branch.
        if len(state["export_ns"]) == 3: state["selected_branch"] = self
        return graph

    def graph_digest(graph):
        started = time.perf_counter_ns(); result = original_digest(graph); state["digest_ns"].append(time.perf_counter_ns() - started)
        return result

    def apply_delta(self, revision, delta):
        state["apply_calls"] += 1
        if state["apply_calls"] != 1:
            return original_apply(self, revision, delta)
        state["primary"] = self
        state["delta"] = copy.deepcopy(delta)
        changed = delta.get("nodes_changed", [])
        started = time.perf_counter_ns()
        for row in changed:
            nid = _native.NodeID(int(row["id"]))
            source = self.node(nid)
            state["before_nodes"][int(row["id"])] = {
                "type": source["type"], "attrs": copy.deepcopy(source["attrs"]) }
        state["preimage_ns"] = time.perf_counter_ns() - started
        started = time.perf_counter_ns(); original_apply(self, revision, delta)
        state["apply_ns"] = time.perf_counter_ns() - started
        started = time.perf_counter_ns()
        state["touched"] = validate_touched_projection(self, delta, state["before_nodes"], _native.NodeID)
        state["projection_ns"] = time.perf_counter_ns() - started

    Substrate.graph_to_dict = graph_export
    Substrate.apply_experiment_graph_delta = apply_delta
    base.canonical_graph_digest = graph_digest
    state["restore"] = lambda: (setattr(Substrate, "graph_to_dict", original_export),
                                setattr(Substrate, "apply_experiment_graph_delta", original_apply),
                                setattr(base, "canonical_graph_digest", original_digest))
    return state


def run_config(cfg):
    cost = load_module("touched_parity_cost_worker", COST_PATH)
    replay = cost.load_replay(); replay.CONFIGS = [cfg]
    base = replay.load_base(); replay.load_base = lambda: base
    state = instrument(base, cfg); cost.load_replay = lambda: replay
    try:
        row = cost.worker(0)
        # Exact audit is selected branch export+digest and returned-primary export+digest.
        # Call indices are preregistered from the locked run_worker operation order.
        exact = {"selected_branch_export_ns": state["export_ns"][2],
                 "returned_primary_export_ns": state["export_ns"][3],
                 "selected_branch_digest_ns": state["digest_ns"][2],
                 "returned_primary_digest_ns": state["digest_ns"][3]}
        row["audit_measurements"] = {"all_graph_export_ns": state["export_ns"], "all_digest_ns": state["digest_ns"],
            "exact_full_parity_audit": exact, "touched_projection": state["touched"],
            "touched_preimage_capture_ns": state["preimage_ns"],
            "touched_projection_validation_ns": state["projection_ns"],
            "selected_apply_ns": state["apply_ns"], "apply_calls": state["apply_calls"]}
        control = None
        if cfg["replicate"] == 0:
            from substrate_rs import _native
            primary, branch = state["primary"], state["selected_branch"]
            start = time.perf_counter_ns()
            scratch = primary._snapshot_with_backend("shared_graph_pages").fork()
            noise_id = primary.node_count() - cfg["noise_nodes"]
            scratch.set_attr(_native.NodeID(noise_id), "audit_untracked_mutation", True)
            touched = validate_touched_projection(scratch, state["delta"], state["before_nodes"], _native.NodeID)
            touched_ns = time.perf_counter_ns() - start
            full_start = time.perf_counter_ns()
            control_actual = base.canonical_graph_digest(scratch.graph_to_dict())
            control_reference = base.canonical_graph_digest(branch.graph_to_dict())
            full_ns = time.perf_counter_ns() - full_start
            control = {"noise_node_id": noise_id, "touched_projection": touched,
                "touched_projection_passes": touched.get("matched") is True,
                "exact_global_digest_detects_mutation": control_actual != control_reference,
                "touched_control_ns": touched_ns, "full_control_audit_ns": full_ns}
            del scratch; gc.collect()
        row["audit_measurements"]["untracked_mutation_falsifier"] = control
        row["audit_measurements"]["graph_export_calls_total"] = len(state["export_ns"])
        row["audit_measurements"]["digest_calls_total"] = len(state["digest_ns"])
        return row
    finally:
        state["restore"]()


def main():
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentTouchedObjectParityV1_1Lock",
            "locked_inputs": locked_inputs(), "random_seed": SEED, "configurations": CONFIGS}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_config(CONFIGS[int(sys.argv[2])]), sort_keys=True)); return
    locked = locked_inputs(); lock = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    if lock.get("locked_inputs") != locked or lock.get("configurations") != CONFIGS:
        raise SystemExit("missing or stale pre-run source lock")
    env = dict(os.environ); env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows, failures = [], []
    for index, cfg in enumerate(CONFIGS):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(index)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=900)
        except subprocess.TimeoutExpired as exc:
            failures.append({"index": index, "configuration": cfg, "error": "worker timeout", "stderr": str(exc.stderr)[-2000:]})
            continue
        if proc.returncode == 0:
            try: rows.append(json.loads(proc.stdout))
            except json.JSONDecodeError as exc: failures.append({"index": index, "configuration": cfg,
                "error": str(exc), "stderr": proc.stderr[-2000:]})
        else: failures.append({"index": index, "configuration": cfg, "returncode": proc.returncode,
                               "stderr": proc.stderr[-4000:]})
        print(f"worker {index + 1}/{len(CONFIGS)} {'ok' if proc.returncode == 0 else 'failed'}", flush=True)
    post = locked_inputs()
    capture = {"schema": "ThoughtexperimentTouchedObjectParityV1_1", "captured_utc": datetime.now(timezone.utc).isoformat(),
        "locked_inputs": locked, "post_run_locked_inputs": post, "source_stable": post == locked,
        "random_seed": SEED, "configurations": CONFIGS, "runs": rows, "worker_failures": failures}
    if OUT.exists(): raise SystemExit("refusing to overwrite existing capture")
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__": main()
