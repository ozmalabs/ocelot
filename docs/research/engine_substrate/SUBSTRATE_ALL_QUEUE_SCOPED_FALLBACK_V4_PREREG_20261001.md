# Direct insertion-order consumer through the rule matcher v4 preregistration

Date: 2026-10-01

## Question

Can the edge-vector insertion-order difference observed in v2 produce a different rule result when the matcher is forced to enumerate that edge type first?

## Source-grounded design

`TypedGraph::insert_edge` appends a new edge index to the edge-type vector and per-node adjacency vectors. `edges_by_type` returns that vector directly, and the both-unbound matcher path iterates it in order. The rule installer greedily chooses the match edge with minimum current edge-type cardinality; equal-cardinality ties preserve the first declared clause.

Repeat the 27-worker `R={1,8,32}`, `M={1,4,16}` five-queue fixture with distinct `handled_mid` writes and a shared sink. Connect each middle node to the sink with `has_sink`; this makes the `handled_mid` and `has_sink` populations both R×M. Declare `handled_mid` first in the probe rule. The rule installer sees zero `handled_mid` edges at install time and a positive `has_sink` population, so its initial clause is `handled_mid`. Its one-shot guard permits one drain; every matched binding writes its middle NodeID into the shared sink's `selected_mid`, so the final value should equal the last edge in the runtime `handled_mid` order consumed by that matcher. No edge sorting is performed.

Capture direct full, scoped-only, and scoped-plus-fallback states. For each settled arm, independently derive the last `handled_mid` edge target from the returned edge-vector order and check that `selected_mid` names that target. Report whether full and fallback select the same node, whether the selected result follows each arm's insertion order, all prior distinct-write and queue invariants, and exact graph-wire parity.

## Expected invariants

- Every arm reaches the expected fixed point; all prior handled/verified counts and queue totals remain correct.
- In each settled arm, the order probe's selected node equals the target of the last `handled_mid` edge in that arm's graph edge vector.
- Do not require full and fallback to select the same node: disagreement is the primary positive evidence that insertion order is behaviorally observable under direct matcher enumeration.
- Preserve strict graph wire comparison and source/native worker fingerprints.

## Limits

This is an adversarial authored rule with deliberate shared-output conflicts; a positive mismatch establishes possible operational sensitivity, not natural prevalence. A null mismatch in this exact fixture does not prove all match ordering is insensitive. It does not establish general scheduler equivalence, frame correctness, or a complexity law.
