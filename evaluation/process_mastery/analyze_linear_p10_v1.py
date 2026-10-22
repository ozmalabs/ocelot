"""Mechanical summaries and integrity checks for the frozen P10 scorecard."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def analyze(payload):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    rows = payload.get("records")
    if not isinstance(rows, list) or any(not row.get("status") for row in rows):
        raise ValueError("scorecard contains a missing record/status")
    if any(row["status"] not in {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}
           for row in rows):
        raise ValueError("scorecard contains an unknown trial status")
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get("family"), row.get("profile"))].append(row)
    summary = {}
    for (family, arm), group in sorted(groups.items()):
        statuses = Counter(row["status"] for row in group)
        completed = [row for row in group if row["status"] == "COMPLETED"]
        summary[f"{family}/{arm}"] = {
            "n": len(group), "statuses": dict(sorted(statuses.items())),
            "solved": sum(row.get("outcome") == "solved" for row in completed),
            "completed_n": len(completed),
            "solve_rate_of_all": (sum(row.get("outcome") == "solved" for row in group) / len(group)
                                  if group else None),
            "mean_steps_solved": (sum(row.get("steps", 0) for row in completed
                                       if row.get("outcome") == "solved") /
                                  max(1, sum(row.get("outcome") == "solved" for row in completed))),
            "input_audit_failures": sum(
                row.get("input_audit", {}).get("answer_fields_absent") is False or
                row.get("input_audit", {}).get("trace_nodes_are_graph_schemas") is False
                for row in group),
        }
    return {"schema": "pmb-linear-p10-analysis-v1",
            "phase": payload.get("metadata", {}).get("phase"),
            "split": payload.get("metadata", {}).get("split"),
            "n_records": len(rows), "families": summary,
            "unsupported_rows": sum(row["status"] == "UNSUPPORTED" for row in rows),
            "leakage_or_trace_audit_failures": sum(
                row.get("input_audit", {}).get("answer_fields_absent") is False or
                row.get("input_audit", {}).get("trace_nodes_are_graph_schemas") is False
                for row in rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path, nargs="?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        sample = {"schema": "pmb-scorecard-v1", "metadata": {"phase": "linear-p10-v1"},
                  "records": [{"family": "a", "profile": "greedy", "status": "COMPLETED",
                               "outcome": "solved", "steps": 2,
                               "input_audit": {"answer_fields_absent": True,
                                               "trace_nodes_are_graph_schemas": True}},
                              {"family": "a", "profile": "baseline", "status": "UNSUPPORTED"}]}
        result = analyze(sample)
        assert result["n_records"] == 2 and result["unsupported_rows"] == 1
        assert result["leakage_or_trace_audit_failures"] == 0
        print("linear_p10 analyzer self-check: PASS")
        return
    if args.scorecard is None:
        parser.error("scorecard is required unless --self-check is used")
    print(json.dumps(analyze(json.loads(args.scorecard.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
