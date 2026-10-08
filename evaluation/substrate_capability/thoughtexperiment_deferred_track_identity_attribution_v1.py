#!/usr/bin/env python3
"""Source-locked producer attribution probe for deferred TrackIdentity."""
from __future__ import annotations

import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
OVERRIDE = os.environ.get("OCELot_NATIVE_IMPORT_ROOT")
if OVERRIDE:
    sys.path.insert(0, OVERRIDE)
RUNNER = Path(__file__).resolve()
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_TRACK_IDENTITY_ATTRIBUTION_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_deferred_track_identity_attribution_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_deferred_track_identity_attribution_v1_lock_20261002.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_deferred_track_identity_attribution_v1_20261002.json"
SOURCES = ("runners/dsl/src/graph.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs")
WORKERS = 3
PROGRESS_BUDGET = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen() -> dict:
    from substrate_rs import _native
    files = (RUNNER, PREREG, ANALYZER, *(ROOT / source for source in SOURCES))
    binary = Path(_native.__file__).resolve()
    return {"files": {str(path.relative_to(ROOT)): sha(path) for path in files},
            "native_binary": {"path": str(binary), "sha256": sha(binary)}}


def make_case():
    from substrate_rs import Substrate
    sub = Substrate()
    prev = [sub.add_node("PrevPercept", {"feat": [0.0, 0.0]}),
            sub.add_node("PrevPercept", {"feat": [9.0, 9.0]})]
    cur = [sub.add_node("CurPercept", {"feat": [0.05, 0.05]}),
           sub.add_node("CurPercept", {"feat": [9.05, 9.05]}),
           sub.add_node("CurPercept", {"feat": [500.0, 500.0]})]
    anchor = sub.add_node("Anchor", {})
    sub.add_edge_unchecked(anchor, "has_anchor", anchor)
    sub._inner.add_rule({"name": "trans_frame_identity_assignment",
                  "match": [["a", "has_anchor", "a"]],
                  "effects": [["track_identity",
                               {"__term__": {"type": "NodesOfType", "node_type": "PrevPercept"}},
                               {"__term__": {"type": "NodesOfType", "node_type": "CurPercept"}},
                               "feat", None, None, "identity", 1.0]]})
    sub._inner.add_rule({"name": "trace_direct_control",
                  "match": [["a", "has_anchor", "a"]],
                  "effects": [["set_attr", "a", "direct_probe", True]]})
    return sub, sorted(int(node.value) for node in prev + cur)


def targets(report: dict):
    events = report["rule_write_events"]
    nodes = {int(node) for event in events for node in event["node_ids"]}
    edges = {tuple((int(edge[0]), str(edge[1]), int(edge[2])))
             for event in events for edge in event["edges"]}
    return nodes, edges


def exact_targets(report: dict):
    return (set(map(int, report["affected_nodes"])),
            {tuple((int(edge[0]), str(edge[1]), int(edge[2]))) for edge in report["affected_edges"]})


def execute() -> dict:
    traced_sub, percept_ids = make_case()
    exact_sub, _ = make_case()
    traced = traced_sub._inner.run_rules_delta_report(PROGRESS_BUDGET, False)
    exact = exact_sub._inner.run_rules_snapshot_delta_report(PROGRESS_BUDGET, False)
    plain_sub, _ = make_case()
    plain = plain_sub._inner.run_rules_report(PROGRESS_BUDGET, False)
    event_nodes, event_edges = targets(traced)
    exact_nodes, exact_edges = exact_targets(exact)
    aggregate_nodes = set(map(int, traced["affected_nodes"]))
    aggregate_edges = {tuple((int(edge[0]), str(edge[1]), int(edge[2]))) for edge in traced["affected_edges"]}
    events = traced["rule_write_events"]
    deferred = [event for event in events if event["deferred"]]
    direct = [event for event in events if not event["deferred"]]
    producer = [event for event in deferred if event["rule_name"] == "trans_frame_identity_assignment"]
    direct_control = [event for event in direct if event["rule_name"] == "trace_direct_control"]
    changed_percepts = set(percept_ids) & exact_nodes
    producer_nodes = {int(node) for event in producer for node in event["node_ids"]}
    return {"plain": {key: plain[key] for key in ("status", "progress_steps", "passes_completed")},
            "traced": {key: traced[key] for key in ("status", "progress_steps", "passes_completed")},
            "exact": {key: exact[key] for key in ("status", "progress_steps", "passes_completed")},
            "event_count": len(events), "deferred_events": len(deferred),
            "event_names": sorted({event["rule_name"] for event in events}),
            "producer_events": producer, "direct_control_events": direct_control,
            "changed_percept_ids": sorted(changed_percepts),
            "producer_covers_changed_percepts": changed_percepts <= producer_nodes,
            "event_covers_exact_nodes": exact_nodes <= event_nodes,
            "event_covers_exact_edges": exact_edges <= event_edges,
            "aggregate_covers_event_nodes": event_nodes <= aggregate_nodes,
            "aggregate_covers_event_edges": event_edges <= aggregate_edges,
            "dropped_events": int(traced["rule_write_events_dropped"])}


def worker(index: int) -> dict:
    expected = json.loads(LOCK.read_text())["sources"]
    before = frozen()
    if before != expected: raise RuntimeError("source/native fingerprint differs from lock")
    result = execute()
    after = frozen()
    return {"worker_index": index, "pid": os.getpid(), "sources_before": before,
            "sources_after": after, "source_stable": before == after, "result": result}


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":"))); return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists(): raise SystemExit("refusing to overwrite lock or capture")
        LOCK.write_text(json.dumps({"schema": "DeferredTrackIdentityAttributionV1Lock",
                                   "sources": frozen(), "workers": WORKERS,
                                   "progress_budget": PROGRESS_BUDGET}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    if sys.argv[1:] != ["--run"]: raise SystemExit("usage: --lock, --run, or --worker INDEX")
    lock = json.loads(LOCK.read_text())
    if frozen() != lock["sources"]: raise SystemExit("source/native drift from lock")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (OVERRIDE, str(ROOT / "runners/dsl/python"), str(ROOT))))
    workers = []
    for index in range(WORKERS):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(index)], cwd=ROOT,
                              env=env, text=True, capture_output=True, timeout=180)
        if proc.returncode: raise RuntimeError(f"worker {index} failed: {proc.stderr[-2500:]}")
        workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    if frozen() != lock["sources"]: raise SystemExit("source/native drift during capture")
    CAPTURE.write_text(json.dumps({"schema": "DeferredTrackIdentityAttributionV1Results",
                                   "lock_sha256": sha(LOCK), "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                   "host": platform.platform(), "workers": workers}, indent=2, sort_keys=True) + "\n")
    print(CAPTURE.relative_to(ROOT)); return 0


if __name__ == "__main__": raise SystemExit(main())
