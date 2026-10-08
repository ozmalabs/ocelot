#!/usr/bin/env python3
"""Apply the real lineage gate to the source-locked v2 harvested shapes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = [str(ROOT), str(ROOT / "runners/dsl/python")]
import sys
sys.path[:0] = sys_path

INPUT = ROOT / "evaluation/reports/thoughtexperiment_harvest_shape_receipt_lineage_v2_raw_20261001.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_harvest_shape_lineage_owner_v1_analysis_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_HARVEST_SHAPE_LINEAGE_OWNER_ANALYSIS_V1_PREREG_20261001.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from domains.order_n_postulates import differentiate

    raw = json.loads(INPUT.read_text())
    fingerprints = raw["source_before"]["files"]
    current_relevant = {
        path: sha(ROOT / path) for path in (
            "domains/implication_harvester.py", "domains/order_n_postulates.py")}
    source_matches_capture = all(fingerprints.get(path) == digest
                                 for path, digest in current_relevant.items())
    rows = []
    for worker in raw["workers"]:
        arm_shapes = {"direct": worker["direct_shape"],
                      "receipt": worker["receipt_shape"]}
        outputs = {}
        for arm, shape in arm_shapes.items():
            outputs[arm] = {}
            for mt_name, mt_id in (("machine_learning", 15483),
                                   ("computer_vision", 21985)):
                derived = differentiate("", shapes=[shape],
                    postulate_mt_lineage={mt_name, mt_id},
                    substantive_structural=True,
                    postulate_mt_hops={mt_name: 0, mt_id: 0},
                    structural_max_hops=0)
                outputs[arm][mt_name] = derived
        rows.append({"pid": worker["pid"],
            "direct_shape": arm_shapes["direct"],
            "receipt_shape": arm_shapes["receipt"],
            "same_shape": arm_shapes["direct"] == arm_shapes["receipt"],
            "outputs": outputs})
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "input": INPUT.name,
        "input_source_stable": raw.get("source_stable"),
        "current_lineage_code_matches_capture": source_matches_capture,
        "current_hashes": current_relevant, "workers": rows,
        "gates": {
            "three_source_capture_workers": len(rows) == 3,
            "current_lineage_code_matches_capture": source_matches_capture,
            "all_direct_receipt_shapes_equal": all(row["same_shape"] for row in rows),
            "machine_learning_lineage_rejects_both": all(
                not row["outputs"]["direct"]["machine_learning"]
                and not row["outputs"]["receipt"]["machine_learning"]
                for row in rows),
            "computer_vision_lineage_accepts_both": all(
                row["outputs"]["direct"]["computer_vision"]
                and row["outputs"]["receipt"]["computer_vision"]
                for row in rows),
            "direct_receipt_outputs_equal": all(
                row["outputs"]["direct"] == row["outputs"]["receipt"]
                for row in rows),
        }}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
        "gates": result["gates"],
        "source_node_id": rows[0]["direct_shape"].get("source_node_id"),
        "owner": rows[0]["direct_shape"].get("source_mt"),
        "ml_transfer_count": len(rows[0]["outputs"]["direct"]["machine_learning"]),
        "cv_transfer_count": len(rows[0]["outputs"]["direct"]["computer_vision"])},
        sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("lineage owner analysis gate failed")


if __name__ == "__main__":
    main()
