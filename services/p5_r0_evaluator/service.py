from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Callable
from urllib.parse import unquote

from .attestation_binding import VerifiedAttestationBinding
from .auth import AuthError
from .canonical import b64encode, canonical_bytes, digest, parse_canonical, signing_digest
from .engine import RepositoryEngineFactory
from .interfaces import EngineFactory, ObjectStore, Principal, Signer, StoreError, TokenVerifier
from .schemas import (SchemaError, bounded_compute_claim, compute_class_observation, compute_class_observation_request, compute_class_seed,
                      execution_evidence, next_task, run_start,
                      task_result, task_response)
from .signing import sign_object
from .timing import TimingAttestor, coarse_wall_bucket, timing_digest, validate_attestation


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
                 trusted_worker_supervisor: Any | None = None):
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
        return deepcopy(self.signer.authority)

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
            raise ServiceError(409, "state generation conflict; run is impassable") from exc

    @staticmethod
    def _state_name(run_id: str) -> str:
        return f"runs/{run_id}/state.json"

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

    def _record_timing(self, state: dict[str, Any], *, task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        if self.timing_attestor is None:
            raise ServiceError(503, "independent timing attestation unavailable")
        try:
            value = self.timing_attestor.record(run_id=state["run_id"], task_id=task_id, event=event, payload_digest=payload_digest)
            last_sequence = state.get("timing_sequence", 0)
            if type(value.get("sequence")) is not int or value["sequence"] != last_sequence + 1:
                raise ValueError("timing sequence is not monotonic")
            if value.get("schema") == "P5R0IndependentTimingAttestationV2":
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
                    raise ValueError("configured timing authority requires V2 records")
                expected_authority_id = None
                expected_key_id = None
                expected_ledger_id = None
                expected_public_key_digest = None
            previous = state.get("timing_record_digest")
            value = validate_attestation(value, run_id=state["run_id"], task_id=task_id, event=event, payload_digest=payload_digest, expected_authority_id=expected_authority_id, expected_key_id=expected_key_id, expected_public_key_digest=expected_public_key_digest, expected_ledger_id=expected_ledger_id, previous_digest=previous, last_sequence=last_sequence if value.get("schema") == "P5R0IndependentTimingAttestationV2" else None)
            if value.get("schema") == "P5R0IndependentTimingAttestationV2" and value.get("previous_digest") != previous:
                raise ValueError("timing chain is not continuous")
            state["timing_sequence"] = value["sequence"]
            state["timing_record_digest"] = digest(value)
            return value
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
        if set(manifest) != {"schema", "case_index", "index_digest", "truth_digest", "store_digest", "split_digest", "manifest_digest"} or manifest.get("manifest_digest") != request["manifest_digest"] or manifest.get("index_digest") != lock.get("case_index_digest") or manifest.get("manifest_digest") != digest({k: v for k, v in manifest.items() if k != "manifest_digest"}):
            raise ServiceError(422, "manifest commitment")
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
        state = {"schema": "P5R0RunStateV1", "run_id": run_id, "principal": principal.subject, "lock_digest": lock["lock_digest"], "manifest_digest": manifest["manifest_digest"], "case_index_digest": manifest["index_digest"], "truth_digest": private_store["truth_digest"], "store_digest": private_store["store_digest"], "policy_digest": lock.get("policy_digest", digest(lock["policy"])), "claim_paths_digest": lock.get("claim_paths_digest"), "attestation_claims_digest": lock.get("attestation_claims_digest"), "wip_policy_digest": lock.get("wip_policy_digest"), "worker_contract_digest": request["worker_contract_digest"], "timing_certified": self.timing_certified, "timing_sequence": 0, "timing_record_digest": None, "status": "active", "cursor": 0, "next_sequence": 1, "issued": None, "receipts": [], "receipt_sequence": 0, "idempotency": {}, "completed_results": {}, "compute_observations": {}}
        try:
            engine = self.engine_factory.create(manifest, private_store)
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
        try:
            self._run_store(state["run_id"]).create(name, canonical_bytes(receipt))
        except StoreError as exc:
            raise ServiceError(409, "receipt persistence conflict") from exc
        state["receipt_sequence"] = sequence
        return receipt

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
        manifest = self._get(f"manifests/{state['manifest_digest']}.json")
        schedule = self._schedule(manifest)
        if state["cursor"] >= len(schedule):
            raise ServiceError(409, "run has no next task")
        arm, case = schedule[state["cursor"]]
        task_id = digest({"run_id": run_id, "sequence": state["next_sequence"], "case_id": case["case_id"], "arm": arm})
        nonce = digest({"task_id": task_id, "nonce": request["idempotency_key"]})
        engine = self._engines.get(run_id)
        if engine is None:
            raise ServiceError(503, "evaluator state unavailable; fail closed")
        try:
            task = engine.issue(arm=arm, case=case, sequence=state["next_sequence"], task_id=task_id, nonce=nonce, control=None)
            if set(task) != {"schema", "case_token", "task_nonce", "observation", "legal_actions", "protocol_budget", "episode_step", "reset_policy", "arm", "persistent_projection", "control"} or task["schema"] != "P5R0WorkerTaskV3":
                raise ValueError("worker task shape")
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
        received_at_ms = self._now_ms()
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
        self._require_fresh(issued)
        if request["sequence"] != issued["sequence"] or request["task_digest"] != issued["task_digest"] or digest(issued["task"]) != request["task_digest"]:
            raise ServiceError(409, "task replay or digest mismatch")
        engine = self._engines.get(run_id)
        if engine is None:
            raise ServiceError(503, "evaluator state unavailable; fail closed")
        manifest = self._get(f"manifests/{state['manifest_digest']}.json")
        case = next((row for row in manifest["case_index"] if row["case_id"] == issued["case_id"]), None)
        if case is None:
            raise ServiceError(422, "case commitment unavailable")
        try:
            outcome = engine.evaluate(arm=issued["arm"], case=case, task=issued["task"], reply=request["reply"])
            outcome_name = str(outcome.get("outcome", "protocol_error"))
        except Exception:
            outcome = None
            outcome_name = "protocol_error"
        evidence_digest = digest(request["execution_evidence"])
        receive_timing = None
        if self.timing_attestor is not None:
            receive_timing = self._record_timing(state, task_id=task_id, event="result_received", payload_digest=req_digest)
        if issued.get("timing_attestation") is not None:
            self._run_store(run_id).create(f"runs/{run_id}/timing/{issued['sequence']:06d}-issued.json", canonical_bytes(issued["timing_attestation"]))
        if receive_timing is not None:
            self._run_store(run_id).create(f"runs/{run_id}/timing/{issued['sequence']:06d}-received.json", canonical_bytes(receive_timing))
        timing_binding = {"issued": timing_digest(issued.get("timing_attestation")), "received": timing_digest(receive_timing), "certified": bool(getattr(self.timing_attestor, "independent", False) and receive_timing is not None and receive_timing.get("schema") == "P5R0IndependentTimingAttestationV2")}
        record_source = {"schema": "P5R0EvaluatorOutcomeV3", "outcome": outcome_name, "task_digest": issued["task_digest"], "result_digest": req_digest, "case_id": issued["case_id"], "arm": issued["arm"], "reply": request["reply"], "evaluator_digest": digest(outcome or {"protocol_error": True})}
        record = {"schema": "P5R0TaskRecordV2", "run_id": run_id, "task_id": task_id, "sequence": issued["sequence"], "phase": "primary", "case_id": issued["case_id"], "arm": issued["arm"], "outcome": outcome_name, "action": request["reply"]["action"], "task_digest": issued["task_digest"], "result_digest": req_digest, "worker_invocation": request["worker_invocation"], "worker_exit": request["worker_exit"], "execution_evidence_digest": evidence_digest, "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "timing_attestation": timing_binding, "evaluator_digest": digest(record_source)}
        self._run_store(run_id).create(f"runs/{run_id}/evidence/{issued['sequence']:06d}.json", canonical_bytes(request["execution_evidence"]))
        receipt = self._append_receipt(state, "terminal", outcome_name if outcome_name in {"complete_correct", "complete_wrong", "abstain", "protocol_error", "resource_exhausted", "safety_violation", "containment_failure", "rollback_impasse"} else "containment_failure", {"task_digest": issued["task_digest"], "result_digest": req_digest, "record_digest": digest(record), "evidence_digest": evidence_digest, "lock_digest": state["lock_digest"], "worker_invocation": request["worker_invocation"], "native_verified": False, "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "timing": timing_binding})
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
                close = self._append_receipt(state, "run_closed", "containment_failure", {"lock_digest": state["lock_digest"], "native_verified": False, "reason": "cloud wrapper lacks independent native closure attestation", "seal_commitment_digest": digest(commitment)})
                state["receipts"].append(close["receipt_hash"])
                state["status"] = "impasse"
                disposition = "impasse"
                seal = self._make_seal(state, commitment, close["receipt_hash"])
                state["result"] = seal
            except Exception:
                state["status"] = "impasse"
                state["result"] = self._make_seal(state, self._seal_commitment(state, "rollback or close failed"), None)
                disposition = "impasse"
        response = {"schema": "P5R0TaskResultResponseV2", "run_id": run_id, "task_id": task_id, "sequence": issued["sequence"], "outcome": outcome_name, "result_digest": req_digest, "issued_at_ms": issued["issued_at_ms"], "received_at_ms": received_at_ms, "record": record, "receipt": receipt, "next_sequence": state["next_sequence"], "done": done, "disposition": disposition}
        state["idempotency"][idem_key] = {"request_digest": req_digest, "response": response}
        self._save_state(state, generation)
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
        self._run_store(state["run_id"]).create(f"runs/{state['run_id']}/result.seal.json", canonical_bytes(seal))
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
