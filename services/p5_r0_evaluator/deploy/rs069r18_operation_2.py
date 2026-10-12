"""Fail-closed RS-069R18R10 operation-2 WIP provider handler.

This module is the reviewed IaC boundary for ``correct_wip_provider_claim_mapping``.
It is deliberately not dispatched by the legacy RS-069 runner. Operation 2 is a
self-custodied IaC policy update: a canonical R18R10 master approval artifact, exact
request/plan/input/attempt bindings, and a read-only provider prestate are required.
Independent evaluator evidence is not an operation-2 prerequisite; Confidential
Space attestation is explicitly deferred to RS-080 and is not asserted here.

The execution path is narrow: absolute-gcloud describe -> exact fresh prestate check
-> one fixed ``update-oidc`` provider update using the explicit observed no-etag
precondition (etag-bearing state fails closed) -> absolute-gcloud describe -> exact
desired-state check.
The provider update is status-only: its stdout is never parsed or treated as state
evidence. Any post-mutation failure uses the same fixed update runner to restore the
captured prestate, followed by a fresh describe/configuration-digest check.
No shell input, raw command output, token, claim value, or attestation assertion is
written to the ledger; phase evidence is redacted and digest-only.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, parse_canonical, sha256
from services.p5_r0_evaluator.deploy.authority_binding_proposal import (
    REVIEW_AUDIENCE,
    REVIEW_ISSUER,
    REVIEW_PROVIDER,
    REVIEW_SUBJECT_PREFIX,
)
from services.p5_r0_evaluator.deploy.rs069r17_operation_2_approval import (
    DEFAULT_REQUEST,
    LATER_OPERATION_IDS,
    OPERATION_ID,
    validate_request,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-r18r10-ledger.jsonl"
DEFAULT_RECOVERY_MARKER = REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-r18r10-recovery.json"
_GCLOUD = Path("/home/matt/google-cloud-sdk/bin/gcloud")
_APPROVAL_SCHEMA = "P5R0RS069R18R10ApprovalArtifactV2"
_ACCEPTANCE_CONTRACT = "P5R0RS069R18R10Operation2AcceptanceV2"
_APPROVAL_ID = "P5-MASTER-001/APPROVAL-007-RS069R18R10"
_ATTEMPT_RE = re.compile(r"^rs069r18r10-op2-[a-z0-9][a-z0-9-]{7,63}$")
_HISTORICAL_LEDGER_PATHS = (
    REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-ledger.jsonl",
    REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-r18r8-ledger.jsonl",
    REPOSITORY_ROOT / "var/p5-r0-rs069/operation-2-r18r9-ledger.jsonl",
)
_ATTESTATION_DEFERRED = {
    "status": "deferred",
    "deferred_to": "RS-080",
    "asserted": False,
}
_PROVIDER_RE = re.compile(
    r"^//iam\.googleapis\.com/projects/(?P<number>[0-9]+)/locations/global/"
    r"workloadIdentityPools/(?P<pool>[a-z0-9-]+)/providers/(?P<provider>[a-z0-9-]+)$"
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNRESOLVED_RE = re.compile(
    r"(?:REQUIRED_INPUT(?::|\b)|UNRESOLVED|REPLACE_[A-Z0-9_]*|"
    r"\b(?:PROJECT_ID|PROJECT_NUMBER|POOL|PROVIDER|LOCATION|VERSION)\b)"
)
_EXPECTED_PROJECT_ID = "ocelot-proof"
_EXPECTED_PROJECT_NUMBER = "141633828616"
_EXPECTED_POOL = "p5-cs-pool"
_EXPECTED_PROVIDER = "p5-cs-production"
_EXPECTED_LOCATION = "global"
_EXPECTED_ZONE = "us-east1-b"
_EXPECTED_WORKLOAD = "evaluator"
_EXPECTED_TEE = "CONFIDENTIAL_SPACE"
_EXPECTED_HARDWARE = "GCP_AMD_SEV"
_EXPECTED_DEBUG = "disabled-since-boot"
_EXPECTED_CLAIM_PATHS = {
    "audience": "aud",
    "nonce": "eat_nonce",
    "issued_at": "iat",
    "expires_at": "exp",
    "issuer": "iss",
    "subject": "sub",
    "image_digest": "submods.container.image_digest",
    "project_number": "submods.gce.project_number",
    "project_id": "submods.gce.project_id",
    "zone": "submods.gce.zone",
    "debug_state": "dbgstat",
    "tee": "swname",
    "hardware_model": "hwmodel",
    "secure_boot": "secboot",
    "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
    "smoke": "submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
}
_EXPECTED_CLAIM_VALUES = {
    "audience": REVIEW_AUDIENCE,
    "debug_state": _EXPECTED_DEBUG,
    "hardware_model": _EXPECTED_HARDWARE,
    "issuer": REVIEW_ISSUER,
    "project_id": _EXPECTED_PROJECT_ID,
    "project_number": _EXPECTED_PROJECT_NUMBER,
    "secure_boot": True,
    "smoke": False,
    "subject_prefix": REVIEW_SUBJECT_PREFIX,
    "tee": _EXPECTED_TEE,
    "workload": _EXPECTED_WORKLOAD,
    "zone": _EXPECTED_ZONE,
}
_EXPECTED_MAPPING_KEYS = {
    "google.subject",
    "attribute.image_digest",
    "attribute.project_number",
    "attribute.project_id",
    "attribute.zone",
    "attribute.debug_state",
    "attribute.tee",
    "attribute.hardware_model",
    "attribute.secure_boot",
    "attribute.workload",
    "attribute.confidential_space_smoke",
}
_CONDITION_ORDER = (
    "audience", "issuer", "subject_prefix", "image_digest", "project_number",
    "project_id", "zone", "debug_state", "tee", "hardware_model", "workload",
    "smoke", "secure_boot",
)


class RS069Operation2Blocked(RuntimeError):
    """Operation 2 is not safe to execute from the supplied inputs."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RS069Operation2Blocked(message)


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None


