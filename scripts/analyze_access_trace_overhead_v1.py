#!/usr/bin/env python3
"""Independent hash and timing recomputation for the paired access-trace replay."""
from __future__ import annotations
import argparse
import collections
import gzip
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "evaluation/reports/access_trace_overhead_v1_20261003.json"
RAW = ROOT / "evaluation/reports/access_trace_overhead_v1_workers_raw_20261003.json.gz"
OUTPUT = ROOT / "evaluation/reports/access_trace_overhead_v1_analysis_20261003.json"


def sha(path: Path, compressed: bool = False) -> str:
    h = hashlib.sha256()
    opener = gzip.open if compressed else open
    with opener(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()
    summary = json.loads(SUMMARY.read_text())
    with gzip.open(RAW, "rt") as f:
        raw = json.load(f)
    pairs = collections.defaultdict(dict)
    modes = collections.Counter()
    timing_rows = []
    pids = set()
    for run in raw["runs"]:
        mode, rep = run["mode"], int(run["replicate"])
        modes[mode] += 1
        base = run["worker_result"]["base_worker"]
        pids.add(int(base["pid"]))
        pair = pairs[rep].setdefault(mode, {})
        pair["digest"] = base["capture"]["graph_semantic_sha256"]
        pair["requests"] = {q["prompt"]: q for q in base["capture"]["requests"]}
    prompts = sorted({q["prompt"] for p in pairs.values() for m in p.values() for q in m["requests"].values()})
    timing = {}
    for prompt in prompts:
        rows = []
        for rep in sorted(pairs):
            on = int(pairs[rep]["on"]["requests"][prompt]["elapsed_ns"])
            off = int(pairs[rep]["off"]["requests"][prompt]["elapsed_ns"])
            rows.append({"replicate": rep, "on_ns": on, "off_ns": off, "on_over_off": on / off})
        timing[prompt] = {"pairs": rows,
                          "on_median_ns": statistics.median(x["on_ns"] for x in rows),
                          "off_median_ns": statistics.median(x["off_ns"] for x in rows),
                          "median_paired_on_over_off": statistics.median(x["on_over_off"] for x in rows),
                          "paired_ratio_min": min(x["on_over_off"] for x in rows),
                          "paired_ratio_max": max(x["on_over_off"] for x in rows)}
    direct = {"on": 0, "off": 0}; access_rows = {"on": 0, "off": 0}; drops = 0
    for run in raw["runs"]:
        mode = run["mode"]
        for req in run["worker_result"]["base_worker"]["capture"]["requests"]:
            rows = req.get("access_rows", [])
            access_rows[mode] += len(rows)
            direct[mode] += sum(1 for r in rows if r[1] in ("term_nodes_of_type_query", "term_nodes_of_type_candidate"))
            drops += int(req.get("access_dropped_events", 0)) + int(req.get("work_dropped_events", 0))
    digests_ok = all(set(pair) == {"on", "off"} and pair["on"]["digest"] == pair["off"]["digest"]
                     for pair in pairs.values())
    work_traces_ok = all(
        pairs[rep]["on"]["requests"][prompt].get("work_rows")
        == pairs[rep]["off"]["requests"][prompt].get("work_rows")
        for rep in pairs for prompt in prompts)
    result = {
        "schema_version": 1,
        "inputs": {"summary_sha256": sha(SUMMARY), "archive_sha256": sha(RAW),
                    "decompressed_archive_sha256": sha(RAW, compressed=True)},
        "checks": {
            "archive_hashes_match_summary": sha(RAW) == summary["raw_compressed_sha256"]
                and sha(RAW, compressed=True) == summary["raw_sha256"],
            "all_preregistered_capture_gates_pass": all(summary["checks"].values()) and all(raw["checks"].values()),
            "six_workers_three_pairs": len(pids) == 6 and len(pairs) == 3 and modes == {"on": 3, "off": 3},
            "paired_graph_semantics_match": digests_ok,
            "paired_scheduler_work_rows_match": work_traces_ok,
            "on_trace_rows_and_off_zero": access_rows["on"] > 0 and access_rows["off"] == 0,
            "zero_trace_drops": drops == 0,
            "summary_timing_reproduces": timing == summary["timing_summary"],
        },
        "timing_summary": timing,
        "access_event_rows": access_rows,
        "direct_nodes_of_type_event_rows": direct,
        "claim_boundary": "Independent descriptive recomputation for three matched pairs on one fixture; not a general performance estimate or significance result.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not all(result["checks"].values()):
        raise SystemExit("archive or timing recomputation check failed")


if __name__ == "__main__": main()
