"""Release-only P2 orchestration with native authority and durable outcomes.

A release score verifies the signed lock and its staged artifact closure, binds the
caller request byte-for-byte to the locked sealed input, preflights both durable
receipt channels, then runs the fixed worker and evaluator.  No unsealed outcome
or independently supplied signed envelope reaches a release worker.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
from dataclasses import replace
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from evaluation.p0a.canonical import canonical_bytes, object_hash, parse_canonical
from .lock import ARTIFACT_NAMES, canonical_content_hash, is_digest, public_key_encoding, validate_lock
from .podman import PodmanLauncher, PodmanPolicyUnavailable, PodmanSpec
from .protocol import MAX_FRAME_BYTES, P2ProtocolError, validate_envelope
from .receipts import ReceiptFailureLog, ReceiptLog
from .runtime import validate_runtime_closure

_METRICS = {"brier_milli": 0, "ece_milli": 1000, "feasibility_milli": 0,
            "minimality_milli": 0, "safety_milli": 0, "abstention_milli": 0}
_IMAGE_ARTIFACTS = frozenset({"p2_image", "p2_bypass_image", "p2_python_bypass_image"})


def _safe_digest(value: Any) -> str:
    """Hash an untrusted value without making parsing success a prerequisite for a failure seal."""
    try:
        return object_hash(value)
    except Exception:
        return "sha256:" + hashlib.sha256(type(value).__qualname__.encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise P2ProtocolError("release artifact unavailable")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _mounted_tree_commitment(root: Path) -> str:
    """Evaluator-side commitment to a read-only probe mount before/after launch."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise P2ProtocolError("probe mount unavailable")
    entries: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            raise P2ProtocolError("probe mount symlink")
        if path.is_dir():
            entries.append({"path": relative, "kind": "directory", "digest": ""})
        elif path.is_file():
            entries.append({"path": relative, "kind": "file", "digest": _file_digest(path)})
        else:
            raise P2ProtocolError("probe mount type")
    return object_hash({"entries": entries})


def _same_file(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=True) == right.resolve(strict=True)
    except (OSError, RuntimeError):
        return False


