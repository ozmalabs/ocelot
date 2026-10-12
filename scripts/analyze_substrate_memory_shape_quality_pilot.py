#!/usr/bin/env python3
"""Independent metadata/cluster audit for the durable memory shape-quality pilot."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_memory_shape_quality_pilot_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_memory_shape_quality_analysis_20260925.json"
FEATURES = ("new_signs", "utts", "round")


def rank_key(label):
    order = label.split("<")
    positions = {name: i for i, name in enumerate(order)}
    # shape_key returns, per input coordinate, the number of values below it.
    return [positions[name] for name in FEATURES]


def main():
    raw_bytes = RAW.read_bytes()
    report = json.loads(raw_bytes)
    records = report["dataset_record_metadata"]
    queries = report["queries"]
    expected_labels = {"<".join(p) for p in itertools.permutations(FEATURES)}
    groups = {}
    for r in records:
        groups.setdefault(r["rank_label"], []).append(r)
    errors = []
    if len(records) != 36:
        errors.append(f"expected 36 durable records, found {len(records)}")
    if set(groups) != expected_labels:
        errors.append("durable rank-label classes differ from the six permutations")
    for label, group in groups.items():
        if len(group) != 6:
            errors.append(f"{label}: expected six records, found {len(group)}")
        counts = {m: sum(x["magnitude_label"] == m for x in group) for m in ("low", "high")}
        if counts != {"low": 3, "high": 3}:
            errors.append(f"{label}: magnitude counts {counts}")
    if len(queries) != 12 or len({q["query_id"] for q in queries}) != 12:
        errors.append("expected twelve unique rank × magnitude queries")

    audited = []
    for q in queries:
        label = q["expected_rank_label"]
        members = groups.get(label, [])
        predicted_cluster = "cat:" + ",".join(map(str, rank_key(label)))
        all_rank = all(x["rank_label"] == label for x in members)
        mag_hits = sum(x["magnitude_label"] == q["expected_magnitude_label"] for x in members)
        rank_precision = sum(x["rank_label"] == label for x in members) / len(members) if members else 0
        magnitude_precision = mag_hits / len(members) if members else 0
        ok = (
            q["shape_cluster_id"] == predicted_cluster and
            q["shape_candidate_count"] == len(members) == 6 and
            q["shape_recall_all_records_in_rank_cluster"] == all_rank and all_rank and
            abs(q["shape_rank_precision"] - rank_precision) < 1e-12 and
            abs(q["shape_magnitude_precision"] - magnitude_precision) < 1e-12 and
            q["exact_key_correct"] is True
        )
        if not ok:
            errors.append(f"{q['query_id']}: runtime readback disagrees with independent fixture audit")
        audited.append({
            "query_id": q["query_id"], "expected_cluster_id": predicted_cluster,
            "observed_cluster_id": q["shape_cluster_id"],
            "fixture_cluster_size": len(members), "fixture_rank_precision": rank_precision,
            "fixture_magnitude_precision": magnitude_precision,
            "reported_shape_rank_precision": q["shape_rank_precision"],
            "reported_shape_magnitude_precision": q["shape_magnitude_precision"],
            "reported_exact_key_correct": q["exact_key_correct"], "audit_pass": ok,
        })

    checks = {
        "six_rank_classes_with_six_records_each": set(groups) == expected_labels and
            all(len(v) == 6 for v in groups.values()),
        "low_high_fixture_balance": all(
            sum(x["magnitude_label"] == "low" for x in v) == 3 and
            sum(x["magnitude_label"] == "high" for x in v) == 3 for v in groups.values()),
        "all_query_readbacks_match_fixture": not errors,
        "magnitude_collision_is_derived_from_fixture": all(
            abs(x["fixture_magnitude_precision"] - 0.5) < 1e-12 for x in audited),
    }
    payload = {
        "analysis": "substrate-memory-shape-quality-independent-audit-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "task_count": len(queries), "record_count": len(records),
        "query_checks": audited, "errors": errors, "checks": checks,
        "audit_limit": "The main raw report retains the exact-key correctness boolean but not the returned key string or shape candidate key list; this independent audit therefore verifies cluster identity and the expected cluster membership from the frozen record catalog, but cannot independently recheck those omitted per-record readbacks.",
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"analysis": payload["analysis"], "checks": checks,
                      "errors": errors, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
