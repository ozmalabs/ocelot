from dataclasses import replace

from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, digest
from services.p5_r0_evaluator.deployments import (
    DeploymentPolicy,
    DeploymentPreflightError,
    confidential_space_commands,
    deployment_commands,
    render_deployment,
)


def _policy() -> DeploymentPolicy:
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    provider = "//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/provider"
    authority = {
        "schema": "P5R0PublicAuthorityV4",
        "authority_id": "receipt-authority",
        "key_id": "receipt-key",
        "public_key": public,
        "public_key_digest": digest(public),
        "transport_attestation": {
            "schema": "P5R0AuthorityTransportV1",
            "provider": provider,
            "audience": "https://sts.googleapis.com",
            "event": "confidential_space_attestation",
        },
    }
    paths = {
        "audience": "aud", "nonce": "eat_nonce", "issued_at": "iat", "expires_at": "exp",
        "issuer": "iss", "subject": "sub", "image_digest": "submods.container.image_digest",
        "project_number": "submods.gce.project_number", "project_id": "submods.gce.project_id", "zone": "submods.gce.zone",
        "debug_state": "dbgstat", "tee": "swname", "hardware_model": "hwmodel", "secure_boot": "secboot",
        "workload": "submods.container.env.P5R0_EXPECTED_WORKLOAD",
    }
    return DeploymentPolicy(
        service_name="p5-evaluator", project_id="project", project_number="123",
        region="us-central1", zone="us-central1-a", pool="pool", provider=provider,
        issuer="https://confidentialcomputing.googleapis.com", caller_audience="https://runner.example",
        allowed_subject="runner@example.iam.gserviceaccount.com", bucket="private-bucket", prefix="v3",
        kms_key_version="projects/project/locations/us/keyRings/p5/cryptoKeys/evaluator/cryptoKeyVersions/1",
        authority=authority, image_digest="sha256:" + "a" * 64, base_image_digest="sha256:" + "b" * 64,
        runtime_digest="sha256:" + "c" * 64, resource_profile_digest="sha256:" + "d" * 64,
        timing_authority_id="independent-authority", timing_key_id="independent-key",
        timing_ledger_id="independent-ledger", timing_public_key_digest="sha256:" + "e" * 64,
        claim_paths=paths, debug_state="disabled-since-boot", tee="CONFIDENTIAL_SPACE",
        hardware_model="GCP_AMD_SEV",
    )


def test_rendered_artifacts_share_complete_policy_and_commands_are_shell_safe():
    policy = _policy()
    rendered = render_deployment(policy)
    assert "P5R0_TIMING_LEDGER_ID" in rendered.metadata
    assert "tee-env-P5R0_ATTESTATION_AUDIENCE=https://sts.googleapis.com" in rendered.metadata
    assert 'assertion.aud == "https://sts.googleapis.com"' in rendered.cel
    assert 'assertion.iss == "https://confidentialcomputing.googleapis.com"' in rendered.cel
    assert 'assertion.submods.container.image_digest' in rendered.cel
    assert 'assertion.submods.gce.project_number' in rendered.cel
    assert 'assertion.submods.gce.project_id' in rendered.cel
    assert 'assertion.submods.gce.zone' in rendered.cel
    assert 'assertion.dbgstat == "disabled-since-boot"' in rendered.cel
    assert 'assertion.swname == "CONFIDENTIAL_SPACE"' in rendered.cel
    assert 'assertion.hwmodel == "GCP_AMD_SEV"' in rendered.cel
    assert 'assertion.secboot == true' in rendered.cel
    assert 'assertion.aud == "//iam.googleapis.com/' not in rendered.cel
    assert rendered.policy_digest.startswith("sha256:")
    assert f"@{policy.base_image_digest}" in rendered.containerfile
    assert deployment_commands(policy)[1].startswith("gcloud run services replace rendered-p5-evaluator.yaml")


def test_rendered_workload_binding_uses_selected_policy_value():
    rendered = render_deployment(replace(_policy(), workload="evaluator-v2"))
    assert "P5R0_EXPECTED_WORKLOAD=evaluator-v2" in rendered.metadata
    assert "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD == \"evaluator-v2\"" in rendered.cel


