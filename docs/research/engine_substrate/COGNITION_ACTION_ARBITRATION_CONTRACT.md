# P5.G3 — Action inhibition before external emission

**Status:** G3.1 contract and development fixtures; no runtime stop enforcement is claimed. The policy is `ResponseInhibitionPolicy.enabled=0` by default. G3.2 owns graph stop/withhold records; G3.3 owns the native sink gate and must pass an instrumented sink test before any emission-safety claim.

## State and identity

An action proposal is an immutable `ActionRequest` identified by `(request_id, source_epoch, action_key)`. Selection records one candidate for that request. Authorization is a distinct, revocable token identified by `(request_id, source_epoch, authorization_id)` and names the exact selected candidate and sink route. An emission receipt is minted only after the common sink accepts that token; it records the request, authorization, route, epoch and one sink receipt ID. Observation is a later world event linked to the emission receipt. An observed outcome never retroactively authorizes an emission.

The graph lifecycle is monotonic: `proposed → selected → authorized → emitted → observed`, or `proposed/selected/authorized → withheld`. `withheld` and `emitted` are terminal for that request. Stop against an already emitted request yields `already_emitted` and an audit record; it does not erase the receipt or imply reversal of the world effect. A retry after withholding requires a new request ID and a fresh selection/authorization. Reusing the old ID cannot rearm it.

## Stop ordering and the commit boundary

A stop event is scoped to request ID and source epoch. A stop for another request or stale epoch cannot cancel the current request. When stop and go/authorization events for the same request and epoch are both visible before sink commit, stop wins independent of insertion order: pending authorization is revoked, the request becomes withheld, and the sink receives no action. A stop arriving after the sink has accepted an authorization is recorded as `already_emitted`; physical undo is outside this contract.

There is one final authorization check at the native dispatch-to-effect boundary. Candidate ranking and graph state alone do not constitute sink authorization. The check atomically observes the current stop state and consumes the authorization at most once immediately before invoking an effect. All reflex and motor routes must cross this same check; no route may call an effect handler directly. A hard host veto remains active when the graph policy is disabled and can only withhold more actions. With the graph policy disabled and no host veto, the legacy route preserves its existing behavior.

Current dispatch inventory: [`substrate/world_adapter.py`](../../../substrate/world_adapter.py) `WorldAdapter.fire_reflexes` repeatedly obtains a selected ready reflex from Rust `Substrate.next_ready_reflex` and invokes the registered response callback (`fn(self)`). The selector is [`runners/dsl/src/py.rs`](../../../runners/dsl/src/py.rs) `PySubstrate::next_ready_reflex`, which calls `reflex_runtime::next_ready` and stamps the reflex before returning it. This is the common reflex callback boundary; G3.3 must move/extend the final authorization consumption so a stop is checked immediately before callback effect, and must audit any motor dispatch path found during implementation. The current selector's stamp is a scheduling mark, not an emission receipt.

## Failure and retry rules

- Missing, stale, mismatched, revoked or previously consumed authorization means withhold.
- Stop dominates go only when both apply to the same request and epoch and are known before sink commit. A stale stop is retained as audit evidence but does not affect a newer request.
- Sink failure produces a terminal `emission_failed` record with the consumed authorization identity. The same authorization cannot be retried; a new request must be selected and authorized.
- Duplicate dispatch of an emitted or withheld request is idempotent and cannot invoke the sink again.
- A sink receipt is the only transition to `emitted`; graph intent, selection, or callback scheduling is not proof of emission.

## Development acceptance fixtures

These fixtures define transition outcomes for G3.2/G3.3; they are not runtime evidence. `test_stop_before_emit_withholds` covers stop after selection but before commit. `test_go_executes_once` covers a valid token and duplicate request. `test_late_stop_reports_already_emitted` preserves the emission receipt and reports no undo. `test_same_epoch_stop_wins` permutes stop/go insertion order and requires the same withheld result. G3.2 adds `test_withheld_cannot_rearm_from_same_request` and `test_default_off_parity`. G3.3 requires instrumented sink tests `test_native_sink_never_receives_stopped_action`, `test_same_epoch_stop_wins_at_sink`, and `test_sink_idempotence`; graph-only assertions cannot satisfy them.
