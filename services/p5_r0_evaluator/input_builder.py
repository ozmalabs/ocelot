"""Canonical deterministic input builder and its disclosed source binding.

This is a project-controlled implementation identity, not an execution authority.
The binding is committed by manifests/locks/evidence so source drift fails closed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from .canonical import digest

INPUT_BUILDER_SCHEMA = "P5R0InputBuilderBindingV1"
INPUT_BUILDER_IMPLEMENTATION = "services.p5_r0_evaluator.input_builder.deterministic_input_builder"
INPUT_BUILDER_VERSION = "P5R0InputBuilderV1"
INPUT_BUILDER_SOURCE_PATH = "services/p5_r0_evaluator/input_builder.py"


def deterministic_input_builder(input_seed_digest: str) -> Mapping[str, Any]:
    """Return the complete deterministic public input for a seed commitment."""
    if not isinstance(input_seed_digest, str) or not input_seed_digest.startswith("sha256:"):
        raise ValueError("input seed digest is required")
    return {"schema": "P5R0DeterministicInputV1", "input_seed_digest": input_seed_digest}


def input_builder_binding(repository_root: Path | None = None) -> dict[str, Any]:
    root = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    source = root / INPUT_BUILDER_SOURCE_PATH
    if not source.is_file():
        raise ValueError("input-builder source is missing")
    source_digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    value = {
        "schema": INPUT_BUILDER_SCHEMA,
        "implementation": INPUT_BUILDER_IMPLEMENTATION,
        "version": INPUT_BUILDER_VERSION,
        "source_path": INPUT_BUILDER_SOURCE_PATH,
        "source_digest": source_digest,
    }
    value["binding_digest"] = digest({key: child for key, child in value.items() if key != "binding_digest"})
    return value


def validate_input_builder_binding(value: Mapping[str, Any], repository_root: Path | None = None) -> dict[str, Any]:
    expected = input_builder_binding(repository_root)
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise ValueError("input-builder implementation binding drift")
    return dict(value)


__all__ = [
    "INPUT_BUILDER_IMPLEMENTATION", "INPUT_BUILDER_SCHEMA", "INPUT_BUILDER_SOURCE_PATH",
    "INPUT_BUILDER_VERSION", "deterministic_input_builder", "input_builder_binding",
    "validate_input_builder_binding",
]