def test_policy_rejects_provider_resource_used_as_token_audience():
    policy = _policy()
    with pytest.raises(DeploymentPreflightError, match="separate from the provider resource"):
        render_deployment(replace(policy, attestation_audience=policy.provider))


def test_preflight_rejects_vm_environment_drift():
    policy = _policy()
    rendered = render_deployment(policy)
    tampered = replace(rendered, vm=rendered.vm.replace('value: "disabled-since-boot"', 'value: "enabled"', 1))
    with pytest.raises(DeploymentPreflightError, match="VM environment drift"):
        from services.p5_r0_evaluator.deployments import preflight_deployment
        preflight_deployment(tampered, policy)


def test_preflight_rejects_cel_and_base_image_drift():
    policy = _policy()
    rendered = render_deployment(policy)
    with pytest.raises(DeploymentPreflightError, match="CEL drift"):
        from services.p5_r0_evaluator.deployments import preflight_deployment
        preflight_deployment(replace(rendered, cel=rendered.cel.replace("disabled", "enabled", 1)), policy)
    with pytest.raises(DeploymentPreflightError, match="Containerfile base image drift"):
        from services.p5_r0_evaluator.deployments import preflight_deployment
        preflight_deployment(replace(rendered, containerfile=rendered.containerfile.replace(policy.base_image_digest, "sha256:" + "f" * 64)), policy)


def test_policy_rejects_cel_unsafe_claim_path_and_shell_identifier():
    policy = _policy()
    with pytest.raises(DeploymentPreflightError, match="CEL-safe"):
        render_deployment(replace(policy, claim_paths={**policy.claim_paths, "subject": "sub\" || true"}))
    with pytest.raises(DeploymentPreflightError, match="safe GCP identifier"):
        render_deployment(replace(policy, service_name="bad;touch-pwned"))



def test_preflight_rejects_unrecognized_vm_environment_entry():
    from services.p5_r0_evaluator.deployments import preflight_deployment
    policy = _policy()
    rendered = render_deployment(policy)
    tampered = replace(rendered, vm=rendered.vm.replace("          resources:", '            - name: UNREVIEWED\n              value: "x"\n          resources:', 1))
    with pytest.raises(DeploymentPreflightError, match="VM environment drift"):
        preflight_deployment(tampered, policy)



# Local renderer/preflight tests only; these do not invoke deployment commands or cloud APIs.
@pytest.mark.parametrize("field", ("metadata", "cel", "vm", "containerfile"))
def test_preflight_rejects_unresolved_placeholder_in_every_rendered_artifact(field):
    policy = _policy()
    rendered = render_deployment(policy)
    tampered = replace(rendered, **{field: getattr(rendered, field) + "\nREPLACE_PROJECT_ID"})

    from services.p5_r0_evaluator.deployments import preflight_deployment
    with pytest.raises(DeploymentPreflightError, match="unresolved placeholders"):
        preflight_deployment(tampered, policy)



def test_confidential_space_render_uses_dedicated_entrypoint_and_bootstrap_marker():
    policy = _policy()
    rendered = render_deployment(policy)
    assert "confidential_space_app:application" in rendered.containerfile
    assert "P5R0_CONFIDENTIAL_SPACE_BOOTSTRAP=1" in rendered.containerfile
    assert "services.p5_r0_evaluator.app:application" not in rendered.containerfile



