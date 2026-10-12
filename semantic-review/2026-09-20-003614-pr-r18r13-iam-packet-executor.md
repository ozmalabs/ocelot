# IAM packet and reviewed executor remediation

The DISPATCH-052 remediation separates the GCS capability from the existing KMS-capable `p5-evaluator` account, preserves the old packet as a superseded observation, and adds a blocked V2 packet, child approval, and injected signed-environment executor boundary. The packet, approval, definitions, prestate, credential evidence, and R18R12 dependency artifacts are internally digest-valid, and the read-only validator correctly reports `ready_for_executor=false` with no applied state. The master runsheet and APPROVAL-012 still prohibit IAM/GCS mutation, credential export, KMS calls, and downstream progression until the missing external and reviewed-executor gates are complete. **Review state: BLOCKED** — no apply was attempted.

Watch for: **confirmed** the new `execute_reviewed_iam` path does not enforce the exact IAM conditions, removals, full policy versions, or approved credential-evidence digest at the apply boundary; **confirmed** the checked-in credential evidence has no attestation/token and the child approval is disabled; **confirmed** the historical supersession check records the old digest but does not independently reload and verify the old packet. **Verdict**: NEEDS_CHANGES

## High-level view

The identity correction is coherent: the V2 packet and desired definitions consistently target `p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com`, while retaining `p5-evaluator@...` as the existing KMS authority and requiring removal of its broad bucket grant. The old packet remains present and digest-valid in the current checkout, but preservation is not yet an independently enforced evidence gate.

The declared IAM state is least privilege as a proposal: the custom role contains only `storage.objects.create` and `storage.objects.get`, the bucket grant is prefix-conditional, the WIF principal receives token creation only on the GCS-only account, and the broad/stale grants are removed. The checked-in prestate has versioned existing policies and absent target account/role, but the new R18R13 runtime wrapper reduces that state to a bare digest before mutation and forwards incomplete policy requests.

The execution boundary remains safely closed today because the packet says the credential is not injected and the approval is disabled. It is not yet safe to enable: the adapter accepts any well-formed short-lived credential metadata rather than one bound to the approved signed-environment evidence, and the new wrapper has no successful apply/rollback test proving that the exact packet contract reaches the backend.

<details>
<summary>Issues (6)</summary>

1. **Incomplete exact IAM request boundary** — **confirmed** the new wrapper sends only partial role, bucket, and target-policy requests; it does not carry the exact condition expression, stale/broad removals, WIF principal, or complete role metadata to the backend. Route this path through the fully validated request builder or add equivalent immutable request and poststate enforcement before enabling the child approval.
2. **Prestate/version binding is digest-only at apply** — **confirmed** `execute_reviewed_iam` accepts a backend response containing only the approved state digest and does not compare the full normalized state or each etag/fingerprint. Require full fresh-state equality, including target-account/role absence and policy versions, immediately before mutation.
3. **Credential evidence is not bound to approval** — **confirmed** `ReviewedIAMExecutorAdapter` accepts an arbitrary valid-looking evidence digest and does not match it to the packet/approval’s signed-environment evidence or verify attestation claims. Bind the injected credential to the reviewed evidence digest, target account, provider/image identity, and bounded expiry.
4. **Historical supersession is asserted, not verified** — **confirmed** the packet records the old path/digest and `historical_packet_rewritten=false`, but `validate_iam_boundary` never reloads or recomputes the prior packet. Independently verify the prior artifact and preserve that verification in the remediation evidence before treating historical preservation as closed.
5. **New apply path lacks behavioral coverage** — **confirmed** the R18R13-specific tests cover blocked execution and adapter forwarding, but do not execute a successful `execute_reviewed_iam` flow, inspect exact mutation requests, prove full prestate rejection, or prove rollback/no-retry behavior on this path. Add those tests using a fake reviewed backend before enabling execution.
6. **Stale R18R12 prestate annotation** — **confirmed** the prestate says the R18R12 approval source is unavailable/non-canonical even though the current validator verifies that artifact and its digest. Refresh the evidence annotation or record the reason for the historical discrepancy so the packet has one unambiguous dependency status.

</details>

<details>
<summary>Details</summary>

### Separate GCS-only identity and historical packet preservation

The V2 packet consistently binds the operation to `p5-r0-gcs-only@ocelot-proof.iam.gserviceaccount.com` and `projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1`. Its prestate records the existing `p5-evaluator` account as KMS-capable and still holding the broad `roles/storage.objectAdmin` bucket grant; the desired state moves operation-4 access to the separate account rather than reusing a credential capable of KMS signing. This addresses the prior shared-account identity problem.

**Confirmed** the current old packet at `services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json` recomputes to `sha256:a8c313f6e5b775b4ba48a8e8ff4cc5e2561c560930c4e89ec2e9666fb509c447`, and the V2 packet records that exact digest with `historical_packet_rewritten=false`. **Confirmed** the validator checks only those fields; it does not load the recorded prior path or recompute its digest. The remediation therefore demonstrates current-file consistency, not an independently enforced no-rewrite proof. The action is to add a prior-artifact existence/content digest check and retain its result without rewriting the old packet or any prior ledger.

