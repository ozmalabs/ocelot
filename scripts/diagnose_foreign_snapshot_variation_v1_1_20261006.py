#!/usr/bin/env python3
"""Trace foreign audience snapshots during the held-topic baseline workload."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_FOREIGN_SNAPSHOT_VARIATION_DIAGNOSTIC_V1_1_PREREG_20261006.md"
RUNNER = Path(__file__).resolve()
PARITY_RUNNER = ROOT / "scripts/substrate_held_topic_area_settlement_parity_v1_1.py"
BASE_RUNNER = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"
LOCK = ROOT / "evaluation/substrate_capability/foreign_snapshot_variation_v1_1_20261006_lock.json"
OUTDIR = ROOT / "evaluation/reports/foreign_snapshot_variation_v1_1_20261006"
CAPTURE = OUTDIR / "capture.json.gz"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def load_parity_runner():
    spec = importlib.util.spec_from_file_location("settlement_parity_runner_v11", PARITY_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lock_payload():
    from substrate_rs import _native
    parity = load_parity_runner()
    base = parity.load_base()
    return {
        "schema_version": 1,
        "protocol_sha256": sha(PROTOCOL),
        "diagnostic_runner_sha256": sha(RUNNER),
        "parity_runner_sha256": sha(PARITY_RUNNER),
        "base_runner_sha256": sha(BASE_RUNNER),
        "base_inputs": base.fingerprint(),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "worker_hash_seeds": [1, 2, 3],
        "design": {"arm": "global", "workers": 3, "turns_per_worker": 7,
                   "trace": "foreign_snapshot input, reconstructed enumeration, model result"},
    }


def install_trace(parity):
    old_configure = parity.configure_arm
    old_restore = parity.restore
    import domains.system_model as system_model
    old_model_system = system_model.model_system

    def configure_with_trace(base, arm):
        agents, old_patch_state = old_configure(base, arm)
        events_by_agent = {}
        old_capture = base.capture_turn

        def traced_model_system(agent, target="self", **kwargs):
            result = old_model_system(agent, target, **kwargs)
            if isinstance(target, dict) and target.get("kind") == "foreign_snapshot":
                graph = target.get("graph", {})
                from substrate_rs import _native
                foreign = _native.Substrate()
                foreign.graph_from_dict(graph)
                enum_ids = [int(system_model._v(node)) for node in foreign.nodes(None)]
                raw_nodes = {int(row["id"]): row for row in graph.get("nodes", [])}
                enum_labels = [json.dumps({k: v for k, v in raw_nodes.get(nid, {}).items() if k != "id"},
                                          sort_keys=True, separators=(",", ":"), default=str)
                               for nid in enum_ids]
                result_fields = {}
                for name in ("target_kind", "target_id", "node_count", "horizon", "grounded",
                             "counts_trajectory", "fixed_sample_foreign_ids",
                             "volatile_sample_foreign_ids", "method", "frontier_growth_rate",
                             "converged", "forward_look_ran", "imagine_steps_run"):
                    if hasattr(result, name):
                        value = getattr(result, name)
                        if name == "model_node":
                            continue
                        result_fields[name] = value
                event = {
                    "input_graph_sha256": object_sha(graph),
                    "input_node_count": len(graph.get("nodes", [])),
                    "input_edge_count": len(graph.get("edges", [])),
                    "input_graph": graph,
                    "reconstructed_foreign_enumeration_ids": enum_ids,
                    "reconstructed_foreign_enumeration_labels": enum_labels,
                    "result": result_fields,
                }
                events_by_agent.setdefault(id(agent), []).append(event)
            return result

        system_model.model_system = traced_model_system

        def capture_with_trace(agent, *args, **kwargs):
            key = id(agent)
            prior = len(events_by_agent.get(key, []))
            row = old_capture(agent, *args, **kwargs)
            row["foreign_snapshot_diagnostics"] = events_by_agent.get(key, [])[prior:]
            parity = row.get("settlement_parity", {})
            parity.pop("graph_snapshot_zlib_b64", None)
            parity["snapshot_turn"] = False
            return row

        base.capture_turn = capture_with_trace
        return agents, (old_patch_state, base, old_capture)

    def restore_with_trace(state):
        old_patch_state, base, old_capture = state
        base.capture_turn = old_capture
        system_model.model_system = old_model_system
        old_restore(old_patch_state)

    parity.configure_arm = configure_with_trace
    parity.restore = restore_with_trace
    return (parity, old_configure, old_restore, system_model, old_model_system)


def worker(rep):
    parity = load_parity_runner()
    installed = install_trace(parity)
    try:
        result = parity.worker("global", rep)
        result["diagnostic_worker_environment"] = {"PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED")}
        result["diagnostic_source_sha256"] = sha(RUNNER)
        return result
    finally:
        parity, old_configure, old_restore, system_model, old_model_system = installed
        parity.configure_arm = old_configure
        parity.restore = old_restore
        system_model.model_system = old_model_system


def main():
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    locked = lock_payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("source lock absent or stale")
    if CAPTURE.exists():
        raise SystemExit(f"refusing to overwrite {CAPTURE}")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "runners/dsl/python"),
                                         str(ROOT / "scripts"), env.get("PYTHONPATH", "")])
    runs = []
    for rep, seed in enumerate((1, 2, 3)):
        worker_env = dict(env)
        worker_env["PYTHONHASHSEED"] = str(seed)
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(rep), str(seed)], cwd=ROOT,
                              env=worker_env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    ended = lock_payload()
    payload = {"schema": "ForeignSnapshotVariationDiagnosticV1_1", "locked_inputs": locked,
               "post_run_inputs": ended, "runs": runs,
               "environment": {"PYTHONHASHSEED_by_worker": [1, 2, 3], "platform": platform.platform()}}
    CAPTURE.write_bytes(gzip.compress(json.dumps(payload, sort_keys=True,
        separators=(",", ":"), default=str).encode(), compresslevel=6, mtime=0))
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "workers": len(runs),
                      "source_stable": ended == locked}, indent=2))
    if ended != locked:
        raise SystemExit("source changed during capture")


if __name__ == "__main__":
    main()
