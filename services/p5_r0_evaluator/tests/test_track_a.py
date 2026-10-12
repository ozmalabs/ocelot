from __future__ import annotations

import tempfile
from dataclasses import replace

import pytest

pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p5_r0.receipts import ReceiptChain
from evaluation.p5_r0.rs050_contract import contract_digest
from services.p5_r0_evaluator.canonical import b64encode, digest
from services.p5_r0_evaluator.input_builder import input_builder_binding
from services.p5_r0_evaluator.tests.test_one_shot import _binding
from services.p5_r0_evaluator.time_seed import derive_time_seed, time_seed_algorithm_binding
from services.p5_r0_evaluator.signing import KMSEd25519Signer, issue_verifier_kms_capability
from services.p5_r0_evaluator.deploy.iam_predecessor import issue_verified_iam_predecessor
from services.p5_r0_evaluator.track_a import (
    TrackAConfig,
    TrackAResult,
    TrackARunner,
    TrackASelection,
    TrackACapabilities,
    issue_verifier_supervisor_capability,
    _kms_authority_commitment,
    _canonical_result_digest,
)


# Keep the fake objects interface-shaped: no callback fields or local
# native_verified/attested promotion flags are supplied to the runner.
class _Builder:
    binding = input_builder_binding()
    algorithm_binding = time_seed_algorithm_binding()

    def build(self, seed):
        return {"seed": seed}


class _KMSClient:
    def __init__(self, key):
        self.key = key

    def get_public_key(self, *, request):
        class Response:
            algorithm = "EC_SIGN_ED25519"
            pem = self.key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        return Response()

    def asymmetric_sign(self, *, request):
        class Response:
            signature = self.key.sign(request["data"])
        return Response()


def _signer():
    key = Ed25519PrivateKey.generate()
    public = b64encode(key.public_key().public_bytes_raw())
    authority = {
        "schema": "P5R0PublicAuthorityV4", "authority_id": "self-custodied/evaluator",
        "key_id": "result-key", "public_key": public, "public_key_digest": digest(public),
        "transport_attestation": {"schema": "P5R0AuthorityTransportV1", "provider": "provider", "audience": "audience", "event": "confidential_space_attestation"},
    }
    capability = issue_verifier_kms_capability(issuer="structural-test-adapter", key_version="projects/project/locations/us/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1", authority=authority)
    return KMSEd25519Signer("projects/project/locations/us/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1", authority, client=_KMSClient(key), verifier_capability=capability)


class _TimingVerifier:
    def verify(self, record, *, run_id, event):
        return {"status": "verified", "record_digest": digest(dict(record)), "authority_digest": digest("timing-authority")}


class _Supervisor:
    """Explicit verifier-issued test capability; not external evidence."""

    capability = issue_verifier_supervisor_capability(
        issuer="structural-test-adapter",
        commitment={"schema": "P5R0TrackASupervisorCapabilityV1", "authority_id": "test-supervisor"},
        observation=lambda _value: True,
        resource=lambda _value: True,
    )


