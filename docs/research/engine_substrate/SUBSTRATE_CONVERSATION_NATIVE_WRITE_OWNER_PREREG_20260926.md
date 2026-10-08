# Native rule-write to frame-owner notification preregistration (2026-09-26)

## Question

When a native conversation rule writes a shared evidence node owned by two consumer frames, does the scoped graph-delta observer report every directly affected Microtheory, and can a caller use those IDs to schedule consumer frames with exact parity to full closure?

## Fixture and arms

Use the locked read-only-boundary conversation graph (N=2/4/8, three fresh replicates) with the patched native score rule that reads `BoundaryEvidence.boundary_value`. Add one native trigger rule: a controller Microtheory owns a trigger and boundary edge 0, and a typed trigger relation points to that evidence. When the trigger's `active` attr is 1, the rule sets edge 0's `boundary_value` to 4 and resets the trigger to 0. The shared evidence is also owned by frames 0 and 1; the controller and two consumers therefore directly own the written node.

Settle an initial baseline. Reopen only frames 0/1, bump their epochs, and activate the trigger. Compare three fresh-graph arms:

- `full_oracle`: run full exact-snapshot delta closure; record full final projection, exact changed graph IDs, owner Mts, and fixed-point status.
- `native_required`: run `run_rules_scoped_delta_report` on the controller scope. Map returned Microtheory IDs to the live frames; schedule each reported consumer owner with scoped delta reporting until the queue is quiescent. Require exact parity with full closure and a zero-work full probe.
- `native_omitted`: use the same native writer report but deliberately drop consumer frame 1 from the caller queue. Save the stale projection, then run full catch-up and require positive work and exact recovery.

The native observer's returned owner IDs, direct effect targets, and edge keys are compared with the full exact snapshot oracle. The caller's only policy is to enqueue the owners reported by the API; the omitted arm is a negative control. This is not a new native scheduler implementation.

## Gates

Require 27 fresh workers, balanced matrix, unique PIDs and source/native hashes; exact baseline equality; writer rule fires once, evidence becomes 4 and trigger resets; controller scoped report makes progress, does not hit its cap, and has no deferred effects pending; its affected owner set is exactly controller+frames 0+1 and covers the exact snapshot oracle's affected owners; mutation-log node/edge targets cover the exact diff for the native writer operation; all required consumer scopes settle and match the full projection; omitted frame 1 causes a stale projection and positive full catch-up, which recovers exactly; all final full probes are zero-work fixed points; shared evidence is not subsequently rewritten.

## Scope and limitations

This tests the existing native mutation observer on one in-memory conversation rule family and one shared-node `SetAttr` effect. Owner mapping is direct Microtheory ownership, not dependency-component reconstruction from arbitrary access patterns. It does not cover other effect families, deferred effects, concurrent writers, graph-edge birth/deletion, arbitrary rule access, natural task prevalence, or scaling beyond eight frames. It measures caller-driven scheduling from native report output; `frame_notifications_complete` remains false and automatic queue delivery is not claimed.

## Provenance

Lock the protocol, runner, analyzer, the read-only-boundary runner, seed/materializer, Python binding, native substrate/rewrite sources, and native build before execution. Preserve raw records even if any semantic gate fails.
