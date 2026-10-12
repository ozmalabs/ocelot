#!/usr/bin/env python3
"""Measure a broader bounded self-correction candidate panel.

Every generated variant runs on a fresh, matched positive/negative fixture
through sparse-journal and legacy whole-graph residual readout. Nested
forward-look residuals, primary-state isolation, useful outcome, and cost are
captured per candidate so additional search breadth is priced explicitly.
"""
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
    "domains/reflective_faculty.py",
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
EXPECTED = {"dedup_identity_fix": True, "add_match_guard(control)": False}


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run_trial(size: int, label: str, backend: str) -> dict:
    substrate, native, _correct, _wrong, observations = controls.make_fixture(size)
    candidates = _default_candidates(native, "sd_mint_quantum")
    matches = [candidate for candidate in candidates if candidate.get("label") == label]
    if len(matches) != 1:
        raise RuntimeError(f"expected one candidate {label!r}, found {len(matches)}")
    candidate = matches[0]
    before = native.graph_to_dict()
    rules_before = json.dumps(native.export_rules(), sort_keys=True, default=str)
    legacy = backend == "legacy_whole_graph_diff"
    started = time.perf_counter_ns()
    result = imagine_and_check_convergence(
        substrate, candidate, horizon=3, imagine_steps=2,
        experiment_focus_nodes=observations, focus_hops=1,
        snapshot_backend="native_full_copy_scoped",
        _force_full_graph_readout=legacy,
    )
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    after = native.graph_to_dict()
    rules_after = json.dumps(native.export_rules(), sort_keys=True, default=str)
    preservation = controls.graph_preservation(before, after)
    preservation["primary_rewrite_rules_unchanged"] = rules_before == rules_after
    return {
        "elapsed_ms": elapsed_ms,
        "candidate_label": label,
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


def semantic_signature(row: dict) -> str:
    fields = (
        "candidate_label", "converges", "inert", "applied_target_count",
        "residual_before", "residual_after", "frontier_growth_before",
        "frontier_growth_after", "steps_run", "conclusions", "derived_only",
        "forward_look_deltas_before", "forward_look_deltas_after",
        "primary_counts_before", "primary_counts_after", "primary_preservation",
    )
    return json.dumps({key: row[key] for key in fields}, sort_keys=True,
                      separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[0, 10000])
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.warmups < 0 or any(size < 0 for size in args.sizes):
        parser.error("repeats must be positive; warmups and sizes must be nonnegative")
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"stale native engine; rebuild before measuring: {stale}")

    probe_sub, probe_native, _positive, _negative, _obs = controls.make_fixture(0)
    candidate_labels = [c["label"] for c in _default_candidates(probe_native, "sd_mint_quantum")]
    if len(candidate_labels) != len(set(candidate_labels)):
        raise SystemExit("candidate labels are not unique")
    if not set(EXPECTED).issubset(candidate_labels):
        raise SystemExit(f"positive/negative controls missing: {candidate_labels}")

    rng = random.Random(args.seed)
    cells = []
    all_rows = []
    for size in args.sizes:
        for label in candidate_labels:
            by_backend = {backend: [] for backend in BACKENDS}
            for iteration in range(args.warmups + args.repeats):
                order = list(BACKENDS)
                if rng.randrange(2):
                    order.reverse()
                pair = {backend: run_trial(size, label, backend) for backend in order}
                if semantic_signature(pair[BACKENDS[0]]) != semantic_signature(pair[BACKENDS[1]]):
                    raise SystemExit(f"exact nested residual parity failed: size={size}, candidate={label}")
                for backend in BACKENDS:
                    row = pair[backend]
                    if row["inert"] or row["applied_target_count"] < 1:
                        raise SystemExit(f"candidate was not applied: size={size}, candidate={label}, backend={backend}")
                    if not (row["primary_preservation"]["preexisting_nodes_unchanged"]
                            and row["primary_preservation"]["preexisting_edge_instances_preserved"]
                            and row["primary_preservation"]["all_added_nodes_are_durable_trace"]
                            and row["primary_preservation"]["primary_rewrite_rules_unchanged"]):
                        raise SystemExit(f"primary-state isolation failed: size={size}, candidate={label}")
                    if iteration >= args.warmups:
                        by_backend[backend].append(row)
                        all_rows.append({"size": size, "backend": backend, **row})
            positive_expected = EXPECTED.get(label)
            if positive_expected is not None:
                if not all(row["converges"] is positive_expected
                           for rows in by_backend.values() for row in rows):
                    raise SystemExit(f"designated control outcome failed: {label}, size={size}")
            medians = {backend: statistics.median(row["elapsed_ms"] for row in rows)
                       for backend, rows in by_backend.items()}
            journal_speedup = medians["legacy_whole_graph_diff"] / medians["journal"]
            useful = sum(row["converges"] and not row["inert"]
                         for rows in by_backend.values() for row in rows) // 2
            cells.append({
                "size": size,
                "candidate_label": label,
                "repeats": args.repeats,
                "warmups": args.warmups,
                "median_ms": medians,
                "journal_speedup_vs_legacy_diff": journal_speedup,
                "exact_nested_residual_parity": True,
                "primary_state_preserved": True,
                "useful_converging_repeats": useful,
                "candidate_applied": True,
            })

    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentCandidateDiversityV1",
        "implementation_status": "bounded_swap_term_leaf_variants added; exact nested residual parity measured against whole-graph diff",
        "operation": "domains.self_correction.imagine_and_check_convergence over every default candidate for sd_mint_quantum",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha256(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha256(binary)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "protocol": {
            "candidate_labels": candidate_labels,
            "candidate_count": len(candidate_labels),
            "candidate_generation_cap": 4,
            "positive_control": "dedup_identity_fix must converge",
            "negative_control": "add_match_guard(control) must remain divergent",
            "timed_region": "baseline prediction, branch application, candidate prediction, and trace/readout; fixture construction excluded",
            "semantic_gate": "exact conclusions, derived_only, every nested forward-look residual, model outcomes, and primary state across journal/legacy routes",
            "order_seed": args.seed,
        },
        "results": cells,
        "outcomes": all_rows,
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
