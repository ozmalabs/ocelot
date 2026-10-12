"""Fail-closed orchestration for an explicitly configured controlled run.

This module does not generate a lock, bundle, caller token, worker result,
authority signature, or production identity. It only sequences the control-plane
calls after project-controlled validators and a native execution seam are bound
to the committed artifacts. Those seams do not by themselves create execution
evidence or a release result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from .canonical import digest
from .client import EvaluatorClientError, EvaluatorImpasse, P5EvaluatorClient, _digest_id, _validate_authority
from .input_builder import deterministic_input_builder, input_builder_binding
from .time_seed import derive_time_seed, time_seed_algorithm_binding, validate_time_seeded_evidence


_PLACEHOLDER_VALUES = frozenset({"aud", "runner", "REPLACE", "PLACEHOLDER", "TODO"})


class ProductionRunError(RuntimeError):
    """The normal-run contract was not satisfied or execution stopped."""


def validate_production_bundle(bundle: Mapping[str, Any]) -> None:
    """Reject local/non-release bundles before a normal run can start.

    Cryptographic authority verification remains an injected trust-binding
    validator; this structural gate prevents local readiness artifacts from
    being mistaken for signed-environment inputs or execution evidence.
    """
    required = {"authority", "lock", "manifest", "private_store"}
    if not isinstance(bundle, Mapping) or set(bundle) != required:
        raise ProductionRunError("production bundle fields are not closed")
    authority = _validate_authority(bundle["authority"])
    lock = bundle["lock"]
    if not isinstance(lock, Mapping):
        raise ProductionRunError("production lock is missing")
    if lock.get("schema") in {"P5R0LocalLockV2", "P5R0LocalLockV3"} or lock.get("classification") == "local_readiness_only" or lock.get("non_release") is True:
        raise ProductionRunError("local/non-release lock cannot be used for production")
    if lock.get("authority") != authority or lock.get("authority_verified") is not True:
        raise ProductionRunError("production lock authority binding is not verified")
    manifest = bundle["manifest"]
    if not isinstance(manifest, Mapping) or manifest.get("schema") != "P5R0ManifestV2" or not isinstance(manifest.get("case_index"), list) or not manifest["case_index"]:
        raise ProductionRunError("production manifest is invalid")
    if manifest.get("manifest_digest") != digest({key: value for key, value in manifest.items() if key != "manifest_digest"}):
        raise ProductionRunError("production manifest digest is invalid")
    try:
        expected_builder = input_builder_binding()
        expected_algorithm = time_seed_algorithm_binding()
    except Exception as exc:
        raise ProductionRunError("production source commitments are unavailable") from exc
    if manifest.get("input_builder_binding") != expected_builder or manifest.get("time_seed_algorithm_binding") != expected_algorithm:
        raise ProductionRunError("production manifest source commitments are invalid")
    private_store = bundle["private_store"]
    if not isinstance(private_store, Mapping) or private_store.get("schema") != "P5R0CaseStoreV2":
        raise ProductionRunError("evaluator-private production store is invalid")
    if lock.get("manifest_digest") != manifest.get("manifest_digest"):
        raise ProductionRunError("production lock/manifest binding is invalid")
    if lock.get("input_builder_binding") != manifest.get("input_builder_binding") or lock.get("time_seed_algorithm_binding") != manifest.get("time_seed_algorithm_binding"):
        raise ProductionRunError("production lock/source commitment binding is invalid")
    if lock.get("store_digest") != private_store.get("store_digest") or lock.get("truth_digest") != private_store.get("truth_digest"):
        raise ProductionRunError("production lock/private-store binding is invalid")


class ProductionBundleValidator(Protocol):
    def __call__(self) -> None: ...


class ProductionTaskExecutor(Protocol):
    def __call__(self, task_response: Mapping[str, Any], seeded_input: Any) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class ProductionRunConfig:
    """Explicit values required before a normal evaluator run may start."""

    lock_digest: str
    manifest_digest: str
    worker_contract_digest: str
    caller_audience: str
    caller_subject: str
    idempotency_prefix: str
    bundle_validator: ProductionBundleValidator = field(repr=False, compare=False)
    task_executor: ProductionTaskExecutor = field(repr=False, compare=False)
    input_namespace: str = "production-inputs"
    input_builder: Callable[[str], Mapping[str, Any]] = field(default=deterministic_input_builder, repr=False, compare=False)
    input_builder_binding: Mapping[str, Any] = field(default_factory=input_builder_binding, repr=False, compare=False)
    time_seed_algorithm_binding: Mapping[str, Any] = field(default_factory=time_seed_algorithm_binding, repr=False, compare=False)
    max_tasks: int = 144

    def validate(self) -> None:
        for value, name in (
            (self.lock_digest, "lock_digest"),
            (self.manifest_digest, "manifest_digest"),
            (self.worker_contract_digest, "worker_contract_digest"),
        ):
            try:
                _digest_id(value, name)
            except EvaluatorClientError as exc:
                raise ProductionRunError(str(exc)) from exc
        for value, name in ((self.caller_audience, "caller_audience"), (self.caller_subject, "caller_subject")):
            if not isinstance(value, str) or not value or value in _PLACEHOLDER_VALUES or any(char.isspace() for char in value):
                raise ProductionRunError(f"{name} must be a real explicit production value")
        if not self.caller_audience.startswith("https://"):
            raise ProductionRunError("caller_audience must be HTTPS")
        if not isinstance(self.idempotency_prefix, str) or not self.idempotency_prefix or self.idempotency_prefix in _PLACEHOLDER_VALUES:
            raise ProductionRunError("idempotency_prefix is invalid")
        if not callable(self.bundle_validator):
            raise ProductionRunError("project-controlled bundle validator is required")
        if not callable(self.task_executor):
            raise ProductionRunError("native task execution seam is required")
        if not isinstance(self.input_namespace, str) or not self.input_namespace or self.input_namespace in _PLACEHOLDER_VALUES:
            raise ProductionRunError("production input namespace is invalid")
        if not callable(self.input_builder):
            raise ProductionRunError("timing-first input builder is required")
        try:
            if dict(self.input_builder_binding) != input_builder_binding() or dict(self.time_seed_algorithm_binding) != time_seed_algorithm_binding():
                raise ValueError("source binding mismatch")
        except Exception as exc:
            raise ProductionRunError("timing-first source commitments are invalid") from exc
        if type(self.max_tasks) is not int or not 1 <= self.max_tasks <= 10_000:
            raise ProductionRunError("max_tasks is invalid")


class P5ProductionRunner:
    """Run the normal HTTP sequence without manufacturing worker evidence."""

    def __init__(self, client: P5EvaluatorClient, config: ProductionRunConfig):
        if not isinstance(client, P5EvaluatorClient):
            raise ProductionRunError("P5EvaluatorClient is required")
        if not isinstance(config, ProductionRunConfig):
            raise ProductionRunError("ProductionRunConfig is required")
        config.validate()
        _validate_authority(client.authority)
        self.client = client
        self.config = config

    def run(self) -> dict[str, Any]:
        """Run start → next/task result until the service closes or impasses.

        The bundle validator and native execution seam are project-controlled
        adapters. Their outputs are never synthesized or upgraded by this
        runner, and neither adapter is an external task provider.
        """
        try:
            self.config.bundle_validator()
        except ProductionRunError:
            raise
        except Exception as exc:
            raise ProductionRunError("production bundle validation failed") from exc

        started = self.client.start_run(
            lock_digest=self.config.lock_digest,
            manifest_digest=self.config.manifest_digest,
            worker_contract_digest=self.config.worker_contract_digest,
            idempotency_key=f"{self.config.idempotency_prefix}:start",
            execution_mode="timing_first",
        )
        run_id = started.get("run_id") if isinstance(started, Mapping) else None
        try:
            _digest_id(run_id, "run_id")
        except EvaluatorClientError as exc:
            raise ProductionRunError("start response did not contain a valid run_id") from exc

        try:
            seed_response = self.client.issue_time_seed(
                run_id=run_id, namespace=self.config.input_namespace,
                idempotency_key=f"{self.config.idempotency_prefix}:time-seed",
            )
            timing_record = seed_response.get("timing_record")
            if seed_response.get("input_builder_binding") != dict(self.config.input_builder_binding) or seed_response.get("time_seed_algorithm_binding") != dict(self.config.time_seed_algorithm_binding):
                raise ProductionRunError("service time-seed source commitments do not match configuration")
            seeded_input = derive_time_seed(
                timing_record, run_id=run_id, namespace=self.config.input_namespace,
                sequence=timing_record.get("sequence"), input_builder=self.config.input_builder,
                input_builder_binding=self.config.input_builder_binding,
                time_seed_algorithm_binding=self.config.time_seed_algorithm_binding,
            )
            if seed_response.get("timing_record_digest") != seeded_input.timing_record_digest or seed_response.get("input_seed_digest") != seeded_input.input_seed_digest or seed_response.get("input_digest") != seeded_input.input_digest:
                raise ProductionRunError("service time-seed commitment mismatch")
        except ProductionRunError:
            raise
        except Exception as exc:
            raise ProductionRunError("timing-first input derivation failed") from exc

        expected_sequence = 1
        for _ in range(self.config.max_tasks):
            task_response = self.client.next_task(
                run_id=run_id,
                expected_sequence=expected_sequence,
                idempotency_key=f"{self.config.idempotency_prefix}:next:{expected_sequence}",
            )
            try:
                result = self.config.task_executor(task_response, seeded_input)
            except ProductionRunError:
                raise
            except Exception as exc:
                raise ProductionRunError("production task executor failed") from exc
            if not isinstance(result, Mapping):
                raise ProductionRunError("task executor did not return a result mapping")
            result = dict(result)
            if result.get("run_id") != run_id or result.get("sequence") != expected_sequence:
                raise ProductionRunError("task executor result identity or sequence mismatch")
            task_id = result.get("task_id")
            try:
                _digest_id(task_id, "task_id")
            except EvaluatorClientError as exc:
                raise ProductionRunError("task executor result task_id is invalid") from exc
            try:
                validate_time_seeded_evidence(result.get("execution_evidence"), seeded_input)
            except Exception as exc:
                raise ProductionRunError("legacy or mismatched execution evidence is diagnostic-only") from exc
            submitted = self.client.submit_result(run_id=run_id, task_id=task_id, result=result)
            if submitted.get("disposition") == "impasse":
                raise EvaluatorImpasse(submitted)
            if submitted.get("done") is True:
                return self.client.get_result(run_id=run_id)
            next_sequence = submitted.get("next_sequence")
            if type(next_sequence) is not int or next_sequence != expected_sequence + 1:
                raise ProductionRunError("service returned an invalid next_sequence")
            expected_sequence = next_sequence

        raise ProductionRunError("production task budget exhausted before result closure")


__all__ = ["P5ProductionRunner", "ProductionBundleValidator", "ProductionRunConfig", "ProductionRunError", "ProductionTaskExecutor", "validate_production_bundle"]
