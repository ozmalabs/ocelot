#!/usr/bin/env python3
"""Independent parity and cost analysis for batched query predictions."""
from __future__ import annotations
import json, math, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_contract_query_batched_predictions_v1_raw_20261002.json"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_batched_predictions_v1_lock_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_contract_query_batched_predictions_v1_analysis_20261002.json"


def oracle(index: int, bits: int, x: int) -> int:
    for bit, point in enumerate(range(-bits, 0)):
        if x == point:
            return 10 * ((index >> bit) & 1)
    return x


def bucket(value):
    return type(value).__name__, repr(value)


def entropy(values):
    counts = {}
    for value in values:
        key = bucket(value)
        counts[key] = counts.get(key, 0) + 1
    n = len(values)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def main() -> int:
    capture = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    workers = capture["workers"]
    assert capture["lock"] == capture["post_lock"] == lock
    assert len(workers) == 18 and all(row.get("kind") == "worker" for row in workers)
    assert len({row["pid"] for row in workers}) == 18
    assert all(row["source_stable"] and row["before"] == row["after"] == lock["active"] for row in workers)
    cells = {cell["cell"]: cell for cell in lock["design"]["cells"]}
    pairs = {}
    for row in workers:
        pairs.setdefault((row["cell"], row["rep"]), {})[row["arm"]] = row
    assert len(pairs) == 9 and all(set(arms) == {"uncached", "matrix"} for arms in pairs.values())
    paired = []
    for (name, rep), arms in sorted(pairs.items()):
        cell = cells[name]
        h, bits, target = cell["H"], cell["K"], int(cell["target_id"][1:])
        baseline, matrix = arms["uncached"], arms["matrix"]
        assert baseline["history"] == matrix["history"]
        assert baseline["terminal"] == matrix["terminal"]
        assert baseline["misspecification"] == matrix["misspecification"]
        assert len(baseline["history"]) == bits
        obs = list(cell["initial"])
        for row in baseline["history"]:
            survivors = [i for i in range(h)
                         if all(oracle(i, bits, item["inputs"]["x"]) == item["expected"] for item in obs)]
            assert row["survivors_before"] == [f"h{i}" for i in survivors]
            x = row["query"]["x"]
            expected_predictions = [{"hypothesis": f"h{i}", "output": oracle(i, bits, x)} for i in survivors]
            assert row["predictions"] == expected_predictions
            scores = []
            for candidate in cell["inputs"]:
                q = candidate["x"]
                if any(item["inputs"]["x"] == q for item in obs):
                    continue
                scores.append((entropy([oracle(i, bits, q) for i in survivors]), q))
            best_score = max(score for score, _ in scores)
            best_query = min(q for score, q in scores if abs(score - best_score) < 1e-12)
            assert abs(row["entropy_bits"] - best_score) < 1e-12
            assert x == best_query
            assert row["oracle_output"] == oracle(target, bits, x)
            obs.append({"inputs": row["query"], "expected": row["oracle_output"]})
        assert baseline["terminal"]["reason"] == "fewer than two hypotheses fit existing observations"
        assert baseline["terminal"]["surviving_hypotheses"] == [cell["target_id"]]
        assert matrix["matrix_cells"] == h * len(cell["inputs"])
        assert matrix["native_evaluation_calls"] == h * (len(cell["inputs"]) + 1)
        assert matrix["matrix_approximate_bytes"] > 0
        for arm in (baseline, matrix):
            misspec = arm["misspecification"]
            assert misspec["terminal"]["surviving_hypotheses"] == [cell["target_id"]]
            assert misspec["selected_candidate"] == cell["target_id"]
            assert misspec["finite_prediction"] != misspec["oracle_heldout"]
            assert misspec["heldout_x"] not in [item["x"] for item in cell["inputs"]]
        paired.append({"cell": name, "rep": rep, "H": h, "N": len(cell["inputs"]),
                       "uncached_ms": baseline["elapsed_ns"] / 1e6,
                       "matrix_ms": matrix["elapsed_ns"] / 1e6,
                       "speedup": baseline["elapsed_ns"] / matrix["elapsed_ns"],
                       "uncached_calls": baseline["native_evaluation_calls"],
                       "matrix_calls": matrix["native_evaluation_calls"],
                       "matrix_cells": matrix["matrix_cells"],
                       "matrix_approximate_bytes": matrix["matrix_approximate_bytes"],
                       "uncached_peak_rss": baseline["peak_rss_bytes"],
                       "matrix_peak_rss": matrix["peak_rss_bytes"]})
    by_cell = {}
    for name, cell in cells.items():
        rows = [row for row in paired if row["cell"] == name]
        uncached = statistics.median(row["uncached_ms"] for row in rows)
        matrix_ms = statistics.median(row["matrix_ms"] for row in rows)
        peak_ratio = statistics.median(row["matrix_peak_rss"] / row["uncached_peak_rss"] for row in rows)
        by_cell[name] = {"median_uncached_ms": uncached, "median_matrix_ms": matrix_ms,
                         "median_speedup": uncached / matrix_ms,
                         "median_uncached_calls": statistics.median(row["uncached_calls"] for row in rows),
                         "matrix_calls": rows[0]["matrix_calls"],
                         "matrix_cells": rows[0]["matrix_cells"],
                         "median_matrix_approximate_bytes": statistics.median(row["matrix_approximate_bytes"] for row in rows),
                         "median_peak_rss_ratio": peak_ratio}
    gates = {"source_locked_18_workers": True, "paired_semantic_parity": True,
             "independent_oracle_and_entropy_checks": True, "matrix_call_accounting": True,
             "misspecification_false_singleton_preserved": True}
    gates["decision_rule_met"] = all(by_cell[name]["median_speedup"] >= 1.25
                                     and by_cell[name]["median_peak_rss_ratio"] <= 2.0
                                     for name in ("h128_n28", "h512_n36"))
    result = {"schema": "SubstrateContractQueryBatchedPredictionsV1Analysis", "workers": len(workers),
              "source_lock_stable": True, "gates": gates, "cells": by_cell, "paired_rows": paired,
              "claim_boundary": "Batched prediction matrices preserve this pure-Term finite-set selector's measured behavior; timing and memory claims apply only to these coded workloads on this host. The open-world false-singleton failure remains unchanged."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
