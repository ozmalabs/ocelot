# Deferred queue audit v2 results

Date: 2026-09-26

## Result

The source-locked design completed 18 fresh workers: sizes 1/2/4, two replicates, and full/scoped-only/scoped-plus-fallback arms. The initial v2 analyzer used the wrong lock key for the native artifact field; its analysis-only correction is recorded in the [v2.1 amendment](SUBSTRATE_DEFERRED_QUEUE_AUDIT_V2_1_AMENDMENT_20260926.md). The original runner capture is unchanged. The amended independent analysis passes 157/157 checks, including lock stability, exact semantic parity, queue conservation, producer attribution, process uniqueness, and repeated outcomes.

Each full-closure run queues and drains one RulePatch, one TrackIdentity operation, and one NetCollapse operation, with one drain batch per family. The enqueue counters attribute all three records to the fixture's `mixed_deferred_writer` RuleIdx. In scoped-only runs, each record is enqueued and none is drained; the report marks deferred work pending. In scoped-plus-fallback runs, a subsequent global fallback drains one record from each family without enqueuing another. Full and fallback terminal states match exactly and both settle at fixed points for all sizes and replicates.

Measured drain times are in the low tens of microseconds for RulePatch and a few microseconds for TrackIdentity and NetCollapse in this tiny synthetic fixture. These values include audit counter work and should not be interpreted as stable per-item service rates or projected to live workloads.

## Limits and next gate

This instruments five deferred families, but dynamic exercise here covers only RulePatch, TrackIdentity, and NetCollapse. Rule edits and framebuffer samples are source-instrumented but not exercised by this capture. Enqueues carry producer RuleIdx attribution; queue records still do not retain that identity, so drain work is only attributed by family, not producer. Existing pass/enumeration counters are present, but scheduler scan slots and dirty-queue maintenance are not separately counted. The next gate is to add scheduler slot/selection counters with exact loop-work conservation, then dynamically exercise the remaining queue families and compare full-closure semantics, costs, and owner effects.

## Artifacts

- [Preregistration](SUBSTRATE_DEFERRED_QUEUE_AUDIT_V2_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_mixed_deferred_queue_fallback_v2.py)
- [Captured v2 analyzer](../../../scripts/analyze_substrate_deferred_queue_audit_v2.py)
- [Corrected independent analyzer](../../../scripts/analyze_substrate_deferred_queue_audit_v2_1.py)
- [Raw capture](../../../evaluation/reports/substrate_deferred_queue_audit_v2_20260926.json)
- [Amended analysis](../../../evaluation/reports/substrate_deferred_queue_audit_v2_1_analysis_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/deferred_queue_audit_v2_lock_20260926.json)
