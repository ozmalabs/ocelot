#!/usr/bin/env python3
"""Measure native closure cost for the finite-key insertion rule family."""
from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/mint_termination_scale_cost_v1_1_20260926.json"
SIZES = (16, 32, 64, 128, 256, 512, 1024)
SIGNATURE_COUNTS = (1, 2, 4)
REPEATS = 7
SEED = 1701
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402
from substrate_rs import _native  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def rules_for(m: int) -> list[dict]:
    return [{
        "name": f"mint_tag_{i}",
        "match": [["x", "link", "y"]],
        "effects": [
            ["add_node_if_absent", f"w{i}", "Witness", {"tag": f"w{i}"}],
            ["add_edge", "y", "link", f"w{i}", {}],
        ],
    } for i in range(m)]


def one_case(n: int, m: int, replicate: int, warmup: bool = False) -> dict:
    edges = [(i, (i + 1) % n) for i in range(n)]
    rules = rules_for(m)
    analyzer_result = analyze(
        rules, [f"n{i}" for i in range(n)],
        [[f"n{i}", "link", f"n{j}", {}] for i, j in edges])
    if not analyzer_result["accepted"]:
        raise RuntimeError(f"checker refused locked rule fixture: {analyzer_result['reasons']}")

    t0 = time.perf_counter_ns()
    sub = _native.Substrate()
    engine_init_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    node_ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for i, j in edges:
        sub.add_edge_unchecked(node_ids[i], "link", node_ids[j])
    for rule in rules:
        sub.add_rule(rule)
    setup_ns = time.perf_counter_ns() - t0

    progress_budget = analyzer_result["progress_steps_upper_bound"] + 1
    t0 = time.perf_counter_ns()
    report = sub.run_rules_report(progress_budget, False)
    closure_ns = time.perf_counter_ns() - t0
    graph = sub.graph_to_dict()

    actual_nodes = {(x["type"], json.dumps(x["attrs"], sort_keys=True, separators=(",", ":")))
                    for x in graph["nodes"]}
    expected_nodes = {
        *(('Seed', json.dumps({"idx": i}, sort_keys=True, separators=(",", ":"))) for i in range(n)),
        *(('Witness', json.dumps({"tag": f"w{i}"}, sort_keys=True, separators=(",", ":"))) for i in range(m)),
    }
    witness_ids = {x["id"] for x in graph["nodes"] if x["type"] == "Witness"}
    all_ids = {x["id"] for x in graph["nodes"]}
    expected_edges = {(node_ids[i], "link", node_ids[(i + 1) % n], "{}") for i in range(n)}
    expected_edges |= {(src, "link", tgt, "{}") for src in all_ids for tgt in witness_ids}
    actual_edges = {(e["src"], e["type"], e["tgt"], json.dumps(e["attrs"], sort_keys=True, separators=(",", ":")))
                    for e in graph["edges"]}
    labels = {x["id"]: (x["type"], x["attrs"]) for x in graph["nodes"]}
    def label(node_id):
        typ, attrs = labels[node_id]
        return (typ, tuple(sorted(attrs.items())))
    projection_nodes = sorted((x["type"], tuple(sorted(x["attrs"].items()))) for x in graph["nodes"])
    projection_edges = sorted((label(e["src"]), e["type"], label(e["tgt"]),
                               tuple(sorted(e["attrs"].items()))) for e in graph["edges"])
    projection_hash = json_sha({"nodes": projection_nodes, "edges": projection_edges})
    checks = {
        "analyzer_accepts": analyzer_result["accepted"],
        "native_fixed_point": report["status"] == "fixed_point",
        "no_budget_overshoot": report["budget_overshoot"] == 0,
        "exact_node_set": actual_nodes == expected_nodes,
        "exact_edge_set": actual_edges == expected_edges,
        "progress_within_bound": report["progress_steps"] <= analyzer_result["progress_steps_upper_bound"],
    }
    result = {
        "case_id": f"n{n}_m{m}_r{replicate}",
        "n_initial_nodes": n,
        "m_mint_signatures": m,
        "replicate": replicate,
        "warmup_discarded": warmup,
        "engine_init_ns": engine_init_ns,
        "setup_ns": setup_ns,
        "closure_ns": closure_ns,
        "native_report": report,
        "analyzer_bound": analyzer_result["progress_steps_upper_bound"],
        "actual_node_count": len(graph["nodes"]),
        "actual_edge_count": len(graph["edges"]),
        "expected_edge_count": n + m * (n + m),
        "actual_graph_projection_sha256": projection_hash,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    if warmup:
        return result
    return result


def main() -> int:
    warmups = [one_case(n, m, 0, warmup=True) for n in SIZES for m in SIGNATURE_COUNTS]
    schedule = [(n, m, rep) for n in SIZES for m in SIGNATURE_COUNTS for rep in range(1, REPEATS + 1)]
    random.Random(SEED).shuffle(schedule)
    cases = [one_case(*cell) for cell in schedule]
    native_path = Path(_native.__file__).resolve()
    hashed_paths = [Path(__file__).resolve(),
                    ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_COST_V1_1_AMENDMENT_20260926.md",
                    ROOT / "scripts/analyze_mint_termination_fragment.py",
                    ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/graph.rs"]
    payload = {
        "schema_version": 1,
        "run_id": "mint-termination-scale-cost-v1.1-20260926",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version,
        "platform": platform.platform(),
        "provenance": {
            "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in hashed_paths},
            "native_path": str(native_path),
            "native_sha256": sha(native_path),
        },
        "design": {"sizes": list(SIZES), "mint_signature_counts": list(SIGNATURE_COUNTS),
                   "repeats_per_cell": REPEATS, "warmups_per_cell": 1,
                   "schedule_seed": SEED, "cells": len(schedule),
                   "timed_fields": ["setup_ns", "closure_ns"],
                   "claim_limit": "fixed finite-key recursive rule family on directed cycle initial graphs"},
        "warmups": warmups,
        "cases": cases,
        "failed_cases": [x["case_id"] for x in cases if not x["all_checks_pass"]],
        "all_checks_pass": all(x["all_checks_pass"] for x in cases),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": payload["all_checks_pass"],
                      "cells": len(cases), "failed_cases": payload["failed_cases"],
                      "output": str(OUT)}, indent=2))
    return 0 if payload["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
