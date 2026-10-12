#!/usr/bin/env python3
"""Independent structural/progress audit of native termination-family capture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/mint_termination_scale_v1_1_20260926.json"
OUT = ROOT / "evaluation/reports/mint_termination_scale_v1_1_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initial_edges(n: int, topology: str) -> set[tuple[int, int]]:
    if topology == "cycle":
        return {(i, (i + 1) % n) for i in range(n)}
    return {(i, j) for i in range(n) for j in range(n) if i != j}


def main() -> int:
    raw = json.loads(RAW.read_text())
    cases = raw["cases"]
    results = []
    for case in cases:
        n, m = case["n_initial_nodes"], case["m_mint_signatures"]
        ins = initial_edges(n, case["topology"])
        tag_values = (None, True, 1, "w3")
        runtime_tags = []
        for value in tag_values[:m]:
            if not any(value == earlier for earlier in runtime_tags):
                runtime_tags.append(value)
        expected_nodes = {
            *(('Seed', json.dumps({"idx": i}, sort_keys=True)) for i in range(n)),
        }
        expected_nodes.update(('Witness', json.dumps({"tag": value}, sort_keys=True))
                              for value in runtime_tags)
        pairs = set(ins) | {(y, w) for y in range(n + len(runtime_tags))
                            for w in range(n, n + len(runtime_tags))}
        expected_edges = {(a, "link", b, "{}") for a, b in pairs}
        graph = case["actual_graph"]
        got_nodes = {(node["type"], json.dumps(node["attrs"], sort_keys=True))
                     for node in graph["nodes"]}
        got_edges = {(edge["src"], edge["type"], edge["tgt"],
                      json.dumps(edge["attrs"], sort_keys=True)) for edge in graph["edges"]}
        e0 = len(ins)
        bound = m + (n + m) ** 2 - e0
        checks = {
            "rule_program_accepted": case["analyzer"]["accepted"],
            "analyzer_unique_signature_count": case["analyzer"]["unique_mint_signatures"] == m,
            "runtime_key_equivalence_count": case["runtime_distinct_witnesses"] == len(runtime_tags),
            "analyzer_count_conservative": case["analyzer"]["unique_mint_signatures"] >= len(runtime_tags),
            "analyzer_formula_matches": case["analyzer"]["progress_steps_upper_bound"] == bound,
            "native_fixed_point": case["native_report"]["status"] == "fixed_point",
            "exact_nodes": got_nodes == expected_nodes,
            "exact_edges": got_edges == expected_edges,
            "within_fact_bound": case["native_report"]["progress_steps"] <= bound,
            "all_replicated_runner_checks_pass": case["all_checks_pass"],
        }
        results.append({"case_id": case["case_id"], "checks": checks,
                        "all_checks_pass": all(checks.values()),
                        "computed_progress_bound": bound,
                        "observed_progress": case["native_report"]["progress_steps"],
                        "passes": case["native_report"]["passes_completed"]})
    expected_ids = {f"n{n}_m{m}_{topo}_r{r}"
                    for n in (4, 16, 64) for m in (1, 2, 4)
                    for topo in ("cycle", "dense_no_self") for r in (1, 2, 3)}
    checks = {"54_expected_cases": {c["case_id"] for c in cases} == expected_ids,
              "all_native_cases_pass": all(c["all_checks_pass"] for c in results),
              "no_runner_failed_cases": not raw["failed_cases"]}
    out = {"analysis_version": 1, "run_id": raw["run_id"],
           "raw_sha256": sha(RAW), "checks": checks,
           "checks_pass": all(checks.values()), "cases": results,
           "claim_limit": raw["design"]["claim_limit"]}
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_pass": out["checks_pass"], "checks": checks,
                      "output": str(OUT)}, indent=2))
    return 0 if out["checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
