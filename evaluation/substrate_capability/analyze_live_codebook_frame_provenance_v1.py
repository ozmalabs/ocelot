#!/usr/bin/env python3
"""Post-hoc audit of frame-ID attributes in the source-locked live graph."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_live_helper_work_capture_v1_4_workers_raw_20261005.json.gz"
SUMMARY = ROOT / "evaluation/reports/substrate_live_helper_work_capture_v1_4_20261005.json"
PARITY = ROOT / "evaluation/reports/live_helper_work_capture_v1_4_baseline_parity_20261005.json"
OUT = ROOT / "evaluation/reports/live_codebook_frame_provenance_v1_analysis_20261005.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    summary = json.loads(SUMMARY.read_text())
    parity = json.loads(PARITY.read_text())
    raw_hash = sha(RAW)
    archive = json.loads(gzip.open(RAW, "rt", encoding="utf-8").read())
    runs = archive.get("runs", [])
    snapshots = [r for r in runs if "full_graph" in r.get("capture", {})]
    graph = snapshots[0]["capture"]["full_graph"] if len(snapshots) == 1 else {}
    parts = [n for n in graph.get("nodes", []) if str(n.get("type", "")).lower() == "shapesignature"]
    scope_counts = Counter(
        "scope_id_present" if "scope_id" in n.get("attrs", {}) else "scope_id_absent" for n in parts
    )
    frame_counts = Counter(
        "frame_id_present" if "frame_id" in n.get("attrs", {}) else "frame_id_absent" for n in parts
    )
    digests = [r.get("graph_semantic_sha256") for r in runs]
    checks = {
        "raw_archive_matches_capture_summary": raw_hash == summary.get("raw_compressed_sha256"),
        "single_full_graph_snapshot": len(snapshots) == 1,
        "three_worker_graph_semantics_reproduce": len(runs) == 3 and len(set(digests)) == 1,
        "instrumented_parity_report_passes": all(parity.get("checks", {}).values()),
        "shape_signature_population_is_nonempty": len(parts) > 0,
        "all_shape_signatures_lack_scope_id": len(parts) > 0 and scope_counts["scope_id_absent"] == len(parts),
        "all_shape_signatures_lack_frame_id": len(parts) > 0 and frame_counts["frame_id_absent"] == len(parts),
    }
    result = {
        "schema": "LiveCodebookFrameProvenanceV1Analysis",
        "run_id": "live-codebook-frame-provenance-v1-analysis-20261005",
        "inputs": {
            "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": raw_hash,
            "capture_summary_sha256": sha(SUMMARY),
            "instrumented_parity_sha256": sha(PARITY),
        },
        "worker_count": len(runs),
        "worker_graph_semantic_sha256": digests,
        "full_graph_snapshot_count": len(snapshots),
        "graph_node_count": len(graph.get("nodes", [])),
        "shape_signature_count": len(parts),
        "scope_id_attribute_counts": dict(scope_counts),
        "frame_id_attribute_counts": dict(frame_counts),
        "shape_signature_kind_counts": dict(Counter(str(n.get("attrs", {}).get("kind")) for n in parts)),
        "checks": checks,
        "passed": all(checks.values()),
        "interpretation": (
            "In this current v1.4 captured live route, no ShapeSignature has scope_id or frame_id. "
            "A new helper filter keyed by those attributes would return no codebook parts "
            "unless part ownership is established and recorded before helper execution. "
            "This does not establish that all substrate tasks lack frame-local codebooks."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "passed": result["passed"],
                      "shape_signature_count": len(parts), "scope_id": dict(scope_counts),
                      "frame_id": dict(frame_counts), "checks": checks}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
