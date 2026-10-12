#!/usr/bin/env python3
"""Independent exactness, call-count, and crossover analysis."""
from __future__ import annotations
import json, math, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_contract_query_lazy_matrix_crossover_v1_raw_20261002.json"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_lazy_matrix_crossover_v1_lock_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_contract_query_lazy_matrix_crossover_v1_analysis_20261002.json"


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
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def survivors(ids, bits, observations):
    return [index for index in ids if all(oracle(index, bits, row["inputs"]["x"]) == row["expected"]
                                         and type(oracle(index, bits, row["inputs"]["x"])) is type(row["expected"])
                                         for row in observations)]


def expected_uncached_calls(case, history):
    h, bits, n = case["H"], case["K"], case["N"]
    ids = list(range(h))
    observations = list(case["initial_observations"])
    total = 0
    for query in history:
        remaining = list(ids)
        for row in observations:
            # Each observation scans the then-current survivor set.
            total += len(remaining)
            remaining = [i for i in remaining if type(oracle(i, bits, row["inputs"]["x"])) is type(row["expected"])
                         and oracle(i, bits, row["inputs"]["x"]) == row["expected"]]
        assert len(remaining) >= 2
        unused = [row for row in case["candidate_inputs"]
                  if not any(obs["inputs"] == row for obs in observations)]
        total += len(remaining) * len(unused)
        observations.append({"inputs": query["query"], "expected": query["oracle_output"]})
    remaining = list(ids)
    for row in observations:
        total += len(remaining)
        remaining = [i for i in remaining if type(oracle(i, bits, row["inputs"]["x"])) is type(row["expected"])
                     and oracle(i, bits, row["inputs"]["x"]) == row["expected"]]
    return total


def main() -> int:
    capture, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    workers = capture["workers"]
    assert capture["lock"] == capture["post_lock"] == lock
    assert len(workers) == 36 and all(row.get("kind") == "worker" for row in workers)
    assert len({row["pid"] for row in workers}) == 36
    assert all(row["source_stable"] and row["before"] == row["after"] == lock["active"] for row in workers)
    cases = {case["name"]: case for case in lock["design"]["cases"]}
    pairs = {}
    for row in workers:
        pairs.setdefault((row["case"], row["rep"]), {})[row["arm"]] = row
    assert len(pairs) == 18 and all(set(arms) == {"uncached", "lazy_matrix"} for arms in pairs.values())
    paired = []
    for (name, rep), arms in sorted(pairs.items()):
        case = cases[name]
        uncached, matrix = arms["uncached"], arms["lazy_matrix"]
        assert uncached["main"] == matrix["main"]
        assert uncached["misspecification"] == matrix["misspecification"]
        h, bits, m, target = case["H"], case["K"], case["m"], int(case["target_id"][1:])
        assert len(uncached["main"]["history"]) == bits - m
        assert uncached["main"]["terminal"]["reason"] == "fewer than two hypotheses fit existing observations"
        assert uncached["main"]["terminal"]["surviving_hypotheses"] == [case["target_id"]]
        initial_survivors = survivors(list(range(h)), bits, case["initial_observations"])
        assert len(initial_survivors) == h // (2 ** m)
        observations = list(case["initial_observations"])
        for row in uncached["main"]["history"]:
            current = survivors(list(range(h)), bits, observations)
            assert row["survivors_before"] == [f"h{i}" for i in current]
            x = row["query"]["x"]
            assert row["predictions"] == [{"hypothesis": f"h{i}", "output": oracle(i, bits, x)} for i in current]
            scores = []
            for candidate in case["candidate_inputs"]:
                if any(old["inputs"] == candidate for old in observations):
                    continue
                scores.append((entropy([oracle(i, bits, candidate["x"]) for i in current]), candidate))
            best_score = max(score for score, _ in scores)
            best = next(candidate for score, candidate in scores if abs(score - best_score) < 1e-12)
            assert row["query"] == best and abs(row["entropy_bits"] - best_score) < 1e-12
            assert row["oracle_output"] == oracle(target, bits, x)
            observations.append({"inputs": row["query"], "expected": row["oracle_output"]})
        assert uncached["main_calls"] == expected_uncached_calls(case, uncached["main"]["history"])
        assert matrix["main_calls"] == matrix["matrix_cells"]
        assert matrix["matrix_cells"] <= h * (case["N"] + len(case["initial_observations"]))
        if m == bits:
            expected_obs_cells = h + sum(h // (2 ** j) for j in range(m))
            assert matrix["matrix_cells"] == expected_obs_cells
        misspec = uncached["misspecification"]
        assert misspec["history"] == uncached["main"]["history"]
        assert misspec["terminal"]["surviving_hypotheses"] == [case["target_id"]]
        assert uncached["heldout"]["finite_prediction"] != uncached["heldout"]["oracle_output"]
        if matrix["misspecification_calls"] != 0:
            raise AssertionError("matrix did not reuse the completed prediction sequence for misspec control")
        paired.append({"case": name, "rep": rep, "H": h, "N": case["N"], "m": m,
                       "initial_survivors": len(initial_survivors), "query_depth": bits - m,
                       "uncached_ms": uncached["elapsed_ns"] / 1e6,
                       "matrix_ms": matrix["elapsed_ns"] / 1e6,
                       "speedup": uncached["elapsed_ns"] / matrix["elapsed_ns"],
                       "uncached_calls": uncached["main_calls"], "matrix_calls": matrix["main_calls"],
                       "matrix_cells": matrix["matrix_cells"], "matrix_bytes_approx": matrix["matrix_bytes_approx"],
                       "uncached_peak_rss": uncached["peak_rss_bytes"], "matrix_peak_rss": matrix["peak_rss_bytes"]})
    by_case = {}
    for name, case in cases.items():
        rows = [row for row in paired if row["case"] == name]
        by_case[name] = {"H": case["H"], "m": case["m"], "initial_survivors": rows[0]["initial_survivors"],
                         "query_depth": rows[0]["query_depth"],
                         "median_uncached_ms": statistics.median(row["uncached_ms"] for row in rows),
                         "median_matrix_ms": statistics.median(row["matrix_ms"] for row in rows),
                         "median_speedup": statistics.median(row["speedup"] for row in rows),
                         "median_uncached_calls": statistics.median(row["uncached_calls"] for row in rows),
                         "matrix_calls": rows[0]["matrix_calls"],
                         "median_peak_rss_ratio": statistics.median(row["matrix_peak_rss"] / row["uncached_peak_rss"] for row in rows),
                         "matrix_bytes_approx": rows[0]["matrix_bytes_approx"]}
    gates = {"locked_36_workers": True, "paired_semantic_parity": True,
             "independent_entropy_and_oracle": True, "initial_survivor_fraction_exact": True,
             "matrix_call_and_cell_accounting": True, "misspecification_control_parity": True,
             "singleton_avoids_candidate_matrix": True}
    decision_cells = [case["name"] for case in lock["design"]["cases"] if case["m"] in (0, 4)]
    gates["performance_decision_rule_met"] = all(by_case[name]["median_speedup"] >= 1.25
                                                   and by_case[name]["median_peak_rss_ratio"] <= 2.0
                                                   for name in decision_cells)
    result = {"schema": "SubstrateContractQueryLazyMatrixCrossoverV1Analysis", "workers": len(workers),
              "source_lock_stable": True, "gates": gates, "cases": by_case, "paired_rows": paired,
              "claim_boundary": "Current lazy matrix crossover measured only on binary-coded pure Terms at two hypothesis counts on one host; model-adequacy failure remains unchanged."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