class NativeEvaluatorClient:
    """Framed local invocation of the fixed evaluator-native binary."""
    def __init__(self, binary: Path):
        self.binary = Path(binary)
        if self.binary.is_symlink() or not self.binary.is_file() or not os.access(self.binary, os.X_OK):
            raise P2ProtocolError("native evaluator unavailable")
        self.binary = self.binary.resolve(strict=True)

    def evaluate(self, envelope: Mapping[str, Any], proposal: Mapping[str, Any], *, verified_input_digest: str) -> dict[str, Any]:
        request = canonical_bytes({"schema": "P2NativeEvaluationRequestV1", "envelope": dict(envelope),
                                   "proposal": dict(proposal), "verified_input_digest": verified_input_digest})
        try:
            completed = subprocess.run([str(self.binary)], input=request, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=3, check=False, close_fds=True, env={"PATH": ""})
            if completed.returncode or len(completed.stdout) > MAX_FRAME_BYTES:
                raise ValueError("native exit")
            reply = json.loads(completed.stdout)
        except (OSError, ValueError, TypeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            raise P2ProtocolError("native evaluator failure") from exc
        if (not isinstance(reply, dict) or type(reply.get("accepted")) is not bool
                or not isinstance(reply.get("classification"), str) or not isinstance(reply.get("metrics"), dict)
                or not is_digest(reply.get("reconstruction_digest"))
                or reply.get("verified_input_digest") != verified_input_digest):
            raise P2ProtocolError("native evaluator response")
        return reply


class NativeWorkerFailure(P2ProtocolError):
    """Fixed diagnostic classification; it deliberately carries no OCI text."""
    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__(f"native worker {reason_code}")


class NativeWorkerClient:
    """The only release worker path: fixed image, fixed UID, hardened Podman."""
    _REASONS = frozenset({
        "runtime_ready", "loader_or_shared_object_unavailable", "exec_denied", "timeout",
        "signal_or_resource_limit", "input_frame_invalid", "request_schema_invalid",
        "sealed_digest_mismatch", "sealed_graph_invalid", "bounded_simulation_failed",
        "output_write_failed", "unknown_native_failure",
    })
    _DIAGNOSTIC_REASONS = _REASONS - {"runtime_ready", "loader_or_shared_object_unavailable", "exec_denied", "timeout", "signal_or_resource_limit"}

    def __init__(self, spec: PodmanSpec):
        self.spec = spec
        self.launcher = PodmanLauncher()

    @classmethod
    def _diagnostic(cls, stdout: bytes) -> str | None:
        try:
            reply = json.loads(stdout)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if (isinstance(reply, dict) and reply.get("schema") == "P2NativeWorkerDiagnosticV1"
                and reply.get("status") == "unestablished"
                and reply.get("reason_code") in cls._DIAGNOSTIC_REASONS
                and set(reply) == {"schema", "status", "reason_code"}):
            return reply["reason_code"]
        return None

    @staticmethod
    def _launch_reason(status: int | None, stdout: bytes) -> str:
        if status is not None and status < 0:
            return "signal_or_resource_limit"
        if status in {126}:
            return "exec_denied"
        if status in {127} and not stdout:
            return "loader_or_shared_object_unavailable"
        return "unknown_native_failure"

    def probe(self) -> None:
        """Establish only that the pinned scratch runtime can enter its fixed binary."""
        request = canonical_bytes({"schema": "P2NativeRuntimeProbeV1", "nonce": "p2-native-runtime-probe-v1"})
        try:
            stdout, _stderr, status = self.launcher.exchange(self.spec, request)
        except PodmanPolicyUnavailable as exc:
            reason = "timeout" if "wall budget" in str(exc) else "unknown_native_failure"
            raise NativeWorkerFailure(reason) from exc
        try:
            reply = json.loads(stdout)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise NativeWorkerFailure(self._launch_reason(status, stdout)) from exc
        if (status != 0 or not isinstance(reply, dict)
                or reply != {"schema": "P2NativeRuntimeProbeReplyV1", "status": "ready", "abi": "p2-native-v1"}):
            raise NativeWorkerFailure(self._launch_reason(status, stdout))

    def bypass_evidence(self, bypass_image: str, python_bypass_image: str) -> dict[str, Any]:
        """Run fixed native and real-Python hostile probes under the worker policy.

        The evaluator independently commits the read-only mounts before and after
        both probes; therefore a contained report needs denial tokens *and* no
        observable staged-input/agent mutation.
        """
        mounts_before = {"agent": _mounted_tree_commitment(self.spec.agent_root),
                         "input": _mounted_tree_commitment(self.spec.input_root)}
        native_attempts = ("agent_write", "callback", "evaluator_path", "host_protocol", "id_only_route",
                           "input_write", "network", "shell", "undeclared_binary")
        python_attempts = (*native_attempts, "python_execution")

        def run_probe(image: str, entrypoint: str, schema: str, expected: tuple[str, ...],
                      executed_python: bool = False) -> dict[str, Any]:
            probe_spec = replace(self.spec, image_digest=image, entrypoint=entrypoint)
            process: subprocess.Popen[bytes] | None = None
            try:
                process = self.launcher.start(probe_spec)
                stdout, _stderr = process.communicate(b"", timeout=3)
            except subprocess.TimeoutExpired as exc:
                if process is not None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.communicate()
                raise NativeWorkerFailure("timeout") from exc
            except (OSError, PodmanPolicyUnavailable) as exc:
                raise NativeWorkerFailure("unknown_native_failure") from exc
            try:
                report = json.loads(stdout)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise NativeWorkerFailure(self._launch_reason(process.returncode, stdout)) from exc
            if (process.returncode != 0 or not isinstance(report, dict)
                    or set(report) != {"schema", "status", "attempts"}
                    or report.get("schema") != schema or report.get("status") != "contained"
                    or not isinstance(report.get("attempts"), dict)
                    or tuple(sorted(report["attempts"])) != tuple(sorted(expected))):
                raise NativeWorkerFailure("unknown_native_failure")
            for name in expected:
                expected_status = "executed_no_effect" if executed_python and name == "python_execution" else "blocked"
                if report["attempts"].get(name) != expected_status:
                    raise NativeWorkerFailure("unknown_native_failure")
            return report

        native_report = run_probe(bypass_image, "/runtime/p2_bypass_probe", "P2BypassProbeReportV1", native_attempts)
        python_report = run_probe(python_bypass_image, "/runtime/p2_python_bypass_probe",
                                  "P2PythonBypassProbeReportV1", python_attempts, executed_python=True)
        mounts_after = {"agent": _mounted_tree_commitment(self.spec.agent_root),
                        "input": _mounted_tree_commitment(self.spec.input_root)}
        if mounts_after != mounts_before:
            raise NativeWorkerFailure("unknown_native_failure")
        # The signed receipt retains the fixed probe vocabulary and evaluator-side
        # before/after commitments, never unbounded container output.
        return {"schema": "P2HostileBypassEvidenceV2", "status": "contained",
                "native_attempts": {name: {"attempted": True, "result": native_report["attempts"][name]}
                                    for name in native_attempts},
                "python_attempts": {name: {"attempted": True, "result": python_report["attempts"][name]}
                                    for name in python_attempts},
                "evaluator_mounts": {name: {"before": mounts_before[name], "after": mounts_after[name]}
                                     for name in ("agent", "input")}}

    def reply(self, envelope: Mapping[str, Any], *, verified_input_digest: str) -> dict[str, Any]:
        request = {"schema": "P2NativeWorkerRequestV1", "envelope": dict(envelope),
                   "verified_input_digest": verified_input_digest}
        try:
            stdout, _stderr, status = self.launcher.exchange(self.spec, canonical_bytes(request))
        except PodmanPolicyUnavailable as exc:
            reason = "timeout" if "wall budget" in str(exc) else "unknown_native_failure"
            raise NativeWorkerFailure(reason) from exc
        if len(stdout) > MAX_FRAME_BYTES:
            raise NativeWorkerFailure("unknown_native_failure")
        diagnostic = self._diagnostic(stdout)
        if diagnostic is not None:
            raise NativeWorkerFailure(diagnostic)
        if status != 0:
            raise NativeWorkerFailure(self._launch_reason(status, stdout))
        try:
            reply = json.loads(stdout)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise NativeWorkerFailure("unknown_native_failure") from exc
        if not isinstance(reply, dict) or reply.get("verified_input_digest") != verified_input_digest:
            raise NativeWorkerFailure("unknown_native_failure")
        return reply


class P2Runner:
    """The sole release certification runner; it has no callback or broker seam."""
    def __init__(self, *, evaluator_binary: Path, evaluation_lock: Mapping[str, Any], envelope_key: Any,
                 replay_root: Path, receipt_log: ReceiptLog, failure_log: ReceiptFailureLog,
                 worker_spec: PodmanSpec, trusted_lock_keys: Mapping[str, Any] | None = None,
                 release_artifacts: Mapping[str, Path | str] | None = None):
        if not isinstance(receipt_log, ReceiptLog):
            raise P2ProtocolError("P2 receipt log unavailable")
        if not isinstance(failure_log, ReceiptFailureLog):
            raise P2ProtocolError("P2 receipt failure authority unavailable")
        if receipt_log.root == failure_log.root:
            raise P2ProtocolError("P2 receipt failure authority must be separate")
        if envelope_key is None:
            raise P2ProtocolError("P2 evaluator signing key unavailable")
        self.evaluator_binary = Path(evaluator_binary)
        self.evaluation_lock = dict(evaluation_lock) if isinstance(evaluation_lock, Mapping) else evaluation_lock
        self.envelope_key, self.worker_spec = envelope_key, worker_spec
        self.trusted_lock_keys = dict(trusted_lock_keys or {})
        self.release_artifacts = dict(release_artifacts or {})
        self.replay_root = Path(replay_root)
        if self.replay_root.is_symlink() or not self.replay_root.is_dir():
            raise P2ProtocolError("P2 replay ledger unavailable")
        self.replay_root = self.replay_root.resolve(strict=True)
        self.receipts, self.failure_receipts = receipt_log, failure_log

    def _verify_artifact_closure(self, lock: Mapping[str, Any], evaluator: NativeEvaluatorClient) -> None:
        if set(self.release_artifacts) != set(ARTIFACT_NAMES):
            raise P2ProtocolError("P2 incomplete release artifact closure")
        if not isinstance(self.worker_spec, PodmanSpec):
            raise P2ProtocolError("P2 hardened worker required")
        root = Path(self.worker_spec.staging_root)
        if root.is_symlink() or not root.is_dir():
            raise P2ProtocolError("P2 release staging unavailable")
        root = root.resolve(strict=True)
        for name in ARTIFACT_NAMES:
            artifact = self.release_artifacts[name]
            expected = lock["artifacts"][name]
            if name in _IMAGE_ARTIFACTS:
                if artifact != expected or not is_digest(artifact):
                    raise P2ProtocolError(f"P2 {name} substitution")
                continue
            if not isinstance(artifact, Path):
                raise P2ProtocolError(f"P2 {name} staged artifact")
            path = artifact
            if path.is_symlink() or not path.is_file():
                raise P2ProtocolError(f"P2 {name} unavailable")
            path = path.resolve(strict=True)
            if root not in path.parents or _file_digest(path) != expected:
                raise P2ProtocolError(f"P2 {name} digest mismatch")
        validate_runtime_closure(self.release_artifacts["runtime_closure"],
                                 worker_digest=lock["artifacts"]["native_worker_binary"])
        if not _same_file(self.release_artifacts["native_evaluator_binary"], evaluator.binary):
            raise P2ProtocolError("P2 evaluator artifact substitution")
        if not _same_file(self.release_artifacts["native_worker_binary"], self.worker_spec.worker_binary):
            raise P2ProtocolError("P2 worker artifact substitution")
        if not _same_file(self.release_artifacts["seccomp_policy"], self.worker_spec.seccomp_profile):
            raise P2ProtocolError("P2 seccomp artifact substitution")
        sealed_input = Path(self.release_artifacts["sealed_input"]).resolve(strict=True)
        input_root = Path(self.worker_spec.input_root).resolve(strict=True)
        if input_root not in sealed_input.parents:
            raise P2ProtocolError("P2 sealed input outside staged input")
        if self.worker_spec.image_digest != lock["artifacts"]["p2_image"] or self.worker_spec.seccomp_digest != lock["artifacts"]["seccomp_policy"]:
            raise P2ProtocolError("P2 worker runtime substitution")

    def _locked_envelope(self, envelope: Mapping[str, Any], lock: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        """Load and verify the artifact that the lock actually sealed before launch."""
        sealed_path = Path(self.release_artifacts["sealed_input"])
        try:
            raw = sealed_path.read_bytes()
            sealed = parse_canonical(raw)
        except Exception as exc:
            raise P2ProtocolError("P2 sealed input canonical") from exc
        if not isinstance(sealed, Mapping) or canonical_bytes(dict(sealed)) != raw:
            raise P2ProtocolError("P2 sealed input canonical")
        if not isinstance(envelope, Mapping) or canonical_bytes(dict(envelope)) != raw:
            raise P2ProtocolError("P2 caller envelope differs from locked sealed input")
        verified = validate_envelope(sealed, signing_key=self.envelope_key)
        input_digest = lock["artifacts"]["sealed_input"]
        if _file_digest(sealed_path) != input_digest:
            raise P2ProtocolError("P2 sealed input digest mismatch")
        return verified, input_digest

    def _release_preflight(self, lock: Mapping[str, Any]) -> tuple[NativeEvaluatorClient, NativeWorkerClient, dict[str, Any]]:
        """Complete non-lock preflight after the release lock has been verified."""
        if public_key_encoding(self.envelope_key) != lock["evaluator_public_key"]:
            raise P2ProtocolError("P2 evaluator key substitution")
        if public_key_encoding(self.receipts._public_key) != lock["receipt_public_key"]:
            raise P2ProtocolError("P2 receipt key substitution")
        if public_key_encoding(self.failure_receipts._public_key) != lock["evaluator_public_key"]:
            raise P2ProtocolError("P2 failure authority substitution")
        evaluator = NativeEvaluatorClient(self.evaluator_binary)
        self._verify_artifact_closure(lock, evaluator)
        worker = NativeWorkerClient(self.worker_spec)
        try:
            worker.launcher.preflight(self.worker_spec)
            worker.launcher.preflight_image(self.worker_spec, lock["artifacts"]["p2_bypass_image"])
            worker.launcher.preflight_image(self.worker_spec, lock["artifacts"]["p2_python_bypass_image"])
            worker.probe()
            bypass_evidence = worker.bypass_evidence(lock["artifacts"]["p2_bypass_image"],
                                                      lock["artifacts"]["p2_python_bypass_image"])
        except NativeWorkerFailure:
            raise
        except (PodmanPolicyUnavailable, OSError) as exc:
            raise P2ProtocolError("hardened worker preflight failure") from exc
        return evaluator, worker, bypass_evidence

    def _claim(self, envelope: Mapping[str, Any], proposal_digest: str) -> Path:
        target = self.replay_root / f"{proposal_digest[7:]}.claim"
        try:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError as exc:
            raise P2ProtocolError("proposal replay") from exc
        try:
            os.write(fd, canonical_bytes({"run_id": envelope["run_id"], "episode_id": envelope["episode_id"], "proposal_digest": proposal_digest}))
            os.fsync(fd)
        finally:
            os.close(fd)
        return target

    def _receipt_payload(self, *, lock: Mapping[str, Any] | None, input_digest: str | None,
                         proposal_digest: str, result: Mapping[str, Any],
                         submitted_input_evidence_hash: str | None = None) -> dict[str, Any]:
        reconstruction = result.get("reconstruction_digest")
        verified = lock is not None
        artifacts = lock["artifacts"] if verified else {}
        payload = {
            "lock_status": "verified" if verified else "unverified",
            "lock_digest": canonical_content_hash(lock) if verified else None,
            "input_digest": input_digest,
            "proposal_digest": proposal_digest,
            "reconstruction_digest": reconstruction if is_digest(reconstruction) else _safe_digest(dict(result)),
            "worker_image_digest": artifacts.get("p2_image") if verified else None,
            "evaluator_binary_digest": artifacts.get("native_evaluator_binary") if verified else None,
            "outcome": {"classification": result.get("classification", "protocol_error"), "brokered": False,
                        **({"reason_code": result["reason_code"]} if result.get("reason_code") in NativeWorkerClient._REASONS else {})},
            "scoring_vector": dict(result.get("metrics", _METRICS)),
        }
        hostile = result.get("hostile_bypass_evidence")
        if isinstance(hostile, Mapping) and hostile.get("schema") == "P2HostileBypassEvidenceV2":
            payload["hostile_bypass_evidence"] = dict(hostile)
            payload["outcome"]["hostile_bypass_evidence_hash"] = _safe_digest(dict(hostile))
            payload["outcome"]["hostile_bypass_status"] = hostile.get("status")
        if submitted_input_evidence_hash is not None:
            payload["submitted_input_evidence_hash"] = submitted_input_evidence_hash
        return payload

    def _terminal(self, *, lock: Mapping[str, Any] | None, input_digest: str | None,
                  proposal_digest: str, result: Mapping[str, Any],
                  submitted_input_evidence_hash: str | None = None) -> Mapping[str, Any]:
        payload = self._receipt_payload(lock=lock, input_digest=input_digest, proposal_digest=proposal_digest,
                                        result=result, submitted_input_evidence_hash=submitted_input_evidence_hash)
        try:
            record = self.receipts.append(payload)
        except Exception as exc:
            try:
                failure = self.failure_receipts.append(payload,
                    attempted_classification=str(result.get("classification", "protocol_error")),
                    failure_code=type(exc).__name__)
            except Exception as failure_exc:
                raise P2ProtocolError("P2 receipt persistence failure unsealed") from failure_exc
            return {"classification": "receipt_persistence_failed", "success_credit": 0, "brokered": False,
                    "verified_input_digest": input_digest, "failure_record_hash": failure["failure_hash"],
                    "result_seal": failure["failure_hash"]}
        response = {"classification": result.get("classification", "protocol_error"), "success_credit": 0,
                    "brokered": False, "verified_input_digest": input_digest,
                    "receipt_hash": record["receipt_hash"], "result_seal": record["receipt_hash"]}
        if result.get("reason_code") in NativeWorkerClient._REASONS:
            response["reason_code"] = result["reason_code"]
        if result.get("accepted") is True:
            response["selected_action_id"] = result.get("selected_action_id")
        return response

    @staticmethod
    def _discard_claim(claim: Path | None) -> None:
        if claim is not None:
            try:
                claim.unlink(missing_ok=True)
            except OSError:
                pass

    def _finish(self, *, lock: Mapping[str, Any] | None, input_digest: str | None,
                proposal_digest: str, result: Mapping[str, Any], claim: Path | None,
                submitted_input_evidence_hash: str | None = None) -> Mapping[str, Any]:
        response = self._terminal(lock=lock, input_digest=input_digest, proposal_digest=proposal_digest,
                                  result=result, submitted_input_evidence_hash=submitted_input_evidence_hash)
        if response["classification"] == "receipt_persistence_failed":
            self._discard_claim(claim)
        return response

    def score(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        """Score exactly one locked sealed envelope; worker output is never caller supplied."""
        submitted_input_evidence_hash = _safe_digest(envelope)
        lock: Mapping[str, Any] | None = None
        input_digest: str | None = None
        proposal_digest = _safe_digest({"worker_reply": "unavailable", "lock_status": "unverified"})
        claim: Path | None = None
        receipt_submission_evidence: str | None = submitted_input_evidence_hash
        try:
            # No native action is reachable until durable authorities and the trusted
            # release lock are healthy. Before validation, receipt fields remain null.
            self.failure_receipts.preflight()
            self.receipts.preflight()
            lock = validate_lock(self.evaluation_lock, self.trusted_lock_keys)
            input_digest = lock["artifacts"]["sealed_input"]
            proposal_digest = _safe_digest({"worker_reply": "unavailable", "input_digest": input_digest})
            evaluator, worker, bypass_evidence = self._release_preflight(lock)
            sealed_envelope, input_digest = self._locked_envelope(envelope, lock)
            worker_reply = worker.reply(sealed_envelope, verified_input_digest=input_digest)
            proposal_digest = _safe_digest(worker_reply)
            result = evaluator.evaluate(sealed_envelope, worker_reply, verified_input_digest=input_digest)
            result["hostile_bypass_evidence"] = bypass_evidence
            claim = self._claim(sealed_envelope, proposal_digest)
        except P2ProtocolError as exc:
            result = {"accepted": False, "classification": "replay_denied" if str(exc) == "proposal replay" else "protocol_error", "metrics": dict(_METRICS), "error": str(exc)}
            if isinstance(exc, NativeWorkerFailure):
                result["reason_code"] = exc.reason_code
            return self._finish(lock=lock, input_digest=input_digest, proposal_digest=proposal_digest, result=result,
                                claim=claim, submitted_input_evidence_hash=receipt_submission_evidence)
        except Exception as exc:
            result = {"accepted": False, "classification": "protocol_error", "metrics": dict(_METRICS), "error": type(exc).__name__}
            return self._finish(lock=lock, input_digest=input_digest, proposal_digest=proposal_digest, result=result,
                                claim=claim, submitted_input_evidence_hash=receipt_submission_evidence)
        try:
            return self._finish(lock=lock, input_digest=input_digest, proposal_digest=proposal_digest,
                                result=result, claim=claim)
        except Exception:
            self._discard_claim(claim)
            raise


class P2UnitRunner:
    """Non-release test scaffold retaining injectable reconstruction/broker seams."""
    def __init__(self, reconstruct: Callable[[Mapping, Mapping], Mapping], broker: Callable[[Mapping], Mapping] | None = None):
        self.reconstruct, self.broker = reconstruct, broker

    def score(self, envelope: Mapping, proposal: Mapping) -> Mapping:
        reconstruction = self.reconstruct(envelope, proposal)
        if not isinstance(reconstruction, Mapping) or reconstruction.get("accepted") is not True:
            return {"classification": "protocol_error", "success_credit": 0, "brokered": False}
        if self.broker is None:
            return {"classification": "accepted", "success_credit": 0, "brokered": False}
        return self.broker({"action_id": proposal["selection"]["selected_action_id"], "proposal_digest": proposal["proposal_digest"], "idempotency_key": proposal["proposal_digest"]})
