# Durable P5 diagnostic rehydration and evidence seams

This change adds explicit private-store injection, checkpoint persistence and restart rehydration, typed supervisor-evidence validation, and an attested one-shot control-plane wrapper around the existing P5-R0 evaluator. The repository-side service can now reconstruct evaluator state from a durable manifest, truth store, and checkpoint instead of depending on its process-local engine map, while the native runner still deliberately reports no-go without the required external inputs. The implementation preserves several important claim boundaries, including `external_authority_verified: false` and callback rejection of `native_verified: true`. **Watch for:** **confirmed** the native readiness runner still requires the process-local `_PRIVATE_STORES` registry; **confirmed** one-shot timing is recorded outside the service timing chain and conflicts with a real bridge; **confirmed** caller-supplied supervisor evidence can set the result's `native_verified` field without supervisor authentication; **confirmed** persistence failures after evaluator mutation do not invalidate the live engine; and **confirmed** task authorization is optional in one-shot execution.

**Verdict**: NEEDS_CHANGES

## High-level view

The service-side checkpoint path is a real durable-state improvement: it reloads the lock, manifest, private store, and checkpoint and rejects missing or mismatched commitments. The native readiness path is not equally rehydrated, however; its production-shaped runner still asks the fixture registry for private truth, so a fresh process cannot execute the same locked bundle. **(confirmed)**

The one-shot wrapper establishes an attestation-before-start shape and keeps its public output redacted and no-go, but it invents a separate seed event directly through the timing adapter rather than adding that event to the service's durable timing state. With the real chained bridge this makes the first service task event fail sequence validation, and even a permissive adapter leaves the seed outside the receipt/seal binding. **(confirmed)**

The supervisor seam is structurally closed but not authoritative: a self-consistent record with `attestation_status: verified_supervisor_observation` is enough for the readiness code to set `native_verified` before any trusted supervisor or signature check. The final policy normally remains no-go because external authority is still required, but the evidence object itself is already overstated and cannot be treated as a verified native observation. **(confirmed)**

The service invalidates its in-memory engine on generation conflicts, but not when terminal evidence, timing, receipt, or state persistence fails after `engine.evaluate` has mutated it. A retry can therefore reuse state that was never durably committed. **(confirmed)**

<details>
<summary>Issues (5)</summary>

1. **HIGH — Native runner still depends on fixture truth** — **confirmed** `run_readiness_gate` calls `validate_manifest_integrity(bundle)`, `private_store_for(bundle)`, and `P5R0Evaluator(bundle)` without a durable private store. Pass the rehydrated store explicitly through the native runner and reject any production path that falls back to `_PRIVATE_STORES`.
2. **HIGH — One-shot timing is outside the durable chain** — **confirmed** `OneShotProductionRunner` records a synthetic seed event directly on the timing adapter before `service.next_task`; a real chained bridge advances its sequence while the service state still expects the first event, and the seed digest is not in the service receipt/seal chain. Add a service-owned timing-first operation that persists and binds the seed event, or do not derive the seed in this wrapper.
3. **HIGH — Supervisor observations can self-promote native verification** — **confirmed** `validate_supervisor_evidence` authenticates neither a supervisor signer nor a configured `NativeSupervisor`, while `run_readiness_gate` promotes the self-reported status into `native_verified`. Require a trusted adapter/signature and bind invocation count, exit, cleanup, and supervisor identity to the locked closure before deriving that flag.
4. **HIGH — Persistence failure leaves a mutated engine live** — **confirmed** after `engine.evaluate`, later timing/evidence/receipt/object-store writes can fail without removing or restoring `_engines[run_id]`; a retry then operates on state absent from durable `state.json`. Invalidate the engine and rehydrate from the last committed checkpoint on every post-evaluation failure, with an explicit rollback/impasse receipt where applicable.
5. **MEDIUM — One-shot executes without mandatory authorized-task validation** — **confirmed** `authorized_task_validator` is optional and no check binds the service start response or task commitments back to `OneShotConfig`. Make authorization and exact lock/manifest/worker binding mandatory before task execution, and fail closed before invoking the callback when they are absent.

</details>

<details>
<summary>Details</summary>

### HIGH — Native readiness path does not use the durable private store

`evaluation/p5_r0/runner.py:289-290` validates the manifest through the implicit fixture registry, and `evaluation/p5_r0/runner.py:314` calls `private_store_for(bundle)` followed by `P5R0Evaluator(bundle)`. **(confirmed)** A fresh process with only the durable lock, manifest, and truth object therefore cannot enter this runner; it either fails because `_PRIVATE_STORES` is empty or risks selecting process-local truth unrelated to the supplied bundle. The runner's V3 lock checks do not repair this because they validate commitments after obtaining the registry-backed data. The fix is to make the private store an explicit `run_readiness_gate` input or load it from the same durable object-store boundary, pass it to `validate_manifest_integrity` and `P5R0Evaluator`, and remove registry fallback from production/native orchestration.

### HIGH — One-shot timing cannot progress through the real bridge

