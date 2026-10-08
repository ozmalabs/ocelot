#!/usr/bin/env python3
"""Engineering audit of TermArena rollback on malformed scratch operations."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runners/dsl/src/py.rs"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
LOCK = ROOT / "evaluation/substrate_capability/term_arena_failure_rollback_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_term_arena_failure_rollback_20260925.json"
REPLICATES = 3
ATTEMPTS = 100
GOOD = {"type": "Lit", "value": 0}
BAD_PARTIAL = {
    "type": "Eq",
    "a": {"type": "Lit", "value": 1},
    "b": {"type": "UnknownTemporaryTerm"},
}
VALID_REFLECTED = {
    "type": "Eq",
    "a": {"type": "Lit", "value": 1},
    "b": {"type": "Lit", "value": 2},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    return {
        "runner_sha256": sha(Path(__file__)),
        "py_binding_source_sha256": sha(SOURCE),
        "native_sha256": sha(NATIVE),
        "replicates": REPLICATES,
        "attempts_per_case": ATTEMPTS,
        "malformed_partial_term_json": BAD_PARTIAL,
        "valid_reflected_term_json": VALID_REFLECTED,
    }


def call_failure(substrate, name: str, thunk) -> dict:
    before = substrate._inner.term_arena_len()
    failures = 0
    for _ in range(ATTEMPTS):
        try:
            thunk()
        except (ValueError, TypeError):
            failures += 1
    after = substrate._inner.term_arena_len()
    return {
        "case": name,
        "attempts": ATTEMPTS,
        "expected_failures": failures,
        "arena_before": before,
        "arena_after": after,
        "arena_delta": after - before,
    }


def one_run() -> dict:
    sys.path.insert(0, str(ROOT / "runners/dsl/python"))
    from substrate_rs import NodeID, Substrate

    s = Substrate()
    cases = [
        call_failure(s, "evaluate_parse_error", lambda: s._inner.evaluate(BAD_PARTIAL, None)),
        call_failure(
            s,
            "evaluate_env_conversion_error",
            lambda: s._inner.evaluate(GOOD, {1: "non-string variable name"}),
        ),
        call_failure(
            s,
            "relax_parse_error",
            lambda: s._inner.relax_to_fixpoint(BAD_PARTIAL, [], "register", 1),
        ),
        call_failure(
            s,
            "search_later_term_parse_error",
            lambda: s._inner.search(GOOD, BAD_PARTIAL, "assign", None, None, None, None),
        ),
        call_failure(s, "define_concept_parse_error", lambda: s._inner.define_concept("bad", BAD_PARTIAL)),
        call_failure(s, "add_term_subgraph_parse_error", lambda: s._inner.add_term_subgraph(BAD_PARTIAL)),
    ]

    root = s._inner.add_term_subgraph(VALID_REFLECTED)
    removed = s._inner.remove_edge(root, "child.b", NodeID(1))
    cases.append(
        call_failure(
            s,
            "term_subgraph_json_partial_read_error",
            lambda: s._inner.term_subgraph_json(root),
        )
    )
    cases[-1]["malformed_edge_removed"] = bool(removed)
    return {"cases": cases}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": locked_inputs()}, indent=2, sort_keys=True))
        return
    lock = json.loads(LOCK.read_text())
    current = locked_inputs()
    if lock.get("locked_inputs") != current:
        raise SystemExit("locked inputs changed")
    runs = [one_run() for _ in range(REPLICATES)]
    cases = [case for run in runs for case in run["cases"]]
    checks = {
        "all_cases_raise_as_expected": all(c["expected_failures"] == c["attempts"] for c in cases),
        "all_failed_paths_preserve_arena_length": all(c["arena_delta"] == 0 for c in cases),
        "malformed_reflected_graph_created": all(
            next(c for c in run["cases"] if c["case"] == "term_subgraph_json_partial_read_error")["malformed_edge_removed"]
            for run in runs
        ),
        "case_matrix_complete": len(cases) == REPLICATES * 7,
    }
    summaries = []
    for i in range(7):
        observations = [run["cases"][i]["arena_delta"] for run in runs]
        summaries.append({
            "case": runs[0]["cases"][i]["case"],
            "replicates": REPLICATES,
            "arena_delta_median": int(statistics.median(observations)),
            "arena_delta_range": [min(observations), max(observations)],
        })
    report = {
        "schema_version": 1,
        "run_id": "term-arena-failure-rollback-postfix-20260925",
        "evidence_class": "post-change engineering verification; not preregistered performance evidence",
        "locked_inputs": current,
        "checks": checks,
        "case_summaries": summaries,
        "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("TermArena failure-path audit failed; report preserved")


if __name__ == "__main__":
    main()
