from dataclasses import replace
from dataclasses import replace
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from services.p5_r0_evaluator.canonical import b64encode, canonical_bytes, digest
from services.p5_r0_evaluator.rfc3161 import FREETSA_CA_PEM_SHA256
from services.p5_r0_evaluator.deployments import (
    DeploymentPolicy,
    DeploymentPreflightError,
    confidential_space_commands,
    deployment_commands,
    render_deployment,
    render_wip_policy,
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
        "smoke": "submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE",
    }
    return DeploymentPolicy(
        service_name="p5-evaluator", project_id="project", project_number="123",
        region="us-central1", artifact_registry_repository="p5-cs", zone="us-central1-a", pool="pool", provider=provider,
        issuer="https://confidentialcomputing.googleapis.com", caller_audience="https://runner.example",
        allowed_subject="runner@example.iam.gserviceaccount.com",
        attestation_subject_prefix="https://www.googleapis.com/compute/v1/projects/project/zones/us-central1-a/instances/",
        bucket="private-bucket", prefix="v3",
        kms_key_version="projects/project/locations/us/keyRings/p5/cryptoKeys/evaluator/cryptoKeyVersions/1",
        authority=authority, image_digest="sha256:" + "a" * 64, base_image_digest="sha256:" + "b" * 64,
        runtime_digest="sha256:" + "c" * 64, resource_profile_digest="sha256:" + "d" * 64,
        timing_authority_id="independent-authority", timing_key_id="independent-key",
        timing_ledger_id="independent-ledger", timing_public_key_digest="sha256:" + "e" * 64,
        timing_bridge_endpoint="https://timing-bridge.example.test/v1/timing",
        timing_bridge_service_account="bridge-service@example.iam.gserviceaccount.com",
        capability_service_account="p5-evaluator@ocelot-proof.iam.gserviceaccount.com",
        timing_bridge_audience="https://timing-bridge.example.test",
        timing_bridge_freetsa_ca_pem_path="/app/services/p5_r0_evaluator/deploy/freetsa-cacert.pem",
        timing_bridge_freetsa_ca_pem_sha256="sha256:" + "f" * 64,
        timing_bridge_freetsa_certificate_sha256="sha256:" + "1" * 64,
        claim_paths=paths, debug_state="disabled-since-boot", tee="CONFIDENTIAL_SPACE",
        hardware_model="GCP_AMD_SEV",
    )


def test_rendered_artifacts_share_complete_policy_and_commands_are_shell_safe():
    policy = _policy()
    rendered = render_deployment(policy)
    expected_image = "us-central1-docker.pkg.dev/project/p5-cs/evaluator@" + policy.image_digest
    assert expected_image in rendered.metadata
    assert expected_image in rendered.vm
    assert "P5R0_TIMING_LEDGER_ID" in rendered.metadata
    assert f"tee-env-P5R0_CAPABILITY_SERVICE_ACCOUNT={policy.capability_service_account}" in rendered.metadata
    assert "tee-env-P5R0_ATTESTATION_AUDIENCE=https://sts.googleapis.com" in rendered.metadata
    assert f"tee-env-P5R0_ATTESTATION_SUBJECT_PREFIX={policy.attestation_subject_prefix}" in rendered.metadata
    assert f'assertion.sub.startsWith("{policy.attestation_subject_prefix}")' in rendered.cel
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




def test_repository_drift_is_rejected_before_rendering_any_target_reference():
    with pytest.raises(DeploymentPreflightError, match="reviewed existing target"):
        render_deployment(replace(_policy(), artifact_registry_repository="p5"))


def test_confidential_space_and_cloud_run_references_share_reviewed_repository():
    policy = _policy()
    rendered = render_deployment(policy)
    commands = confidential_space_commands(policy, "p5-evaluator-cs")
    expected_prefix = "us-central1-docker.pkg.dev/project/p5-cs/evaluator"
    assert expected_prefix in rendered.metadata
    assert expected_prefix in rendered.vm
    assert expected_prefix + ":candidate" in commands[0]
    assert expected_prefix + ":candidate" in commands[1]
    assert expected_prefix + ":candidate" in commands[2]


def test_rendered_smoke_condition_is_digest_bound_and_disabled_by_default():
    base = _policy()
    normal = render_deployment(base)
    smoke = render_deployment(replace(base, confidential_space_smoke=True))
    assert "tee-env-P5R0_CONFIDENTIAL_SPACE_SMOKE=0" in normal.metadata
    assert 'assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == "0"' in normal.cel
    assert "tee-env-P5R0_CONFIDENTIAL_SPACE_SMOKE=1" in smoke.metadata
    assert 'assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == "1"' in smoke.cel
    assert normal.policy_digest != smoke.policy_digest
    assert normal.wip_policy_digest != smoke.wip_policy_digest


