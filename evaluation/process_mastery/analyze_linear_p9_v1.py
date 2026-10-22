"""Mechanical P9 scorecard summaries; no result tuning or row mutation."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def analyze(payload):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    records = payload.get("records")
    if not isinstance(records, list) or any(row.get("status") is None for row in records):
        raise ValueError("missing records/status")
    groups = defaultdict(list)
    for row in records:
        groups[(row.get("family"), row.get("profile"))].append(row)
    metrics = {}
    for (family, profile), rows in sorted(groups.items()):
        done = [row for row in rows if row["status"] == "COMPLETED"]
        metrics[f"{family}/{profile}"] = {
            "n": len(rows), "statuses": dict(Counter(row["status"] for row in rows)),
            "passed": sum(bool(row.get("external_outcome", {}).get("pass")) for row in done),
            "pass_rate": (sum(bool(row.get("external_outcome", {}).get("pass"))
                               for row in done) / len(done)) if done else None,
            "actions": sum(row.get("actions", 0) for row in done),
            "mean_seconds": (sum(row.get("compute", {}).get("seconds", 0.0)
                                  for row in done) / len(done)) if done else None,
            "mean_graph_nodes": (sum(row.get("compute", {}).get("graph_nodes", 0)
                                      for row in done) / len(done)) if done else None,
            "input_answer_leaks": sum(bool(row.get("target_in_agent_input") or
                                            row.get("answer_in_graph")) for row in rows),
        }
    exact = {arm: metrics.get(f"novel_exact_effects/{arm}", {}).get("pass_rate")
             for arm in ("operators_on", "operators_off", "held_only")}
    gain = (exact["operators_on"] - exact["operators_off"]
            if exact["operators_on"] is not None and exact["operators_off"] is not None else None)
    return {
        "schema": "pmb-linear-p9-analysis-v1",
        "phase": payload.get("metadata", {}).get("phase"),
        "split": payload.get("metadata", {}).get("split"),
        "n_records": len(records), "families": metrics,
        "primary": {"exact_verified_coverage": exact,
                    "operators_on_minus_off_pp": 100.0 * gain if gain is not None else None,
                    "zero_answer_leaks": all(v["input_answer_leaks"] == 0
                                              for v in metrics.values())},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", nargs="?", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        sample = {"schema": "pmb-scorecard-v1", "metadata": {"phase": "linear-p9-v1"},
                  "records": [{"family": "novel_exact_effects", "profile": "operators_on",
                               "status": "COMPLETED", "external_outcome": {"pass": True}},
                              {"family": "novel_exact_effects", "profile": "operators_off",
                               "status": "COMPLETED", "external_outcome": {"pass": False}}]}
        result = analyze(sample)
        assert result["primary"]["operators_on_minus_off_pp"] == 100.0
        print("linear_p9 analyzer self-check: PASS")
        return
    if not args.scorecard:
        parser.error("scorecard required")
    print(json.dumps(analyze(json.loads(args.scorecard.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
