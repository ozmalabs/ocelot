#!/usr/bin/env python3
"""Small source-locked behavioral probe of the explicit semantic ingress."""
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

LOCK = ROOT / "evaluation/substrate_capability/semantic_ingress_contract_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/semantic_ingress_contract_v1_raw_20261003.json"
REPEATS = 3


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


def graph_counts(agent: WorldAdapter) -> dict[str, int]:
    types = ("SemanticEventFrame", "CommunicationInterpretation",
             "DiscourseEvent", "Proposition", "PropositionEvidence",
             "PropositionArgument")
    return {kind: len(list(agent.s.nodes(kind))) for kind in types}


def new_agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    return agent


def run_one(condition: str, replicate: int) -> dict:
    agent = new_agent()
    before = graph_counts(agent)
    frame = {
        "communicative_force": "assertion_or_correction",
        "cognitive_goal": "update_common_ground",
    }
    if condition == "valid_proposed":
        frame["proposition"] = {
            "schema": "neutral_proposition_evidence.v1",
            "kind": "explicit_neutral",
            "predicate": "state_open",
            "arguments": {"theme": "gate"},
            "polarity": "affirmed",
            "provider": "controlled_adapter",
            "evidence_id": f"semantic-ingress-{condition}-{replicate}",
            "commitment_status": "proposed",
        }
    elif condition == "invalid_text_field":
        frame["proposition"] = {
            "schema": "neutral_proposition_evidence.v1",
            "kind": "explicit_neutral",
            "predicate": "state_open",
            "arguments": {"theme": "gate"},
            "polarity": "affirmed",
            "provider": "controlled_adapter",
            "evidence_id": f"semantic-ingress-{condition}-{replicate}",
            "commitment_status": "proposed",
            "text": "The gate is open.",
        }

    error = None
    result = None
    try:
        payload = "The gate is open." if condition == "raw_text_frame" else frame
        result = agent.ingest_semantic_event(payload, provider="controlled_adapter")
    except (TypeError, ValueError) as exc:
        error = type(exc).__name__

    after = graph_counts(agent)
    proposition = (result or {}).get("proposition") or {}
    prop_id = proposition.get("proposition")
    prop_attrs = (dict(agent.s.node(prop_id)["attrs"]) if prop_id else {})
    evidence_present = bool(prop_id and list(
        agent.inner.neighbours(prop_id, "evidenced_by")))
    origin_present = bool(prop_id and list(
        agent.inner.neighbours(prop_id, "originated_in")))
    accepted_edge = bool(prop_id and result and agent.inner.has_edge(
        result["discourse_state_id"], "accepted_claim", prop_id))
    return {
        "condition": condition,
        "replicate": replicate,
        "pid": os.getpid(),
        "error_type": error,
        "bridge_supported": proposition.get("supported"),
        "bridge_reason": proposition.get("reason"),
        "commitment_status": prop_attrs.get("commitment_status"),
        "evidence_present": evidence_present,
        "origin_event_present": origin_present,
        "accepted_claim_edge": accepted_edge,
        "before_counts": before,
        "after_counts": after,
        "proposition_count_delta": after["Proposition"] - before["Proposition"],
    }


def main() -> int:
    locked = source_hashes()
    errors = lock_errors(locked)
    rows = [run_one(condition, i)
            for condition in ("valid_proposed", "invalid_text_field", "raw_text_frame")
            for i in range(REPEATS)]
    after_hashes = source_hashes()
    if locked != after_hashes:
        errors.append("locked source changed during run")
    for row in rows:
        c = row["condition"]
        if c == "valid_proposed":
            if not (row["bridge_supported"] is True
                    and row["commitment_status"] == "proposed"
                    and row["evidence_present"] and row["origin_event_present"]
                    and not row["accepted_claim_edge"]
                    and row["proposition_count_delta"] == 1):
                errors.append(f"valid proposition contract failed at replicate {row['replicate']}")
        elif c == "invalid_text_field":
            if not (row["bridge_supported"] is False
                    and row["proposition_count_delta"] == 0):
                errors.append(f"invalid proposition was not rejected at replicate {row['replicate']}")
        elif not (row["error_type"] == "TypeError"
                  and row["after_counts"] == row["before_counts"]):
            errors.append(f"raw text frame was not rejected without mutation at replicate {row['replicate']}")
    report = {
        "schema": "semantic_ingress_contract_v1",
        "passed": not errors,
        "errors": errors,
        "repeat_count_per_condition": REPEATS,
        "locked_inputs": locked,
        "post_run_inputs": after_hashes,
        "rows": rows,
        "interpretation": (
            "Measures explicit neutral semantic-event ingress and its rejection boundary. "
            "The valid proposition is supplied in structured form by a controlled adapter; "
            "this is not a natural-language extraction or truth-verification test."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "errors": errors,
                      "output": str(OUT), "rows": len(rows)}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