def test_capability_service_account_is_committed_and_validated():
    base = _policy()
    changed = replace(base, capability_service_account="p5-evaluator@other-project.iam.gserviceaccount.com")
    assert render_deployment(base).policy_digest != render_deployment(changed).policy_digest
    with pytest.raises(DeploymentPreflightError, match="capability service account"):
        render_deployment(replace(base, capability_service_account="not-an-account"))
    with pytest.raises(DeploymentPreflightError, match="capability service account"):
        render_deployment(replace(base, capability_service_account=""))


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
    with pytest.raises(DeploymentPreflightError, match="ATTESTATION_SUBJECT_PREFIX"):
        render_deployment(replace(policy, attestation_subject_prefix="https://www.googleapis.com/compute/v1/projects/other/zones/us-central1-a/instances/"))
    with pytest.raises(DeploymentPreflightError, match="ATTESTATION_SUBJECT_PREFIX"):
        render_deployment(replace(policy, attestation_subject_prefix=policy.attestation_subject_prefix[:-1]))



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
    assert "tee-image-reference=us-central1-docker.pkg.dev/project/p5-cs/evaluator@sha256:" in rendered.metadata
    assert "tee-container-log-redirect=true" in rendered.metadata
    assert "tee-env-P5R0_AUTHORITY_JSON=" in rendered.metadata
    assert not re.search(r"^P5R0_[A-Z0-9_]+=", rendered.metadata, re.MULTILINE)




def test_confidential_space_recipe_carries_the_pinned_public_freetsa_ca():
    from hashlib import sha256
    from pathlib import Path

    root = Path(__file__).parents[1]
    ca = root / "deploy" / "freetsa-cacert.pem"
    assert "sha256:" + sha256(ca.read_bytes()).hexdigest() == FREETSA_CA_PEM_SHA256
    for recipe in (root / "Dockerfile.confidential-space", root / "deploy" / "Containerfile"):
        text = recipe.read_text()
        assert "COPY services/p5_r0_evaluator/deploy/freetsa-cacert.pem /app/services/p5_r0_evaluator/deploy/freetsa-cacert.pem" in text


def test_confidential_space_policy_artifacts_are_non_secret_and_allowlisted():
    from pathlib import Path

    deploy_dir = Path(__file__).parents[1] / "deploy"
    allowed = (deploy_dir / "confidential-space.allowed-env").read_text()
    policy = (deploy_dir / "confidential-space.policy.example.json").read_text()
    assert "P5R0_AUTHORITY_JSON" in allowed
    assert "P5R0_ATTESTATION_SUBJECT_PREFIX" in allowed
    assert "GOOGLE_APPLICATION_CREDENTIALS" in allowed
    assert "subject_prefix" in policy and "instances/" in policy
    assert "client_credentials" in policy and '"none"' in policy
    assert "private_key" not in policy.lower()
    assert "access_token" not in policy.lower()



def test_confidential_space_commands_pin_image_and_render_metadata_for_review():
    commands = confidential_space_commands(_policy(), "p5-evaluator-cs")
    assert commands[0] == "docker build --file services/p5_r0_evaluator/Dockerfile.confidential-space --tag us-central1-docker.pkg.dev/project/p5-cs/evaluator:candidate ."
    assert commands[1].startswith("docker push us-central1-docker.pkg.dev/project/p5-cs/evaluator:candidate")
    assert commands[2] == "gcloud artifacts docker images describe us-central1-docker.pkg.dev/project/p5-cs/evaluator:candidate --project=project '--format=value(image_summary.digest)'"
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
        assert "tee.launch_policy.log_redirect=\"always\"" in text
        assert not re.search(r"GOOGLE_APPLICATION_CREDENTIALS|PRIVATE_KEY|ACCESS_TOKEN|TRUTH", label.group(1), re.I)

    probe_path = Path(__file__).parents[2] / "cs_attestation_probe"
    probe = (probe_path / "Dockerfile").read_text()
    source = (probe_path / "probe.py").read_text().lower()
    assert re.findall(r"^LABEL ([^=]+)=", probe, re.MULTILINE) == ["tee.launch_policy.allow_env_override", "tee.launch_policy.log_redirect"]
    assert "CS_EXPECTED_IMAGE_DIGEST" in probe
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in probe
    assert "google.cloud" not in source and "kms" not in source and "truth" not in source



