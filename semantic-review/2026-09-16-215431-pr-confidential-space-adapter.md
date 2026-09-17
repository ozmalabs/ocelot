# Confidential Space adapter with attestation-gated cloud capabilities

The change adds a locked evaluator bootstrap that fetches a Confidential Space metadata JWT, verifies its signature and configured claims, exchanges it through Workload Identity Federation, and only then constructs GCS and KMS clients. The service keeps private case material behind the evaluator and exposes authenticated task/result protocols rather than cloud capabilities to the worker. Task expiry, nonce binding, exact image/project/TEE checks, generation-checked storage, and KMS signing are present. **Watch for:** **confirmed** timing is certified by the same local KMS authority rather than an independent ledger, the terminal result seal is not signed or included in the receipt chain, and the checked-in deployment manifest does not provide the environment required by the adapter; **confirmed** the bootstrap also accepts arbitrary fields in authority metadata before attestation.

**Verdict**: NEEDS_CHANGES

## High-level view

The locked path is materially separated from cloud activation: policy parsing does not create ADC, GCS, KMS, or truth clients, and activation requires a fresh metadata-token nonce plus exact configured claims. **Confirmed** WIP binding is not closed by configuration, because the attestation audience and provider can differ and the metadata endpoint is freely overridden; the deployment artifacts leave the actual claim mapping and provider condition as placeholders.

After activation, one federated access token is passed explicitly to storage and KMS clients, while `ScopedObjectStore` limits application calls to private bundle prefixes and `runs/`. **Confirmed** that is a prefix capability, not a per-run capability, so least privilege depends on the service never making a path mistake and on IAM conditions that are only described in prose.

The protocol does bind task/result digests, server timestamps, expiry, and signed receipts, and it intentionally labels wall time as transport time rather than worker CPU time. **Confirmed** the default timing record is still produced by the same service signer, its signature is not verified by the validator, and the final seal has only a digest; the resulting `timing_certified` and terminal-proof claims are stronger than the evidence stored.

Private truth is not serialized into worker tasks or HTTP responses, and the adapter relocks when the federated expiry is reached on a subsequent request. The local tests cover the main happy and failure paths, but do not exercise the configuration mismatches, independent timing authenticity, process restart/replay behavior, or terminal-seal verification that remain relevant to deployment.

<details>
<summary>Issues (7)</summary>

1. **Pre-attestation authority fields (confirmed)** — `P5R0_AUTHORITY_JSON` is parsed before attestation without enforcing the public-only closed schema. Reject extra/private fields during locked bootstrap.
2. **WIP and metadata endpoint binding (confirmed)** — Attestation and STS audiences can differ, and the metadata URL is arbitrary. Require provider/audience equality and restrict the source to the Confidential Space metadata endpoint.
3. **Cross-run storage capability (likely)** — The runtime can read and write any object below `runs/`, not only the current run. Narrow the capability/IAM condition or explicitly enforce and test the required cross-run boundary.
4. **Independent timing certification (confirmed)** — The default timing record is signed by the same local KMS authority, and validation does not verify signatures or durable sequence. Use an independently anchored, verifiable ledger before setting `timing_certified`.
5. **Unsigned terminal seal (confirmed)** — `seal_digest` is not signed and is not included in the final signed receipt chain. Sign the seal or bind its digest into a final receipt and verify it on read.
6. **Deployment policy wiring (confirmed)** — The manifest uses `P5R0_IMAGE_DIGEST` while code requires `P5R0_EXPECTED_IMAGE_DIGEST` and omits the required attestation/WIP policy variables. Align and supply the complete reviewed non-secret configuration.
7. **Missing boundary regression coverage (confirmed)** — Tests do not cover malformed pre-attestation authority, provider mismatch, non-metadata endpoints, timing authenticity/restart, seal tampering, cross-run access, or restart with an outstanding task. Add those cases before approval.

</details>

<details>
<summary>Details</summary>

### Locked bootstrap and exact attestation binding

The `AttestationGate` requires a freshly generated nonce, passes it to the metadata source, verifies the JWT through Google’s verifier, and compares audience, issuer, nonce, `iat`/`exp`, image digest, project, zone, debug state, TEE, secure boot, and workload against the locked policy. The adapter does not accept an attestation token from an HTTP caller, and `GoogleSTSClient` rejects an STS audience that is not the same canonical provider string it is given. **Confirmed** expiry/replay handling is request-driven: an expired federated capability is dropped before the next health/protected dispatch, while the in-flight request and any process-local client cleanup are not actively interrupted.

**Confirmed gap — pre-attestation authority metadata is not constrained to public fields.** `LockedBootstrapConfig.from_env` parses arbitrary canonical `P5R0_AUTHORITY_JSON` into the locked config, while the closed-field check occurs only later in `KMSEd25519Signer`. An operator could therefore place a private-key or other secret field in an environment value that is read before attestation, contrary to a strong no-secret-before-attestation guarantee. Enforce the exact public authority schema during locked parsing, or keep only a separately validated public-key reference in pre-attestation configuration.

