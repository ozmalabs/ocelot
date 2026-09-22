"""Local-only deployment rendering and fail-closed preflight.

This module emits review artifacts and command strings only. It never invokes a
cloud SDK, creates a credential, or mutates a cloud resource.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shlex
from typing import Any, Mapping

from .confidential_space import (
    DEFAULT_ATTESTATION_ISSUER,
    DEFAULT_TIMING_BRIDGE_FREETSA_CA_PATH,
    DEFAULT_WIP_TOKEN_AUDIENCE,
    LockedBootstrapConfig,
    _validate_attestation_subject_prefix,
    _wip_policy_contract,
)
from .canonical import digest, parse_canonical


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DEFAULT_RS068_WIP_POLICY = Path(__file__).with_name("deploy") / "rs-068-wip-policy-remediation.json"
DEFAULT_RS068_WIP_TEMPLATE = Path(__file__).with_name("deploy") / "wip-provider-policy.cel.tmpl"


_PLACEHOLDER_RE = re.compile(
    r"REPLACE_|PROJECT_|REVIEWED_|IMAGE_DIGEST|RUNTIME_DIGEST|RESOURCE_PROFILE_DIGEST|"
    r"LEDGER_KEY_DIGEST|POOL|PROVIDER|LOCATION|VERSION"
)
_SECRET_RE = re.compile(r"private[_ -]?key|access[_ -]?token|secret|credential", re.I)
_CLAIM_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")


class DeploymentPreflightError(ValueError):
    pass


@dataclass(frozen=True)
class RenderedDeployment:
    metadata: str
    cel: str
    vm: str
    containerfile: str
    policy_digest: str
    claim_paths_digest: str
    attestation_claims_digest: str
    wip_policy_digest: str


@dataclass(frozen=True)
class DeploymentPolicy:
    service_name: str
    project_id: str
    project_number: str
    region: str
    artifact_registry_repository: str
    zone: str
    pool: str
    provider: str
    issuer: str
    caller_audience: str
    allowed_subject: str
    attestation_subject_prefix: str
    bucket: str
    prefix: str
    kms_key_version: str
    authority: Mapping[str, Any]
    image_digest: str
    base_image_digest: str
    runtime_digest: str
    resource_profile_digest: str
    timing_authority_id: str
    timing_key_id: str
    timing_ledger_id: str
    timing_public_key_digest: str
    timing_bridge_endpoint: str
    timing_bridge_service_account: str
    timing_bridge_audience: str
    timing_bridge_freetsa_ca_pem_path: str
    timing_bridge_freetsa_ca_pem_sha256: str
    timing_bridge_freetsa_certificate_sha256: str
    claim_paths: Mapping[str, str]
    capability_service_account: str = ""
    debug_state: str = "disabled-since-boot"
    tee: str = "CONFIDENTIAL_SPACE"
    workload: str = "evaluator"
    hardware_model: str = "GCP_AMD_SEV"
    secure_boot: bool = True
    cpu_limit: str = "1"
    memory_limit: str = "512Mi"
    # Launcher/WIP token audience; distinct from the canonical STS provider.
    attestation_audience: str = DEFAULT_WIP_TOKEN_AUDIENCE
    # The diagnostic path is separately committed in the image/WIP condition.
    confidential_space_smoke: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DeploymentPolicy":
        names = {field for field in cls.__dataclass_fields__}
        if set(value) != names:
            raise DeploymentPreflightError("deployment policy fields are not closed")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise DeploymentPreflightError("deployment policy shape") from exc


@dataclass(frozen=True)
class RenderedWIPPolicy:
    """Review-only WIP mapping/condition derived from a DeploymentPolicy."""

    mapping: Mapping[str, str]
    condition: str
    policy_digest: str
    source_digest: str


def _cel_single(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _wip_condition_strings(contract: Mapping[str, Any]) -> dict[str, str]:
    condition = contract["condition"]
    mapping = contract["mapping"]
    return {
        "audience": f"{condition['audience']} == {_cel_single(condition['audience_value'])}",
        "debug_state": f"{mapping['attribute.debug_state']} == {_cel_single(condition['debug_state'])}",
        "hardware_model": f"{mapping['attribute.hardware_model']} == {_cel_single(condition['hardware_model'])}",
        "image_digest": f"{mapping['attribute.image_digest']} == {_cel_single(condition['image_digest'])}",
        "issuer": f"assertion.{contract.get('claim_paths', {}).get('issuer', 'iss')} == {_cel_single(condition['issuer'])}",
        "project_id": f"{mapping['attribute.project_id']} == {_cel_single(condition['project_id'])}",
        "project_number": f"{mapping['attribute.project_number']} == {_cel_single(condition['project_number'])}",
        "secure_boot": f"{mapping['attribute.secure_boot']} == {str(condition['secure_boot']).lower()}",
        "smoke": f"{mapping['attribute.confidential_space_smoke']} == {_cel_single(condition['confidential_space_smoke'])}",
        "subject_prefix": f"{contract['mapping']['google.subject']}.startsWith({_cel_single(condition['subject_prefix'])})" if condition["subject_prefix"] is not None else "",
        "tee": f"{mapping['attribute.tee']} == {_cel_single(condition['tee'])}",
        "workload": f"{mapping['attribute.workload']} == {_cel_single(condition['workload'])}",
        "zone": f"{mapping['attribute.zone']} == {_cel_single(condition['zone'])}",
    }


def _render_wip_cel(contract: Mapping[str, Any]) -> str:
    newline = chr(10)
    mapping = newline.join(f'  {json.dumps(key)}: {json.dumps(value)}' for key, value in contract["mapping"].items())
    values = _wip_condition_strings(contract)
    terms = [values[name] for name in (
        "audience", "issuer", "subject_prefix", "image_digest", "project_number", "project_id",
        "zone", "debug_state", "tee", "hardware_model", "workload", "smoke", "secure_boot",
    ) if values[name]]
    return "attributeMapping = {" + newline + mapping + newline + "}" + newline + newline + "attributeCondition = \\\"\\\"\\\"" + newline + "  " + (" &&" + newline + "  ").join(terms) + newline + "\\\"\\\"\\\"" + newline


def _load_rs068_policy(path: Path) -> tuple[dict[str, Any], str]:
    try:
        value = parse_canonical(path.read_bytes())
    except Exception as exc:
        raise DeploymentPreflightError("RS-068 WIP policy is not canonical JSON") from exc
    return value, digest(value)


def render_wip_policy(
    policy: DeploymentPolicy | Mapping[str, Any],
    *,
    remediation_policy: Path = DEFAULT_RS068_WIP_POLICY,
    template: Path = DEFAULT_RS068_WIP_TEMPLATE,
) -> RenderedWIPPolicy:
    """Render and parity-check the review-only RS-068 WIP policy.

    This is deliberately a pure renderer. It consumes the checked-in policy
    contract, derives mappings/conditions from the same locked runtime source
    as ``render_deployment``, and never returns an apply operation.
    """
    if not isinstance(policy, DeploymentPolicy):
        policy = DeploymentPolicy.from_mapping(policy)
    _validate_policy_values(policy)
    config = _config(policy)
    source, source_digest = _load_rs068_policy(Path(remediation_policy))
    expected_fields = {"artifact", "authority", "bound_claims", "boundaries", "condition", "mapping", "operation", "schema", "status"}
    if set(source) != expected_fields:
        raise DeploymentPreflightError("RS-068 WIP policy fields are not closed")
    if source["schema"] != "P5R0WIPPolicyRemediationV1" or source["operation"] != "validate_and_render_review_only":
        raise DeploymentPreflightError("RS-068 WIP policy identity drift")
    if source["status"] != "blocked_pending_signed_environment_approval":
        raise DeploymentPreflightError("RS-068 WIP policy must remain blocked")
    if source["authority"] != {
        "authority_id": "self-custodied/ocelot-proof/p5-r0/evaluator/p5-v3-authority",
        "key_id": "p5-v3-authority",
        "kms_key_version": "projects/ocelot-proof/locations/global/keyRings/p5-evaluator/cryptoKeys/p5-v3-authority/cryptoKeyVersions/1",
        "public_key_digest": "sha256:c498dbc2447b36d42840ef25705d6b3a3a1f9ff0d54fd3fa012c1f9c52ff9cbb",
    }:
        raise DeploymentPreflightError("RS-068 WIP authority source drift")
    if source["boundaries"] != {"apply_performed": False, "cloud_operations": [], "generated_lock_request_modified": False, "signed_environment_approval_required": True, "signature_present": False}:
        raise DeploymentPreflightError("RS-068 WIP policy boundary drift")
    contract = _wip_policy_contract(
        provider=config.wip_provider, token_audience=config.attestation_audience, claim_paths=config.claim_paths,
        issuer=config.expected_issuer or "", image_digest=config.image_digest,
        project_number=config.project_number, project_id=config.project_id, zone=config.zone,
        debug_state=config.debug_state, tee=config.tee, hardware_model=config.hardware_model,
        secure_boot=config.secure_boot, workload=config.workload,
        confidential_space_smoke=config.confidential_space_smoke,
        attestation_subject_prefix=config.attestation_subject_prefix,
    )
    contract = {**contract, "claim_paths": dict(config.claim_paths)}
    values = {
        "audience": config.attestation_audience, "debug_state": config.debug_state,
        "hardware_model": config.hardware_model, "image_digest": config.image_digest,
        "issuer": config.expected_issuer, "project_id": config.project_id,
        "project_number": config.project_number, "secure_boot": config.secure_boot,
        "smoke": config.confidential_space_smoke, "subject_prefix": config.attestation_subject_prefix,
        "tee": config.tee, "workload": config.workload, "zone": config.zone,
    }
    bound_claims = source["bound_claims"]
    if bound_claims.get("claim_paths") != dict(config.claim_paths) or bound_claims.get("values") != values:
        raise DeploymentPreflightError("RS-068 WIP claim source drift")
    expected_condition = _wip_condition_strings(contract)
    if source["mapping"] != contract["mapping"]:
        raise DeploymentPreflightError("RS-068 WIP mapping drift")
    if source["condition"] != expected_condition:
        raise DeploymentPreflightError("RS-068 WIP condition drift")
    try:
        template_text = Path(template).read_text()
    except OSError as exc:
        raise DeploymentPreflightError("RS-068 WIP template is unavailable") from exc
    if _contains_placeholder(template_text):
        raise DeploymentPreflightError("RS-068 WIP template contains unresolved placeholders")
    template_terms = [
        *(f'{json.dumps(key)}: {json.dumps(value)}' for key, value in contract["mapping"].items()),
        *expected_condition.values(),
    ]
    if any(term not in template_text for term in template_terms):
        raise DeploymentPreflightError("RS-068 WIP template drift")
    return RenderedWIPPolicy(mapping=dict(contract["mapping"]), condition=_render_wip_cel(contract), policy_digest=config.wip_policy_digest, source_digest=source_digest)



def _require_digest(value: str, name: str) -> None:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise DeploymentPreflightError(f"{name} must be an immutable sha256 digest")


def _safe_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or _PLACEHOLDER_RE.search(value):
        raise DeploymentPreflightError(f"{name} contains an unresolved placeholder")
    if _SECRET_RE.search(name) or _SECRET_RE.search(value):
        raise DeploymentPreflightError(f"{name} contains secret material")
    if any(ord(char) < 0x20 or ord(char) == 0x7f for char in value):
        raise DeploymentPreflightError(f"{name} contains control characters")
    return value


def _contains_placeholder(text: str) -> bool:
    # Environment variable names intentionally contain terms such as
    # PROJECT_ID and IMAGE_DIGEST; inspect values, not those closed keys.
    sanitized = re.sub(r"P5R0_[A-Z0-9_]+", "", text)
    return _PLACEHOLDER_RE.search(sanitized) is not None


def _require_identifier(value: str, name: str) -> None:
    if not _IDENTIFIER_RE.fullmatch(value):
        raise DeploymentPreflightError(f"{name} is not a safe GCP identifier")


def _validate_policy_values(policy: DeploymentPolicy) -> None:
    _require_identifier(policy.service_name, "service_name")
    _require_identifier(policy.project_id, "project_id")
    if not re.fullmatch(r"[0-9]+", policy.project_number):
        raise DeploymentPreflightError("project_number is not numeric")
    for name in ("region", "zone", "pool", "artifact_registry_repository"):
        _require_identifier(getattr(policy, name), name)
    if policy.artifact_registry_repository != "p5-cs":
        raise DeploymentPreflightError("artifact registry repository is not the reviewed existing target")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]", policy.bucket):
        raise DeploymentPreflightError("bucket is not a safe GCS identifier")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", policy.prefix) or ".." in policy.prefix.split("/"):
        raise DeploymentPreflightError("prefix is not a safe object prefix")
    if not re.fullmatch(r"projects/[a-z][a-z0-9-]*/locations/[a-z0-9-]+/keyRings/[A-Za-z0-9_-]+/cryptoKeys/[A-Za-z0-9_-]+/cryptoKeyVersions/[1-9][0-9]*", policy.kms_key_version):
        raise DeploymentPreflightError("kms_key_version is not a safe KMS resource")
    if not re.fullmatch(r"//iam\.googleapis\.com/projects/[0-9]+/locations/global/workloadIdentityPools/[a-z0-9-]+/providers/[a-z0-9-]+", policy.provider):
        raise DeploymentPreflightError("WIP provider is not canonical")
    if policy.provider != f"//iam.googleapis.com/projects/{policy.project_number}/locations/global/workloadIdentityPools/{policy.pool}/providers/{policy.provider.rsplit('/', 1)[-1]}":
        raise DeploymentPreflightError("WIP provider project or pool drift")
    if not re.fullmatch(r"https://[^\s]+", policy.attestation_audience) or policy.attestation_audience == policy.provider:
        raise DeploymentPreflightError("WIP token audience must be separate from the provider resource")
    if not isinstance(policy.attestation_subject_prefix, str) or not policy.attestation_subject_prefix:
        raise DeploymentPreflightError("attestation_subject_prefix is required")
    try:
        _validate_attestation_subject_prefix(policy.attestation_subject_prefix, policy.project_id, policy.zone)
    except ValueError as exc:
        raise DeploymentPreflightError(str(exc)) from exc
    transport = policy.authority.get("transport_attestation") if isinstance(policy.authority, Mapping) else None
    if isinstance(transport, Mapping) and (transport.get("provider") != policy.provider or transport.get("audience") != policy.attestation_audience):
        raise DeploymentPreflightError("authority transport must bind provider and token audience separately")
    if policy.issuer != DEFAULT_ATTESTATION_ISSUER:
        raise DeploymentPreflightError("issuer must be the Google Cloud Attestation issuer")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{5,127}@[a-z][a-z0-9-]{4,29}\.iam\.gserviceaccount\.com", policy.capability_service_account):
        raise DeploymentPreflightError("capability service account is required and invalid")
    for name, value in (("issuer", policy.issuer), ("caller_audience", policy.caller_audience), ("allowed_subject", policy.allowed_subject), ("attestation_subject_prefix", policy.attestation_subject_prefix), ("capability_service_account", policy.capability_service_account), ("debug_state", policy.debug_state), ("tee", policy.tee), ("hardware_model", policy.hardware_model), ("workload", policy.workload), ("timing_authority_id", policy.timing_authority_id), ("timing_key_id", policy.timing_key_id), ("timing_ledger_id", policy.timing_ledger_id)):
        _safe_text(value, name)
    if set(policy.claim_paths) != {"audience", "nonce", "issued_at", "expires_at", "issuer", "subject", "image_digest", "project_number", "project_id", "zone", "debug_state", "tee", "hardware_model", "secure_boot", "workload", "smoke"}:
        raise DeploymentPreflightError("claim paths are not closed")
    for name, value in policy.claim_paths.items():
        if not isinstance(value, str) or not _CLAIM_PATH_RE.fullmatch(value):
            raise DeploymentPreflightError(f"claim path {name} is not CEL-safe")
    if not isinstance(policy.secure_boot, bool):
        raise DeploymentPreflightError("secure_boot must be boolean")
    if not isinstance(policy.confidential_space_smoke, bool):
        raise DeploymentPreflightError("confidential_space_smoke must be boolean")
    if not re.fullmatch(r"[0-9]+(?:m)?", policy.cpu_limit) or not re.fullmatch(r"[0-9]+(?:Mi|Gi)", policy.memory_limit):
        raise DeploymentPreflightError("resource limits are invalid")
    _require_digest(policy.image_digest, "image_digest")
    _require_digest(policy.base_image_digest, "base_image_digest")
    _require_digest(policy.runtime_digest, "runtime_digest")
    _require_digest(policy.resource_profile_digest, "resource_profile_digest")
    _require_digest(policy.timing_public_key_digest, "timing_public_key_digest")
    if policy.timing_bridge_freetsa_ca_pem_path != DEFAULT_TIMING_BRIDGE_FREETSA_CA_PATH:
        raise DeploymentPreflightError("timing bridge CA path must use the fixed image path")
    if not re.fullmatch(r"https://[^\s?#]+", policy.timing_bridge_endpoint):
        raise DeploymentPreflightError("timing bridge endpoint must be HTTPS without query or fragment")
    if not re.fullmatch(r"https://[^\s?#]+", policy.timing_bridge_audience):
        raise DeploymentPreflightError("timing bridge audience must be HTTPS without query or fragment")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{5,127}@[a-z][a-z0-9-]{4,29}\.iam\.gserviceaccount\.com", policy.timing_bridge_service_account):
        raise DeploymentPreflightError("timing bridge service account is invalid")
    _require_digest(policy.timing_bridge_freetsa_ca_pem_sha256, "timing_bridge_freetsa_ca_pem_sha256")
    _require_digest(policy.timing_bridge_freetsa_certificate_sha256, "timing_bridge_freetsa_certificate_sha256")


def _config(policy: DeploymentPolicy) -> LockedBootstrapConfig:
    _validate_policy_values(policy)
    provider = policy.provider
    try:
        return LockedBootstrapConfig(
            authority=dict(policy.authority), caller_audience=policy.caller_audience,
            allowed_subjects=frozenset({policy.allowed_subject}),
            attestation_subject_prefix=policy.attestation_subject_prefix,
            attestation_audience=policy.attestation_audience, wip_provider=provider,
            project_number=policy.project_number, project_id=policy.project_id,
            zone=policy.zone, image_digest=policy.image_digest,
            debug_state=policy.debug_state, tee=policy.tee,
            hardware_model=policy.hardware_model, secure_boot=policy.secure_boot, bucket=policy.bucket,
            prefix=policy.prefix, kms_key_version=policy.kms_key_version,
            runtime_digest=policy.runtime_digest,
            resource_profile_digest=policy.resource_profile_digest,
            base_image_digest=policy.base_image_digest,
            service_name=policy.service_name,
            region=policy.region,
            cpu_limit=policy.cpu_limit,
            memory_limit=policy.memory_limit,
            expected_issuer=policy.issuer, workload=policy.workload, claim_paths=dict(policy.claim_paths),
            confidential_space_smoke=policy.confidential_space_smoke,
            timing_authority_id=policy.timing_authority_id,
            timing_key_id=policy.timing_key_id,
            timing_ledger_id=policy.timing_ledger_id,
            timing_public_key_digest=policy.timing_public_key_digest,
            timing_bridge_endpoint=policy.timing_bridge_endpoint,
            timing_bridge_service_account=policy.timing_bridge_service_account,
            timing_bridge_audience=policy.timing_bridge_audience,
            timing_bridge_freetsa_ca_pem_path=policy.timing_bridge_freetsa_ca_pem_path,
            timing_bridge_freetsa_ca_pem_sha256=policy.timing_bridge_freetsa_ca_pem_sha256,
            timing_bridge_freetsa_certificate_sha256=policy.timing_bridge_freetsa_certificate_sha256,
            capability_service_account=policy.capability_service_account,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise DeploymentPreflightError("deployment policy does not satisfy locked runtime policy") from exc


def _environment(config: LockedBootstrapConfig) -> dict[str, str]:
    values: dict[str, str] = {
        "P5R0_AUTHORITY_JSON": json.dumps(dict(config.authority), sort_keys=True, separators=(",", ":")),
        "P5R0_AUDIENCE": config.caller_audience,
        "P5R0_ALLOWED_SUBJECTS": ",".join(sorted(config.allowed_subjects)),
        "P5R0_ATTESTATION_SUBJECT_PREFIX": config.attestation_subject_prefix or "",
        "P5R0_ATTESTATION_AUDIENCE": config.attestation_audience,
        "P5R0_WIP_PROVIDER": config.wip_provider,
        "P5R0_EXPECTED_PROJECT_NUMBER": config.project_number,
        "P5R0_EXPECTED_PROJECT_ID": config.project_id,
        "P5R0_EXPECTED_ZONE": config.zone,
        "P5R0_EXPECTED_IMAGE_DIGEST": config.image_digest,
        "P5R0_EXPECTED_DEBUG_STATE": config.debug_state,
        "P5R0_EXPECTED_TEE": config.tee,
        "P5R0_EXPECTED_HARDWARE_MODEL": config.hardware_model,
        "P5R0_EXPECTED_WORKLOAD": config.workload,
        "P5R0_EXPECTED_SECURE_BOOT": str(config.secure_boot).lower(),
        "P5R0_CONFIDENTIAL_SPACE_SMOKE": "1" if config.confidential_space_smoke else "0",
        "P5R0_ATTESTATION_ISSUER": config.expected_issuer or "",
        "P5R0_BUCKET": config.bucket,
        "P5R0_PREFIX": config.prefix,
        "P5R0_KMS_KEY_VERSION": config.kms_key_version,
        "P5R0_CAPABILITY_SERVICE_ACCOUNT": config.capability_service_account or "",
        "P5R0_RUNTIME_DIGEST": config.runtime_digest,
        "P5R0_RESOURCE_PROFILE_DIGEST": config.resource_profile_digest,
        "P5R0_BASE_IMAGE_DIGEST": config.base_image_digest,
        "P5R0_SERVICE_NAME": config.service_name,
        "P5R0_REGION": config.region,
        "P5R0_CPU_LIMIT": config.cpu_limit,
        "P5R0_MEMORY_LIMIT": config.memory_limit,
        "P5R0_POLICY_DIGEST": config.policy_digest,
        "P5R0_CLAIM_PATHS_DIGEST": config.claim_paths_digest,
        "P5R0_ATTESTATION_CLAIMS_DIGEST": config.attestation_claims_digest,
        "P5R0_WIP_POLICY_DIGEST": config.wip_policy_digest,
        "P5R0_TIMING_AUTHORITY_ID": config.timing_authority_id or "",
        "P5R0_TIMING_KEY_ID": config.timing_key_id or "",
        "P5R0_TIMING_LEDGER_ID": config.timing_ledger_id or "",
        "P5R0_TIMING_PUBLIC_KEY_DIGEST": config.timing_public_key_digest or "",
    }
    if any((config.timing_authority_id, config.timing_key_id, config.timing_ledger_id, config.timing_public_key_digest)):
        values.update({
            "P5R0_TIMING_BRIDGE_ENDPOINT": config.timing_bridge_endpoint or "",
            "P5R0_TIMING_BRIDGE_SERVICE_ACCOUNT": config.timing_bridge_service_account or "",
            "P5R0_TIMING_BRIDGE_AUDIENCE": config.timing_bridge_audience or "",
            "P5R0_TIMING_BRIDGE_FREETSA_CA_PEM_PATH": config.timing_bridge_freetsa_ca_pem_path,
            "P5R0_TIMING_BRIDGE_FREETSA_CA_PEM_SHA256": config.timing_bridge_freetsa_ca_pem_sha256 or "",
            "P5R0_TIMING_BRIDGE_FREETSA_CERTIFICATE_SHA256": config.timing_bridge_freetsa_certificate_sha256 or "",
        })
    suffixes = {
        "audience": "AUDIENCE", "nonce": "NONCE", "issued_at": "ISSUED_AT", "expires_at": "EXPIRES_AT",
        "issuer": "ISSUER", "subject": "SUBJECT", "image_digest": "IMAGE_DIGEST", "project_number": "PROJECT_NUMBER",
        "project_id": "PROJECT_ID", "zone": "ZONE", "debug_state": "DEBUG_STATE", "tee": "TEE",
        "hardware_model": "HARDWARE_MODEL", "secure_boot": "SECURE_BOOT", "workload": "WORKLOAD", "smoke": "SMOKE",
    }
    for name, path in config.claim_paths.items():
        values[f"P5R0_CLAIM_{suffixes[name]}"] = path
    return values


def _image_reference(policy: DeploymentPolicy, digest: str, *, tag: str | None = None) -> str:
    suffix = f":{tag}" if tag is not None else f"@{digest}"
    return f"{policy.region}-docker.pkg.dev/{policy.project_id}/{policy.artifact_registry_repository}/evaluator{suffix}"


def _metadata(config: LockedBootstrapConfig, policy: DeploymentPolicy) -> str:
    values = _environment(config)
    image_reference = _image_reference(policy, config.image_digest)
    lines = [
        "# Rendered Confidential Space VM metadata; generated from one immutable policy.",
        f"tee-image-reference={image_reference}",
        "tee-container-log-redirect=true",
    ]
    lines.extend(f"tee-env-{name}={value}" for name, value in sorted(values.items()))
    return "\n".join(lines) + "\n"


def _cel_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _cel(config: LockedBootstrapConfig) -> str:
    contract = _wip_policy_contract(
        provider=config.wip_provider, token_audience=config.attestation_audience, claim_paths=config.claim_paths,
        issuer=config.expected_issuer or "", image_digest=config.image_digest,
        project_number=config.project_number, project_id=config.project_id, zone=config.zone,
        debug_state=config.debug_state, tee=config.tee, hardware_model=config.hardware_model,
        secure_boot=config.secure_boot, workload=config.workload,
        confidential_space_smoke=config.confidential_space_smoke,
        attestation_subject_prefix=config.attestation_subject_prefix,
    )
    mapping = "\n".join(f"  {_cel_string(key)}: {_cel_string(value)}" for key, value in contract["mapping"].items())
    condition = contract["condition"]
    terms = [
        f"assertion.{config.claim_paths['audience']} == {_cel_string(condition['audience_value'])}",
        f"assertion.{config.claim_paths['issuer']} == {_cel_string(condition['issuer'])}",
        f"assertion.{config.claim_paths['subject']}.startsWith({_cel_string(condition['subject_prefix'])})" if condition["subject_prefix"] is not None else None,
        f"assertion.{config.claim_paths['image_digest']} == {_cel_string(condition['image_digest'])}",
        f"assertion.{config.claim_paths['project_number']} == {_cel_string(condition['project_number'])}",
        f"assertion.{config.claim_paths['project_id']} == {_cel_string(condition['project_id'])}",
        f"assertion.{config.claim_paths['zone']} == {_cel_string(condition['zone'])}",
        f"assertion.{config.claim_paths['debug_state']} == {_cel_string(condition['debug_state'])}",
        f"assertion.{config.claim_paths['tee']} == {_cel_string(condition['tee'])}",
        f"assertion.{config.claim_paths['hardware_model']} == {_cel_string(condition['hardware_model'])}",
        f"assertion.{config.claim_paths['workload']} == {_cel_string(condition['workload'])}",
        f"assertion.{config.claim_paths['smoke']} == {_cel_string(condition['confidential_space_smoke'])}",
        f"assertion.{config.claim_paths['secure_boot']} == {str(condition['secure_boot']).lower()}",
    ]
    return (
        "# Generated from the same frozen policy as runtime claim paths.\n"
        f"attributeMapping = {{\n{mapping}\n}}\n\n"
        "attributeCondition = \"\"\"\n  " + " &&\n  ".join(term for term in terms if term is not None) + "\n\"\"\"\n"
        f"# policy_digest={config.policy_digest}\n"
        f"# claim_paths_digest={config.claim_paths_digest}\n"
        f"# wip_policy_digest={config.wip_policy_digest}\n"
    )


def _vm(config: LockedBootstrapConfig, policy: DeploymentPolicy) -> str:
    env = _environment(config)
    rendered_env = "\n".join(
        f"            - name: {name}\n              value: {json.dumps(value)}" for name, value in sorted(env.items())
    )
    return f'''apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: {policy.service_name}
  annotations:
    run.googleapis.com/ingress: internal
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "1"
        run.googleapis.com/execution-environment: gen2
    spec:
      serviceAccountName: p5-evaluator@{config.project_id}.iam.gserviceaccount.com
      containerConcurrency: 1
      timeoutSeconds: 30
      containers:
        - image: {_image_reference(policy, policy.image_digest)}
          ports:
            - containerPort: 8080
          env:
{rendered_env}
          resources:
            limits:
              cpu: "{config.cpu_limit}"
              memory: {config.memory_limit}
'''


def _containerfile(policy: DeploymentPolicy) -> str:
    config = _config(policy)
    allow_env_override = ",".join(("P5R0_CONFIDENTIAL_SPACE_BOOTSTRAP", *_environment(config), "P5R0_CLOSURE_JSON"))
    return f'''# Generated from the reviewed DeploymentPolicy; local artifact only.
FROM python:3.12.8-slim-bookworm@{policy.base_image_digest}
LABEL tee.launch_policy.allow_env_override="{allow_env_override}"

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONHASHSEED=0 \\
    PORT=8080 \\
    P5R0_CONFIDENTIAL_SPACE_BOOTSTRAP=1 \\
    P5R0_CONFIDENTIAL_SPACE_SMOKE=0
WORKDIR /app
COPY services /app/services
COPY evaluation /app/evaluation
COPY schemas /app/schemas
RUN pip install --no-cache-dir -r /app/services/p5_r0_evaluator/requirements.txt
USER 65532:65532
EXPOSE 8080
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "4", "--timeout", "30", "services.p5_r0_evaluator.confidential_space_app:application"]
'''


def _parse_env_lines(text: str, expected_image_reference: str) -> dict[str, str]:
    values: dict[str, str] = {}
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, raw = line.partition("=")
        if not separator:
            raise DeploymentPreflightError("rendered metadata environment is malformed")
        if key.startswith("tee-env-"):
            env_name = key[len("tee-env-"):]
            if not re.fullmatch(r"P5R0_[A-Z0-9_]+", env_name) or env_name in values:
                raise DeploymentPreflightError("rendered metadata environment is malformed")
            values[env_name] = raw
        elif key in {"tee-image-reference", "tee-container-log-redirect"} and key not in metadata:
            metadata[key] = raw
        else:
            raise DeploymentPreflightError("rendered metadata environment is malformed")
    if metadata != {
        "tee-container-log-redirect": "true",
        "tee-image-reference": expected_image_reference,
    }:
        raise DeploymentPreflightError("rendered Confidential Space metadata is not locked")
    return values


def _parse_vm_env(text: str) -> dict[str, str]:
    block_match = re.search(r"^          env:\n(?P<block>.*?)^          resources:", text, re.MULTILINE | re.DOTALL)
    if block_match is None:
        raise DeploymentPreflightError("rendered VM environment is missing")
    lines = [line for line in block_match.group("block").splitlines() if line.strip()]
    if len(lines) % 2:
        raise DeploymentPreflightError("rendered VM environment syntax is malformed")
    values: dict[str, str] = {}
    for index in range(0, len(lines), 2):
        name_match = re.fullmatch(r"            - name: ([A-Za-z_][A-Za-z0-9_]*)", lines[index])
        value_match = re.fullmatch(r"              value: (.+)", lines[index + 1])
        if name_match is None or value_match is None:
            raise DeploymentPreflightError("rendered VM environment syntax is malformed")
        key = name_match.group(1)
        if key in values:
            raise DeploymentPreflightError("rendered VM environment has duplicate entries")
        try:
            value = json.loads(value_match.group(1))
        except json.JSONDecodeError as exc:
            raise DeploymentPreflightError("rendered VM environment value is not JSON") from exc
        if not isinstance(value, str):
            raise DeploymentPreflightError("rendered VM environment values must be strings")
        values[key] = value
    return values


def render_deployment(policy: DeploymentPolicy | Mapping[str, Any]) -> RenderedDeployment:
    if not isinstance(policy, DeploymentPolicy):
        policy = DeploymentPolicy.from_mapping(policy)
    _validate_policy_values(policy)
    for name, value in vars(policy).items():
        if name not in {"authority", "claim_paths"} and isinstance(value, str):
            _safe_text(value, name)
    config = _config(policy)
    rendered = RenderedDeployment(
        metadata=_metadata(config, policy), cel=_cel(config), vm=_vm(config, policy),
        containerfile=_containerfile(policy), policy_digest=config.policy_digest,
        claim_paths_digest=config.claim_paths_digest,
        attestation_claims_digest=config.attestation_claims_digest,
        wip_policy_digest=config.wip_policy_digest,
    )
    preflight_deployment(rendered, policy)
    return rendered


def preflight_deployment(rendered: RenderedDeployment, policy: DeploymentPolicy | Mapping[str, Any]) -> None:
    if not isinstance(policy, DeploymentPolicy):
        policy = DeploymentPolicy.from_mapping(policy)
    _validate_policy_values(policy)
    config = _config(policy)
    expected = (config.policy_digest, config.claim_paths_digest, config.attestation_claims_digest, config.wip_policy_digest)
    actual = (rendered.policy_digest, rendered.claim_paths_digest, rendered.attestation_claims_digest, rendered.wip_policy_digest)
    if actual != expected:
        raise DeploymentPreflightError("rendered policy commitments do not match source policy")
    combined = rendered.metadata + rendered.cel + rendered.vm + rendered.containerfile
    if _contains_placeholder(combined):
        raise DeploymentPreflightError("rendered deployment contains unresolved placeholders")
    if _SECRET_RE.search(combined):
        raise DeploymentPreflightError("rendered deployment contains secret-like material")
    expected_image_reference = _image_reference(policy, policy.image_digest)
    parsed_env = _parse_env_lines(rendered.metadata, expected_image_reference)
    expected_env = _environment(config)
    if parsed_env != expected_env:
        raise DeploymentPreflightError("rendered metadata environment drift")
    try:
        parsed = LockedBootstrapConfig.from_env(parsed_env)
    except (RuntimeError, ValueError) as exc:
        raise DeploymentPreflightError("rendered metadata is not a closed locked policy") from exc
    if parsed.policy_digest != rendered.policy_digest or parsed.wip_policy_digest != rendered.wip_policy_digest:
        raise DeploymentPreflightError("rendered policy drift")
    if _parse_vm_env(rendered.vm) != _environment(parsed):
        raise DeploymentPreflightError("rendered VM environment drift")
    if _cel(parsed) != rendered.cel:
        raise DeploymentPreflightError("rendered CEL drift")
    if _containerfile(policy) != rendered.containerfile or f"FROM python:3.12.8-slim-bookworm@{policy.base_image_digest}" not in rendered.containerfile:
        raise DeploymentPreflightError("rendered Containerfile base image drift")
    if 'tee.launch_policy.allow_env_override="' not in rendered.containerfile:
        raise DeploymentPreflightError("Confidential Space environment override policy is missing")
    if f"@{policy.image_digest}" not in rendered.vm:
        raise DeploymentPreflightError("VM image is not digest pinned")
    if "run.googleapis.com/ingress: internal" not in rendered.vm or 'autoscaling.knative.dev/maxScale: "1"' not in rendered.vm:
        raise DeploymentPreflightError("VM isolation settings are not locked")


def deployment_commands(policy: DeploymentPolicy | Mapping[str, Any]) -> tuple[str, ...]:
    """Return shell-safe review commands only after complete local preflight."""
    if not isinstance(policy, DeploymentPolicy):
        policy = DeploymentPolicy.from_mapping(policy)
    rendered = render_deployment(policy)
    artifact = f"rendered-{policy.service_name}.yaml"
    if not re.fullmatch(r"rendered-[a-z][a-z0-9-]{0,62}\.yaml", artifact):
        raise DeploymentPreflightError("rendered artifact path is unsafe")
    # shlex.join preserves the historical string API while ensuring these
    # review commands cannot reinterpret policy values through a shell.
    return (
        shlex.join(("gcloud", "iam", "workload-identity-pools", "providers", "describe", policy.provider.rsplit("/", 1)[-1], f"--workload-identity-pool={policy.pool}", "--location=global", f"--project={policy.project_id}")),
        shlex.join(("gcloud", "run", "services", "replace", artifact, f"--region={policy.region}", f"--project={policy.project_id}")),
    )


def confidential_space_commands(policy: DeploymentPolicy | Mapping[str, Any], vm_name: str) -> tuple[str, ...]:
    """Return exact, review-only image and Confidential Space VM commands.

    The VM command consumes a rendered metadata file using gcloud's custom
    delimiter syntax; it is returned for operator review and is never run by
    this module.
    """
    if not isinstance(policy, DeploymentPolicy):
        policy = DeploymentPolicy.from_mapping(policy)
    _validate_policy_values(policy)
    _require_identifier(vm_name, "vm_name")
    candidate = _image_reference(policy, policy.image_digest, tag="candidate")
    metadata_file = f"rendered-{policy.service_name}.metadata"
    metadata_expression = (
        "^|^$(awk 'BEGIN { sep=\"\" } "
        "/^[[:space:]]*#/ || NF == 0 { next } "
        "{ key=$1; sub(/^[^=]*=/, \"\"); printf \"%s%s=%s\", sep, key, $0; sep=\"|\" }' "
        f"{shlex.quote(metadata_file)})"
    )
    return (
        shlex.join(("docker", "build", "--file", "services/p5_r0_evaluator/Dockerfile.confidential-space", "--tag", candidate, ".")),
        shlex.join(("docker", "push", candidate)),
        shlex.join(("gcloud", "artifacts", "docker", "images", "describe", candidate, f"--project={policy.project_id}", "--format=value(image_summary.digest)")),
        " ".join((
            "gcloud compute instances create", shlex.quote(vm_name),
            f"--project={shlex.quote(policy.project_id)}",
            f"--zone={shlex.quote(policy.zone)}",
            "--machine-type=n2d-standard-2",
            "--confidential-compute-type=SEV",
            "--maintenance-policy=TERMINATE",
            "--image-family=confidential-space",
            "--image-project=confidential-space-images",
            f"--metadata={shlex.quote(metadata_expression)}",
        )),
    )


__all__ = ["DEFAULT_RS068_WIP_POLICY", "DEFAULT_RS068_WIP_TEMPLATE", "DeploymentPolicy", "DeploymentPreflightError", "RenderedDeployment", "RenderedWIPPolicy", "confidential_space_commands", "deployment_commands", "preflight_deployment", "render_deployment", "render_wip_policy"]
