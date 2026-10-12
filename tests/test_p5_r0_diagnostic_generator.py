from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, parse_canonical
from evaluation.p5_r0.diagnostic_generator import (
    DEFAULT_SEED,
    DiagnosticGenerationError,
    build_diagnostic_artifacts,
    write_diagnostic_bundle,
)


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_generator_is_deterministic_and_exactly_bound():
    first = build_diagnostic_artifacts(seed=DEFAULT_SEED)
    second = build_diagnostic_artifacts(seed=DEFAULT_SEED)
    assert first == second
    assert first["split"]["split_digest"].startswith("sha256:")
    assert first["manifest"]["manifest_digest"] == first["bundle_input_manifest"]["commitments"]["manifest_digest"]
    assert first["private_store"]["store_digest"] == first["manifest"]["store_digest"]
    assert first["task_set"]["manifest_digest"] == first["manifest"]["manifest_digest"]
    assert first["task_set"]["case_index_digest"] == first["manifest"]["index_digest"]
    assert first["task_set"]["task_count"] == 144
    assert len(first["task_set"]["control_ids"]) == 11
    assert first["control_commitment"]["task_set_digest"] == first["task_set"]["task_set_digest"]
    assert first["lock_signing_request"]["unsigned_lock_digest"] == first["lock_signing_request"]["unsigned_lock"]["lock_digest"]


def test_public_manifest_has_no_private_truth_fields():
    artifacts = build_diagnostic_artifacts()
    public = artifacts["manifest"]
    private = artifacts["private_store"]
    assert len(public["case_index"]) == 48
    assert len(private["cases"]) == 48
    assert {"truth", "secret_seed", "private_parameters", "private_domain_family"}.isdisjoint(set(_walk(public)))
    assert {"truth", "secret_seed", "private_parameters"}.issubset(set(_walk(private)))


def test_lock_request_is_explicitly_unsigned_and_non_release():
    request = build_diagnostic_artifacts()["lock_signing_request"]
    lock = request["unsigned_lock"]
    assert request["schema"] == "P5R0KMSLockSigningRequestV1"
    assert request["non_release"] is True
    assert request["production_signature_created"] is False
    assert request["cloud_operations"] == []
    assert lock["classification"] == "diagnostic_unsigned_kms_request"
    assert lock["non_release"] is True
    assert lock["signature"] is None
    assert lock["authority_digest"] is None
    assert lock["kms_authority_binding_digest"] is None
    assert request["kms"]["signature_present"] is False


def test_written_bundle_is_canonical_private_and_rerunnable(tmp_path: Path):
    root = tmp_path / "var" / "diagnostic-inputs"
    first = write_diagnostic_bundle(root, repository_root=tmp_path, enforce_var_root=False)
    first_bytes = {path.relative_to(root): path.read_bytes() for path in root.rglob("*.json")}
    second = write_diagnostic_bundle(root, repository_root=tmp_path, enforce_var_root=False)
    second_bytes = {path.relative_to(root): path.read_bytes() for path in root.rglob("*.json")}
    assert first == second
    assert first_bytes == second_bytes
    assert (root / "private-truth/case-store.json").stat().st_mode & 0o777 == 0o400
    assert (root / "public/manifest.json").stat().st_mode & 0o777 == 0o444
    for path, raw in ((path, path.read_bytes()) for path in root.rglob("*.json")):
        assert parse_canonical(raw) == json.loads(raw)
        assert raw == canonical_bytes(json.loads(raw)), path
    assert "private-truth/case-store.json" in first["private_truth_path"]
    assert first["artifacts"]["private_store"]["private"] is True
    assert first["artifacts"]["manifest"]["digest"] == first["manifest_digest"]
    assert first["artifacts"]["private_store"]["digest"] == first["private_store_digest"]
    assert first["artifacts"]["manifest"]["file_digest"].startswith("sha256:")


def test_cli_root_guard_rejects_non_var_output(tmp_path: Path):
    try:
        write_diagnostic_bundle(tmp_path / "not-var-diagnostic")
    except DiagnosticGenerationError as exc:
        assert "under repository var" in str(exc)
    else:  # pragma: no cover - assertion makes this branch explicit
        raise AssertionError("outside-var diagnostic output was accepted")
