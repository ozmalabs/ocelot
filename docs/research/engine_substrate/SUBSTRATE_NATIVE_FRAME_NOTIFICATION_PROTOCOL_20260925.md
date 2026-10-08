# Native frame notification protocol

**Status:** design and evaluation contract. No native frame-notification result is claimed yet.

**Prototype update (2026-09-25):** Rust/PyO3 exposes `run_rules_delta_report`, an opt-in mutation-site observer, `run_rules_snapshot_delta_report`, an exact graph-content oracle, and `run_rules_scoped_delta_report`, a scoped settlement/report path. Eight direct effect fixtures and one deferred `TrackIdentity` fixture matched the oracle; four ownership/lifecycle fixtures returned expected Microtheory IDs, including a deleted owner root. A cross-owner scoped write returned both owner IDs. At 64–2,048 sparse edge matches, caller-visible observer reporting cost about 3× ordinary settlement. These APIs return direct owner Microtheories, not dependency-component frames; scoped settlement flags deferred queues but does not drain them. See [`SUBSTRATE_RULE_GRAPH_DELTA_REPORT_OVERHEAD_RESULTS.md`](SUBSTRATE_RULE_GRAPH_DELTA_REPORT_OVERHEAD_RESULTS.md).

## Question

Can the Rust substrate derive which runtime-owned frames must be revisited after native rule effects, and can scheduling only those frames reach the same settled graph as a full fixpoint?

The existing mechanisms answer adjacent questions. `Substrate::dirty_by_writeset` marks dependent rules from declared rule read/write sets inside global closure. `run_rules_scoped` restricts matching to one caller-selected Microtheory and returns a progress count. The Bigville dynamic-link study derives frames from graph state and uses a Python caller-maintained queue. None of these exposes a native effect-to-frame notification stream.

## Contract to evaluate

The first native API should be additive and opt-in. For one settlement call it should return:

- the ordinary closure status and progress counters;
- the set of affected frame IDs, deduplicated and stable-sorted for reproducibility;
- a completeness flag and explicit reason codes for effects whose write support is broader than a finite frame set.

Notification means **may need reevaluation**, not that a frame definitely contains a newly true match. Over-approximation is acceptable; under-approximation is a semantic failure. A caller can schedule the reported frames and carry unvisited notifications across bounded settlement calls.

### Required mutation coverage

1. **Edge insert, delete, and attribute replacement:** include endpoint owners and frames whose rules read that edge type. Insert/delete can alter connectivity and ownership-derived partition membership; the frame map must be refreshed or invalidated when the partition's dependency edges change.
2. **Node attribute write:** include the node's current owner frame and any frames with rules that read the written attribute through shared evidence.
3. **Node insert/delete:** include former/current incident-edge endpoint owners; invalidate partition membership when the node or ownership edge changes. A deleted node ID may no longer resolve, so capture its frame and incident endpoints before deletion.
4. **ReplaceValue:** cover the old node, new node, and all incoming-edge sources whose edges are rewired.
5. **Deferred effects** (`FbSample`, `TrackIdentity`, `NetCollapse`, rule patches/edits): notification is emitted after the queued operation drains and its actual writes are known. Queueing alone is not a complete notification.
6. **Unbounded or opaque writes** (`writes_any`, external reads, unsupported host callbacks): report global invalidation or `complete=false`; never silently return an empty set.

The API must preserve default `run_rules` behavior and should not force a full graph snapshot on the ordinary path. Any observer cost is measured separately from settlement cost.

## Evaluation protocol

### Fixture and arms

Reuse the runtime-derived Bigville fixture from `SUBSTRATE_BIGVILLE_RUNTIME_PARTITION_DYNAMIC_LINKS_PREREG_20260925.md`: 100 authored residents, 100 components of five Concepts, and ring/star/seeded-random connected cross-frame links. Freeze source revision, generated seed manifest, dependency extraction, and effect program before each run.

Run at least five fresh-process paired replicates per topology and mutation schedule. Compare:

- **Full oracle:** existing global fixpoint after each mutation.
- **Native notification:** collect returned frame IDs and settle only those frames, carrying residual notifications until independently verified fixed point.
- **Caller queue control:** existing Python queue with the same intended affected frames.
- **Omission controls:** suppress one required category at a time (evidence edge, topology update, node birth/death, deferred write) and verify the independent full-graph residual detects stale state.

Mutation schedule: add cross-frame links, change link weights across the threshold in both directions, delete links, reinsert links, add/delete an owned node, update shared evidence, and trigger each supported deferred effect family that can be represented in the fixture. Each checkpoint starts from an identical graph snapshot per arm.

### Correctness gates

- Native-notification and full-oracle settled projections are byte-identical at every checkpoint.
- An independent evaluator recomputes the full-graph residual and finds zero for both settled arms.
- Every omission control yields positive residual for its targeted mutation category; otherwise that category's fixture is not sensitive and cannot support a coverage claim.
- Notification completeness is true only for effect families actually executed and audited. Unsupported/opaque effects must force global invalidation or explicitly lower completeness.
- Frame ownership and partition invalidation agree with a fresh independent reconstruction after topology and lifecycle changes.

### Cost measures

Record notification generation time, frames reported, false-positive frame visits, frame settlement time, candidate bindings, Term evaluations, graph mutations, full-oracle cost, peak memory, and API overhead. Report settlement and mutation/notification costs separately. Use medians and paired ratios with all replicate values; do not extrapolate CPU scaling from the 100-frame fixture.

## Implementation sequence

1. **Direct graph effects: initial gate passed.** Eight deterministic fixtures cover edge/node insertions and deletions, node deletion with an incident edge, attr writes, ReplaceValue rewiring, and conditional/idempotent writes. Expand to multiple matches, attr replacement collisions, no-op paths, and rule retraction.
2. Extend parity coverage to deferred effects by comparing graph-state diffs around each drain. Include framebuffer samples, identity tracking, net collapse, and rule patch/edit effects where fixtures are available.
3. Validate ownership mapping against runtime-derived Bigville partitions and dynamic ownership/topology changes. Current report IDs are Microtheories; group them into the workload's dependency-component frame IDs.
4. Drive an event queue from `run_rules_scoped_delta_report`, comparing full closure, caller-seeded event closure, native owner notifications, and omission controls. Treat deferred queues as global invalidations until their drains report concrete targets.
5. Run the locked paired protocol above. Promote to an optimization only after semantic parity, omission sensitivity, full residual checks, and end-to-end cost gates pass.

## Known limits

This protocol does not establish that natural tasks admit small separators, that the current frame hierarchy minimizes inference width, or that rung-three/four induction is tractable. It measures whether one existing rule workload can notify and settle affected runtime frames correctly and economically. Generalization requires held-out workloads and dynamic partition-learning measurements.
