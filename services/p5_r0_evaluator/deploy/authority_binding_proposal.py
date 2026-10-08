"""Local validator for the RS-068 review-only authority proposal.

This module validates a checked-in, canonical proposal, the canonical WIP
remediation policy, and the frozen unsigned RS-062 lock request.  It never
calls gcloud, KMS, WIP, GCS, Confidential Space, FreeTSA, a deployment, or a
task runner, and it never creates authority or approval material.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import b64decode, parse_canonical
from services.p5_r0_evaluator.canonical import digest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROPOSAL = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json"
DEFAULT_LOCK_REQUEST = REPOSITORY_ROOT / "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json"
DEFAULT_REQUEST_TEMPLATE = Path(__file__).with_name("rs-068-authority-binding-request.json")
DEFAULT_WIP_POLICY = Path(__file__).with_name("rs-068-wip-policy-remediation.json")
REVIEW_AUTHORITY_ID = "self-custodied/ocelot-proof/p5-r0/evaluator/p5-v3-authority"
REVIEW_KEY_ID = "p5-v3-authority"
REVIEW_KMS_KEY_VERSION = "projects/ocelot-proof/locations/global/keyRings/p5-evaluator/cryptoKeys/p5-v3-authority/cryptoKeyVersions/1"
REVIEW_PUBLIC_KEY_DIGEST = "sha256:c498dbc2447b36d42840ef25705d6b3a3a1f9ff0d54fd3fa012c1f9c52ff9cbb"
REVIEW_PROVIDER = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
REVIEW_AUDIENCE = "https://sts.googleapis.com"
REVIEW_ISSUER = "https://confidentialcomputing.googleapis.com"
REVIEW_SUBJECT_PREFIX = "https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/"
_KEY_VERSION_RE = re.compile(r"^projects/[a-z][a-z0-9-]*/locations/[a-z0-9-]+/keyRings/[A-Za-z0-9_-]+/cryptoKeys/[A-Za-z0-9_-]+/cryptoKeyVersions/[1-9][0-9]*$")
_PROVIDER_RE = re.compile(r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CLAIM_PATHS = {
    "audience": "aud", "nonce": "eat_nonce", "issued_at": "iat", "expires_at": "exp",
    "issuer": "iss", "subject": "sub", "image_digest": "submods.container.image_digest",
    "project_number": "submods.gce.project_number", "project_id": "submods.gce.project_id",
    "zone": "submods.gce.zone", "debug_state": "dbgstat", "tee": "swname",
    "hardware_model": "hwmodel", "secure_boot": "secboot",
    "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
    "smoke": "submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
}
_EXPECTED_WIP_MAPPING = {
    "google.subject": "assertion.sub",
    "attribute.image_digest": "assertion.submods.container.image_digest",
    "attribute.project_number": "assertion.submods.gce.project_number",
    "attribute.project_id": "assertion.submods.gce.project_id",
    "attribute.zone": "assertion.submods.gce.zone",
    "attribute.debug_state": "assertion.dbgstat",
    "attribute.tee": "assertion.swname",
    "attribute.hardware_model": "assertion.hwmodel",
    "attribute.secure_boot": "assertion.secboot",
    "attribute.workload": "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD",
    "attribute.confidential_space_smoke": "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
}
_EXPECTED_WIP_VALUES = {
    "audience": REVIEW_AUDIENCE, "debug_state": "disabled-since-boot", "hardware_model": "GCP_AMD_SEV",
    "image_digest": "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c",
    "issuer": REVIEW_ISSUER, "project_id": "ocelot-proof", "project_number": "141633828616",
    "secure_boot": True, "smoke": False, "subject_prefix": REVIEW_SUBJECT_PREFIX,
    "tee": "CONFIDENTIAL_SPACE", "workload": "evaluator", "zone": "us-east1-b",
}
_EXPECTED_WIP_CONDITION = {
    "audience": "assertion.aud == 'https://sts.googleapis.com'",
    "debug_state": "assertion.dbgstat == 'disabled-since-boot'",
    "hardware_model": "assertion.hwmodel == 'GCP_AMD_SEV'",
    "image_digest": "assertion.submods.container.image_digest == 'sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c'",
    "issuer": "assertion.iss == 'https://confidentialcomputing.googleapis.com'",
    "project_id": "assertion.submods.gce.project_id == 'ocelot-proof'",
    "project_number": "assertion.submods.gce.project_number == '141633828616'",
    "secure_boot": "assertion.secboot == true",
    "smoke": "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == '0'",
    "subject_prefix": "assertion.sub.startsWith('https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/')",
    "tee": "assertion.swname == 'CONFIDENTIAL_SPACE'",
    "workload": "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD == 'evaluator'",
    "zone": "assertion.submods.gce.zone == 'us-east1-b'",
}
_OBSERVED_WIP_MAPPING = {
    "attribute.image_digest": "assertion.submods.container.image_digest",
    "attribute.project_id": "assertion.submods.gce.project_id",
    "attribute.project_number": "assertion.submods.gce.project_number",
    "attribute.workload": "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD",
    "attribute.zone": "assertion.submods.gce.zone",
    "google.subject": "assertion.sub",
}
_OBSERVED_WIP_CONDITION = "assertion.aud == 'https://sts.googleapis.com' && assertion.iss == 'https://confidentialcomputing.googleapis.com' && assertion.swname == 'CONFIDENTIAL_SPACE' && assertion.dbgstat == 'disabled-since-boot' && 'STABLE' in assertion.submods.confidential_space.support_attributes && assertion.hwmodel == 'GCP_AMD_SEV' && assertion.secboot == true && assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD == 'evaluator' && assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == '0' && assertion.sub.startsWith('https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/') && assertion.submods.gce.project_number == '141633828616' && assertion.submods.gce.project_id == 'ocelot-proof' && assertion.submods.gce.zone == 'us-east1-b' && assertion.submods.container.image_digest == 'sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c'"


class AuthorityBindingProposalValidationError(ValueError):
    """The RS-068 proposal is malformed or improperly promoted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuthorityBindingProposalValidationError(message)


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        return parse_canonical(path.read_bytes())
    except Exception as exc:
        raise AuthorityBindingProposalValidationError(f"{label} is not canonical JSON") from exc


