#!/usr/bin/env python3
"""Compare global and explicit-area full closure on held-topic conversations."""
from __future__ import annotations
import gzip
import base64
import zlib
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_AREA_SETTLEMENT_PARITY_V1_1_PREREG_20261005.md"
BASE_PATH = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/held_topic_area_settlement_parity_v1_1_20261005_lock.json"
OUTDIR = ROOT / "evaluation/reports/held_topic_area_settlement_parity_v1_1_20261005"
CAPTURE = OUTDIR / "capture.json.gz"
ARMS = ("global", "barrier", "async")
AREA_BY_RULE = {
    "slang_variant_bind_denotes": "ambient_lexicon",
    "curiosity_targets_ambivalent_nodes": "ambient_curiosity",
    "gr_condition_lapse": "ambient_residual",
    "sd_decode": "shape_decode",
    "sd_transform_decode": "shape_decode",
    "sd_infer_dimension": "shape_decode",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                   default=str).encode()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("held_topic_base_v1_6", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lock_payload():
    from substrate_rs import _native
    base = load_base()
    return {
        "schema_version": 1,
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "base_runner_sha256": sha(BASE_PATH),
        "base_inputs": base.fingerprint(),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "design": {"arms": list(ARMS), "workers_per_arm": 3, "turns_per_worker": 7,
                   "area_assignments": AREA_BY_RULE,
                   "settlement": {"budget_per_area": 0, "max_rounds": 100000,
                                  "drop_residual": False}},
    }


def graph_snapshot(agent):
    graph = agent.s.graph_to_dict()
    nodes = sorted(graph.get("nodes", []), key=lambda row: int(row["id"]))
    edges = sorted(graph.get("edges", []), key=lambda row: (
        int(row["src"]), str(row["type"]), int(row["tgt"]),
        json.dumps(row.get("attrs", {}), sort_keys=True, default=str)))
    return {"nodes": nodes, "edges": edges}


def graph_fingerprints(graph):
    """Return raw ID-sensitive and ID-independent WL fingerprints plus counts."""
    nodes = graph["nodes"]
    edges = graph["edges"]
    raw = json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()
    ids = {int(row["id"]): json.dumps(
        {k: v for k, v in row.items() if k != "id"}, sort_keys=True,
        separators=(",", ":"), default=str) for row in nodes}
    colors = {node_id: hashlib.sha256(label.encode()).hexdigest()
              for node_id, label in ids.items()}
    normalized_edges = []
    for edge in edges:
        normalized_edges.append((int(edge["src"]), int(edge["tgt"]), str(edge["type"]),
                                 json.dumps(edge.get("attrs", {}), sort_keys=True,
                                            separators=(",", ":"), default=str)))
    for _ in range(4):
        neighborhoods = {node_id: [] for node_id in colors}
        for src, tgt, kind, attrs in normalized_edges:
            neighborhoods[src].append(("out", kind, attrs, colors[tgt]))
            neighborhoods[tgt].append(("in", kind, attrs, colors[src]))
        colors = {node_id: hashlib.sha256((ids[node_id] + "|" + json.dumps(
            sorted(neighborhoods[node_id]), separators=(",", ":"))).encode()).hexdigest()
            for node_id in colors}
    node_bag = sorted(colors.values())
    edge_bag = sorted((colors[src], kind, colors[tgt], attrs)
                      for src, tgt, kind, attrs in normalized_edges)
    iso_payload = json.dumps({"nodes": node_bag, "edges": edge_bag},
                             separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(iso_payload).hexdigest(), len(nodes), len(edges)


def configure_arm(base, arm):
    from substrate.world_adapter import WorldAdapter
    import substrate.boot_all as boot_all

    original_load_all = boot_all.load_all_seeds
    original_comprehend = WorldAdapter.comprehend
    original_converse = WorldAdapter.converse
    original_capture_turn = base.capture_turn
    worker_agents = []

    def load_with_areas(agent, *args, **kwargs):
        result = original_load_all(agent, *args, **kwargs)
        if arm != "global":
            results = {name: bool(agent.inner.set_rule_area(name, area))
                       for name, area in AREA_BY_RULE.items()}
            if not all(results.values()):
                raise RuntimeError(f"area assignment failed: {results}")
            actual = {str(name): str(area) for name, area in agent.inner.rule_areas()}
            for name, area in AREA_BY_RULE.items():
                if actual.get(name) != area:
                    raise RuntimeError(f"area assignment readback mismatch: {name}={actual.get(name)!r}")
            agent._area_assignment_readback = actual
        worker_agents.append(agent)
        return result

    def area_comprehend(self):
        if not getattr(self, "_area_settlement_capture_active", False) or arm == "global":
            value = original_comprehend(self)
            if getattr(self, "_area_settlement_capture_active", False):
                self._area_settlement_calls.append({"mode": "global", "steps": int(value)})
            return value
        report = self.inner.run_rules_settle(
            budget_per_area=0, max_rounds=100000, drop_residual=False,
            snapshot_round=(arm == "barrier"))
        area_totals = {}
        for round_row in report["rounds"]:
            for row in round_row["rows"]:
                bucket = area_totals.setdefault(str(row["area"]), Counter())
                for key in ("dirty", "attempted", "steps", "carried"):
                    bucket[key] += int(row[key])
        summary = {"mode": arm, "steps": int(report["steps"]),
                   "rounds": int(report["n_rounds"]),
                   "areas": list(report["areas"]),
                   "hit_max_rounds": bool(report["hit_max_rounds"]),
                   "final_residual": (int(report["rounds"][-1]["residual"])
                                      if report["rounds"] else None),
                   "area_totals": {name: dict(counts) for name, counts in sorted(area_totals.items())}}
        self._area_settlement_calls.append(summary)
        return int(report["steps"])

    def traced_converse(self, *args, **kwargs):
        self._area_settlement_calls = []
        self._area_settlement_capture_active = True
        try:
            reply = original_converse(self, *args, **kwargs)
        finally:
            self._area_settlement_capture_active = False
        self._area_settlement_last_turn = {
            "settlement_calls": self._area_settlement_calls,
            "area_assignments": getattr(self, "_area_assignment_readback", {"global": "global"}),
        }
        return reply

    def capture_turn_with_graph(agent, *args, **kwargs):
        row = original_capture_turn(agent, *args, **kwargs)
        graph = graph_snapshot(agent)
        graph_sha, graph_wl_sha, node_count, edge_count = graph_fingerprints(graph)
        turn_index = int(getattr(agent, "_area_settlement_turn_index", 0))
        row["settlement_parity"] = {**agent._area_settlement_last_turn,
            "graph_sha256": graph_sha, "graph_wl_sha256": graph_wl_sha,
            "node_count": node_count, "edge_count": edge_count,
            "snapshot_turn": turn_index == 6,
            "graph_snapshot_zlib_b64": (base64.b64encode(zlib.compress(
                json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode(), level=6)).decode()
                if turn_index == 6 else None)}
        agent._area_settlement_turn_index = turn_index + 1
        del row["task_frame"]  # the matched task frame is already in the v1 capture
        return row

    boot_all.load_all_seeds = load_with_areas
    WorldAdapter.comprehend = area_comprehend
    WorldAdapter.converse = traced_converse
    base.capture_turn = capture_turn_with_graph
    return worker_agents, (boot_all, original_load_all, WorldAdapter,
                           original_comprehend, original_converse, base,
                           original_capture_turn)


def restore(patch_state):
    boot_all, old_load, world, old_comprehend, old_converse, base, old_capture = patch_state
    boot_all.load_all_seeds = old_load
    world.comprehend = old_comprehend
    world.converse = old_converse
    base.capture_turn = old_capture


def worker(arm, rep):
    base = load_base()
    agents, patch_state = configure_arm(base, arm)
    try:
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        agent = WorldAdapter(seeds=())
        started = lock_payload()
        boot_start = time.perf_counter_ns()
        load_all_seeds(agent)
        boot_ns = time.perf_counter_ns() - boot_start
        teaching = []
        for topic, answer in base.FACTS.items():
            result, work = base.measured(agent, lambda topic=topic, answer=answer:
                agent.learn_from_teacher(topic, {"answer": answer,
                    "learn": [{"phrase": topic, "answer": answer}]}))
            teaching.append({"topic": topic, "expected_answer": answer,
                             "returned_answer": result, "work": work})
        turns = [base.capture_turn(agent, *task) for task in base.TASKS]
        graph = graph_snapshot(agent)
        graph_sha, graph_wl_sha, node_count, edge_count = graph_fingerprints(graph)
        ended = lock_payload()
        return {"arm": arm, "replicate": rep, "pid": os.getpid(),
                "boot_ns": boot_ns, "teaching": teaching, "turns": turns,
                "final_graph": {"sha256": graph_sha, "wl_sha256": graph_wl_sha, "node_count": node_count,
                                "edge_count": edge_count},
                "worker_input_sha256": object_sha(started),
                "worker_source_stable": started == ended,
                "environment": {"python": sys.version, "platform": platform.platform()}}
    finally:
        restore(patch_state)


def main():
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3])), sort_keys=True, default=str))
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
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")])
    runs = []
    for arm in ARMS:
        for rep in range(3):
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", arm, str(rep)],
                                  cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            runs.append(json.loads(proc.stdout))
    ended = lock_payload()
    payload = {"schema": "HeldTopicAreaSettlementParityV1_1", "locked_inputs": locked,
               "post_run_inputs": ended, "runs": runs}
    CAPTURE.write_bytes(gzip.compress(json.dumps(payload, sort_keys=True,
        separators=(",", ":"), default=str).encode(), compresslevel=6, mtime=0))
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "workers": len(runs),
                      "arms": {arm: sum(row["arm"] == arm for row in runs) for arm in ARMS},
                      "source_stable": ended == locked}, indent=2))
    if ended != locked:
        raise SystemExit("source changed during capture")


if __name__ == "__main__":
    main()
