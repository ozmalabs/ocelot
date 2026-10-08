#!/usr/bin/env python3
"""Independent validation and summary for GenInfer relation-count scaling."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_geninfer_relation_count_probe_v1_20260926.json"
OUTPUT = ROOT / "evaluation/reports/substrate_geninfer_relation_count_probe_v1_analysis_20260926.json"
RELATION_COUNTS = (4, 8, 16, 32, 64)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    grouped = defaultdict(list)
    for sample in raw["samples"]:
        grouped[int(sample["relation_count"])].append(sample)
    checks = {
        "all_five_locked_relation_counts_present": set(grouped) == set(RELATION_COUNTS),
        "five_samples_per_condition": all(
            len(grouped[n]) == 5 for n in RELATION_COUNTS),
        "relation_cardinalities_exact": all(
            s["base_relation_count"] == n and s["goal_relation_count"] == n
            for n in RELATION_COUNTS for s in grouped[n]),
        "every_call_returns_locked_matrix": all(
            s["matrix"] == [2, 1, 1, 1]
            for n in RELATION_COUNTS for s in grouped[n]),
        "candidate_count_fixed_at_6560": (
            raw["protocol"]["bound"] == 4
            and raw["protocol"]["candidate_count_per_call"] == 6560
            and all(int(raw["candidate_counts_by_relation_count"][str(n)]) == 6560
                    for n in RELATION_COUNTS)),
        "schedule_matches_lock": (
            raw["protocol"]["relation_counts"] == list(RELATION_COUNTS)
            and raw["protocol"]["repetitions"] == 5
            and len(raw["samples"]) == 25),
        "all_elapsed_samples_finite_positive": all(
            math.isfinite(s["elapsed_seconds"]) and s["elapsed_seconds"] > 0
            for s in raw["samples"]),
        "native_extension_hash_current": sha(Path(
            raw["provenance"]["native_extension_path"]))
            == raw["provenance"]["native_extension_sha256"],
        "source_hashes_current": all(
            sha(ROOT / rel) == digest
            for rel, digest in raw["provenance"]["source_sha256"].items()),
    }
    summary = {}
    for n in RELATION_COUNTS:
        times = [float(s["elapsed_seconds"]) for s in grouped[n]]
        summary[str(n)] = {
            "candidate_count_per_call": 6560,
            "samples": len(times),
            "median_seconds": statistics.median(times),
            "min_seconds": min(times),
            "max_seconds": max(times),
            "median_candidates_per_second": statistics.median(6560 / t for t in times),
        }
    base_median = summary["4"]["median_seconds"]
    ratios = {str(n): summary[str(n)]["median_seconds"] / base_median
              for n in RELATION_COUNTS[1:]}
    result = {
        "schema_version": 1,
        "source": str(SOURCE.relative_to(ROOT)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "by_relation_count": summary,
        "median_time_ratio_vs_4_relations": ratios,
        "interpretation": (
            "Descriptive direct-call timing at fixed B and fixed candidate count "
            "for predicate-distinguished copies of one shape motif. This does "
            "not establish diverse-shape or natural-task scaling."),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
