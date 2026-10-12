# Thoughtexperiment event value attribution v1.2 preregistration

## Question

Can opt-in per-event before/after values recover ordered semantic writes for direct and deferred rule events under repeated and overlapping writes, while preserving exact branch residuals and reporting instrumentation truncation?

## Implementation contract

Add event-local snapshots to the existing rule-write observer. On the first mutation touch of a node or edge during an event, retain its before-state (including absence); at event finish, read its after-state. Preserve event order and distinguish unchanged from changed fields. Existing `node_ids` and `edges` remain conservative write-target sets. Event snapshots are observational and do not alter rule matching or mutation semantics.

Apply explicit per-event and per-run capture budgets. The report must state configured and consumed budgets, number of events/fields truncated, and whether the capture is complete. A truncated value must never be represented as a complete before/after pair. The default ordinary execution path must not allocate event snapshots; only the explicitly enabled attribution report may pay this cost. Serialize values using the engine's existing persistence encoding and include schema/version tags.

## Workloads

Use source-locked, fresh-process workers for: (1) direct node-attribute and edge insertion writes; (2) deferred TrackIdentity writes; (3) repeated writes to one node field where the value changes twice and then is restored; (4) overlapping direct and deferred writers to the same field; (5) a no-op write; (6) edge insert/delete and edge-attribute mutation; and (7) multi-producer deferred events. Include an unrelated writer and an absent-before field. Compare each event's ordered values against an independent replay oracle and compare final state to the exact branch snapshot residual.

## Gates

1. Lock engine, binding, runner, analyzer, protocol, native extension and build manifest before capture; verify hashes before and after each worker.
2. Preserve plain, target-traced, and exact snapshot-delta status, progress-step and final-graph parity.
3. Independently check every complete event pair against the state immediately before and after that event in a replayed sequence; check final replay state against the branch snapshot.
4. Require exact event ordering and explicit attribution of absent, unchanged, changed, and truncated states. Never guess across truncated intervals.
5. Record event count, touched objects, encoded bytes, truncation, wall time, CPU time and peak RSS; compare traced and untraced runs separately. Do not claim negligible overhead from semantic parity.

## Claim limits

Passing validates ordered write-value capture for the listed mutation routes and bounded workloads only. It does not establish target-blind diagnosis, causal necessity, repair utility, natural-task prevalence, general termination, or production-scale instrumentation cost. If any mutation route bypasses the journal or serializes values ambiguously, keep the event incomplete and report the uncovered route.

## Implementation status note (2026-10-05)

The current source slice adds opt-in `RuleWriteEvent` value snapshots and persistence-format serialization. It estimates the retained before-image size with Rust `Debug` formatting, capped at 64 KiB per event and 4 MiB per report; reports mark an event incomplete if a first-touch before-image cannot be retained. The reported byte count is an estimate of retained before-images, not encoded JSON bytes or peak memory. After-images are cloned at event finish, so actual capture memory can exceed that estimate. This does not yet satisfy the full budget contract above. The Rust library passes `cargo check`; the release extension has not been rebuilt or runtime-validated, and no v1.2 capture has been run. Treat this as implementation-in-progress, not a passed gate. Before claiming the budget gate, account for both before- and after-images (including container/string payloads) or enforce an exact serialized-size cap, expose object counts and encoded byte counts, and measure peak RSS.

## v1.2.4 repeated-target extension

This source-locked extension adds an `overlap` fixture with two different rules that both write the same node field in sequence during one settlement. The initial value is 0; the first rule writes 1 and the second writes 2. The gate requires the ordered event snapshots to report 0→1 then 1→2, replay to the final value 2, and identify the second rule as the last writer. The legacy target-only reconstruction must expose both candidate events for the final changed field, demonstrating why target sets alone are ambiguous. The original direct/deferred fixtures remain controls. This extension does not claim coverage of multiple writes inside one rule invocation or truncation behavior.


## v1.2.4 bounded capture-budget extension

For each event, estimate the Debug representation sizes of both before- and after-values before retaining the pair. Enforce a 64 KiB/event and 4 MiB/report representation estimate, plus 512 objects/event and 16,384 objects/report. Any pair that would cross a cap is omitted and the event/report truncation receipt is set; do not emit a partial pair. The report includes configured caps and consumed estimated bytes/objects. These are representation-size bounds, not exact heap/RSS limits or encoded-JSON limits.

Add two deliberate stress controls: `byte_cap` uses a single large list-valued attribute so the before-image estimate exceeds the per-event cap; `object_cap` applies one rule to 520 distinct nodes so the per-event object cap is reached. Require explicit truncation, no partial value pair for the oversized object, at most 512 retained objects for the object-cap event, bounded reported totals, and unchanged ordinary/traced/exact final-state parity. Replay complete fixtures only; do not infer missing changes from truncated event intervals.


## v1.2.4 direct/deferred same-field conflict extension

Add `direct_deferred_overlap`: a direct rule writes `CurPercept.identity=99`, while a queued `TrackIdentity` effect writes an inferred identity (0 for the matched percept) to that same field. Run with progress budget 10. Require complete ordered snapshots, exact plain/traced/exact final graph parity, a repeated alternating value chain identifying each direct and deferred writer, and explicit `progress_budget_reached` status rather than treating the cap as convergence. Confirm that the final value agrees with the final captured writer event. This is a deliberately conflicting authored workload and is not a general closure-termination result.


## v1.2.4 report-object cap boundary

The cap constants imply a report-byte upper bound of 16,384 report objects × 64 KiB/event ÷ 512 objects/event = 2 MiB for snapshot pairs, so the 4 MiB/report estimated-byte cap cannot bind before the report-object cap under the current accounting. Verify the reachable object boundary using 33 rules, each touching a disjoint group of 512 nodes. Require 32 complete event groups (16,384 objects), explicit truncation on the 33rd group, no event claiming completeness for omitted pairs, exact plain/traced/exact graph parity, and replay parity for every captured complete group. Treat the report-byte bound as algebraic evidence conditional on the current counters and caps; it does not bound transient Debug formatting allocations or heap/RSS.