### Exact IAM permissions, conditions, removals, and apply boundary

The reviewed definition is precise as a static artifact. It requires the custom role `projects/ocelot-proof/roles/p5R0Operation4BundleWriterV1` to contain exactly `storage.objects.create` and `storage.objects.get`; the bucket grant targets the GCS-only service account under `p5_r0_r18r13_op4_exact_run` and the exact `rs069r18r13-op4-04a98e3e/` object prefix; the target-account policy contains only `roles/iam.serviceAccountTokenCreator` for the reviewed image-digest WIF principal; and the bucket policy removes the shared account’s `roles/storage.objectAdmin` plus the stale `v3/` WIF `roles/storage.objectUser` binding. Public principals and direct WIF bucket access are forbidden.

**Confirmed** the new `execute_reviewed_iam` path does not use the definition’s full request construction. It calls `apply_custom_role` with a resource, two permissions, and a prestate digest, but omits role title/stage and version. It calls `update_bucket_policy` with only bucket, service-account, condition title, and prestate digest, omitting the condition expression, role, and both removals. It calls `update_target_account_policy` with only the target account and prestate digest, omitting the exact WIF principal and token-creator role. `ReviewedIAMExecutorAdapter` validates only resource/bucket/account identity before forwarding these requests. A backend can therefore be marked `reviewed` and receive insufficiently constrained requests without the runtime proving the exact IAM change described by the packet.

The older `execute_provisioning` implementation does construct and validate the complete requests and exact poststate, but the new R18R13 invocation documented by the remediation is `execute_reviewed_iam(executor=ReviewedIAMExecutorAdapter(...))`, not that older path. The safe repair is to make the R18R13 path consume the same immutable definition/request/poststate validators, or to duplicate their protections in the new wrapper and test every exact binding before an enabled child approval is issued.

### Fresh prestate, dependency digests, and credential-source restrictions

The current prestate artifact is canonical at `var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json`, with artifact digest `sha256:03c83325fd531f0a2db39f0d54d02b10ae7cfa96577ab3cc93046602f109b946` and state digest `sha256:a7580109437962f92903ff8d03f03a3f3de386b1da0f51e2cb73aff2518dc692`. It records versioned bucket and existing-account policy etags/fingerprints, absent target account/policy, and absent custom role. The V2 packet binds those values, and the R18R12 ledger chain is canonical with verified event `sha256:bbb534870778e46c38c6e0fc03dbc36f47f5f78c6127b12ef2e8557877f0a727` and head `sha256:30a59807d8dbf7aa2529d4efab406b4dcd5e87597442be71045827c816833329`.

**Confirmed** the new wrapper’s pre-mutation check is only `observed.get("state_digest") == PRESTATE_STATE_DIGEST`; it does not call the existing full normalization/equality validator and does not verify the captured policy versions or account/role fields. A backend returning the approved digest with stale or incomplete policy state can pass the gate. The action is to compare the complete fresh observation with the approved normalized state and reject any missing, ambiguous, or changed etag/fingerprint before calling the first mutator.

**Confirmed** the credential evidence artifact at `var/p5-r0-rs069/rs069r18r13-credential-binding-evidence-v1.json` is intentionally unresolved, with digest `sha256:725608ffadaadc94bbcb0ff9fc640d14350f914c5508530969a584df65fedeef`, `credential_injected=false`, `token_present=false`, and no signed-environment evidence digest. The adapter correctly rejects ADC, key material, export, wrong account, expired credentials, and unreviewed/direct-gcloud backends. **Confirmed** it still accepts any syntactically valid `sha256:` evidence digest supplied by a caller and does not compare it with the packet or child approval. The future credential must be an externally genuine, short-lived signed-environment token for the GCS-only account, and the adapter must require equality with the newly reviewed evidence digest plus the exact provider/image/authority bindings.

The R18R12 dependency is correctly represented as `verified_repository_binding_review_only`, with no KMS signature, no attestation assertion, and no downstream enablement. **Confirmed** the prestate’s unresolved text still says the R18R12 approval source is unavailable/non-canonical even though the current validator successfully loads and verifies `services/p5_r0_evaluator/deploy/rs-069r18r12-operation-3-approval.json` at digest `sha256:cfa0b7cc40f288282fdb432538460fc65cc4b0c8d3d247c73786fd4fa5cc9dd0`. Refresh or explicitly classify that stale unresolved note so the evidence packet does not contradict the dependency validator. The repository-only R18R12 status is not an external KMS or attestation approval and cannot be promoted into one.

### Approval, rollback, and lifecycle

