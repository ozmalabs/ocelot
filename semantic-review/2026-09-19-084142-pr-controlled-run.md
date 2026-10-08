# Project-generated controlled-run manifest and signed-execution gate

The two changes correctly move the P5 controlled-run model to project-generated inputs: the generator owns the manifest, split, private truth, task set, controls, contracts, policy, and unsigned lock request, while environment facts remain separate gates. The materializer discloses the timing-derived hash chain, records semantic and raw file commitments, and marks the output review-only with no execution evidence, signatures, cloud operations, or production promotion. The handoff and blocker plan also consistently state that there is no external task provider and that generated inputs are not execution evidence. **Watch for:** **confirmed** blocking gaps remain in the alternate production API path, which accepts unseeded V1 evidence, and in the missing input-builder version commitment; route all production runs through the timing-first contract and bind the builder identity before promotion.

**Verdict**: NEEDS_CHANGES

## High-level view

The generator/materializer boundary is coherent: project-controlled artifacts are provenance and commitment inputs, not evidence that a task ran. The manifest distinguishes semantic artifact digests from raw file digests, exposes `timing_record_digest`, `input_seed_digest`, and `input_digest`, and sets the local status to blocked without claiming signed execution.

The timing-first behavior is implemented in `OneShotProductionRunner`, but the repository exposes another path through `P5ProductionRunner` and the service schemas. **Confirmed:** that path can issue tasks and accept `P5R0ExecutionEvidenceV1` without deriving or preserving a timing-seeded input, so the documented requirement is not enforced at the production boundary.

The documents correctly describe the project authority as self-custodied and use external authority/provider language only for signed-environment trust binding. No remaining P5 document or generated manifest says that an external task or input provider must supply the run; `external_authority_required` is potentially confusing naming, but its adjacent semantics explicitly say it is not an independent evaluator requirement.

<details>
<summary>Issues (2)</summary>

1. **Unseeded production API path** — **confirmed:** `P5ProductionRunner` never calls `issue_time_seed`/`derive_time_seed`, and `schemas.execution_evidence` still accepts `P5R0ExecutionEvidenceV1` without the three required digest bindings. Make the production route timing-first and require V2 evidence bound to the service-owned seed, or remove/declassify the legacy route as diagnostic-only.
2. **Uncommitted input-builder identity** — **confirmed:** the manifest commits `time_seed.py` but neither `OneShotConfig` nor the materialized manifest commits an input-builder version/source digest. Add a canonical builder/version commitment to the lock, evidence, and seal path so deterministic reconstruction cannot silently change the builder while retaining the same hash algorithm.

</details>

<details>
<summary>Details</summary>

### Project-owned inputs and review-only claim boundary

The generator creates the controlled-run artifacts and labels the task set’s `authorized` field as a frozen contract shape, while the adjacent control commitment marks it self-custodied, diagnostic, non-release, and still requiring signed execution. The materializer rechecks canonical artifact bytes, semantic commitments, private custody, closure observations, authority proposal semantics, and the unsigned request; it emits `generated_controlled_run_inputs=true`, `fabricated_evidence=false`, `execution_evidence_present=false`, and no cloud operations. The manifest’s outer `manifest_digest` is a semantic digest of the object before the self-referential field is added; its artifact record separately preserves the raw file digest, so the differing values are not a binding mismatch.

The materializer’s disclosed algorithm is exact at the hash-chain level: `sha256(canonical_json(timing_record))` produces `timing_record_digest`; the canonical object containing `P5R0TimeSeedV1`, that timing digest, run ID, namespace, and sequence produces `input_seed_digest`; only that digest is passed to the builder; and canonical input bytes produce `input_digest`. The `OneShotProductionRunner` then requires those three values in `P5R0ExecutionEvidenceV2`, and the service’s V2 task record/receipt/seal chain retains an evidence-digest path to them. No document or manifest claims that this local materialization is signed execution.

### Unseeded production API path

This is a **confirmed** gap: `P5ProductionRunner.run()` starts the run, calls `next_task`, invokes its callback, and submits the callback result; there is no `issue_time_seed` or `derive_time_seed` operation in that sequence (`services/p5_r0_evaluator/production_runner.py:118-166`). Its tests construct and submit `P5R0ExecutionEvidenceV1`, which contains only closure/runtime/host/kill digests and `native_verified`, not the timing/input chain.

The service schema still deliberately accepts both V1 and V2 (`services/p5_r0_evaluator/schemas.py:59-74`), and `next_task` can issue a task without requiring the prior `issue_time_seed` operation. Thus a caller using the ordinary client/runner route can produce a task/result chain that is internally signed and sealed as an impasse but has no time-derived input binding. The fix is to make the production route use the one-shot timing-first contract, or add an explicit production mode that rejects V1, requires the service-owned seed commitment before task issuance, and verifies V2 digests against the committed run state. V1 can remain only behind a clearly diagnostic/test-only boundary.

