# Ordered typed-node COW index v5 preregistration

Date: 2026-10-06

## Question

Can `by_type` support order-preserving O(1) deletion/retyping with COW branch state, without changing the typed-node order used by matching and first-witness selection?

## Design

Replace each contiguous typed-node vector with a COW-paged ordered vector of optional NodeIDs and a live count. Maintain a global COW-paged NodeID-to-position vector. Deletion/retyping clears one position; insertion appends. Compact a typed population only when it has at least 64 tombstones occupying at least half its ordered slots, then remap live positions. Iteration filters tombstones in order. NodeID reuse must append a new membership at the end, matching the prior `retain` then `push` behavior.

## Measurement and controls

Repeat the v4 source-locked 7,164/16,384/50,771, 21-repetition set/insert/delete/retype panel and eager/shared arms. In addition to attribute-index parity and parent/sibling isolation, require exact `nodes_of_type` order for every arm. A deterministic 128-node control deletes the first 64 members to trigger compaction, re-inserts the 64 freed IDs in freelist order, and checks exact order, indexed values, and parent/sibling isolation. The Rust capture records timings and Boolean gates; the independent analyzer summarizes paired fork-plus-write medians and their v4 comparison.

## Gate and limits

All source-lock, exact-index, typed-order, reuse, compaction, and isolation checks must pass. Report deletion/retype scaling and any set/insert change separately. This graph-level synthetic panel does not establish whole-Substrate closure cost, allocator memory, natural-task prevalence, or general tractability.