class _Worker:
    def __init__(self, run_id, lock_digest, closure_digest):
        self.run_id = run_id
        self.lock_digest = lock_digest
        self.closure_digest = closure_digest
        self.calls = []

    def preflight(self, closure):
        value = {"schema": "P5R0TrackAClosurePreflightV1", "status": "verified", "closure_digest": closure["closure_digest"]}
        value["preflight_digest"] = digest(value)
        return value

    def execute(self, task):
        self.calls.append(task)
        action = 99 if task["task"]["control"] else 0
        reply = {"schema": "P5R0WorkerReplyV3", "action": action}
        task_id = task["task_id"]
        identity = {
            "schema": "P5R0SupervisorIdentityV1",
            "supervisor_id": "test-supervisor",
            "authority_key_digest": digest("supervisor-key"),
            "authentication_method": "attested_channel",
        }
        identity["identity_digest"] = digest(identity)
        supervisor_evidence = {
            "schema": "P5R0SupervisorEvidenceV1", "run_id": self.run_id,
            "lock_digest": self.lock_digest, "closure_digest": self.closure_digest,
            "supervisor_digest": identity["identity_digest"], "worker_invocations": 1,
            "worker_exit": 0, "observed": True, "timed_out": False, "oom": False,
            "process_group_killed": False, "cleanup_verified": True,
            "attestation_status": "verified_supervisor_observation", "evidence_digest": "",
        }
        supervisor_evidence["evidence_digest"] = digest({k: supervisor_evidence[k] for k in supervisor_evidence if k != "evidence_digest"})
        resource_digest = digest("resource")
        invocation = {
            "schema": "P5R0RS050InvocationV1", "run_id": self.run_id,
            "lock_digest": self.lock_digest, "closure_digest": self.closure_digest,
            "supervisor_digest": identity["identity_digest"], "task_id": task_id,
            "sequence": 1, "worker_exit": 0, "timed_out": False, "oom": False,
            "process_group_killed": False, "cleanup_verified": True, "observed": True,
            "resource_profile_digest": resource_digest,
            "resource_observation_digest": digest({"task": task_id}), "evidence_digest": "",
        }
        invocation["evidence_digest"] = digest({k: invocation[k] for k in invocation if k != "evidence_digest"})
        evidence = {
            "schema": "P5R0RS050EvidenceV1", "run_id": self.run_id,
            "lock_digest": self.lock_digest, "closure_digest": self.closure_digest,
            "resource_profile_digest": resource_digest, "supervisor_identity": identity,
            "supervisor_evidence": supervisor_evidence, "worker_invocations": 1,
            "invocations": [invocation],
            "claim_boundary": "Authenticated external supervisor/resource evidence only; no native result, release, adoption, independent evaluation, or promotion claim.",
            "contract_digest": contract_digest(), "evidence_digest": "",
        }
        evidence["evidence_digest"] = digest({k: evidence[k] for k in evidence if k != "evidence_digest"})
        return reply, evidence


class _SealStore:
    def __init__(self):
        self.value = None
        self.calls = []

    def create(self, result):
        value = {"schema": "P5R0TrackAResultSealV1", "run_id": result["run_id"], "result_digest": _canonical_result_digest(result), "chain_digest": result["receipt_chain_digest"], "seal_digest": ""}
        value["seal_digest"] = digest({key: value[key] for key in value if key != "seal_digest"})
        return value

    def persist(self, run_id, seal):
        self.calls.append("persist")
        self.value = dict(seal)

    def read(self, run_id):
        self.calls.append("read")
        return dict(self.value)

    def verify(self, result, seal):
        self.calls.append("verify")
        return {"status": "verified", "seal_digest": digest(dict(seal))}


