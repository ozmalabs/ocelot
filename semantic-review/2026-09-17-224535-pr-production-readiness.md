# P5 production-readiness plumbing with independent timing bridge

The change adds a fail-closed Confidential Space bootstrap refinement, separates caller OIDC identity from attested-VM identity, adds explicit evaluator service-account impersonation, and introduces an RFC 3161-backed timing-bridge seam with a durable GCS ledger. The P5 HTTP service still schedules only primary arms and seals completed runs as `impasse` with `native_verified: false`, so timing evidence is not converted into a P5 GO. The deployment and preregistration text keeps real caller subjects, bridge custody, held-out truth, and production authority external. **Watch for:** **confirmed** smoke mode is not bound in the checked-in WIP CEL template; **confirmed** bridge evidence can be accepted with a previous digest that differs from the durable ledger head; **confirmed** no normal HTTP task client or thought-manifold production adapter was added.

**Verdict**: NEEDS_CHANGES

## High-level view

The Confidential Space path separates caller identity from attested-VM identity and requires post-attestation capability-account impersonation. **Confirmed:** the handwritten WIP policy template is weaker than the runtime-generated policy because it omits the smoke claim and condition.

The timing path separates RFC 3161 proof, bridge-owned Ed25519 V3 records, and evaluator verification, with generation-checked ledger storage. **Confirmed:** the bridge does not require the RFC evidence’s previous digest to equal the durable ledger head, allowing a malformed adapter to poison the evidence chain.

**Confirmed:** the repository still has no normal task client or thought-manifold production adapter. The final disposition remains an explicit impasse rather than a production GO, so these are incomplete execution surfaces rather than hidden success claims.

<details>
<summary>Issues (4)</summary>

1. **Smoke policy binding** — The checked-in WIP CEL template omits the smoke mapping and condition; make it match the runtime-generated policy and verify parity in deployment preflight.
2. **RFC evidence chain continuity** — The bridge accepts RFC evidence chained to a previous digest different from the durable ledger head; bind validation and proof verification to the ledger head and test the mismatch.
3. **Normal task client** — No client executes the canonical P5 HTTP protocol with injected identity, envelope verification, retry/idempotency preservation, and impasse handling; add that seam or keep the milestone explicitly at service-plumbing status.
4. **Thought-manifold production contract** — No native state machine, closed manifold schemas, custody bindings, or P5 adapter exists; complete the native Stage A/B work before describing blocks 348–351 as production capability evidence.

</details>

<details>
<summary>Details</summary>

## Confidential Space identity separation and smoke-policy binding

The new `P5R0_ATTESTATION_SUBJECT_PREFIX` constrains the Confidential Space JWT subject to the attested Compute VM while `P5R0_AUDIENCE` and `P5R0_ALLOWED_SUBJECTS` remain the application caller identity. Capability construction uses a verified federated token to impersonate the committed evaluator account instead of passing raw WIF credentials to GCS/KMS. The real audience, caller subject, bridge identity, and authority remain placeholders or external inputs, consistent with the preregistration’s no-release boundary.

**Confirmed concern:** `LockedBootstrapConfig` and the generated deployment CEL include `P5R0_CONFIDENTIAL_SPACE_SMOKE` in the WIP condition, but the checked-in `services/p5_r0_evaluator/deploy/wip-provider-policy.cel.tmpl` has neither a smoke mapping nor a smoke equality condition. A deployment rendered or reviewed from that template can issue the federated capability token without enforcing the image’s diagnostic-versus-normal mode, while runtime and policy digests claim that smoke is bound. Make the template losslessly match `_wip_policy_contract`, including mapping and condition, and add a preflight test comparing template/rendered policy fields before accepting deployment artifacts.

## RFC 3161 evidence chain versus the durable bridge ledger

The bridge keeps raw RFC response proof internal, verifies the pinned TSA response, signs a separate V3 record with a bridge key, and persists request/record digests under a generation-conditional per-run ledger. The evaluator client checks the proof and V3 chain before accepting timing evidence, so a normal caller cannot submit its own timing claim.