The child approval at `services/p5_r0_evaluator/deploy/rs069r18r13-iam-approval-v3.json` is canonical at `sha256:4314b6699bd5f56135e8d5d2f48daed5ee4254275eaf7376db14bf69a013b682`; it names APPROVAL-012, DISPATCH-052, the GCS-only account, and the V2 packet digest `sha256:a9b975dc9a66ec5bc12a9c3dd8c825f494ddbe76b4b3e51578b7f2b367b2b546`, but deliberately sets `enabled=false` and `ready_for_executor=false`. The read-only command returned `mutations_performed=false`, `applied_state=false`, and `later_operations_enabled=false`; no IAM ledger was created by this review.

The declared rollback order is target-account policy, bucket policy, then custom role, with exact prestate re-observation and `manual_review_no_retry` for ambiguity. The adapter forwards rollback calls with the correct target identities, and the legacy executor tests demonstrate reverse-order rollback and populated-ledger retry rejection. **Confirmed** no R18R13 test exercises rollback through `execute_reviewed_iam`, and the new wrapper’s rollback verification again trusts only a returned state digest. A future post-mutation failure must leave a durable failed-closed ledger, verify the complete prestate including whether the newly created service account remains, and stop for manual review if account creation or any rollback step is ambiguous; it must never silently retry or claim full restoration from a digest-only response.

### Tests and remaining gates

The repository-only checks run for this review were:

- `PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.rs069r18r13_iam_boundary` — passed read-only; `ready_for_executor=false`, `mutations_performed=false`, `applied_state=false`.
- `PYTHONPATH=. python3 -m pytest -q services/p5_r0_evaluator/tests/test_rs069r18r13_iam_boundary.py services/p5_r0_evaluator/tests/test_iam_capability_provisioning.py` — `17 passed`.
- `PYTHONPATH=. python3 -m compileall -q services/p5_r0_evaluator` — passed.
- `git diff --check` — passed.
- Independent canonical digest recomputation — passed for the V2 packet, V3 approval, IAM and GCS definitions, prestate, credential evidence, R18R12 binding/approval, and old packet.

**Confirmed not tested on the new path:** a successful `execute_reviewed_iam` invocation, exact request payloads for permissions/conditions/removals/token creator, full versioned-prestate drift rejection, credential-evidence digest mismatch, poststate exactness, rollback restoration, and no-retry after a populated R18R13 ledger. The 17 passing tests establish the blocked gate and adapter forwarding shape, not safe effectful IAM execution.

Remaining prerequisites are: create or reconcile the separate GCS-only account and exact custom role through reviewed IaC without key material; apply and verify the conditional grant, exact token-creator binding, and broad/stale removals; capture fresh versioned target-account/role/policy preconditions; obtain genuine signed-environment attestation and inject only its bounded token; repair the executor contract and add success/rollback tests; issue a newly enabled child approval bound to all fresh digests; then capture a verified IAM poststate and receipt. Until all are complete, the correct disposition is **BLOCKED**, not `PASS_REVIEW` and not `NO_GO` (because no effectful attempt occurred).

</details>

<details>
<summary>File map</summary>

- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-boundary-packet-v2.json` — blocked V2 packet with separate GCS-only identity, desired IAM, dependencies, and supersession record.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-approval-v3.json` — disabled APPROVAL-012 child approval bound to the packet and current evidence.
- `services/p5_r0_evaluator/deploy/rs069r18r13_iam_boundary.py` — packet/dependency validator and blocked reviewed-execution wrapper.
- `services/p5_r0_evaluator/deploy/iam_capability_provisioning.py` — canonical IAM validators, injected credential type, and backend adapter.
- `services/p5_r0_evaluator/deploy/rs069r18r13-iam-provisioning-definition-v1.json` — exact role, condition, removal, prestate, rollback, and poststate definition.
- `services/p5_r0_evaluator/deploy/gcs-capability-definition.json` — GCS capability and credential-source definition.
- `services/p5_r0_evaluator/deploy/rs069r18r13-gcs-boundary-packet-v1.json` — preserved superseded shared-account packet.
- `services/p5_r0_evaluator/deploy/rs-069r18r12-binding-review.json` and `rs-069r18r12-operation-3-approval.json` — repository-only R18R12 dependency artifacts.
- `var/p5-r0-rs069/rs069r18r13-iam-prestate-v2.json` — read-only versioned IAM prestate.
- `var/p5-r0-rs069/rs069r18r13-credential-binding-evidence-v1.json` — unresolved credential evidence.
- `var/p5-r0-rs069/operation-3-r18r12-ledger.jsonl` — canonical four-event R18R12 dependency ledger.
- `services/p5_r0_evaluator/tests/test_rs069r18r13_iam_boundary.py` and `test_iam_capability_provisioning.py` — focused blocked-boundary, validator, adapter, and legacy executor tests.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — governing P5 state and APPROVAL-012/DISPATCH-052 constraints.

Full repository diff: `git diff main` (the IAM remediation files are untracked additions in this dirty checkout, so inspect the listed paths directly in addition to the diff).

</details>
