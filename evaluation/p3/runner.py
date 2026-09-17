"""P3-R0 coordinator: finite staged worker/evaluator path and mandatory no-adoption."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import object_hash
from .admission import (P3ReadinessRequestV1, StagedCandidateV1, deny_before_evaluation,
                        reject_and_rollback, terminal_rollback_impasse, validate_and_stage, verify_preflight)
from .execution import P3EvaluatorClient, P3ExecutionFailure, P3WorkerClient
from .lock import P3ReleaseLockV1
from .protocol import P3ProtocolError
from .receipts import P3ReceiptLog, receipt_payload
from .staging import validate_staging_index
from .study import (DISTRIBUTIONS, e1_decision, materialize_study, release_next,
                    score_four_arm_distribution, seal_results)


@dataclass
class P3R0Runner:
    lock: P3ReleaseLockV1
    receipt_log: P3ReceiptLog
    trusted_p2_keys: Mapping[str, Any]
    trusted_p0_keys: Mapping[str, Any] = field(default_factory=dict)
    trusted_p1_keys: Mapping[str, Any] = field(default_factory=dict)

    def _admit(self, request: P3ReadinessRequestV1, proposal: Mapping[str, Any] | None) -> StagedCandidateV1:
        if proposal is None: raise P3ProtocolError("proposal required")
        verify_preflight(request, self.lock, trusted_p0_keys=self.trusted_p0_keys,
                         trusted_p1_keys=self.trusted_p1_keys, trusted_p2_keys=self.trusted_p2_keys)
        return validate_and_stage(request=request, proposal=proposal, lock=self.lock)

    def run(self, request: P3ReadinessRequestV1, *, proposal: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """R0 admits only to restore: it cannot evaluate or adopt through a host seam."""
        try:
            staged=self._admit(request, proposal)
        except Exception as exc:
            return deny_before_evaluation(receipt_log=self.receipt_log, lock=self.lock, reason=f"preflight:{type(exc).__name__}", proposal=proposal)
        try:
            return reject_and_rollback(candidate=request.candidate, pre_snapshot=request.pre_snapshot, receipt_log=self.receipt_log,
                                       lock=self.lock, proposal_digest=staged.proposal_digest, reason="P3-R0 local-test no-adoption rejection")
        except Exception as exc:
            return terminal_rollback_impasse(candidate=request.candidate, pre_snapshot=request.pre_snapshot, receipt_log=self.receipt_log,
                                             lock=self.lock, proposal_digest=staged.proposal_digest, cause=exc)

    def _verify_execution_closure(self, *, worker: P3WorkerClient, evaluator: P3EvaluatorClient,
                                  staging_index: Path, staging_root: Path) -> dict[str, Any]:
        index=validate_staging_index(staging_index, root=staging_root, lock=self.lock)
        evaluator_entry=next(entry for entry in index["entries"] if entry["name"] == "native_evaluator")
        expected_evaluator=(Path(staging_root).resolve(strict=True) / evaluator_entry["path"]).resolve(strict=True)
        if evaluator.binary != expected_evaluator:
            raise P3ProtocolError("P3 evaluator artifact substitution")
        if worker.spec.image_digest != self.lock.artifacts["native_worker"]:
            raise P3ProtocolError("P3 worker image substitution")
        if evaluator.public_key != self.receipt_log.public_key:
            raise P3ProtocolError("P3 evaluator authority substitution")
        # The index separately commits evaluator and worker OCI closures.  The
        # probe is retained as evaluator-signed receipt evidence before task one.
        worker.launcher.preflight(worker.spec)
        return worker.adversarial_probe(lock_digest=self.lock.digest)

    @staticmethod
    def _execution_record(evidence: Mapping[str, Any]) -> dict[str, Any]:
        return {"schema":"P3PairExecutionV1", "pair_id":evidence["pair_id"], "sequence":evidence["sequence"],
                "task_digest":evidence["task_digest"], "arms":dict(evidence["arms"]),
                "receipt_digest":evidence["evidence_digest"], "safety_ok":evidence["safety_ok"],
                "resources":dict(evidence["resource_ledger"]), "retention_delta":evidence["retention_delta"],
                "transfer_delta":evidence["transfer_delta"]}

    def run_e1_local_test(self, request: P3ReadinessRequestV1, *, proposal: Mapping[str, Any], run_id: str, seed: bytes,
                          worker: P3WorkerClient, evaluator: P3EvaluatorClient,
                          staging_index: Path, staging_root: Path) -> dict[str, Any]:
        """Run the finite 12x30 path without callback injection or adoption authority.

        The worker is launched only by hardened Podman and cannot receive a host
        callable, evaluator path, mutable mount, or more than the current sealed
        envelope.  Each independently evaluator-signed evidence object is appended
        before it enters score accounting.  Local custody remains non-release.
        """
        staged: StagedCandidateV1 | None=None
        current_envelope: Mapping[str, Any] | None=None
        try:
            staged=self._admit(request, proposal)
            containment=self._verify_execution_closure(worker=worker, evaluator=evaluator, staging_index=staging_index, staging_root=staging_root)
            self.receipt_log.append("containment", containment)
            manifest, package, _private=materialize_study(seed=seed, signing_key=self.receipt_log.signer, run_id=run_id,
                                                           lock_digest=self.lock.digest)
            worker.bind_task_release(lock_digest=self.lock.digest, run_id=run_id)
            evaluator.bind_task_release(lock_digest=self.lock.digest, run_id=run_id)
            outcomes={}; retention=[]; transfer=[]; safety=True; resources=True; released:set[str]=set()
            for distribution in DISTRIBUTIONS:
                records=[]; chain_receipts=[]
                for _ in range(30):
                    envelope=release_next(released, package, distribution)
                    current_envelope=envelope
                    worker_output=worker.execute_next(envelope, candidate_digest=staged.candidate_digest)
                    evidence=evaluator.evaluate(lock_digest=self.lock.digest, envelope=envelope, worker_output=worker_output,
                                                candidate_digest=staged.candidate_digest, pre_snapshot_digest=staged.pre_snapshot_digest)
                    # This evaluator-signed canonical record is append-safe in the
                    # receipt chain before the scorer may consume it.
                    receipt=self.receipt_log.append("pair", dict(evidence))
                    record=self._execution_record(evidence); chain_receipts.append(receipt["receipt_hash"])
                    records.append(record)
                outcome, kept, moved, safe, resourced=score_four_arm_distribution(records, package=package, distribution=distribution, seed=seed)
                outcome["receipt_digests"]=list(chain_receipts)
                outcomes[distribution]=outcome; retention.extend(kept); transfer.append(sum(moved)//30); safety &= safe; resources &= resourced
            bindings={key:self.lock.body[key] for key in ("p0_go_digest","p1_go_digest","p2_go_digest","native_export_digest","candidate_digest","pre_snapshot_digest")}
            seal=seal_results(run_id=run_id, lock_digest=self.lock.digest, outcomes=outcomes, signer=self.receipt_log.signer, release_bindings=bindings)
            classified={record["distribution_id"]:record for record in seal["outcomes"]}
            decision=e1_decision(outcomes=classified, retention_deltas=retention, transfer_deltas=transfer, safety_ok=safety,
                                 resources_ok=resources, custody_ok=False, seed=seed)
            result_payload=receipt_payload(lock_digest=self.lock.digest, proposal_digest=staged.proposal_digest, outcome="no_go",
                reason="local-test custody cannot authorize adoption", control_digests=self.lock.artifacts, snapshot_digest=seal["seal_digest"], release_bindings=bindings)
            result_payload["result_seal_digest"]=seal["seal_digest"]
            self.receipt_log.append("result", result_payload)
            rollback=reject_and_rollback(candidate=request.candidate, pre_snapshot=request.pre_snapshot, receipt_log=self.receipt_log,
                                         lock=self.lock, proposal_digest=staged.proposal_digest, reason="P3-R0 local-test rollback after sealed E1 accounting")
            return {"manifest_digest":manifest["manifest_digest"],"seal":seal,"decision":decision,"rollback":rollback,"adopted":False,"custody":"local-test"}
        except Exception as exc:
            if staged is None:
                return deny_before_evaluation(receipt_log=self.receipt_log, lock=self.lock, reason=f"e1:{type(exc).__name__}", proposal=proposal)
            if current_envelope is not None:
                bindings={key:self.lock.body[key] for key in ("p0_go_digest","p1_go_digest","p2_go_digest","native_export_digest","candidate_digest","pre_snapshot_digest")}
                terminal={"schema":"P3EnvelopeTerminalEvidenceV1", "lock_digest":self.lock.digest, "run_id":run_id,
                          "task_digest":current_envelope["task_digest"], "sequence":current_envelope["sequence"],
                          "reason":f"e1:{type(exc).__name__}"}
                terminal["evidence_digest"] = object_hash(terminal)
                payload=receipt_payload(lock_digest=self.lock.digest, proposal_digest=staged.proposal_digest, outcome="no_go",
                                        reason="evaluator_task_envelope_rejected", control_digests=self.lock.artifacts,
                                        release_bindings=bindings)
                payload["terminal_evidence"] = terminal
                self.receipt_log.append("terminal", payload)
            try:
                rollback=reject_and_rollback(candidate=request.candidate, pre_snapshot=request.pre_snapshot, receipt_log=self.receipt_log,
                                             lock=self.lock, proposal_digest=staged.proposal_digest, reason=f"P3-R0 E1 failure:{type(exc).__name__}")
            except Exception as rollback_error:
                # A restore or verification failure is terminal; it is not a normal
                # denial and never gets swallowed behind a best-effort rollback.
                return terminal_rollback_impasse(candidate=request.candidate, pre_snapshot=request.pre_snapshot, receipt_log=self.receipt_log,
                                                 lock=self.lock, proposal_digest=staged.proposal_digest, cause=rollback_error)
            return {"outcome":"no_go","reason":f"e1:{type(exc).__name__}","rollback":rollback,"adopted":False,"custody":"local-test"}
