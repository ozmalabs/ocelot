#!/usr/bin/env python3
"""Paired ablation of zero-step candidate-base graph readout."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(EVAL)]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.self_correction import imagine_and_check_convergence  # noqa: E402
import thoughtexperiment_self_correction_copy_comparison_v1 as controls  # noqa: E402

SOURCES = (
    "domains/self_correction.py", "domains/imagination.py",
    "domains/collapse_model.py", "domains/reflective_faculty.py",
    "substrate/boot_core.py", "seeds/shape_decode_loop.json",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_applied(applied: dict) -> dict:
    return {name: re.sub(r"_(?:scfix|scguard)_[0-9a-f]{8}$", "", value)
            if isinstance(value, str) else value
            for name, value in applied.items()}


def trial(size: int, arm: str, mode: str) -> dict:
    sub, native, correct, wrong, observations = controls.make_fixture(size)
    candidate = correct if arm == "correct" else wrong
    before = native.graph_to_dict()
    rules_before = json.dumps(native.export_rules(), sort_keys=True, default=str)
    start = time.perf_counter_ns()
    result = imagine_and_check_convergence(
        sub, candidate, horizon=3, imagine_steps=2,
        experiment_focus_nodes=observations, focus_hops=1,
        snapshot_backend="native_full_copy_scoped",
        _force_full_noop_readout=(mode == "full_noop_readout"),
    )
    elapsed = (time.perf_counter_ns() - start) / 1_000_000
    after = native.graph_to_dict()
    rules_after = json.dumps(native.export_rules(), sort_keys=True, default=str)
    preservation = controls.graph_preservation(before, after)
    preservation["primary_rewrite_rules_unchanged"] = rules_before == rules_after
    return {
        "elapsed_ms": elapsed,
        "converges": bool(result["converges"]),
        "inert": bool(result["inert"]),
        "applied": normalize_applied(result["applied"]),
        "model_before": [result["model_before"].converged,
                         result["model_before"].residual,
                         result["model_before"].frontier_growth_rate],
        "model_after": [result["model_after"].converged,
                        result["model_after"].residual,
                        result["model_after"].frontier_growth_rate,
                        result["model_after"].imagine_steps_run],
        "conclusions": result["imagined"].conclusions,
        "derived_only": result["imagined"].derived_only,
        "primary_unchanged": (preservation["preexisting_nodes_unchanged"]
                               and preservation["preexisting_edge_instances_preserved"]
                               and preservation["all_added_nodes_are_durable_trace"]
                               and preservation["primary_rewrite_rules_unchanged"]),
        "graph_counts": [len(before["nodes"]), len(before["edges"])],
    }


def signature(row: dict) -> str:
    return json.dumps({k: v for k, v in row.items() if k not in {"elapsed_ms", "mode"}},
                      sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--order-seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path, default=ROOT /
                        "evaluation/reports/thoughtexperiment_noop_readout_ablation_v1.json")
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or min(args.sizes) < 0:
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine: {stale}")

    rng = random.Random(args.order_seed)
    comparisons, schedule = [], []
    all_rows = []
    for size in args.sizes:
        for arm in ("correct", "wrong"):
            for mode in ("fast_noop", "full_noop_readout"):
                for _ in range(args.warmups):
                    trial(size, arm, mode)
            rows = {mode: [] for mode in ("fast_noop", "full_noop_readout")}
            for repeat in range(args.repeats):
                block = list(rows)
                rng.shuffle(block)
                for mode in block:
                    row = trial(size, arm, mode)
                    row.update(size=size, candidate_arm=arm, mode=mode, repeat=repeat)
                    rows[mode].append(row)
                    all_rows.append(row)
                    schedule.append({"size": size, "candidate_arm": arm,
                                     "repeat": repeat, "mode": mode})
            exact = all(signature(a) == signature(b)
                        for a, b in zip(rows["fast_noop"], rows["full_noop_readout"]))
            isolation = all(r["primary_unchanged"] for mode_rows in rows.values()
                            for r in mode_rows)
            expected = all(r["converges"] is (arm == "correct")
                           for mode_rows in rows.values() for r in mode_rows)
            if not (exact and isolation and expected):
                mismatches = []
                for a, b in zip(rows["fast_noop"], rows["full_noop_readout"]):
                    mismatches.extend(k for k in a if k != "elapsed_ms" and a[k] != b[k])
                raise SystemExit(f"ablation parity/isolation gate failed size={size} arm={arm}: "
                                 f"exact={exact} isolation={isolation} expected={expected} "
                                 f"mismatches={sorted(set(mismatches))}")
            fast = statistics.median(r["elapsed_ms"] for r in rows["fast_noop"])
            full = statistics.median(r["elapsed_ms"] for r in rows["full_noop_readout"])
            comparisons.append({"size": size, "candidate_arm": arm,
                                "exact_result_parity": exact,
                                "primary_graph_and_rules_unchanged": isolation,
                                "expected_control_outcome": expected,
                                "fast_noop_median_ms": fast,
                                "full_noop_readout_median_ms": full,
                                "speedup": full / fast,
                                "fast_noop_trials": rows["fast_noop"],
                                "full_noop_readout_trials": rows["full_noop_readout"]})

    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentNoopReadoutAblationV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha(binary)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha(ROOT / name) for name in SOURCES},
        "protocol": {"branch_backend": "native_full_copy_scoped",
                    "contrast": "zero-step, no-hypothesis candidate-base imagination either elides or executes the legacy whole-graph snapshot/diff readout",
                    "focus": "three volatile observations plus one-hop aperture",
                    "timed_region": "baseline prediction plus candidate application and rehearsal; fixture build excluded",
                    "order": "seeded randomized paired complete blocks per size and candidate"},
        "order_seed": args.order_seed,
        "comparison_order": schedule,
        "comparisons": comparisons,
        "rows": all_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(capture, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "comparisons": [
        {"size": r["size"], "arm": r["candidate_arm"],
         "fast_ms": round(r["fast_noop_median_ms"], 1),
         "full_ms": round(r["full_noop_readout_median_ms"], 1),
         "speedup": round(r["speedup"], 3)} for r in comparisons]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
