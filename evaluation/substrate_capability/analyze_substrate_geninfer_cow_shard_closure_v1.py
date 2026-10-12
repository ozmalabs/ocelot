#!/usr/bin/env python3
"""Independent paired semantic/provenance gate for the COW closure panel."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/substrate_geninfer_cow_shard_closure_v1_20261006.json"
OUT = ROOT / "evaluation/reports/substrate_geninfer_cow_shard_closure_v1_analysis_20261006.json"
RUNNER = ROOT / "evaluation/substrate_capability/substrate_geninfer_cow_shard_closure_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_geninfer_cow_shard_closure_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_COW_SHARD_CLOSURE_V1_PREREG_20261006.md"
V1 = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"
BASE = Path("/tmp/ocelot_fullseed_cow_shards_v10")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    data = json.loads(CAPTURE.read_text())
    rows = data.get("cases", [])
    errors = []
    expected_cases = {case["id"]: case for case in data.get("case_spec", [])}
    keyed = {(row.get("case", {}).get("id"), row.get("variant")): row for row in rows}
    if len(rows) != 30 or len(keyed) != 30:
        errors.append("expected exactly 30 unique case/variant workers")
    if data.get("worker_count") != 30 or not data.get("source_stable"):
        errors.append("capture worker count or global source stability failed")
    for key, digest in (("runner_sha256", sha(RUNNER)), ("v1_runner_sha256", sha(V1)),
                        ("analyzer_sha256", sha(ANALYZER)), ("protocol_sha256", sha(PROTOCOL))):
        if data.get(key) != digest:
            errors.append(f"capture {key} does not match current source")
    source_maps = data.get("source_sha256_by_worker", [])
    if len(source_maps) != 30 or any(source_map != source_maps[0] for source_map in source_maps[1:]):
        errors.append("source hashes differ across workers or worker hash list is incomplete")
    binary_hashes = {
        variant: {row.get("source_before", {}).get("native_sha256") for row in rows if row.get("variant") == variant}
        for variant in ("64", "512")
    }
    if any(len(hashes) != 1 for hashes in binary_hashes.values()) or binary_hashes["64"] == binary_hashes["512"]:
        errors.append("binary hash differs within a variant or the paired variants are not distinct")
    pids = [row.get("pid") for row in rows]
    if len(set(pids)) != 30:
        errors.append("workers did not use 30 distinct processes")

    paired = []
    for case_id, case in expected_cases.items():
        pair = [keyed.get((case_id, variant)) for variant in ("64", "512")]
        if any(row is None for row in pair):
            errors.append(f"{case_id}: missing paired variant")
            continue
        for row in pair:
            expected_native = (BASE / f"shards{row['variant']}/tree/runners/dsl/python/substrate_rs/_native.abi3.so").resolve()
            if Path(row["source_before"]["native_path"]).resolve() != expected_native:
                errors.append(f"{case_id}/{row['variant']}: wrong native path")
            if row["source_before"] != row["source_after"] or not row.get("source_stable"):
                errors.append(f"{case_id}/{row['variant']}: source drift")
            for stage in ("train", "heldout", "corrupted_heldout"):
                resource = row.get(stage, {})
                for field in ("closure_work", "closure_wall_ns", "closure_cpu_ns", "hwm_before_kib", "hwm_after_kib", "nodes_before", "nodes_after", "edges_after"):
                    if not isinstance(resource.get(field), int) or resource[field] < 0:
                        errors.append(f"{case_id}/{row['variant']}: invalid {stage}.{field}")
        a, b = pair
        for field in ("target_acquired_during_training", "training_oracle_exact_match", "heldout_exact_match", "corrupted_heldout_exact_match"):
            if a.get(field) != b.get(field):
                errors.append(f"{case_id}: paired semantic mismatch in {field}")
        for stage in ("train", "heldout", "corrupted_heldout"):
            if a[stage].get("closure_work") != b[stage].get("closure_work"):
                errors.append(f"{case_id}: closure work mismatch in {stage}")
            for field in ("status", "covered_by", "residual", "transform_receipts"):
                if a[stage].get(field) != b[stage].get(field):
                    errors.append(f"{case_id}: paired semantic mismatch in {stage}.{field}")
        for field in ("matrix", "target_acquired_during_training", "training_acquired_generator_names",
                      "training_quanta_added", "training_oracle_exact_match", "heldout_exact_match",
                      "corrupted_heldout_exact_match"):
            if a.get(field) != b.get(field):
                errors.append(f"{case_id}: paired result mismatch in {field}")
        if case["kind"] == "positive":
            for row in pair:
                if not row.get("target_acquired_during_training"):
                    errors.append(f"{case_id}/{row['variant']}: target not acquired")
                if not row.get("training_oracle_exact_match") or not row.get("heldout_exact_match"):
                    errors.append(f"{case_id}/{row['variant']}: positive oracle check failed")
                if row.get("corrupted_heldout_exact_match"):
                    errors.append(f"{case_id}/{row['variant']}: corrupted heldout passed")
        elif case["kind"] == "disabled":
            if any(row.get("target_acquired_during_training") for row in pair):
                errors.append(f"{case_id}: disabled condition acquired target")
        paired.append((case, pair))

    cells = {}
    for kind, ns in (("positive", (4, 16, 64)), ("disabled", (8,)), ("predicate_corrupt", (8,))):
        for n in ns:
            subset = [(case, pair) for case, pair in paired if case["kind"] == kind and case["n"] == n]
            for variant_index, variant in enumerate(("64", "512")):
                selected = [pair[variant_index] for _, pair in subset]
                cells[f"{kind}_n{n}_shards{variant}"] = {
                    "runs": len(selected),
                    "median_train_wall_ms": statistics.median(row["train"]["closure_wall_ns"] for row in selected) / 1e6 if selected else None,
                    "median_heldout_wall_ms": statistics.median(row["heldout"]["closure_wall_ns"] for row in selected) / 1e6 if selected else None,
                    "median_train_cpu_ms": statistics.median(row["train"]["closure_cpu_ns"] for row in selected) / 1e6 if selected else None,
                    "median_train_work": statistics.median(row["train"]["closure_work"] for row in selected) if selected else None,
                    "median_train_hwm_delta_kib": statistics.median(row["train"]["hwm_delta_kib"] for row in selected) if selected else None,
                }
    report = {
        "schema": "GenInferCowShardClosureV1Analysis",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gates_pass": not errors,
        "errors": errors,
        "input_sha256": sha(CAPTURE),
        "summary": {"workers": len(rows), "paired_cases": len(paired), "cells": cells},
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "gates_pass": report["gates_pass"], "errors": errors, "summary": report["summary"]}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
