# RS-065 digest refresh and unsigned request boundary

The digest refresh aligns the repository-only RS-065 KMS lock-signing contract and downstream authority/request references with the current generated unsigned request. The generated request matches `build_diagnostic_artifacts()` exactly, carries request digest `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d`, unsigned-lock digest `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`, and raw file SHA-256 `0e8d1f306446ba4e62d31f3eaab523430b372671772db0593516a702bee5f45`. The request-only boundary remains intact: authority and signature fields are null, `signature_present` and `production_signature_created` are false, and cloud operations are empty; the concrete KMS/provider values in the RS-068 proposal remain explicitly review-only. **Watch for:** **confirmed** `RS-063_EVIDENCE_PACKET.md` still cites the older artifact-index digest `sha256:18cf…272c45`, while the current generated artifact index and canonical RS-063 request use `sha256:04a98…97768`; this does not invalidate the direct RS-065 chain, but the packet should be refreshed before treating all cross-stage digest documentation as consistent.

**Verdict**: NEEDS_CHANGES

## High-level view

The direct RS-065 chain is reproducible and exact: the generated request, nested unsigned lock, KMS contract/test, and downstream authority/request plans agree on the repaired commitments. The adapter describes a future signed-environment operation without invoking the existing signer capability.

The release boundary remains fail-closed: authority binding, KMS key-version binding, signature, approval, and promotion are absent or false, and generated artifacts have no cloud operations. The RS-068 proposal’s concrete public metadata remains review-only rather than created authority.

The requested full service/P5 suite is green at 340 tests. A separate **confirmed** cross-stage evidence mismatch remains in the RS-063 packet because its prose has not followed the current artifact-index refresh.

<details>
<summary>Issues (1)</summary>

1. **Stale RS-063 artifact-index reference** — **confirmed:** `RS-063_EVIDENCE_PACKET.md` records `sha256:18cf4683…`, but the current generated `var/p5-r0-diagnostic-inputs/artifact-index.json` and canonical RS-063 execution request record `sha256:04a98e3e…`; refresh the packet’s artifact-index digest and raw-file commitment, then rerun the local evidence checks.

</details>

<details>
<summary>Details</summary>

### Generated request and exact lock commitment

The generated request at `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json` exactly equals the current `build_diagnostic_artifacts()["lock_signing_request"]` output after canonical parsing. Its canonical request digest is `sha256:922085ca833426751f89610dc2274d10f82efe758ee3b92e9d6c9441db20292d`, and its raw file SHA-256 is `0e8d1f306446ba4e62d31f3eaab523430b372671772db0593516a702bee5f45`. The outer `unsigned_lock_digest` equals the nested lock’s `lock_digest` at `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`; the KMS contract and exact-value test use those same values.

All direct RS-065 downstream bindings checked in this pass agree with those commitments. The RS-067 contract retains them with null `authority_binding_digest` and `signature`; the RS-068 request and generated proposal mark the lock request unchanged; the RS-069 plan binds the same unsigned-lock digest; and the RS-063 canonical execution request binds the current generated artifact-index digest plus the same unsigned-lock digest. No direct RS-065 dependency points at the stale `18cf…` value.

### Unsigned boundary and observed authority metadata

The request’s unsigned lock has `signature: null`, `authority_digest: null`, and `kms_authority_binding_digest: null`. At the outer request level, KMS `key_version` and `authority_binding_digest` are null, `signature_present` is false, `production_signature_created` is false, `non_release` is true, and `cloud_operations` is `[]`. The generated artifact index independently reports `production_outputs_created: false` and no cloud operations.

The KMS adapter validates the exact generated request and only describes `Signer.sign_digest`; its operation descriptor does not call the capability. Its future response validator requires the exact request/lock digests, Confidential Space approval, authority/KMS public-key and key-version agreement, a closed authority binding, and an Ed25519 signature over the exact lock digest while preserving `non_release`. The RS-068 proposal’s concrete authority ID, public key, key version, and provider are observed review metadata, not a created authority: its `authority_binding` and signature remain null, `authority_created` and promotion are false, and signed-environment approval is still required.

### Cross-stage artifact-index documentation drift

This is **confirmed** in `docs/research/engine_substrate/RS-063_EVIDENCE_PACKET.md`. Its bound-artifacts section says the generated artifact index has digest `sha256:18cf46837fe0f91db0b90a47a49bd9a3138574933df16af7ea548d95bc272c45` and raw SHA-256 `3573eb…`, but the current generated artifact index reports `index_digest: sha256:04a98e3e48685228fd68ea757de276fe1c1a7ce347bd027a2756a48595897768`. The canonical RS-063 execution request and its test already use `04a98e…`, so this is stale evidence prose rather than a failure of the RS-065 lock/request chain; it should nevertheless be corrected to avoid two competing dependency records.

### Validation and proposed state

`PYTHONPATH=. python3 -m services.p5_r0_evaluator.deploy.kms_lock_signing validate`, the RS-067 authority-binding validator, and the blocked RS-063 execution-request validator all passed. The requested `PYTHONPATH=. python3 -m pytest services/p5_r0_evaluator/tests tests/test_p5_r0*.py -q` completed with `340 passed in 22.83s`; no KMS, gcloud, GCS, FreeTSA, deployment, VM, supervisor, or task operation was run.

Proposed state is **PASS_REVIEW for the repository-only RS-065 adapter and repaired digest chain**, with production execution still blocked/no-go. The overall digest-refresh package remains **NEEDS_CHANGES** until the stale RS-063 evidence reference is refreshed and revalidated; that documentation fix does not authorize signing, ingestion, promotion, or task execution.

</details>

<details>
<summary>Files</summary>

- `var/p5-r0-diagnostic-inputs/public/lock-signing-request.json` — current generated unsigned request and lock commitments.
- `services/p5_r0_evaluator/deploy/kms_lock_signing.py` — exact-request validator and future signed-response boundary.
- `services/p5_r0_evaluator/deploy/p5-r0-kms-lock-signing-contract.json` — RS-065 request-only contract with repaired digests.
- `services/p5_r0_evaluator/tests/test_kms_lock_signing.py` — exact-value and adversarial RS-065 coverage.
- `services/p5_r0_evaluator/deploy/p5-r0-authority-binding-contract.json` — downstream RS-067 null-authority/signature contract.
- `services/p5_r0_evaluator/deploy/rs-068-authority-binding-request.json` — RS-068 lock-request commitment reference.
- `var/p5-r0-diagnostic-inputs/public/rs-068-authority-binding-proposal.json` — review-only observed authority metadata.
- `services/p5_r0_evaluator/deploy/p5-r0-signed-environment-execution-request.json` — canonical RS-063 generated commitments and blocked execution plan.
- `services/p5_r0_evaluator/deploy/rs-069-iac-change-plan.json` — downstream immutable digest plan.
- `docs/research/engine_substrate/RS-063_EVIDENCE_PACKET.md` — stale artifact-index documentation requiring refresh.
- `docs/research/engine_substrate/RS-065_EVIDENCE_PACKET.md` — RS-065 evidence and repaired request commitments.
- `docs/research/engine_substrate/RS-067_EVIDENCE_PACKET.md` — downstream authority-binding evidence.

Full diff: `git diff main` plus the generated `var/` artifacts and untracked RS-065/RS-067/RS-068/RS-069 materials listed by `git status --short`.

</details>
