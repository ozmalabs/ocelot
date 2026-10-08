# Conditional MVP plan for a self-custodied attested diagnostic

The corrected DISPATCH-062 documents resolve all three REVIEW-063 corrections: pre-run lock signing is conditional, Track A selects one explicit task/control contract, and mandatory pre-run input delivery is separated from optional post-sign GCS publication. The plan also preserves the requested attestation, timing-before-seed, native/resource, supervisor, receipt, and self-custody boundaries without treating P5-E1/E2 or Track B hardening as Track A evidence. Two residual plan-level gaps remain against the normative P5 requirements: the mandatory persisted verified result seal is not explicit, and the ordering of workload rehydration versus post-attestation capability activation is ambiguous when GCS is the delivery boundary. **Watch for:** **confirmed** the final KMS signature and receipt chain are mandatory, but the result-seal persistence gate must be added; **likely** the input sequence needs to distinguish pre-launch package provisioning from post-attestation workload consumption.

**Verdict**: NEEDS_CHANGES

## High-level view

The signing branch is modeled as either a real KMS signature over the exact immutable lock before execution or no pre-run lock signature, with the final KMS signature carrying the complete lock and input binding in the latter case. Final-result signing remains mandatory in both branches, and GCS cannot promote an unsigned or merely uploaded artifact.

The MVP is bounded to one canonical case, one `cold_reset` task invocation, and one `illegal_action` protocol control identified in the immutable lock. The remaining catalog, broader controls, contrasts, and aggregate scoring are explicitly omitted, so the plan does not silently inherit the full P5 matrix.

The durable input boundary is mandatory before task issue, while post-sign GCS publication is optional transport. The documents need one tighter ordering statement so that a GCS-backed workload reads and freshly rehydrates inputs only after attestation has activated the exact capability, then obtains timing before any time-seeded task input.

Timing-first seed derivation, authenticated supervisor/resource evidence, OOM/deadline cleanup, canonical receipts, self-custody, and P5-E1/E2 separation remain required or explicit. The final result path still needs an explicit persisted verified result seal, not only a KMS signature and optional publication.

<details>
<summary>Issues (2)</summary>

1. **Persisted result-seal gate** — **confirmed** the plan requires a real KMS signature over the final result but does not make creation, verification, persistence, and final binding of the verified result seal/digest a Track A acceptance gate. Add that mandatory gate; keep GCS publication optional and after signing.
2. **Attestation-before-rehydration ordering** — **likely** the required execution order says to deliver and rehydrate before attestation while also forbidding GCS capability construction until after attestation. Split pre-launch package provisioning from signed-workload read/verification/rehydration, and require the latter after attestation but before timing and task issue.

</details>

<details>
<summary>Details</summary>

### Conditional lock signing and the missing result seal

The plan makes pre-run lock signing optional, requires real KMS signing of the exact immutable lock if that branch is selected, and requires the final KMS signature in either branch. The no-lock-signature branch depends on the final signature binding the immutable lock representation/digest and every generated, delivered, rehydrated, and selected-contract input; this is stated consistently in the blocker plan and handoff.

The **confirmed** gap is separate from lock signing. P5 requires a persisted verified result-seal digest in public evidence and requires a missing persisted result seal to yield an impasse (`P5_ATTESTED_RESULT_REQUIREMENTS.md`, REQ-EVID-004 and REQ-FAIL-001); its no-partial-GO rule also includes that seal. The corrected documents mention seal paths and rollback/impasse sealing, but their mandatory Track A matrices stop at the KMS-signed final result and make only GCS persistence optional. Add an explicit A6 requirement to produce, verify, persist, and bind the result seal/digest before final signing, and state that optional post-sign GCS publication carries the already sealed-and-signed result rather than supplying the required seal.

### Durable input delivery after attestation capability activation

The **likely** sequencing ambiguity comes from two rules that are not ordered consistently. The handoff says the workload must verify bytes/digests and rehydrate the private store in a fresh process, while its required order places “deliver and rehydrate” before the Confidential Space launch; elsewhere it says GCS capabilities are constructed only after verified attestation. If GCS is the approved delivery boundary, the signed workload cannot perform that read before attestation-gated capability activation.

Provision the immutable public/private package and record its digests before launch. After the one real attestation activates only the bound read capability, have the locked workload read and verify the package and fresh-process rehydrate the private store. That completion must precede the verified timing-derived seed and task/control issue. The plan should also say explicitly that no time-seeded input, challenge, or worker task is built before the timing record, while static package provisioning is commitment data and never execution evidence.

### Narrow task contract, execution evidence, and release boundary

The explicit `case_id`/digest/ordinal, `cold_reset` budget, and single `illegal_action` control satisfy REVIEW-063’s requirement to select rather than inherit the catalog. The same worker/evaluator seam, supervisor, receipt path, and immutable lock are required for the control, and an unexpected legal action fails closed. The safety checks therefore do not add hidden P5 arms.

The required timing-before-seed order, FreeTSA bridge and durable ledger, authenticated lifecycle/resource evidence, OOM/deadline and process-group cleanup, rollback/impasse handling, and canonical signed receipt chain are all stated as Track A gates. The claim boundary excludes exact-CPU-timing, independent-evaluator, release, adoption, positive-transfer, and broader unselected-arm claims. P5-E1/E2 and upstream gates remain outside this dispatch, while Track B hardening remains optional and non-blocking.

</details>

<details>
<summary>Files reviewed</summary>

- `docs/research/engine_substrate/P5_BLOCKER_COMPLETION_PLAN.md` — corrected Track A/Track B plan, MVP sequence, signing branch, and fail-closed rules.
- `docs/research/engine_substrate/P5_PRODUCTION_INPUT_HANDOFF.md` — durable input boundary, gate matrix, publication boundary, and acceptance rule.
- `docs/research/engine_substrate/P5_ATTESTED_RESULT_REQUIREMENTS.md` — normative timing, resource, receipt, result-seal, and claim requirements.
- `docs/research/engine_substrate/P5_MASTER_RUNSHEET.md` — REVIEW-063 findings and DISPATCH-062 scope.

Full diff context: the reviewed documents and their current working-tree state in this repository.

</details>