### Input-builder provenance is not committed

This is a **confirmed** gap: `controlled_run_materializer._time_seed_algorithm()` records the implementation and raw digest of `time_seed.py`, but records only the abstract operation `input_builder(input_seed_digest)` and no builder identity, version, source digest, or lock commitment (`services/p5_r0_evaluator/deploy/controlled_run_materializer.py:217-234`). `OneShotConfig` likewise accepts an arbitrary callable (`services/p5_r0_evaluator/time_seed.py:47-50` and `services/p5_r0_evaluator/one_shot.py:30-47`). The prescribed formula remains disclosed, but deterministic reconstruction can still change if the callable changes while the formula and `input_seed_digest` remain identical. The builder commitment should be canonical, exact-bound to the run/lock, and carried through V2 evidence and the persisted result seal; otherwise keep the path explicitly review-only.

### Provider wording and state

The P5 requirements, handoff, blocker plan, and generated manifest consistently say that all controlled-run inputs are project-generated and that the absence of an external task provider is not a blocker. The remaining `external_authority_required` fields refer to the external signed-environment trust/attestation gate, not to task or input supply, and the surrounding values set `independent_evaluator_required=false` and `independent_authority_claim=false`. No wording change is required for an external task/input provider; renaming that authority field to `signed_environment_authority_required` would be a clarity improvement, not a current blocker.

### Test coverage

The focused materializer, timing, one-shot, execution-request, and production-runner tests pass (32 tests), and deterministic manifest regeneration is byte-for-byte identical. Coverage proves the one-shot seam and local boundary assertions, but it does not test that the ordinary service/production-runner path is rejected before task issuance when no time seed exists, nor that an input-builder version/source commitment is required and preserved through the final seal.

</details>

<details>
<summary>Files</summary>

- `services/p5_r0_evaluator/deploy/controlled_run_materializer.py` — validates project-generated artifacts and emits the review-only manifest, including the disclosed time-seed algorithm.
- `var/p5-r0-controlled-run/manifest.json` — deterministic local manifest with semantic/raw commitments and blocked signed-environment status.
- `docs/research/engine_substrate/P5_ATTESTED_RESULT_REQUIREMENTS.md` — canonical project-generated-input, timing-chain, and claim-boundary requirements.
- `docs/research/engine_substrate/P5_PRODUCTION_INPUT_HANDOFF.md` — generated-input/evidence handoff and no-external-provider clarification.
- `docs/research/engine_substrate/P5_BLOCKER_COMPLETION_PLAN.md` — blocker and no-go plan.
- `services/p5_r0_evaluator/one_shot.py` — timing-first path that validates V2 evidence.
- `services/p5_r0_evaluator/production_runner.py` — alternate path that currently bypasses timing-first seed derivation.
- `services/p5_r0_evaluator/schemas.py` — accepts both unbound V1 and bound V2 execution evidence.
- `services/p5_r0_evaluator/time_seed.py` — disclosed hash-chain implementation without builder provenance.

Full diff: `git diff main`.

</details>

## Proposed master-runner state updates

Do not promote any signed-execution item. Retain `RS-062` and the materializer as `PASS_REVIEW` for project-generated local inputs only; retain `RS-063`, `RS-065`, `RS-067`, `RS-068`, and `RS-069` at their existing repository-only `PASS_REVIEW` states. Keep `RS-066`, `RS-070`, `RS-080`, `RS-090`, `RS-100`, and `RS-110` `BLOCKED`, and retain `RS-900` as `NO_GO`. Add the two findings as blockers before any `RS-070` task release or `RS-090` execution transition: enforce timing-first/V2 evidence on every production route and commit the input-builder identity/version; no cloud, KMS, GCS, supervisor, task, or runsheet mutation is authorized by this review.


## Repair update (local code/tests only)

The two confirmed blockers are addressed in the repository implementation, without promoting execution. `P5ProductionRunner` now starts with `execution_mode=timing_first`, invokes the service-owned time-seed route before requesting a task, derives the configured input, and rejects legacy or mismatched evidence before submission. The service refuses task issuance until the timing/input commitments are durably present; timing-first result submission requires `P5R0ExecutionEvidenceV2` and exact timing, input, builder, and algorithm bindings. Requests without an explicit mode remain explicitly `diagnostic_only`, where legacy V1 is retained only for compatibility tests.

The deterministic generator, review-only materializer, lock request, manifest, and source-bound diagnostic outputs now disclose and bind the input-builder implementation/version/source digest and time-seed algorithm implementation/version/source digest. Altering either source binding fails closed. The final service seal remains local-readiness/no-go and carries no signed execution claim. Focused local validation passed; no KMS, gcloud, GCS, FreeTSA, deployment, VM, supervisor, or task execution was performed.
