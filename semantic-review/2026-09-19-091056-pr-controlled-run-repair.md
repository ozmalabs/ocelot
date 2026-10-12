# Timing-first production gate with bound deterministic inputs

The repair moves the normal evaluator route to an explicit `timing_first` mode: the service-owned independent timing seed is committed before task issuance, the input is derived from that seed, and result evidence is checked against the run’s timing and input commitments. Legacy run-start requests are normalized to `diagnostic_only`, while timing-first submissions require V2 evidence and the builder/algorithm source bindings; the final local seal carries the same input commitment bundle. The materializer and bundle validators recompute the builder and time-seed source digests, and the focused gate/boundary tests pass. **Watch for:** **confirmed** RS-065’s checked-in KMS lock-signing contract still contains the pre-repair unsigned-lock digest, so the full local validation suite is not green until that repository-only commitment is refreshed.

**Verdict**: NEEDS_CHANGES

## High-level view

The production path is now gated by a service-owned timing record and cannot issue a timing-first task until timing, input-seed, and input digests are durable. V1 evidence is confined to the explicitly diagnostic mode; normal result acceptance requires V2 timing/input fields plus the input-builder implementation, version, source digest, and time-seed source digest.

The deterministic input builder and time-seed algorithm are bound into generated provenance, manifests, locks, bundle validation, evidence, and the terminal seal. Source-drift tests fail closed for altered builder or algorithm commitments, and the final seal remains `local_readiness_only/no_go` with `native_verified` and `external_authority_verified` false.

The repair leaves the no-cloud/no-signing/no-result boundary intact, but one downstream repository contract was not regenerated after the unsigned lock changed. This is **confirmed**: RS-065 rejects the current generated request as commitment drift; this is a consistency blocker for the review state, not evidence that signing or cloud execution occurred.

<details>
<summary>Issues (1)</summary>

1. **RS-065 unsigned-lock commitment drift** — **confirmed:** `p5-r0-kms-lock-signing-contract.json` and its exact-value test still expect `sha256:3b5514...`, while the repaired generator emits `sha256:4fc805...`; refresh the contract and dependent RS-065 commitment, then rerun the full local suite before changing the blocked/no-go state.

</details>

<details>
<summary>Details</summary>

### Timing-first task release and V2 result admission

`P5ProductionRunner` starts every normal run with `execution_mode=timing_first`, calls the service-owned time-seed route, derives the configured input, and validates the returned timing/input commitments before requesting a task. `EvaluatorService.next_task` independently fails closed when the durable seed fields are absent, so a caller cannot bypass the runner by requesting a task directly. At result admission, timing-first runs reject `P5R0ExecutionEvidenceV1` as diagnostic-only and compare every V2 timing, input, builder, and algorithm binding with the committed run state before evaluator execution.

The terminal `P5R0ResultSealV4` repeats those input commitments and verifies them against persisted state, while the receipt chain remains signed only as the evaluator’s local control-plane record. The seal explicitly reports `native_verified=false`, `external_authority_verified=false`, and `local_readiness_only/no_go`; it does not turn locally supplied evidence into a production result.

### Builder and time-seed provenance

The generator/materializer and production bundle validator recompute the canonical builder and time-seed bindings from repository source, rather than trusting only caller-provided digest strings. The focused materializer tests cover altered builder and algorithm source commitments, and the runner/service tests cover missing seed, legacy V1, and mismatched timing-first evidence before evaluation. The normal runner configuration also compares its bindings with the current repository bindings before construction.

### RS-065 downstream commitment drift

This is **confirmed**: `services/p5_r0_evaluator/deploy/kms_lock_signing.py` derives the expected RS-065 request from the repaired diagnostic generator, which now yields unsigned-lock digest `sha256:4fc80599aa0cc99881983cdb1270720de6d5c3f99c47701cf471da409d29a3df`. The checked-in `p5-r0-kms-lock-signing-contract.json` still records `sha256:3b551422667868fa846b9a3b504a2b102444b6909c4f8ff07e6e67fba1b31fc6`, and `test_checked_in_request_is_exact_and_contract_has_no_output` asserts the same stale value. Consequently `validate_contract()` raises `RS-065 request commitment drift`, and the CLI contract test fails; regenerate this repository-only metadata and its exact-value expectation without invoking KMS or creating a signature.

### No-cloud, no-signing, and no-result boundary

The review-only materializer, bundle definition, authority proposal, execution request, and KMS lock-signing validator explicitly describe no KMS, gcloud, GCS, FreeTSA, deployment, supervisor, task execution, or production output. Their outputs remain unsigned or diagnostic/non-release, and the generated manifest remains blocked pending signed-environment operations. The failing RS-065 checks are consistency checks over those local artifacts; they do not indicate a cloud call, signature generation, supervisor invocation, task execution, or promoted result.

### Proposed state and validation

Keep the repair at `PASS_REVIEW` for local timing-first implementation and project-generated commitments only, but keep overall production promotion `NEEDS_CHANGES`/blocked until the RS-065 digest contract is refreshed and the full suite passes. Retain no-go for signed-environment execution, KMS/GCS/gcloud/FreeTSA operations, deployment, supervisor startup, task release, and any production result claim.

Targeted validation passed: 46 tests covering the runner, service, materializer, bundle definition, time-seed path, and repair boundary. Broader relevant validation reached 304 passed and 2 failed; both failures are the confirmed RS-065 stale-digest mismatch described above. `git diff --check` also passed.

</details>

<details>
<summary>Files</summary>

- `services/p5_r0_evaluator/production_runner.py` — timing-first normal-run orchestration and V2 evidence gate.
- `services/p5_r0_evaluator/service.py` — durable seed gate, V2 binding checks, and sealed input commitments.
- `services/p5_r0_evaluator/schemas.py` — explicit diagnostic V1 and timing-first V2 request validation.
- `services/p5_r0_evaluator/input_builder.py` — canonical deterministic builder binding and source digest.
- `services/p5_r0_evaluator/time_seed.py` — independent timing-derived input commitments and evidence validation.
- `services/p5_r0_evaluator/deploy/controlled_run_materializer.py` — review-only provenance and no-operation boundary.
- `services/p5_r0_evaluator/deploy/kms_lock_signing.py` — failing RS-065 commitment validation path.
- `services/p5_r0_evaluator/deploy/p5-r0-kms-lock-signing-contract.json` — stale unsigned-lock digest metadata.
- `services/p5_r0_evaluator/tests/test_kms_lock_signing.py` — stale exact-value assertion causing one failure.

Full diff: `git diff main` plus the untracked repair files listed by `git status --short`.

</details>