def _digest(value: Any) -> str:
    return sha256(canonical_bytes(value))


def _reject_unresolved(value: Any, label: str) -> None:
    """Reject every unresolved marker in a mutation-bound object."""
    if value is None:
        raise RS069Operation2Blocked(f"{label} is unresolved")
    if isinstance(value, str):
        if _UNRESOLVED_RE.search(value) or value.strip() in {"UNKNOWN", "UNRESOLVED", "<REQUIRED_INPUT>"}:
            raise RS069Operation2Blocked(f"{label} is unresolved")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unresolved(key, f"{label}.key")
            _reject_unresolved(item, f"{label}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unresolved(item, f"{label}[{index}]")


def _load_canonical_artifact(path: Path, label: str, *, allow_unavailable_etag: bool = False) -> dict[str, Any]:
    """Load canonical bytes; decoded caller mappings are never trust roots."""
    try:
        raw = path.read_bytes()
        value = parse_canonical(raw)
    except Exception as exc:
        raise RS069Operation2Blocked(f"{label} is not a canonical artifact") from exc
    if allow_unavailable_etag and isinstance(value, Mapping) and value.get("etag_unavailable") is True and value.get("fingerprint") is None:
        for key, item in value.items():
            if key != "fingerprint":
                _reject_unresolved(key, f"{label}.key")
                _reject_unresolved(item, f"{label}.{key}")
    else:
        _reject_unresolved(value, label)
    return value


def _artifact_digest(value: Mapping[str, Any], field: str = "artifact_digest") -> str:
    _require(set(value) > {field}, f"{field} is missing")
    supplied = value.get(field)
    unsigned = {key: item for key, item in value.items() if key != field}
    _require(_is_digest(supplied), f"{field} is unresolved")
    _require(supplied == _digest(unsigned), f"{field} mismatch")
    return supplied


def _condition_expression(condition: Mapping[str, str]) -> str:
    _require(set(condition) == set(_CONDITION_ORDER), "condition keys are not canonical")
    _reject_unresolved(condition, "condition")
    return " && ".join(condition[key] for key in _CONDITION_ORDER)


def _resolved(value: Any, label: str) -> None:
    _require(
        isinstance(value, str) and bool(value) and _UNRESOLVED_RE.search(value) is None,
        f"{label} is unresolved",
    )


def canonical_provider_resource_name(provider_resource: str) -> str:
    """Return the one canonical resource spelling accepted by operation 2."""
    _resolved(provider_resource, "provider resource")
    _require(provider_resource != REVIEW_AUDIENCE, "provider resource is confused with token audience")
    if provider_resource.startswith("projects/"):
        canonical = "//iam.googleapis.com/" + provider_resource
    else:
        canonical = provider_resource
    match = _PROVIDER_RE.fullmatch(canonical)
    _require(match is not None, "provider resource is not canonical")
    parts = match.groupdict()
    _require(
        parts == {"number": _EXPECTED_PROJECT_NUMBER, "pool": _EXPECTED_POOL, "provider": _EXPECTED_PROVIDER},
        "provider/project/pool binding drift",
    )
    return canonical


def _provider_parts(provider_resource: str) -> dict[str, str]:
    canonical = canonical_provider_resource_name(provider_resource)
    match = _PROVIDER_RE.fullmatch(canonical)
    assert match is not None
    parts = match.groupdict()
    return {"project_number": parts["number"], "pool": parts["pool"], "provider": parts["provider"], "location": _EXPECTED_LOCATION}


def provider_resource_digest(provider_resource: str) -> str:
    return _digest(canonical_provider_resource_name(provider_resource))


def _desired_state(request: Mapping[str, Any], candidate_image_digest: str) -> dict[str, Any]:
    _require(request.get("scope") == [OPERATION_ID], "operation scope widened")
    _require(request.get("target", {}).get("project_id") == _EXPECTED_PROJECT_ID, "target project drift")
    _require(request.get("target", {}).get("region") == "us-east1", "target region drift")
    _require(request.get("target", {}).get("repository") == "p5-cs", "target repository drift")
    desired = request.get("desired_state")
    _require(isinstance(desired, Mapping), "desired WIP state is missing")
    mapping = desired.get("mapping")
    condition = desired.get("condition")
    _require(isinstance(mapping, Mapping) and set(mapping) == _EXPECTED_MAPPING_KEYS, "desired mapping is not closed")
    _reject_unresolved(mapping, "desired.mapping")
    _require(all(isinstance(key, str) and isinstance(value, str) and value.startswith("assertion.") for key, value in mapping.items()), "desired mapping contains an unresolved value")
    _require(isinstance(condition, Mapping) and set(condition) == set(_EXPECTED_CLAIM_VALUES) | {"image_digest"}, "desired condition is not closed")
    _reject_unresolved(condition, "desired.condition")
    _require(all(isinstance(value, str) and value for value in condition.values()), "desired condition contains an unresolved marker")
    _require(condition["image_digest"] == f"assertion.submods.container.image_digest == '{candidate_image_digest}'", "candidate image is not bound in condition")
    _require(desired.get("mapping_digest") == sha256(mapping), "desired mapping digest drift")
    _require(desired.get("condition_digest") == sha256(condition), "desired condition digest drift")
    _require(desired.get("mapping_condition_digest") == sha256({"mapping": mapping, "condition": condition}), "desired mapping/condition digest drift")
    return {
        "mapping": dict(mapping),
        "condition": dict(condition),
        "condition_expression": _condition_expression(condition),
        "condition_expression_digest": _digest(_condition_expression(condition)),
        "mapping_digest": desired["mapping_digest"],
        "condition_digest": desired["condition_digest"],
        "mapping_condition_digest": desired["mapping_condition_digest"],
    }


def validate_operation_2_bindings(
    request: Mapping[str, Any],
    *,
    candidate_image_digest: str,
    provider_resource: str | None,
    attested_claim_record: Mapping[str, Any] | None,
    approval: Mapping[str, Any] | None,
    review_state: str | None = None,
    claim_artifact_path: Path | None = None,
    approval_artifact_path: Path | None = None,
    expected_prestate_digest: str | None = None,
) -> dict[str, Any]:
    """Validate immutable bindings; only canonical file artifacts can authorize."""
    try:
        validate_request(request)
    except Exception as exc:
        raise RS069Operation2Blocked("operation-2 review packet validation failed") from exc
    _require(_is_digest(candidate_image_digest), "candidate image digest is unresolved")
    _reject_unresolved(candidate_image_digest, "candidate image digest")
    _require(provider_resource is not None, "provider resource is unresolved")
    _reject_unresolved(provider_resource, "provider resource")
    provider_resource = canonical_provider_resource_name(provider_resource)
    parts = _provider_parts(provider_resource)
    _require(attested_claim_record is None, "caller-supplied claim record is not an authentication artifact")
    _require(approval is None, "caller-supplied approval is not an authentication artifact")
    _require(claim_artifact_path is None, "Confidential Space attestation is deferred to RS-080")
    _require(approval_artifact_path is not None, "canonical self-custodied master approval artifact is missing")
    approval_artifact = _load_canonical_artifact(Path(approval_artifact_path), "approval artifact")
    desired = _desired_state(request, candidate_image_digest)
    required = request["required_inputs"]
    _require(required["wip_token_audience"]["value"] == REVIEW_AUDIENCE, "token audience drift")
    _require(required["claim_paths"]["value"] == _EXPECTED_CLAIM_PATHS, "claim-path binding drift")
    if required["candidate_image_digest"]["value"] is not None:
        _require(required["candidate_image_digest"]["value"] == candidate_image_digest, "candidate image digest binding drift")
    _require(required["wip_policy_template_digest"]["value"] == request["desired_state"]["template_digest"], "template digest binding drift")
    _require(required["claim_paths_digest"]["value"] == _digest(_EXPECTED_CLAIM_PATHS), "claim-path digest drift")
    _require(required["sts_audience_digest"]["value"] == _digest(REVIEW_AUDIENCE), "audience digest drift")
    provider_digest = provider_resource_digest(provider_resource)
    _require(provider_digest == _digest(provider_resource), "provider digest binding drift")
    _require(_is_digest(expected_prestate_digest), "expected prestate digest is unresolved")
    approval_bindings = approval_artifact.get("bindings")
    _require(isinstance(approval_bindings, Mapping), "approval artifact bindings are unresolved")
    attempt_id = approval_bindings.get("attempt_id")
    _require(isinstance(attempt_id, str) and _ATTEMPT_RE.fullmatch(attempt_id) is not None, "approval attempt identity is invalid")
    _reject_unresolved(attempt_id, "approval attempt identity")
    expected_scope = {
        "operation_id": OPERATION_ID,
        "operation_order": 2,
        "scope": [OPERATION_ID],
        "request_scope_digest": request["request_scope_digest"],
        "plan_digest": request["typed_plan_binding"]["plan_digest"],
        "candidate_image_digest": candidate_image_digest,
        "provider_resource_digest": provider_digest,
        "mapping_digest": desired["mapping_digest"],
        "condition_digest": desired["condition_digest"],
        "mapping_condition_digest": desired["mapping_condition_digest"],
        "expected_prestate_digest": expected_prestate_digest,
        "attempt_id": attempt_id,
    }
    _require(
        set(approval_artifact) == {
            "schema", "acceptance_contract", "approval_id", "custody", "status", "request_scope_digest",
            "bindings", "attestation", "artifact_digest",
        },
        "approval artifact is not closed",
    )
    _require(approval_artifact["schema"] == _APPROVAL_SCHEMA, "approval artifact schema drift")
    _require(approval_artifact["acceptance_contract"] == _ACCEPTANCE_CONTRACT, "approval acceptance contract drift")
    _require(approval_artifact["approval_id"] == _APPROVAL_ID, "approval artifact identity drift")
    _require(approval_artifact["custody"] == "self_custodied", "approval artifact custody drift")
    _require(approval_artifact["status"] == "approved_single_operation_pending_apply", "approval artifact is not approved")
    _require(approval_artifact["request_scope_digest"] == request["request_scope_digest"], "approval request binding drift")
    _require(approval_artifact["attestation"] == _ATTESTATION_DEFERRED, "Confidential Space attestation must be deferred to RS-080")
    _require(approval_artifact["bindings"] == expected_scope, "approval artifact binding drift")
    approval_artifact_digest = _artifact_digest(approval_artifact)
    _require(request.get("later_operations") and all(item.get("enabled") is False for item in request["later_operations"]), "later operation enabled")
    _require(tuple(item.get("id") for item in request["later_operations"]) == LATER_OPERATION_IDS, "later operation order drift")
    return {
        "provider": parts, "provider_resource": provider_resource,
        "approval_artifact_digest": approval_artifact_digest,
        "attestation": approval_artifact["attestation"],
        "desired": desired, "approval": expected_scope,
    }


def _state_from_gcloud(raw: Mapping[str, Any], provider_resource: str) -> dict[str, Any]:
    """Canonicalize one exact provider describe response; never retain raw output."""
    _require(isinstance(raw, Mapping), "provider describe output is not an object")
    canonical_provider = canonical_provider_resource_name(provider_resource)
    observed_name = raw.get("name")
    _require(isinstance(observed_name, str), "provider prestate name is unresolved")
    _require(canonical_provider_resource_name(observed_name) == canonical_provider, "provider prestate name drift")
    mapping = raw.get("attributeMapping")
    condition = raw.get("attributeCondition")
    fingerprint_fields = [key for key in ("fingerprint", "etag") if key in raw]
    _require(len(fingerprint_fields) <= 1, "provider fingerprint is missing or ambiguous")
    etag_unavailable = not fingerprint_fields
    fingerprint = None if etag_unavailable else raw[fingerprint_fields[0]]
    if etag_unavailable:
        _require(fingerprint is None, "provider fingerprint availability drift")
    else:
        _resolved(fingerprint, "provider fingerprint")
    _require(isinstance(mapping, Mapping) and all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items()), "provider mapping is malformed")
    _reject_unresolved(mapping, "provider mapping")
    _require(isinstance(condition, str) and condition, "provider condition is unresolved")
    _reject_unresolved(condition, "provider condition")
    state = {
        "schema": "P5R0RS069WIPProviderStateV1",
        "provider_resource": canonical_provider,
        "project_id": _EXPECTED_PROJECT_ID,
        "project_number": _EXPECTED_PROJECT_NUMBER,
        "pool": _EXPECTED_POOL,
        "location": _EXPECTED_LOCATION,
        "fingerprint": fingerprint,
        "etag_unavailable": etag_unavailable,
        "mapping": dict(mapping),
        "condition": condition,
    }
    state["mapping_digest"] = sha256(state["mapping"])
    state["condition_digest"] = _digest(state["condition"])
    state["mapping_condition_digest"] = _digest({"mapping": state["mapping"], "condition": state["condition"]})
    stable = {key: value for key, value in state.items() if key not in {"fingerprint", "mapping_digest", "condition_digest", "mapping_condition_digest", "state_digest", "configuration_digest"}}
    stable.update({"mapping": state["mapping"], "condition": state["condition"]})
    state["configuration_digest"] = _digest(stable)
    state["state_digest"] = state["configuration_digest"]
    return state


