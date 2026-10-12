# Hardened IAM executor against REVIEW-053 and the P5 runsheet

The DISPATCH-053 hardening closes most of REVIEW-053: the V2 packet targets a separate GCS-only service account, request validators carry the exact custom role, conditional grant, broad/stale removals, token-creator binding, version preconditions, and rollback digests, and the historical V1 packet is now reloaded and digest-verified. The signed-environment adapter requires an injected, expiring, non-exported credential and delegates cryptographic verification to the reviewed backend. The checked-in approval remains disabled and the read-only validator reports no applied state. **Watch for:** **confirmed** the readiness predicate cannot transition to a credential-ready state without another code/artifact change; **confirmed** bucket visibility can be erased during normalization; exact role metadata and partial-account rollback coverage remain incomplete. **Verdict**: NEEDS_CHANGES

**Disposition: BLOCKED.** The current repository is not safe for an effectful IAM apply. No cloud, IAM, GCS, KMS, or credential mutation was attempted or retried.

## High-level view

The proposal and request boundary now separates the KMS-capable `p5-evaluator` account from `p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com`, and carries the exact conditional GCS grant, `storage.objects.create/get` permissions, WIF token-creator binding, broad/stale removals, and no-public-principal constraint.

Versioned policy/role preconditions, exact target policy, account separation, poststate receipt, reverse rollback, and no-retry ledger behavior are enforced. **Confirmed** bucket posture is not preserved: missing or drifted uniform-bucket/public-access fields can be replaced by the hard-coded approved posture before validation.

Historical V1 and R18R12 repository artifacts are independently reloaded and digest-checked. Credential provenance is structurally bound to packet, provider, image, audience, target, authority, attestation, expiry, and backend verification, but the checked-in credential/approval gates are unresolved and cannot transition to ready as written.

The focused tests cover closed requests, success, poststate failure, rollback failure, tampered history, incomplete requests, and credential verification. **Confirmed** they do not cover bucket posture drift, exact role title/stage, or a newly created account persisting through rollback.

<details>
<summary>Issues (5)</summary>

1. **Credential readiness dead-end — confirmed** — `validate_iam_boundary` requires the checked-in credential artifact to retain `credential_injected=false` and `token_present=false`, while `credential_ready` requires `token_present=true`; it also requires the approval evidence digest to remain `null`. Replace these current-state assertions with a reviewed transition schema, then bind a fresh evidence/approval digest before enabling execution.
2. **Bucket visibility erased by normalization — confirmed** — `normalize_prestate` hard-codes `uniform_bucket_level_access=true` and `public_access_prevention=inherited` instead of validating the observed fields, and does not require a canonical observation to contain `bucket`. Preserve and compare these fields in V2/canonical prestate and poststate validation; add drift tests.
3. **Custom-role poststate is not fully exact — confirmed** — request validation requires title `P5 R0 operation 4 bundle writer` and stage `GA`, but `_role`/`validate_poststate` only require those fields to be strings. Require exact title and stage in poststate and receipt validation, with adversarial tests.
4. **Required external apply evidence is absent — confirmed** — the target account and role are absent, the captured prestate is not a future apply-time capture, credential evidence has no attestation/token, approval is disabled, and no IAM poststate/receipt exists. Capture fresh versioned prestate, provision/reconcile the separate account and role through reviewed IaC, obtain genuine signed-environment evidence, issue a new uniquely bound enabled approval, and only then perform one gated apply.
5. **Account-creation rollback coverage is incomplete — confirmed** — the implementation leaves a newly created account for manual review when exact restoration cannot equal the prestate, but the R18R13 fake backend simply returns the old absent-account state. Add a stateful partial-failure test and prove `rollback_failed_manual_review` plus no retry.

</details>

<details>
<summary>Details</summary>

### Exact IAM policy, role, and account separation

`_desired_requests` and `_validate_requests` carry a closed custom-role request for `projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1`, exactly `storage.objects.create` and `storage.objects.get`, title/stage metadata, and a version/absence precondition. The bucket request adds the GCS-only account under `p5_r0_r18r13_op4_exact_run`, removes the existing KMS-capable account's `roles/storage.objectAdmin` and the stale v3 WIF `roles/storage.objectUser` grant, and disallows public principals. The target-account request replaces policy with exactly one `roles/iam.serviceAccountTokenCreator` grant for the reviewed image-digest WIF principal. The adapter independently rejects incomplete or differently shaped requests.

The packet, definition, credential target, poststate checks, and receipt keep the accounts separate: the new account must have no key material or KMS project role, while the existing account retains its KMS authority and policy. These are repository claims only; the target account, role, and exact grants are absent in the captured prestate.

**Confirmed** the poststate contract is weaker than the request contract for role metadata. `_role` checks only that existing title/stage are strings, and `validate_poststate` checks permissions but not exact title/stage. A backend could return the right permissions with different metadata and still produce a verified poststate. Close this before apply.

### Fresh prestate, poststate, and bucket posture

The executor compares a normalized fresh observation with the approved state and preserves etag/fingerprint or absence preconditions for bucket, existing-account, target-account, and custom-role resources. Poststate checks the exact conditional grant, both named removals, no public principals/direct WIF access, exact target policy, exact permissions, account separation, and existing KMS authority; the receipt records pre/post digests and resource versions.

**Confirmed** `normalize_prestate` is not lossless for bucket security posture. It synthesizes `uniform_bucket_level_access=true` and `public_access_prevention=inherited` regardless of input, and a canonical observation can omit `bucket` because the function never reads it. The V2 conversion reads raw fields but does not reject drift before hard-coded normalization. A backend observation with changed or incomplete bucket posture can therefore compare equal to the approved state and pass prestate/poststate validation. Require the bucket object and exact observed values instead of synthesizing them.