def _public_key(value: Any, label: str) -> None:
    _require(isinstance(value, str) and value, f"{label} is missing")
    try:
        raw = b64decode(value)
    except Exception as exc:
        raise AuthorityBindingProposalValidationError(f"{label} is not canonical base64url") from exc
    _require(raw and __import__("base64").urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") == value, f"{label} is not canonical base64url")
    _require(len(raw) == 32, f"{label} must contain 32 Ed25519 bytes")


def validate_request_template(path: Path = DEFAULT_REQUEST_TEMPLATE) -> dict[str, Any]:
    """Validate the tracked, marker-only RS-068 input contract."""
    request = _load(Path(path), "RS-068 authority-binding request template")
    expected = {"artifact", "authority", "bound_claims", "boundaries", "classification", "generated_outputs", "generator", "lock_request", "schema", "status"}
    _require(set(request) == expected, "RS-068 request template fields are not closed")
    _require(request["schema"] == "P5R0RS068AuthorityBindingRequestV1", "RS-068 request template schema drift")
    _require(request["classification"] == "repository_definition_only" and request["status"] == "blocked_pending_signed_environment_approval", "RS-068 request template must remain blocked")
    authority = request["authority"]
    _require(isinstance(authority, Mapping) and set(authority) == {"authority_id", "key_id", "kms_key_version", "public_key", "public_key_digest"}, "RS-068 authority request fields are not closed")
    for name in authority:
        _require(isinstance(authority[name], str) and authority[name].startswith("REQUIRED_INPUT:"), f"RS-068 authority.{name} must remain a required-input marker")
    claims = request["bound_claims"]
    _require(isinstance(claims, Mapping) and set(claims) == {"claim_paths", "values"}, "RS-068 claim request fields are not closed")
    _require(claims["claim_paths"] == _CLAIM_PATHS, "RS-068 request claim paths drift")
    expected_values = {"audience": REVIEW_AUDIENCE, "debug_state": "disabled-since-boot", "hardware_model": "GCP_AMD_SEV", "image_digest": "REQUIRED_INPUT:attested evaluator image digest", "issuer": REVIEW_ISSUER, "project_id": "REQUIRED_INPUT:attested project ID", "project_number": "REQUIRED_INPUT:attested project number", "secure_boot": True, "smoke": False, "subject_prefix": "REQUIRED_INPUT:attested Compute VM subject prefix", "tee": "CONFIDENTIAL_SPACE", "workload": "evaluator", "zone": "REQUIRED_INPUT:attested evaluator zone"}
    _require(claims["values"] == expected_values, "RS-068 request claim values drift")
    _require(request["boundaries"] == {"approval_present": False, "authority_binding_present": False, "cloud_operations": [], "kms_signing_invoked": False, "local_execution": False, "signature_present": False}, "RS-068 request boundary drift")
    _require(request["generated_outputs"] == {"lock_request": "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json", "proposal": "var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json"}, "RS-068 generated output paths drift")
    _require(request["generator"] == {"inputs_are_required_markers": True, "name": "services.p5_r0_evaluator.deploy.authority_binding_proposal", "operation": "validate_only", "version": "RS068AuthorityBindingRequestV1"}, "RS-068 generator contract drift")
    _require(request["lock_request"] == {"authority_binding_digest": None, "request_digest": "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d", "signature_present": False, "unsigned_lock_digest": "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df"}, "RS-068 lock request commitment drift")
    return {"schema": request["schema"], "status": request["status"], "authority_binding_present": False, "approval_present": False, "signature_present": False, "production_promotable": False}


def _validate_wip_policy(path: Path) -> str:
    policy = _load(Path(path), "RS-068 WIP remediation policy")
    expected = {"artifact", "authority", "bound_claims", "boundaries", "condition", "mapping", "operation", "schema", "status"}
    _require(set(policy) == expected, "WIP remediation policy fields are not closed")
    _require(policy["schema"] == "P5R0WIPPolicyRemediationV1" and policy["operation"] == "validate_and_render_review_only", "WIP remediation policy identity drift")
    _require(policy["status"] == "blocked_pending_signed_environment_approval", "WIP remediation policy must remain blocked")
    _require(policy["authority"] == {"authority_id": REVIEW_AUTHORITY_ID, "key_id": REVIEW_KEY_ID, "kms_key_version": REVIEW_KMS_KEY_VERSION, "public_key_digest": REVIEW_PUBLIC_KEY_DIGEST}, "WIP authority binding drift")
    claims = policy["bound_claims"]
    _require(isinstance(claims, Mapping) and set(claims) == {"claim_paths", "values"}, "WIP claim contract is not closed")
    _require(claims["values"].get("audience") != REVIEW_PROVIDER, "WIP token audience must be separate from the provider resource")
    _require(claims["claim_paths"] == _CLAIM_PATHS and claims["values"] == _EXPECTED_WIP_VALUES, "WIP claim path/value contract drift")
    _require(policy["mapping"] == _EXPECTED_WIP_MAPPING, "WIP attribute mapping is incomplete or drifted")
    _require(policy["condition"] == _EXPECTED_WIP_CONDITION, "WIP attribute condition is incomplete or drifted")
    _require(policy["boundaries"] == {"apply_performed": False, "cloud_operations": [], "generated_lock_request_modified": False, "signed_environment_approval_required": True, "signature_present": False}, "WIP remediation boundary drift")
    return digest(policy)


def _validate_lock_request(path: Path) -> None:
    request = _load(path, "lock-signing request")
    _require(request.get("schema") == "P5R0KMSLockSigningRequestV1", "lock request schema drift")
    _require(request.get("request_digest") == "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d", "lock request digest drift")
    _require(request.get("unsigned_lock_digest") == request.get("unsigned_lock", {}).get("lock_digest"), "lock digest binding drift")
    _require(request.get("unsigned_lock_digest") == "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df", "unsigned lock digest drift")
    _require(request.get("kms") == {"authority_binding_digest": None, "key_version": None, "operation": "sign_exact_lock_digest_in_reviewed_signed_environment", "required": True, "signature_present": False}, "lock request is not unsigned request-only state")
    _require(request.get("production_signature_created") is False and request.get("cloud_operations") == [], "lock request has a production effect")
    lock = request["unsigned_lock"]
    _require(lock.get("authority_digest") is None and lock.get("kms_authority_binding_digest") is None and lock.get("signature") is None and lock.get("non_release") is True, "unsigned lock contains promoted authority material")


def validate_proposal(path: Path = DEFAULT_PROPOSAL, lock_request: Path = DEFAULT_LOCK_REQUEST, wip_policy: Path = DEFAULT_WIP_POLICY) -> dict[str, Any]:
    proposal = _load(Path(path), "RS-068 proposal")
    wip_policy_digest = _validate_wip_policy(Path(wip_policy))
    expected = {"artifact", "authority", "bound_claims", "boundaries", "classification", "generated_request", "item_id", "kms", "limitations", "observed_kms", "observed_wip_provider", "schema", "signing", "state_proposed", "status"}
    _require(set(proposal) == expected, "proposal fields are not closed")
    _require(proposal["schema"] == "P5R0AuthorityBindingProposalV1" and proposal["item_id"] == "RS-068", "proposal identity drift")
    _require(proposal["classification"] == "diagnostic_unsigned_non_release", "proposal classification drift")
    _require(proposal["state_proposed"] == "BLOCKED" and proposal["status"] == "blocked_pending_wip_policy_review_and_confidential_space_approval", "proposal must remain blocked")

    authority = proposal["authority"]
    _require(set(authority) == {"authority_id", "key_id", "public_key", "public_key_digest", "schema", "transport_attestation"}, "authority fields are not closed")
    _require(authority["schema"] == "P5R0PublicAuthorityV4", "authority schema drift")
    _require(authority["authority_id"] == REVIEW_AUTHORITY_ID, "review-only authority ID does not match the documented self-custodied evaluator authority")
    _require(authority["key_id"] == REVIEW_KEY_ID, "selected evaluator key ID drift")
    _public_key(authority["public_key"], "authority public key")
    _require(authority["public_key_digest"] == digest(authority["public_key"]) == REVIEW_PUBLIC_KEY_DIGEST, "authority public-key digest mismatch")
    transport = authority["transport_attestation"]
    _require(set(transport) == {"audience", "event", "provider", "schema"}, "transport fields are not closed")
    _require(transport == {"audience": REVIEW_AUDIENCE, "event": "confidential_space_attestation", "provider": REVIEW_PROVIDER, "schema": "P5R0AuthorityTransportV1"}, "transport binding drift")
    _require(_PROVIDER_RE.fullmatch(transport["provider"]) is not None, "WIP provider is not canonical")

    kms = proposal["kms"]
    _require(set(kms) == {"authority_binding", "key_version", "public_key", "public_key_digest"}, "KMS fields are not closed")
    _require(kms["authority_binding"] is None, "unreviewed KMS authority binding was promoted")
    _require(kms["key_version"] == REVIEW_KMS_KEY_VERSION and _KEY_VERSION_RE.fullmatch(kms["key_version"]), "selected KMS version drift")
    _require(kms["public_key"] == authority["public_key"] and kms["public_key_digest"] == authority["public_key_digest"], "KMS/public-key binding drift")

    claims = proposal["bound_claims"]
    _require(set(claims) == {"claim_paths", "claims"} and claims["claim_paths"] == _CLAIM_PATHS, "claim-path commitment drift")
    expected_claims = {"debug_state": "disabled-since-boot", "hardware_model": "GCP_AMD_SEV", "image_digest": "sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c", "issuer": REVIEW_ISSUER, "project_id": "ocelot-proof", "project_number": "141633828616", "secure_boot": True, "smoke": False, "tee": "CONFIDENTIAL_SPACE", "workload": "evaluator", "zone": "us-east1-b"}
    _require(claims["claims"] == expected_claims, "signed-environment claim commitment drift")
    _require(_DIGEST_RE.fullmatch(expected_claims["image_digest"]) is not None, "image claim is not a digest")
    _require(_PROVIDER_RE.fullmatch(transport["provider"]).group("number") == expected_claims["project_number"], "provider/project claim drift")

    observed_wip = proposal["observed_wip_provider"]
    _require(observed_wip["provider"] == transport["provider"] and observed_wip["audience"] == transport["audience"] and observed_wip["issuer"] == expected_claims["issuer"] and observed_wip["state"] == "ACTIVE", "observed WIP metadata drift")
    _require(observed_wip["attribute_mapping"] == _OBSERVED_WIP_MAPPING, "WIP observation mapping drift")
    _require(observed_wip["attribute_condition"] == _OBSERVED_WIP_CONDITION, "WIP observation condition drift")
    _require("attribute.debug_state" not in observed_wip["attribute_mapping"], "WIP observation no longer records the observed mapping omission")

    generated = proposal["generated_request"]
    _require(generated == {"authority_binding_digest": None, "lock_request_path": "var/p5-r0-diagnostic-inputs/public/lock-signing-request.json", "request_digest": "sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d", "unsigned_lock_digest": "sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df", "unchanged": True}, "generated request binding drift")
    _validate_lock_request(Path(lock_request))

    boundaries = proposal["boundaries"]
    _require(boundaries == {"authority_created": False, "cloud_operations": [], "gcs_upload_performed": False, "kms_asymmetric_sign_invoked": False, "lock_request_modified": False, "production_promotable": False, "signed_environment_approval_required": True, "signature_present": False, "task_execution": False}, "no-go boundary drift")
    _require(proposal["signing"] == {"asymmetric_sign_invoked": False, "signature": None, "signature_present": False, "signed_environment_approval_required": True, "signed_environment_approved": False}, "signing boundary drift")
    _require(proposal["observed_kms"]["public_key_digest"] == kms["public_key_digest"] and proposal["observed_kms"]["key_version"] == kms["key_version"], "observed KMS binding drift")
    _require(isinstance(proposal["limitations"], list) and proposal["limitations"], "limitations are required")
    return {"schema": proposal["schema"], "status": proposal["status"], "authority_id_resolved": True, "authority_id": authority["authority_id"], "key_id": authority["key_id"], "kms_key_version": kms["key_version"], "public_key_digest": kms["public_key_digest"], "wip_policy_digest": wip_policy_digest, "signed_environment_approval_required": True, "signature_present": False, "production_promotable": False}


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local-only RS-068 authority proposal")
    parser.add_argument("command", choices=("validate", "validate-template"))
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--lock-request", type=Path, default=DEFAULT_LOCK_REQUEST)
    parser.add_argument("--wip-policy", type=Path, default=DEFAULT_WIP_POLICY)
    parser.add_argument("--request-template", type=Path, default=DEFAULT_REQUEST_TEMPLATE)
    args = parser.parse_args(argv)
    if args.command == "validate-template":
        print(json.dumps(validate_request_template(args.request_template), sort_keys=True, separators=(",", ":")))
        return 0
    print(json.dumps(validate_proposal(args.proposal, args.lock_request, args.wip_policy), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
