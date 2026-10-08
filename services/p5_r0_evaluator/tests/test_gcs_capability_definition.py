from copy import deepcopy
import json
from pathlib import Path

import pytest

from evaluation.p0a.canonical import sha256
from services.p5_r0_evaluator.deploy.gcs_capability_definition import (
    DEFAULT_DEFINITION,
    GCSCapabilityDefinitionError,
    validate_definition,
)

ROOT = Path(__file__).resolve().parents[3]


def _definition() -> dict:
    return json.loads(DEFAULT_DEFINITION.read_text(encoding="utf-8"))


def _write_tampered(tmp_path: Path, value: dict) -> Path:
    value["definition_digest"] = sha256({key: item for key, item in value.items() if key != "definition_digest"})
    path = tmp_path / "gcs-capability-definition.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_definition_binds_exact_scope_wif_credential_chain_and_r18r12():
    report = validate_definition()
    assert report["project_id"] == "ocelot-proof"
    assert report["bucket"] == "p5-evaluator-ocelot-proof-141633828616"
    assert report["run_id"] == "rs069r18r13-op4-04a98e3e"
    assert report["object_count"] == 11
    assert report["generation_precondition"] == 0
    assert report["wif_principal"].endswith("394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c")
    assert report["cloud_operations"] == []
    assert _definition()["capability_service_account"]["email"] == "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com"
    assert _definition()["iam"]["remove_broad_grant"]["member"] == "serviceAccount:p5-evaluator@ocelot-proof.iam.gserviceaccount.com"
    assert report["apply_performed"] is False


def test_definition_rejects_wif_principal_or_condition_drift(tmp_path):
    value = _definition()
    value["wif_binding"]["principal"] = value["wif_binding"]["principal"].replace("394a0707", "0a42a061")
    with pytest.raises(GCSCapabilityDefinitionError, match="exact WIF principal drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)

    value = _definition()
    value["wif_binding"]["attribute_condition_terms"][-1] = "assertion.secboot == false"
    with pytest.raises(GCSCapabilityDefinitionError, match="WIF attribute condition drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)


def test_definition_rejects_broad_or_promoted_iam(tmp_path):
    value = _definition()
    value["iam"]["bucket_writer"]["permissions"].append("storage.objects.delete")
    with pytest.raises(GCSCapabilityDefinitionError, match="custom writer IAM drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)

    value = _definition()
    value["iam"]["state"] = "applied"
    with pytest.raises(GCSCapabilityDefinitionError, match="IAM state was promoted"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)


def test_definition_rejects_non_confidential_or_exported_credentials(tmp_path):
    value = _definition()
    value["credential_source"]["origin"] = "ambient ADC"
    with pytest.raises(GCSCapabilityDefinitionError, match="credential-source boundary drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)

    value = _definition()
    value["apply_boundary"]["credentials_exported"] = True
    with pytest.raises(GCSCapabilityDefinitionError, match="apply boundary drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)


def test_definition_rejects_object_generation_or_r18r12_dependency_drift(tmp_path):
    value = _definition()
    value["artifacts"]["objects"][6]["expected_generation"] = 1
    with pytest.raises(GCSCapabilityDefinitionError, match="generation-0 precondition drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)

    value = _definition()
    value["dependency"]["ledger_head_digest"] = "sha256:" + "0" * 64
    with pytest.raises(GCSCapabilityDefinitionError, match="R18R12 ledger head drift"):
        validate_definition(_write_tampered(tmp_path, value), ROOT)


def test_definition_keeps_private_truth_and_forbids_object_mutation():
    value = _definition()
    assert value["destination"]["visibility"]["uniform_bucket_level_access"] is True
    assert value["destination"]["visibility"]["private_truth_suffix"] == "private-truth/case-store.json"
    assert value["operation"]["forbidden_actions"] == ["gcs.list", "gcs.delete", "gcs.overwrite", "credential_generation"]
    assert value["iam"]["remove_broad_grant"] == {
        "member": "serviceAccount:p5-evaluator@ocelot-proof.iam.gserviceaccount.com",
        "role": "roles/storage.objectAdmin",
        "required": True,
    }
    assert value["apply_boundary"]["later_operations_enabled"] is False