class _Execution:
    def __init__(self, selection, builder, worker):
        self.selection = selection
        self.builder = builder
        self.worker = worker
        self.calls = []
        self.attestation_binding_digest = None
        self.input_namespace = "track-a-inputs"
        self.run_id = digest("track-a-run")
        self.receipt_key = Ed25519PrivateKey.generate()
        self.receipt_root = tempfile.TemporaryDirectory()
        self.failure_receipt_root = tempfile.TemporaryDirectory()
        self.timing = {
            "schema": "P5R0IndependentTimingAttestationV3", "ledger_id": "ledger",
            "run_id": self.run_id, "task_id": digest("timing-task"), "event": "task_issued",
            "sequence": 1, "previous_digest": None, "seed_digest": digest("seed"),
            "payload_digest": digest("payload"), "observed_at": "2026-01-01T00:00:00Z",
            "authority_id": "timing-authority", "key_id": "timing-key",
            "public_key": "timing-public", "public_key_digest": digest("timing-public"),
            "rfc3161_evidence_digest": digest("freetsa"), "signature": "bridge-signature",
        }

    def start(self, selection, inputs):
        self.calls.append("start")
        return self.run_id

    def acquire_timing_record(self, run_id, namespace):
        self.calls.append("timing")
        return {"timing_record": self.timing, "timing_record_digest": digest(self.timing)}

    def _task(self, control_id):
        task = {"schema": "P5R0WorkerTaskV3", "case_token": digest("case-token"),
                "task_nonce": digest(control_id or "task"), "observation": {"x": 1},
                "legal_actions": ["left", "right"], "protocol_budget": {"frame_bytes": 65536},
                "episode_step": 0, "reset_policy": "fresh_case", "arm": "cold_reset",
                "persistent_projection": {}, "control": ({"control_id": control_id} if control_id else None)}
        return {"schema": "P5R0TrackATaskEnvelopeV1", "run_id": self.run_id,
                "task_id": digest({"control": control_id}), "sequence": 1,
                "case_id": self.selection.case_id, "case_digest": self.selection.case_digest,
                "ordinal": self.selection.ordinal, "arm": "cold_reset", "task": task,
                "task_digest": digest(task), "control_id": control_id}

    def issue_task(self, run_id, selection, seeded):
        self.calls.append("task")
        return self._task(None)

    def submit_task(self, run_id, task, reply, evidence):
        self.calls.append("submit_task")
        return {"run_id": self.run_id, "outcome": "complete_correct", "task_digest": task["task_digest"]}

    def issue_control(self, run_id, selection, seeded):
        self.calls.append("control")
        return self._task("illegal_action")

    def submit_control(self, run_id, task, reply, evidence):
        self.calls.append("submit_control")
        return {"run_id": self.run_id, "outcome": "protocol_error", "task_digest": task["task_digest"]}

    def _canonical_result(self, seeded, receipt_chain_digest=None):
        value = {"schema": "P5R0TrackACanonicalResultV1", "run_id": self.run_id,
                 "disposition": "track_a_diagnostic", "claim_boundary": "Self-custodied Track A diagnostic only; no independent evaluator, release, adoption, positive transfer, exact CPU timing, or general-intelligence claim.",
                 "timing_record_digest": seeded.timing_record_digest, "input_seed_digest": seeded.input_seed_digest,
                 "input_digest": seeded.input_digest, "public_input_digest": self.public_input_digest,
                 "access_binding_digest": self.access_binding_digest,
                 "attestation_binding_digest": self.attestation_binding_digest,
                 "closure_digest": self.worker.closure_digest,
                 "supervisor_commitment_digest": digest(dict(_Supervisor.capability.commitment)),
                 "kms_authority_commitment_digest": self.signer_commitment_digest,
                 "kms_key_version": self.signer_key_version,
                 "kms_transport_commitment_digest": self.signer_transport_digest}
        if receipt_chain_digest is not None:
            value["receipt_chain_digest"] = receipt_chain_digest
        return value

    def verify_receipts(self, run_id):
        self.calls.append("receipts")
        task_digest = self._task(None)["task_digest"]
        control_digest = self._task("illegal_action")["task_digest"]
        seeded = derive_time_seed(self.timing, run_id=run_id, namespace=self.input_namespace, sequence=1, input_builder=self.builder.build, input_builder_binding=self.builder.binding, time_seed_algorithm_binding=self.builder.algorithm_binding)
        result_digest = _canonical_result_digest(self._canonical_result(seeded))
        chain = ReceiptChain(self.receipt_root.name, signer=self.receipt_key, authority_id="test-receipt-authority", key_id="test-receipt-key", protocol="V3")
        common = {"run_id": run_id, "closure_digest": self.worker.closure_digest, "timing_record_digest": digest(self.timing), "result_digest": result_digest}
        for kind, extra in (("preregistered", {}), ("start", {}), ("timing", {}), ("task", {"task_digest": task_digest}), ("control", {"task_digest": control_digest}), ("result", {}), ("rollback", {}), ("close", {})):
            chain.append(run_id=run_id, kind=kind, outcome="verified", binding={**common, **extra})
        public = b64encode(self.receipt_key.public_key().public_bytes_raw())
        return {"schema": "P5R0TrackAReceiptVerificationV2", "status": "verified", "run_id": run_id,
                "chain_digest": chain.digest, "task_digest": task_digest, "control_digest": control_digest,
                "timing_record_digest": digest(self.timing), "closure_digest": self.worker.closure_digest,
                "result_digest": result_digest, "authority_id": "test-receipt-authority", "key_id": "test-receipt-key",
                "public_key": public, "public_key_digest": digest(public), "records": chain.records,
                "records_digest": digest(chain.records)}

    def rollback(self, run_id):
        self.calls.append("rollback")
        failure_chain = ReceiptChain(self.failure_receipt_root.name, signer=self.receipt_key, authority_id="test-receipt-authority", key_id="test-receipt-key", protocol="V3")
        for kind in ("impasse", "rollback", "close"):
            failure_chain.append(run_id=run_id, kind=kind, outcome="verified", binding={"run_id": run_id, "rollback_digest": digest("rollback"), "result_digest": digest("failure-result")})
        records_by_kind = {record["payload"]["kind"]: record for record in failure_chain.records}
        links = {
            "rollback_receipt_hash": records_by_kind["rollback"]["receipt_hash"],
            "impasse_receipt_hash": records_by_kind["impasse"]["receipt_hash"],
            "close_receipt_hash": records_by_kind["close"]["receipt_hash"],
        }
        public = b64encode(self.receipt_key.public_key().public_bytes_raw())
        chain = {"schema": "P5R0TrackAFailureReceiptChainV1", "root": self.failure_receipt_root.name,
                 "root_digest": digest(str(__import__("pathlib").Path(self.failure_receipt_root.name).resolve())),
                 "authority_id": "test-receipt-authority", "key_id": "test-receipt-key", "public_key": public,
                 "records": failure_chain.records, "records_digest": digest(failure_chain.records)}
        rollback_digest = digest("rollback")
        closure_receipt = {"schema": "P5R0TrackAClosureReceiptV1", "run_id": run_id, "kind": "close", "status": "verified", "rollback_digest": rollback_digest, "receipt_chain_digest": failure_chain.final_digest, **links, "receipt_digest": ""}
        closure_receipt["receipt_digest"] = digest({key: closure_receipt[key] for key in closure_receipt if key != "receipt_digest"})
        seal = {"schema": "P5R0TrackAImpasseSealV1", "run_id": run_id, "rollback_digest": rollback_digest, "closure_receipt_digest": digest(closure_receipt), "receipt_chain_digest": failure_chain.final_digest, **links, "seal_digest": ""}
        seal["seal_digest"] = digest({key: seal[key] for key in seal if key != "seal_digest"})
        return {"schema": "P5R0TrackAFailureClosureV1", "run_id": run_id, "status": "exact", "rollback_digest": rollback_digest, "receipt_chain_digest": failure_chain.final_digest, "receipt_chain": chain, "closure_receipt": closure_receipt, "impasse_seal": seal}

    def create_result(self, run_id, selection, task_outcome, control_outcome, evidence, receipts, rollback, attestation, seeded):
        self.calls.append("result")
        return self._canonical_result(seeded, receipts["chain_digest"])


