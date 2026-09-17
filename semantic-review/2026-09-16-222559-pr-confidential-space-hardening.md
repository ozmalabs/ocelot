# Attestation-gated Confidential Space evaluator hardening

This change hardens the evaluator bootstrap so policy is parsed into an immutable locked state, the Confidential Space token is fetched only from the pinned metadata endpoint, and GCS/KMS capabilities are created only after the token has passed the configured claim and WIP checks. It also replaces broad run storage with a run-bound child capability, validates independently signed V2 timing records when supplied, and signs V4 terminal seals that bind the close receipt and complete receipt chain. The focused suite passes 21 tests and covers the requested pre-attestation, WIP, timing, path, expiry, and seal-boundary attacks. **Watch for:** **confirmed** the production factory still has no independent V2 timing attestor, **confirmed** the KMS signer retains an ambient-ADC construction escape hatch, and **confirmed** the deployment artifacts contain values that make startup fail or remain placeholders; **likely** the configurable claim paths and rendered WIP condition are not guaranteed to describe the same token.

**Verdict**: NEEDS_CHANGES

## High-level view

The locked adapter keeps cloud clients and private storage behind successful attestation, freezes the public authority/provider relationship, and relocks when the federated token expires. The run-bound store rejects traversal and cross-run names, but **confirmed** direct `KMSEd25519Signer` construction without a client can still create a default-credential KMS client outside that normal factory boundary.

The timing path is fail-closed: the built-in KMS-signed V1 recorder is diagnostic, while `timing_certified` requires an independently signed V2 record. **Confirmed**: the production factory never constructs such a ledger, and V2 `ledger_id` is not pinned across events. V4 seals are signed and re-verified against the close receipt and complete receipt chain when `/result` is read.

The policy parser closes the authority shape and canonical WIP provider, but **confirmed** the deployment system remains a template. The Cloud Run manifest and image recipe contain unresolved project, image, key, authority, digest, and timing values; IAM and WIP conditions are prose/templates only, and the deployment docs disagree over the image-digest variable name. **Likely**: configurable claim paths can diverge from the CEL template unless rendering enforces equality.

<details>
<summary>Issues (8)</summary>

1. **KMS ambient-client escape hatch** — **confirmed**: `KMSEd25519Signer` constructs `KeyManagementServiceClient()` when called without a client, allowing an exported capability constructor to reach ambient ADC outside the attestation/STS path. Require an explicit federated client at the signer boundary.
2. **Independent timing provider** — **confirmed**: `CapabilityFactory.build()` always installs the local KMS-backed V1 recorder, so no production path emits independently signed V2 evidence and every normal seal remains uncertified. Provision and wire a durable independent attestor, or explicitly keep timing uncertified and exclude it from deployment claims.
3. **Timing ledger identity continuity** — **confirmed**: V2 validation checks the pinned key, run/task/payload, sequence, and previous digest but does not require a stable `ledger_id` across the run. Pin the ledger identity or bind it into the run policy and reject a different ledger.
4. **Claim-path/WIP policy drift** — **likely**: the adapter permits dotted claim-path overrides while the CEL template hard-codes top-level `aud`, `iss`, and workload paths; no renderer or test proves that the provider condition matches runtime configuration. Generate both from one frozen policy and fail deployment if they differ.
5. **Incomplete policy commitment** — **confirmed**: `policy_digest` omits the public authority object and `kms_key_version`, although both determine who signs receipts and which KMS key is used. Include those bindings or expose a complete deployment-policy commitment.
6. **Unresolved deployment contract** — **confirmed**: `cloud-run.yaml`, `Containerfile`, metadata, and CEL artifacts still contain `REPLACE_`, `PROJECT_`, `IMAGE_DIGEST`, `VERSION`, and `REVIEWED_` placeholders; the digest values and authority fields would fail `from_env`, and no deployment gate rejects unresolved values. Render and validate one reviewed, digest-pinned manifest before apply.
7. **Runtime IAM and Confidential Space provisioning** — **likely**: the repository supplies only prose IAM guidance and an ordinary Cloud Run manifest; it does not prove the target runtime exposes the pinned Confidential Space metadata-token endpoint or install the exact prefix-scoped bucket/KMS/WIP grants. Verify the target runtime, private objects, key version, WIP condition, and least-privilege service-account bindings before rollout.
8. **Production-boundary regression coverage** — **confirmed**: local tests validate the V2 validator and fake activation separately, but do not exercise a service run with a V2 attestor, ledger identity switching, restart/reconciliation, rendered claim/WIP policy, or final deployment configuration. Add those tests before treating the cloud lock as complete.

</details>

<details>
<summary>Details</summary>

### Locked capabilities and the pre-attestation boundary

The remaining **confirmed** boundary issue is `KMSEd25519Signer.__init__` creating `kms.KeyManagementServiceClient()` when `client` is omitted. `CapabilityFactory` supplies an explicit client in the normal adapter path, but the signer itself does not enforce that boundary, unlike `GCSStore`; make it fail closed without an explicit client so a future caller cannot bypass attestation by constructing the signer directly.

