# COW value-shard write-amplification v6 preregistration

Date: 2026-10-06

## Question

Does the current 64-shard value index copy too many unrelated value entries on a branch's first mutation, and what shard count balances fork-write latency, copied entries, and memory?

## Arms and workload

Profile `CowShardedMap<Value, RoaringBitmap, S>` with `S ∈ {64, 128, 256, 512}` and N = 7,164, 16,384, and 50,771 distinct integer keys, each mapping to a singleton bitmap. Run 21 repetitions per fresh worker. Compare:

- **COW:** shallow clone, remove the selected key from the cloned bitmap/map, verify branch miss and unchanged parent/sibling hit.
- **Eager:** deep copy the complete map, perform the same deletion, and verify identical results.

Measure clone, first mutation, and clone-plus-mutation separately. Before each COW write, capture structural copy estimates (root references and entries in the selected value shard). Record shard occupancy, RSS/high-water snapshots before and after fixture construction, and source/binary locks. Each shard-count/size/arm runs in its own process to isolate memory observations.

## Gates and limits

All value queries, deletion outcomes, and parent/sibling isolation must pass. Report timing and estimated clone work separately; RSS is page-granular and is not an allocator-exact measure. This is a direct value-map component study, not an end-to-end Graph/Substrate result. Select no new default from this study alone; apply any candidate shard count to the full graph mutation panel and measure closure and memory before promotion.