class _Adapter:
    def __init__(self, caps, binding):
        self.caps = caps
        self.attestation_binding = binding
        self.startup_evidence = {"schema": "P5R0StartupAttestationEvidenceV1", "status": "attested",
                                 "policy_digest": binding.policy_digest, "claim_paths_digest": binding.claim_paths_digest,
                                 "attestation_claims_digest": binding.attestation_claims_digest, "wip_policy_digest": binding.wip_policy_digest,
                                 "attestation": {"verified": True, "binding_digest": binding.binding_digest, "claims_digest": binding.claims_digest},
                                 "federation": {"exchanged": True, "access_token_digest": binding.federated_token_digest},
                                 "capabilities": "constructed_after_attestation"}
        self.calls = []
        self.activation_commitment = None
        self._provisioned = None
        self._selection = None

    def provision_inputs(self, selection):
        self.calls.append("provision")
        fields = {"schema": "P5R0TrackAProvisionedInputsV1", "status": "provisioned",
                  "lock_digest": selection.lock_digest, "manifest_digest": selection.manifest_digest,
                  "public_input_digest": digest("public"), "private_store_digest": digest("private"),
                  "access_binding_digest": digest("access"), "provisioning_digest": ""}
        fields["provisioning_digest"] = digest({key: fields[key] for key in fields if key != "provisioning_digest"})
        self._selection = selection
        self._provisioned = fields
        return fields

    def activate_attested_capabilities(self, activation_commitment):
        self.calls.append("activate")
        expected = {
            "schema": "P5R0TrackACapabilityActivationV1",
            "lock_digest": self._selection.lock_digest,
            "manifest_digest": self._selection.manifest_digest,
            "worker_contract_digest": self._selection.worker_contract_digest,
            "selection": self._selection.as_dict(),
            "selection_digest": digest(self._selection.as_dict()),
            "public_input_digest": self._provisioned["public_input_digest"],
            "private_store_digest": self._provisioned["private_store_digest"],
            "access_binding_digest": self._provisioned["access_binding_digest"],
            "attestation_binding_digest": self.attestation_binding.binding_digest,
            "provisioning_digest": self._provisioned["provisioning_digest"],
            "iam_receipt_digest": activation_commitment.get("iam_receipt_digest"),
            "iam_ledger_head_digest": activation_commitment.get("iam_ledger_head_digest"),
            "iam_poststate_digest": activation_commitment.get("iam_poststate_digest"),
            "iam_predecessor_digest": activation_commitment.get("iam_predecessor_digest"),
        }
        if (set(activation_commitment) != set(expected) | {"commitment_digest"}
                or any(activation_commitment.get(key) != value for key, value in expected.items())
                or activation_commitment.get("commitment_digest") != digest({key: value for key, value in activation_commitment.items() if key != "commitment_digest"})):
            raise ValueError("activation commitment was not verified")
        self.activation_commitment = dict(activation_commitment)
        self.caps = replace(self.caps, activation_commitment=dict(activation_commitment))
        return self.caps

    def read_and_rehydrate_inputs(self, provisioned):
        self.calls.append("rehydrate")
        value = {"schema": "P5R0TrackARehydratedInputsV1", "status": "verified_fresh_process",
                 **{key: provisioned[key] for key in ("lock_digest", "manifest_digest", "public_input_digest", "private_store_digest", "access_binding_digest")},
                 "rehydration_digest": ""}
        value["rehydration_digest"] = digest({key: value[key] for key in value if key != "rehydration_digest"})
        return value