### Claim policy and WIP binding

**Likely drift:** `LockedBootstrapConfig.from_env()` freezes a closed set of claim names but permits each path to be replaced with any non-empty dotted path, while the CEL template independently references top-level `assertion.aud`, `assertion.iss`, and workload claims. A reviewed alternate mapping can therefore be rejected by the provider or trust a different path if the provider condition is not rendered exactly as documented. Freeze one token-derived mapping and mechanically compare the CEL condition with runtime configuration before provisioning.

**Confirmed gap:** `policy_digest` omits the public authority object and `kms_key_version`, despite their determining receipt signer and KMS key. Include them in the commitment.

### Independent timing and terminal seal evidence

**Confirmed:** the default `SignedTimingAttestor` signs V1 records with the same KMS authority used for evaluator receipts and declares `independent = False`. The service sets `timing_certified` only for an independent, separately pinned V2 attestor. V2 validation verifies its Ed25519 signature, public-key digest, expected authority/key, run/task/payload binding, UTC timestamp, sequence, and previous digest; `CapabilityFactory.build()` nevertheless always selects the diagnostic V1 recorder.

**Confirmed gap:** V2 records carry a `ledger_id`, but `_record_timing()` persists only the sequence and record digest and `validate_attestation()` never compares ledger IDs. The previous-digest chain prevents an unlinked record, but permits a signed record from a different ledger identity using the same key. Bind a reviewed ledger ID to the run policy and check every event.

The V4 seal is signed by the configured receipt authority, its commitment is bound into the `run_closed` receipt, and `/result` verifies the persisted seal against state, the authority key, every receipt sequence/hash/signature, the final chain digest/count, and the close receipt. This closes the prior seal-tampering gap; **confirmed** timing remains uncertified until an independent attestor is wired.

### Deployment readiness and exact remaining prerequisites

**Confirmed:** the checked-in artifacts are not a deployable lock. `cloud-run.yaml` contains unresolved project, region, provider, authority, image, KMS-version, runtime/resource digest, and timing values; `Containerfile` still requires an immutable base-image digest; and `P5R0_AUTHORITY_JSON`, `P5R0_EXPECTED_IMAGE_DIGEST`, `P5R0_RUNTIME_DIGEST`, `P5R0_RESOURCE_PROFILE_DIGEST`, and `P5R0_TIMING_PUBLIC_KEY_DIGEST` contain syntactically invalid or placeholder values. The README/IAM guidance refers to `P5R0_IMAGE_DIGEST`, while the parser and manifest use `P5R0_EXPECTED_IMAGE_DIGEST`; standardize the name before rendering.

Before GCP provisioning, the reviewed deployment change must freeze the exact production and base-image digests, runtime/resource commitments, project/zone, Confidential Space issuer and actual claim paths, canonical WIP provider/audience, application audience and runner subject, private bucket and `v3` prefix, KMS Ed25519 key version/public authority, and independent timing ledger authority/key/identity. It must create or verify the private bucket and committed lock/manifest/truth objects, dedicated runtime and runner service accounts, internal Cloud Run ingress, exact WIP attribute condition, prefix-scoped storage grants, and one-key-version KMS grants. It must verify that the selected runtime supplies the pinned Confidential Space metadata endpoint and token contract. A deployment gate must reject every unresolved placeholder and run the rendered configuration through `LockedBootstrapConfig.from_env()` before apply.

### Boundary coverage

The 21 focused tests pass and cover locked startup without client creation, exact image/nonce rejection, closed authority and WIP mismatch, endpoint pinning, expiry relock, run-scoped path attacks, forged timing payloads, KMS signature validation, replay/idempotency behavior, and terminal seal tampering. **Confirmed missing coverage:** no test constructs the production `CapabilityFactory` with a V2 attestor, persists and reloads a V2 chain, rejects a changed ledger ID, or validates rendered Cloud Run/CEL configuration as one unit. Those checks are needed to turn local evidence into a deployment lock.

</details>

<details>
<summary>Files</summary>

- `services/p5_r0_evaluator/confidential_space.py` — locked attestation gate, explicit capability factory, run-scoped storage, and local timing recorder.
- `services/p5_r0_evaluator/timing.py` — signed V2 timing validation and chain checks.
- `services/p5_r0_evaluator/service.py` — authenticated runs, receipts, timing integration, and V4 result seals.
- `services/p5_r0_evaluator/store.py` — generation-checked memory/GCS object stores.
- `services/p5_r0_evaluator/tests/test_confidential_space.py` — attestation, WIP, path, expiry, and timing boundary tests.
- `services/p5_r0_evaluator/tests/test_service.py` — authenticated task/result, replay, observation, and seal tests.
- `services/p5_r0_evaluator/deploy/*` — review-only Cloud Run, image, IAM, metadata, and WIP policy artifacts.
- `services/p5_r0_evaluator/README.md` — protocol and deployment guidance.

Full diff/context: the adapter files are currently untracked in this worktree, so `git diff main` does not include them; the reviewed implementation is under `services/p5_r0_evaluator/`.

</details>