**Confirmed concern:** in `TimingBridgeService.record`, `_validate_evidence` validates the RFC evidence with `previous_digest=evidence.get("previous_digest")` and `last_sequence=sequence - 1`, and `verify_proof` receives that same evidence-supplied previous digest. Neither check compares the evidence to `head.previous_digest` from the durable ledger. A compatible or malformed adapter can return sequence 2 with an arbitrary previous digest; the service then signs a V3 record chained to the ledger head but binds it to RFC evidence chained elsewhere, and appends it to the ledger. The client rejects the proof/record pair, but the bridge has already advanced and poisoned its durable chain. Require the evidence previous digest to equal `head.previous_digest`, pass the ledger head into proof verification, and add a mismatched-adapter test.

## Normal P5 task path remains clientless

The service’s `_schedule` creates only `cold_reset`, `frozen_transfer`, and `warm_adaptive` primary arms, and close always records the missing native-closure/control/contrast evidence. **Confirmed gap:** there is no repository HTTP client that obtains an injected caller token, preserves exact request bytes across retries, verifies task envelopes, executes only an authorized worker, submits results, and polls an impasse seal.

The canonical production-gap findings and current source contain no normal P5 task-client module or client tests. Implement the dependency-free client seam with external token/authority configuration and retry/idempotency rules, or explicitly keep this milestone classified as service plumbing rather than “normal path executable.” The client must surface `impasse` as a result and must not synthesize missing controls, native closure, held-out truth, or a GO.

## Thought-manifold production boundary remains unimplemented

The thought-manifold plan explicitly says there is no production adapter, canonical serializer, task-envelope or lock binding, durable manifold store, or HTTP integration, and requires native ownership of trajectory iteration, workspace selection, recurrence, persistence, mint admission, and rollback before P5 integration. The changed repository adds no `P5ThoughtManifoldRequestV1`, segment, mint, native state machine, or adapter, so the Python research paths remain outside the P5 contract.

**Confirmed gap:** the requested production-readiness work does not advance this plan beyond documentation. Complete the native contract/state machine and Stage A/B replay controls first, then bind public/result-visible manifold commitments into the evaluator lock, task, result, private store, receipt, rollback, and preregistration surfaces. Until then, retain planning-only status and do not describe local blocks 348–351 results as P5 capability evidence.

## Validation and claim boundary

The targeted bridge/RFC3161 suite passed 69 tests, and the Confidential Space/deployment/service suite passed 73 tests. **Confirmed not tested:** smoke-policy parity between the checked-in template and generated CEL, the malformed previous-digest case above, a restart-safe normal client, and manifold schema/ownership controls. The preregistration amendment and service seal explicitly state that no release, adoption, P5 claim, or general-intelligence claim is being made; the remaining issue is missing production follow-up rather than a false GO.

</details>

<details>
<summary>Files changed</summary>

- `services/p5_r0_evaluator/confidential_space.py` — separates attested VM identity from caller identity and constructs post-attestation capabilities.
- `services/p5_r0_evaluator/timing_bridge.py` — bounded HTTPS client and evaluator-side RFC 3161/V3 verification.
- `services/p5_r0_evaluator/timing_bridge_service.py` — bridge evidence conversion, signing, and ledger sequencing.
- `services/p5_r0_evaluator/timing_bridge_production.py` — GCS durable ledger, KMS signer, and production assembly.
- `services/p5_r0_evaluator/rfc3161.py` — pinned TSA proof construction and verification.
- `services/p5_r0_evaluator/deploy/wip-provider-policy.cel.tmpl` — reviewable WIP mapping/condition template.
- `evaluation/p5_r0/PREREGISTRATION.local.md` — local-only external deployment status amendment.
- `docs/research/psychology_affect/THOUGHT_MANIFOLD_PRODUCTION_PLAN.md` — planning-only manifold contract and rollout boundary.

Full diff: `git diff main`

</details>
