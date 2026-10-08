#!/usr/bin/env python3
"""Compare independent native CAN frame settlement with monolithic settlement.

This is a first cut-validity experiment, not a boundary-message scheduler:
frame workers receive intra-frame edges only. A disconnected block graph is
therefore the exact-factorization positive control; connected graph families
are cross-boundary omission controls.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "seeds/can_native_reimplementation.json"
OUT = Path(os.environ.get(
    "SUBSTRATE_CAN_FRAME_OUT",
    ROOT / "evaluation/reports/substrate_can_frame_factorization_20260924.json",
))
SIZES = tuple(int(x) for x in os.environ.get("SUBSTRATE_CAN_FRAME_SIZES", "16,32").split(","))
TOPOLOGIES = tuple(os.environ.get(
    "SUBSTRATE_CAN_FRAME_TOPOLOGIES", "blocks4,path,banded2,complete"
).split(","))
MODES = tuple(os.environ.get("SUBSTRATE_CAN_FRAME_MODES", "2state,3state").split(","))
REPLICATES = int(os.environ.get("SUBSTRATE_CAN_FRAME_REPLICATES", "3"))
FRAME_SIZE = int(os.environ.get("SUBSTRATE_CAN_FRAME_SIZE", "4"))
GRANULARITY = float(os.environ.get("SUBSTRATE_CAN_FRAME_GRANULARITY", "0.25"))
BETA = 2.0
THRESHOLD = math.atanh(0.5)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_pairs(n: int, topology: str):
    for a in range(n):
        for b in range(a + 1, n):
            if (topology == "complete"
                    or (topology == "path" and b == a + 1)
                    or (topology == "banded2" and b - a <= 2)
                    or (topology == "blocks4" and a // FRAME_SIZE == b // FRAME_SIZE)):
                yield a, b


def update(mode: str, h: float) -> float:
    if mode == "2state":
        return 1.0 if h >= 0.0 else -1.0
    scaled = BETA * h
    if scaled > THRESHOLD:
        return 1.0
    if scaled < -THRESHOLD:
        return -1.0
    return 0.0


def build_engine(sr, engine_rules_only, seed_doc, mode, fields, weights):
    n = len(fields)
    sub = sr.Substrate()
    inner = sub._inner
    inner.load_seed_manifest(engine_rules_only(seed_doc))
    mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": mode, "can_tick": 0,
    })
    concepts = [inner.add_node("Concept", {
        "name": f"c{i}", "state": 0.0,
        "external_field": fields[i], "identity_field": 0.0,
    }) for i in range(n)]
    for concept in concepts:
        inner.add_edge(mt, "has_concept", concept, {})
    for (a, b), weight in weights.items():
        inner.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": weight})
    return inner, concepts


def residuals(mode, fields, weights, states):
    out = []
    for a, state in enumerate(states):
        h = fields[a] + sum(weights.get((a, b), 0.0) * states[b]
                            for b in range(len(states)))
        out.append(update(mode, h) != state)
    return out


def main() -> None:
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    from substrate_rs import _native

    seed_doc = json.loads(SEED_FILE.read_text())
    rows = []
    started = time.perf_counter()
    for n in SIZES:
        if n % FRAME_SIZE:
            raise ValueError(f"N={n} must be divisible by frame size {FRAME_SIZE}")
        for topology in TOPOLOGIES:
            for mode in MODES:
                for replicate in range(REPLICATES):
                    seed = 20260924 + n * 1000 + replicate
                    frng = random.Random(seed * 53 + n)
                    prng = random.Random(seed * 31 + n)
                    fields = [frng.uniform(-1.0, 1.0) for _ in range(n)]
                    weights: dict[tuple[int, int], float] = {}
                    for a, b in make_pairs(n, topology):
                        w = round(prng.uniform(-1.0, 1.0) / GRANULARITY) * GRANULARITY
                        weights[a, b] = w
                        weights[b, a] = w
                    frame_ids = [i // FRAME_SIZE for i in range(n)]
                    cross_directed = sum(frame_ids[a] != frame_ids[b] for a, b in weights)

                    mono, mono_nodes = build_engine(sr, engine_rules_only, seed_doc,
                                                    mode, fields, weights)
                    mono_t0, mono_c0 = time.perf_counter_ns(), time.process_time_ns()
                    mono_steps = mono.run_rules(100_000)
                    mono_wall = time.perf_counter_ns() - mono_t0
                    mono_cpu = time.process_time_ns() - mono_c0
                    mono_states = [float(mono.node(x)["attrs"].get("state", 0.0)) for x in mono_nodes]
                    mono_terminal = mono.run_rules(1)

                    frame_engines = []
                    for begin in range(0, n, FRAME_SIZE):
                        end = begin + FRAME_SIZE
                        local_fields = fields[begin:end]
                        local_weights = {
                            (a - begin, b - begin): value
                            for (a, b), value in weights.items()
                            if begin <= a < end and begin <= b < end
                        }
                        frame_engines.append(build_engine(
                            sr, engine_rules_only, seed_doc, mode, local_fields, local_weights
                        ))
                    part_t0, part_c0 = time.perf_counter_ns(), time.process_time_ns()
                    frame_steps = []
                    part_states = [0.0] * n
                    frame_terminals = []
                    for fi, (inner, nodes) in enumerate(frame_engines):
                        steps = inner.run_rules(100_000)
                        frame_steps.append(steps)
                        begin = fi * FRAME_SIZE
                        part_states[begin:begin + FRAME_SIZE] = [
                            float(inner.node(x)["attrs"].get("state", 0.0)) for x in nodes
                        ]
                    part_wall = time.perf_counter_ns() - part_t0
                    part_cpu = time.process_time_ns() - part_c0
                    for inner, _ in frame_engines:
                        frame_terminals.append(inner.run_rules(1))

                    mono_residuals = residuals(mode, fields, weights, mono_states)
                    part_residuals = residuals(mode, fields, weights, part_states)
                    rows.append({
                        "n": n, "topology": topology, "mode": mode,
                        "replicate": replicate, "seed": seed,
                        "frame_size": FRAME_SIZE, "frame_count": n // FRAME_SIZE,
                        "directed_edges": len(weights), "cross_frame_directed_edges": cross_directed,
                        "monolithic_steps": mono_steps, "frame_steps": frame_steps,
                        "monolithic_budget_complete": mono_steps < 100_000,
                        "frames_budget_complete": all(x < 100_000 for x in frame_steps),
                        "monolithic_terminal_probe": mono_terminal,
                        "frame_terminal_probes": frame_terminals,
                        "monolithic_vs_partitioned_exact_state_match": mono_states == part_states,
                        "monolithic_independent_residuals": sum(mono_residuals),
                        "partitioned_independent_residuals_on_full_graph": sum(part_residuals),
                        "monolithic_wall_ns": mono_wall, "monolithic_cpu_ns": mono_cpu,
                        "partition_workers_sequential_wall_ns": part_wall,
                        "partition_workers_sequential_cpu_ns": part_cpu,
                        "monolithic_states": [int(x) for x in mono_states],
                        "partitioned_states": [int(x) for x in part_states],
                    })
                    print(f"N={n} {topology} {mode} rep={replicate + 1}/{REPLICATES} "
                          f"cross={cross_directed} exact={mono_states == part_states} "
                          f"residual={sum(part_residuals)}", flush=True)

    groups = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                group = [x for x in rows if (x["n"], x["topology"], x["mode"]) == (n, topology, mode)]
                groups.append({
                    "n": n, "topology": topology, "mode": mode, "replicates": len(group),
                    "cross_frame_directed_edges": group[0]["cross_frame_directed_edges"],
                    "exact_state_match_replicates": sum(x["monolithic_vs_partitioned_exact_state_match"] for x in group),
                    "partitioned_residual_free_replicates": sum(x["partitioned_independent_residuals_on_full_graph"] == 0 for x in group),
                    "median_monolithic_wall_ns": int(statistics.median(x["monolithic_wall_ns"] for x in group)),
                    "median_partition_sequential_wall_ns": int(statistics.median(x["partition_workers_sequential_wall_ns"] for x in group)),
                    "median_monolithic_cpu_ns": int(statistics.median(x["monolithic_cpu_ns"] for x in group)),
                    "median_partition_sequential_cpu_ns": int(statistics.median(x["partition_workers_sequential_cpu_ns"] for x in group)),
                })
    payload = {
        "run_id": "substrate-can-frame-factorization-20260924",
        "question": "When does independent frame-local native CAN settlement preserve monolithic outcomes?",
        "scope_limit": "Frames are independent native substrates and receive only intra-frame edges; no boundary messages or dynamic wakeups are implemented.",
        "positive_control": "blocks4 has zero cross-frame edges; exact state equivalence is expected.",
        "negative_controls": "path, banded2, complete retain cross-frame couplings in the monolith but omit them from independent frame substrates.",
        "configuration": {"sizes": SIZES, "topologies": TOPOLOGIES, "modes": MODES,
                          "replicates": REPLICATES, "frame_size": FRAME_SIZE,
                          "weight_granularity": GRANULARITY, "rule_budget_per_run": 100_000},
        "runtime": {"elapsed_seconds": time.perf_counter() - started,
                    "python": platform.python_version(), "platform": platform.platform(),
                    "processor": platform.processor()},
        "provenance": {
            "script_sha256": sha(Path(__file__).resolve()),
            "seed_manifest_sha256": sha(SEED_FILE),
            "native_extension": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "substrate_source_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
            "rewrite_source_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
            "term_source_sha256": sha(ROOT / "runners/dsl/src/term.rs"),
            "pythonpath": os.environ.get("PYTHONPATH", ""), "cwd": str(ROOT),
            "command": "PYTHONPATH=<temporary-native-package>:$PWD python3 scripts/substrate_can_frame_factorization.py",
        },
        "summaries": groups, "workers": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    positive = [x for x in rows if x["topology"] == "blocks4"]
    checks = {
        "all_runs_within_budget": all(x["monolithic_budget_complete"] and x["frames_budget_complete"] for x in rows),
        "all_monolithic_fixed_points": all(x["monolithic_terminal_probe"] == 0 and x["monolithic_independent_residuals"] == 0 for x in rows),
        "all_frames_reach_local_fixed_points": all(all(v == 0 for v in x["frame_terminal_probes"]) for x in rows),
        "block_positive_control_exact": bool(positive) and all(x["monolithic_vs_partitioned_exact_state_match"] and x["partitioned_independent_residuals_on_full_graph"] == 0 for x in positive),
    }
    print(json.dumps({"workers": len(rows), "groups": len(groups), "checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("frame factorization positive control failed")


if __name__ == "__main__":
    main()