def _validate_state_integrity(state: Mapping[str, Any]) -> None:
    _require(isinstance(state, Mapping), "provider state is not an object")
    _require(isinstance(state.get("etag_unavailable"), bool), "provider etag availability is unresolved")
    for key, item in state.items():
        if key == "fingerprint" and state["etag_unavailable"] is True and item is None:
            continue
        _reject_unresolved(key, "provider state.key")
        _reject_unresolved(item, f"provider state.{key}")
    _require(state.get("schema") == "P5R0RS069WIPProviderStateV1", "provider state schema drift")
    canonical_provider = canonical_provider_resource_name(state.get("provider_resource"))
    _require(state.get("provider_resource") == canonical_provider, "provider resource is not canonical")
    _provider_parts(canonical_provider)
    _require(state.get("project_id") == _EXPECTED_PROJECT_ID and state.get("project_number") == _EXPECTED_PROJECT_NUMBER, "provider project binding drift")
    _require(state.get("pool") == _EXPECTED_POOL and state.get("location") == _EXPECTED_LOCATION, "provider pool/location binding drift")
    if state["etag_unavailable"]:
        _require(state.get("fingerprint") is None, "provider fingerprint availability drift")
    else:
        _resolved(state.get("fingerprint"), "provider fingerprint")
    _require(isinstance(state.get("mapping"), Mapping) and all(isinstance(k, str) and isinstance(v, str) for k, v in state["mapping"].items()), "provider mapping is malformed")
    _reject_unresolved(state["mapping"], "provider state mapping")
    _require(isinstance(state.get("condition"), str) and state["condition"], "provider condition is unresolved")
    _reject_unresolved(state["condition"], "provider state condition")
    _require(state.get("mapping_digest") == sha256(state["mapping"]), "provider mapping digest drift")
    _require(state.get("condition_digest") == _digest(state["condition"]), "provider condition digest drift")
    _require(state.get("mapping_condition_digest") == _digest({"mapping": state["mapping"], "condition": state["condition"]}), "provider mapping/condition digest drift")
    stable = {key: value for key, value in state.items() if key not in {"fingerprint", "mapping_digest", "condition_digest", "mapping_condition_digest", "state_digest", "configuration_digest"}}
    stable.update({"mapping": state["mapping"], "condition": state["condition"]})
    _require(state.get("configuration_digest") == _digest(stable), "provider configuration digest drift")
    _require(state.get("state_digest") == state.get("configuration_digest"), "provider state digest drift")


