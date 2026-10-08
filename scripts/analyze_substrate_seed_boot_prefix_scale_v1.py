#!/usr/bin/env python3
"""Independently summarize and validate the seed boot prefix scale report."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/seed_boot_prefix_scale_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_seed_boot_prefix_scale_v1_analysis_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(row: dict) -> dict:
    return {key: row[key] for key in (
        "report", "node_count", "edge_count", "graph_sha256", "grammar_sha256",
        "rule_store_sha256", "rule_access_sha256", "active_rule_count",
        "rule_order", "rule_order_sha256")}


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    errors = []
    if not raw.get("all_gates_pass") or not raw.get("all_state_parity"):
        errors.append("runner state parity gate failed")
    if not raw.get("unique_processes"):
        errors.append("runner process uniqueness gate failed")
    if raw.get("runner_sha256") != lock.get("runner_sha256"):
        errors.append("runner hash differs from lock")
    if raw.get("lock_sha256") != sha(LOCK):
        errors.append("raw report lock hash mismatch")
    if raw.get("source_hashes_after") != lock.get("sources"):
        errors.append("source hashes differ from lock")
    snapshot_root = Path(raw["snapshot"]["full_seed_dir"])
    corpus = json.loads((ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json").read_text())
    for item in corpus["manifests"]:
        path = snapshot_root / item["path"]
        if not path.is_file() or sha(path) != item["sha256"]:
            errors.append(f"frozen snapshot mismatch: {item['path']}")
            break
    arms = raw.get("arms", [])
    pids = [arm["worker"]["process_id"] for arm in arms]
    if len(arms) != 16 or len(set(pids)) != 16:
        errors.append("expected 16 unique worker processes")
    summaries = {}
    for size in lock["size_points"]:
        rows = [arm for arm in arms if arm["requested_size"] == size]
        if len(rows) != 4:
            errors.append(f"N={size}: expected four arms")
            continue
        fps = [state(arm["worker"]) for arm in rows]
        parity = all(fp == fps[0] for fp in fps)
        if not parity:
            errors.append(f"N={size}: boot state differs across arms")
        cold = [arm for arm in rows if arm["cache_mode"] == "cold"]
        warm = [arm for arm in rows if arm["cache_mode"] == "warm"]
        if len(cold) != 2 or len(warm) != 2:
            errors.append(f"N={size}: expected two cold/two warm arms")
        for arm in warm:
            if arm["cache"].get("before") != arm["cache"].get("after"):
                errors.append(f"N={size}: warm cache changed")
        sample = rows[0]["worker"]
        subset = raw["snapshot"]["subsets"][str(size)]
        if subset["seed_id_count"] != size:
            errors.append(f"N={size}: seed index size mismatch")
        want_files = lock["full_physical_manifest_count"] if size == lock["full_index_seed_count"] else size
        if subset["manifest_file_count"] != want_files:
            errors.append(f"N={size}: physical manifest count mismatch")
        summaries[str(size)] = {
            "seed_id_count": subset["seed_id_count"],
            "physical_manifest_count": subset["manifest_file_count"],
            "node_count": sample["node_count"],
            "edge_count": sample["edge_count"],
            "active_rule_count": sample["active_rule_count"],
            "rule_summary_count": sample["report"].get("self_model", {}).get("rules", {}).get("total"),
            "program_summary_count": sample["report"].get("self_model", {}).get("programs", {}).get("total"),
            "loaded_seed_count": sample["report"].get("loaded"),
            "failed_seed_count": len(sample["report"].get("failed", [])),
            "state_parity": parity,
            "wall_seconds": {
                "cold": [arm["worker"]["wall_ns"] / 1e9 for arm in cold],
                "cold_median": statistics.median(arm["worker"]["wall_ns"] for arm in cold) / 1e9,
                "warm": [arm["worker"]["wall_ns"] / 1e9 for arm in warm],
                "warm_median": statistics.median(arm["worker"]["wall_ns"] for arm in warm) / 1e9,
            },
            "cpu_seconds": {
                "cold": [arm["worker"]["cpu_ns"] / 1e9 for arm in cold],
                "cold_median": statistics.median(arm["worker"]["cpu_ns"] for arm in cold) / 1e9,
                "warm": [arm["worker"]["cpu_ns"] / 1e9 for arm in warm],
                "warm_median": statistics.median(arm["worker"]["cpu_ns"] for arm in warm) / 1e9,
            },
            "peak_rss_kib": [arm["worker"]["peak_rss_native_units"] for arm in rows],
            "peak_rss_mib_range": [min(arm["worker"]["peak_rss_native_units"] for arm in rows) / 1024,
                                   max(arm["worker"]["peak_rss_native_units"] for arm in rows) / 1024],
        }
    # The runner records the canonical order so this analyzer does not need
    # to import the optional native extension just to inspect source payloads.
    full_order = raw["snapshot"]["subsets"][str(lock["full_index_seed_count"])]["order"]
    seed_paths = {}
    for path in sorted(snapshot_root.glob("*.json")) + sorted((snapshot_root / "generated").glob("*.json")):
        try:
            manifest = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(manifest, dict):
            continue
        sid = manifest.get("id") or path.stem
        seed_paths[sid] = str(path)
    if len(full_order) != lock["full_index_seed_count"]:
        errors.append("full source index size differs from lock")
    composition = {}
    bands = ((1, 128), (129, 256), (257, 512), (513, 737))
    for start, end in bands:
        rows = []
        for sid in full_order[start - 1:end]:
            path = Path(seed_paths[sid])
            try:
                manifest = json.loads(path.read_text())
            except Exception:
                continue
            if not isinstance(manifest, dict):
                continue
            graph = manifest.get("graph") if isinstance(manifest.get("graph"), dict) else {}
            rows.append({"seed_id": sid, "relative_path": path.relative_to(snapshot_root).as_posix(),
                         "bytes": path.stat().st_size, "top_level_keys": sorted(manifest),
                         "top_level_nodes": len(manifest.get("nodes") or []),
                         "top_level_edges": len(manifest.get("edges") or []),
                         "top_level_rules": len(manifest.get("rules") or []),
                         "concepts": len(manifest.get("concepts") or []),
                         "nested_graph_nodes": len(graph.get("nodes") or []),
                         "nested_graph_edges": len(graph.get("edges") or [])})
        composition[f"{start}-{end}"] = {
            "seed_id_count": len(rows),
            "manifest_bytes": sum(row["bytes"] for row in rows),
            "top_level_nodes": sum(row["top_level_nodes"] for row in rows),
            "top_level_edges": sum(row["top_level_edges"] for row in rows),
            "top_level_rules": sum(row["top_level_rules"] for row in rows),
            "concepts": sum(row["concepts"] for row in rows),
            "nested_graph_nodes": sum(row["nested_graph_nodes"] for row in rows),
            "nested_graph_edges": sum(row["nested_graph_edges"] for row in rows),
            "largest_manifests": sorted(rows, key=lambda row: row["bytes"], reverse=True)[:8],
            "most_rules": sorted(rows, key=lambda row: row["top_level_rules"], reverse=True)[:8],
        }
    report = {"schema_version": 1,
              "analysis_id": "substrate-seed-boot-prefix-scale-v1-analysis-20260925",
              "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
              "environment": {"python": sys.version, "platform": platform.platform(),
                              "logical_cpu_count": os.cpu_count(),
                              "ru_maxrss_unit": "KiB on Linux"},
              "validation_errors": errors, "all_checks_pass": not errors,
              "unique_processes": len(set(pids)) == 16,
              "all_size_state_parity": all(v["state_parity"] for v in summaries.values()),
              "sizes": summaries, "seed_band_composition": composition,
              "claim_limit": "four nested points, one host/corpus, two replicates per cache condition; timing is non-monotonic and exploratory."}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": report["all_checks_pass"],
                      "validation_errors": errors, "analysis": str(OUT)}))
    return 0 if report["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
