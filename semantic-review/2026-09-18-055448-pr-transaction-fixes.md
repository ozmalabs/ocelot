# Durable checkpoint rollback and timing outbox repairs

The transaction fixes now persist engine checkpoints, rebuild a fresh engine from the pre-evaluation durable checkpoint after terminal persistence failures, and use per-event timing outboxes plus exact replay checks. The focused P5 suite passes, including rollback retry, seed/result timing recovery, V1 seed rejection, and receipt/timing bindings; compile and whitespace checks also pass. The repository remains diagnostic/no-go because native verification and external authority claims stay false. **Watch for:** **confirmed** external timing cannot continue after a fresh evaluator process, **confirmed** the injected recorder adapter is broken by this diff, and **confirmed** an outbox verification-write failure leaves a timing event permanently unrecoverable.

**Verdict**: NEEDS_CHANGES

## High-level view

Rollback now uses the caller-supplied durable pre-evaluation checkpoint independently of the mutated in-memory checkpoint. A failed evidence, receipt, seal, or final-state write drops the mutated engine, rehydrates a fresh engine, and leaves the in-memory checkpoint at the durable baseline; the retry test demonstrates that the evaluator counter is not reused from the failed attempt.

Timing requests are namespace-bound by task/event/payload digests, validated against the V3 signature, sequence, previous digest, authority, ledger, and RFC3161 digest, and persisted with exact create-or-verify semantics. **Confirmed:** the remaining failure boundary is between the external bridge’s chain head and the evaluator process: a new HTTPS bridge client has no way to restore the durable head, and a failed outbox finalization cannot recover the returned record.

The no-go boundary is preserved: V1 timing is rejected before seed artifacts or recorder use, evidence cannot self-claim native verification, and the wrapper closes only as a diagnostic impasse. **Confirmed:** the added tests do not cover a fresh production-shaped bridge client or a failure of the outbox’s own verification write.

<details>
<summary>Issues (4)</summary>

1. **P1 — Recorder adapter method removed** — **confirmed:** `ExternallyKeyedTimingAttestor` now defines `restore_chain` where `record` used to be, so the supported `timing_recorder_factory` path constructs an object that cannot record an event. Restore the `record` method as a separate method and add a construction-to-record regression.
2. **P1 — Fresh bridge loses the durable timing head** — **confirmed:** `HTTPSRFC3161TimingBridgeClient` stores `_chains` only in memory and has no `restore_chain`; after restart, the next bridge response is validated as sequence 1/previous `None` even though the durable bridge ledger returns sequence 2/previous record digest. Add a validated chain-head restore before every post-restart event, or make the client recover the head from the durable bridge.
3. **P1 — Outbox finalization failure is not recoverable** — **confirmed:** if the external recorder succeeds but replacing the pending outbox marker with the verified record fails, the marker remains pending without the record and every retry returns `timing recovery record unavailable`. Persist/retrieve the returned record through an idempotent bridge operation or provide a durable recovery protocol; do not reinvoke the recorder or fabricate evidence.
4. **P2 — Missing production-shaped regressions** — **confirmed:** the tests exercise fake timing objects and same-process retries, but no test creates a fresh HTTPS bridge client against an already-advanced chain or injects failure into the pending-to-verified outbox replace. Add both regressions before treating restart and timing-write recovery as closed.

</details>

<details>
<summary>Details</summary>

### Pre-evaluation checkpoint rollback and retry isolation

The rollback fix is **confirmed resolved** for the requested engine invariant. `submit_result` captures `state["engine_checkpoint"]` before evaluation; `_rehydrate_after_failed_evaluation` validates and passes that supplied checkpoint directly to `engine_factory.rehydrate`, rather than comparing it with the post-evaluation checkpoint left in the mutable state. It then reinstalls the fresh engine and resets the in-memory checkpoint digest to the durable baseline. The evidence persistence failure test verifies the engine value returns to zero and that the same result can be retried to a committed cursor/receipt state, so a retry cannot consume the mutated engine instance.

### External timing recorder seam

The change to `services/p5_r0_evaluator/timing.py` is **confirmed** to have removed the `record` method from `ExternallyKeyedTimingAttestor`: the new `restore_chain` method begins at line 59, and the former recording body remains indented inside it at lines 70–81 while referring to undefined `task_id`, `event`, and `payload_digest`. `CapabilityFactory` still supports constructing this class around `timing_recorder_factory`, and the service requires `.record(...)`; that path therefore fails closed on its first timing event instead of reaching the recorder.

### Fresh-process timing chain binding

The restart gap is **confirmed** by the two changed components. The service restores a chain only when it sees a newly created pending outbox and the attestor happens to implement `restore_chain` (`service.py` lines 344–347). The production `HTTPSRFC3161TimingBridgeClient` has only an in-memory `_chains` map and a `record` method (`timing_bridge.py` lines 106 and 157 onward); it does not implement that restoration seam. After a process restart, the durable evaluator state still says sequence 1 with digest `D1`, but the new client validates the bridge’s sequence-2 response against local `(0, None)`, causing its local proof/sequence check to fail closed. This blocks the next event even though the bridge ledger and evaluator state are otherwise consistent.

### Outbox durability boundary

The outbox makes the normal state-write failure replay-safe, which the new seed and result tests confirm: once the outbox is `verified`, a retry reads the exact record and does not invoke the recorder again. The remaining failure is **confirmed** at `service.py` lines 370–378. The recorder is called after a pending marker is created; if the replace that stores `timing_record` and changes `status` to `verified` fails, durable storage retains only the pending marker. On retry, lines 336–343 deliberately refuse to call the recorder again and refuse a marker containing no record, so the operation is fail-closed but not recoverable/idempotent as required.

### Schema, digest, sequence, receipt, and no-go boundaries

The timing validation is **confirmed** to bind the V3 schema, run/task/event/payload, signer public-key digest, configured authority/key/ledger, RFC3161 evidence digest, sequence, and previous-record digest. Seed issuance rejects diagnostic V1 before recorder or seed artifacts; receipt payloads bind task/result/evidence/timing digests; exact object writes prevent conflicting reuse. These checks preserve the self-custodied diagnostic boundary: native evidence remains false and the service closes as `impasse`, rather than promoting a local result.

The test coverage gap is **confirmed** from the focused suite: 176 P5 service tests pass, including the added same-process persistence retries, but the suite has no fresh-client chain restoration test and no injected failure of the outbox pending-to-verified replacement. Those are the two paths that can invalidate the claimed restart and timing-write guarantees while all current tests remain green.

</details>

<details>
<summary>File map</summary>

- `services/p5_r0_evaluator/service.py` — durable checkpoints, timing outbox/replay handling, result rollback, and receipt/state persistence.
- `services/p5_r0_evaluator/timing.py` — external recorder chain restoration and V3 timing validation.
- `services/p5_r0_evaluator/timing_bridge.py` — HTTPS bridge client and in-memory chain head.
- `services/p5_r0_evaluator/engine.py` — fresh repository-engine checkpoint rehydration.
- `services/p5_r0_evaluator/tests/test_service.py` — rollback, restart, timing recovery, conflict, and V1 rejection regressions.
- `services/p5_r0_evaluator/tests/test_timing_bridge.py` — signed V3 bridge validation tests.
- `services/p5_r0_evaluator/tests/test_timing_bridge_service.py` — durable ledger sequence/replay tests.

Full diff: `git diff main -- evaluation/p5_r0 services/p5_r0_evaluator tests/test_p5_r0_runner.py tests/test_p5_r0_v3_activation.py tests/test_p5_r0_v3_repair.py`.

</details>
