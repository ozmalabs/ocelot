"""Local-only deployment rendering and fail-closed preflight.

This module emits review artifacts and command strings only. It never invokes a
cloud SDK, creates a credential, or mutates a cloud resource.
"""

from dataclasses import dataclass
import json
import re
import shlex
from typing import Any, Mapping

from .confidential_space import (
    DEFAULT_ATTESTATION_ISSUER,
    DEFAULT_WIP_TOKEN_AUDIENCE,
    LockedBootstrapConfig,
    _wip_policy_contract,
)


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
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
    zone: str
    pool: str
    provider: str
    issuer: str
    caller_audience: str
    allowed_subject: str
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
    claim_paths: Mapping[str, str]
    debug_state: str = "disabled-since-boot"
    tee: str = "CONFIDENTIAL_SPACE"
    workload: str = "evaluator"
    hardware_model: str = "GCP_AMD_SEV"
    secure_boot: bool = True
    cpu_limit: str = "1"
    memory_limit: str = "512Mi"
    # Launcher/WIP token audience; distinct from the canonical STS provider.
    attestation_audience: str = DEFAULT_WIP_TOKEN_AUDIENCE

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DeploymentPolicy":
        names = {field for field in cls.__dataclass_fields__}
        if set(value) != names:
            raise DeploymentPreflightError("deployment policy fields are not closed")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise DeploymentPreflightError("deployment policy shape") from exc


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
    for name in ("region", "zone", "pool"):
        _require_identifier(getattr(policy, name), name)
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
    transport = policy.authority.get("transport_attestation") if isinstance(policy.authority, Mapping) else None
    if isinstance(transport, Mapping) and (transport.get("provider") != policy.provider or transport.get("audience") != policy.attestation_audience):
        raise DeploymentPreflightError("authority transport must bind provider and token audience separately")
    if policy.issuer != DEFAULT_ATTESTATION_ISSUER:
        raise DeploymentPreflightError("issuer must be the Google Cloud Attestation issuer")
    for name, value in (("issuer", policy.issuer), ("caller_audience", policy.caller_audience), ("allowed_subject", policy.allowed_subject), ("debug_state", policy.debug_state), ("tee", policy.tee), ("hardware_model", policy.hardware_model), ("workload", policy.workload), ("timing_authority_id", policy.timing_authority_id), ("timing_key_id", policy.timing_key_id), ("timing_ledger_id", policy.timing_ledger_id)):
        _safe_text(value, name)
    if set(policy.claim_paths) != {"audience", "nonce", "issued_at", "expires_at", "issuer", "subject", "image_digest", "project_number", "project_id", "zone", "debug_state", "tee", "hardware_model", "secure_boot", "workload"}:
        raise DeploymentPreflightError("claim paths are not closed")
    for name, value in policy.claim_paths.items():
        if not isinstance(value, str) or not _CLAIM_PATH_RE.fullmatch(value):
            raise DeploymentPreflightError(f"claim path {name} is not CEL-safe")
    if not isinstance(policy.secure_boot, bool):
        raise DeploymentPreflightError("secure_boot must be boolean")
    if not re.fullmatch(r"[0-9]+(?:m)?", policy.cpu_limit) or not re.fullmatch(r"[0-9]+(?:Mi|Gi)", policy.memory_limit):
        raise DeploymentPreflightError("resource limits are invalid")
    _require_digest(policy.image_digest, "image_digest")
    _require_digest(policy.base_image_digest, "base_image_digest")
    _require_digest(policy.runtime_digest, "runtime_digest")
    _require_digest(policy.resource_profile_digest, "resource_profile_digest")
    _require_digest(policy.timing_public_key_digest, "timing_public_key_digest")


