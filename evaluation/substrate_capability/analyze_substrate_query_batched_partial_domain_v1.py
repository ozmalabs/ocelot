#!/usr/bin/env python3
"""Independent semantic analysis for partial-domain matrix selector coverage."""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_contract_query_batched_partial_domain_v1_raw_20261002.json"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_batched_partial_domain_v1_lock_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_contract_query_batched_partial_domain_v1_analysis_20261002.json"


def oracle(index: int, env: dict):
    x, y = env["x"], env.get("y", 0)
    return [lambda: x, lambda: x + 1, lambda: x - 1, lambda: x * 2,
            lambda: abs(x), lambda: x % 3, lambda: x / 2, lambda: x + y][index]()


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
    capture, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    workers = capture["workers"]
    assert capture["lock"] == capture["post_lock"] == lock
    assert len(workers) == 32 and all(row.get("kind") == "worker" for row in workers)
    assert len({row["pid"] for row in workers}) == 32
    assert all(row["source_stable"] and row["before"] == row["after"] == lock["active"] for row in workers)
    design = lock["design"]
    hypotheses, grid = design["hypotheses"], design["candidate_inputs"]
    grid_keys = {json.dumps(env, sort_keys=True) for env in grid}
    assert len(grid) == 44 and any("y" not in env for env in grid) and any("y" in env for env in grid)
    pairs = {}
    for row in workers:
        pairs.setdefault((row["target"], row["rep"]), {})[row["arm"]] = row
    assert len(pairs) == 16 and all(set(arms) == {"uncached", "matrix"} for arms in pairs.values())
    summary = []
    selected_partial_total = 0
    for (target, rep), arms in sorted(pairs.items()):
        uncached, matrix = arms["uncached"], arms["matrix"]
        assert uncached["history"] == matrix["history"]
        assert uncached["terminal"] == matrix["terminal"]
        assert uncached["terminal"]["reason"] == "fewer than two hypotheses fit existing observations"
        assert uncached["terminal"]["surviving_hypotheses"] == [f"h{target}"]
        observations = [{"inputs": {"x": 0, "y": 1}, "expected": oracle(target, {"x": 0, "y": 1})}]
        for query in uncached["history"]:
            env = query["query"]
            assert json.dumps(env, sort_keys=True) in grid_keys
            assert not any(old["inputs"] == env for old in observations)
            survivors = [i for i in range(len(hypotheses)) if all(
                type(oracle(i, old["inputs"])) is type(old["expected"])
                and oracle(i, old["inputs"]) == old["expected"] for old in observations)]
            assert query["survivors_before"] == [f"h{i}" for i in survivors]
            expected_predictions = [{"hypothesis": f"h{i}", "output": oracle(i, env)} for i in survivors]
            assert query["predictions"] == expected_predictions
            scores = []
            for candidate in grid:
                if any(old["inputs"] == candidate for old in observations):
                    continue
                scores.append((entropy([oracle(i, candidate) for i in survivors]), candidate))
            max_score = max(score for score, _ in scores)
            best = next(candidate for score, candidate in scores if abs(score - max_score) < 1e-12)
            assert abs(query["entropy_bits"] - max_score) < 1e-12
            assert query["query"] == best
            assert query["oracle_output"] == oracle(target, env)
            observations.append({"inputs": env, "expected": query["oracle_output"]})
        for row in (uncached, matrix):
            unsupported = row["unsupported_control"]
            assert unsupported["result"] == {"ok": False, "reason": "batched selection requires pure Term hypotheses"}
            assert unsupported["evaluator_calls"] == 0
        assert matrix["matrix_cells"] == len(hypotheses) * (len(grid) + 1)
        selected_partial_total += matrix["selected_partial_count"]
        summary.append({"target": target, "rep": rep, "queries": len(uncached["history"]),
                        "selected_partial_inputs": matrix["selected_partial_count"],
                        "uncached_calls": uncached["native_calls"], "matrix_calls": matrix["native_calls"],
                        "uncached_ms": uncached["elapsed_ns"] / 1e6,
                        "matrix_ms": matrix["elapsed_ns"] / 1e6})
    gates = {"locked_32_workers": True, "all_eight_targets_identified": True,
             "paired_history_parity": True, "independent_operator_oracle": True,
             "partial_and_complete_grid_covered": True, "unsupported_holds_refused_without_eval": True,
             "matrix_cell_count_correct": True}
    result = {"schema": "SubstrateContractQueryBatchedPartialDomainV1Analysis", "workers": len(workers),
              "source_lock_stable": True, "gates": gates,
              "aggregate": {"paired_target_repetitions": len(summary), "selected_partial_inputs": selected_partial_total,
                            "total_queries": sum(row["queries"] for row in summary)},
              "rows": summary,
              "claim_boundary": "Matrix selector is semantically equivalent to the uncached selector for the eight measured pure-Term operators and partial x/y inputs. Holds is refused before evaluation. No natural-task or model-adequacy claim."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
