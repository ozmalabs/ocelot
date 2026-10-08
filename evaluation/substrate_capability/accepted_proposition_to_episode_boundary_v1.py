#!/usr/bin/env python3
"""Measure whether accepted semantic propositions enter episodic memory."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter

LOCK = ROOT / "evaluation/substrate_capability/accepted_proposition_to_episode_boundary_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/accepted_proposition_to_episode_boundary_v1_raw_20261003.json"
REPEATS = 3
MEMORY_TYPES = (
    "EpisodicEvent", "MemoryContext", "MemorySchema", "Episode",
    "MemoryRetrievalRequest", "RecallCandidate", "RecallOutcome",
)
CASES = (
    ("code_14", "has_secret_code", {"agent": "user", "value": "14"}),
    ("code_29", "has_secret_code", {"agent": "user", "value": "29"}),
    ("gate_open", "state_open", {"agent": "user", "theme": "gate"}),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return {item["path"]: sha(ROOT / item["path"])
            for item in lock["locked_inputs"]}


def lock_errors(actual: dict[str, str]) -> list[str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return [f"source hash mismatch: {item['path']}"
            for item in lock["locked_inputs"]
            if actual.get(item["path"]) != item["sha256"]]


def counts(agent: WorldAdapter) -> dict[str, int]:
    return {kind: len(list(agent.s.nodes(kind)))
            for kind in (*MEMORY_TYPES, "Proposition", "DiscourseEvent")}


def run_one(case, replicate: int) -> dict:
    case_id, predicate, arguments = case
    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    before = counts(agent)
    frame = {
        "communicative_force": "assertion_or_correction",
        "cognitive_goal": "update_common_ground",
        "proposition": {
            "schema": "neutral_proposition_evidence.v1",
            "kind": "explicit_neutral",
            "predicate": predicate,
            "arguments": arguments,
            "polarity": "affirmed",
            "provider": "controlled_semantic_adapter",
            "evidence_id": f"accepted-memory-boundary-{case_id}-{replicate}",
            "commitment_status": "proposed",
            "uptake_signal": "accept",
        },
    }
    result = agent.ingest_semantic_event(frame, provider="controlled_semantic_adapter")
    proposition_result = result["proposition"]
    proposition = proposition_result.get("proposition")
    attrs = dict(agent.s.node(proposition)["attrs"]) if proposition else {}
    # Process a second full native graph pass before checking memory. This is
    # enough for either proposition uptake or episodic binding to fire if the
    # relevant graph patterns exist; neither gets Python-written memory input.
    agent.inner.run_rules()
    after = counts(agent)
    return {
        "case_id": case_id,
        "replicate": replicate,
        "pid": os.getpid(),
        "proposition_supported": proposition_result.get("supported"),
        "commitment_status": attrs.get("commitment_status"),
        "uptake_applied": attrs.get("uptake_applied"),
        "proposition_origin_event": bool(proposition and agent.inner.has_edge(
            proposition, "originated_in", result["discourse_event_id"])),
        "before_counts": before,
        "after_counts": after,
        "memory_counts": {kind: after[kind] for kind in MEMORY_TYPES},
    }


def main() -> int:
    before = source_hashes()
    errors = lock_errors(before)
    rows = [run_one(case, replicate)
            for case in CASES for replicate in range(REPEATS)]
    after = source_hashes()
    if before != after:
        errors.append("locked source changed during run")
    for row in rows:
        if not (row["proposition_supported"] is True
                and row["commitment_status"] == "accepted"
                and row["uptake_applied"] == "accept"
                and row["proposition_origin_event"]):
            errors.append(f"accepted-proposition control failed: {row['case_id']}/{row['replicate']}")
        if any(row["memory_counts"][kind] != 0 for kind in MEMORY_TYPES):
            errors.append(f"unexpected memory node: {row['case_id']}/{row['replicate']}")
    report = {
        "schema": "accepted_proposition_to_episode_boundary_v1",
        "passed_integrity": not errors,
        "integrity_errors": errors,
        "repeat_count_per_case": REPEATS,
        "case_count": len(CASES),
        "row_count": len(rows),
        "locked_inputs": before,
        "post_run_inputs": after,
        "accepted_proposition_count": sum(
            row["commitment_status"] == "accepted" for row in rows),
        "rows_without_episodic_event": sum(
            row["memory_counts"]["EpisodicEvent"] == 0 for row in rows),
        "rows_without_episode": sum(
            row["memory_counts"]["Episode"] == 0 for row in rows),
        "rows_without_recall_request": sum(
            row["memory_counts"]["MemoryRetrievalRequest"] == 0 for row in rows),
        "rows": rows,
        "interpretation": (
            "The semantic adapter explicitly supplies neutral propositions and an accept "
            "signal; native lifecycle rules accept them. Only the semantic ingress and "
            "episodic-memory rules are loaded. No memory event/context/schema/request is "
            "written by the harness. Absence of episodic binding is an integration result, "
            "not a failure of the separately measured structured-memory rules."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"passed_integrity": report["passed_integrity"],
                      "errors": errors, "rows": len(rows),
                      "accepted_propositions": report["accepted_proposition_count"],
                      "without_episode": report["rows_without_episode"],
                      "output": str(OUT)}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
