from __future__ import annotations

import time
from copy import deepcopy
from typing import Any, Callable
from urllib.parse import unquote

from .attestation_binding import VerifiedAttestationBinding
from .auth import AuthError
from .canonical import b64encode, canonical_bytes, digest, parse_canonical, signing_digest
from .engine import RepositoryEngineFactory
from .interfaces import EngineFactory, ObjectStore, Principal, Signer, StoreError, TokenVerifier
from .input_builder import deterministic_input_builder, input_builder_binding as input_builder_binding_for_service
from .schemas import (SchemaError, bounded_compute_claim, compute_class_observation, compute_class_observation_request, compute_class_seed,
                      execution_evidence, next_task, run_start,
                      task_result, task_response)
from .signing import sign_object
from .timing import TimingAttestor, coarse_wall_bucket, timing_digest, validate_attestation
from .time_seed import derive_time_seed, time_seed_algorithm_binding as time_seed_algorithm_binding_for_service


class ServiceError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class EvaluatorService:
    """A small fail-closed HTTP control plane around one V3 evaluator run.

    Truth and evaluator state never enter a response. The process-local engine is
    deliberately an injected seam: a production restart without a rehydration
    implementation becomes an impasse rather than silently restarting a session.
    """
    def __init__(self, *, store: ObjectStore, signer: Signer, verifier: TokenVerifier,
                 engine_factory: EngineFactory | None = None,
                 timing_attestor: TimingAttestor | None = None,
                 max_body_bytes: int = 1_048_576,
                 clock_ms: Callable[[], int] | None = None,
                 task_ttl_ms: int = 30_000,
                 image_digest: str | None = None,
                 runtime_digest: str | None = None,
                 resource_profile_digest: str | None = None,
                 timing_authority_id: str | None = None,
                 timing_key_id: str | None = None,
                 timing_ledger_id: str | None = None,
                 timing_public_key_digest: str | None = None,
                 policy_digest: str | None = None,
                 claim_paths_digest: str | None = None,
                 attestation_claims_digest: str | None = None,
                 wip_policy_digest: str | None = None,
                 wip_provider: str | None = None,
                 verified_attestation_binding: VerifiedAttestationBinding | None = None,
                 trusted_worker_supervisor: Any | None = None,
                 input_builder: Callable[[str], Any] = deterministic_input_builder,
                 input_builder_binding: dict[str, Any] | None = None,
                 time_seed_algorithm_binding: dict[str, Any] | None = None):
        self.store = store
        self.signer = signer
        self.verifier = verifier
        self.timing_attestor = timing_attestor
        self.engine_factory = engine_factory or RepositoryEngineFactory()
        self.max_body_bytes = max_body_bytes
        self.clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        if task_ttl_ms <= 0:
            raise ValueError("task_ttl_ms must be positive")
        self.task_ttl_ms = task_ttl_ms
        self.protocol_digests = {
            "image_digest": image_digest,
            "runtime_digest": runtime_digest,
            "resource_profile_digest": resource_profile_digest,
        }
        self.timing_authority_id = timing_authority_id
        self.timing_key_id = timing_key_id
        self.timing_ledger_id = timing_ledger_id
        self.timing_public_key_digest = timing_public_key_digest
        self.policy_bindings = {
            "policy_digest": policy_digest,
            "claim_paths_digest": claim_paths_digest,
            "attestation_claims_digest": attestation_claims_digest,
            "wip_policy_digest": wip_policy_digest,
        }
        if any(value is not None for value in self.policy_bindings.values()) and not all(self.policy_bindings.values()):
            raise ValueError("immutable policy bindings are incomplete")
        if verified_attestation_binding is not None and type(verified_attestation_binding) is not VerifiedAttestationBinding:
            raise ValueError("verified attestation binding is not adapter-created")
        if verified_attestation_binding is not None:
            public_binding = verified_attestation_binding.as_public_dict()
            claimed_binding_digest = public_binding.pop("binding_digest", None)
            if claimed_binding_digest != digest(public_binding):
                raise ValueError("verified attestation binding commitment is invalid")
        self.verified_attestation_binding = verified_attestation_binding
        self.wip_provider = wip_provider
        self.trusted_worker_supervisor = trusted_worker_supervisor
        if not callable(input_builder):
            raise ValueError("input builder must be callable")
        self.input_builder = input_builder
        self.input_builder_binding = dict(input_builder_binding or input_builder_binding_for_service())
        self.time_seed_algorithm_binding = dict(time_seed_algorithm_binding or time_seed_algorithm_binding_for_service())
        if verified_attestation_binding is not None:
            if wip_provider is not None and verified_attestation_binding.provider != wip_provider:
                raise ValueError("verified attestation provider mismatch")
            for key, expected in self.protocol_digests.items():
                bound = getattr(verified_attestation_binding, key, None)
                if expected is not None and bound is not None and bound != expected:
                    raise ValueError(f"verified attestation {key} mismatch")
            for key, expected in self.policy_bindings.items():
                if expected is not None and getattr(verified_attestation_binding, key, None) != expected:
                    raise ValueError(f"verified attestation {key} mismatch")
        self._engines: dict[str, Any] = {}
        self._run_stores: dict[str, ObjectStore] = {}

    def _run_store(self, run_id: str) -> ObjectStore:
        store = self._run_stores.get(run_id)
        if store is not None:
            return store
        binder = getattr(self.store, "bind_run", None)
        if callable(binder):
            store = binder(run_id)
            self._run_stores[run_id] = store
            return store
        # Local MemoryStore fixtures predate capability binding; production
        # stores expose bind_run and therefore never use this fallback.
        return self.store

    @property
    def authority(self) -> dict[str, Any]:
        return parse_canonical(canonical_bytes(self.signer.authority))

    @property
    def attestation_binding(self) -> VerifiedAttestationBinding | None:
        """The immutable redacted startup binding, never raw attestation data."""
        return self.verified_attestation_binding

    @property
    def timing_certified(self) -> bool:
        """Whether this service has an independently pinned timing attestor."""
        return bool(
            self.timing_attestor is not None
            and getattr(self.timing_attestor, "independent", False) is True
            and all((self.timing_authority_id, self.timing_key_id,
                     self.timing_ledger_id, self.timing_public_key_digest))
            and self.timing_public_key_digest != self.authority.get("public_key_digest")
        )

    @property
    def bounded_compute_ready(self) -> bool:
        """Whether a future supervisor claim could be accepted.

        Readiness is deliberately not certification: no claim is emitted until
        a trusted supervisor supplies and validates an evidence digest.
        """
        supervisor = self.trusted_worker_supervisor
        return bool(
            self.verified_attestation_binding is not None
            and self.timing_certified
            and supervisor is not None
            and getattr(supervisor, "trusted", False) is True
            and getattr(supervisor, "independent", False) is True
        )

    @property
    def bounded_compute_certified(self) -> bool:
        """Always false until an independently validated supervisor claim exists."""
        return False

    @staticmethod
    def _supervisor_validates_claim(supervisor: Any, claim: dict[str, Any]) -> bool:
        validator = getattr(supervisor, "validate_bounded_compute_claim", None)
        if not callable(validator):
            return False
        try:
            return validator(claim) is True
        except Exception:
            return False

    def validate_bounded_compute_claim(self, value: Any) -> dict[str, Any]:
        """Accept only a claim validated by the configured trusted supervisor."""
        if not self.bounded_compute_ready:
            raise ServiceError(503, "bounded-compute attestation gates unavailable")
        try:
            claim = bounded_compute_claim(value)
        except SchemaError as exc:
            raise ServiceError(422, str(exc)) from exc
        if claim["binding_digest"] != self.verified_attestation_binding.binding_digest:
            raise ServiceError(422, "bounded-compute attestation binding mismatch")
        if not self._supervisor_validates_claim(self.trusted_worker_supervisor, claim):
            raise ServiceError(503, "trusted worker supervisor rejected bounded-compute claim")
        return claim

    def _auth(self, headers: dict[str, str]) -> Principal:
        try:
            # Cloud Run consumes Authorization for its IAM check. Callers that
            # need both platform IAM and application OIDC auth send the same
            # token in X-P5-Authorization; local callers may keep using the
            # ordinary Authorization header.
            token = (headers.get("x-p5-authorization") or headers.get("X-P5-Authorization")
                     or headers.get("authorization") or headers.get("Authorization"))
            return self.verifier.verify(token)
        except AuthError as exc:
            raise ServiceError(401, str(exc)) from exc
        except Exception as exc:
            raise ServiceError(401, "invalid identity token") from exc

    def _json_body(self, raw: bytes) -> dict[str, Any]:
        if len(raw) > self.max_body_bytes:
            raise ServiceError(413, "request body too large")
        try:
            return parse_canonical(raw)
        except Exception as exc:
            raise ServiceError(422, "request must be canonical JSON") from exc

    def _get(self, name: str) -> dict[str, Any]:
        try:
            item = self.store.get(name)
            return parse_canonical(item.data)
        except Exception as exc:
            raise ServiceError(422, "required canonical object unavailable") from exc

    def _save_state(self, state: dict[str, Any], generation: int) -> int:
        try:
            return self._run_store(state["run_id"]).replace(self._state_name(state["run_id"]), canonical_bytes(state), generation).generation
        except StoreError as exc:
            # A failed generation write makes the in-memory evaluator
            # incomparable with the durable run; never continue using it.
            self._engines.pop(state.get("run_id"), None)
            raise ServiceError(409, "state generation conflict; run is impassable") from exc

    @staticmethod
    def _state_name(run_id: str) -> str:
        return f"runs/{run_id}/state.json"

    @staticmethod
    def _checkpoint_has_private_fields(value: Any) -> bool:
        if isinstance(value, dict):
            if any(key in {"truth", "secret_seed", "private_store", "private_truth"} for key in value):
                return True
            return any(EvaluatorService._checkpoint_has_private_fields(child) for child in value.values())
        if isinstance(value, list):
            return any(EvaluatorService._checkpoint_has_private_fields(child) for child in value)
        return False

    @classmethod
    def _checkpoint_engine(cls, state: dict[str, Any], engine: Any) -> None:
        checkpoint = getattr(engine, "checkpoint", None)
        if not callable(checkpoint):
            return
        try:
            value = checkpoint()
            canonical_bytes(value)
        except Exception as exc:
            raise ServiceError(503, "evaluator checkpoint unavailable") from exc
        if not isinstance(value, dict) or cls._checkpoint_has_private_fields(value):
            raise ServiceError(503, "evaluator checkpoint contains private truth")
        state["engine_checkpoint"] = value
        state["engine_checkpoint_digest"] = digest(value)

    @classmethod
    def _validate_checkpoint(cls, checkpoint: Any) -> dict[str, Any]:
        if not isinstance(checkpoint, dict) or cls._checkpoint_has_private_fields(checkpoint):
            raise ServiceError(503, "durable evaluator checkpoint unavailable; fail closed")
        try:
            canonical_bytes(checkpoint)
        except Exception as exc:
            raise ServiceError(503, "durable evaluator checkpoint unavailable; fail closed") from exc
        return checkpoint

    def _rehydrate_checkpoint(self, state: dict[str, Any], checkpoint: Any) -> Any:
        """Build a fresh engine from an independently validated checkpoint.

        The checkpoint argument is the caller's durable baseline. It must not
        be compared with, or installed through, the mutable state checkpoint:
        post-evaluation failures intentionally pass the old checkpoint while
        state may already contain a newer in-memory checkpoint.
        """
        checkpoint = self._validate_checkpoint(checkpoint)
        rehydrate = getattr(self.engine_factory, "rehydrate", None)
        if not callable(rehydrate):
            raise ServiceError(503, "evaluator rehydration unavailable; fail closed")
        try:
            lock, manifest, private_store = self._load_bundle({
                "lock_digest": state["lock_digest"],
                "manifest_digest": state["manifest_digest"],
                "worker_contract_digest": state["worker_contract_digest"],
            })
            for key, expected in (("lock_digest", lock["lock_digest"]), ("manifest_digest", manifest["manifest_digest"]),
                                  ("case_index_digest", manifest["index_digest"]), ("truth_digest", private_store["truth_digest"]),
                                  ("store_digest", private_store["store_digest"])):
                if state.get(key) != expected:
                    raise ValueError("run bundle commitment mismatch")
            return rehydrate(manifest, private_store, deepcopy(checkpoint))
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(503, "evaluator rehydration failed closed") from exc

    def _engine_for_state(self, state: dict[str, Any]) -> Any:
        engine = self._engines.get(state["run_id"])
        if engine is not None:
            return engine
        checkpoint = state.get("engine_checkpoint")
        if not isinstance(checkpoint, dict) or state.get("engine_checkpoint_digest") != digest(checkpoint):
            raise ServiceError(503, "evaluator checkpoint unavailable; fail closed")
        engine = self._rehydrate_checkpoint(state, checkpoint)
        self._engines[state["run_id"]] = engine
        return engine

    def _rehydrate_after_failed_evaluation(self, state: dict[str, Any], checkpoint: Any) -> None:
        """Drop the mutated engine and install only a fresh durable baseline."""
        run_id = state["run_id"]
        self._engines.pop(run_id, None)
        checkpoint = self._validate_checkpoint(checkpoint)
        try:
            engine = self._rehydrate_checkpoint(state, checkpoint)
        except Exception as exc:
            self._engines.pop(run_id, None)
            if isinstance(exc, ServiceError):
                raise
            raise ServiceError(503, "evaluator rehydration unavailable; fail closed") from exc
        # Keep the in-memory view aligned with the last committed state. The
        # next retry loads the same values from state.json, never the mutated
        # post-evaluation checkpoint.
        state["engine_checkpoint"] = deepcopy(checkpoint)
        state["engine_checkpoint_digest"] = digest(checkpoint)
        self._engines[run_id] = engine

    def _post_evaluation_call(self, state: dict[str, Any], checkpoint: Any, operation: Callable[[], Any]) -> Any:
        """Run a terminal persistence operation transactionally with the engine."""
        try:
            return operation()
        except Exception as exc:
            try:
                self._rehydrate_after_failed_evaluation(state, checkpoint)
            except Exception as rollback_exc:
                raise rollback_exc from exc
            raise

    @staticmethod
    def _response(value: dict[str, Any]) -> bytes:
        return canonical_bytes(value)

    def _now_ms(self) -> int:
        now = self.clock_ms()
        if type(now) is not int or now < 0:
            raise ServiceError(503, "trusted clock unavailable")
        return now

    def _check_protocol_digests(self, values: dict[str, Any]) -> None:
        for key, expected in self.protocol_digests.items():
            if expected is not None and values.get(key) != expected:
                raise ServiceError(422, f"{key} is not bound to the configured runtime")

    @staticmethod
    def _timing_outbox_name(run_id: str, task_id: str, event: str) -> str:
        operation_digest = digest({"task_id": task_id, "event": event})
        return f"runs/{run_id}/timing-outbox/{operation_digest}.json"

    @staticmethod
    def _timing_record_recovery_name(run_id: str, task_id: str, event: str) -> str:
        operation_digest = digest({"task_id": task_id, "event": event})
        return f"runs/{run_id}/timing-outbox/record-{operation_digest}.json"

    def _create_or_verify(self, name: str, data: bytes, message: str) -> None:
        """Create an immutable object, or accept only its exact prior value."""
        run_store = self._run_store(name.split("/")[1])
        try:
            run_store.create(name, data)
            return
        except StoreError as create_exc:
            try:
                existing = run_store.get(name)
            except Exception as get_exc:
                raise ServiceError(503, message) from get_exc
            if existing.data != data:
                raise ServiceError(409, message) from create_exc

    def _read_or_create_exact(self, name: str, value: dict[str, Any], message: str) -> dict[str, Any]:
        data = canonical_bytes(value)
        try:
            existing = self._run_store(name.split("/")[1]).get(name)
            if existing.data != data:
                raise ServiceError(409, message)
            return parse_canonical(existing.data)
        except ServiceError:
            raise
        except Exception:
            self._create_or_verify(name, data, message)
            return value

    def _validate_timing_record(self, state: dict[str, Any], value: dict[str, Any], *,
                                task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        last_sequence = state.get("timing_sequence", 0)
        if type(value.get("sequence")) is not int or value["sequence"] != last_sequence + 1:
            raise ValueError("timing sequence is not monotonic")
        independent_schema = value.get("schema") in {"P5R0IndependentTimingAttestationV2", "P5R0IndependentTimingAttestationV3"}
        if independent_schema:
            if not all((self.timing_authority_id, self.timing_key_id, self.timing_ledger_id, self.timing_public_key_digest)):
                raise ValueError("independent timing authority is not pinned")
            if self.timing_public_key_digest == self.authority.get("public_key_digest"):
                raise ValueError("independent timing key must differ from receipt key")
            expected_authority_id = self.timing_authority_id
            expected_key_id = self.timing_key_id
            expected_ledger_id = self.timing_ledger_id
            expected_public_key_digest = self.timing_public_key_digest
        else:
            if self.timing_authority_id is not None:
                raise ValueError("configured timing authority requires V2 or V3 records")
            expected_authority_id = None
            expected_key_id = None
            expected_ledger_id = None
            expected_public_key_digest = None
        previous = state.get("timing_record_digest")
        value = validate_attestation(value, run_id=state["run_id"], task_id=task_id, event=event,
                                     payload_digest=payload_digest, expected_authority_id=expected_authority_id,
                                     expected_key_id=expected_key_id, expected_public_key_digest=expected_public_key_digest,
                                     expected_ledger_id=expected_ledger_id, previous_digest=previous,
                                     last_sequence=last_sequence if independent_schema else None)
        if independent_schema and value.get("previous_digest") != previous:
            raise ValueError("timing chain is not continuous")
        return value

    def _record_timing(self, state: dict[str, Any], *, task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        if self.timing_attestor is None:
            raise ServiceError(503, "independent timing attestation unavailable")
        try:
            # A process with no store is retained only for the narrow unit-test
            # seam that exercises V3 validation directly. Production services
            # always have a durable store and therefore never call the recorder
            # without first creating the recovery marker.
            use_outbox = getattr(self, "store", None) is not None
            outbox_item = None
            outbox_created = False
            outbox_name = self._timing_outbox_name(state["run_id"], task_id, event)
            request = {"schema": "P5R0TimingOutboxRequestV1", "run_id": state["run_id"],
                       "task_id": task_id, "event": event, "payload_digest": payload_digest}
            request_digest = digest(request)
            if use_outbox:
                run_store = self._run_store(state["run_id"])
                try:
                    outbox_item = run_store.get(outbox_name)
                    outbox = parse_canonical(outbox_item.data)
                except Exception:
                    outbox = {"schema": "P5R0TimingOutboxV1", "request": request,
                              "request_digest": request_digest, "status": "pending",
                              "timing_record": None, "timing_record_digest": None}
                    try:
                        outbox_item = run_store.create(outbox_name, canonical_bytes(outbox))
                        outbox_created = True
                    except StoreError:
                        try:
                            outbox_item = run_store.get(outbox_name)
                            outbox = parse_canonical(outbox_item.data)
                        except Exception as exc:
                            raise ServiceError(503, "timing recovery marker unavailable; fail closed") from exc
                if set(outbox) != {"schema", "request", "request_digest", "status", "timing_record", "timing_record_digest"} or outbox.get("schema") != "P5R0TimingOutboxV1":
                    raise ValueError("timing recovery marker schema")
                if outbox.get("request") != request or outbox.get("request_digest") != request_digest:
                    raise ServiceError(409, "conflicting timing request reuse")
                recovery_name = self._timing_record_recovery_name(state["run_id"], task_id, event)
                recovered_record = None
                if outbox.get("status") == "pending":
                    try:
                        recovered_record = parse_canonical(run_store.get(recovery_name).data)
                        if not isinstance(recovered_record, dict):
                            raise ValueError("timing recovery record schema")
                    except ServiceError:
                        raise
                    except Exception:
                        recovered_record = None
                    if recovered_record is not None:
                        value = recovered_record
                    else:
                        if not outbox_created:
                            raise ServiceError(503, "timing recovery record unavailable; fail closed")
                        restore_chain = getattr(self.timing_attestor, "restore_chain", None)
                        if callable(restore_chain):
                            restore_chain(run_id=state["run_id"], sequence=state.get("timing_sequence", 0), previous_digest=state.get("timing_record_digest"))
                        value = self.timing_attestor.record(run_id=state["run_id"], task_id=task_id,
                                                            event=event, payload_digest=payload_digest)
                elif outbox.get("status") == "verified" and isinstance(outbox.get("timing_record"), dict):
                    value = outbox["timing_record"]
                    if outbox.get("timing_record_digest") != digest(value):
                        raise ValueError("timing recovery record digest")
                else:
                    raise ValueError("timing recovery marker status")
            else:
                restore_chain = getattr(self.timing_attestor, "restore_chain", None)
                if callable(restore_chain):
                    restore_chain(run_id=state["run_id"], sequence=state.get("timing_sequence", 0), previous_digest=state.get("timing_record_digest"))
                value = self.timing_attestor.record(run_id=state["run_id"], task_id=task_id,
                                                    event=event, payload_digest=payload_digest)
            value = self._validate_timing_record(state, value, task_id=task_id, event=event,
                                                 payload_digest=payload_digest)
            if use_outbox and outbox.get("status") == "pending":
                record_data = canonical_bytes(value)
                self._create_or_verify(recovery_name, record_data, "timing recovery record persistence conflict")
                verified = dict(outbox)
                verified["status"] = "verified"
                verified["timing_record"] = value
                verified["timing_record_digest"] = digest(value)
                try:
                    self._run_store(state["run_id"]).replace(outbox_name, canonical_bytes(verified), outbox_item.generation)
                except StoreError as exc:
                    raise ServiceError(503, "timing recovery record could not be committed; fail closed") from exc
            state["timing_sequence"] = value["sequence"]
            state["timing_record_digest"] = digest(value)
            return value
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(503, "independent timing attestation failed closed") from exc

    @staticmethod
    def _seed_binding(state: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        return {"schema": "P5ComputeClassSeedV1", "run_id": state["run_id"], "task_id": state["issued"]["task_id"], "sequence": state["issued"]["sequence"], "task_digest": state["issued"]["task_digest"], "idempotency_key": request["idempotency_key"]}

    def _seed_response(self, state: dict[str, Any]) -> dict[str, Any]:
        binding = state["seed_binding"]
        # Ed25519 signatures are deterministic. The challenge is therefore
        # reconstructible after a restart without persisting seed material.
        seed = self.signer.sign_digest(signing_digest(binding))
        if digest(seed) != state["seed_digest"]:
            raise ServiceError(503, "seed commitment mismatch")
        return {"schema": "P5ComputeClassSeedResponseV1", "run_id": state["run_id"], "task_id": state["issued"]["task_id"], "sequence": state["issued"]["sequence"], "seed": seed, "seed_digest": state["seed_digest"], "issued_at_ms": state["seed_issued_at_ms"], "expires_at_ms": state["seed_expires_at_ms"], "authority_id": self.authority["authority_id"], "key_id": self.authority["key_id"], "public_key": self.authority["public_key"], "public_key_digest": self.authority["public_key_digest"]}

    def _require_fresh(self, issued: dict[str, Any]) -> None:
        if self._now_ms() >= issued["expires_at_ms"]:
            raise ServiceError(409, "task or seed has expired")

    def _authority_check(self, lock: dict[str, Any], worker_contract_digest: str) -> None:
        authority = self.authority
        if lock.get("authority") != authority or lock.get("authority_digest") != digest(authority):
            raise ServiceError(422, "lock authority is not the configured KMS authority")
        if lock.get("authority_transport_digest") != digest(authority["transport_attestation"]):
            raise ServiceError(422, "lock authority transport binding")
        if lock.get("lock_digest") != digest({k: v for k, v in lock.items() if k not in {"lock_digest", "signature"}}):
            raise ServiceError(422, "lock commitment")
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from .canonical import b64decode
            Ed25519PublicKey.from_public_bytes(b64decode(authority["public_key"])).verify(
                b64decode(lock["signature"]), signing_digest(lock, "lock_digest")
            )
        except Exception as exc:
            raise ServiceError(422, "lock signature") from exc
        if lock.get("schema") != "P5R0LocalLockV3" or lock.get("classification") != "local_readiness_only" or lock.get("non_release") is not True:
            raise ServiceError(422, "unsupported lock")
        worker = lock.get("worker_contract")
        if not isinstance(worker, dict) or worker.get("task_schema") != "P5R0WorkerTaskV3" or worker.get("reply_schema") != "P5R0WorkerReplyV3" or worker.get("digest") != worker_contract_digest:
            raise ServiceError(422, "worker contract")
        if any(value is not None for value in self.policy_bindings.values()):
            for key, expected in self.policy_bindings.items():
                if lock.get(key) != expected:
                    raise ServiceError(422, f"immutable {key} mismatch")
            if not isinstance(lock.get("policy"), dict) or lock["policy"].get("policy_digest") != self.policy_bindings["policy_digest"]:
                raise ServiceError(422, "immutable policy object mismatch")

    def _load_bundle(self, request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        lock = self._get(f"locks/{request['lock_digest']}.json")
        manifest = self._get(f"manifests/{request['manifest_digest']}.json")
        private_store = self._get(f"truth/{lock.get('store_digest')}.json")
        self._authority_check(lock, request["worker_contract_digest"])
        if lock.get("lock_digest") != request["lock_digest"] or lock.get("manifest_digest") != request["manifest_digest"]:
            raise ServiceError(422, "requested commitment does not match lock")
        manifest_fields = {"schema", "case_index", "index_digest", "truth_digest", "store_digest", "split_digest", "manifest_digest"}
        allowed_manifest_fields = manifest_fields | {"input_builder_binding", "time_seed_algorithm_binding"}
        if not isinstance(manifest, dict) or not set(manifest).issubset(allowed_manifest_fields) or not manifest_fields.issubset(manifest) or manifest.get("manifest_digest") != request["manifest_digest"] or manifest.get("index_digest") != lock.get("case_index_digest") or manifest.get("manifest_digest") != digest({k: v for k, v in manifest.items() if k != "manifest_digest"}):
            raise ServiceError(422, "manifest commitment")
        for key in ("input_builder_binding", "time_seed_algorithm_binding"):
            value = manifest.get(key)
            if value is not None and (not isinstance(value, dict) or value.get("binding_digest") != digest({k: v for k, v in value.items() if k != "binding_digest"})):
                raise ServiceError(422, f"{key} commitment")
            if value is not None and lock.get(key) != value:
                raise ServiceError(422, f"lock/{key} binding")
        if set(private_store) != {"schema", "case_index_digest", "truth_digest", "cases", "store_digest"} or private_store.get("store_digest") != lock.get("store_digest") or private_store.get("truth_digest") != lock.get("truth_digest") or private_store.get("case_index_digest") != lock.get("case_index_digest") or private_store.get("store_digest") != digest({"case_index_digest": private_store.get("case_index_digest"), "truth_digest": private_store.get("truth_digest"), "cases": private_store.get("cases")}):
            raise ServiceError(422, "private store commitment")
        if private_store.get("schema") != "P5R0CaseStoreV2" or not isinstance(private_store.get("cases"), list):
            raise ServiceError(422, "private store schema")
        return lock, manifest, private_store

    def start(self, request: dict[str, Any], principal: Principal) -> dict[str, Any]:
        try:
            request = run_start(request)
        except SchemaError as exc:
            raise ServiceError(422, str(exc)) from exc
        req_digest = digest(request)
        run_id = digest({"schema": "P5R0RunV1", "lock_digest": request["lock_digest"], "manifest_digest": request["manifest_digest"], "principal": principal.subject, "idempotency_key": request["idempotency_key"]})
        run_store = self._run_store(run_id)
        idem_name = f"runs/{run_id}/idempotency/start-{digest(request['idempotency_key'])}.json"
        try:
            item = run_store.get(idem_name)
            saved = parse_canonical(item.data)
            if saved.get("request_digest") != req_digest:
                raise ServiceError(409, "idempotency key reused with different request")
            return saved["response"]
        except ServiceError:
            raise
        except Exception:
            pass
        lock, manifest, private_store = self._load_bundle(request)
        if request["execution_mode"] == "timing_first":
            if not isinstance(manifest.get("input_builder_binding"), dict) or not isinstance(manifest.get("time_seed_algorithm_binding"), dict):
                raise ServiceError(422, "timing-first source commitments are unavailable")
            if lock.get("input_builder_binding") != manifest["input_builder_binding"] or lock.get("time_seed_algorithm_binding") != manifest["time_seed_algorithm_binding"]:
                raise ServiceError(422, "timing-first lock source commitments mismatch")
        state = {"schema": "P5R0RunStateV1", "run_id": run_id, "principal": principal.subject, "execution_mode": request["execution_mode"], "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "case_index_digest": manifest["index_digest"], "truth_digest": private_store["truth_digest"], "store_digest": private_store["store_digest"], "input_builder_binding": manifest.get("input_builder_binding"), "time_seed_algorithm_binding": manifest.get("time_seed_algorithm_binding"), "policy_digest": lock.get("policy_digest", digest(lock["policy"])), "claim_paths_digest": lock.get("claim_paths_digest"), "attestation_claims_digest": lock.get("attestation_claims_digest"), "wip_policy_digest": lock.get("wip_policy_digest"), "worker_contract_digest": request["worker_contract_digest"], "timing_certified": self.timing_certified, "timing_sequence": 0, "timing_record_digest": None, "time_seed_timing_record_digest": None, "time_seed_input_seed_digest": None, "time_seed_input_digest": None, "status": "active", "cursor": 0, "next_sequence": 1, "issued": None, "receipts": [], "receipt_sequence": 0, "idempotency": {}, "completed_results": {}, "compute_observations": {}}
        try:
            engine = self.engine_factory.create(manifest, private_store)
            self._checkpoint_engine(state, engine)
            self._engines[run_id] = engine
            receipt = self._append_receipt(state, "preregistered", "verified", {"lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "case_index_digest": manifest["index_digest"], "truth_digest": private_store["truth_digest"], "store_digest": private_store["store_digest"], "worker_contract_digest": request["worker_contract_digest"]})
            state["receipts"].append(receipt["receipt_hash"])
            state_obj = run_store.create(self._state_name(run_id), canonical_bytes(state))
            response = {"schema": "P5R0RunStartResponseV1", "run_id": run_id, "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "case_index_digest": manifest["index_digest"], "truth_digest": private_store["truth_digest"], "store_digest": private_store["store_digest"], "policy_digest": state["policy_digest"], "worker_contract_digest": request["worker_contract_digest"], "authority_id": self.authority["authority_id"], "key_id": self.authority["key_id"], "public_key": self.authority["public_key"], "public_key_digest": self.authority["public_key_digest"], "status": "active", "next_sequence": 1}
            idem = {"schema": "P5R0IdempotencyV1", "request_digest": req_digest, "response": response}
            run_store.create(idem_name, canonical_bytes(idem))
            return response
        except (StoreError, ServiceError) as exc:
            self._engines.pop(run_id, None)
            if isinstance(exc, ServiceError):
                raise
            raise ServiceError(409, "run creation conflict") from exc
        except Exception as exc:
            self._engines.pop(run_id, None)
            raise ServiceError(503, "evaluator initialization failed closed") from exc

    def _load_run(self, run_id: str, principal: Principal) -> tuple[dict[str, Any], int]:
        if len(run_id) != 71 or not run_id.startswith("sha256:"):
            raise ServiceError(404, "run not found")
        try:
            item = self._run_store(run_id).get(self._state_name(run_id))
            state = parse_canonical(item.data)
        except Exception as exc:
            raise ServiceError(404, "run not found") from exc
        if state.get("principal") != principal.subject:
            raise ServiceError(403, "run principal mismatch")
        return state, item.generation

    def _schedule(self, manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        # Controls/contrasts are intentionally not synthesized by the HTTP wrapper.
        # A run with only this primary schedule can never be reported as GO.
        return [(arm, row) for arm in ("cold_reset", "frozen_transfer", "warm_adaptive") for row in manifest["case_index"]]

    def _append_receipt(self, state: dict[str, Any], kind: str, outcome: str, binding: dict[str, Any]) -> dict[str, Any]:
        sequence = int(state["receipt_sequence"]) + 1
        previous = state["receipts"][-1] if state["receipts"] else None
        payload = {"schema": "P5R0ReceiptPayloadV3", "run_id": state["run_id"], "kind": kind, "outcome": outcome, "binding": dict(binding), "resources": {}}
        receipt = {"schema": "P5R0ReceiptV3", "sequence": sequence, "previous_hash": previous, "payload": payload, "receipt_hash": "", "signature": ""}
        receipt["receipt_hash"] = digest({k: v for k, v in receipt.items() if k not in {"receipt_hash", "signature"}})
        receipt["signature"] = sign_object(receipt, self.signer, "receipt_hash")
        name = f"runs/{state['run_id']}/receipts/{sequence:06d}.json"
        self._create_or_verify(name, canonical_bytes(receipt), "receipt persistence conflict")
        state["receipt_sequence"] = sequence
        return receipt

    def _seed_intent(self, state: dict[str, Any], namespace: str) -> dict[str, Any]:
        namespace_digest = digest(namespace)
        task_id = digest({"schema": "P5R0TimeSeedTaskV1", "run_id": state["run_id"], "namespace": namespace, "sequence": 0})
        payload_digest = digest({"schema": "P5R0TimeSeedRequestV1", "run_id": state["run_id"], "namespace": namespace, "sequence": 0})
        value = {"schema": "P5R0TimeSeedIntentV1", "run_id": state["run_id"], "namespace_digest": namespace_digest,
                 "task_id": task_id, "payload_digest": payload_digest,
                 "intent_digest": digest({"run_id": state["run_id"], "namespace_digest": namespace_digest, "task_id": task_id, "payload_digest": payload_digest})}
        name = f"runs/{state['run_id']}/timing-outbox/seed-intent.json"
        return self._read_or_create_exact(name, value, "conflicting time-seed request reuse")

    def _result_intent(self, state: dict[str, Any], task_id: str, request_digest: str, issued: dict[str, Any]) -> int:
        base = {"schema": "P5R0ResultIntentV1", "run_id": state["run_id"], "task_id": task_id,
                "sequence": issued["sequence"], "task_digest": issued["task_digest"],
                "request_digest": request_digest}
        name = f"runs/{state['run_id']}/result-intent/{digest(task_id)}.json"
        try:
            intent = parse_canonical(self._run_store(state["run_id"]).get(name).data)
        except Exception:
            intent = dict(base)
            intent["received_at_ms"] = self._now_ms()
            self._create_or_verify(name, canonical_bytes(intent), "conflicting result request recovery")
        if (intent.get("schema") != "P5R0ResultIntentV1" or intent.get("run_id") != state["run_id"]
                or intent.get("task_id") != task_id or intent.get("sequence") != issued["sequence"]
                or intent.get("task_digest") != issued["task_digest"] or intent.get("request_digest") != request_digest
                or type(intent.get("received_at_ms")) is not int):
            raise ServiceError(409, "conflicting result request recovery")
        return intent["received_at_ms"]

    def issue_time_seed(self, run_id: str, namespace: str, principal: Principal) -> dict[str, Any]:
        """Record and durably commit the one-shot timing-first event.

        This is deliberately service-owned: callers cannot advance the timing
        adapter or derive an input without the event being part of the run's
        durable timing and receipt chains.
        """
        if not isinstance(namespace, str) or not namespace:
            raise ServiceError(422, "time-seed namespace is invalid")
        state, generation = self._load_run(run_id, principal)
        if state.get("status") != "active" or state.get("cursor") != 0 or state.get("issued") is not None:
            raise ServiceError(409, "time-seed operation is not available")
        if state.get("time_seed_timing_record_digest") is not None:
            raise ServiceError(409, "time-seed operation already committed")
        if not self.timing_certified:
            raise ServiceError(503, "independent V3 timing authority unavailable for time seed")
        intent = self._seed_intent(state, namespace)
        task_id = intent["task_id"]
        payload_digest = intent["payload_digest"]
        timing_record = self._record_timing(state, task_id=task_id, event="task_issued", payload_digest=payload_digest)
        if timing_record.get("schema") != "P5R0IndependentTimingAttestationV3":
            raise ServiceError(503, "time-seed timing must be independently certified V3")
        timing_digest_value = digest(timing_record)
        seeded = None
        if state.get("execution_mode") == "timing_first":
            if self.input_builder_binding != state.get("input_builder_binding") or self.time_seed_algorithm_binding != state.get("time_seed_algorithm_binding"):
                raise ServiceError(422, "configured source commitments do not match the run lock")
            try:
                seeded = derive_time_seed(
                    timing_record, run_id=run_id, namespace=namespace,
                    sequence=timing_record["sequence"], input_builder=self.input_builder,
                    input_builder_binding=self.input_builder_binding,
                    time_seed_algorithm_binding=self.time_seed_algorithm_binding,
                )
            except Exception as exc:
                raise ServiceError(503, "timing-first input derivation failed closed") from exc
        timing_name = f"runs/{run_id}/timing/{timing_record['sequence']:06d}-seed.json"
        try:
            self._create_or_verify(timing_name, canonical_bytes(timing_record), "timing record persistence conflict")
            receipt = self._append_receipt(state, "time_seed_issued", "verified", {
                "task_id": task_id, "namespace_digest": digest(namespace),
                "payload_digest": payload_digest, "timing_record_digest": timing_digest_value,
                "input_seed_digest": seeded.input_seed_digest if seeded is not None else None,
                "input_digest": seeded.input_digest if seeded is not None else None,
                "input_builder_source_digest": self.input_builder_binding.get("source_digest") if seeded is not None else None,
                "time_seed_algorithm_source_digest": self.time_seed_algorithm_binding.get("source_digest") if seeded is not None else None,
            })
            state["receipts"].append(receipt["receipt_hash"])
            state["time_seed_timing_record_digest"] = timing_digest_value
            state["time_seed_namespace_digest"] = digest(namespace)
            state["time_seed_input_seed_digest"] = seeded.input_seed_digest if seeded is not None else None
            state["time_seed_input_digest"] = seeded.input_digest if seeded is not None else None
            self._save_state(state, generation)
        except Exception as exc:
            self._engines.pop(run_id, None)
            if isinstance(exc, ServiceError):
                raise
            raise ServiceError(503, "durable time-seed persistence failed closed") from exc
        response = {"schema": "P5R0TimeSeedResponseV1", "run_id": run_id, "task_id": task_id, "timing_record": timing_record, "timing_record_digest": timing_digest_value, "namespace_digest": digest(namespace)}
        if seeded is not None:
            response.update({"input_seed_digest": seeded.input_seed_digest, "input_digest": seeded.input_digest, "input_builder_binding": self.input_builder_binding, "time_seed_algorithm_binding": self.time_seed_algorithm_binding})
        return response

    def next_task(self, run_id: str, request: dict[str, Any], principal: Principal) -> dict[str, Any]:
        try:
            request = next_task(request)
        except SchemaError as exc:
            raise ServiceError(422, str(exc)) from exc
        state, generation = self._load_run(run_id, principal)
        req_digest = digest(request)
        prior = state["idempotency"].get("next:" + request["idempotency_key"])
        if prior is not None:
            if prior["request_digest"] != req_digest:
                raise ServiceError(409, "idempotency key reused with different request")
            return prior["response"]
        if request["expected_sequence"] != state["next_sequence"]:
            raise ServiceError(409, "sequence conflict")
        if state["issued"] is not None:
            self._require_fresh(state["issued"])
            response = state["issued"]["response"]
            state["idempotency"]["next:" + request["idempotency_key"]] = {"request_digest": req_digest, "response": response}
            self._save_state(state, generation)
            return response
        if state["status"] != "active":
            raise ServiceError(409, "run is closed")
        if state.get("execution_mode") == "timing_first":
            required_seed_fields = ("time_seed_timing_record_digest", "time_seed_input_seed_digest", "time_seed_input_digest")
            if any(not isinstance(state.get(key), str) for key in required_seed_fields):
                raise ServiceError(409, "timing-first seed must be committed before task issuance")
        manifest = self._get(f"manifests/{state['manifest_digest']}.json")
        schedule = self._schedule(manifest)
        if state["cursor"] >= len(schedule):
            raise ServiceError(409, "run has no next task")
        arm, case = schedule[state["cursor"]]
        task_id = digest({"run_id": run_id, "sequence": state["next_sequence"], "case_id": case["case_id"], "arm": arm})
        nonce = digest({"task_id": task_id, "nonce": request["idempotency_key"]})
        engine = self._engine_for_state(state)
        try:
            task = engine.issue(arm=arm, case=case, sequence=state["next_sequence"], task_id=task_id, nonce=nonce, control=None)
            if set(task) != {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "episode_step", "reset_policy", "arm", "persistent_projection", "control"} or task["schema"] != "P5R0WorkerTaskV3":
                raise ValueError("worker task shape")
            self._checkpoint_engine(state, engine)
            task_digest = digest(task)
            issued_at_ms = self._now_ms()
            timing = None
            if self.timing_attestor is not None:
                timing = self._record_timing(state, task_id=task_id, event="task_issued", payload_digest=task_digest)
            expires_at_ms = issued_at_ms + self.task_ttl_ms
            envelope = {"schema": "P5R0TaskEnvelopeV1", "run_id": run_id, "task_id": task_id, "sequence": state["next_sequence"], "task_digest": task_digest, "task": task, "issued_at_ms": issued_at_ms, "expires_at_ms": expires_at_ms, "authority_id": self.authority["authority_id"], "key_id": self.authority["key_id"], "public_key_digest": self.authority["public_key_digest"], "signature": ""}
            envelope["signature"] = sign_object(envelope, self.signer)
            response = {"schema": "P5R0NextTaskResponseV1", "run_id": run_id, "task_id": task_id, "sequence": state["next_sequence"], "phase": "primary", "case_id": case["case_id"], "side": "primary", "pair_id": None, "task_digest": task_digest, "task": task, "task_envelope": envelope, "authority": self.authority, "issued_at_ms": issued_at_ms, "expires_at_ms": expires_at_ms}
            task_response(response)
            state["seed_binding"] = None
            state["seed_digest"] = None
            state["seed_request_digest"] = None
            state["seed_issued_at_ms"] = None
            state["seed_expires_at_ms"] = None
            state["timing_observations"] = {}
            state["issued"] = {"task_id": task_id, "sequence": state["next_sequence"], "task_digest": task_digest, "case_id": case["case_id"], "arm": arm, "task": task, "timing_attestation": timing, "issued_at_ms": issued_at_ms, "expires_at_ms": expires_at_ms, "response": response}
            state["idempotency"]["next:" + request["idempotency_key"]] = {"request_digest": req_digest, "response": response}
            self._save_state(state, generation)
            return response
        except ServiceError:
            self._engines.pop(run_id, None)
            raise
        except Exception as exc:
            raise ServiceError(503, "task construction failed closed") from exc

    def issue_compute_seed(self, run_id: str, task_id: str, request: dict[str, Any], principal: Principal) -> dict[str, Any]:
        try:
            request = compute_class_seed(request, run_id, task_id)
        except SchemaError as exc:
            raise ServiceError(422, str(exc)) from exc
        state, generation = self._load_run(run_id, principal)
        issued = state.get("issued")
        if not isinstance(issued, dict) or issued.get("task_id") != task_id or issued.get("sequence") != request["sequence"]:
            raise ServiceError(409, "no matching outstanding task")
        self._require_fresh(issued)
        req_digest = digest(request)
        if state.get("seed_digest") is not None:
            if state.get("seed_request_digest") != req_digest:
                raise ServiceError(409, "only one seed issuance is permitted per task")
            return self._seed_response(state)
        binding = self._seed_binding(state, request)
        seed = self.signer.sign_digest(signing_digest(binding))
        state["seed_binding"] = binding
        state["seed_digest"] = digest(seed)
        state["seed_request_digest"] = req_digest
        state["seed_issued_at_ms"] = self._now_ms()
        state["seed_expires_at_ms"] = issued["expires_at_ms"]
        state["idempotency"]["seed:" + request["idempotency_key"]] = {"request_digest": req_digest, "response_digest": digest(seed)}
        self._save_state(state, generation)
        return self._seed_response(state)

    def compute_class_observation(self, run_id: str, request: dict[str, Any], principal: Principal) -> dict[str, Any]:
        try:
            request = compute_class_observation_request(request, run_id)
        except SchemaError as exc:
            raise ServiceError(422, str(exc)) from exc
        state, generation = self._load_run(run_id, principal)
        req_digest = digest(request)
        prior = state["idempotency"].get("compute:" + request["idempotency_key"])
        if prior is not None:
            if prior["request_digest"] != req_digest:
                raise ServiceError(409, "idempotency key reused with different observation request")
            return prior["response"]
        observations_by_sequence = state.setdefault("compute_observations", {})
        existing_observation = observations_by_sequence.get(str(request["sequence"]))
        if existing_observation is not None:
            raise ServiceError(409, "compute-class observation already exists for this task")
        completed = state.get("completed_results", {}).get(str(request["sequence"]))
        issued = state.get("issued")
        if not isinstance(completed, dict) or completed.get("task_id") != request["task_id"]:
            raise ServiceError(409, "result is not committed for this task")
        self._require_fresh(completed)
        if issued is not None:
            raise ServiceError(409, "task result is not committed")
        if completed.get("task_digest") != request["task_digest"] or completed.get("result_digest") != request["result_digest"]:
            raise ServiceError(409, "compute-class binding mismatch")
        if state.get("seed_digest") != request["seed_digest"]:
            raise ServiceError(409, "compute-class seed mismatch")
        self._check_protocol_digests(request)
        issued_at_ms = completed["issued_at_ms"]
        received_at_ms = completed["received_at_ms"]
        if received_at_ms < issued_at_ms:
            raise ServiceError(503, "trusted clock moved backwards")
        timing_digests = {
            "task": digest({"schema": "P5R0ServerTimingV1", "run_id": run_id, "task_id": request["task_id"], "sequence": request["sequence"], "event": "task_issued", "task_digest": completed["task_digest"], "observed_at_ms": issued_at_ms}),
            "result": digest({"schema": "P5R0ServerTimingV1", "run_id": run_id, "task_id": request["task_id"], "sequence": request["sequence"], "event": "result_received", "task_digest": completed["task_digest"], "result_digest": completed["result_digest"], "observed_at_ms": received_at_ms}),
        }
        observation = {"schema": "P5ComputeClassObservationV2", "run_id": run_id, "task_id": request["task_id"], "sequence": request["sequence"], "task_digest": completed["task_digest"], "seed_digest": request["seed_digest"], "timing_observation_digests": timing_digests, "wall_time_bucket": coarse_wall_bucket(received_at_ms - issued_at_ms), "cpu_time_bucket": "not_observed", "image_digest": request["image_digest"], "runtime_digest": request["runtime_digest"], "resource_profile_digest": request["resource_profile_digest"], "result_digest": completed["result_digest"], "wall_vs_cpu": "provider_wall_transport_interval_not_worker_cpu", "limitation": "This signed observation reports a coarse service-observed wall interval from task issuance to result receipt; it is not a worker CPU-time or process-containment measurement.", "issued_at_ms": issued_at_ms, "received_at_ms": received_at_ms, "expires_at_ms": completed["expires_at_ms"], "authority_id": self.authority["authority_id"], "key_id": self.authority["key_id"], "public_key": self.authority["public_key"], "public_key_digest": self.authority["public_key_digest"], "observation_digest": "", "signature": ""}
        observation["observation_digest"] = digest({key: value for key, value in observation.items() if key not in {"observation_digest", "signature"}})
        observation["signature"] = sign_object(observation, self.signer, "observation_digest")
        try:
            compute_class_observation(observation)
        except SchemaError as exc:
            raise ServiceError(503, "compute-class observation construction failed closed") from exc
        try:
            self._run_store(run_id).create(f"runs/{run_id}/compute-class/observation-{request['sequence']:06d}.json", canonical_bytes(observation))
        except StoreError as exc:
            raise ServiceError(409, "compute-class observation persistence conflict") from exc
        observations_by_sequence[str(request["sequence"])] = observation
        state["idempotency"]["compute:" + request["idempotency_key"]] = {"request_digest": req_digest, "response": observation}
        self._save_state(state, generation)
        return observation

    def submit_result(self, run_id: str, task_id: str, request: dict[str, Any], principal: Principal) -> dict[str, Any]:
        try:
            request = task_result(request, run_id, task_id)
        except SchemaError as exc:
            raise ServiceError(422, str(exc)) from exc
        state, generation = self._load_run(run_id, principal)
        req_digest = digest(request)
        idem_key = "result:" + request["idempotency_key"]
        prior = state["idempotency"].get(idem_key)
        if prior is not None:
            if prior["request_digest"] != req_digest:
                raise ServiceError(409, "idempotency key reused with different request")
            return prior["response"]
        issued = state.get("issued")
        if not isinstance(issued, dict) or issued.get("task_id") != task_id:
            raise ServiceError(409, "no matching outstanding task")
        if state.get("execution_mode") == "timing_first":
            evidence = request["execution_evidence"]
            if evidence.get("schema") != "P5R0ExecutionEvidenceV2":
                raise ServiceError(422, "legacy untimed execution evidence is diagnostic-only")
            expected_evidence_bindings = {
                "timing_record_digest": state.get("time_seed_timing_record_digest"),
                "input_seed_digest": state.get("time_seed_input_seed_digest"),
                "input_digest": state.get("time_seed_input_digest"),
                "input_builder_implementation": (state.get("input_builder_binding") or {}).get("implementation"),
                "input_builder_version": (state.get("input_builder_binding") or {}).get("version"),
                "input_builder_source_digest": (state.get("input_builder_binding") or {}).get("source_digest"),
                "time_seed_algorithm_source_digest": (state.get("time_seed_algorithm_binding") or {}).get("source_digest"),
            }
            if any(evidence.get(key) != value for key, value in expected_evidence_bindings.items()):
                raise ServiceError(422, "timing-first evidence commitment mismatch")
        self._require_fresh(issued)
        if request["sequence"] != issued["sequence"] or request["task_digest"] != issued["task_digest"] or digest(issued["task"]) != request["task_digest"]:
            raise ServiceError(409, "task replay or digest mismatch")
        received_at_ms = self._result_intent(state, task_id, req_digest, issued)
        checkpoint_before = deepcopy(state.get("engine_checkpoint"))
        engine = self._engine_for_state(state)
        manifest = self._get(f"manifests/{state['manifest_digest']}.json")
        case = next((row for row in manifest["case_index"] if row["case_id"] == issued["case_id"]), None)
        if case is None:
            raise ServiceError(422, "case commitment unavailable")
        try:
            outcome = engine.evaluate(arm=issued["arm"], case=case, task=issued["task"], reply=request["reply"])
            self._checkpoint_engine(state, engine)
            outcome_name = str(outcome.get("outcome", "protocol_error"))
        except Exception as exc:
            self._rehydrate_after_failed_evaluation(state, checkpoint_before)
            if isinstance(exc, ServiceError):
                raise
            outcome = None
            outcome_name = "protocol_error"
        evidence_digest = digest(request["execution_evidence"])
        receive_timing = None
        if self.timing_attestor is not None:
            receive_timing = self._post_evaluation_call(state, checkpoint_before, lambda: self._record_timing(state, task_id=task_id, event="result_received", payload_digest=req_digest))
        if issued.get("timing_attestation") is not None:
            self._post_evaluation_call(state, checkpoint_before, lambda: self._create_or_verify(f"runs/{run_id}/timing/{issued['sequence']:06d}-issued.json", canonical_bytes(issued["timing_attestation"]), "timing record persistence conflict"))
        if receive_timing is not None:
            self._post_evaluation_call(state, checkpoint_before, lambda: self._create_or_verify(f"runs/{run_id}/timing/{issued['sequence']:06d}-received.json", canonical_bytes(receive_timing), "timing record persistence conflict"))
        timing_binding = {"issued": timing_digest(issued.get("timing_attestation")), "received": timing_digest(receive_timing), "certified": bool(getattr(self.timing_attestor, "independent", False) and receive_timing is not None and receive_timing.get("schema") in {"P5R0IndependentTimingAttestationV2", "P5R0IndependentTimingAttestationV3"})}
        record_source = {"schema": "P5R0EvaluatorOutcomeV3", "outcome": outcome_name, "task_digest": issued["task_digest"], "result_digest": req_digest, "case_id": issued["case_id"], "arm": issued["arm"], "reply": request["reply"], "evaluator_digest": digest(outcome or {"protocol_error": True})}
        record = {"schema": "P5R0TaskRecordV2", "run_id": run_id, "task_id": task_id, "sequence": issued["sequence"], "phase": "primary", "case_id": issued["case_id"], "arm": issued["arm"], "outcome": outcome_name, "action": request["reply"]["action"], "task_digest": issued["task_digest"], "result_digest": req_digest, "worker_invocation": request["worker_invocation"], "worker_exit": request["worker_exit"], "execution_evidence_digest": evidence_digest, "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "timing_attestation": timing_binding, "evaluator_digest": digest(record_source)}
        self._post_evaluation_call(state, checkpoint_before, lambda: self._create_or_verify(f"runs/{run_id}/evidence/{issued['sequence']:06d}.json", canonical_bytes(request["execution_evidence"]), "evidence persistence conflict"))
        receipt = self._post_evaluation_call(state, checkpoint_before, lambda: self._append_receipt(state, "terminal", outcome_name if outcome_name in {"complete_correct", "complete_wrong", "abstain", "protocol_error", "resource_exhausted", "safety_violation", "containment_failure", "rollback_impasse"} else "containment_failure", {"task_digest": issued["task_digest"], "result_digest": req_digest, "record_digest": digest(record), "evidence_digest": evidence_digest, "lock_digest": state["lock_digest"], "worker_invocation": request["worker_invocation"], "native_verified": False, "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "timing": timing_binding}))
        state["receipts"].append(receipt["receipt_hash"])
        state.setdefault("completed_results", {})[str(issued["sequence"])] = {"task_id": task_id, "task_digest": issued["task_digest"], "result_digest": req_digest, "record_digest": digest(record), "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "expires_at_ms": issued["expires_at_ms"]}
        state["cursor"] += 1
        state["next_sequence"] += 1
        state["issued"] = None
        manifest = self._get(f"manifests/{state['manifest_digest']}.json")
        done = state["cursor"] >= len(self._schedule(manifest))
        disposition = "in_progress"
        if done:
            try:
                engine.restore()
                commitment = self._seal_commitment(state, "cloud wrapper lacks independent native closure attestation")
                close = self._post_evaluation_call(state, checkpoint_before, lambda: self._append_receipt(state, "run_closed", "containment_failure", {"lock_digest": state["lock_digest"], "native_verified": False, "reason": "cloud wrapper lacks independent native closure attestation", "seal_commitment_digest": digest(commitment)}))
                state["receipts"].append(close["receipt_hash"])
                state["status"] = "impasse"
                disposition = "impasse"
                seal = self._post_evaluation_call(state, checkpoint_before, lambda: self._make_seal(state, commitment, close["receipt_hash"]))
                state["result"] = seal
            except Exception as exc:
                self._rehydrate_after_failed_evaluation(state, checkpoint_before)
                raise ServiceError(503, "run close persistence failed closed") from exc
        response = {"schema": "P5R0TaskResultResponseV2", "run_id": run_id, "task_id": task_id, "sequence": issued["sequence"], "outcome": outcome_name, "result_digest": req_digest, "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "record": record, "receipt": receipt, "next_sequence": state["next_sequence"], "done": done, "disposition": disposition}
        state["idempotency"][idem_key] = {"request_digest": req_digest, "response": response}
        self._post_evaluation_call(state, checkpoint_before, lambda: self._save_state(state, generation))
        return response

    def _seal_commitment(self, state: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            "schema": "P5R0SealCommitmentV1", "run_id": state["run_id"],
            "lock_digest": state["lock_digest"], "manifest_digest": state["manifest_digest"],
            "policy_bindings": {key: state.get(key) for key in ("policy_digest", "claim_paths_digest", "attestation_claims_digest", "wip_policy_digest")},
            "outcome": "local_readiness_only/no_go", "disposition": "impasse",
            "preclose_chain_digest": digest(state["receipts"]),
            "preclose_receipt_count": len(state["receipts"]),
            "timing_digest": digest([state.get("timing_certified"), state["receipts"]]),
            "input_commitments": {
                "timing_record_digest": state.get("time_seed_timing_record_digest"),
                "input_seed_digest": state.get("time_seed_input_seed_digest"),
                "input_digest": state.get("time_seed_input_digest"),
                "input_builder_binding": state.get("input_builder_binding"),
                "time_seed_algorithm_binding": state.get("time_seed_algorithm_binding"),
            },
            "native_verified": False, "timing_certified": bool(state.get("timing_certified")),
            "gate_reasons": [reason, "controls and mechanics contrasts are not synthesized by this wrapper"] + ([] if state.get("timing_certified") else ["no independent timing/seed ledger configured"]),
            "claim_boundary": "No release, adoption, positive transfer, P5 claim, or general intelligence claim.",
        }

    def _make_seal(self, state: dict[str, Any], commitment: dict[str, Any], terminal_receipt_hash: str | None) -> dict[str, Any]:
        seal = {
            "schema": "P5R0ResultSealV4", "run_id": state["run_id"],
            "commitment": commitment, "seal_digest": digest(commitment),
            "terminal_receipt_hash": terminal_receipt_hash,
            "chain_digest": digest(state["receipts"]), "receipt_count": len(state["receipts"]),
            "native_verified": False, "timing_certified": bool(state.get("timing_certified")),
            "external_authority_verified": False,
            "receipt_public_key": self.authority["public_key"],
            "receipt_public_key_digest": self.authority["public_key_digest"],
            "signature": "",
        }
        seal["signature"] = sign_object(seal, self.signer)
        self._create_or_verify(f"runs/{state['run_id']}/result.seal.json", canonical_bytes(seal), "result seal persistence conflict")
        return seal

    def _verify_result_seal(self, state: dict[str, Any], seal: dict[str, Any]) -> None:
        if not isinstance(seal, dict) or seal.get("schema") != "P5R0ResultSealV4":
            raise ServiceError(503, "result seal schema invalid")
        commitment = seal.get("commitment")
        if not isinstance(commitment, dict) or seal.get("seal_digest") != digest(commitment):
            raise ServiceError(503, "result seal commitment invalid")
        if commitment.get("run_id") != state["run_id"] or commitment.get("lock_digest") != state["lock_digest"] or commitment.get("manifest_digest") != state["manifest_digest"]:
            raise ServiceError(503, "result seal run binding invalid")
        expected_policy_bindings = {key: state.get(key) for key in ("policy_digest", "claim_paths_digest", "attestation_claims_digest", "wip_policy_digest")}
        if commitment.get("policy_bindings") != expected_policy_bindings:
            raise ServiceError(503, "result seal policy binding invalid")
        expected_input_commitments = {
            "timing_record_digest": state.get("time_seed_timing_record_digest"),
            "input_seed_digest": state.get("time_seed_input_seed_digest"),
            "input_digest": state.get("time_seed_input_digest"),
            "input_builder_binding": state.get("input_builder_binding"),
            "time_seed_algorithm_binding": state.get("time_seed_algorithm_binding"),
        }
        if commitment.get("input_commitments") != expected_input_commitments:
            raise ServiceError(503, "result seal input commitment invalid")
        if seal.get("chain_digest") != digest(state["receipts"]) or seal.get("receipt_count") != len(state["receipts"]):
            raise ServiceError(503, "result seal receipt binding invalid")
        if seal.get("receipt_public_key") != self.authority["public_key"] or seal.get("receipt_public_key_digest") != self.authority["public_key_digest"]:
            raise ServiceError(503, "result seal authority binding invalid")
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from .canonical import b64decode
            Ed25519PublicKey.from_public_bytes(b64decode(self.authority["public_key"])).verify(b64decode(seal["signature"]), signing_digest(seal))
        except Exception as exc:
            raise ServiceError(503, "result seal signature invalid") from exc
        previous = None
        receipts = []
        for sequence, expected_hash in enumerate(state["receipts"], 1):
            try:
                item = self._run_store(state["run_id"]).get(f"runs/{state['run_id']}/receipts/{sequence:06d}.json")
                receipt = parse_canonical(item.data)
            except Exception as exc:
                raise ServiceError(503, "receipt chain unavailable") from exc
            if receipt.get("sequence") != sequence or receipt.get("previous_hash") != previous or receipt.get("receipt_hash") != expected_hash or receipt.get("receipt_hash") != digest({k: v for k, v in receipt.items() if k not in {"receipt_hash", "signature"}}):
                raise ServiceError(503, "receipt chain tampered")
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                from .canonical import b64decode
                Ed25519PublicKey.from_public_bytes(b64decode(self.authority["public_key"])).verify(b64decode(receipt["signature"]), signing_digest(receipt, "receipt_hash"))
            except Exception as exc:
                raise ServiceError(503, "receipt signature invalid") from exc
            receipts.append(receipt)
            previous = receipt["receipt_hash"]
        close = receipts[-1] if receipts else None
        if close is None or close.get("payload", {}).get("kind") != "run_closed" or close.get("payload", {}).get("binding", {}).get("seal_commitment_digest") != seal["seal_digest"] or seal.get("terminal_receipt_hash") != close["receipt_hash"]:
            raise ServiceError(503, "result seal close binding invalid")

    def result(self, run_id: str, principal: Principal) -> dict[str, Any]:
        state, _ = self._load_run(run_id, principal)
        if state.get("status") != "impasse":
            return {"schema": "P5R0RunResultResponseV1", "run_id": run_id, "status": state["status"], "disposition": "in_progress", "result_seal": None, "chain_digest": digest(state["receipts"]), "receipt_public_key": self.authority["public_key"], "receipt_public_key_digest": self.authority["public_key_digest"], "evidence_uri": f"runs/{run_id}/evidence/"}
        seal = state.get("result")
        if not isinstance(seal, dict):
            raise ServiceError(503, "result seal unavailable")
        try:
            persisted = parse_canonical(self._run_store(run_id).get(f"runs/{run_id}/result.seal.json").data)
        except Exception as exc:
            raise ServiceError(503, "result seal unavailable") from exc
        if persisted != seal:
            raise ServiceError(503, "result seal state/storage mismatch")
        self._verify_result_seal(state, persisted)
        return {"schema": "P5R0RunResultResponseV1", "run_id": run_id, "status": "impasse", "disposition": "impasse", "result_seal": persisted, "chain_digest": persisted["chain_digest"], "receipt_public_key": self.authority["public_key"], "receipt_public_key_digest": self.authority["public_key_digest"], "evidence_uri": f"runs/{run_id}/evidence/"}

    def dispatch(self, method: str, path: str, raw_body: bytes, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        try:
            principal = self._auth(headers)
            parts = [unquote(part) for part in path.split("/") if part]
            if method == "POST" and parts == ["v1", "runs"]:
                result = self.start(self._json_body(raw_body), principal)
            elif method == "POST" and len(parts) == 5 and parts[0:2] == ["v1", "runs"] and parts[3:] == ["tasks", "next"]:
                result = self.next_task(parts[2], self._json_body(raw_body), principal)
            elif method == "POST" and len(parts) == 4 and parts[0:2] == ["v1", "runs"] and parts[3] == "time-seed":
                body = self._json_body(raw_body)
                if body.get("schema") != "P5R0TimeSeedRequestV1" or body.get("run_id") != parts[2] or not isinstance(body.get("namespace"), str) or not isinstance(body.get("idempotency_key"), str):
                    raise ServiceError(422, "time-seed request")
                result = self.issue_time_seed(parts[2], body["namespace"], principal)
            elif method == "POST" and len(parts) == 6 and parts[0:2] == ["v1", "runs"] and parts[3] == "tasks" and parts[5] == "seed":
                result = self.issue_compute_seed(parts[2], parts[4], self._json_body(raw_body), principal)
            elif method == "POST" and len(parts) == 5 and parts[0:2] == ["v1", "runs"] and parts[3:] == ["compute-class", "observation"]:
                result = self.compute_class_observation(parts[2], self._json_body(raw_body), principal)
            elif method == "POST" and len(parts) == 6 and parts[0:2] == ["v1", "runs"] and parts[3] == "tasks" and parts[5] == "result":
                result = self.submit_result(parts[2], parts[4], self._json_body(raw_body), principal)
            elif method == "GET" and len(parts) == 4 and parts[0:2] == ["v1", "runs"] and parts[3] == "result":
                if raw_body:
                    raise ServiceError(422, "GET must not have a body")
                result = self.result(parts[2], principal)
            else:
                raise ServiceError(404, "route not found")
            return 200, {"content-type": "application/json", "cache-control": "no-store"}, self._response(result)
        except ServiceError as exc:
            return exc.status, {"content-type": "application/json", "cache-control": "no-store"}, self._response({"schema": "P5R0ErrorV1", "error": exc.message})
        except Exception:
            return 503, {"content-type": "application/json", "cache-control": "no-store"}, self._response({"schema": "P5R0ErrorV1", "error": "internal evaluator failure; fail closed"})
