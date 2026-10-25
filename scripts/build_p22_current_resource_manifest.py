"""Reconcile P22 checkpoint provenance with available isolated resource cells."""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.analyze_linear_p22_v1 import RESOURCE_FIELDS
from evaluation.process_mastery.p22_resource_accounting import (
    analyzer_resource_record, resource_snapshot_digest_valid,
)

RESULTS = ROOT / "evaluation/process_mastery/results"
AUDIT = RESULTS / "p22_checkpoint_resource_audit_20261025.json"
PRIOR_PANEL = RESULTS / "p22_resource_panel_existing_checkpoints_0609_0612_0622_0625.json.gz"
SUPPLEMENT = RESULTS / "p22_resource_panel_new_approved_checkpoints_0609_0612_0622_0625.json.gz"
OUTPUT = RESULTS / "p22_current_resource_manifest_20261025.json"


def _read(path: Path, *, compressed: bool = False) -> tuple[dict, str]:
    raw = path.read_bytes()
    payload = json.loads(gzip.decompress(raw) if compressed else raw)
    return payload, hashlib.sha256(raw).hexdigest()


def build() -> dict[str, Any]:
    audit, audit_hash = _read(AUDIT)
    prior, prior_hash = _read(PRIOR_PANEL, compressed=True)
    supplement, supplement_hash = _read(SUPPLEMENT, compressed=True)
    sources = {
        str(path.relative_to(ROOT)): digest for path, digest in (
            (AUDIT, audit_hash), (PRIOR_PANEL, prior_hash), (SUPPLEMENT, supplement_hash))
    }
    issues: list[dict[str, str]] = []
    if audit.get("issues"):
        issues.append({"source": "checkpoint_audit", "issue": "audit_has_issues"})
    for label, panel in (("prior_panel", prior), ("supplementary_panel", supplement)):
        if panel.get("heldout_accessed") is not False:
            issues.append({"source": label, "issue": "heldout_access_not_false"})
        if panel.get("validation_accessed") not in (None, False):
            issues.append({"source": label, "issue": "validation_access_not_false"})
        if panel.get("status") not in {"DEVELOPMENT_ONLY", "DEVELOPMENT_ONLY_PARTIAL"}:
            issues.append({"source": label, "issue": "panel_status_invalid"})

    checkpoint_rows = {row["checkpoint_id"]: row for row in audit["checkpoints"]}
    panel_rows = list(prior.get("rows", [])) + list(supplement.get("rows", []))
    cells_by_checkpoint: dict[str, list[dict]] = {}
    fields_by_name: dict[str, list[tuple[float | int, str]]] = {
        field: [] for field in RESOURCE_FIELDS
    }
    cell_rows = []
    for row in panel_rows:
        checkpoint_id = row.get("checkpoint_id")
        outcome = row.get("outcome") or {}
        snapshot = outcome.get("resource_snapshot")
        if checkpoint_id not in checkpoint_rows:
            issues.append({"checkpoint": str(checkpoint_id), "issue": "cell_checkpoint_not_audited"})
            continue
        if outcome.get("status") != "COMPLETED":
            issues.append({"checkpoint": checkpoint_id, "issue": "cell_not_completed"})
        if not isinstance(snapshot, dict) or not resource_snapshot_digest_valid(snapshot):
            issues.append({"checkpoint": checkpoint_id, "issue": "cell_snapshot_digest_invalid"})
            continue
        measured = analyzer_resource_record(
            snapshot,
            cumulative_primitive_work=outcome.get("cumulative_primitive_work"),
            wall_time_seconds=outcome.get("isolated_worker_wall_time_seconds"))
        resources = measured.get("resources", {})
        coverage = measured.get("resource_measurements", {})
        cell_fields = {}
        for field in RESOURCE_FIELDS:
            value = resources.get(field)
            status = coverage.get(field, {}).get("status")
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or status not in {"MEASURED", "MEASURED_NODE_PAYLOAD_BYTES"}):
                issues.append({"checkpoint": checkpoint_id,
                               "issue": f"cell_resource_unmeasured:{field}"})
            else:
                fields_by_name[field].append((value, checkpoint_id))
                cell_fields[field] = value
        if outcome.get("approval_events_added", 0) or outcome.get("world_receipts_added", 0):
            issues.append({"checkpoint": checkpoint_id, "issue": "cell_added_action_evidence"})
        if not outcome.get("primitive_budget_respected"):
            issues.append({"checkpoint": checkpoint_id, "issue": "primitive_ceiling_exceeded"})
        if not outcome.get("rule_progress_limit_respected"):
            issues.append({"checkpoint": checkpoint_id, "issue": "rule_progress_limit_exceeded"})
        cells_by_checkpoint.setdefault(checkpoint_id, []).append(row)
        cell_rows.append({
            "checkpoint_id": checkpoint_id,
            "checkpoint_digest": row.get("checkpoint_digest"),
            "family": row.get("family"),
            "arm": row.get("arm"),
            "generation": row.get("generation"),
            "world_id": row.get("world_id"),
            "status": outcome.get("status"),
            "score": outcome.get("score"),
            "isolated_worker_wall_time_seconds": outcome.get(
                "isolated_worker_wall_time_seconds"),
            "isolated_worker_peak_rss_bytes": outcome.get(
                "isolated_worker_peak_rss_bytes"),
            "resource_snapshot_sha256": snapshot.get("snapshot_sha256"),
            "approval_events_added": outcome.get("approval_events_added", 0),
            "world_receipts_added": outcome.get("world_receipts_added", 0),
            "primitive_budget_respected": outcome.get("primitive_budget_respected"),
            "rule_progress_limit_respected": outcome.get("rule_progress_limit_respected"),
            "resources": cell_fields,
        })

    expected_ids = set(checkpoint_rows)
    if set(cells_by_checkpoint) != expected_ids:
        for checkpoint_id in sorted(expected_ids - set(cells_by_checkpoint)):
            issues.append({"checkpoint": checkpoint_id, "issue": "no_isolated_cells"})
    for checkpoint_id, rows in cells_by_checkpoint.items():
        if len(rows) != 4:
            issues.append({"checkpoint": checkpoint_id, "issue": "expected_four_world_cells"})
        if len({row.get("world_id") for row in rows}) != len(rows):
            issues.append({"checkpoint": checkpoint_id, "issue": "duplicate_world_cell"})
        if any(row.get("checkpoint_digest") != checkpoint_rows[checkpoint_id]["checkpoint_digest"]
               for row in rows):
            issues.append({"checkpoint": checkpoint_id, "issue": "checkpoint_digest_mismatch"})

    resource_ranges = {}
    for field, values in fields_by_name.items():
        raw_values = [value for value, _ in values]
        low = min(raw_values) if raw_values else None
        high = max(raw_values) if raw_values else None
        resource_ranges[field] = {
            "cell_count": len(values),
            "minimum": low,
            "minimum_checkpoint_ids": sorted({checkpoint_id for value, checkpoint_id in values
                                                if value == low}),
            "maximum": high,
            "maximum_checkpoint_ids": sorted({checkpoint_id for value, checkpoint_id in values
                                                if value == high}),
        }

    missing = audit.get("missing_invention_full_descendants", [])
    expected_total = (audit.get("root_count", 0) + audit.get("passive_descendant_count", 0)
                      + 12)
    return {
        "schema": "p22_current_resource_manifest_v1",
        "status": "PASS_PARTIAL_INCOMPLETE" if not issues else "FAIL",
        "checkpoint_count": len(checkpoint_rows),
        "expected_checkpoint_count": expected_total,
        "missing_checkpoint_count": expected_total - len(checkpoint_rows),
        "missing_invention_full_descendants": missing,
        "isolated_cell_count": len(cell_rows),
        "four_isolated_worlds_per_captured_checkpoint": (
            len(cell_rows) == 4 * len(checkpoint_rows)
            and all(len(rows) == 4 for rows in cells_by_checkpoint.values())),
        "all_cells_completed": all(row["status"] == "COMPLETED" for row in cell_rows),
        "all_resource_fields_measured": not any(
            item["issue"].startswith("cell_resource_unmeasured:") for item in issues),
        "all_resource_snapshots_digest_valid": not any(
            item["issue"] == "cell_snapshot_digest_invalid" for item in issues),
        "approvals_added": sum(row["approval_events_added"] for row in cell_rows),
        "receipts_added": sum(row["world_receipts_added"] for row in cell_rows),
        "validation_accessed": False,
        "heldout_accessed": False,
        "per_field_ceilings_frozen": False,
        "final_manifest_complete": len(checkpoint_rows) == expected_total,
        "resource_ranges": resource_ranges,
        "sources": sources,
        "cells": cell_rows,
        "issues": issues,
    }


def main() -> int:
    result = build()
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "checkpoint_count", "expected_checkpoint_count",
        "missing_checkpoint_count", "isolated_cell_count",
        "four_isolated_worlds_per_captured_checkpoint", "all_cells_completed",
        "all_resource_fields_measured", "all_resource_snapshots_digest_valid",
        "approvals_added", "receipts_added", "validation_accessed",
        "heldout_accessed", "per_field_ceilings_frozen", "issues")}, sort_keys=True))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
