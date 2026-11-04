"""Mechanical summaries for the frozen Linear P6 scorecard."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def analyze(payload: dict) -> dict:
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    records = payload.get("records")
    if not isinstance(records, list) or any(r.get("status") is None for r in records):
        raise ValueError("scorecard contains a missing record/status")
    by = defaultdict(list)
    for row in records:
        by[(row.get("family"), row.get("profile"))].append(row)
    summary = {}
    for (family, profile), rows in sorted(by.items()):
        statuses = Counter(r["status"] for r in rows)
        completed = [r for r in rows if r["status"] == "COMPLETED"]
        solved = sum(r.get("outcome") == "solved" for r in completed)
        summary[f"{family}/{profile}"] = {
            "n": len(rows), "statuses": dict(sorted(statuses.items())),
            "solved": solved if family == "a" else None,
            "solve_rate": solved / len(rows) if family == "a" and rows else None,
            "program_passes": sum(bool(r.get("external_outcome", {}).get("all_ok"))
                                   for r in completed) if family == "e" else None,
        }
    return {"schema": "pmb-linear-p6-analysis-v1",
            "phase": payload.get("metadata", {}).get("phase"),
            "split": payload.get("metadata", {}).get("split"),
            "n_records": len(records), "families": summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path, nargs="?")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        sample = {"schema": "pmb-scorecard-v1", "metadata": {"phase": "linear-p6-v1"},
                  "records": [{"family": "a", "profile": "baseline",
                               "status": "FAILED", "outcome": "unsolved"},
                              {"family": "a", "profile": "track-i",
                               "status": "COMPLETED", "outcome": "solved"}]}
        result = analyze(sample)
        assert result["n_records"] == 2
        assert result["families"]["a/track-i"]["solve_rate"] == 1.0
        print("linear_p6 analyzer self-check: PASS")
        return
    if args.scorecard is None:
        parser.error("scorecard is required unless --self-check is used")
    payload = json.loads(args.scorecard.read_text())
    print(json.dumps(analyze(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