def _runner():
    selection = TrackASelection(digest("lock"), digest("manifest"), digest("worker"), "case-1", digest("case"), 0)
    builder = _Builder()
    binding = _binding()
    signer = _signer()
    closure = {
        "schema": "P5R0ClosureBindingV3", "bound": True, "image_ref": "candidate@" + binding.image_digest,
        "image_digest": binding.image_digest, "entrypoint": "/runtime/p5_r0_worker",
        "files": {"worker": digest("worker-file")}, "worker_digest": digest("worker-file"),
        "runtime_path": "/usr/bin/crun", "runtime_digest": digest("runtime"),
        "closure_digest": digest("closure"), "seccomp_profile": "/etc/seccomp.json",
        "seccomp_digest": digest("seccomp"), "argv_digest": digest("argv"),
        "limits": {"steps": 8, "frame_bytes": 65536, "wall_seconds": 3, "memory_mb": 512, "cpu": 1, "pids": 32},
        "runtime": "crun", "network": "none", "pull": "never", "worker_contract": "P5R0WorkerContractV3",
    }
    execution = _Execution(selection, builder, None)
    execution.signer_commitment_digest = _kms_authority_commitment(signer, signer.authority)["commitment_digest"]
    execution.signer_key_version = signer.key_version
    execution.signer_transport_digest = digest(signer.authority["transport_attestation"])
    execution.attestation_binding_digest = binding.binding_digest
    execution.public_input_digest = digest("public")
    execution.access_binding_digest = digest("access")
    worker = _Worker(execution.run_id, selection.lock_digest, closure["closure_digest"])
    execution.worker = worker
    caps = TrackACapabilities(execution, worker, _Supervisor.capability, signer, _SealStore(), builder, _TimingVerifier(), closure, binding)
    predecessor_receipt = {"schema": "P5R0APPROVAL023IAMReceiptV1", "operation_id": "provision_gcs_only_iam_boundary", "prestate_digest": digest("iam-prestate"), "service_account": "p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com", "custom_role": "projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1", "wif_principal": "principalSet://test", "condition_expression": "resource.name.startsWith('projects/_/buckets/p5-evaluator-ocelot-proof-141633828616/objects/p5-r0/operation-4/rs069r18r13-op4-04a98e3e/')", "credentials_exported": False, "keys_created": False}
    predecessor_receipt["receipt_digest"] = digest(predecessor_receipt)
    predecessor = issue_verified_iam_predecessor(result={"status": "verified", "operation_id": "provision_gcs_only_iam_boundary", "attempt_id": "dispatch082-iam-20260920-a7f4c2d9", "poststate_digest": digest("iam-poststate"), "ledger_head_digest": digest("iam-ledger"), "receipt": predecessor_receipt, "mutations_performed": True, "later_operations_enabled": False}, evidence_digest=digest("iam-evidence"))
    return TrackARunner(_Adapter(caps, binding), TrackAConfig(selection, "track-a-inputs", predecessor)), execution


