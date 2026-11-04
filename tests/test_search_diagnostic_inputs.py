"""P23.01: hash-bound, training-only, read-only diagnostic inventory."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from evaluation.process_mastery.linear_p22_v1 import allocation


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/research/engine_substrate/COGNITION_SEARCH_DIAGNOSIS_CONTRACT.md"
TABLE_HEADER = "| Path | SHA-256 | Class | Status | Branch disposition | Parent artifact | Training draws |"
# P23 froze its source/contract inputs immediately before the P26 search
# repairs changed two of these files.  The source snapshot remains available
# as an immutable Git tree even though the current checkout has advanced.
P23_SOURCE_SNAPSHOT = "8b3bc7c0a61f0aab84544075e649b6292171d2a8"


def _rows():
    text = CONTRACT.read_text()
    table = text.split(TABLE_HEADER, 1)[1]
    rows = []
    for line in table.splitlines():
        match = re.fullmatch(
            r"\| `([^`]+)` \| `([0-9a-f]{64})` \| ([^|]+) \| ([^|]+) \| ([^|]+) \| (—|`[^`]+`) \| ([^|]+) \|",
            line,
        )
        if match:
            path, digest, kind, status, disposition, parent, draws = match.groups()
            rows.append({
                "path": path,
                "sha256": digest,
                "class": kind,
                "status": status,
                "disposition": disposition,
                "parent": parent.strip("`") if parent != "—" else None,
                "draws": draws.strip(),
            })
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _attempt_count(snapshot: dict) -> int:
    return int(snapshot.get("node_counts", {}).get("OpenProcessSearchAttempt", 0))


def test_checkpoint_inputs_are_hash_bound():
    rows = _rows()
    assert len(rows) >= 40
    assert len({row["path"] for row in rows}) == len(rows)
    for row in rows:
        path = ROOT / row["path"]
        assert path.is_file(), row["path"]
        current_digest = _sha256(path)
        if current_digest == row["sha256"]:
            continue
        # A later, separately versioned implementation may legitimately
        # supersede a frozen source input. Validate the original bytes from
        # the P23 snapshot instead of comparing the historical hash to the
        # new working-tree version.
        snapshot = subprocess.run(
            ["git", "show", f"{P23_SOURCE_SNAPSHOT}:{row['path']}"],
            cwd=ROOT, check=False, capture_output=True,
        )
        assert snapshot.returncode == 0, row["path"]
        assert _sha256_bytes(snapshot.stdout) == row["sha256"], row["path"]


def test_restored_branch_work_not_double_counted():
    rows = [row for row in _rows() if row["class"] == "branch"]
    unique = [row for row in rows if row["disposition"] in {
        "unique branch", "completed; no candidate"}]
    replay = [row for row in rows if row["disposition"] == "duplicate/replay"]
    interrupted = [row for row in rows if row["disposition"].startswith("interrupted;")]
    assert unique and replay and interrupted

    increments = []
    for row in unique:
        artifact = json.loads((ROOT / row["path"]).read_text())
        assert artifact["status"] in {"COMPLETED", "NO_CANDIDATE_FIRST_TRIAL"}
        cumulative = _attempt_count(artifact["resource_snapshot"])
        parent_raw = artifact["parent_checkpoint"].get("resource_snapshot_json")
        assert parent_raw, row["path"]
        inherited = _attempt_count(json.loads(parent_raw))
        assert cumulative >= inherited, row["path"]
        increments.append(cumulative - inherited)

    # Replays and invalid interrupted allocations remain in the inventory but
    # cannot inflate completed independent branch work.
    assert all(row["status"] == "COMPLETED" for row in replay)
    assert all(row["status"] == "INTERRUPTED_INVALID_ALLOCATION" for row in interrupted)
    assert sum(increments) > 0


def test_diagnostic_has_no_agent_output_channel():
    text = CONTRACT.read_text().lower()
    assert "read-only" in text
    assert "no diagnostic witness" in text
    assert "may be emitted into or consumed by an agent graph" in text
    assert "candidate validator" in text and "world adapter" in text
    assert "mutation command" in text


def test_heldout_ids_rejected():
    rows = [row for row in _rows() if row["class"] == "branch"]
    plan = allocation()
    training_ids = {
        world_id
        for family_rows in plan["training_world_ids_by_family"].values()
        for world_id in family_rows
    }
    forbidden_ids = {
        world_id
        for split_key in ("validation_world_ids_by_family", "world_ids_by_family")
        for family_rows in plan[split_key].values()
        for world_id in family_rows
    }
    assert training_ids.isdisjoint(forbidden_ids)
    training_prefixes = (
        "p22:d4-v2:train:",
        "p22:loopover-v2:train:",
    )
    for row in rows:
        if row["disposition"].startswith("interrupted;"):
            continue
        artifact = json.loads((ROOT / row["path"]).read_text())
        ids = set(artifact.get("training_world_ids", []))
        assert ids
        # Later development draws are intentionally outside the preregistered
        # 0..199 allocation, but retain an explicit `train` split identity.
        assert all(world_id.startswith(training_prefixes) for world_id in ids)
        assert ids.isdisjoint(forbidden_ids)
        assert artifact.get("validation_world_ids", []) == []
