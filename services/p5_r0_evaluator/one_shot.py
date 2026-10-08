"""Evaluator-owned one-shot run boundary.

The one-shot path is intentionally an adapter around the already locked
ConfidentialSpaceAdapter and EvaluatorService. It does not manufacture a
bundle, worker, closure, authority, timing record, or result. Those are
explicitly injected and validated after attestation has activated capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .attestation_binding import VerifiedAttestationBinding
from .canonical import digest
from .client import _digest_id
from .interfaces import Principal
from .input_builder import input_builder_binding
from .schemas import task_response
from .time_seed import TimeSeededInput, derive_time_seed, time_seed_algorithm_binding, validate_time_seeded_evidence


class OneShotProductionError(RuntimeError):
    """The evaluator-owned one-shot contract failed closed."""


BundleValidator = Callable[[], None]
ClosureValidator = Callable[[], None]
EvidenceValidator = Callable[[Mapping[str, Any], TimeSeededInput], None]
TaskExecutor = Callable[[Mapping[str, Any], TimeSeededInput], Mapping[str, Any]]
AuthorizedTaskValidator = Callable[[Mapping[str, Any]], None]
SupervisorEvidenceValidator = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class OneShotConfig:
    """Explicit non-secret run commitments and project-controlled execution seams."""

    lock_digest: str
    manifest_digest: str
    worker_contract_digest: str
    principal_subject: str
    input_namespace: str
    input_builder: Callable[[str], Mapping[str, Any]] = field(repr=False, compare=False)
    bundle_validator: BundleValidator = field(repr=False, compare=False)
    closure_validator: ClosureValidator = field(repr=False, compare=False)
    evidence_validator: EvidenceValidator = field(repr=False, compare=False)
    task_executor: TaskExecutor = field(repr=False, compare=False)
    authorized_task_validator: AuthorizedTaskValidator | None = field(default=None, repr=False, compare=False)
    supervisor_evidence_validator: SupervisorEvidenceValidator | None = field(default=None, repr=False, compare=False)
    max_tasks: int = 144
    input_builder_binding: Mapping[str, Any] = field(default_factory=input_builder_binding, repr=False, compare=False)
    time_seed_algorithm_binding: Mapping[str, Any] = field(default_factory=time_seed_algorithm_binding, repr=False, compare=False)

    def validate(self) -> None:
        for value, name in (
            (self.lock_digest, "lock_digest"),
            (self.manifest_digest, "manifest_digest"),
            (self.worker_contract_digest, "worker_contract_digest"),
        ):
            try:
                _digest_id(value, name)
            except Exception as exc:
                raise OneShotProductionError(f"{name} is invalid") from exc
        if not isinstance(self.principal_subject, str) or not self.principal_subject or self.principal_subject in {"runner", "aud", "REPLACE"}:
            raise OneShotProductionError("real one-shot principal subject is required")
        if not isinstance(self.input_namespace, str) or not self.input_namespace or self.input_namespace in {"runner", "aud", "REPLACE"}:
            raise OneShotProductionError("real one-shot input namespace is required")
        if not callable(self.input_builder):
            raise OneShotProductionError("time-seeded input builder is required")
        try:
            if dict(self.input_builder_binding) != input_builder_binding() or dict(self.time_seed_algorithm_binding) != time_seed_algorithm_binding():
                raise ValueError("source binding mismatch")
        except Exception as exc:
            raise OneShotProductionError("time-seeded source commitments are invalid") from exc
        if not all(callable(value) for value in (self.bundle_validator, self.closure_validator, self.evidence_validator, self.task_executor)):
            raise OneShotProductionError("project-controlled bundle, closure, evidence, and task adapters are required")
        if not callable(self.authorized_task_validator):
            raise OneShotProductionError("authorized task validator is required")
        if self.supervisor_evidence_validator is not None and not callable(self.supervisor_evidence_validator):
            raise OneShotProductionError("supervisor evidence validator is invalid")
        if type(self.max_tasks) is not int or not 1 <= self.max_tasks <= 10_000:
            raise OneShotProductionError("one-shot task budget is invalid")


class OneShotProductionRunner:
    """Run an attested service without exposing an HTTP caller boundary."""

    def __init__(self, adapter: Any, config: OneShotConfig):
        if not callable(getattr(adapter, "activate_attested_service", None)):
            raise OneShotProductionError("ConfidentialSpaceAdapter is required")
        if not isinstance(config, OneShotConfig):
            raise OneShotProductionError("OneShotConfig is required")
        config.validate()
        self.adapter = adapter
        self.config = config

    def _require_attested_capabilities(self, service: Any) -> VerifiedAttestationBinding:
        if getattr(self.adapter, "attested", False) is not True:
            raise OneShotProductionError("attested service activation failed")
        binding = getattr(self.adapter, "attestation_binding", None)
        if type(binding) is not VerifiedAttestationBinding:
            raise OneShotProductionError("verified attestation binding is unavailable")
        if getattr(service, "timing_certified", False) is not True:
            raise OneShotProductionError("independent timing capability is unavailable")
        if getattr(service, "signer", None) is None or getattr(service, "store", None) is None:
            raise OneShotProductionError("KMS/GCS capabilities are unavailable")
        return binding

    def run(self, *, emit: Callable[[str], Any] | None = None) -> dict[str, Any]:
        """Attest, validate project-generated inputs, execute tasks, and emit redacted state."""
        service = self.adapter.activate_attested_service()
        binding = self._require_attested_capabilities(service)
        try:
            self.config.bundle_validator()
            self.config.closure_validator()
        except OneShotProductionError:
            raise
        except Exception as exc:
            raise OneShotProductionError("project-generated bundle/closure validation failed") from exc

        principal = Principal(self.config.principal_subject)
        try:
            started = service.start({
                "schema": "P5R0RunStartRequestV1",
                "lock_digest": self.config.lock_digest,
                "manifest_digest": self.config.manifest_digest,
                "worker_contract_digest": self.config.worker_contract_digest,
                "idempotency_key": "one-shot-start",
                "execution_mode": "timing_first",
            }, principal)
        except Exception as exc:
            raise OneShotProductionError("one-shot run start failed closed") from exc
        required_start_commitments = {
            "lock_digest": self.config.lock_digest,
            "manifest_digest": self.config.manifest_digest,
            "worker_contract_digest": self.config.worker_contract_digest,
        }
        if not isinstance(started, Mapping) or any(started.get(key) != expected for key, expected in required_start_commitments.items()):
            raise OneShotProductionError("one-shot start commitments do not match configuration")
        run_id = started.get("run_id") if isinstance(started, Mapping) else None
        try:
            _digest_id(run_id, "run_id")
        except Exception as exc:
            raise OneShotProductionError("one-shot start returned no valid run") from exc

        try:
            seed = service.issue_time_seed(run_id, self.config.input_namespace, principal)
            if not isinstance(seed, Mapping):
                raise OneShotProductionError("service-owned timing seed is unavailable")
            timing_record = seed.get("timing_record")
            if not isinstance(timing_record, Mapping):
                raise OneShotProductionError("durable timing seed record is unavailable")
            seeded_input = derive_time_seed(
                timing_record, run_id=run_id, namespace=self.config.input_namespace,
                sequence=timing_record.get("sequence"), input_builder=self.config.input_builder,
                input_builder_binding=self.config.input_builder_binding,
                time_seed_algorithm_binding=self.config.time_seed_algorithm_binding,
            )
        except OneShotProductionError:
            raise
        except Exception as exc:
            raise OneShotProductionError("time-seeded input derivation failed closed") from exc

        expected_sequence = 1
        for _ in range(self.config.max_tasks):
            try:
                response = service.next_task(run_id, {
                    "schema": "P5R0NextTaskRequestV1",
                    "expected_sequence": expected_sequence,
                    "idempotency_key": f"one-shot-next-{expected_sequence}",
                }, principal)
                response = task_response(response)
                if response["run_id"] != run_id or response["sequence"] != expected_sequence:
                    raise OneShotProductionError("one-shot task is not bound to the started run")
                self.config.authorized_task_validator(response)
            except Exception as exc:
                raise OneShotProductionError("one-shot task issuance failed closed") from exc
            try:
                result = self.config.task_executor(response, seeded_input)
            except OneShotProductionError:
                raise
            except Exception as exc:
                raise OneShotProductionError("one-shot task executor failed") from exc
            if not isinstance(result, Mapping):
                raise OneShotProductionError("one-shot executor returned no result mapping")
            result = dict(result)
            # A caller-supplied callback can only provide diagnostic output; it
            # cannot promote itself into a native worker or supervisor.
            if result.get("native_verified") is True or result.get("external_authority_verified") is True or (isinstance(result.get("execution_evidence"), Mapping) and result["execution_evidence"].get("native_verified") is True):
                raise OneShotProductionError("one-shot callback cannot claim production authority")
            try:
                validate_time_seeded_evidence(result.get("execution_evidence"), seeded_input)
                self.config.evidence_validator(result, seeded_input)
                if self.config.supervisor_evidence_validator is not None:
                    supervisor_evidence = result.get("supervisor_evidence")
                    if not isinstance(supervisor_evidence, Mapping):
                        raise OneShotProductionError("one-shot supervisor evidence is unavailable")
                    self.config.supervisor_evidence_validator(supervisor_evidence)
            except OneShotProductionError:
                raise
            except Exception as exc:
                raise OneShotProductionError("one-shot evidence validation failed") from exc
            if result.get("run_id") != run_id or result.get("task_id") != response.get("task_id") or result.get("sequence") != expected_sequence:
                raise OneShotProductionError("one-shot result identity or sequence mismatch")
            try:
                submitted = service.submit_result(run_id, response["task_id"], result, principal)
            except Exception as exc:
                raise OneShotProductionError("one-shot result submission failed closed") from exc
            if submitted.get("disposition") == "impasse":
                return self._redacted_result(service, service.result(run_id, principal), binding, seeded_input, emit)
            if submitted.get("done") is True:
                return self._redacted_result(service, service.result(run_id, principal), binding, seeded_input, emit)
            if type(submitted.get("next_sequence")) is not int or submitted["next_sequence"] != expected_sequence + 1:
                raise OneShotProductionError("one-shot next sequence is invalid")
            expected_sequence = submitted["next_sequence"]
        raise OneShotProductionError("one-shot task budget exhausted before closure")

    def _redacted_result(self, service: Any, result: Mapping[str, Any], binding: VerifiedAttestationBinding, seeded_input: TimeSeededInput, emit: Callable[[str], Any] | None) -> dict[str, Any]:
        if not isinstance(result, Mapping) or result.get("schema") != "P5R0RunResultResponseV1":
            raise OneShotProductionError("one-shot result schema is invalid")
        seal = result.get("result_seal")
        public = {
            "schema": "P5R0OneShotResultV1",
            "status": result.get("status"),
            "disposition": result.get("disposition"),
            "run_id": result.get("run_id"),
            "chain_digest": result.get("chain_digest"),
            "result_seal_digest": digest(seal) if isinstance(seal, Mapping) else None,
            "startup_evidence_digest": digest(self.adapter.startup_evidence),
            "attestation_binding_digest": binding.binding_digest,
            "time_seed_timing_record_digest": seeded_input.timing_record_digest,
            "input_seed_digest": seeded_input.input_seed_digest,
            "input_digest": seeded_input.input_digest,
            "timing_certified": bool(getattr(service, "timing_certified", False)),
            "native_verified": bool(getattr(service, "native_verified", False)),
            "external_authority_verified": bool(getattr(service, "external_authority_verified", False)),
        }
        if emit is not None:
            from .canonical import canonical_bytes
            emit(canonical_bytes(public).decode("utf-8"))
        return public


__all__ = ["OneShotConfig", "OneShotProductionError", "OneShotProductionRunner"]
