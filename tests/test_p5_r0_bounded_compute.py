from __future__ import annotations

from types import SimpleNamespace

import pytest

from evaluation.p5_r0 import bounded_compute
from evaluation.p5_r0 import runner
from evaluation.p5_r0.protocol import P5R0Error, digest


IMAGE = digest("image")
HARDWARE = {
    "hardware_model": "test-cpu",
    "machine_type": "x86_64",
    "vcpu_count": 4,
    "secure_boot": False,
    "tee": "none",
}
LIMITS = {"steps": 8, "frame_bytes": 65536, "wall_seconds": 3, "memory_mb": 512, "cpu": 1, "pids": 32}
TASK = {"schema": "P5R0WorkerTaskV1", "legal_actions": [0, 1], "observation": {"x": 1}}
REPLY = {"schema": "P5R0WorkerReplyV1", "action": 1}


def test_valid_evidence_is_canonical_and_does_not_persist_elapsed_time():
    evidence = bounded_compute.recompute_bounded_compute_evidence(
        task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
        duration_ms=99, hardware_profile=HARDWARE,
    )
    assert set(evidence) == bounded_compute.EVIDENCE_FIELDS
    assert evidence["duration_bucket"] == "<100ms"
    assert "duration_ms" not in evidence and evidence["attestation_status"] == "unattested_local"
    assert bounded_compute.validate_bounded_compute_evidence(
        evidence, task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
        duration_ms=99, hardware_profile=HARDWARE,
    ) == evidence


@pytest.mark.parametrize(
    ("duration", "bucket"),
    [(0, "<100ms"), (99, "<100ms"), (100, "<1s"), (999, "<1s"),
     (1000, "<10s"), (9999, "<10s"), (10000, "<100s"), (99999, "<100s")],
)
def test_duration_bucket_boundaries(duration, bucket):
    assert bounded_compute.duration_bucket(duration) == bucket


def test_timeout_and_over_deadline_are_rejected(monkeypatch):
    monkeypatch.setattr(runner, "hardened_crun_argv", lambda **_: ["fake-worker"])

    class TimedOut:
        pid = 123
        returncode = None

        def communicate(self, *_, **__):
            raise runner.subprocess.TimeoutExpired(["fake-worker"], 3)

        def wait(self, *_, **__):
            self.returncode = -9
            return self.returncode

        def poll(self):
            return self.returncode

    killed = []
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_, **__: TimedOut())
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: killed.append((pid, sig)))
    with pytest.raises(P5R0Error):
        runner._invoke_native_case(
            podman="podman", image_digest=IMAGE, seccomp_profile=__file__,
            task=TASK, return_evidence=True,
        )
    assert killed
    with pytest.raises(P5R0Error):
        bounded_compute.recompute_bounded_compute_evidence(
            task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
            duration_ms=3001, hardware_profile=HARDWARE,
        )


def test_digest_and_resource_tampering_is_rejected():
    evidence = bounded_compute.recompute_bounded_compute_evidence(
        task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
        duration_ms=100, hardware_profile=HARDWARE,
    )
    for field, replacement in (("input_digest", digest("changed")), ("result_digest", digest("changed")),
                               ("image_digest", digest("other-image")), ("vcpu_count", 8),
                               ("max_cpu_millis", 1), ("resource_profile_digest", digest("other-profile"))):
        forged = dict(evidence)
        forged[field] = replacement
        with pytest.raises(P5R0Error):
            bounded_compute.validate_bounded_compute_evidence(
                forged, task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
                duration_ms=100, hardware_profile=HARDWARE,
            )


def test_local_construction_rejects_forged_confidential_space_claims():
    local = bounded_compute.recompute_bounded_compute_evidence(
        task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
        duration_ms=100, hardware_profile=HARDWARE,
    )
    assert local["attestation_status"] == "unattested_local"
    token_digest = digest("confidential-space-token")
    with pytest.raises(P5R0Error):
        bounded_compute.recompute_bounded_compute_evidence(
            task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
            duration_ms=100,
            hardware_profile={**HARDWARE, "tee": "confidential_space", "secure_boot": True},
            attestation_digest=token_digest,
            attestation_status="verified_confidential_space",
        )
    with pytest.raises(P5R0Error):
        bounded_compute.recompute_confidential_space_evidence(
            task=TASK, reply=REPLY, image_digest=IMAGE, duration_ms=100,
        )
    with pytest.raises(P5R0Error):
        bounded_compute.recompute_bounded_compute_evidence(
            task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
            duration_ms=100, hardware_profile=HARDWARE,
            attestation_digest=token_digest,
        )


def test_native_evidence_result_path_preserves_action_only_default(monkeypatch):
    monkeypatch.setattr(runner, "hardened_crun_argv", lambda **_: ["fake-worker"])

    class Completed:
        pid = 123
        returncode = 0

        def communicate(self, *_, **__):
            return b'{"action":1,"schema":"P5R0WorkerReplyV1"}', b""

        def poll(self):
            return self.returncode

    monkeypatch.setattr(runner.subprocess, "Popen", lambda *_, **__: Completed())
    assert runner._invoke_native_case(
        podman="podman", image_digest=IMAGE, seccomp_profile=__file__, task=TASK,
    ) == 1
    action, evidence = runner.invoke_native_case_with_evidence(
        podman="podman", image_digest=IMAGE, seccomp_profile=__file__, task=TASK,
        hardware_profile=HARDWARE,
    )
    assert action == 1 and evidence["schema"] == "P5R0BoundedComputeEvidenceV1"
    assert evidence["attestation_status"] == "unattested_local"



def test_invalid_bucket_or_status_and_record_binding_are_rejected():
    evidence = bounded_compute.recompute_bounded_compute_evidence(
        task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
        duration_ms=100, hardware_profile=HARDWARE,
    )
    forged = dict(evidence)
    forged["duration_bucket"] = "not-a-bucket"
    forged["binding_digest"] = digest({key: forged[key] for key in forged if key != "binding_digest"})
    with pytest.raises(P5R0Error):
        bounded_compute.validate_bounded_compute_evidence(
            forged, task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
            duration_ms=100, hardware_profile=HARDWARE,
        )
    forged = dict(evidence)
    forged["deadline_status"] = "over_deadline"
    forged["binding_digest"] = digest({key: forged[key] for key in forged if key != "binding_digest"})
    with pytest.raises(P5R0Error):
        bounded_compute.validate_bounded_compute_evidence(
            forged, task=TASK, reply=REPLY, image_digest=IMAGE, limits=LIMITS,
            duration_ms=100, hardware_profile=HARDWARE,
        )
    record, binding = bounded_compute.attach_bounded_compute_evidence({}, {}, evidence)
    assert record["bounded_compute_evidence_digest"] == binding["bounded_compute_evidence_digest"] == digest(evidence)



def test_production_service_rejects_unverified_native_claim():
    from services.p5_r0_evaluator.schemas import SchemaError, execution_evidence

    value = {
        "schema": "P5R0ExecutionEvidenceV1",
        "closure_digest": digest("closure"),
        "runtime_digest": digest("runtime"),
        "host_digest": digest("host"),
        "kill_digest": digest("kill"),
        "native_verified": True,
    }
    with pytest.raises(SchemaError):
        execution_evidence(value)
