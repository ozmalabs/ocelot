#!/usr/bin/env python3
"""Engineering verification of scratch-Term cleanup in public shape APIs."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
SOURCE = ROOT / "runners/dsl/src/py.rs"
OUT = ROOT / "evaluation/reports/substrate_term_arena_shape_cleanup_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/term_arena_shape_cleanup_lock_20260925.json"
SIZES = (10, 100, 1000)
REPLICATES = 3
TERM = {
    "type": "Eq",
    "a": {"type": "Lit", "value": 1},
    "b": {"type": "Lit", "value": 1},
}
MALFORMED_PARTIAL = {
    "type": "Eq",
    "a": {"type": "Lit", "value": 1},
    "b": {"type": "UnknownTemporaryTerm"},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs() -> dict:
    return {
        "runner_sha256": sha(Path(__file__)),
        "py_binding_source_sha256": sha(SOURCE),
        "native_sha256": sha(NATIVE),
        "sizes": list(SIZES),
        "replicates": REPLICATES,
        "term_json": TERM,
        "malformed_partial_term_json": MALFORMED_PARTIAL,
    }


def one_run() -> dict:
    sys.path.insert(0, str(ROOT / "runners/dsl/python"))
    from substrate_rs import Substrate

    s = Substrate()
    arena_start = s._inner.term_arena_len()
    expected = s.shape_of_term(TERM)
    after_first = s._inner.term_arena_len()
    series = []
    for n in SIZES:
        before = s._inner.term_arena_len()
        start = time.perf_counter_ns()
        outputs = [s.shape_of_term(TERM) for _ in range(n)]
        elapsed = time.perf_counter_ns() - start
        series.append({
            "calls": n,
            "arena_delta": s._inner.term_arena_len() - before,
            "all_shapes_equal": all(value == expected for value in outputs),
            "elapsed_ns": elapsed,
        })

    malformed = {}
    for name in ("shape_of_term", "add_shape_node_for_term"):
        before = s._inner.term_arena_len()
        failures = 0
        for _ in range(100):
            try:
                getattr(s, name)(MALFORMED_PARTIAL)
            except ValueError:
                failures += 1
        malformed[name] = {
            "attempts": 100,
            "expected_parse_failures": failures,
            "arena_delta": s._inner.term_arena_len() - before,
        }

    before_arena = s._inner.term_arena_len()
    before_graph = s._inner.node_count()
    for _ in range(1000):
        s.add_shape_node_for_term(TERM)
    graph_delta = s._inner.node_count() - before_graph
    arena_delta = s._inner.term_arena_len() - before_arena
    return {
        "arena_start": arena_start,
        "arena_after_first_shape_query": after_first,
        "shape_queries": series,
        "malformed_partial_inputs": malformed,
        "shape_node_creation": {
            "calls": 1000,
            "arena_delta": arena_delta,
            "graph_node_delta": graph_delta,
        },
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": inputs()}, indent=2, sort_keys=True))
        return
    lock = json.loads(LOCK.read_text())
    current = inputs()
    if lock.get("locked_inputs") != current:
        raise SystemExit("locked inputs changed")
    runs = [one_run() for _ in range(REPLICATES)]
    checks = {
        "fresh_arena_starts_empty": all(row["arena_start"] == 0 for row in runs),
        "first_shape_query_releases_term": all(row["arena_after_first_shape_query"] == 0 for row in runs),
        "shape_queries_release_all_terms": all(
            item["arena_delta"] == 0 and item["all_shapes_equal"]
            for row in runs for item in row["shape_queries"]
        ),
        "malformed_partial_terms_rollback": all(
            item["expected_parse_failures"] == item["attempts"] and item["arena_delta"] == 0
            for row in runs for item in row["malformed_partial_inputs"].values()
        ),
        "shape_nodes_persist_without_term_arena_growth": all(
            row["shape_node_creation"]["arena_delta"] == 0
            and row["shape_node_creation"]["graph_node_delta"] == 1000
            for row in runs
        ),
    }
    aggregate = {}
    for n in SIZES:
        observations = [
            row["shape_queries"][i]["elapsed_ns"]
            for row in runs
            for i, count in enumerate(SIZES)
            if count == n
        ]
        aggregate[str(n)] = {
            "elapsed_ns_median": int(statistics.median(observations)),
            "elapsed_ns_range": [min(observations), max(observations)],
        }
    report = {
        "schema_version": 1,
        "run_id": "term-arena-shape-cleanup-postfix-20260925",
        "evidence_class": "post-change engineering verification; not preregistered performance evidence",
        "locked_inputs": current,
        "checks": checks,
        "timing_summary": aggregate,
        "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("shape cleanup verification failed; report preserved")


if __name__ == "__main__":
    main()
