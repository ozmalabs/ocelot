"""Measure isolated resources for P22 checkpoints added after the 96-cell panel."""
from __future__ import annotations

import hashlib
import gzip
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.process_mastery.checkpoint_world_adapter import CheckpointExpression
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2, generate_loopover_world_v2,
)
from evaluation.process_mastery.linear_p22_v1 import _checkpoint
from evaluation.process_mastery.p22_checkpoint_panel import score_checkpoint_world_isolated
from evaluation.process_mastery.p22_resource_accounting import (
    analyzer_resource_record, resource_snapshot_digest_valid,
)
from evaluation.process_mastery.analyze_linear_p22_v1 import RESOURCE_FIELDS

RESULTS = ROOT / "evaluation/process_mastery/results"
OUTPUT = RESULTS / "p22_resource_panel_new_approved_checkpoints_0609_0612_0622_0625.json.gz"
RESOURCE_AUDIT = RESULTS / "p22_checkpoint_resource_audit_20261025.json"
PRIOR_PANEL = RESULTS / "p22_resource_panel_existing_checkpoints_0609_0612_0622_0625.json.gz"
CHECKPOINT_SOURCES = {
    "p22-d4-g2-2d2cb9ecda29": (
        "p22_approved_candidate_d4_full_g1_0002_0003.json", "d4", (609, 610, 611, 612)),
    "p22-loopover-g1-c9f470ba1639": (
        "p22_approved_candidate_loopover_full_g0_0034_0035.json", "loopover",
        (622, 623, 624, 625)),
}
GENERATORS = {"d4": generate_d4_world_v2, "loopover": generate_loopover_world_v2}


def _read(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _child(payload: dict) -> dict:
    adoption = payload.get("simulated_adoption") or {}
    raw = adoption.get("child_checkpoint") or adoption.get("generation_2_checkpoint")
    if not isinstance(raw, dict):
        raise ValueError("approved result lacks its captured child checkpoint")
    checkpoint = _checkpoint(raw)
    return asdict(checkpoint)


def run() -> dict:
    audit, audit_sha = _read(RESOURCE_AUDIT)
    prior_bytes = PRIOR_PANEL.read_bytes()
    prior = json.loads(__import__("gzip").decompress(prior_bytes))
    if audit.get("issues") or not audit.get("all_captured_checkpoint_and_snapshot_digests_valid"):
        raise ValueError("current checkpoint provenance audit is not clean")
    if prior.get("status") != "DEVELOPMENT_ONLY" or prior.get("heldout_accessed") is not False:
        raise ValueError("prior panel is not a training-only resource panel")

    checkpoint_ids = {row["checkpoint_id"] for row in audit["checkpoints"]}
    prior_ids = {row["checkpoint_id"] for row in prior["rows"]}
    expected_ids = set(CHECKPOINT_SOURCES)
    if checkpoint_ids - prior_ids != expected_ids:
        raise ValueError("prior panel gap does not match the two newly approved checkpoints")

    sources = {
        str(RESOURCE_AUDIT.relative_to(ROOT)): audit_sha,
        str(PRIOR_PANEL.relative_to(ROOT)): hashlib.sha256(prior_bytes).hexdigest(),
    }
    rows = []
    for checkpoint_id, (filename, family, draws) in CHECKPOINT_SOURCES.items():
        path = RESULTS / filename
        payload, digest = _read(path)
        sources[str(path.relative_to(ROOT))] = digest
        checkpoint_record = _child(payload)
        checkpoint = CheckpointExpression(**checkpoint_record)
        if checkpoint.checkpoint_id != checkpoint_id:
            raise ValueError("checkpoint identity differs from the registered panel gap")
        if not any(row["checkpoint_id"] == checkpoint_id
                   and row["checkpoint_digest"] == checkpoint.checkpoint_digest
                   for row in audit["checkpoints"]):
            raise ValueError("checkpoint digest is not covered by the current audit")

        for draw in draws:
            generator = GENERATORS[family]
            world = agent_view(generator(split="train", draw=draw))
            outcome = score_checkpoint_world_isolated(
                checkpoint_record, world,
                cumulative_primitive_ceiling=600_000,
                native_rule_progress_ceiling=20_000,
                allow_heldout_evaluation=False,
                scoring_policy_profile="p22_frozen_process_scoring_v1")
            snapshot = outcome.get("resource_snapshot")
            if not isinstance(snapshot, dict) or not resource_snapshot_digest_valid(snapshot):
                raise RuntimeError("isolated cell returned an invalid resource snapshot")
            measured = analyzer_resource_record(
                snapshot,
                cumulative_primitive_work=outcome.get("cumulative_primitive_work"),
                wall_time_seconds=snapshot["runtime_counters"]["wall_time_seconds"])
            missing = [field for field in RESOURCE_FIELDS
                       if measured["resources"].get(field) is None
                       or measured["resource_measurements"].get(field, {}).get("status")
                       not in {"MEASURED", "MEASURED_NODE_PAYLOAD_BYTES"}]
            if missing:
                raise RuntimeError(f"isolated cell lacks measured fields: {missing}")
            if outcome.get("approval_events_added") or outcome.get("world_receipts_added"):
                raise RuntimeError("resource scoring unexpectedly added approval or receipt")
            rows.append({
                "checkpoint_id": checkpoint_id,
                "checkpoint_digest": checkpoint.checkpoint_digest,
                "family": family,
                "generation": checkpoint.generation,
                "world_id": world["world_id"],
                "draw": draw,
                "outcome": outcome,
            })

    return {
        "schema": "p22_new_checkpoint_isolated_resource_panel_v1",
        "status": "DEVELOPMENT_ONLY_PARTIAL",
        "split": "training",
        "heldout_accessed": False,
        "validation_accessed": False,
        "scoring_policy_profile": "p22_frozen_process_scoring_v1",
        "cumulative_primitive_ceiling": 600_000,
        "native_rule_progress_ceiling": 20_000,
        "prior_panel_gap_checkpoint_count": len(expected_ids),
        "checkpoint_count": len(expected_ids),
        "cell_count": len(rows),
        "all_cells_completed": all(row["outcome"].get("status") == "COMPLETED" for row in rows),
        "all_resource_fields_measured": True,
        "all_snapshots_digest_valid": True,
        "approvals_added": 0,
        "receipts_added": 0,
        "sources": sources,
        "rows": rows,
    }


def main() -> int:
    result = run()
    raw = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
    OUTPUT.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    print(json.dumps({key: result[key] for key in (
        "status", "checkpoint_count", "cell_count", "all_cells_completed",
        "all_resource_fields_measured", "all_snapshots_digest_valid",
        "approvals_added", "receipts_added", "heldout_accessed")}, sort_keys=True))
    return 0 if result["all_cells_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