def test_track_a_orders_provision_attestation_rehydration_timing_and_seal_before_signature():
    runner, execution = _runner()
    result = runner.run()
    assert isinstance(result, TrackAResult)
    assert result.status == "diagnostic_only"
    assert execution.calls == ["start", "timing", "task", "submit_task", "control", "submit_control", "receipts", "rollback", "result"]
    assert runner.adapter.calls == ["provision", "activate", "rehydrate"]
    assert runner.adapter.caps.seal_store.calls == ["persist", "read", "verify"]
    assert result.final_signature
    public = result.as_dict()
    for field in ("attestation_binding_digest", "timing_record_digest", "input_seed_digest", "input_digest", "public_input_digest", "access_binding_digest", "receipt_chain_digest", "closure_digest", "supervisor_commitment_digest", "kms_authority_commitment_digest", "kms_key_version", "kms_transport_commitment_digest"):
        assert public[field]


def test_track_a_blocks_before_rehydration_without_sealed_attestation():
    runner, _ = _runner()
    runner.adapter.attestation_binding = None
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "attestation_binding_unavailable"
    assert runner.adapter.calls == ["provision"]


def test_track_a_rejects_local_boolean_worker_fallback():
    runner, _ = _runner()
    runner.adapter.caps = TrackACapabilities(runner.adapter.caps.execution, object(), runner.adapter.caps.supervisor,
                                             runner.adapter.caps.signer, runner.adapter.caps.seal_store,
                                             runner.adapter.caps.input_builder, runner.adapter.caps.timing_verifier,
                                             runner.adapter.caps.closure,
                                             runner.adapter.caps.attestation_binding)
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "worker_interface"



def test_track_a_requires_verified_timing_before_task_issue():
    runner, execution = _runner()
    caps = runner.adapter.caps
    runner.adapter.caps = TrackACapabilities(caps.execution, caps.worker, caps.supervisor, caps.signer,
                                             caps.seal_store, caps.input_builder, object(), caps.closure,
                                             caps.attestation_binding)
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "timing_verifier_interface"
    assert execution.calls == ["start", "timing", "rollback"]


def test_track_a_rejects_local_signer_before_input_read():
    runner, _ = _runner()
    caps = runner.adapter.caps

    class LocalSigner:
        authority = caps.signer.authority

        def sign_digest(self, value):
            return "local"

    runner.adapter.caps = TrackACapabilities(caps.execution, caps.worker, caps.supervisor, LocalSigner(),
                                             caps.seal_store, caps.input_builder, caps.timing_verifier,
                                             caps.closure, caps.attestation_binding)
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "kms_signer_required"
    assert runner.adapter.calls == ["provision", "activate"]


def test_track_a_rolls_back_after_post_start_worker_failure():
    runner, execution = _runner()
    caps = runner.adapter.caps

    def fail(_task):
        raise RuntimeError("worker unavailable")

    caps.worker.execute = fail
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "worker_execution_unavailable"
    assert execution.calls == ["start", "timing", "task", "rollback"]



def test_track_a_never_builds_input_before_timing_verification():
    runner, execution = _runner()
    builder = runner.adapter.caps.input_builder
    calls = []
    original = builder.build

    def build(seed):
        calls.append(seed)
        return original(seed)

    builder.build = build

    class FailingTimingVerifier:
        def verify(self, record, *, run_id, event):
            raise RuntimeError("unverified timing")

    caps = runner.adapter.caps
    runner.adapter.caps = TrackACapabilities(caps.execution, caps.worker, caps.supervisor, caps.signer,
                                             caps.seal_store, builder, FailingTimingVerifier(), caps.closure,
                                             caps.attestation_binding)
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "timing_proof_unavailable"
    assert calls == []
    assert execution.calls == ["start", "timing", "rollback"]


def test_track_a_rejects_self_declared_supervisor_flags():
    runner, execution = _runner()

    class LegacySupervisor:
        trusted = True
        independent = True

        def validate_execution_evidence(self, _value):
            return True

        def validate_bounded_compute_claim(self, _value):
            return True

    caps = runner.adapter.caps
    runner.adapter.caps = TrackACapabilities(caps.execution, caps.worker, LegacySupervisor(), caps.signer,
                                             caps.seal_store, caps.input_builder, caps.timing_verifier,
                                             caps.closure, caps.attestation_binding)
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "supervisor_capability_required"
    assert execution.calls == []


