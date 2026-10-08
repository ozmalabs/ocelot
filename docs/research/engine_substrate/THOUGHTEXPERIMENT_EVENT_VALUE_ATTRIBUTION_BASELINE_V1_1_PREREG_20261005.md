# Thoughtexperiment event value attribution baseline v1.1

## Question

Can the current per-rule target observer plus isolated whole-settlement before/after graph snapshots recover exact changed fields for a progressed direct-write event and a deferred TrackIdentity event, without assigning changes when event targets overlap?

## Method

Run two bounded authored fixtures in three fresh worker processes, with a maximum progress budget of 3 to match the existing deferred-attribution probe and bound repeated writes. The direct fixture has one rule that updates a node attribute and inserts an edge. The deferred fixture follows the existing TrackIdentity attribution fixture: one deferred identity assignment plus a separate direct control write. Capture full semantic graph snapshots immediately before and after plain, target-traced, and exact-snapshot settlement calls. An independent analyzer derives node type/attribute and edge existence/attribute changes from those raw snapshots. Attribute each changed field only to a unique progressed event whose touched IDs contain that object; otherwise mark it ambiguous or uncovered. Non-progress events must not be credited with semantic changes. Reconcile attributed fields to the independently derived exact graph delta.

This is an external reconstruction baseline. It does not add native per-event before-images, establish ordered attribution when multiple progressed events overlap within one settlement, or prove causal necessity. Preserve those ambiguities as failed/unknown outcomes.

## Gates

1. Lock runner, analyzer, protocol, graph/rewrite/substrate/PyO3 sources, Python wrapper, native extension, and build manifest before capture.
2. Use three distinct worker PIDs and verify all locked inputs before and after each worker.
3. Require ordinary, target-traced, and exact snapshot-delta closures to agree on status and progress steps for each fixture.
4. Independently reconcile every reported attributed field with the before/after graph delta; require no changed fields to be silently omitted or multiply attributed.
5. Record unassignable overlap as explicit ambiguity; never choose a writer based on its known fixture role.

## Claim limits

Passing shows that event identity and target sets can support value attribution for these small fixtures when settlement deltas have an unambiguous progressed writer. It does not establish per-firing attribution for general settlements, candidate diagnosis, open-ended repair, natural-task frequency, or performance. Per-event native before-images remain a separate implementation and overhead gate.