def test_standalone_wip_template_contains_complete_review_mapping():
    template = (Path(__file__).resolve().parents[1] / "deploy" / "wip-provider-policy.cel.tmpl").read_text()
    for term in (
        '"attribute.debug_state": "assertion.dbgstat"',
        '"attribute.tee": "assertion.swname"',
        '"attribute.hardware_model": "assertion.hwmodel"',
        '"attribute.secure_boot": "assertion.secboot"',
        '"attribute.workload": "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD"',
        '"attribute.confidential_space_smoke": "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE"',
        "assertion.aud == 'https://sts.googleapis.com'",
        "assertion.iss == 'https://confidentialcomputing.googleapis.com'",
        "assertion.sub.startsWith('https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/')",
        "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == '0'",
    ):
        assert term in template
    assert "assertion.aud == '//iam.googleapis.com/" not in template



def _rs068_policy() -> DeploymentPolicy:
    base = _policy()
    provider = "//iam.googleapis.com/projects/141633828616/locations/global/workloadIdentityPools/p5-cs-pool/providers/p5-cs-production"
    authority = dict(base.authority)
    authority["transport_attestation"] = {
        "schema": "P5R0AuthorityTransportV1",
        "provider": provider,
        "audience": "https://sts.googleapis.com",
        "event": "confidential_space_attestation",
    }
    return replace(
        base,
        project_id="ocelot-proof",
        project_number="141633828616",
        zone="us-east1-b",
        pool="p5-cs-pool",
        provider=provider,
        authority=authority,
        attestation_subject_prefix="https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/",
        image_digest="sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c",
        kms_key_version="projects/ocelot-proof/locations/global/keyRings/p5-evaluator/cryptoKeys/p5-v3-authority/cryptoKeyVersions/1",
        capability_service_account="p5-evaluator@ocelot-proof.iam.gserviceaccount.com",
    )


def test_rs068_renderer_proves_complete_mapping_and_condition_parity():
    rendered = render_wip_policy(_rs068_policy())
    assert set(rendered.mapping) == {
        "google.subject", "attribute.image_digest", "attribute.project_number", "attribute.project_id",
        "attribute.zone", "attribute.debug_state", "attribute.tee", "attribute.hardware_model",
        "attribute.secure_boot", "attribute.workload", "attribute.confidential_space_smoke",
    }
    assert rendered.mapping["attribute.debug_state"] == "assertion.dbgstat"
    assert rendered.mapping["attribute.tee"] == "assertion.swname"
    assert rendered.mapping["attribute.hardware_model"] == "assertion.hwmodel"
    assert rendered.mapping["attribute.secure_boot"] == "assertion.secboot"
    for term in (
        "assertion.aud == 'https://sts.googleapis.com'",
        "assertion.iss == 'https://confidentialcomputing.googleapis.com'",
        "assertion.sub.startsWith('https://www.googleapis.com/compute/v1/projects/ocelot-proof/zones/us-east1-b/instances/')",
        "assertion.submods.container.image_digest == 'sha256:394a0707d1e162315bdf22de4ff034a7cf75a32b919cef6f12bba501521be11c'",
        "assertion.dbgstat == 'disabled-since-boot'",
        "assertion.swname == 'CONFIDENTIAL_SPACE'",
        "assertion.hwmodel == 'GCP_AMD_SEV'",
        "assertion.secboot == true",
        "assertion.submods.container.env.P5R0_EXPECTED_WORKLOAD == 'evaluator'",
        "assertion.submods.container.env.P5R0_CONFIDENTIAL_SPACE_SMOKE == '0'",
    ):
        assert term in rendered.condition
    assert rendered.policy_digest.startswith("sha256:")
    assert rendered.source_digest.startswith("sha256:")


@pytest.mark.parametrize("mutation, message", [
    (lambda value: value["mapping"].pop("attribute.debug_state"), "mapping drift"),
    (lambda value: value["authority"].update({"key_id": "wrong-key"}), "authority source drift"),
    (lambda value: value["bound_claims"]["values"].update({"zone": "other-zone"}), "claim source drift"),
    (lambda value: value["condition"].update({"secure_boot": "assertion.secboot == false"}), "condition drift"),
])
def test_rs068_renderer_rejects_policy_source_drift(tmp_path, mutation, message):
    source = json.loads((Path(__file__).parents[1] / "deploy" / "rs-068-wip-policy-remediation.json").read_text())
    mutation(source)
    path = tmp_path / "rs-068-policy.json"
    path.write_bytes(canonical_bytes(source))
    with pytest.raises(DeploymentPreflightError, match=message):
        render_wip_policy(_rs068_policy(), remediation_policy=path)


def test_rs068_renderer_rejects_template_mapping_omission(tmp_path):
    template = (Path(__file__).parents[1] / "deploy" / "wip-provider-policy.cel.tmpl").read_text()
    path = tmp_path / "wip-policy.cel.tmpl"
    path.write_text(template.replace('  "attribute.debug_state": "assertion.dbgstat",\n', ""))
    with pytest.raises(DeploymentPreflightError, match="template drift"):
        render_wip_policy(_rs068_policy(), template=path)
