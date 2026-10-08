#!/usr/bin/env python3
"""Independent validation and summary for the locked GenInfer scale probe."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_geninfer_scale_probe_v1_20260926.json"
OUTPUT = ROOT / "evaluation/reports/substrate_geninfer_scale_probe_v1_analysis_20260926.json"
EXPECTED = {4: ([2, 1, 1, 1], 6560),
            8: ([4, 2, 2, 2], 83520),
            12: ([6, 3, 3, 3], 390624)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    by_bound = defaultdict(list)
    for sample in raw["samples"]:
        by_bound[int(sample["bound"])].append(sample)

    checks = {
        "all_three_locked_bounds_present": set(by_bound) == set(EXPECTED),
        "five_finite_positive_samples_per_bound": all(
            len(by_bound[b]) == 5
            and all(math.isfinite(s["elapsed_seconds"])
                    and s["elapsed_seconds"] > 0 for s in by_bound[b])
            for b in EXPECTED),
        "candidate_counts_match_exhaustive_formula": all(
            int(raw["candidate_counts_by_bound"][str(b)]) == (2 * b + 1) ** 4 - 1
            == count for b, (_, count) in EXPECTED.items()),
        "all_calls_return_expected_generator": all(
            sample["matrix"] == EXPECTED[int(sample["bound"])][0]
            for sample in raw["samples"]),
        "schedule_and_sample_total_match_lock": (
            raw["protocol"]["scales"] == [1, 2, 3]
            and raw["protocol"]["bounds"] == [4, 8, 12]
            and raw["protocol"]["repetitions"] == 5
            and len(raw["samples"]) == 15),
        "native_extension_hash_current": sha(Path(
            raw["provenance"]["native_extension_path"]))
            == raw["provenance"]["native_extension_sha256"],
        "source_hashes_current": all(
            sha(ROOT / rel) == digest
            for rel, digest in raw["provenance"]["source_sha256"].items()),
    }

    summary = {}
    for bound in sorted(EXPECTED):
        times = [float(x["elapsed_seconds"]) for x in by_bound[bound]]
        candidates = EXPECTED[bound][1]
        summary[str(bound)] = {
            "candidate_count": candidates,
            "samples": len(times),
            "median_seconds": statistics.median(times),
            "min_seconds": min(times),
            "max_seconds": max(times),
            "median_candidates_per_second": statistics.median(
                candidates / t for t in times),
        }
    ratios = {
        f"B{bound}_over_B4_median_time":
            summary[str(bound)]["median_seconds"] / summary["4"]["median_seconds"]
        for bound in (8, 12)
    }
    result = {
        "schema_version": 1,
        "source": str(SOURCE.relative_to(ROOT)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "by_bound": summary,
        "median_time_ratios": ratios,
        "interpretation": (
            "Descriptive per-call CPU wall time and candidate throughput for one "
            "positive, fixed 2-D family. Three bounds and five repeated calls do "
            "not establish an asymptotic runtime law or natural workload cost."),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