def test_track_a_recomputes_and_verifies_the_receipt_chain():
    runner, execution = _runner()
    original = execution.verify_receipts

    def forged(run_id):
        value = original(run_id)
        value["chain_digest"] = digest("forged-chain")
        return value

    execution.verify_receipts = forged
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "receipt_chain_digest"
    assert execution.calls[-1] == "rollback"


def test_track_a_rejects_replayed_task_run_id():
    runner, execution = _runner()
    original = execution.issue_task

    def replay(run_id, selection, seeded):
        task = dict(original(run_id, selection, seeded))
        task["run_id"] = digest("different-run")
        return task

    execution.issue_task = replay
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "task_run_mismatch"


def test_track_a_requires_verifier_issued_kms_capability():
    runner, _execution = _runner()
    runner.adapter.caps.signer.verifier_capability = None
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "kms_capability_required"
    assert runner.adapter.calls == ["provision", "activate"]


def test_track_a_failure_persists_and_verifies_impasse_seal():
    runner, execution = _runner()
    caps = runner.adapter.caps

    def fail(_task):
        raise RuntimeError("worker unavailable")

    caps.worker.execute = fail
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "worker_execution_unavailable"
    assert caps.seal_store.calls == ["persist", "read", "verify"]



def test_track_a_cross_checks_receipt_result_digest_with_final_result():
    runner, execution = _runner()
    original = execution.verify_receipts

    def forged(run_id):
        value = original(run_id)
        value["result_digest"] = digest("different-final-result")
        previous = None
        first_hash = None
        for record in value["records"]:
            payload = dict(record["payload"])
            binding = dict(payload["binding"])
            binding["result_digest"] = value["result_digest"]
            if first_hash is not None:
                binding["preregistration_receipt_hash"] = first_hash
            payload["binding"] = binding
            record["payload"] = payload
            record["previous_hash"] = previous
            record["receipt_hash"] = object_hash(record, "receipt_hash", "signature")
            record["signature"] = sign(record, execution.receipt_key, "receipt_hash")
            if first_hash is None:
                first_hash = record["receipt_hash"]
            previous = record["receipt_hash"]
        value["records_digest"] = digest(value["records"])
        value["chain_digest"] = digest(value["records"])
        return value

    from evaluation.p0a.canonical import object_hash, sign
    execution.verify_receipts = forged
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "receipt_result_digest_mismatch"


def test_track_a_failure_closure_requires_close_receipt_cross_links():
    runner, execution = _runner()
    original = execution.rollback

    def forged(run_id):
        value = original(run_id)
        receipt = dict(value["closure_receipt"])
        receipt["rollback_digest"] = digest("wrong-rollback")
        value["closure_receipt"] = receipt
        return value

    execution.rollback = forged
    runner.adapter.caps.worker.execute = lambda _task: (_ for _ in ()).throw(RuntimeError("worker unavailable"))
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "rollback_unverified"


def test_track_a_failure_closure_reloads_and_verifies_durable_append_only_chain():
    runner, execution = _runner()
    original = execution.rollback

    def forged(run_id):
        value = original(run_id)
        chain = dict(value["receipt_chain"])
        records = [dict(record) for record in chain["records"]]
        records[1]["previous_hash"] = None
        chain["records"] = records
        value["receipt_chain"] = chain
        return value

    execution.rollback = forged
    runner.adapter.caps.worker.execute = lambda _task: (_ for _ in ()).throw(RuntimeError("worker unavailable"))
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "rollback_unverified"


def test_track_a_synthetic_capability_is_explicitly_non_promotable():
    runner, _ = _runner()
    result = runner.run()
    public = result.as_dict()
    assert result.status == "diagnostic_only"
    assert public["production_promotable"] is False


def test_track_a_rejects_production_claim_without_real_kms_capability():
    runner, _ = _runner()
    runner.adapter.caps = replace(runner.adapter.caps, production_promotable=True)
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "production_kms_capability_required"


