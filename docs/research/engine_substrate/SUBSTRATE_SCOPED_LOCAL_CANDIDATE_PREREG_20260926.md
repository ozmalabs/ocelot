# Scoped local-candidate prototype preregistration

**ID:** `SUBSTRATE_SCOPED_LOCAL_CANDIDATE_20260926`  
**Question:** can scoped matching avoid enumerating every typed edge once per frame while preserving the monolithic matcher’s binding order and rule effects?

## Proposed admissible path

Use a specialized candidate source only when a rule has exactly one match edge, distinct source/target variables, and the graph has never deleted any edge (`edge_delete_generation == 0`). Edge slots are allocated monotonically before the first deletion; the freelist is global and can reuse a slot across edge types, so a type-local version alone is insufficient. For each owned node, enumerate typed outgoing edges with the source variable seeded and typed incoming edges with the target variable seeded. Collect and deduplicate complete bindings; sort by EdgeIdx (which then follows `edges_by_type` insertion order); then visit/apply in that same order as the ordinary full matcher. Keep post-match scope filtering. Every other rule/history shape uses the current full-match/filter implementation.

The optimization claims only *candidate enumeration pruning*. It does not claim that edge-list maintenance, rule-order changes, multi-edge joins, or high-boundary frames are addressed. Deleted/reinserted edge types deliberately fall back because free-list reuse breaks the EdgeIdx/order equivalence.

## Locked confirmation matrix

1. Rerun chain/tree/star topology settlement at N={8,16,32,64}, five repeats, event/full arms, full state projections, owner notifications, and omitted-notification controls. Capture to v3 artifacts; never overwrite v1/v2.
2. Include an order-sensitive single-edge fixture with multiple progressing matches targeting the same attr, verifying optimized binding order and exact final state against full closure.
3. Include a deletion/reinsertion control (including a deletion of another edge type followed by reuse); verify the global deletion generation makes the optimized path ineligible and fallback parity is exact.
4. Include a two-edge-rule control; verify it takes the fallback path and matches the prior scoped/full oracle.
5. Record path selection counters (optimized/fallback), candidate/Term counters, source/native/build provenance, and independent analysis. Timing is descriptive; counts and parity are primary.

## Gates and claim boundary

All event/full states and progress outcomes match; notifications cover every changed owner; omission controls retain selected stale projections; order-sensitive fixture matches exactly; deleted-type and multi-edge controls demonstrate fallback; path-selection and global counters reconcile. The generated topologies do not establish the prevalence of the admissible condition in natural workloads. Any unsupported case falling through is by design, not evidence of general optimization coverage.