def _config(policy: DeploymentPolicy) -> LockedBootstrapConfig:
    _validate_policy_values(policy)
    provider = policy.provider
    try:
        return LockedBootstrapConfig(
            authority=dict(policy.authority), caller_audience=policy.caller_audience,
            allowed_subjects=frozenset({policy.allowed_subject}),
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
            timing_authority_id=policy.timing_authority_id,
            timing_key_id=policy.timing_key_id,
            timing_ledger_id=policy.timing_ledger_id,
            timing_public_key_digest=policy.timing_public_key_digest,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise DeploymentPreflightError("deployment policy does not satisfy locked runtime policy") from exc


def _environment(config: LockedBootstrapConfig) -> dict[str, str]:
    values: dict[str, str] = {
        "P5R0_AUTHORITY_JSON": json.dumps(dict(config.authority), sort_keys=True, separators=(",", ":")),
        "P5R0_AUDIENCE": config.caller_audience,
        "P5R0_ALLOWED_SUBJECTS": ",".join(sorted(config.allowed_subjects)),
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
        "P5R0_ATTESTATION_ISSUER": config.expected_issuer or "",
        "P5R0_BUCKET": config.bucket,
        "P5R0_PREFIX": config.prefix,
        "P5R0_KMS_KEY_VERSION": config.kms_key_version,
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
    suffixes = {
        "audience": "AUDIENCE", "nonce": "NONCE", "issued_at": "ISSUED_AT", "expires_at": "EXPIRES_AT",
        "issuer": "ISSUER", "subject": "SUBJECT", "image_digest": "IMAGE_DIGEST", "project_number": "PROJECT_NUMBER",
        "project_id": "PROJECT_ID", "zone": "ZONE", "debug_state": "DEBUG_STATE", "tee": "TEE",
        "hardware_model": "HARDWARE_MODEL", "secure_boot": "SECURE_BOOT", "workload": "WORKLOAD",
    }
    for name, path in config.claim_paths.items():
        values[f"P5R0_CLAIM_{suffixes[name]}"] = path
    return values


def _metadata(config: LockedBootstrapConfig, policy: DeploymentPolicy) -> str:
    values = _environment(config)
    image_reference = (
        f"{policy.region}-docker.pkg.dev/{config.project_id}/p5/evaluator@{config.image_digest}"
    )
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
        secure_boot=config.secure_boot,
        workload=config.workload,
    )
    mapping = "\n".join(f"  {_cel_string(key)}: {_cel_string(value)}" for key, value in contract["mapping"].items())
    condition = contract["condition"]
    terms = [
        f"assertion.{config.claim_paths['audience']} == {_cel_string(condition['audience_value'])}",
        f"assertion.{config.claim_paths['issuer']} == {_cel_string(condition['issuer'])}",
        f"assertion.{config.claim_paths['image_digest']} == {_cel_string(condition['image_digest'])}",
        f"assertion.{config.claim_paths['project_number']} == {_cel_string(condition['project_number'])}",
        f"assertion.{config.claim_paths['project_id']} == {_cel_string(condition['project_id'])}",
        f"assertion.{config.claim_paths['zone']} == {_cel_string(condition['zone'])}",
        f"assertion.{config.claim_paths['debug_state']} == {_cel_string(condition['debug_state'])}",
        f"assertion.{config.claim_paths['tee']} == {_cel_string(condition['tee'])}",
        f"assertion.{config.claim_paths['hardware_model']} == {_cel_string(condition['hardware_model'])}",
        f"assertion.{config.claim_paths['workload']} == {_cel_string(condition['workload'])}",
        f"assertion.{config.claim_paths['secure_boot']} == {str(condition['secure_boot']).lower()}",
    ]
    return (
        "# Generated from the same frozen policy as runtime claim paths.\n"
        f"attributeMapping = {{\n{mapping}\n}}\n\n"
        "attributeCondition = \"\"\"\n  " + " &&\n  ".join(terms) + "\n\"\"\"\n"
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
        - image: {policy.region}-docker.pkg.dev/{config.project_id}/p5/evaluator@{policy.image_digest}
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
    allow_env_override = ",".join(("P5R0_CONFIDENTIAL_SPACE_BOOTSTRAP", *_environment(config)))
    return f'''# Generated from the reviewed DeploymentPolicy; local artifact only.
FROM python:3.12.8-slim-bookworm@{policy.base_image_digest}
LABEL tee.launch_policy.allow_env_override="{allow_env_override}"

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONHASHSEED=0 \\
    PORT=8080 \\
    P5R0_CONFIDENTIAL_SPACE_BOOTSTRAP=1
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
    expected_image_reference = f"{policy.region}-docker.pkg.dev/{config.project_id}/p5/evaluator@{policy.image_digest}"
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
    image = f"{policy.region}-docker.pkg.dev/{policy.project_id}/p5/evaluator"
    candidate = f"{image}:candidate"
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


__all__ = ["DeploymentPolicy", "DeploymentPreflightError", "RenderedDeployment", "confidential_space_commands", "deployment_commands", "preflight_deployment", "render_deployment"]
