#!/usr/bin/env python3
"""Source-locked direct-rule write-attribution and overhead probe."""
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
OVERRIDE = os.environ.get("OCELot_NATIVE_IMPORT_ROOT")
if OVERRIDE:
    sys.path.insert(0, OVERRIDE)

RUNNER = Path(__file__).resolve()
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_RULE_WRITE_ATTRIBUTION_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_rule_write_attribution_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_rule_write_attribution_v1_lock_20261002.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_rule_write_attribution_v1_20261002.json"
SOURCE_PATHS = (
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/ext.py",
)
WORKERS = 3
TIMING_PAIRS = 15
KINDS = ("mixed_direct", "overlap_noop")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loaded_binary() -> Path:
    from substrate_rs import _native
    return Path(_native.__file__).resolve()


def frozen() -> dict:
    files = (RUNNER, PREREG, ANALYZER, *(ROOT / name for name in SOURCE_PATHS))
    binary = loaded_binary()
    return {
        "files": {str(path.relative_to(ROOT)): sha(path) for path in files},
        "native_binary": {"path": str(binary), "sha256": sha(binary)},
    }


def make_case(kind: str):
    from substrate_rs import Substrate
    from substrate_rs.ext import add_rule

    sub = Substrate()
    a = sub.add_node("A", {"initial": 1})
    b = sub.add_node("B", {})
    c = sub.add_node("C", {})
    sub.add_edge_unchecked(a, "input", b)
    if kind == "mixed_direct":
        sub.add_edge_unchecked(a, "remove_me", b)
        sub.add_edge_unchecked(b, "remove_with_node", c)
        add_rule(sub, "mixed_writer", [("x", "input", "y"), ("x", "remove_me", "y"),
                                        ("y", "remove_with_node", "z")],
                 [["set_attr", "x", "observed", True],
                  ["del_edge", "x", "remove_me", "y"],
                  ["add_node", "fresh", "Derived", {"kind": "mixed"}],
                  ["add_edge", "x", "derived", "fresh", {}],
                  ["del_node", "z"]])
    elif kind == "overlap_noop":
        for name in ("writer_first", "writer_second"):
            add_rule(sub, name, [("x", "input", "y")],
                     [["set_attr", "x", "shared", True],
                      ["add_edge", "x", "derived", "y", {}]])
    else:
        raise ValueError(kind)
    return sub


def summarized(report: dict) -> dict:
    return {key: report.get(key) for key in ("status", "progress_steps", "passes_completed")}


def event_targets(report: dict) -> tuple[set[int], set[tuple[int, str, int]]]:
    nodes = {int(node) for event in report["rule_write_events"] for node in event["node_ids"]}
    edges = {tuple((int(edge[0]), str(edge[1]), int(edge[2])))
             for event in report["rule_write_events"] for edge in event["edges"]}
    return nodes, edges


def exact_targets(report: dict) -> tuple[set[int], set[tuple[int, str, int]]]:
    return ({int(node) for node in report["affected_nodes"]},
            {tuple((int(edge[0]), str(edge[1]), int(edge[2]))) for edge in report["affected_edges"]})


def run_fixture(kind: str) -> dict:
    plain = make_case(kind)._inner.run_rules_report(100_000, False)
    traced = make_case(kind)._inner.run_rules_delta_report(100_000, False)
    exact = make_case(kind)._inner.run_rules_snapshot_delta_report(100_000, False)
    event_nodes, event_edges = event_targets(traced)
    exact_nodes, exact_edges = exact_targets(exact)
    aggregate_nodes = set(map(int, traced["affected_nodes"]))
    aggregate_edges = {tuple((int(edge[0]), str(edge[1]), int(edge[2])))
                       for edge in traced["affected_edges"]}
    events = traced["rule_write_events"]
    return {
        "kind": kind,
        "plain": summarized(plain),
        "traced": summarized(traced),
        "exact": summarized(exact),
        "event_count": len(events),
        "event_names": sorted({event["rule_name"] for event in events}),
        "no_progress_event_count": sum(not event["progressed"] for event in events),
        "dropped_events": int(traced["rule_write_events_dropped"]),
        "exact_changed_nodes": sorted(exact_nodes),
        "exact_changed_edges": [list(edge) for edge in sorted(exact_edges)],
        "event_covers_exact_nodes": exact_nodes <= event_nodes,
        "event_covers_exact_edges": exact_edges <= event_edges,
        "aggregate_covers_event_nodes": event_nodes <= aggregate_nodes,
        "aggregate_covers_event_edges": event_edges <= aggregate_edges,
        "unattributed_exact_nodes": sorted(exact_nodes - event_nodes),
        "unattributed_exact_edges": [list(edge) for edge in sorted(exact_edges - event_edges)],
    }


def timing(kind: str, worker_index: int) -> dict:
    rng = random.Random(91000 + worker_index * 31 + KINDS.index(kind))
    pairs = []
    for _ in range(TIMING_PAIRS):
        arms = {"plain": make_case(kind), "attributed": make_case(kind)}
        order = ["plain", "attributed"]
        rng.shuffle(order)
        values = {}
        for arm in order:
            start = time.perf_counter_ns()
            if arm == "plain":
                arms[arm]._inner.run_rules_report(100_000, False)
            else:
                arms[arm]._inner.run_rules_delta_report(100_000, False)
            values[arm] = time.perf_counter_ns() - start
        pairs.append(values)
    return {"pairs": pairs, "pair_count": len(pairs)}


def worker(index: int) -> dict:
    expected = json.loads(LOCK.read_text())["sources"]
    before = frozen()
    if before != expected:
        raise RuntimeError("source/native fingerprint differs from lock")
    fixtures = [run_fixture(kind) for kind in KINDS]
    timings = {kind: timing(kind, index) for kind in KINDS}
    after = frozen()
    return {"worker_index": index, "pid": os.getpid(), "sources_before": before,
            "sources_after": after, "source_stable": before == after,
            "fixtures": fixtures, "timings": timings}


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":")))
        return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite lock or capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentRuleWriteAttributionV1Lock",
                                   "sources": frozen(), "workers": WORKERS,
                                   "timing_pairs_per_fixture_worker": TIMING_PAIRS,
                                   "fixtures": list(KINDS)}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: --lock, --run, or --worker INDEX")
    lock = json.loads(LOCK.read_text())
    if frozen() != lock["sources"]:
        raise SystemExit("current sources/native binary differ from lock")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (OVERRIDE, str(ROOT / "runners/dsl/python"), str(ROOT))))
    rows = []
    for index in range(WORKERS):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(index)], cwd=ROOT,
                              env=env, text=True, capture_output=True, timeout=180)
        if proc.returncode:
            raise RuntimeError(f"worker {index} failed: {proc.stderr[-3000:]}")
        rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    if frozen() != lock["sources"]:
        raise SystemExit("source/native drift during capture")
    CAPTURE.write_text(json.dumps({"schema": "ThoughtexperimentRuleWriteAttributionV1Results",
                                   "lock_sha256": sha(LOCK),
                                   "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                   "host": platform.platform(), "workers": rows},
                                  indent=2, sort_keys=True) + "\n")
    print(CAPTURE.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