**Confirmed gap — WIP and metadata trust endpoints are not closed by the adapter.** `AttestationGate` verifies the token for `attestation_audience`, but activation sends the same subject token to STS with `wip_provider`; `LockedBootstrapConfig` never requires those two values to be equal. `metadata_token_url` is also an unrestricted environment override, so the code does not itself guarantee that the nonce and audience go only to the Confidential Space metadata endpoint. Require the canonical audience/provider equality and validate or hard-code the expected metadata host and path; keep the provider-side CEL condition bound to the same exact image and workload claims.

### Federated clients and prefix capabilities

**Likely gap — the storage capability is broader than a least-privilege run capability.** `ScopedObjectStore` permits reads of every object below `runs/` and creates/replaces anywhere below `runs/`, while the deployment IAM guidance grants the runtime identity the corresponding broad prefix. A service compromise or future path bug could therefore access another principal’s run state/evidence. Bind the capability and IAM condition to the current run where possible, or document and enforce why a single process must have cross-run access; add negative tests for cross-run object names and untrusted path variants.

### Timing attestations and terminal receipt proof

Task and result records use server-observed timestamps and explicitly label the interval as transport time rather than worker CPU time. The task/result receipt signatures and generation preconditions provide integrity for individual objects.

**Confirmed gap — `timing_certified` does not mean independently observed.** `CapabilityFactory.build` always constructs `SignedTimingAttestor(signer)`, and that class signs with the same local KMS authority used for evaluator receipts. `_make_seal` then sets `timing_certified` solely from the presence of that attestor. This proves that the service recorded its own events, not that an independent clock/seed ledger observed freshness or ordering. In addition, `validate_attestation` checks only that `signature` is a non-empty string; it does not verify the signature, authority, observed-time format, or monotonic sequence, and the sequence resets on process restart. Require a separately anchored attestor for certification, cryptographically verify its records, persist/reconcile sequence state, and leave the seal uncertified otherwise.

**Confirmed gap — the terminal seal is a digest without an authenticating signature.** `_make_seal` emits `seal_digest` but no signature, and the preceding `run_closed` receipt does not include that digest. A consumer can recompute the digest but cannot establish that the returned terminal seal was issued by the configured authority or that it is the seal corresponding to the signed receipt chain. Sign the seal itself or include its digest in a final signed receipt, then verify that binding when serving `/result`.

### Private truth boundary and lifecycle

Private truth stays out of worker tasks and HTTP responses, while expiry is observed when a request enters the adapter rather than proactively revoking work already executing.

### Coverage against the claimed deployment contract

The 16 local tests cover locked startup, exact nonce and image rejection, STS request formation, explicit fake GCS/KMS clients, scoped paths, expiry relocking, KMS signature verification, private-commitment flows, server timing, and replay/idempotency behavior. Python compilation also passes.

**Confirmed gap — the checked-in Cloud Run manifest cannot satisfy the adapter’s required configuration as written.** `cloud-run.yaml` sets `P5R0_IMAGE_DIGEST`, but `LockedBootstrapConfig.from_env` requires `P5R0_EXPECTED_IMAGE_DIGEST`; it also omits `P5R0_ATTESTATION_AUDIENCE`, `P5R0_WIP_PROVIDER`, `P5R0_ATTESTATION_ISSUER`, expected project/zone/TEE/debug/secure-boot/workload values, claim paths, and metadata configuration. The separate metadata example contains placeholders and is not wired into the manifest. Align the variable names and provide a reviewed, complete non-secret policy before treating the adapter as deployable.

The tests do not cover malformed authority fields before activation, mismatched attestation/provider audiences, a non-metadata token URL, fake or unverifiable timing signatures, timing sequence reset, unsigned seal tampering, cross-run storage access, or a restart with an outstanding task. Those cases should be added before approval because they map directly to the gaps above.

</details>

<details>
<summary>File map</summary>

- `services/p5_r0_evaluator/confidential_space.py` — locked Confidential Space gate, STS exchange, capability factory, scoped storage, and timing attestor.
- `services/p5_r0_evaluator/app.py` — locked WSGI entrypoint and bounded request handling.
- `services/p5_r0_evaluator/store.py` — explicit-credential GCS adapter and generation-checked object operations.
- `services/p5_r0_evaluator/signing.py` — KMS Ed25519 public-key validation and signing.
- `services/p5_r0_evaluator/timing.py` — timing-attestation shape validation and coarse wall buckets.
- `services/p5_r0_evaluator/service.py` and `schemas.py` — authenticated evaluator protocol, receipts, result seals, and compute-class observations.
- `services/p5_r0_evaluator/deploy/*` — review-only deployment, IAM, metadata, and WIP policy artifacts.
- `services/p5_r0_evaluator/tests/*` — 16 local adapter/service tests.

The full review input is the untracked adapter addition under `services/p5_r0_evaluator` plus its deployment and test artifacts; `git diff main` does not include these untracked files. The repository also contains unrelated pre-existing worktree changes that were not reviewed.

</details>