def validate_prestate(state: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    """Reject any fresh observed-state, mapping, condition, or digest drift before mutation."""
    _validate_state_integrity(state)
    _validate_state_integrity(expected)
    _require(expected == state, "prestate observed state or configuration drift")


def validate_poststate(state: Mapping[str, Any], desired: Mapping[str, Any], provider_resource: str) -> None:
    """Require the poststate to be exactly the approved mapping/condition."""
    _validate_state_integrity(state)
    _reject_unresolved(desired, "desired state")
    try:
        expected_provider = canonical_provider_resource_name(provider_resource)
    except RS069Operation2Blocked as exc:
        raise RS069Operation2Blocked("poststate provider drift") from exc
    _require(state.get("provider_resource") == expected_provider, "poststate provider drift")
    _require(desired.get("mapping_digest") == sha256(desired.get("mapping")), "desired mapping digest drift")
    _require(desired.get("condition_digest") == sha256(desired.get("condition")), "desired condition digest drift")
    _require(desired.get("mapping_condition_digest") == sha256({"mapping": desired.get("mapping"), "condition": desired.get("condition")}), "desired mapping/condition digest drift")
    _require(state.get("mapping_digest") == desired.get("mapping_digest"), "poststate mapping drift")
    _require(state.get("condition") == desired.get("condition_expression"), "poststate condition drift")
    _require(state.get("condition_digest") == desired.get("condition_expression_digest"), "poststate condition digest drift")
    _require(state.get("mapping_condition_digest") == _digest({"mapping": desired.get("mapping"), "condition": desired.get("condition_expression")}), "poststate mapping/condition drift")
    _require(state.get("mapping") == desired.get("mapping"), "poststate desired mapping mismatch")


def _describe_command(provider_resource: str) -> list[str]:
    parts = _provider_parts(provider_resource)
    return [
        str(_GCLOUD), "iam", "workload-identity-pools", "providers", "describe", parts["provider"],
        f"--project={_EXPECTED_PROJECT_ID}", f"--location={_EXPECTED_LOCATION}",
        f"--workload-identity-pool={parts['pool']}", "--format=json",
    ]


def _mapping_argument(mapping: Mapping[str, str]) -> str:
    _reject_unresolved(mapping, "update mapping")
    return ",".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def _update_command(
    provider_resource: str,
    mapping: Mapping[str, str],
    condition: Mapping[str, str] | str,
    fingerprint: str | None,
    etag_unavailable: bool = False,
) -> list[str]:
    parts = _provider_parts(provider_resource)
    _require(isinstance(etag_unavailable, bool), "update etag availability is unresolved")
    if not etag_unavailable:
        raise RS069Operation2Blocked("OIDC provider update cannot safely apply an etag-bearing state")
    _require(fingerprint is None, "update fingerprint must be absent when etag is unavailable")
    condition_text = condition if isinstance(condition, str) else _condition_expression(condition)
    _require(isinstance(condition_text, str) and condition_text, "update condition is unresolved")
    _reject_unresolved(condition_text, "update condition")
    command = [
        str(_GCLOUD), "iam", "workload-identity-pools", "providers", "update-oidc", parts["provider"],
        f"--project={_EXPECTED_PROJECT_ID}", f"--location={_EXPECTED_LOCATION}",
        f"--workload-identity-pool={parts['pool']}", f"--attribute-mapping={_mapping_argument(mapping)}",
        f"--attribute-condition={condition_text}",
    ]
    # Provider updates are status-only.  State evidence must come from a fresh
    # describe response, never from update stdout.
    return command


def build_rollback_command(
    provider_resource: str,
    prestate: Mapping[str, Any],
    current_fingerprint: str | None,
    current_etag_unavailable: bool,
) -> list[str]:
    """Build rollback through the same fixed provider-update runner."""
    _validate_state_integrity(prestate)
    _require(canonical_provider_resource_name(prestate.get("provider_resource")) == canonical_provider_resource_name(provider_resource), "rollback provider drift")
    return _update_command(provider_resource, prestate["mapping"], prestate["condition"], current_fingerprint, current_etag_unavailable)


def _ledger_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    previous: str | None = None
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_bytes().splitlines(), start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RS069Operation2Blocked(f"operation-2 ledger malformed at line {line_number}") from exc
        _require(isinstance(record, dict) and record.get("previous_event_digest") == previous, "operation-2 ledger chain drift")
        digest = record.get("event_digest")
        _require(digest == sha256({key: value for key, value in record.items() if key != "event_digest"}), "operation-2 ledger digest drift")
        previous = digest
        records.append(record)
    return records


def _historical_attempt_ids() -> set[str]:
    """Read immutable prior ledgers only to prevent R18R10 identity reuse."""
    attempts: set[str] = set()
    for path in _HISTORICAL_LEDGER_PATHS:
        if not path.exists():
            continue
        for record in _ledger_records(path):
            attempt_id = record.get("attempt_id")
            if isinstance(attempt_id, str):
                attempts.add(attempt_id)
    return attempts


def _historical_ledger_heads() -> dict[str, str | None]:
    """Capture immutable prior ledger heads for redacted run-start evidence."""
    heads: dict[str, str | None] = {}
    for path in _HISTORICAL_LEDGER_PATHS:
        if path.exists():
            records = _ledger_records(path)
            heads[str(path)] = records[-1]["event_digest"] if records else None
    return heads


def _ledger_event(path: Path, record: Mapping[str, Any], previous: str | None) -> dict[str, Any]:
    body = dict(record)
    body["previous_event_digest"] = previous
    body["event_digest"] = sha256(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write(canonical_bytes(body) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return body


def _write_recovery_marker(path: Path, record: Mapping[str, Any]) -> bool:
    """Persist a redacted no-retry marker when the primary ledger is uncertain."""
    marker = path.with_name(path.stem + "-recovery.json")
    body = {
        "schema": "P5R0RS069R18RecoveryMarkerV1",
        "status": "manual_review_required_no_retry",
        "operation_id": OPERATION_ID,
        "attempt_id": record.get("attempt_id"),
        "ledger_path": str(path),
        "mutations_performed": bool(record.get("mutations_performed")),
        "rollback_status": record.get("rollback_status", "unknown"),
        "reason": "terminal_ledger_write_unconfirmed",
    }
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        with marker.open("xb") as stream:
            stream.write(canonical_bytes(body))
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        return True
    except OSError:
        return False
    return True


def _ledger_failure_result(path: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    marker_written = _write_recovery_marker(path, record)
    return {
        "status": "terminal_ledger_write_failed",
        "operation_id": OPERATION_ID,
        "attestation": dict(_ATTESTATION_DEFERRED),
        "rollback_status": "manual_review_ledger_failure",
        "ledger_path": str(path),
        "recovery_marker_path": str(path.with_name(path.stem + "-recovery.json")),
        "recovery_marker_written": marker_written,
        "mutations_performed": bool(record.get("mutations_performed")),
        "later_operations_skipped": list(LATER_OPERATION_IDS),
    }


def _run_status(command: list[str], root: Path) -> None:
    """Run a fixed mutating argv and use only its exit status.

    Provider update stdout is intentionally discarded as evidence.  A fresh
    describe is required for every poststate or rollback verification.
    """
    try:
        result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL, text=True, capture_output=True, check=False)
    except OSError as exc:
        raise RS069Operation2Blocked("operation-2 update runner unavailable") from exc
    if result.returncode != 0:
        raise RS069Operation2Blocked(f"operation-2 update command failed with exit {result.returncode}")


def _run_json(command: list[str], root: Path) -> Mapping[str, Any]:
    """Run a fixed argv only; no shell and no stdin are ever accepted."""
    try:
        result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL, text=True, capture_output=True, check=False)
    except OSError as exc:
        raise RS069Operation2Blocked("operation-2 runner unavailable") from exc
    if result.returncode != 0:
        raise RS069Operation2Blocked(f"operation-2 command failed with exit {result.returncode}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RS069Operation2Blocked("operation-2 command returned non-JSON state") from exc
    _require(isinstance(value, Mapping), "operation-2 command returned non-object state")
    return value


def _failure_classification(phase: str, exc: Exception) -> str:
    """Return a redacted stable class, never command output or exception text."""
    if isinstance(exc, RS069Operation2Blocked):
        return f"{phase}_blocked"
    return f"{phase}_error"


def execute_operation_2(
    *,
    request: Mapping[str, Any],
    candidate_image_digest: str,
    provider_resource: str | None,
    attested_claim_record: Mapping[str, Any] | None,
    approval: Mapping[str, Any] | None,
    expected_prestate: Mapping[str, Any] | None,
    repository_root: Path = REPOSITORY_ROOT,
    ledger_path: Path = DEFAULT_LEDGER,
    apply_enabled: bool = False,
    review_state: str | None = None,
    claim_artifact_path: Path | None = None,
    approval_artifact_path: Path | None = None,
    expected_prestate_path: Path | None = None,
) -> dict[str, Any]:
    """Run only from canonical artifacts; never authenticate caller values."""
    _require(apply_enabled is True, "operation 2 apply is disabled until handler master review")
    _require(review_state is None, "caller review state is not an authentication artifact")
    _require(attested_claim_record is None and approval is None, "caller approval or claim values are not authentication artifacts")
    _require(expected_prestate is None, "caller prestate is not a canonical artifact")
    root = Path(repository_root).resolve()
    _require(Path.cwd().resolve() == root, "operation-2 runner must be invoked from repository root")
    _require(expected_prestate_path is not None, "canonical expected prestate artifact is missing")
    expected = _load_canonical_artifact(Path(expected_prestate_path), "expected prestate", allow_unavailable_etag=True)
    _validate_state_integrity(expected)
    bindings = validate_operation_2_bindings(
        request, candidate_image_digest=candidate_image_digest, provider_resource=provider_resource,
        attested_claim_record=None, approval=None, review_state=None,
        claim_artifact_path=claim_artifact_path, approval_artifact_path=approval_artifact_path,
        expected_prestate_digest=expected["state_digest"],
    )
    _require(request.get("workflow", {}).get("later_operations_enabled") is False, "later operation enablement drift")
    ledger = Path(ledger_path)
    resolved_ledger = ledger.resolve()
    _require(resolved_ledger not in {path.resolve() for path in _HISTORICAL_LEDGER_PATHS}, "historical operation-2 ledger is immutable")
    if resolved_ledger.is_relative_to(root):
        _require(resolved_ledger == DEFAULT_LEDGER.resolve(), "R18R10 ledger path is not canonical")
    recovery = ledger.with_name(ledger.stem + "-recovery.json")
    _require(not recovery.exists(), "prior recovery marker requires manual review")
    try:
        records = _ledger_records(ledger)
        _require(not records, "operation-2 ledger already contains an attempt; retry is disabled")
        previous = None
        historical_attempts = _historical_attempt_ids()
        historical_ledger_heads = _historical_ledger_heads()
    except Exception as exc:
        return _ledger_failure_result(ledger, {"attempt_id": None, "mutations_performed": False, "rollback_status": type(exc).__name__})
    attempt = bindings["approval"]["attempt_id"]
    _require(attempt not in historical_attempts, "approval attempt identity was already used")
    mutation_started = False
    poststate: dict[str, Any] | None = None
    failure_phase = "prestate_describe"
    rollback_substep = "not_started"
    rollback_error_classification: str | None = None
    phase_attempts: dict[str, list[dict[str, Any]]] = {
        "desired_update": [],
        "current_state_describe": [],
        "rollback_update": [],
        "restored_state_describe": [],
    }

    def record_phase(
        phase: str,
        classification: str,
        state: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        evidence: dict[str, Any] = {"classification": classification, "redacted": True}
        if state is not None:
            evidence["state_digest"] = state["state_digest"]
            evidence["configuration_digest"] = state["configuration_digest"]
        if extra is not None:
            evidence.update(extra)
        phase_attempts[phase].append(evidence)

    try:
        started = _ledger_event(ledger, {
            "schema": "P5R0RS069R18R10Operation2LedgerEventV2", "acceptance_contract": _ACCEPTANCE_CONTRACT,
            "kind": "run_started", "attempt_id": attempt,
            "operation_id": OPERATION_ID, "operation_order": 2, "scope": [OPERATION_ID],
            "later_operations_enabled": False, "approval_id": _APPROVAL_ID,
            "approval_digest": bindings["approval_artifact_digest"], "attestation": bindings["attestation"],
            "historical_ledger_heads": historical_ledger_heads,
            "candidate_image_digest": candidate_image_digest, "provider_resource_digest": provider_resource_digest(provider_resource),
            "desired_mapping_condition_digest": bindings["desired"]["mapping_condition_digest"], "cloud_operations": [], "mutations_performed": False,
        }, previous)
        previous = started["event_digest"]
    except Exception:
        return _ledger_failure_result(ledger, {"attempt_id": attempt, "mutations_performed": False, "rollback_status": "not_applicable_no_mutation"})
    try:
        prestate = _state_from_gcloud(_run_json(_describe_command(provider_resource), root), provider_resource)
        failure_phase = "prestate_validation"
        validate_prestate(prestate, expected)
        event = _ledger_event(ledger, {
            "schema": "P5R0RS069R18R10Operation2LedgerEventV2", "acceptance_contract": _ACCEPTANCE_CONTRACT,
            "kind": "prestate_captured", "attempt_id": attempt,
            "operation_id": OPERATION_ID, "provider_resource_digest": provider_resource_digest(provider_resource),
            "prestate_digest": prestate["state_digest"], "prestate_configuration_digest": prestate["configuration_digest"],
            "prestate_fingerprint": prestate["fingerprint"], "etag_unavailable": prestate["etag_unavailable"],
            "command": _describe_command(provider_resource), "redacted": True, "cloud_operations": ["wip_provider_describe"], "mutations_performed": False,
        }, previous)
        previous = event["event_digest"]
        mutation_started = True
        failure_phase = "desired_update"
        try:
            _run_status(_update_command(provider_resource, bindings["desired"]["mapping"], bindings["desired"]["condition"], prestate["fingerprint"], prestate["etag_unavailable"]), root)
        except Exception as update_exc:
            record_phase(
                "desired_update",
                _failure_classification("desired_update", update_exc),
                extra={
                    "desired_mapping_condition_digest": bindings["desired"]["mapping_condition_digest"],
                    "prestate_digest": prestate["state_digest"],
                    "etag_unavailable": prestate["etag_unavailable"],
                },
            )
            raise
        record_phase(
            "desired_update",
            "desired_update_succeeded",
            extra={
                "desired_mapping_condition_digest": bindings["desired"]["mapping_condition_digest"],
                "prestate_digest": prestate["state_digest"],
                "etag_unavailable": prestate["etag_unavailable"],
            },
        )
        failure_phase = "poststate_describe"
        try:
            poststate = _state_from_gcloud(_run_json(_describe_command(provider_resource), root), provider_resource)
        except Exception as describe_exc:
            record_phase("current_state_describe", _failure_classification("current_state_describe", describe_exc))
            raise
        record_phase("current_state_describe", "current_state_describe_succeeded", poststate)
        failure_phase = "poststate_validation"
        validate_poststate(poststate, bindings["desired"], provider_resource)
        verified = _ledger_event(ledger, {
            "schema": "P5R0RS069R18R10Operation2LedgerEventV2", "acceptance_contract": _ACCEPTANCE_CONTRACT,
            "kind": "operation_verified", "attempt_id": attempt, "approval_id": _APPROVAL_ID,
            "operation_id": OPERATION_ID, "operation_order": 2, "prestate_digest": prestate["state_digest"],
            "poststate_digest": poststate["state_digest"], "poststate_fingerprint": poststate["fingerprint"],
            "desired_mapping_condition_digest": bindings["desired"]["mapping_condition_digest"], "attestation": bindings["attestation"], "command": "fixed_update_runner", "cloud_operations": ["wip_provider_update", "wip_provider_describe"], "mutations_performed": True,
            "later_operations_skipped": list(LATER_OPERATION_IDS), "redacted": True,
        }, previous)
        try:
            stopped = _ledger_event(ledger, {
                "schema": "P5R0RS069R18R10Operation2LedgerEventV2", "acceptance_contract": _ACCEPTANCE_CONTRACT,
                "kind": "run_stopped", "attempt_id": attempt, "approval_id": _APPROVAL_ID,
                "operation_id": OPERATION_ID, "status": "verified", "verified_event_digest": verified["event_digest"],
                "rollback_status": "not_required_verified", "phase_attempts": phase_attempts,
                "cloud_operations": ["wip_provider_update", "wip_provider_describe"],
                "mutations_performed": True, "later_operations_skipped": list(LATER_OPERATION_IDS), "redacted": True,
            }, verified["event_digest"])
        except Exception:
            return _ledger_failure_result(ledger, {"attempt_id": attempt, "mutations_performed": True, "rollback_status": "manual_review_ledger_failure"})
        return {"status": "verified", "operation_id": OPERATION_ID, "attestation": dict(_ATTESTATION_DEFERRED), "stop_event_digest": stopped["event_digest"], "ledger_path": str(ledger), "attempt_id": attempt, "mutations_performed": True, "later_operations_skipped": list(LATER_OPERATION_IDS), "phase_attempts": phase_attempts}
    except Exception as exc:
        rollback_status = "not_applicable_no_mutation"
        if mutation_started:
            try:
                rollback_substep = "describe_current_state"
                if poststate is not None:
                    current = poststate
                else:
                    try:
                        current = _state_from_gcloud(_run_json(_describe_command(provider_resource), root), provider_resource)
                    except Exception as current_exc:
                        record_phase("current_state_describe", _failure_classification("current_state_describe", current_exc))
                        raise
                    record_phase("current_state_describe", "current_state_describe_succeeded", current)
                rollback_substep = "rollback_update"
                try:
                    _run_status(build_rollback_command(provider_resource, expected, current["fingerprint"], current["etag_unavailable"]), root)
                except Exception as rollback_update_exc:
                    record_phase(
                        "rollback_update",
                        _failure_classification("rollback_update", rollback_update_exc),
                        extra={
                            "current_state_digest": current["state_digest"],
                            "rollback_target_configuration_digest": expected["configuration_digest"],
                            "etag_unavailable": current["etag_unavailable"],
                        },
                    )
                    raise
                record_phase(
                    "rollback_update",
                    "rollback_update_succeeded",
                    extra={
                        "current_state_digest": current["state_digest"],
                        "rollback_target_configuration_digest": expected["configuration_digest"],
                        "etag_unavailable": current["etag_unavailable"],
                    },
                )
                rollback_substep = "describe_restored_state"
                try:
                    restored = _state_from_gcloud(_run_json(_describe_command(provider_resource), root), provider_resource)
                except Exception as restored_exc:
                    record_phase("restored_state_describe", _failure_classification("restored_state_describe", restored_exc))
                    raise
                record_phase("restored_state_describe", "restored_state_describe_succeeded", restored)
                rollback_substep = "verify_restored_configuration_digest"
                _require(restored["configuration_digest"] == expected["configuration_digest"], "rollback configuration mismatch")
                rollback_status = "rolled_back_verified"
            except Exception as rollback_exc:
                rollback_status = "rollback_failed_manual_review"
                rollback_error_classification = _failure_classification(rollback_substep, rollback_exc)
        try:
            stopped = _ledger_event(ledger, {
                "schema": "P5R0RS069R18R10Operation2LedgerEventV2", "acceptance_contract": _ACCEPTANCE_CONTRACT,
                "kind": "run_stopped", "attempt_id": attempt, "approval_id": _APPROVAL_ID,
                "operation_id": OPERATION_ID, "status": "failed_closed",
                "error": {"code": type(exc).__name__, "classification": _failure_classification(failure_phase, exc), "redacted": True},
                "rollback_status": rollback_status, "rollback_substep": rollback_substep,
                "rollback_error": ({"classification": rollback_error_classification, "redacted": True} if rollback_error_classification else None),
                "phase_attempts": phase_attempts,
                "cloud_operations": ["wip_provider_describe", "wip_provider_update"] if mutation_started else ["wip_provider_describe"],
                "mutations_performed": mutation_started, "later_operations_skipped": list(LATER_OPERATION_IDS), "redacted": True,
            }, previous)
        except Exception:
            return _ledger_failure_result(ledger, {"attempt_id": attempt, "mutations_performed": mutation_started, "rollback_status": rollback_status})
        return {"status": "failed_closed", "operation_id": OPERATION_ID, "attestation": dict(_ATTESTATION_DEFERRED), "stop_event_digest": stopped["event_digest"], "attempt_id": attempt, "rollback_status": rollback_status, "rollback_substep": rollback_substep, "rollback_error_classification": rollback_error_classification, "ledger_path": str(ledger), "mutations_performed": mutation_started, "later_operations_skipped": list(LATER_OPERATION_IDS), "phase_attempts": phase_attempts}


__all__ = [
    "DEFAULT_LEDGER", "DEFAULT_REQUEST", "LATER_OPERATION_IDS", "OPERATION_ID", "RS069Operation2Blocked",
    "build_rollback_command", "canonical_provider_resource_name", "execute_operation_2", "provider_resource_digest", "validate_operation_2_bindings",
    "validate_poststate", "validate_prestate",
]
