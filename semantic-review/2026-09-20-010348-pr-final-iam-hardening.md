# Final IAM hardening against REVIEW-054 and the P5 master runsheet

DISPATCH-054 closes the three repository gaps identified by REVIEW-054: bucket visibility is carried through normalization and checked against the private prestate, custom-role title/stage/permissions are exact in requests, state, poststate, and receipt, and partial account creation is a manual-review stop rather than an automatic deletion or retry. Historical V1 and R18R12 artifacts remain digest-bound and are read without rewrite. **Disposition: BLOCKED.** No effectful IAM, GCS, KMS, credential, or retry invocation is recommended. **Watch for:** **confirmed** the readiness transition can still be self-promoted by a caller-supplied provenance boolean and structurally fabricated evidence; **confirmed** no genuine signed-environment credential, concrete reviewed executor, live IAM poststate, or receipt exists. The full P5 runsheet remains `NO_GO`, with IAM at a blocked pre-apply frontier.

**Verdict**: NEEDS_CHANGES

## High-level view

The IAM boundary now keeps the KMS-capable existing account separate from the GCS-only account and binds the exact conditional writer grant, token-creator target, custom-role metadata, private bucket posture, and broad/stale grant removals. The checked-in packet and approval remain disabled, so this repository state cannot apply.

The REVIEW-054 normalization, role, receipt, and account-creation rollback gaps are closed in the implementation and adversarial tests. The remaining code-level issue is the readiness transition itself: it accepts a caller-controlled `provenance_verified` flag rather than deriving verified state from a cryptographically verified signed-environment object.

**Confirmed** the P5 runsheet still requires real deployment and attestation facts before IAM can be enabled: the reviewed image/WIP/Confidential Space binding, KMS authority observation, exact GCS-only token-creator grant, bounded credential, fresh IAM prestate, concrete executor, and a newly bound child approval are absent. No downstream GCS upload or P5 execution gate can advance from this repository evidence.

<details>
<summary>Issues (3)</summary>

1. **Caller-controlled credential promotion** — **confirmed**: `transition_credential_readiness` accepts `provenance_verified=True` and synthetic evidence that passes shape, digest-format, source, and expiry checks without verifying a signed attestation. Replace the boolean with verifier-produced evidence and derive readiness only after cryptographic verification.
2. **Missing signed-environment IAM capability** — **confirmed**: the checked-in credential evidence is unresolved and bound to the superseded packet, approval is disabled, and no concrete reviewed executor or real STS/attestation credential exists. Supply a fresh redacted signed-environment evidence digest, bounded non-exported short-lived credential, exact provider/image/audience/authority bindings, and a reviewed executor before enabling the child approval.
3. **No live IAM poststate or receipt** — **confirmed**: the target account and custom role are absent in the read-only prestate and no applied poststate/receipt exists. Recapture versioned IAM prestate, issue a fresh uniquely bound approval, perform at most one authorized apply, then require authenticated exact poststate/receipt or verified rollback/manual-review evidence before operation 4.

</details>

<details>
<summary>Details</summary>

### Credential readiness cannot be promoted by local evidence

**Confirmed** the state machine is monotonic once a state is accepted, but monotonicity does not make promotion trustworthy. `transition_credential_readiness` takes `provenance_verified` from its caller and `_validate_verified_credential` accepts a caller-provided mapping containing a syntactically valid evidence digest, `attestation_verified=true`, `token_present=true`, source strings, and bounded expiry. The focused test exercises exactly this path with synthetic evidence and `provenance_verified=True`; no signed-environment signature or external verifier is required by the transition.

The checked-in V2 packet is still safely unresolved: its status is `required_but_not_injected`, its credential artifact has no token or evidence digest and references the superseded V1 packet, and the V3 approval has `enabled=false`, `ready_for_executor=false`, and no signed-environment evidence digest. That blocks the current path, but a future packet/artifact edit could make `validate_iam_boundary` report readiness before the evidence has been cryptographically established. The later `ReviewedIAMExecutorAdapter` verifier is a useful apply-time defense, but it does not make the readiness report or the transition API a trustworthy promotion boundary, especially because `execute_reviewed_iam` accepts an injected protocol implementation.