def test_track_a_binds_activation_to_lock_manifest_private_input_and_selection():
    runner, _ = _runner()
    result = runner.run()
    assert result.status == "diagnostic_only"
    commitment = runner.adapter.activation_commitment
    assert commitment["lock_digest"] == runner.config.selection.lock_digest
    assert commitment["manifest_digest"] == runner.config.selection.manifest_digest
    assert commitment["private_store_digest"] == digest("private")
    assert commitment["selection_digest"] == digest(runner.config.selection.as_dict())


def test_track_a_rejects_capability_activation_commitment_drift():
    runner, _ = _runner()
    original = runner.adapter.activate_attested_capabilities

    def forged(commitment):
        capabilities = original(commitment)
        altered = dict(commitment)
        altered["private_store_digest"] = digest("other-private-store")
        return replace(capabilities, activation_commitment=altered)

    runner.adapter.activate_attested_capabilities = forged
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "capability_activation_commitment"
    assert runner.adapter.calls == ["provision", "activate"]



def test_track_a_rejects_stale_startup_attestation_before_activation():
    runner, _ = _runner()
    runner.adapter.startup_evidence["policy_digest"] = digest("stale-policy")
    result = runner.run()
    assert result.status == "blocked"
    assert result.reason_code == "attestation_binding_mismatch"
    assert runner.adapter.calls == ["provision"]


def test_track_a_activation_and_result_expose_all_input_commitments():
    runner, _ = _runner()
    result = runner.run()
    commitment = runner.adapter.activation_commitment
    assert commitment["worker_contract_digest"] == runner.config.selection.worker_contract_digest
    assert commitment["selection"] == runner.config.selection.as_dict()
    assert commitment["selection_digest"] == digest(runner.config.selection.as_dict())
    assert commitment["public_input_digest"] == digest("public")
    assert commitment["private_store_digest"] == digest("private")
    assert commitment["access_binding_digest"] == digest("access")
    assert commitment["attestation_binding_digest"] == runner.adapter.attestation_binding.binding_digest
    public = result.as_dict()
    assert public["public_input_digest"] == digest("public")
    assert public["access_binding_digest"] == digest("access")


def test_track_a_rejects_failure_closure_without_impasse_member():
    runner, execution = _runner()
    original = execution.rollback

    def forged(run_id):
        value = original(run_id)
        chain = dict(value["receipt_chain"])
        records = [record for record in chain["records"] if record["payload"]["kind"] != "impasse"]
        chain["records"] = records
        chain["records_digest"] = digest(records)
        value["receipt_chain"] = chain
        value["receipt_chain_digest"] = digest(records)
        receipt = dict(value["closure_receipt"])
        receipt["receipt_chain_digest"] = value["receipt_chain_digest"]
        receipt["receipt_digest"] = digest({key: receipt[key] for key in receipt if key != "receipt_digest"})
        value["closure_receipt"] = receipt
        seal = dict(value["impasse_seal"])
        seal["closure_receipt_digest"] = digest(receipt)
        seal["receipt_chain_digest"] = value["receipt_chain_digest"]
        seal["seal_digest"] = digest({key: seal[key] for key in seal if key != "seal_digest"})
        value["impasse_seal"] = seal
        return value

    execution.rollback = forged
    runner.adapter.caps.worker.execute = lambda _task: (_ for _ in ()).throw(RuntimeError("worker unavailable"))
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "rollback_unverified"


def test_track_a_rejects_failure_receipt_member_cross_link_drift():
    runner, execution = _runner()
    original = execution.rollback

    def forged(run_id):
        value = original(run_id)
        receipt = dict(value["closure_receipt"])
        receipt["close_receipt_hash"] = digest("wrong-close")
        receipt["receipt_digest"] = digest({key: receipt[key] for key in receipt if key != "receipt_digest"})
        value["closure_receipt"] = receipt
        seal = dict(value["impasse_seal"])
        seal["closure_receipt_digest"] = digest(receipt)
        seal["seal_digest"] = digest({key: seal[key] for key in seal if key != "seal_digest"})
        value["impasse_seal"] = seal
        return value

    execution.rollback = forged
    runner.adapter.caps.worker.execute = lambda _task: (_ for _ in ()).throw(RuntimeError("worker unavailable"))
    result = runner.run()
    assert result.status == "impasse"
    assert result.reason_code == "rollback_unverified"
