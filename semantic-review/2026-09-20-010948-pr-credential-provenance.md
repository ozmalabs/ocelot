# Verifier-owned credential provenance for R18R13 IAM readiness

This change hardens the R18R13 IAM boundary around a separate GCS-only service account, digest-bound packet and authority dependencies, bounded non-exported credentials, and fail-closed apply/rollback behavior. It reloads the superseded packet and keeps the checked-in IAM approval disabled, so the repository path does not claim an applied IAM state. The central REVIEW-055 requirement is not met: readiness still accepts a caller boolean and a caller-constructed mapping rather than verifier-owned signed-environment evidence. **Watch for:** **confirmed** caller-controlled promotion remains possible; **confirmed** the readiness transition does not bind image or audience; **confirmed** the tests positively exercise synthetic evidence instead of rejecting it; **confirmed** the full P5 path remains blocked on real signed-environment, IAM, KMS, GCS, timing, supervisor, and result-seal evidence.

**Verdict**: NEEDS_CHANGES

## High-level view

The IAM boundary preserves the separate GCS-only identity and reviewed packet/approval/authority digests, but **confirmed** readiness can still be promoted before a signed-environment verifier establishes those facts.

The startup attestation path has an opaque adapter-created binding and checks image, provider, policy, claims, and expiry. **confirmed** that binding is not the credential-readiness source: `transition_credential_readiness` still receives `provenance_verified` and a plain mapping, while its expected fields omit image and audience.

Historical supersession and no-retry controls are retained: the old packet is reloaded and digest-checked, `historical_packet_rewritten` must be false, and an existing IAM ledger prevents another apply attempt. **Confirmed**, these controls do not close the missing verifier-owned credential gate.

The master runsheet therefore remains at `NO_GO` with `RS-069R18R13-IAM` blocked. **Confirmed**, real signed-environment and downstream P5 evidence must be obtained before any IAM or later operation can be promoted.

<details>
<summary>Issues (4)</summary>

1. **Caller-promotable credential readiness** — **confirmed**: `transition_credential_readiness` accepts `provenance_verified=True` and a caller-supplied mapping, so synthetic evidence can advance readiness. Replace both inputs with an adapter/verifier-produced sealed evidence object and derive the boolean internally.
2. **Incomplete current-environment binding at readiness** — **confirmed**: the transition checks packet, provider, principal/resource, authority digest, account, and token expiry, but not image digest or audience and does not cryptographically verify the signed-environment evidence. Bind all required fields to the current packet and verifier output before promotion.
3. **Adversarial coverage validates the unsafe seam** — **confirmed**: the readiness test expects a hand-built mapping plus `provenance_verified=True` to return `verified`, and no test asserts that forged booleans or synthetic mappings are rejected. Replace the positive seam with a fake verifier/adapter fixture and add rejection tests for every binding and expiry dimension.
4. **External P5 gates are still absent** — **confirmed**: the runsheet and production handoff still lack real signed-environment credential/attestation, fresh least-privilege IAM state, exact child approval, KMS signature, GCS receipt, timing, supervisor/receipt-chain, and result-seal evidence. Supply each exact prerequisite in sequence; do not enable IAM or downstream operations from repository artifacts alone.

</details>

<details>
<summary>Details</summary>

### Caller-controlled readiness still crosses the IAM gate

**confirmed** — `services/p5_r0_evaluator/deploy/rs069r18r13_iam_boundary.py` defines `transition_credential_readiness(..., provenance_verified: bool, credential: Mapping[str, Any] | None, ...)`. The verified transition requires the caller’s boolean, then validates only the shape and values of the caller’s mapping. `_validate_verified_credential` accepts `attestation_verified=True`, `token_present=True`, a formatted digest, the expected source string, and bounded timestamps; none proves that a signed-environment verifier created or verified the evidence.

The fixture in `services/p5_r0_evaluator/tests/test_rs069r18r13_iam_boundary.py` demonstrates the bypass: `_credential_transition_fixture()` constructs a dictionary locally, and `test_credential_readiness_is_explicit_monotonic_and_source_bound()` passes it with `provenance_verified=True` and asserts `"verified"`. A caller can promote readiness without a `ConfidentialSpaceAdapter`, adapter-created `VerifiedAttestationBinding`, credential verifier, or real signed token.

`ReviewedIAMExecutorAdapter` has stronger apply-time checks, including a backend callback and exact credential metadata, but it runs after readiness has been reported. It does not make the transition API a trustworthy promotion boundary, and `execute_reviewed_iam` still receives an injected executor protocol.

### Packet identity is not enough for the signed-environment credential

