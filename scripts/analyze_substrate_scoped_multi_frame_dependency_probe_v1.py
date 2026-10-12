#!/usr/bin/env python3
"""Independent integrity/gate check for the multi-frame probe and failed pilot."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT = ROOT / "evaluation/reports/substrate_scoped_multi_frame_dependency_probe_v1_20260926.json"
PILOT = ROOT / "evaluation/reports/substrate_scoped_multi_frame_dependency_probe_v1_20260926_pilot_failure.json"
BASELINE = ROOT / "evaluation/substrate_capability/frame_topology_cost_attribution_baseline_20260926"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data, pilot = json.loads(REPORT.read_text()), json.loads(PILOT.read_text())
    paths = {
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_PREREG_20260926.md",
        "amendment": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_V1_1_AMENDMENT_20260926.md",
        "runner": ROOT / "scripts/substrate_scoped_multi_frame_dependency_probe_v1.py",
        "graph_rs": BASELINE / "graph.rs",
        "substrate_rs": BASELINE / "substrate.rs",
        "rewrite_rs": BASELINE / "rewrite.rs",
        "py_rs": BASELINE / "py.rs",
        "native": BASELINE / "_native.abi3.so",
    }
    integrity = {key: sha(path) == data["inputs"][key] for key, path in paths.items()}
    from domains.engine_provenance import rust_source_fingerprint
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(BASELINE / "source_tree")) == data["inputs"]["rust_source_fingerprint"]
    archived_pilot_runner = ROOT / "scripts/archive/substrate_scoped_multi_frame_dependency_probe_v1_0_failed.py"
    pilot_integrity = {
        "pilot_raw_preserved": PILOT.is_file(),
        "pilot_runner_source_preserved": sha(archived_pilot_runner) == pilot["inputs"]["runner"],
        "pilot_had_exact_owner_notifications": all(
            sorted({int(m) for r in pilot["event"][stage]["reports"] for m in r["affected_microtheories"]}) == [0, 1, 2]
            for stage in ("birth", "deletion")
        ),
        "pilot_parity_failure_preserved": not pilot["gates"]["birth_event_matches_full"] and not pilot["gates"]["deletion_event_matches_full"],
    }
    def owners(stage):
        return sorted({int(m) for r in stage["reports"] for m in r["affected_microtheories"]})
    event, oracle, omitted = data["event"], data["full_oracle"], data["omitted_seed_control"]
    gates = {
        "confirmatory_artifact_hashes_match": all(integrity.values()),
        "pilot_failure_and_source_are_preserved": all(pilot_integrity.values()),
        "birth_owner_set_exact": owners(event["birth"]) == event["born"]["owners"],
        "deletion_owner_set_exact": owners(event["deletion"]) == event["ended"]["owners"],
        "queue_settles_both_stages": event["birth"]["complete"] and event["deletion"]["complete"],
        "birth_projection_matches_full": event["born"] == oracle["born"],
        "deletion_projection_matches_full": event["ended"] == oracle["ended"],
        "full_closure_reaches_fixed_points": oracle["birth"]["status"] == oracle["deletion"]["status"] == "fixed_point",
        "two_edges_born_and_removed": event["born"]["dependency_edges"] == [True, True] and event["ended"]["dependency_edges"] == [False, False],
        "omission_control_diverges": omitted["born"]["bridge_id"] is None and omitted["born"] != oracle["born"],
    }
    result = {"protocol": data["protocol"], "integrity": integrity, "pilot_integrity": pilot_integrity,
              "gates": gates, "all_pass": all(gates.values()),
              "owner_sets": {"birth": owners(event["birth"]), "deletion": owners(event["deletion"])}}
    out = REPORT.with_name("substrate_scoped_multi_frame_dependency_probe_v1_20260926_analysis.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit("integrity or analysis gate failed")


if __name__ == "__main__":
    main()
