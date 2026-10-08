#!/usr/bin/env python3
"""Scale effect-only attribute replay/order probes across writers and bindings."""
from __future__ import annotations

import hashlib
import itertools
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_replay_order_scale_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(binding_count: int, writer_values: tuple[int, ...], order: tuple[str, ...]) -> dict:
    from substrate_rs import Substrate

    s = Substrate()
    inner = s._inner
    roots, targets = [], []
    for _ in range(binding_count):
        root = inner.add_node("ScaleReplayRoot", {"watched": 0})
        target = inner.add_node("ScaleReplayTarget", {})
        inner.add_edge_unchecked(root, "trigger", target, {})
        roots.append(root)
        targets.append(target)

    writer_names = [f"writer_{idx}" for idx in range(len(writer_values))]
    control_nodes = []
    for idx, _value in enumerate(writer_values):
        control = inner.add_node("ScaleReplayControl", {})
        control_nodes.append(control)
        inner.add_edge_unchecked(roots[0], f"update_{idx}", control, {})

    observed_value = {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "watched"}}
    rules = {
        "reader": {
            "name": "scale_replay_reader",
            "match": [["x", "trigger", "y"]],
            "effects": [["set_attr", "y", "observed", observed_value]],
        }
    }
    for idx, (name, value) in enumerate(zip(writer_names, writer_values)):
        rules[name] = {
            "name": f"scale_replay_{name}",
            "match": [["x", f"update_{idx}", "z"]],
            "effects": [["set_attr", "x", "watched", value]],
        }
    for name in order:
        inner.add_rule(rules[name])

    progress = inner.run_rules(100)
    graph = inner.graph_to_dict()
    final_by_id = {n["id"]: n for n in graph["nodes"]}
    final_values = [final_by_id[root.value]["attrs"]["watched"] for root in roots]
    observed_values = [final_by_id[target.value]["attrs"].get("observed") for target in targets]
    terminal_progress = inner.run_rules(1)
    mismatch_count = sum(actual != expected for actual, expected in zip(observed_values, final_values))
    return {
        "binding_count": binding_count,
        "writer_count": len(writer_values),
        "writer_values": list(writer_values),
        "rule_order": list(order),
        "progress_count": progress,
        "terminal_progress": terminal_progress,
        "oracle_values": final_values,
        "reader_values": observed_values,
        "mismatch_count": mismatch_count,
        "mismatch_fraction": mismatch_count / binding_count,
        "reader_matches_final_graph_oracle": mismatch_count == 0,
        "graph": graph,
    }


def main() -> None:
    writer_families = ((5,), (3, 7), (-2, 5, 11))
    binding_counts = (8, 64, 128)
    cases = []
    for writer_values in writer_families:
        labels = ("reader", *(f"writer_{idx}" for idx in range(len(writer_values))))
        for order in itertools.permutations(labels):
            for binding_count in binding_counts:
                cases.append(run_case(binding_count, writer_values, order))

    grouped = []
    for writer_values in writer_families:
        subset = [c for c in cases if c["writer_values"] == list(writer_values)]
        grouped.append({
            "writer_values": list(writer_values),
            "writer_count": len(writer_values),
            "schedule_count": len(subset),
            "binding_counts": list(binding_counts),
            "mismatching_schedules_by_binding_count": {
                str(n): sum(not c["reader_matches_final_graph_oracle"]
                            for c in subset if c["binding_count"] == n)
                for n in binding_counts
            },
            "mismatch_fractions_by_binding_count": {
                str(n): [c["mismatch_fraction"] for c in subset if c["binding_count"] == n]
                for n in binding_counts
            },
        })
    checks = {
        "all_cases_settle": all(c["terminal_progress"] == 0 for c in cases),
        "all_oracles_read_final_graph": all(
            len(c["oracle_values"]) == c["binding_count"]
            and len(c["reader_values"]) == c["binding_count"] for c in cases),
        "all_writer_orders_covered": len(cases) == sum(
            len(tuple(itertools.permutations(("reader", *(f"writer_{i}" for i in range(len(values)))))))
            * len(binding_counts) for values in writer_families),
        "at_least_one_stale_schedule_per_family_and_scale": all(
            group["mismatching_schedules_by_binding_count"][str(n)] > 0
            for group in grouped for n in binding_counts),
        "largest_binding_count_exceeds_prior_envelope": max(binding_counts) > 32,
    }
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    payload = {
        "schema_version": 1,
        "run_id": "substrate-replay-order-scale-20260925",
        "scope": "all authored rule-order permutations for one, two, and three writers at 8, 64, and 128 reader bindings; one writer writes root 0 while the remaining reader bindings are controls",
        "claim_boundary": "Deterministic mechanism sweep over one graph generator. It measures stale effect-only Attr reads against settled final graph state; it does not establish frequency on authored tasks or natural-world workloads, nor compare alternate scheduler policies.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(ext),
            "native_extension_sha256": sha(ext),
            "source_sha256": {
                "harness": sha(Path(__file__).resolve()),
                "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
                "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
                "stage_a": sha(ROOT / "runners/dsl/src/stage_a.rs"),
                "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            },
        },
        "checks": checks,
        "grouped_results": grouped,
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(cases), "checks": checks, "grouped_results": grouped,
                      "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("replay order scale probe failed")


if __name__ == "__main__":
    main()