`services/p5_r0_evaluator/one_shot.py:131-145` calls `service.timing_attestor.record` for a synthetic sequence-zero seed task and derives input before calling `service.next_task`. The service's normal task path records its own `task_issued` event in `services/p5_r0_evaluator/service.py:297-322`, while the chained timing adapters maintain their last sequence and previous digest per run (`services/p5_r0_evaluator/timing.py:59-70`). **(confirmed)** With a real chained adapter, the seed call consumes sequence 1, then the service state still has `timing_sequence == 0`; the next record is sequence 2 and `_record_timing` rejects it as non-monotonic. The synthetic event is also never written into `state["timing_record_digest"]`, `runs/<id>/timing`, a receipt binding, or the final service seal, so a permissive adapter would still leave the seed/input/result provenance disconnected. The seed event must be a first-class service operation whose verified V3 record is persisted in the same chain and whose digest is carried through task, result, receipt, and seal; otherwise the wrapper must stop before input derivation.

### HIGH — Self-attested supervisor evidence can set `native_verified`

`evaluation/p5_r0/supervisor.py:33-59` checks a closed field set, digest formatting, and `evidence_digest == digest(fields)`, but it does not verify a supervisor signature, a transport identity, or a configured `NativeSupervisor.validate_execution_evidence` result. Any caller can therefore construct a record with `attestation_status: verified_supervisor_observation` and a matching self-digest. **(confirmed)** `evaluation/p5_r0/runner.py:171-174` accepts that record, and `evaluation/p5_r0/runner.py:413-417` derives `supervisor_verified` and writes `native_verified` from those booleans before `evaluate_gate` runs. The default external-authority gate keeps the disposition no-go, but the result still contains a fabricated positive native-verification field, and a relaxed/custom policy could consume it. The validator must be an adapter boundary that authenticates the observation and checks it against the locked host-kill digest, exact invocation cardinality, worker exits, closure, and cleanup; only the adapter's verified result should derive `native_verified`.

### HIGH — Terminal persistence failures do not roll back evaluator state

The service protects the `engine.evaluate` call itself, but after the checkpoint is updated at `services/p5_r0_evaluator/service.py:622-638`, the result path performs timing writes, evidence-object creation, terminal receipt creation, and state advancement at `services/p5_r0_evaluator/service.py:639-670`. **(confirmed)** Failures from those operations are not covered by an outer cleanup handler, so `_engines[run_id]` remains the mutated engine while durable `state.json` still contains the outstanding task and the previous checkpoint. A retry can then evaluate against an already-advanced evaluator state and commit a result that does not correspond to the durable pre-failure state. The fix is transactional at the boundary: on every post-evaluation persistence or generation error, discard the engine, restore/rehydrate from the last durable checkpoint, and append a durable rollback/impasse record only when that record itself can be committed; never continue with the mutated object.

### MEDIUM — One-shot task authorization and commitment binding are optional

`services/p5_r0_evaluator/one_shot.py:41-49` makes both authorized-task and supervisor validators optional, and `services/p5_r0_evaluator/one_shot.py:150-159` invokes the service task and callback even when no authorized-task validator exists. The wrapper also checks only that `start` returned a syntactically valid `run_id` (`one_shot.py:116-129`); it does not compare the returned lock, manifest, or worker commitments with `OneShotConfig`, and `task_response` validates shape/digest but not authorization. **(confirmed)** This permits execution of a task selected by a misbound service or callback without verified authorized inputs. The no-go flags prevent this from becoming a trusted P5 result today, but the integration still violates the fail-closed input gate and can produce misleading diagnostic provenance. Require the validator, verify exact start/task commitments against the configured lock and manifest, and validate the time-seeded input namespace/content before invoking the worker seam.

### Test coverage does not exercise the blocking paths

The focused changed-file suite passes (`22 passed`), including checkpoint restoration, schema closure, and redaction tests. **(confirmed)** It does not cover a real chained timing adapter across the one-shot seed and first task, a fresh native-runner process with no `_PRIVATE_STORES` entry, forged supervisor evidence reaching `native_verified`, or receipt/evidence persistence failure followed by retry. Those cases should be added before treating the repository-side capability as complete.

</details>

<details>
<summary>File map</summary>

- `evaluation/p5_r0/runner.py` — native readiness orchestration, closure checks, supervisor projection, and persistence-independent evaluator construction.
- `evaluation/p5_r0/supervisor.py` — closed-shape supervisor observation validator without authenticity verification.
- `services/p5_r0_evaluator/engine.py` — explicit private-store engine creation and checkpoint rehydration.
- `services/p5_r0_evaluator/service.py` — durable run state, checkpoint persistence, timing, result submission, receipts, and seals.
- `services/p5_r0_evaluator/one_shot.py` — attested one-shot sequencing, seed derivation, callback execution, and redaction.
- `services/p5_r0_evaluator/timing.py` — per-run timing sequence/previous-digest tracking.
- `services/p5_r0_evaluator/tests/test_one_shot.py` — fake timing/service one-shot tests.
- `tests/test_p5_r0_supervisor.py` — closed-schema supervisor tests.

Full diff: `git diff main -- evaluation/p5_r0/evaluator.py evaluation/p5_r0/native.py evaluation/p5_r0/runner.py evaluation/p5_r0/scoring.py evaluation/p5_r0/supervisor.py services/p5_r0_evaluator/engine.py services/p5_r0_evaluator/interfaces.py services/p5_r0_evaluator/service.py services/p5_r0_evaluator/one_shot.py`.

</details>
