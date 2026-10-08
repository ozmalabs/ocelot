# Concurrent CoW degree and target-placement v1 preregistration

**Question:** How do branch write costs and retained allocations vary with graph degree profile and with clustered, spread, low-out-degree, or high-out-degree target selection?

## Design

- Reuse the native global `System` allocator meter and matched thread-only plus same-backend fork/drop/no-write controls from the prior concurrent mutation panel.
- Cross deterministic degree profiles `{path, regular-four, star, grid}`, graph sizes `{10,000, 50,000}`, target policy `{clustered, evenly spread, lowest out-degree first, highest out-degree first}`, write density `{1%, 10%}`, backend `{shared snapshot, eager copy}`, and three counterbalanced paired repetitions. Fanout is fixed at 16 to focus this panel on degree/placement rather than repeat the fanout sweep.
- Each base node has an initialized marker attribute. Every target receives a unique 128-byte surface value and one new outgoing branch edge to the branch-local node. Policies select exactly `ceil(N*density)` distinct node IDs; report the selected out-degree distribution (min/median/max and total) in every receipt.
- For path/star/grid, edges are deterministic as in v1. Regular-four uses four directed cyclic successor edges per node, yielding uniform out-degree four. All rule/graph construction is complete before measurement baselines.
- Half the concurrent branches are cancelled while half remain live. Preserve source/eager branch-ID parity, primary and later-fork isolation, matched fork/drop controls, and exact zero mutation-adjusted post-drop allocator residual.

## Gates and scope

All 384 rows (4 profiles × 2 sizes × 4 target policies × 2 densities × 2 backends × 3 repetitions) must pass full write/edge validation, surviving-sibling checks, allocator/cancellation gates, and exact paired branch-ID parity. Report full-wave time, total live allocation, mutation-adjusted incremental bytes above the fork-only control, after-cancel bytes, and selected degree summaries. This is a synthetic one-host graph study; it does not claim a natural workload distribution, asymptotic bound, or serving behavior.
