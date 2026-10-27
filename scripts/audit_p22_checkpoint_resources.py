"""Read-only resource/provenance audit for currently captured P22 checkpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

# Make direct script execution from any working directory resolve the repo's
# top-level packages just like `python -m` does.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.checkpoint_world_adapter import CheckpointWorldAdapter
from evaluation.process_mastery.linear_p22_v1 import _checkpoint
from evaluation.process_mastery.analyze_linear_p22_v1 import RESOURCE_FIELDS
from evaluation.process_mastery.p22_resource_accounting import (
    analyzer_resource_record,
    resource_snapshot_digest_valid,
)

RESULTS = ROOT / "evaluation/process_mastery/results"
ROOT_FILES = {
    family: RESULTS / f"p22_four_arm_checkpoint_roots_{family}_0520.json"
    for family in ("d4", "loopover")
}
PASSIVE_FILE = RESULTS / "p22_passive_control_training_lineages_0600_0602.json"
ADOPTION_FILES = {
    "d4:invention_only:g1": "p22_approved_candidate_d4_0962_0972.json",
    "d4:invention_only:g2": "p22_approved_candidate_d4_g1_0818_0821.json",
    "loopover:invention_only:g1": "p22_approved_candidate_loopover_0951_0953.json",
    "loopover:invention_only:g2": "p22_approved_candidate_loopover_invention_g1_0114_0117.json",
    "d4:full:g1": "p22_approved_candidate_d4_full_0985_0986.json",
    "d4:full:g2": "p22_approved_candidate_d4_full_g1_0002_0003.json",
    "loopover:full:g1": "p22_approved_candidate_loopover_full_g0_0034_0035.json",
    "loopover:full:g2": "p22_approved_candidate_loopover_full_g1_0174_0177.json",
}
EXPECTED_ACTIVE = {
    "d4:invention_only": (1, 2, 3),
    "d4:full": (1, 2, 3),
    "loopover:invention_only": (1, 2, 3),
    "loopover:full": (1, 2, 3),
}


def _read(path: Path) -> tuple[dict, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict[str, Any]:
    sources: dict[str, str] = {}
    records: list[tuple[str, Any, dict]] = []
    issues: list[dict[str, str]] = []
    roots: dict[str, Any] = {}

    for family, path in ROOT_FILES.items():
        payload, digest = _read(path)
        sources[str(path.relative_to(ROOT))] = digest
        for arm, row in payload["arms"].items():
            checkpoint = _checkpoint(row["generation_zero_checkpoint"])
            key = f"{family}:{arm}:g0"
            roots[f"{family}:{arm}"] = checkpoint
            records.append((key, checkpoint, row["generation_zero_checkpoint"]))

    passive_payload, digest = _read(PASSIVE_FILE)
    sources[str(PASSIVE_FILE.relative_to(ROOT))] = digest
    passive_counts = {}
    for family, family_row in passive_payload["families"].items():
        for arm in ("unchanged", "adaptive_only"):
            lineage = family_row["arms"][arm]["lineages"]
            passive_counts[f"{family}:{arm}"] = len(lineage)
            parent = roots[f"{family}:{arm}"].checkpoint_digest
            for row in lineage:
                checkpoint = _checkpoint(row)
                key = f"{family}:{arm}:g{checkpoint.generation}"
                records.append((key, checkpoint, row))
                if checkpoint.parent_digest != parent:
                    issues.append({"checkpoint": key, "issue": "passive_parent_digest"})
                if checkpoint.approval_id or checkpoint.receipt_id:
                    issues.append({"checkpoint": key, "issue": "passive_has_action_evidence"})
                parent = checkpoint.checkpoint_digest

    active_counts = {key: 0 for key in EXPECTED_ACTIVE}
    active_parent: dict[str, Any] = {
        "d4:invention_only:g1": roots["d4:invention_only"],
        "d4:full:g1": roots["d4:full"],
        "loopover:invention_only:g1": roots["loopover:invention_only"],
        "loopover:full:g1": roots["loopover:full"],
    }
    for lineage_key, filename in ADOPTION_FILES.items():
        path = RESULTS / filename
        payload, digest = _read(path)
        sources[str(path.relative_to(ROOT))] = digest
        adoption = payload.get("simulated_adoption") or {}
        raw = adoption.get("child_checkpoint") or adoption.get("generation_2_checkpoint")
        if not raw:
            issues.append({"checkpoint": lineage_key, "issue": "missing_adopted_checkpoint"})
            continue
        checkpoint = _checkpoint(raw)
        family, arm, generation_text = lineage_key.split(":")
        generation = int(generation_text[1:])
        base_key = f"{family}:{arm}"
        active_counts[base_key] += 1
        parent = active_parent.get(lineage_key)
        if parent is None or checkpoint.parent_digest != parent.checkpoint_digest:
            issues.append({"checkpoint": lineage_key, "issue": "active_parent_digest"})
        if checkpoint.generation != generation:
            issues.append({"checkpoint": lineage_key, "issue": "active_generation"})
        if (adoption.get("approval_status") != "consumed"
                or not adoption.get("approval_id")
                or adoption.get("receipt_status") != "verified"
                or not adoption.get("receipt_id")):
            issues.append({"checkpoint": lineage_key, "issue": "approval_or_receipt_unverified"})
        active_parent[f"{family}:{arm}:g{generation + 1}"] = checkpoint
        records.append((lineage_key, checkpoint, raw))

    ids: set[str] = set()
    checkpoint_rows = []
    field_samples: dict[str, list[tuple[str, float | int]]] = {
        field: [] for field in RESOURCE_FIELDS
    }
    for key, checkpoint, raw in records:
        if checkpoint.checkpoint_id in ids:
            issues.append({"checkpoint": key, "issue": "duplicate_checkpoint_id"})
        ids.add(checkpoint.checkpoint_id)
        if not CheckpointWorldAdapter._checkpoint_digest_valid(checkpoint):
            issues.append({"checkpoint": key, "issue": "checkpoint_digest_invalid"})
        snapshot = json.loads(checkpoint.resource_snapshot_json)
        if not resource_snapshot_digest_valid(snapshot):
            issues.append({"checkpoint": key, "issue": "resource_snapshot_digest_invalid"})
        measured = analyzer_resource_record(
            snapshot,
            cumulative_primitive_work=checkpoint.cumulative_primitive_work,
            wall_time_seconds=snapshot["runtime_counters"]["wall_time_seconds"],
        )
        measured_count = 0
        for field in RESOURCE_FIELDS:
            evidence = measured["resource_measurements"].get(field, {})
            if (measured["resources"].get(field) is not None
                    and evidence.get("status") in {
                        "MEASURED", "MEASURED_NODE_PAYLOAD_BYTES"}):
                measured_count += 1
                value = measured["resources"][field]
                if (isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)):
                    issues.append({"checkpoint": key,
                                   "issue": f"resource_non_numeric:{field}"})
                else:
                    field_samples[field].append((checkpoint.checkpoint_id, value))
            else:
                issues.append({"checkpoint": key, "issue": f"resource_unmeasured:{field}"})
        checkpoint_rows.append({
            "lineage": key,
            "checkpoint_id": checkpoint.checkpoint_id,
            "generation": checkpoint.generation,
            "checkpoint_digest": checkpoint.checkpoint_digest,
            "resource_snapshot_sha256": snapshot.get("snapshot_sha256"),
            "cumulative_primitive_work": checkpoint.cumulative_primitive_work,
            "measured_resource_fields": measured_count,
        })

    observed_resource_ranges = {}
    for field, samples in field_samples.items():
        values = [value for _, value in samples]
        minimum = min(values) if values else None
        maximum = max(values) if values else None
        observed_resource_ranges[field] = {
            "measured_count": len(samples),
            "minimum": minimum,
            "minimum_checkpoint_ids": [checkpoint_id for checkpoint_id, value in samples
                                       if value == minimum],
            "maximum": maximum,
            "maximum_checkpoint_ids": [checkpoint_id for checkpoint_id, value in samples
                                       if value == maximum],
        }

    observed = {(row["lineage"].rsplit(":g", 1)[0], row["generation"])
               for row in checkpoint_rows}
    missing = [f"{arm_key}:g{generation}"
               for arm_key, generations in EXPECTED_ACTIVE.items()
               for generation in generations if (arm_key, generation) not in observed]
    complete = not missing and not issues
    return {
        "schema": "p22_checkpoint_resource_readiness_audit_v1",
        "status": "PASS_COMPLETE" if complete else "PASS_PARTIAL_INCOMPLETE" if not issues else "FAIL",
        "read_only": True,
        "checkpoint_count": len(checkpoint_rows),
        "unique_checkpoint_ids": len(ids),
        "root_count": 8,
        "passive_descendant_count": sum(passive_counts.values()),
        "approved_invention_full_descendant_count": sum(active_counts.values()),
        "resource_fields_per_checkpoint": len(RESOURCE_FIELDS),
        "all_captured_checkpoint_and_snapshot_digests_valid": not any(
            row["issue"].endswith("digest_invalid") for row in issues),
        "all_captured_resource_fields_measured": not any(
            row["issue"].startswith("resource_unmeasured:") for row in issues),
        "missing_invention_full_descendants": missing,
        "per_field_ceilings_frozen": False,
        "isolated_final_wall_time_panel_complete": False,
        "heldout_access_allowed": False,
        "sources": sources,
        "observed_resource_ranges": observed_resource_ranges,
        "checkpoints": checkpoint_rows,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="evaluation/process_mastery/results/p22_checkpoint_resource_audit_20261025.json")
    args = parser.parse_args()
    result = audit()
    path = Path(args.output)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "checkpoint_count", "unique_checkpoint_ids", "root_count",
        "passive_descendant_count", "approved_invention_full_descendant_count",
        "resource_fields_per_checkpoint", "all_captured_checkpoint_and_snapshot_digests_valid",
        "all_captured_resource_fields_measured", "missing_invention_full_descendants",
        "per_field_ceilings_frozen", "isolated_final_wall_time_panel_complete",
        "heldout_access_allowed", "issues")}, sort_keys=True))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
