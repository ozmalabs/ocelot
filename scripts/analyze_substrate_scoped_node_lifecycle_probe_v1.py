#!/usr/bin/env python3
"""Independent integrity and gate check for the locked lifecycle probe."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT = ROOT / "evaluation/reports/substrate_scoped_node_lifecycle_probe_v1_20260926.json"
BASELINE = ROOT / "evaluation/substrate_capability/frame_topology_cost_attribution_baseline_20260926"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads(REPORT.read_text())
    files = {
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_NODE_LIFECYCLE_PREREG_20260926.md",
        "runner": ROOT / "scripts/substrate_scoped_node_lifecycle_probe_v1.py",
        "graph_rs": BASELINE / "graph.rs",
        "substrate_rs": BASELINE / "substrate.rs",
        "rewrite_rs": BASELINE / "rewrite.rs",
        "py_rs": BASELINE / "py.rs",
        "native": BASELINE / "_native.abi3.so",
    }
    integrity = {name: sha(path) == data["inputs"][name] for name, path in files.items()}
    from domains.engine_provenance import rust_source_fingerprint
    integrity["rust_source_fingerprint"] = rust_source_fingerprint(str(BASELINE / "source_tree")) == data["inputs"]["rust_source_fingerprint"]
    event, oracle, omitted = data["event"], data["full_oracle"], data["omitted_seed_control"]
    def owners(stage):
        return sorted({int(owner) for report in stage["reports"] for owner in report["affected_microtheories"]})
    gates = {
        "artifact_hashes_match": all(integrity.values()),
        "birth_notification_is_exact": owners(event["birth"]) == event["born"]["owners"],
        "deletion_notification_is_exact": owners(event["deletion"]) == event["ended"]["owners"],
        "both_event_stages_settle": event["birth"]["complete"] and event["deletion"]["complete"],
        "birth_matches_full_oracle": event["born"] == oracle["born"],
        "deletion_matches_full_oracle": event["ended"] == oracle["ended"],
        "full_oracle_reaches_fixed_point": oracle["birth"]["status"] == oracle["deletion"]["status"] == "fixed_point",
        "omitted_seed_control_is_stale": omitted["born"] != oracle["born"] and omitted["born"]["bridge_id"] is None,
    }
    result = {"protocol": data["protocol"], "integrity": integrity, "gates": gates,
              "all_pass": all(gates.values()), "event_owner_sets": {"birth": owners(event["birth"]), "deletion": owners(event["deletion"])}}
    out = REPORT.with_name("substrate_scoped_node_lifecycle_probe_v1_20260926_analysis.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit("integrity or preregistered analysis gate failed")


if __name__ == "__main__":
    main()