The prerequisite is a verifier-owned, closed evidence object: verify the real Confidential Space/STS provenance and attestation signature in the reviewed backend, bind its digest to the current V2 packet, provider, image, audience, authority, and target account, and derive `verified` from that result. A caller-supplied boolean, local digest recomputation, fixture, or self-asserted token flag must not be able to advance the state.

### Exact IAM state and rollback semantics

The REVIEW-054 concerns about visibility and role metadata are **confirmed resolved** in the current implementation. `_bucket` preserves the observed uniform-access and public-access-prevention fields; V2 and canonical normalization carry them into the digest-bound state; poststate requires the exact private values and equality with prestate; and the receipt records the same visibility plus exact role title, stage, permissions, and condition title. The stateful account-creation test models creation before a later failure, requires `rollback_failed_manual_review`, and confirms the ledger prevents retry. The definition deliberately forbids automatic deletion of a newly created account when ownership of that partial state is ambiguous.

**Confirmed** these are repository guarantees only. The checked-in prestate still says the GCS-only account and custom role do not exist, so exact IAM poststate, least-privilege policy, and rollback behavior have not been observed against the project.

### Historical artifacts remain immutable inputs

The V2 boundary reloads the superseded V1 packet, recomputes its self-digest, and requires the hard-coded historical digest; it likewise verifies the R18R12 ledger chain, terminal status, approval digest, and no-mutation flags. The packet explicitly records `historical_packet_rewritten=false`, and the V1 packet remains observation-only. No current hardening path writes either historical artifact; any change would fail the current digest checks rather than silently becoming new evidence.

### P5 gate before any effectful IAM invocation

The full `P5_MASTER_RUNSHEET.md` keeps the release decision at `NO_GO` and `RS-069R18R13-IAM` blocked. Before an effectful IAM attempt, the exact remaining prerequisites are: a fresh reviewed candidate image and Confidential Space deployment binding; canonical WIP provider claim mapping/condition and STS audience observation; real signed-environment launcher JWT/TEE/Secure Boot/AMD SEV/debug/workload/image/project/zone/smoke evidence; read-only observation of the evaluator KMS version and public key; a self-custodied `P5R0PublicAuthorityV4` bound to that key/version; an exact STS exchange and token-creator grant for the separate GCS-only account; a fresh least-privilege IAM observation proving broad/public grants are absent or correctly targeted; a verifier-backed, non-exported, bounded short-lived credential; a concrete reviewed executor; and a fresh child approval bound to unchanged packet, authority, request, prestate, and evidence digests. Only after that one gated attempt may the result be an authenticated exact IAM poststate and receipt, or a verified rollback/manual-review stop. No invocation is recommended without this evidence, and no GCS upload, KMS signing, Confidential Space task run, timing record, supervisor evidence, or P5 result may be inferred from local tests or generated artifacts.

</details>

<details>
<summary>File map</summary>

- `services/p5_r0_evaluator/deploy/iam_capability_provisioning.py` — exact IAM state normalization, requests, poststate/receipt checks, injected executor boundary, rollback, and no-retry ledger.
- `services/p5_r0_evaluator/deploy/rs069r18r13_iam_boundary.py` — V2 packet/approval validation, credential readiness transition, historical reload, R18R12 dependency checks, and blocked apply wrapper.
- `services/p5_r0_evaluator/tests/test_iam_capability_provisioning.py` — visibility/role drift, stateful account creation, partial failure, rollback, and no-retry coverage.
- `services/p5_r0_evaluator/tests/test_rs069r18r13_iam_boundary.py` — packet/history checks, signed-environment adapter, credential transition, receipt, rollback, and blocked-boundary coverage.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-boundary-packet-v2.json` — disabled V2 IAM packet with separate GCS-only identity.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-approval-v3.json` — disabled V3 child approval and unresolved external gates.
- `var/p5-r0-rs069/rs069r18r13-credential-binding-evidence-v1.json` — unresolved credential evidence.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — authoritative `NO_GO`/blocked frontier and REVIEW-054/DISPATCH-054 history.

Full repository comparison remains `git diff main`; this review performed no executor, cloud, credential, signing, retry, or runsheet operation.

</details>
