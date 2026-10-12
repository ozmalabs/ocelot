# CAN cross-frame mutation matrix — preregistration

**State:** pilot protocol frozen before execution. This extends caller-notified event propagation; it does not test automatic native notifications.

## Question and hypotheses

Does an explicit affected-frame queue continue to match a full frame scan after cross-frame edge changes, node-field changes, and node lifecycle changes on the authored 3-state CAN rule?

**H1:** for all registered size/mutation cells, event execution and full round-robin rescan reach identical graph-state projections, both settle under the cap, and an independent final-graph local-update oracle reports zero residual. Every registered mutation must change at least one state or active-node projection. **H2:** the omitted-notification controls for cross-frame edge insertion, node birth, and node deletion at N=8 leave detectable residual. An H2 miss is reported as a control failure, not excluded.

## Frozen matrix

- Base sizes N ∈ {8, 16, 32}, frame size 4; one deterministic path instance per cell; 3-state CAN update rule only.
- Mutations: cross-frame edge insertion, deletion, and weight replacement; external-field write; identity-field write; birth of a new node in a new frame connected across the boundary; deletion of the boundary-adjacent node; and a mixed edge-weight plus external-field write.
- One fresh matched event/reference pair per size and mutation (24 cells). Caller notification frames are derived mechanically from the changed node/edge endpoints and the pre-mutation edge set, then recorded.
- Omitted-notification negative controls for insertion, birth, and deletion at N=8.
- Initial and resumed closure cap: 100,000 progressing applications per condition. A cap exit is inconclusive and fails H1.

## Procedure and decision rule

Settle the paired graphs to equal initial fixed points. Apply the same mutation to each copy. The event queue receives the listed initial frame notifications and enqueues source frames when a changed target frame can affect their local update. The reference rescans all active frames round-robin. Compare active-node identities/states and deleted-node tombstones, then recompute every active node's expected state from final node fields and causal edges in a separate analyzer.

H1 passes only if all 24 pairs complete, match exactly, have zero independently recomputed residual, and the mutation changes state or active-node projection. H2 passes only if each N=8 omitted-notification control has positive independently recomputed residual and disagrees with the corresponding full scan. No runtime or work advantage is required; progress and frame-turn counts are descriptive only.

## Scope and provenance

The runner must save complete state projections, active-node/frame maps, final fields/weights, per-frame work, error/cap statuses, source/seed/native hashes, engine source match, and exact cell set. This is one authored path topology and one native update rule. Even a pass does not establish natural cut locality, broad effect semantics, asynchronous basin equivalence, or automatic native writer-to-frame notification.
