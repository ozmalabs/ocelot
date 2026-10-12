#!/usr/bin/env python3
"""Corrected independent review; v1 comparison normalizes the schema delta."""
from __future__ import annotations
import hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_raw_20261002.json"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2_lock_20261002.json"
REVIEW = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_review_20261002.json"
V1_RAW = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v1_raw_20261001.json"
RUNTIME_SOURCES = (
    "domains/self_correction.py", "domains/edit_ops.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
    "substrate/boot_core.py", "domains/engine_provenance.py",
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
    "runners/dsl/python/substrate_rs/__init__.py",
)
LOCKED_SOURCES = (*RUNTIME_SOURCES,
    "evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V2_PREREG_20261002.md",
    "evaluation/substrate_capability/analyze_thoughtexperiment_correction_candidate_surface_v2.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(rows):
    return [{key: row[key] for key in ("target_rule", "candidate_labels", "candidate_count")}
            for row in rows]


def families(rows):
    result = Counter()
    for row in rows:
        for label in row["candidate_labels"]:
            result["swap_term_leaf" if label.startswith("swap_term_leaf:") else label] += 1
    return dict(sorted(result.items()))


def main() -> int:
    capture = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    v1 = json.loads(V1_RAW.read_text())
    workers = capture["workers"]
    inventory = workers[0]["inventory"]
    old = v1["workers"][0]["inventory"]
    runtime_expected = {name: lock["sources"][name] for name in RUNTIME_SOURCES}
    current_expected = {name: sha(ROOT / name) for name in LOCKED_SOURCES}
    from substrate_rs import _native
    current_expected["loaded_native_binary"] = sha(Path(_native.__file__).resolve())
    task_shaped = sorted({row["target_rule"] for row in inventory
                          if row["task_shaped_labels"]})
    gates = {
        "three_fresh_distinct_workers": len(workers) == 3 and len({w["pid"] for w in workers}) == 3,
        "exact_inventory_parity_across_workers": all(w["inventory"] == inventory for w in workers),
        "enumeration_preserved_primary_graph_and_rules": all(w["read_only"] for w in workers),
        "worker_source_hashes_match_lock": all(w["source_hashes"] == runtime_expected for w in workers),
        "source_and_binary_hashes_match_lock_now": current_expected == lock["sources"],
        "source_hashes_stable_across_capture": capture["source_before"] == capture["source_after"] == lock["sources"],
        "candidate_counts_reconcile": sum(families(inventory).values()) == sum(w["candidate_count"] for w in workers[:1]),
        "historical_inventory_matches_on_shared_fields": normalize(inventory) == normalize(old),
        "one_task_shaped_rule": task_shaped == ["sd_mint_quantum"],
    }
    result = {
        "schema": "ThoughtexperimentCorrectionCandidateSurfaceV2CorrectedReview",
        "reviewer_sha256": sha(Path(__file__).resolve()),
        "supersedes": "evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_20261002.json historical-schema comparator only",
        "initial_review_retained": True,
        "gate_count": len(gates), "passed_gate_count": sum(gates.values()), "gates": gates,
        "summary": {
            "workers": len(workers), "active_rules": workers[0]["active_rule_count"],
            "candidate_instances": workers[0]["candidate_count"],
            "candidate_family_counts": families(inventory),
            "task_shaped_rules": task_shaped,
            "historical_v1_shared_fields_match": normalize(inventory) == normalize(old),
        },
    }
    REVIEW.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
