#!/usr/bin/env python3
"""Locked equal-size/equal-edge topology stress for thoughtexperiment fanout."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
COST_PATH = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_edge_topology_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_EDGE_TOPOLOGY_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_edge_topology_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_edge_topology_v1_20261004.json"
BASE_CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_20261004.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_1_analysis_20261004.json"
TOPOLOGIES, BACKENDS, REPLICATES = ("path", "star", "cluster_star", "random_recursive_tree"), ("full_copy", "shared_graph_pages"), range(3)
NOISE_NODES, SEED = 100_000, 20261007


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def configurations():
    rows = [dict(frames=4, topology="independent_states", fanout=4, noise_nodes=NOISE_NODES,
                 noise_edge_topology=topology, noise_edge_count=NOISE_NODES - 1,
                 backend=backend, replicate=rep)
            for topology, backend, rep in itertools.product(TOPOLOGIES, BACKENDS, REPLICATES)]
    random.Random(SEED).shuffle(rows)
    return rows


CONFIGS = configurations()


def locked_inputs():
    cost = load_module("fanout_edge_topology_cost_lock", COST_PATH)
    return {"cost_breakdown_locked_inputs": cost.locked_inputs(),
            "runner_sha256": sha(Path(__file__)), "analyzer_sha256": sha(ANALYZER),
            "protocol_sha256": sha(PREREG), "baseline_capture_sha256": sha(BASE_CAPTURE),
            "baseline_analysis_sha256": sha(BASE_ANALYSIS)}


def add_noise_edges(base, cfg):
    original = base.build_workload

    def build(cfg_in):
        result = original(cfg_in)
        world = result[0]
        n = cfg_in["noise_nodes"]
        first = world.s.node_count() - n
        topology = cfg_in["noise_edge_topology"]
        if topology == "path":
            pairs = ((first + i, first + i + 1) for i in range(n - 1))
        elif topology == "star":
            pairs = ((first, first + i) for i in range(1, n))
        elif topology == "cluster_star":
            # 100 stars of 1,000 nodes, joined by 99 edges between centers.
            block = n // 100
            within = ((first + start, first + start + offset)
                      for start in range(0, n, block) for offset in range(1, block))
            bridges = ((first + i * block, first + (i + 1) * block) for i in range(99))
            pairs = itertools.chain(within, bridges)
        elif topology == "random_recursive_tree":
            rng = random.Random(SEED + cfg_in["replicate"])
            pairs = ((first + i, first + rng.randrange(i)) for i in range(1, n))
        else:
            raise ValueError(f"unknown noise topology: {topology}")
        added = 0
        for src, tgt in pairs:
            world.inner.add_edge_unchecked(src, "thoughtexperiment_noise_link", tgt, {})
            added += 1
        if added != cfg_in["noise_edge_count"]:
            raise RuntimeError(f"edge topology produced {added} edges, expected {cfg_in['noise_edge_count']}")
        result = (*result, {"noise_nodes": n, "noise_edges": added, "topology": topology})
        return result[:7]

    base.build_workload = build


def run_config(cfg):
    cost = load_module("fanout_edge_topology_cost_worker", COST_PATH)
    replay = cost.load_replay()
    replay.CONFIGS = [cfg]
    base = replay.load_base()
    add_noise_edges(base, cfg)
    replay.load_base = lambda: base
    cost.load_replay = lambda: replay
    return cost.worker(0)


def main():
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentFanoutEdgeTopologyV1Lock",
            "locked_inputs": locked_inputs(), "random_seed": SEED, "configurations": CONFIGS},
            indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_config(CONFIGS[int(sys.argv[2])]), sort_keys=True)); return
    locked = locked_inputs()
    lock = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    if lock.get("locked_inputs") != locked or lock.get("configurations") != CONFIGS:
        raise SystemExit("missing or stale pre-run source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows, failures = [], []
    for index, cfg in enumerate(CONFIGS):
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(index)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=900)
        except subprocess.TimeoutExpired as exc:
            failures.append({"index": index, "configuration": cfg, "error": "worker timeout",
                             "stderr": str(exc.stderr)[-2000:]})
            continue
        if proc.returncode == 0:
            try: rows.append(json.loads(proc.stdout))
            except json.JSONDecodeError as exc: failures.append({"index": index, "configuration": cfg,
                "error": str(exc), "stderr": proc.stderr[-2000:]})
        else: failures.append({"index": index, "configuration": cfg, "returncode": proc.returncode,
                               "stderr": proc.stderr[-4000:]})
        print(f"worker {index + 1}/{len(CONFIGS)} {'ok' if proc.returncode == 0 else 'failed'}", flush=True)
    post = locked_inputs()
    capture = {"schema": "ThoughtexperimentFanoutEdgeTopologyV1", "captured_utc": datetime.now(timezone.utc).isoformat(),
               "locked_inputs": locked, "post_run_locked_inputs": post, "source_stable": post == locked,
               "random_seed": SEED, "configurations": CONFIGS, "runs": rows, "worker_failures": failures}
    if OUT.exists(): raise SystemExit("refusing to overwrite existing capture")
    OUT.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__": main()
