#!/usr/bin/env python3
"""Source-locked end-to-end baseline for self-correction rehearsal.

Runs the existing `imagine_and_check_convergence` path on a fresh substrate
for each arm/repeat. The correct and wrong candidate outcomes are controls;
unrelated graph load is added without connecting it to the correction frame.
This measures the current detached-copy implementation, not a CoW fork.

Example:
  python3 evaluation/substrate_capability/thoughtexperiment_self_correction_baseline_v1.py \
      --sizes 0 1000 10000 --repeats 3 --warmups 1 \
      --out evaluation/reports/thoughtexperiment_self_correction_baseline_v1.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners" / "dsl" / "python")]

import substrate_rs as srs  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
import domains.reflective_faculty as rf  # noqa: E402
from domains.self_correction import (  # noqa: E402
    _default_candidates,
    imagine_and_check_convergence,
)

LOCKED_SOURCES = (
    "domains/self_correction.py",
    "domains/self_correct_dispatch.py",
    "domains/imagination.py",
    "domains/collapse_model.py",
    "domains/reflective_faculty.py",
    "substrate/boot_core.py",
    "seeds/shape_decode_loop.json",
    "tests/test_self_correction.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/cognitive_cycle.rs",
    "runners/dsl/src/graph_rules.rs",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def summarize(values: list[float]) -> dict:
    return {
        "median_ms": statistics.median(values) * 1000.0,
        "p95_ms": percentile(values, 0.95) * 1000.0,
        "min_ms": min(values) * 1000.0,
        "max_ms": max(values) * 1000.0,
    }


def make_fixture(unrelated_nodes: int):
    substrate, agent_root = boot_core()
    native = rf._native_eval2(substrate)
    rf._ensure_shape_decode_loop(substrate, native, agent_root)
    for i in range(3):
        obs = substrate.add_node(
            "Observation", {"signature": [[f"zzzimag{i}", "X"]],
                            "key": [f"zzzimag{i}"], "status": "pending"})
        substrate.add_edge(agent_root, "observed", obs)

    if unrelated_nodes:
        nodes = [substrate.add_node("ThoughtexperimentNoise", {
            "ordinal": i, "partition": i % 32, "payload": "x" * 24,
        }) for i in range(unrelated_nodes)]
        for i in range(unrelated_nodes - 1):
            substrate.add_edge_unchecked(nodes[i], "te_noise_next", nodes[i + 1])

    candidates = _default_candidates(native, "sd_mint_quantum")
    correct = next((c for c in candidates if c.get("label") == "dedup_identity_fix"), None)
    wrong = next((c for c in candidates if c is not correct), None)
    if correct is None or wrong is None:
        raise RuntimeError("locked correction fixture lacks correct/wrong candidates")
    return substrate, native, correct, wrong


def trial(unrelated_nodes: int, label: str, repeats: int, warmups: int) -> dict:
    times: list[float] = []
    outcomes: list[dict] = []
    graph_sizes: list[dict] = []
    for iteration in range(warmups + repeats):
        substrate, native, correct, wrong = make_fixture(unrelated_nodes)
        before = native.graph_to_dict()
        start = time.perf_counter()
        result = imagine_and_check_convergence(
            substrate, correct if label == "correct" else wrong,
            horizon=3, imagine_steps=2)
        elapsed = time.perf_counter() - start
        after = native.graph_to_dict()
        outcome = {
            "converges": bool(result["converges"]),
            "inert": bool(result["inert"]),
            "applied": result["applied"],
            "residual_before": float(result["model_before"].residual),
            "residual_after": float(result["model_after"].residual),
            "frontier_growth_before": float(result["model_before"].frontier_growth_rate),
            "frontier_growth_after": float(result["model_after"].frontier_growth_rate),
            "steps_run": result["model_after"].imagine_steps_run,
            "n_conclusions": result["imagined"].n_conclusions,
            "live_rule_count_before": native.rule_count(),
            "live_rule_count_after": native.rule_count(),
            "live_graph_counts_before": [len(before["nodes"]), len(before["edges"])],
            "live_graph_counts_after": [len(after["nodes"]), len(after["edges"])],
        }
        if iteration >= warmups:
            times.append(elapsed)
            outcomes.append(outcome)
            graph_sizes.append({"nodes": len(before["nodes"]),
                                "edges": len(before["edges"])})

    return {
        "candidate_arm": label,
        "unrelated_nodes_requested": unrelated_nodes,
        "repeats": repeats,
        "warmups": warmups,
        "elapsed": summarize(times),
        "outcomes": outcomes,
        "graph_sizes": graph_sizes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1_000, 10_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")

    native_path = Path(srs._native.__file__).resolve()
    runner_path = Path(__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentSelfCorrectionBaselineV1",
        "implementation_status": "full detached serialization copy; no CoW fork",
        "operation": "domains.self_correction.imagine_and_check_convergence",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(runner_path), "sha256": sha256(runner_path)},
        "binary": {"path": str(native_path), "sha256": sha256(native_path)},
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "controls": {
            "positive_candidate": "dedup_identity_fix",
            "negative_candidate": "first default candidate other than positive",
            "probe": "three pending shape-decode observations, horizon=3, imagine_steps=2",
            "scale_intervention": "unconnected attributed chain; does not touch correction frame",
            "timed_region": "candidate rehearsal including model-before/after, snapshot, rule import, candidate application, inference and conclusion diff; fixture build excluded",
            "historical_expected_outcomes": {"correct": True, "wrong": False},
        },
        "results": [trial(n, arm, args.repeats, args.warmups)
                    for n in args.sizes for arm in ("correct", "wrong")],
    }
    rendered = json.dumps(capture, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
