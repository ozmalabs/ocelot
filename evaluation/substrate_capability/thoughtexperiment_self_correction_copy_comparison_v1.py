#!/usr/bin/env python3
"""Matched rehearsal comparison across branch and residual-readout routes.

All backends run `imagine_and_check_convergence` on fresh copies of the same
source-locked positive/negative fixture. The scoped journal arm is compared
with the identical scoped deep-copy route using legacy whole-graph snapshot and
diff readout. Native branches are deep-copy controls, not a Rust CoW overlay.
Fixture construction is excluded; prediction, candidate application, branch
execution, and trace/readout costs are included. The runner records exact
nested forward-look residuals as well as aggregate outcomes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import platform
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
import domains.reflective_faculty as rf  # noqa: E402
from domains.self_correction import (  # noqa: E402
    _default_candidates,
    imagine_and_check_convergence,
)

LOCKED_SOURCES = (
    "domains/self_correction.py",
    "domains/collapse_model.py",
    "domains/imagination.py",
    "domains/reflective_faculty.py",
    "substrate/boot_core.py",
    "seeds/shape_decode_loop.json",
    "tests/test_self_correction.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/checker.rs",
    "runners/dsl/src/cognitive_cycle.rs",
    "runners/dsl/src/grammar.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/l2_adaptive.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/sym.rs",
    "runners/dsl/src/term.rs",
)
BACKENDS = ("serialization", "native_full_copy", "native_full_copy_scoped",
            "native_full_copy_scoped_legacy_readout")


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def make_fixture(unrelated_nodes: int):
    substrate, agent_root = boot_core()
    native = rf._native_eval2(substrate)
    rf._ensure_shape_decode_loop(substrate, native, agent_root)
    observations = []
    for i in range(3):
        obs = substrate.add_node(
            "Observation", {"signature": [[f"zzzimag{i}", "X"]],
                            "key": [f"zzzimag{i}"], "status": "pending"})
        substrate.add_edge(agent_root, "observed", obs)
        observations.append(obs)
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
        raise RuntimeError("locked fixture lacks the expected positive/negative candidates")
    return substrate, native, correct, wrong, observations


def graph_preservation(before: dict, after: dict) -> dict:
    before_nodes = {node["id"]: (node.get("type"), node.get("attrs", {}))
                    for node in before["nodes"]}
    after_nodes = {node["id"]: (node.get("type"), node.get("attrs", {}))
                   for node in after["nodes"]}
    old_nodes_unchanged = all(after_nodes.get(nid) == value
                              for nid, value in before_nodes.items())

    def edge_key(edge: dict) -> str:
        return json.dumps((edge.get("src"), edge.get("type"), edge.get("tgt"),
                           edge.get("attrs", {})), sort_keys=True)

    before_edges = Counter(edge_key(edge) for edge in before["edges"])
    after_edges = Counter(edge_key(edge) for edge in after["edges"])
    removed_old_edges = sum((before_edges - after_edges).values())
    added_types = sorted(
        after_nodes[nid][0] for nid in (after_nodes.keys() - before_nodes.keys())
    )
    return {
        "preexisting_nodes_unchanged": old_nodes_unchanged,
        "preexisting_edge_instances_preserved": removed_old_edges == 0,
        "removed_preexisting_edge_instances": removed_old_edges,
        "trace_node_types_added": added_types,
        "all_added_nodes_are_durable_trace": all(
            type_ in {"CollapseModel", "Imagination", "ImaginedConclusion"}
            for type_ in added_types
        ),
    }


def run_cell(size: int, arm: str, backend: str, repeats: int, warmups: int) -> dict:
    elapsed_ms = []
    outcomes = []
    for iteration in range(warmups + repeats):
        substrate, native, correct, wrong, observations = make_fixture(size)
        before = native.graph_to_dict()
        rules_before = json.dumps(native.export_rules(), sort_keys=True, default=str)
        start = time.perf_counter_ns()
        legacy_readout = backend == "native_full_copy_scoped_legacy_readout"
        snapshot_backend = "native_full_copy_scoped" if legacy_readout else backend
        result = imagine_and_check_convergence(
            substrate, correct if arm == "correct" else wrong,
            horizon=3, imagine_steps=2, experiment_focus_nodes=observations,
            focus_hops=1, snapshot_backend=snapshot_backend,
            _force_full_graph_readout=legacy_readout,
        )
        duration_ns = time.perf_counter_ns() - start
        after = native.graph_to_dict()
        rules_after = json.dumps(native.export_rules(), sort_keys=True, default=str)
        preservation = graph_preservation(before, after)
        preservation["primary_rewrite_rules_unchanged"] = rules_before == rules_after
        row = {
            "trial_wall_ms": duration_ns / 1_000_000,
            "converges": bool(result["converges"]),
            "inert": bool(result["inert"]),
            "applied": result["applied"],
            "residual_before": float(result["model_before"].residual),
            "residual_after": float(result["model_after"].residual),
            "frontier_growth_before": float(result["model_before"].frontier_growth_rate),
            "frontier_growth_after": float(result["model_after"].frontier_growth_rate),
            "steps_run": result["model_after"].imagine_steps_run,
            "n_conclusions": result["imagined"].n_conclusions,
            "conclusions": result["imagined"].conclusions,
            "derived_only": result["imagined"].derived_only,
            "forward_look_deltas_before": result["model_before"].forward_look_deltas,
            "forward_look_deltas_after": result["model_after"].forward_look_deltas,
            "primary_counts_before": [len(before["nodes"]), len(before["edges"])],
            "primary_counts_after": [len(after["nodes"]), len(after["edges"])],
            "primary_rule_count_before": native.rule_count(),
            "primary_rule_count_after": native.rule_count(),
            "primary_preservation": preservation,
        }
        if iteration >= warmups:
            elapsed_ms.append(duration_ns / 1_000_000)
            outcomes.append(row)
    return {
        "unrelated_nodes_requested": size,
        "candidate_arm": arm,
        "snapshot_backend": backend,
        "repeats": repeats,
        "warmups": warmups,
        "median_ms": statistics.median(elapsed_ms),
        "min_ms": min(elapsed_ms),
        "max_ms": max(elapsed_ms),
        "outcomes": outcomes,
    }


def outcome_signature(row: dict) -> tuple:
    fields = (
        "converges", "inert", "applied", "residual_before", "residual_after",
        "frontier_growth_before", "frontier_growth_after", "steps_run",
        "n_conclusions", "primary_counts_before", "primary_counts_after",
        "conclusions", "derived_only", "forward_look_deltas_before",
        "forward_look_deltas_after",
            "primary_rule_count_before", "primary_rule_count_after",
            "primary_preservation",
    )
    normalized = []
    for field in fields:
        value = row[field]
        if field == "applied":
            # The fixture intentionally salts installed candidate rule names;
            # compare their semantic base labels, not per-run UUID suffixes.
            value = {
                name: re.sub(r"_(?:scfix|scguard)_[0-9a-f]{8}$", "", result)
                if isinstance(result, str) else result
                for name, result in value.items()
            }
        normalized.append(json.dumps(value, sort_keys=True))
    return tuple(normalized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 1000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(n < 0 for n in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")

    rows = [run_cell(size, arm, backend, args.repeats, args.warmups)
            for size in args.sizes
            for arm in ("correct", "wrong")
            for backend in BACKENDS]
    by_key = {(r["unrelated_nodes_requested"], r["candidate_arm"], r["snapshot_backend"]): r
              for r in rows}
    parity = []
    for size in args.sizes:
        for arm in ("correct", "wrong"):
            serial = by_key[(size, arm, "serialization")]["outcomes"]
            native = by_key[(size, arm, "native_full_copy")]["outcomes"]
            scoped = by_key[(size, arm, "native_full_copy_scoped")]["outcomes"]
            legacy = by_key[(size, arm, "native_full_copy_scoped_legacy_readout")]["outcomes"]
            matched = all(len(serial) == len(other) and all(
                outcome_signature(a) == outcome_signature(b)
                for a, b in zip(serial, other)
            ) for other in (native, scoped, legacy))
            expected = arm == "correct"
            expected_outcomes = all(r["converges"] is expected for r in serial + native + scoped + legacy)
            primary_preserved = all(
                r["primary_preservation"]["preexisting_nodes_unchanged"]
                and r["primary_preservation"]["preexisting_edge_instances_preserved"]
                and r["primary_preservation"]["all_added_nodes_are_durable_trace"]
                and r["primary_preservation"]["primary_rewrite_rules_unchanged"]
                for r in serial + native + scoped + legacy
            )
            if not (matched and expected_outcomes and primary_preserved):
                raise SystemExit(f"semantic parity gate failed for size={size}, arm={arm}")
            parity.append({"size": size, "arm": arm, "matched_repeats": len(serial),
                           "exact_outcome_parity": True,
                           "primary_graph_and_rule_store_preserved": True,
                           "expected_control_outcome": expected})

    native_path = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentSelfCorrectionCopyComparisonV1",
        "implementation_status": "serialization_and_legacy_diff_baselines; scoped_sparse_journal_and_native_deep_copy_controls; no_native_CoW",
        "operation": "domains.self_correction.imagine_and_check_convergence",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "binary": {"path": str(native_path), "sha256": sha256(native_path)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "controls": {
            "positive_candidate": "dedup_identity_fix",
            "negative_candidate": "first default candidate other than positive",
            "probe": "three pending shape-decode observations, horizon=3, imagine_steps=2",
            "scale_intervention": "unconnected attributed chain; does not touch correction frame",
            "timed_region": "matched model-before, branch creation, candidate application, prediction, and trace/readout; fixture construction excluded",
            "native_full_copy": "deep native copy; derived caches reset; external or wrapper-owned active state refused",
            "native_full_copy_scoped": "deep native copy plus sparse frame-local edge-read indexes; full node identity space retained",
            "native_full_copy_scoped_legacy_readout": "same scoped deep-copy route with legacy whole-graph snapshots and graph_diff readout",
            "native_full_copy_scoped": "same scoped deep-copy route with sparse Rust mutation-journal residual readout",
            "nested_residual_gate": "exact per-round conclusions and derived_only residuals recorded for both baseline and candidate forward looks",
            "frame_aperture": "three Observation nodes plus one-hop edge closure; identical focus applied to all snapshot backends",
        },
        "semantic_parity": parity,
        "results": rows,
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
