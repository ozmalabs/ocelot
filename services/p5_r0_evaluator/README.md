# P5-R0 V3 evaluator service

This is an isolated, authenticated control-plane wrapper for the existing `evaluation.p5_r0` evaluator. It is not deployed by this change.

The Confidential Space workload is deliberately separate from the Cloud Run entrypoint: `Dockerfile`/`app.py` remain the Cloud Run path, while `Dockerfile.confidential-space`, `deploy/Containerfile`, and `confidential_space_app.py` form the dedicated attested image path. The latter starts with policy-only locked state and exposes `/healthz` plus non-secret `/startup-attestation` evidence before activation.

## Guarantees

- HTTP bodies, GCS objects, task envelopes, receipts, and seals use strict canonical JSON. Duplicate keys, floats, non-NFC strings, unknown fields, and non-canonical bytes fail closed.
- The service reads lock/public manifest/private store commitments from private GCS through `ObjectStore`; truth is never returned to the runner. GCS writes use create-only or generation preconditions.
- `KMSEd25519Signer` obtains and validates the configured KMS `EC_SIGN_ED25519` public key, sends the protocol's SHA-256 digest as raw signing data, and verifies every returned signature locally. No private key is exported or accepted by the service.
- Google-signed OIDC identity tokens are required and the runner principal is bound to run state. Start, task, and result operations enforce idempotency, one outstanding task, sequence, task digest, and immutable receipt replay checks.
- Task envelopes and V3 receipts are signed by the configured authority. The service always reports no-go/impasse for this minimal wrapper because Cloud Run cannot independently prove local crun containment, controls, mechanics contrasts, or rollback closure.

## Timing and third-party seeds

The service records task issuance and result receipt timestamps with its trusted process clock. These timestamps are never accepted from the runner. The task envelope and response expose the service-issued `issued_at_ms` and `expires_at_ms`; terminal records, receipts, and result responses bind the service-observed `received_at_ms` and the exact canonical `result_digest` (the digest of the complete result request). The compute-class observation derives its coarse wall bucket from those two server timestamps.

A `TimingAttestor` may additionally record signed `task_issued` and `result_received` events. Such an attestor certifies freshness/order and its provider-observed interval, not the worker's exact CPU start/end or process containment. A runner-submitted timestamp, duration, timeout flag, or seed is never treated as an observation. Timing remains uncertified for GO purposes when no independent attestor is configured.

## Protocol adaptations still required

The checked-in V3 lock currently uses `P5R0AuthorityV2`, local filesystem receipt roots, and closure fields for local crun/Podman. This service introduces `P5R0AuthorityV3`, `P5R0TaskEnvelopeV1`, HTTP request/response schemas, GCS URI object names, and `P5R0ResultSealV3HTTP`; an adapter is needed before the existing local `verify_result_seal` can verify a GCS-backed seal. The wrapper currently schedules only the 144 primary records and intentionally does not synthesize the locked controls/contrast matrix. It therefore emits an explicit impasse rather than claiming GO.

## Local checks

From the repository root: `PYTHONPATH=. pytest services/p5_r0_evaluator/tests -q` and `python -m py_compile services/p5_r0_evaluator/*.py`. Docker/Cloud Run deployment is deliberately not invoked.


## Compute-class protocol

The compute-class endpoints are application-authenticated with the same Google OIDC verifier as the run control plane. Cloud Run ingress must remain internal; `Authorization` is reserved for platform IAM when applicable and `X-P5-Authorization` carries the application token. No endpoint is intended for public ingress.

1. `POST /v1/runs/{run_id}/tasks/{task_id}/seed` issues one deterministic challenge derived by the configured Cloud KMS Ed25519 key. The response may contain the challenge, but durable state stores only its `seed_digest`, binding, and expiry; private truth and challenge material are never written to GCS. Reusing the same idempotency key returns the same KMS-derived challenge; a different key cannot issue a second seed.
2. `POST /v1/runs/{run_id}/compute-class/observation` requires the committed result, exact server-issued task digest, exact service-computed result digest, seed, and immutable runtime commitments. It emits a signed `P5ComputeClassObservationV2` containing service-observed issuance/receipt timestamps and a coarse wall bucket derived only from their difference. Replays are idempotent and conflicting reuse fails with 409. There is deliberately no runner timing endpoint.

The signed compute-class record states `wall_vs_cpu: provider_wall_transport_interval_not_worker_cpu` and `cpu_time_bucket: not_observed`. A service-observed interval includes request transport and does not prove worker CPU start/end, process containment, or scheduler behavior. The observation is consequently an auditable coarse timing commitment, not a CPU-time or isolation claim. Production startup requires `P5R0_IMAGE_DIGEST`, `P5R0_RUNTIME_DIGEST`, and `P5R0_RESOURCE_PROFILE_DIGEST`; these are non-secret immutable commitments supplied through deployment configuration.

The service still uses generation-checked private GCS objects and never serializes the private case store into run state or responses. It fails closed on expired tasks, missing seed bindings, mismatched runtime commitments, missing timing events, replay conflicts, stale state generations, and unavailable engine state. The Cloud KMS signer only sends SHA-256 digests to `asymmetric_sign`; private key material is neither accepted nor exportable by this service.