The checked-in V2 prestate is internally digest-valid and records the expected private posture, versioned etags, absent target account/policy, absent role, and existing KMS authority. It is not a fresh apply-time observation after external provisioning changes.

### Signed-environment provenance and historical reload

`ReviewedIAMExecutorAdapter` rejects missing, expired, exported, key-bearing, ambient-ADC, wrong-account, and wrong-source credentials. `validate_credential_binding` additionally requires exact packet, provider, image, STS audience, authority-binding, attestation proof/claims, and backend cryptographic verification; every backend call receives the same opaque injected credential. The repository path performs no cloud SDK, direct gcloud, ADC discovery, key creation, or token export.

**Confirmed** the current readiness implementation cannot be advanced by merely supplying a future credential. It first requires `credential_injected=false` and `evidence.token_present=false`, then requires `evidence.token_present=true` for readiness; it also requires the current approval's signed-environment digest to be `null`. A future evidence artifact and enabled approval therefore require a reviewed validator/packet transition. The eventual evidence must be genuine signed-environment attestation with exact provider/image/audience/authority claims, bounded expiry, a short-lived injected credential, and backend cryptographic verification.

The historical supersession path loads `services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json`, recomputes its self-digest, and requires the recorded V1 schema/digest. The V1 packet remains unchanged and observation-only. R18R12 is also reloaded through its canonical ledger and approval checks, but remains repository-only binding evidence, not external KMS or Confidential Space evidence.

### Rollback, lifecycle, and no-retry boundary

After account creation, role reconciliation, bucket update, and target-policy update, any failure triggers reverse restoration of target policy, bucket policy, and role with current version preconditions. The executor verifies the complete normalized state afterward; ambiguous restore is `rollback_failed_manual_review`, and an existing ledger prevents retry. Automatic deletion of a newly created account is forbidden, so an account that survives a failed later phase must remain a manual-review stop.

**Confirmed** the tests do not model account persistence. Their fake poststate returns the expected absent account even after simulated `ensure_service_account`, proving rollback ordering/digest comparison but not the real partial-account outcome. Add that stateful case before treating rollback coverage as complete.

### Test coverage and current gate

The supplied hardening validation reports 23 focused IAM tests, 414 adjacent P5/service tests, compileall success, and whitespace checks. The focused additions cover closed request forwarding, partial failure, ambiguity/manual review/no retry, historical tamper rejection, credential provenance/cryptographic verification, incomplete requests, and no-credential rejection. Missing adversarial cases are bucket visibility drift/missing bucket, exact role title/stage drift, and account creation persisting through rollback.

Read-only checks performed here were the preparation CLI, which returned `ready_for_executor=false`, `mutations_performed=false`, `applied_state=false`, `cloud_operations=[]`, and `historical_packet_verified=true`, plus independent self-digest recomputation for the V2 packet, V3 approval, prestate, credential evidence, and historical V1 packet. No effectful executor invocation, cloud command, credential operation, or retry was performed.

The exact prerequisites before any effectful apply are: (1) close the bucket-normalization and role-poststate gaps and add stateful/adversarial tests; (2) capture fresh, independently reviewed, versioned prestate for bucket policy, existing-account policy, target-account existence/policy, custom-role existence, and bucket security posture; (3) create or reconcile the separate GCS-only account without keys/KMS roles and the exact role through reviewed IaC; (4) establish the exact conditional grant, broad/stale removals, and WIF token-creator binding; (5) obtain genuine signed-environment attestation/evidence and a bounded short-lived injected credential with exact provider/image/audience/authority claims and backend cryptographic verification; (6) issue a new unique enabled child approval bound to current packet, definitions, fresh prestate, credential evidence, authority/R18R12 evidence, and attempt identity; and (7) after one approved apply, capture authenticated poststate/receipt or verified rollback/manual-review evidence. Until then, effectful IAM apply is **not safe**; the correct disposition is **BLOCKED**, not `PASS_REVIEW` and not `NO_GO`, because no effectful attempt occurred.

</details>

<details>
<summary>File map</summary>

- `services/p5_r0_evaluator/deploy/iam_capability_provisioning.py` — IAM normalization, exact requests/poststate/receipt, signed-environment adapter, rollback, and no-retry executor.
- `services/p5_r0_evaluator/deploy/rs069r18r13_iam_boundary.py` — V2 packet/approval/source validation, historical V1 reload, R18R12 checks, and blocked apply wrapper.
- `services/p5_r0_evaluator/tests/test_rs069r18r13_iam_boundary.py` — R18R13 success, failure, rollback, provenance, historical, and no-credential tests.
- `services/p5_r0_evaluator/tests/test_iam_capability_provisioning.py` — IAM definition, prestate/poststate, apply, rollback, and no-retry tests.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-provisioning-definition-v1.json` — desired IAM, prestate, rollback, poststate, and execution boundary.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-boundary-packet-v2.json` — blocked V2 packet and historical supersession binding.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-approval-v3.json` — disabled single-operation child approval.
- `var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json` — digest-valid read-only IAM prestate with absent target account/role.
- `var/p5-r0-rs069/rs069r18r13-credential-binding-evidence-v1.json` — digest-valid but unresolved credential evidence.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — REVIEW-053/DISPATCH-053 history; IAM remediation and downstream GCS/P5 gates remain blocked.

Full repository comparison: `git diff main`; the hardened IAM files are untracked additions in this dirty checkout, so inspect the listed paths directly as well.

</details>
