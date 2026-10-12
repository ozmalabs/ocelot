#!/usr/bin/env python3
"""Check sparse thoughtexperiment readout across unrelated graph topologies."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.self_correction import _default_candidates, imagine_and_check_convergence  # noqa: E402
from evaluation.substrate_capability import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

LOCKED_SOURCES = (
    "domains/self_correction.py",
    "domains/edit_ops.py",
    "domains/collapse_model.py",
    "domains/imagination.py",
    "substrate/boot_core.py",
    "seeds/shape_decode_loop.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)
BACKENDS = ("journal", "legacy_whole_graph_diff")
CONTROL_LABELS = ("dedup_identity_fix", "add_match_guard(control)")
EXPECTED = {"dedup_identity_fix": True, "add_match_guard(control)": False}


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def make_fixture(size: int, topology: str):
    sub, native, _positive, _negative, observations = controls.make_fixture(0)
    noise = [sub.add_node("TopologyNoise", {"ordinal": i, "payload": "x" * 24})
             for i in range(size)]
    if topology == "path":
        pairs = ((i - 1, i) for i in range(1, size))
    elif topology == "star":
        pairs = ((0, i) for i in range(1, size))
    elif topology == "grid":
        width = max(1, int(size ** 0.5))
        pairs = ((i, j) for i in range(size)
                 for j in (i + 1, i + width)
                 if j < size and (j == i + width or j // width == i // width))
    else:
        raise ValueError(f"unknown topology: {topology}")
    for src, tgt in pairs:
        sub.add_edge_unchecked(noise[src], "noise_link", noise[tgt])
    candidates = _default_candidates(native, "sd_mint_quantum")
    return sub, native, observations, candidates


def run_trial(size: int, topology: str, label: str, backend: str) -> dict:
    sub, native, observations, candidates = make_fixture(size, topology)
    candidate = next((c for c in candidates if c.get("label") == label), None)
    if candidate is None:
        raise RuntimeError(f"missing control candidate {label!r}")
    before = native.graph_to_dict()
    rules_before = json.dumps(native.export_rules(), sort_keys=True, default=str)
    started = time.perf_counter_ns()
    result = imagine_and_check_convergence(
        sub, candidate, horizon=3, imagine_steps=2,
        experiment_focus_nodes=observations, focus_hops=1,
        snapshot_backend="native_full_copy_scoped",
        _force_full_graph_readout=(backend == "legacy_whole_graph_diff"),
    )
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    after = native.graph_to_dict()
    rules_after = json.dumps(native.export_rules(), sort_keys=True, default=str)
    preservation = controls.graph_preservation(before, after)
    preservation["primary_rewrite_rules_unchanged"] = rules_before == rules_after
    semantic = {
        "converges": bool(result["converges"]),
        "inert": bool(result["inert"]),
        "applied_target_count": len(result["applied"]),
        "residual_before": float(result["model_before"].residual),
        "residual_after": float(result["model_after"].residual),
        "frontier_growth_before": float(result["model_before"].frontier_growth_rate),
        "frontier_growth_after": float(result["model_after"].frontier_growth_rate),
        "steps_run": result["model_after"].imagine_steps_run,
        "conclusions": result["imagined"].conclusions,
        "derived_only": result["imagined"].derived_only,
        "forward_look_deltas_before": result["model_before"].forward_look_deltas,
        "forward_look_deltas_after": result["model_after"].forward_look_deltas,
        "primary_counts_before": [len(before["nodes"]), len(before["edges"])],
        "primary_counts_after": [len(after["nodes"]), len(after["edges"])],
        "primary_preservation": preservation,
    }
    return {"elapsed_ms": elapsed_ms, **semantic}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[10000])
    parser.add_argument("--topologies", nargs="+", choices=("path", "star", "grid"),
                        default=("path", "star", "grid"))
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")
    rng = random.Random(args.seed)
    cells = []
    for size in args.sizes:
        for topology in args.topologies:
            for label in CONTROL_LABELS:
                samples = {backend: [] for backend in BACKENDS}
                for iteration in range(args.warmups + args.repeats):
                    order = list(BACKENDS)
                    if rng.randrange(2):
                        order.reverse()
                    pair = {backend: run_trial(size, topology, label, backend)
                            for backend in order}
                    left, right = (pair[BACKENDS[0]], pair[BACKENDS[1]])
                    left_sem = {k: v for k, v in left.items() if k != "elapsed_ms"}
                    right_sem = {k: v for k, v in right.items() if k != "elapsed_ms"}
                    if left_sem != right_sem:
                        raise SystemExit(f"semantic/nested residual mismatch: {size=}, {topology=}, {label=}")
                    if left["converges"] is not EXPECTED[label] or left["inert"]:
                        raise SystemExit(f"control behavior failed: {size=}, {topology=}, {label=}")
                    if not (left["primary_preservation"]["preexisting_nodes_unchanged"]
                            and left["primary_preservation"]["preexisting_edge_instances_preserved"]
                            and left["primary_preservation"]["all_added_nodes_are_durable_trace"]
                            and left["primary_preservation"]["primary_rewrite_rules_unchanged"]):
                        raise SystemExit(f"primary isolation failed: {size=}, {topology=}, {label=}")
                    if iteration >= args.warmups:
                        for backend in BACKENDS:
                            samples[backend].append(pair[backend])
                medians = {backend: statistics.median(row["elapsed_ms"] for row in rows)
                           for backend, rows in samples.items()}
                cells.append({
                    "unrelated_nodes": size,
                    "topology": topology,
                    "candidate_label": label,
                    "repeats": args.repeats,
                    "warmups": args.warmups,
                    "median_ms": medians,
                    "journal_speedup": medians["legacy_whole_graph_diff"] / medians["journal"],
                    "exact_nested_residual_parity": True,
                    "expected_control_outcome": EXPECTED[label],
                    "primary_state_preserved": True,
                })
    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentTopologyScalingV1",
        "implementation_status": "matched positive/negative self-correction over unrelated path/star/grid topologies",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha256(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha256(binary)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "sizes": args.sizes,
            "topologies": args.topologies,
            "candidate_labels": CONTROL_LABELS,
            "timed_region": "baseline prediction, candidate application, branch prediction, and residual readout; topology fixture build excluded",
            "semantic_gate": "exact top-level and nested residual equality across journal and whole-graph diff; expected positive/negative control; unchanged primary graph/rules",
            "order_seed": args.seed,
        },
        "results": cells,
    }
    rendered = json.dumps(capture, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
