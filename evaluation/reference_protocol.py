"""Runnable, non-scoring adapters for Phase 8 reference collection.

This module creates protocol envelopes and validates externally collected
observations.  It never turns missing model or human runs into scores.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from evaluation.comparative_release_gate import (
    BASELINES,
    CORPUS_PROTOCOL_ID,
    REFERENCE_PROTOCOLS,
)
from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase8_corpus_runner import PROTOCOL_ID, scorecard_to_dict, unrun_scorecard


REFERENCE_RUN_SCHEMA = "phase8_reference_run.v1"


def reference_run_scaffold(system: str, corpus: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Emit a ready-to-fill collection envelope with no inferred result."""
    if system not in BASELINES:
        raise ValueError(f"unknown reference system: {system}")
    corpus = load_corpus() if corpus is None else corpus
    protocol = REFERENCE_PROTOCOLS[system]
    return {
        "schema": REFERENCE_RUN_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "corpus_protocol_id": CORPUS_PROTOCOL_ID,
        "system": system,
        "collection_status": "unavailable",
        "adapter_entrypoint": protocol["adapter_entrypoint"],
        "collection_mode": protocol["collection_mode"],
        "required_observation": protocol["required_observation"],
        "annotation_source": protocol["annotation_source"],
        "case_ids": [event["id"] for event in corpus["events"]],
        "observations": [],
        "scorecard": scorecard_to_dict(unrun_scorecard(system)),
        "notes": "Populate only from an actually executed adapter or human session; do not infer scores.",
    }


def validate_reference_observations(envelope: Mapping[str, Any]) -> list[str]:
    """Validate case binding without scoring free-form outputs."""
    errors: list[str] = []
    system = str(envelope.get("system", ""))
    if system not in BASELINES:
        errors.append(f"unknown reference system: {system}")
    expected = set(envelope.get("case_ids", ()))
    observed = envelope.get("observations", ())
    if not isinstance(observed, list):
        return errors + ["observations must be a list"]
    seen = [str(item.get("case_id", "")) for item in observed if isinstance(item, dict)]
    if len(seen) != len(observed):
        errors.append("every observation must be an object with case_id")
    if len(seen) != len(set(seen)):
        errors.append("duplicate case_id observations")
    unknown = sorted(set(seen) - expected)
    if unknown:
        errors.append(f"observations contain unknown case IDs: {unknown}")
    return errors


def write_reference_scaffold(system: str, path: Path) -> dict[str, Any]:
    result = reference_run_scaffold(system)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a Phase 8 reference-run envelope")
    parser.add_argument("system", choices=BASELINES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = write_reference_scaffold(args.system, args.output)
    print(json.dumps({"output": str(args.output), "status": result["collection_status"], "cases": len(result["case_ids"])}))
