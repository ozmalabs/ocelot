#!/usr/bin/env python3
"""Exercise invalidation when term-read edge resources change.

The cases cover a typed term-edge insertion, deletion, and an edge type used
both as a match driver and in a term. Each reader writes a computed edge count
to an attribute and is compared with a direct count from the final graph.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_term_edge_wakeup_20260924.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name: str, setup) -> dict:
    from substrate_rs import Substrate

    substrate, source, target, reader_idx, writer_idx, counted_edge_type = setup(Substrate())
    access_sets = substrate._inner.rule_access_sets()
    reader_access = next(row for row in access_sets if row[0] == reader_idx)
    writer_access = next(row for row in access_sets if row[0] == writer_idx)
    progress = substrate._inner.run_rules(30)
    observed = substrate.node(target)["attrs"].get("observed_count")
    oracle = len(substrate._inner.neighbours(source, counted_edge_type))
    return {
        "case": name,
        "reader_rule": reader_access[1],
        "writer_rule": writer_access[1],
        "reader_match_edge_types": [e[1] for e in substrate._inner.export_rules()[reader_idx]["match"]],
        "reader_term_edge_reads": reader_access[4],
        "writer_edge_writes": writer_access[5],
        "rule_access_sets": [list(row) for row in access_sets],
        "progress_count": progress,
        "counted_edge_type": counted_edge_type,
        "final_edge_count_oracle": oracle,
        "reader_observed_count": observed,
        "settled_correctly": observed == oracle,
    }


def make_rule_pair(substrate, case_name: str, read_edge_type: str,
                   reader_match_type: str, writer_match_type: str,
                   writer_op: str, initial_edge: bool = False):
    source = substrate.add_node("WakeupProbe", {})
    target = substrate.add_node("WakeupProbe", {})
    substrate.add_edge_unchecked(source, reader_match_type, target)
    substrate.add_edge_unchecked(source, writer_match_type, target)
    if initial_edge:
        substrate.add_edge_unchecked(source, read_edge_type, target)
    var_x = {"type": "Var", "name": "x"}
    count = {"type": "Count", "source": {
        "type": "Edges", "node": var_x, "edge_type": read_edge_type}}
    reader_idx = substrate._inner.add_rule({
        "name": f"tractability_{case_name}_reader",
        "match": [["x", reader_match_type, "y"]],
        "effects": [["set_attr", "y", "observed_count", {"__term__": count}]],
    })
    writer_idx = substrate._inner.add_rule({
        "name": f"tractability_{case_name}_writer",
        "match": [["x", writer_match_type, "y"]],
        "effects": [[writer_op, "x", read_edge_type, "y"]],
    })
    return substrate, source, target, reader_idx, writer_idx, read_edge_type


def make_overlapping_case(substrate):
    source = substrate.add_node("WakeupProbe", {})
    old_target = substrate.add_node("WakeupProbe", {})
    new_target = substrate.add_node("WakeupProbe", {})
    substrate.add_edge_unchecked(source, "trigger", old_target)
    substrate.add_edge_unchecked(source, "seed", new_target)
    var_x = {"type": "Var", "name": "x"}
    count = {"type": "Count", "source": {
        "type": "Edges", "node": var_x, "edge_type": "trigger"}}
    reader_idx = substrate._inner.add_rule({
        "name": "tractability_overlap_reader",
        "match": [["x", "trigger", "y"]],
        "effects": [["set_attr", "y", "observed_count", {"__term__": count}]],
    })
    writer_idx = substrate._inner.add_rule({
        "name": "tractability_overlap_writer",
        "match": [["x", "seed", "z"]],
        "effects": [["add_edge", "x", "trigger", "z"]],
    })
    # Inspect the old binding's output: it must be refreshed from 1 to 2 even
    # though the newly-added trigger edge also creates a second reader binding.
    return substrate, source, old_target, reader_idx, writer_idx, "trigger"


def main() -> None:
    from substrate_rs import Substrate, _native

    cases = [
        run_case("typed_edge_insert", lambda s: make_rule_pair(
            s, "insert", "causal", "trigger", "trigger", "add_edge")),
        run_case("typed_edge_delete", lambda s: make_rule_pair(
            s, "delete", "causal", "trigger", "trigger", "del_edge", initial_edge=True)),
        run_case("match_and_term_edge_overlap", make_overlapping_case),
    ]
    all_correct = all(case["settled_correctly"] for case in cases)

    result = {
        "run_state": "exploratory_pilot",
        "protocol": "term-edge wakeup diagnostic v2",
        "command": "PYTHONPATH=<fresh-native-package>:. python3 scripts/substrate_term_edge_wakeup_pilot.py",
        "commit": __import__("subprocess").check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": __import__("subprocess").check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True).strip() != "",
        "python": sys.version,
        "platform": platform.platform(),
        "native_extension_path": str(Path(_native.__file__).resolve()),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "harness_sha256": sha(Path(__file__)),
        "source_sha256": {
            "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
            "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
            "binding": sha(ROOT / "runners/dsl/src/py.rs"),
        },
        "cases": cases,
        "settled_all_correctly": all_correct,
        "claim_boundary": [
            "Three deterministic two-rule cases only; no broad closure or scale claim.",
            "Each reference is a direct count of final typed neighbours.",
            "These cover typed Edges insertion, deletion, and match/term edge-type overlap, not every term/effect or execution mode.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "settled_all_correctly": all_correct,
        "cases": [{k: c[k] for k in ("case", "progress_count", "final_edge_count_oracle", "reader_observed_count", "settled_correctly")} for c in cases],
    }, indent=2))
    if not all_correct:
        raise SystemExit("a term-edge reader did not settle to the independent edge-count oracle")


if __name__ == "__main__":
    main()
