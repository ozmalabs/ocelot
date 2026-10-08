#!/usr/bin/env python3
"""Audit named-phase coverage in the archived exploratory 100k fanout run."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_100k_exploratory_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_phase_remainder_v1_20261004.json"
BACKENDS = ("full_copy", "shared_graph_pages")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
    rows = capture.get("runs", [])
    expected = {(r, b) for r in range(3) for b in BACKENDS}
    observed = {(row["configuration"]["replicate"], row["configuration"]["backend"]) for row in rows}
    checks = {
        "six_unique_backend_replicate_rows": len(rows) == 6 and observed == expected,
        "all_rows_at_100k_noise_scale": all(row["configuration"].get("noise_nodes") == 100_000 for row in rows),
        "nonnegative_named_phase_remainder": all(row["lifecycle_wall_ns"] >= sum(row["phase_ns"].values()) for row in rows),
        "semantic_and_isolation_checks_pass": all(row["primary_unchanged_before_return"]
            and row["stale_residual_rejected"] and row["stale_retry_left_primary_unchanged"]
            and row["selected_branch_matches_monolithic_oracle"]
            and row["primary_matches_monolithic_oracle"] for row in rows),
    }
    summaries = {}
    for backend in BACKENDS:
        subset = [row for row in rows if row["configuration"]["backend"] == backend]
        life = [row["lifecycle_wall_ns"] for row in subset]
        named = [sum(row["phase_ns"].values()) for row in subset]
        remainder = [a - b for a, b in zip(life, named)]
        summaries[backend] = {
            "replicates": len(subset),
            "median_lifecycle_ms": statistics.median(life) / 1e6,
            "median_named_phase_sum_ms": statistics.median(named) / 1e6,
            "median_unattributed_remainder_ms": statistics.median(remainder) / 1e6,
            "median_unattributed_fraction": statistics.median(r / t for r, t in zip(remainder, life)),
            "per_worker_ms": [{"replicate": row["configuration"]["replicate"],
                "lifecycle": row["lifecycle_wall_ns"] / 1e6,
                "named_phases": sum(row["phase_ns"].values()) / 1e6,
                "unattributed_remainder": (row["lifecycle_wall_ns"] - sum(row["phase_ns"].values())) / 1e6}
                for row in subset],
        }
    result = {
        "schema": "ThoughtexperimentPredecessorFanoutPhaseRemainderV1",
        "capture": CAPTURE.relative_to(ROOT).as_posix(),
        "capture_sha256": sha(CAPTURE),
        "checks": checks,
        "summaries": summaries,
        "interpretation": "The remainder is lifecycle time outside the recorded phase timers. It is not attributed to hashing alone; it may include graph exports, digest checks, readback, allocator sampling, and other validation work.",
        "reproducibility_limit": "The exploratory capture has no retained matching 100k runner or pre-run source lock; this derived timing audit cannot replay or upgrade it to confirmatory scale evidence.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summaries": {k: {name: value for name, value in v.items() if name != "per_worker_ms"}
                                   for k, v in summaries.items()}}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