def test_confidential_space_probe_uses_authorized_env_and_operator_metadata_shape():
    from pathlib import Path
    import re

    root = Path(__file__).parents[1]
    dockerfiles = [
        root / "Dockerfile.confidential-space",
        root / "deploy" / "Containerfile",
    ]
    labels = []
    for dockerfile in dockerfiles:
        match = re.search(r'tee\.launch_policy\.allow_env_override="([^"]+)"', dockerfile.read_text())
        assert match is not None
        labels.append(set(match.group(1).split(",")))
    assert labels[0] == labels[1]
    assert "P5R0_AUTHORITY_JSON" in labels[0]
    assert "P5R0_EXPECTED_IMAGE_DIGEST" in labels[0]

    metadata = (root / "deploy" / "confidential-space.metadata.example").read_text()
    assert "tee-image-reference=" in metadata
    assert "tee-container-log-redirect=true" in metadata
    assert not re.search(r"^P5R0_[A-Z0-9_]+=", metadata, re.MULTILINE)
    assert "tee-env-P5R0_AUTHORITY_JSON=" in metadata
    assert "tee-env-P5R0_EXPECTED_IMAGE_DIGEST=" in metadata

    rendered = render_deployment(_policy())
    rendered_label = re.search(r'tee\.launch_policy\.allow_env_override="([^"]+)"', rendered.containerfile)
    assert rendered_label is not None
    assert set(rendered_label.group(1).split(",")) == labels[0]
    assert "tee-image-reference=us-central1-docker.pkg.dev/project/p5/evaluator@sha256:" in rendered.metadata
    assert "tee-container-log-redirect=true" in rendered.metadata
    assert "tee-env-P5R0_AUTHORITY_JSON=" in rendered.metadata
    assert not re.search(r"^P5R0_[A-Z0-9_]+=", rendered.metadata, re.MULTILINE)


def test_confidential_space_policy_artifacts_are_non_secret_and_allowlisted():
    from pathlib import Path

    deploy_dir = Path(__file__).parents[1] / "deploy"
    allowed = (deploy_dir / "confidential-space.allowed-env").read_text()
    policy = (deploy_dir / "confidential-space.policy.example.json").read_text()
    assert "P5R0_AUTHORITY_JSON" in allowed
    assert "GOOGLE_APPLICATION_CREDENTIALS" in allowed
    assert "client_credentials" in policy and '"none"' in policy
    assert "private_key" not in policy.lower()
    assert "access_token" not in policy.lower()



def test_confidential_space_commands_pin_image_and_render_metadata_for_review():
    commands = confidential_space_commands(_policy(), "p5-evaluator-cs")
    assert commands[0] == "docker build --file services/p5_r0_evaluator/Dockerfile.confidential-space --tag us-central1-docker.pkg.dev/project/p5/evaluator:candidate ."
    assert commands[1].startswith("docker push us-central1-docker.pkg.dev/project/p5/evaluator:candidate")
    assert commands[2] == "gcloud artifacts docker images describe us-central1-docker.pkg.dev/project/p5/evaluator:candidate --project=project '--format=value(image_summary.digest)'"
    assert commands[3].startswith("gcloud compute instances create p5-evaluator-cs")
    assert "--metadata=" in commands[3] and "rendered-p5-evaluator.metadata" in commands[3]
    assert "--image-family=confidential-space" in commands[3]


def test_confidential_space_labels_match_closed_allowlist_and_forbid_capabilities():
    from pathlib import Path
    import re

    root = Path(__file__).parents[1]
    allowed = {
        line.strip() for line in (root / "deploy" / "confidential-space.allowed-env").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    for path in (root / "Dockerfile.confidential-space", root / "deploy" / "Containerfile"):
        text = path.read_text()
        label = re.search(r'tee\.launch_policy\.allow_env_override="([^"]+)"', text)
        assert label is not None
        assert set(label.group(1).split(",")) == allowed
        assert "tee.launch_policy.log_redirect" not in text
        assert not re.search(r"GOOGLE_APPLICATION_CREDENTIALS|PRIVATE_KEY|ACCESS_TOKEN|TRUTH", label.group(1), re.I)

    probe_path = Path(__file__).parents[2] / "cs_attestation_probe"
    probe = (probe_path / "Dockerfile").read_text()
    source = (probe_path / "probe.py").read_text().lower()
    assert re.findall(r"^LABEL ([^=]+)=", probe, re.MULTILINE) == ["tee.launch_policy.allow_env_override", "tee.launch_policy.log_redirect"]
    assert "CS_EXPECTED_IMAGE_DIGEST" in probe
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in probe
    assert "google.cloud" not in source and "kms" not in source and "truth" not in source