**confirmed** — the transition’s `expected_credential` contains packet digest, provider, principal, target resource, authority-binding digest, and service account. `_validate_verified_credential` does not require image digest or audience in the credential evidence and does not consume a sealed verifier result. The separate `InjectedSignedEnvironmentCredential` and `ReviewedIAMExecutorAdapter.validate_credential_binding()` check `WIF_IMAGE_DIGEST`, `STS_AUDIENCE`, attestation claims, authority digest, and backend verification, but that object is not the source used by `transition_credential_readiness`.

This creates two inconsistent promotion paths: synthetic readiness evidence can pass without image/audience binding, while the eventual adapter handles a different credential representation. The fix needs one verifier-owned evidence type bound to the current packet, provider, image, audience, authority, target account, and effective expiry; readiness should be derived from that type rather than caller metadata.

### Historical artifacts and lifecycle boundaries remain protected

The R18R13 validator reloads the superseded packet from its repository-relative path, checks its self-digest against `OLD_PACKET_DIGEST`, requires `historical_packet_rewritten` to be false, and keeps `later_operations_enabled` false. The apply path refuses an existing operation ledger before invoking the executor, while the packet and approval remain disabled and record no cloud operations. **Confirmed** — the current boundary preserves historical packet identity and no-retry semantics; no code path in this review rewrites those artifacts. This does not substitute for verifier-owned credential provenance.

### The tests do not cover the required adversarial boundary

**confirmed** — tests cover expired/exported adapter credentials, wrong provider in the synthetic transition fixture, overlong short-lived expiry, adapter-owned startup evidence, and some capability-binding drift. They do not test that `provenance_verified=True` is ignored or rejected, that a plain dict cannot be promoted, or that readiness requires a sealed object whose verifier-derived fields match the current packet, image, audience, authority, and account. The positive synthetic fixture is directly contrary to REVIEW-055.

Required coverage is a verifier-owned fake Confidential Space/credential adapter path plus negative cases for forged booleans, synthetic mappings, stale packet/evidence digests, wrong provider, image, audience, authority, or account, expired attestation, expired source token, expired capability token, and mismatched source/capability expiry. Tests must also assert that no executor call is possible when any check fails.

### Exact remaining external prerequisites for the P5 path

**confirmed** — `P5_MASTER_RUNSHEET.md` remains `NO_GO`, with `RS-069R18R13-IAM` blocked after REVIEW-055. Before IAM can be enabled, the external path must provide: a fresh reviewed candidate image digest and Confidential Space deployment binding; a fresh canonical WIP provider, claim mapping/condition, and STS audience observation; the existing evaluator KMS key version and Ed25519 public-key observation; self-custodied `P5R0PublicAuthorityV4` metadata bound to that exact key/version; a real launcher JWT containing nonce, `iat`, `exp`, issuer, TEE, Secure Boot, AMD SEV, debug, workload, image, project, zone, and smoke claims; an STS exchange and IAM-Credentials token-creator grant for the exact GCS-only capability account; a fresh least-privilege IAM observation proving the narrow writer, absence of broad grants, verified token creator, and absence of public principals; and a new child approval bound to the unchanged current packet and authority digests.

After IAM preconditions are verified, the remaining sequence requires an exact destination project/bucket/prefix/run binding and authenticated remote GCS receipt, a real KMS signature over the exact generated lock, signed Confidential Space activation bound to image/WIP/IAM/KMS/GCS claims, a verified FreeTSA timing record before seed derivation, authenticated supervisor/resource evidence, signed append-only receipts with rollback/expiry events, and a persisted verified result seal. The handoff also records unresolved upstream P0-A/P0-E1/P0-E2/P1–P4 release gates; there is no external task provider because the task set is project-generated. None of these facts may be replaced by local fixtures, booleans, normal service readiness, or repository digests.

</details>

<details>
<summary>Files</summary>

- `services/p5_r0_evaluator/deploy/rs069r18r13_iam_boundary.py` — R18R13 packet validation and credential-readiness transition.
- `services/p5_r0_evaluator/deploy/iam_capability_provisioning.py` — injected credential metadata and reviewed executor adapter.
- `services/p5_r0_evaluator/deploy/attestation_binding.py` — adapter-sealed startup attestation binding.
- `services/p5_r0_evaluator/tests/test_rs069r18r13_iam_boundary.py` — IAM readiness, executor, rollback, and synthetic-evidence tests.
- `services/p5_r0_evaluator/tests/test_signed_environment_process.py` — startup attestation, capability, and signed-environment boundary tests.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — REVIEW-055, DISPATCH-055, and current P5 state.
- `docs/research/engine_substrate/P5_PRODUCTION_INPUT_HANDOFF.md` — exact signed-execution input/evidence prerequisites.

Full worktree diff and untracked review-scope files should be inspected with `git diff main` and the file list above.

</details>
