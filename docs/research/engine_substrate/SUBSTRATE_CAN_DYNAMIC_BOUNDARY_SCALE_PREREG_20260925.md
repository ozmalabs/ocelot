# CAN dynamic boundary wakeup scale pilot — preregistration

**State:** pilot protocol frozen before the expanded run. This continues the four-mutation mechanism probe; it is not a native notification or natural-workload test.

## Question and hypothesis

When settlement is scoped to four-node frames, does the existing caller-notified event queue continue to reach the same full-graph fixed point as round-robin full rescan as the number of frames grows from 2 to 16?

**H1:** for every registered size/mutation pair, event settlement and full rescan produce identical ordered state vectors and both have zero residual under an independent local-update predicate. The omitted-initial-notification negative control must leave detectable residual on the edge-insertion case.

**Primary measures:** exact final-state agreement and independent zero-residual status. **Cost measures:** event/full progress applications and frame turns/rounds. Costs are descriptive for this one host/run; no timing superiority threshold is set.

## Frozen workload

- Sizes: N ∈ {8, 16, 32, 64}; frame size 4; path coupling; 3-state CAN update rule only.
- Mutations at the first frame boundary: cross-frame edge insertion, edge deletion, edge-weight replacement, and external-field change at node 0.
- The insertion cell also runs a negative control with no initial direct-frame notification.
- One deterministic instance per size/mutation. The same constructed model is copied into event and full-rescan arms.
- Initial and resumed closure cap: 100,000 progress applications. Any cap exit is recorded as inconclusive and counts as a primary failure.

## Procedure and decision rule

Settle both copies to equal initial states. Apply the registered mutation to each. The event arm is explicitly told which directly affected frame(s), then wakes causal predecessors when a frame's committed state changes. The reference scans every frame in round-robin order until a no-progress pass. Compare exact state vectors and independently evaluate the local CAN update equation on every final node. Do not tune notification rules or mutation weights after looking at outcomes.

Pass the pilot only if all 16 event arms settle under the cap, match the corresponding reference state exactly, and have zero independent residual; all full-rescan references must also settle and have zero residual. The insertion negative control must disagree with the full rescan and retain positive residual at all four sizes. Otherwise preserve each failure and narrow the claim.

## Provenance and limits

The runner must record harness, seed, relevant Rust-source and loaded-extension hashes, source/build provenance, environment, and all per-cell states/counters. The existing runner's event queue is Python and receives caller-supplied initial notifications. Even a full pass establishes only scale robustness of this explicit notification/propagation mechanism on path CAN models; it does not establish automatic native write-to-frame notification, general frame discovery, high-treewidth behavior, or task-distribution locality.
