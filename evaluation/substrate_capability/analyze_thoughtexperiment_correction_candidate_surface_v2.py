#!/usr/bin/env python3
"""Independent integrity and count analysis for candidate surface v2."""
from __future__ import annotations
import hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_raw_20261002.json"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2_lock_20261002.json"
ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_20261002.json"
SOURCES = (
    "domains/self_correction.py", "domains/edit_ops.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
    "substrate/boot_core.py", "domains/engine_provenance.py",
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
    "runners/dsl/python/substrate_rs/__init__.py",
    "evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V2_PREREG_20261002.md",
    "evaluation/substrate_capability/analyze_thoughtexperiment_correction_candidate_surface_v2.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_hashes() -> dict:
    paths = {name: sha(ROOT / name) for name in SOURCES}
    binary = Path("runners/dsl/python/substrate_rs/_native.abi3.so")
    paths["loaded_native_binary"] = sha(ROOT / binary)
    return paths


def family_counts(rows: list[dict]) -> dict:
    counts = Counter()
    for row in rows:
        for label in row["candidate_labels"]:
            if label.startswith("swap_term_leaf:"):
                family = "swap_term_leaf"
            else:
                family = label
            counts[family] += 1
    return dict(sorted(counts.items()))


def main() -> int:
    capture = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    workers = capture["workers"]
    baseline = workers[0]["inventory"]
    old = capture["previous_inventory"]
    current = capture["current_inventory"]
    total = sum(row["candidate_count"] for row in baseline)
    task_rules = sorted({row["target_rule"] for row in baseline
                         if row["task_shaped_labels"]})
    worker_expected = {name: lock["sources"][name] for name in SOURCES[:10]}
    gates = {
        "three_distinct_worker_pids": len(workers) == 3 and len({w["pid"] for w in workers}) == 3,
        "identical_per_rule_inventories": all(w["inventory"] == baseline for w in workers),
        "enumeration_read_only_in_each_worker": all(w["read_only"] for w in workers),
        "worker_source_hashes_match_lock": all(
            w["source_hashes"] == worker_expected for w in workers),
        "parent_source_hashes_stable_and_locked": (
            capture["source_before"] == capture["source_after"] == lock["sources"]
            and current_hashes() == lock["sources"]
        ),
        "candidate_family_counts_reconcile": sum(family_counts(baseline).values()) == total,
        "current_inventory_matches_historical_v1": current == old,
        "semantic_engine_matches_lock": capture["semantic_engine"] == lock["semantic_engine"],
        "one_task_shaped_rule_reported": task_rules == ["sd_mint_quantum"],
    }
    result = {
        "schema": "ThoughtexperimentCorrectionCandidateSurfaceV2Analysis",
        "gate_count": len(gates), "passed_gate_count": sum(gates.values()),
        "gates": gates,
        "summary": {
            "worker_count": len(workers), "active_rules": len(baseline),
            "candidate_instances": total,
            "rules_with_candidates": sum(bool(row["candidate_count"]) for row in baseline),
            "task_shaped_rules": task_rules,
            "candidate_family_counts": family_counts(baseline),
            "historical_inventory_exact_match": current == old,
        },
        "source_hashes_current": current_hashes(),
    }
    ANALYSIS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
