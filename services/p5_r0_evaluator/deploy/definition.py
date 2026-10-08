"""Fail-closed validation and local rendering for the RS-040 definition.

This module is deliberately local-only.  It reads a checked-in definition,
validates the immutable native closure shape, and optionally renders the
existing deployment policy through ``deployments.py``.  It never invokes a
cloud SDK, gcloud, Docker, Podman, or an apply operation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from services.p5_r0_evaluator.deployments import (
    DeploymentPreflightError,
    preflight_deployment,
    render_deployment,
)
from evaluation.p5_r0.native import DEFAULT_LIMITS, V3_HOST_CLOSURE_KEYS
from evaluation.p5_r0.protocol import digest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEFINITION = Path(__file__).with_name("p5-r0-native-deployment.json")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PLACEHOLDER_RE = re.compile(
    r"REPLACE_|PROJECT_ID|PROJECT_NUMBER|IMAGE_DIGEST|RUNTIME_DIGEST|"
    r"RESOURCE_PROFILE_DIGEST|REVIEWED_|<[^>]+>|\$\{[^}]+\}"
)

EXPECTED_HOST_PATHS = {
    "host_runner": "evaluation/p5_r0/runner.py",
    "host_native": "evaluation/p5_r0/native.py",
    "host_evaluator": "evaluation/p5_r0/evaluator.py",
    "host_worker_validator": "evaluation/p5_r0/native_worker.py",
    "host_repair": "evaluation/p5_r0/repair.py",
    "host_receipts": "evaluation/p5_r0/receipts.py",
    "host_evidence": "evaluation/p5_r0/evidence.py",
    "host_rollback": "evaluation/p5_r0/rollback.py",
    "host_kill": "evaluation/p0a/supervisor.py",
    "worker": "evaluation/p5_r0/native_worker_entrypoint_v3.py",
    "containerfile": "evaluation/p5_r0/Containerfile.v3",
    "runtime": "/usr/bin/crun",
    "seccomp_profile": "/usr/share/containers/seccomp.json",
}
EXPECTED_ARGV_FLAGS = [
    "--rm",
    "--interactive",
    "--runtime=crun",
    "--pull=never",
    "--network=none",
    "--read-only",
    "--cap-drop=ALL",
    "--security-opt=no-new-privileges",
    "--security-opt=seccomp=/usr/share/containers/seccomp.json",
    "--user=65532:65532",
    "--pid=private",
    "--ipc=private",
    "--uts=private",
    "--pids-limit=32",
    "--memory=512m",
    "--cpus=1",
]
EXPECTED_FIXED_FIELDS = {
    "issuer": "https://confidentialcomputing.googleapis.com",
    "attestation_audience": "https://sts.googleapis.com",
    "debug_state": "disabled-since-boot",
    "tee": "CONFIDENTIAL_SPACE",
    "workload": "evaluator",
    "hardware_model": "GCP_AMD_SEV",
    "secure_boot": True,
    "cpu_limit": "1",
    "memory_limit": "512Mi",
    "confidential_space_smoke": False,
    "timing_bridge_freetsa_ca_pem_path": "/app/services/p5_r0_evaluator/deploy/freetsa-cacert.pem",
}


class DefinitionValidationError(ValueError):
    """The repository definition is malformed or has drifted."""


class DefinitionBlockedError(DefinitionValidationError):
    """The definition is structurally valid but lacks reviewed run/environment bindings."""


@dataclass(frozen=True)
class ValidationReport:
    ready: bool
    missing_inputs: tuple[str, ...]
    definition_digest: str


def _walk_strings(value: Any, path: str = ""):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk_strings(child, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{index}]")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DefinitionValidationError(message)


def _validate_static(definition: Mapping[str, Any], repository_root: Path) -> None:
    _require(definition.get("schema") == "P5R0NativeDeploymentDefinitionV1", "definition schema drift")
    _require(definition.get("classification") == "repository_definition_only", "definition classification drift")
    _require(definition.get("status") == "blocked_pending_reviewed_inputs", "definition status must remain blocked")

    for path, value in _walk_strings(definition):
        if _PLACEHOLDER_RE.search(value):
            raise DefinitionValidationError(f"unresolved placeholder at {path}")

    sources = definition.get("source_files")
    _require(isinstance(sources, Mapping), "source file map is missing")
    for key in ("deployment_renderer", "native_closure_builder", "native_closure_spec", "native_lock_validator", "canonical_containerfile"):
        path = sources.get(key)
        _require(isinstance(path, str) and (repository_root / path).is_file(), f"source file missing: {key}")

    closure = definition.get("native_closure")
    _require(isinstance(closure, Mapping), "native closure is missing")
    _require(closure.get("image") == {"reference": "from:controlled_run_bindings.image_reference", "digest": "from:controlled_run_bindings.image_digest"}, "image closure drift")
    _require(closure.get("runtime") == {"name": "crun", "path": "/usr/bin/crun", "digest": "from:controlled_run_bindings.runtime_digest"}, "runtime closure drift")
    execution = closure.get("execution")
    _require(isinstance(execution, Mapping), "native execution policy is missing")
    _require(execution.get("network") == "none", "native network must be none")
    _require(execution.get("pull") == "never", "native pull policy must be never")
    _require(execution.get("entrypoint") == "/runtime/p5_r0_worker", "native entrypoint drift")
    resource_profile = closure.get("resource_profile")
    _require(isinstance(resource_profile, Mapping), "resource profile is missing")
    _require(dict(resource_profile) == {**DEFAULT_LIMITS, "digest": "from:controlled_run_bindings.resource_profile_digest"}, "resource profile drift")
    seccomp = closure.get("seccomp")
    _require(seccomp == {"profile_path": "/usr/share/containers/seccomp.json", "default_action": "SCMP_ACT_ERRNO", "digest": "from:controlled_run_bindings.seccomp_digest", "allowed_syscalls_digest": "from:controlled_run_bindings.allowed_syscalls_digest"}, "seccomp closure drift")
    argv = closure.get("argv")
    _require(isinstance(argv, Mapping), "native argv is missing")
    _require(argv.get("program") == "podman" and argv.get("subcommand") == "run", "native argv program drift")
    _require(argv.get("flags") == EXPECTED_ARGV_FLAGS and argv.get("image_argument_index") == 18, "native argv flags drift")
    _require(argv.get("entrypoint") == "/runtime/p5_r0_worker", "native argv entrypoint drift")

    host = closure.get("host_closure")
    _require(isinstance(host, Mapping), "host closure is missing")
    _require(set(EXPECTED_HOST_PATHS).issubset(V3_HOST_CLOSURE_KEYS | {"worker", "containerfile", "runtime", "seccomp_profile"}), "host closure key contract drift")
    for key, expected in EXPECTED_HOST_PATHS.items():
        _require(host.get(key) == expected, f"host closure path drift: {key}")

    policy = definition.get("deployment_policy")
    _require(isinstance(policy, Mapping), "deployment policy definition is missing")
    _require(policy.get("fixed_fields") == EXPECTED_FIXED_FIELDS, "deployment policy fixed fields drift")
    _require(set(policy.get("required_fields", [])) == set(_deployment_policy_fields()), "deployment policy field contract drift")
    _require(policy.get("rendered_artifacts") == ["metadata", "cel", "vm", "containerfile"], "rendered artifact contract drift")

    apply_plan = definition.get("apply_plan")
    _require(isinstance(apply_plan, Mapping) and apply_plan.get("mode") == "review_only_no_execution", "apply plan is not review-only")
    _require(apply_plan.get("commands") == [], "apply plan must not contain executable commands")


def _deployment_policy_fields() -> tuple[str, ...]:
    from services.p5_r0_evaluator.deployments import DeploymentPolicy

    return tuple(DeploymentPolicy.__dataclass_fields__)


def _validate_input_shapes(definition: Mapping[str, Any]) -> None:
    inputs = definition.get("controlled_run_bindings")
    _require(isinstance(inputs, Mapping), "controlled-run binding map is missing")
    digest_fields = (
        "image_digest",
        "base_image_digest",
        "runtime_digest",
        "resource_profile_digest",
        "seccomp_digest",
        "allowed_syscalls_digest",
        "argv_digest",
        "closure_digest",
    )
    for field in digest_fields:
        value = inputs.get(field)
        if value is not None:
            _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"invalid controlled-run binding digest: {field}")
    host_digests = inputs.get("host_digests")
    if host_digests is not None:
        _require(isinstance(host_digests, Mapping), "host digest map is malformed")
        for field, value in host_digests.items():
            if value is not None:
                _require(isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None, f"invalid host digest: {field}")
    repository = inputs.get("artifact_registry_repository")
    if repository is not None:
        _require(isinstance(repository, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,62}", repository) is not None, "artifact registry repository is malformed")
        _require(repository == "p5-cs", "artifact registry repository is not the reviewed existing target")
    image_reference = inputs.get("image_reference")
    image_digest = inputs.get("image_digest")
    if image_reference is not None:
        _require(isinstance(image_reference, str), "image reference is malformed")
        if image_digest is not None:
            _require(image_reference.endswith("@" + image_digest), "image reference/digest drift")


def _missing_inputs(definition: Mapping[str, Any]) -> list[str]:
    inputs = definition.get("controlled_run_bindings", {})
    missing: list[str] = []
    if not isinstance(inputs, Mapping):
        return ["controlled_run_bindings"]
    for key, value in inputs.items():
        if value is None:
            missing.append(f"controlled_run_bindings.{key}")
        elif isinstance(value, Mapping):
            for child, child_value in value.items():
                if child_value is None:
                    missing.append(f"controlled_run_bindings.{key}.{child}")
    return missing


def load_definition(path: Path = DEFAULT_DEFINITION) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise DefinitionValidationError("definition cannot be loaded") from exc
    if not isinstance(value, dict):
        raise DefinitionValidationError("definition root must be an object")
    return value


def validate_definition(
    definition: Mapping[str, Any],
    *,
    repository_root: Path = REPOSITORY_ROOT,
    require_complete: bool = False,
) -> ValidationReport:
    _validate_static(definition, Path(repository_root).resolve())
    _validate_input_shapes(definition)
    missing = tuple(_missing_inputs(definition))
    report = ValidationReport(
        ready=not missing,
        missing_inputs=missing,
        definition_digest=digest(dict(definition)),
    )
    if require_complete and missing:
        raise DefinitionBlockedError("reviewed run/environment bindings are required: " + ", ".join(missing))
    return report


def _validate_policy_bindings(definition: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    if not isinstance(policy, Mapping):
        raise DefinitionValidationError("deployment policy input must be an object")
    expected = definition["deployment_policy"]["fixed_fields"]
    for field, value in expected.items():
        if policy.get(field) != value:
            raise DefinitionValidationError(f"deployment policy fixed field drift: {field}")
    inputs = definition["controlled_run_bindings"]
    for field in ("image_digest", "base_image_digest", "runtime_digest", "resource_profile_digest"):
        if inputs.get(field) is not None and policy.get(field) != inputs[field]:
            raise DefinitionValidationError(f"deployment policy/native binding drift: {field}")
    if inputs.get("artifact_registry_repository") is not None and policy.get("artifact_registry_repository") != inputs["artifact_registry_repository"]:
        raise DefinitionValidationError("deployment policy/native binding drift: artifact_registry_repository")


def render_definition(
    definition: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    output_dir: Path,
) -> dict[str, Path]:
    validate_definition(definition, require_complete=True)
    _validate_policy_bindings(definition, policy)
    try:
        rendered = render_deployment(policy)
        preflight_deployment(rendered, policy)
    except (DeploymentPreflightError, TypeError, ValueError) as exc:
        raise DefinitionValidationError("deployment policy preflight failed") from exc
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    service_name = policy["service_name"]
    artifacts = {
        "metadata": output / f"rendered-{service_name}.metadata",
        "cel": output / f"rendered-{service_name}.cel",
        "vm": output / f"rendered-{service_name}.yaml",
        "containerfile": output / f"rendered-{service_name}.Containerfile",
    }
    values = {
        "metadata": rendered.metadata,
        "cel": rendered.cel,
        "vm": rendered.vm,
        "containerfile": rendered.containerfile,
    }
    for name, path in artifacts.items():
        path.write_text(values[name])
    return artifacts


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate/render the local-only RS-040 P5 definition")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    validate_parser.add_argument("--allow-blocked", action="store_true")
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--definition", type=Path, default=DEFAULT_DEFINITION)
    render_parser.add_argument("--policy", type=Path, required=True)
    render_parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        definition = load_definition(args.definition)
        if args.command == "validate":
            report = validate_definition(definition, require_complete=not args.allow_blocked)
            print(json.dumps({"ready": report.ready, "missing_inputs": report.missing_inputs, "definition_digest": report.definition_digest}, sort_keys=True))
            return 0 if report.ready or args.allow_blocked else 2
        policy = json.loads(args.policy.read_text())
        artifacts = render_definition(definition, policy, output_dir=args.output_dir)
        print(json.dumps({name: str(path) for name, path in artifacts.items()}, sort_keys=True))
        return 0
    except (DefinitionValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"RS-040 validation blocked: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return _cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
