#!/usr/bin/env python3
"""Source-locked adoption, stale-base, and conflict probe for experiment deltas."""
from __future__ import annotations

import copy, hashlib, json, os, platform, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SIZES = (0, 10000, 50000)
REPEATS = 5
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_residual_adoption_v1.py",
    "scripts/analyze_thoughtexperiment_residual_adoption_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_RESIDUAL_ADOPTION_V1_PREREG_20261001.md",
    "domains/imagination.py", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_residual_adoption_v1.json"

def sha_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()

def digest(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode())

def apply_oracle(base: dict, delta: dict) -> dict:
    """Independent full-primary graph-diff application for scoped branches."""
    nodes = {int(node["id"]): copy.deepcopy(node) for node in base["nodes"]}
    edges = {(int(edge["src"]), edge["type"], int(edge["tgt"])): copy.deepcopy(edge)
             for edge in base["edges"]}
    for edge in delta["edges_removed"]:
        edges.pop((int(edge["src"]), edge["type"], int(edge["tgt"])), None)
    removed_nodes = {int(node_id) for node_id in delta["nodes_removed"]}
    for node_id in removed_nodes:
        nodes.pop(node_id, None)
    for key, edge in list(edges.items()):
        if key[0] in removed_nodes or key[2] in removed_nodes:
            edges.pop(key)
    for node in delta["nodes_added"]:
        nodes[int(node["id"])] = copy.deepcopy(node)
    for change in delta["nodes_changed"]:
        node = nodes[int(change["id"])]
        attrs = node.setdefault("attrs", {})
        for key in change["attrs_before"]:
            if key not in change["attrs_after"]:
                attrs.pop(key, None)
        attrs.update(change["attrs_after"])
        if "type_after" in change:
            node["type"] = change["type_after"]
    for edge in delta["edges_added"]:
        key = (int(edge["src"]), edge["type"], int(edge["tgt"]))
        edges[key] = {**key_to_edge(key), "attrs": {}}
    return {"nodes": [nodes[nid] for nid in sorted(nodes)],
            "edges": [edges[key] for key in sorted(edges)]}

def key_to_edge(key):
    return {"src": key[0], "type": key[1], "tgt": key[2]}

def canonical_graph(graph: dict) -> dict:
    return {"nodes": sorted(graph["nodes"], key=lambda node: int(node["id"])),
            "edges": sorted(graph["edges"], key=lambda edge:
                (int(edge["src"]), edge["type"], int(edge["tgt"]))) }

def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())

def run_branch(size: int):
    from domains.imagination import imagine
    from evaluation.substrate_capability.thoughtexperiment_productive_residual_snapshot_v1 import make_fixture
    sub, fact = make_fixture(size)
    snapshot = sub.snapshot()
    base_revision = tuple(snapshot.source_revision)
    pre = sub._inner.graph_to_dict()
    hypothesis = {
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"candidate_ordinal": 0}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": fact.value}],
    }
    result = imagine(sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
                     steps=2, cut_grounding=False, snapshot_backend="native_reusable_snapshot",
                     _snapshot_handle=snapshot, record_trace=False, _measure_phases=True)
    return sub, result, base_revision, pre

def worker(size: int, repeat: int) -> dict:
    order = ["adopt", "stale_reject", "conflict_reject"]
    if repeat % 2:
        order.reverse()
    arms = {}
    for arm in order:
        sub, result, base_revision, before = run_branch(size)
        receipt = result.conclusions
        branch_graph = result.detached._inner.graph_to_dict()
        primary_after_branch = sub._inner.graph_to_dict()
        if arm == "adopt":
            started = time.perf_counter_ns()
            sub.apply_experiment_graph_delta(base_revision, receipt)
            apply_ms = (time.perf_counter_ns() - started) / 1e6
            after = sub._inner.graph_to_dict()
            expected = apply_oracle(before, receipt)
            arms[arm] = {"apply_ms": apply_ms, "base_revision": list(base_revision),
                         "receipt_counts": {k: len(v) for k, v in receipt.items()},
                         "primary_unchanged_before_apply": before == primary_after_branch,
                         "expected_full_primary_digest": digest(canonical_graph(expected)),
                         "actual_full_primary_digest": digest(canonical_graph(after)),
                         "full_primary_parity": canonical_graph(expected) == canonical_graph(after),
                         "scoped_branch_edge_count": len(branch_graph["edges"]),
                         "base_primary_edge_count": len(before["edges"])}
        elif arm == "stale_reject":
            sub.add_node("ConcurrentPrimaryWrite", {"worker": repeat})
            at_call = sub._inner.graph_to_dict()
            started = time.perf_counter_ns()
            try:
                sub.apply_experiment_graph_delta(base_revision, receipt)
                error = None
            except RuntimeError as exc:
                error = str(exc)
            reject_ms = (time.perf_counter_ns() - started) / 1e6
            after = sub._inner.graph_to_dict()
            arms[arm] = {"reject_ms": reject_ms, "error": error,
                         "unchanged_at_rejection": at_call == after,
                         "before_call_digest": digest(at_call), "after_call_digest": digest(after)}
        else:
            malformed = copy.deepcopy(receipt)
            changed = malformed["nodes_changed"]
            if not changed:
                raise RuntimeError("fixture produced no changed-node before-image")
            changed[0]["type_before"] = "DefinitelyNotTheBaseType"
            changed[0]["type_after"] = "Fact"
            at_call = sub._inner.graph_to_dict()
            started = time.perf_counter_ns()
            try:
                sub.apply_experiment_graph_delta(base_revision, malformed)
                error = None
            except RuntimeError as exc:
                error = str(exc)
            reject_ms = (time.perf_counter_ns() - started) / 1e6
            after = sub._inner.graph_to_dict()
            arms[arm] = {"reject_ms": reject_ms, "error": error,
                         "unchanged_at_rejection": at_call == after,
                         "before_call_digest": digest(at_call), "after_call_digest": digest(after)}
    return {"schema": "ThoughtexperimentResidualAdoptionWorkerV1", "size": size,
            "repeat_index": repeat, "worker_pid": os.getpid(), "arm_order": order,
            "arms": arms}

def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3])), separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    rows = []
    for size in SIZES:
        for repeat in range(REPEATS):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(size), str(repeat)],
                                  cwd=ROOT, text=True, capture_output=True)
            if proc.returncode:
                raise SystemExit(f"worker failed size={size} repeat={repeat}: {proc.stderr[-5000:]}")
            rows.append(json.loads(proc.stdout))
            print(f"[{len(rows)}/{len(SIZES)*REPEATS}] size={size} repeat={repeat}", flush=True)
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentResidualAdoptionCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha_file(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "source_sha256": {path: sha_file(ROOT / path) for path in SOURCES},
        "protocol": {"sizes": list(SIZES), "repeats_per_size": REPEATS,
            "receipt": "conclusions; includes injected hypothesis dependencies", "arms": ["adopt", "stale_reject", "conflict_reject"]},
        "workers": rows}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + str(ROOT / "runners/dsl/python") + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, str(ROOT / "scripts/analyze_thoughtexperiment_residual_adoption_v1.py")],
                   cwd=ROOT, env=env, check=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
