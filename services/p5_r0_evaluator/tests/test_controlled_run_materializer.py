from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from evaluation.p0a.canonical import canonical_bytes, sha256
from services.p5_r0_evaluator.deploy.controlled_run_materializer import (
    DEFAULT_GENERATED_ROOT,
    ControlledRunMaterializationError,
    materialize,
    validate_artifact_commitments,
    validate_authority_semantics,
    validate_generator_provenance,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_materializer_emits_canonical_blocked_review_manifest(tmp_path: Path):
    manifest = materialize()
    output = tmp_path / "manifest.json"
    output.write_bytes(canonical_bytes(manifest))

    assert output.read_bytes() == canonical_bytes(manifest)
    assert manifest["status"] == "blocked_pending_signed_environment_operations"
    assert manifest["custody"]["all_inputs_project_generated_or_self_custodied"] is True
    assert manifest["custody"]["independent_authority_claim"] is False
    assert manifest["time_seed_algorithm"]["materializer_status"] == "disclosed_only_no_timing_record_consumed"
    assert manifest["time_seed_algorithm"]["public_bindings"] == ["timing_record_digest", "input_seed_digest", "input_digest", "input_builder_implementation", "input_builder_version", "input_builder_source_digest", "time_seed_algorithm_source_digest"]
    assert manifest["input_builder_binding"]["implementation"] == "services.p5_r0_evaluator.input_builder.deterministic_input_builder"
    assert manifest["input_builder_binding"]["version"] == "P5R0InputBuilderV1"
    assert manifest["input_builder_binding"]["source_digest"].startswith("sha256:")
    assert manifest["time_seed_algorithm"]["source_digest"].startswith("sha256:")
    assert manifest["time_seed_algorithm"]["algorithm"]["input_value"] == "input_builder(input_seed_digest)"
    assert manifest["review_only_boundary"]["generated_controlled_run_inputs"] is True
    assert manifest["review_only_boundary"]["fabricated_evidence"] is False
    assert manifest["review_only_boundary"]["execution_evidence_present"] is False
    assert len(manifest["artifact_commitments"]["artifacts"]) == 11
    assert len(manifest["closure_commitments"]) == 2
    assert manifest["review_only_boundary"]["cloud_operations"] == []
    assert manifest["review_only_boundary"]["commands"] == []
    assert all(not item["enabled"] for item in manifest["signed_environment_operations_pending"]["RS-069"])
    assert all(not item["enabled"] for item in manifest["signed_environment_operations_pending"]["RS-063_future_mutating_steps"])


def test_altered_seed_algorithm_is_rejected():
    provenance = _load(DEFAULT_GENERATED_ROOT / "public/generator-provenance.json")
    provenance["generator"]["split_seed"] = "attacker-split"

    with pytest.raises(ControlledRunMaterializationError, match="seed algorithm drift"):
        validate_generator_provenance(provenance)




def test_altered_input_builder_or_time_seed_source_is_rejected():
    provenance = deepcopy(_load(DEFAULT_GENERATED_ROOT / "public/generator-provenance.json"))
    provenance["input_builder_binding"]["source_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ControlledRunMaterializationError, match="source identity commitment drift"):
        validate_generator_provenance(provenance)

    provenance = deepcopy(_load(DEFAULT_GENERATED_ROOT / "public/generator-provenance.json"))
    provenance["time_seed_algorithm_binding"]["source_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ControlledRunMaterializationError, match="source identity commitment drift"):
        validate_generator_provenance(provenance)
    index = _load(DEFAULT_GENERATED_ROOT / "artifact-index.json")
    index = deepcopy(index)
    index["artifacts"]["manifest"]["file_digest"] = "sha256:" + "0" * 64

    index["index_digest"] = sha256({key: value for key, value in index.items() if key != "index_digest"})

    with pytest.raises(ControlledRunMaterializationError, match="artifact digest drift: manifest"):
        validate_artifact_commitments(index, DEFAULT_GENERATED_ROOT)


def test_independent_authority_claim_is_rejected():
    proposal = _load(DEFAULT_GENERATED_ROOT / "public/rs-068-authority-binding-proposal.json")
    proposal = deepcopy(proposal)
    proposal["authority"]["authority_id"] = "independent/evaluator/authority"

    with pytest.raises(ControlledRunMaterializationError, match="self-custodied"):
        validate_authority_semantics(proposal)


def test_manifest_retains_self_custodied_not_independent_semantics():
    manifest = materialize()
    authority = manifest["authority_commitment"]
    assert authority["custody"] == "self_custodied"
    assert authority["independent_authority_claim"] is False
    assert authority["independent_evaluator_required"] is False
    assert authority["authority_binding_digest"] is None
    assert authority["signature_present"] is False
