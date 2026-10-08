#!/usr/bin/env python3
"""Measure sparse journal readout against whole-graph diff on real inference.

Each timed branch executes a graph rule that consumes an injected hypothesis
and emits novel structure. Fresh, identical substrates keep node IDs aligned;
the full-graph readout is the exact semantic control for the journal.
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
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

import substrate_rs as srs  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402
from domains.imagination import imagine  # noqa: E402

LOCKED_SOURCES = (
    "domains/imagination.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/ext.py",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run_branch(size: int, legacy: bool) -> dict:
    sub = srs.Substrate()
    sub.add_node("Rule", {
        "id": "derive_from_hypothesis",
        "match": [["h", "contradicts", "f"], ["f", "stale", "z"]],
        "effect": [
            ["set_attr", "f", "checked", True],
            ["add_node", "c", "Conclusion", {"derived_from_hypothesis": True}],
            ["add_edge", "h", "yields", "c", {}],
            ["del_node", "z"],
        ],
    })
    fact = sub.add_node("Fact", {"value": "blue"})
    stale = sub.add_node("Stale", {})
    sub.add_edge_unchecked(fact, "stale", stale)
    previous = None
    for i in range(size):
        node = sub.add_node("Unrelated", {"ordinal": i, "payload": "x" * 24})
        if previous is not None:
            sub.add_edge_unchecked(previous, "next", node)
        previous = node
    hypothesis = {
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": fact.value}],
    }
    before = sub._inner.graph_to_dict()
    started = time.perf_counter_ns()
    result = imagine(
        sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
        steps=1, cut_grounding=False, snapshot_backend="native_full_copy_scoped",
        _force_full_graph_readout=legacy, record_trace=False,
    )
    elapsed = time.perf_counter_ns() - started
    after = sub._inner.graph_to_dict()
    return {
        "elapsed_ms": elapsed / 1_000_000,
        "steps_run": result.steps_run,
        "conclusions": result.conclusions,
        "derived_only": result.derived_only,
        "n_conclusions": result.n_conclusions,
        "converged": result.converged,
        "covers_mutation_classes": all((
            result.conclusions["nodes_added"],
            result.conclusions["nodes_changed"],
            result.conclusions["nodes_removed"],
            result.conclusions["edges_added"],
            result.conclusions["edges_removed"],
            result.derived_only["nodes_changed"],
            result.derived_only["nodes_removed"],
            result.derived_only["edges_removed"],
        )),
        "primary_graph_unchanged": before == after,
    }


def signature(row: dict) -> str:
    return json.dumps({k: row[k] for k in (
        "steps_run", "conclusions", "derived_only", "n_conclusions", "converged",
        "covers_mutation_classes", "primary_graph_unchanged",
    )}, sort_keys=True, separators=(",", ":"))


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

    cells = []
    for size in args.sizes:
        modes = {"journal": [], "whole_graph_diff": []}
        for iteration in range(args.warmups + args.repeats):
            # Alternate execution order to reduce systematic thermal/order bias.
            order = (False, True) if iteration % 2 == 0 else (True, False)
            pair = {}
            for legacy in order:
                pair["whole_graph_diff" if legacy else "journal"] = run_branch(size, legacy)
            if signature(pair["journal"]) != signature(pair["whole_graph_diff"]):
                raise SystemExit(f"exact residual parity failed at size={size}, iteration={iteration}")
            if not pair["journal"]["primary_graph_unchanged"]:
                raise SystemExit(f"primary graph mutation detected at size={size}")
            if iteration >= args.warmups:
                for mode in modes:
                    modes[mode].append(pair[mode])
        medians = {mode: statistics.median(r["elapsed_ms"] for r in rows)
                   for mode, rows in modes.items()}
        cells.append({
            "unrelated_nodes": size,
            "repeats": args.repeats,
            "warmups": args.warmups,
            "median_ms": medians,
            "journal_speedup": medians["whole_graph_diff"] / medians["journal"],
            "exact_residual_parity": True,
            "primary_graph_preserved": True,
            "nonempty_derived_output": all(
                row["n_conclusions"] > 0 and row["covers_mutation_classes"]
                for row in modes["journal"] + modes["whole_graph_diff"]
            ),
            "outcomes": modes,
        })
        if not cells[-1]["nonempty_derived_output"]:
            raise SystemExit(f"probe did not produce derived output at size={size}")

    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentDeltaJournalInferenceV1",
        "operation": "domains.imagination.imagine with one hypothesis-driven graph-rule step",
        "implementation_status": "experimental sparse touched-object journal vs legacy whole-graph snapshots and graph_diff",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "runner": {"path": str(Path(__file__).resolve()),
                   "sha256": sha256(Path(__file__).resolve())},
        "binary": {"path": str(binary), "sha256": sha256(binary)},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "sources": {name: sha256(ROOT / name) for name in LOCKED_SOURCES},
        "controls": {
            "inference": "injected Hypothesis matches one held Rule; rule adds nodes/edges, changes an attr, and deletes a node with its incident edge",
            "scale_intervention": "disconnected attributed chain outside the focus aperture",
            "timed_region": "native scoped branch, hypothesis insertion, one rule step, and exact residual readout",
            "semantic_gate": "exact equality of conclusions, derived_only, counts, steps, convergence; all five mutation classes required in conclusions and changed/deleted classes in derived_only",
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
