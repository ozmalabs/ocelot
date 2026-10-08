# Query Index Reuse Across Thought-Experiment Branches v1.1 Results

**Result:** reusing one immutable prediction index becomes substantially faster than recomputing predictions when several hypothesis branches share the same generated pool. Cached and uncached branches produced identical query paths and survivor sets, and every hidden target remained among the survivors.

| Branches per batch | Median cached batch | Median uncached batch | Paired median speedup | Cached matrix heap | Target still present | Unique target recovered |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 59.36 ms | 39.87 ms | 0.74× | 642,367 bytes | 15/15 | 13/15 |
| 5 | 80.75 ms | 199.70 ms | 2.70× | 642,367 bytes | 75/75 | 64/75 |
| 20 | 127.67 ms | 823.10 ms | 6.53× | 642,367 bytes | 300/300 | 280/300 |

Each anchor had a complete generated pool (218–662 hypotheses). The cached arm evaluates each hypothesis/query pair once per batch: a median 5,798 selector predictions. The uncached arm performs a median 5,906, 29,690, and 118,551 selector predictions at batch sizes 1, 5, and 20. Target-response evaluations are additional and common to both arms. The cache build takes about 37–41 ms. It loses for one branch, but by a five-branch batch it amortizes and reaches 6.53× lower median wall time at 20 branches. Its measured Python heap estimate is about 0.64 MB per pool; native term memory and process RSS are excluded.

All branch results match exactly between cached and uncached routes, and all hidden target hypotheses remain in their final survivor sets. Only 357/390 simulated branches ended with a unique target. The rest retain near-equal hypotheses under the absolute `1e-9` matching tolerance despite exhausting the 13-candidate family. This is a real ambiguity outcome, not a cache mismatch; the initial analyzer incorrectly required singleton recovery. The [amended analysis](../../../evaluation/reports/substrate_query_index_branch_reuse_v1_1_20260930_analysis.json) corrects that gate and passes 432 integrity checks. See the [amendment](SUBSTRATE_QUERY_INDEX_BRANCH_REUSE_V1_1_AMENDMENT_20260930.md).

This is a serial in-process hypothesis-branch benchmark. Its synthetic target model returns labels by evaluating a sampled hypothesis. It does not fork or mutate the Rust `Substrate` graph, establish concurrent safety, or prove end-to-end CoW gains. It does show a bounded use case for shared immutable read state with branch-local active sets: repeated counterfactual query experiments amortize the prediction matrix. The next gate is to connect the same reuse pattern to the actual thoughtexperiment branch API and measure total RSS, concurrent branches, and residual collection.

## Evidence

- [Preregistration](SUBSTRATE_QUERY_INDEX_BRANCH_REUSE_V1_PREREG_20260930.md)
- [Analysis amendment](SUBSTRATE_QUERY_INDEX_BRANCH_REUSE_V1_1_AMENDMENT_20260930.md)
- [Source-locked runner](../../../scripts/substrate_query_index_branch_reuse_v1.py)
- [Original validator](../../../scripts/analyze_substrate_query_index_branch_reuse_v1.py) — preserved initial singleton criterion, which failed on tolerance-equivalent hypotheses.
- [Amended analyzer](../../../scripts/analyze_substrate_query_index_branch_reuse_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_query_index_branch_reuse_v1_20260930_lock.json)
- [Raw capture](../../../evaluation/reports/substrate_query_index_branch_reuse_v1_20260930_raw.json)
- [Amended analysis capture](../../../evaluation/reports/substrate_query_index_branch_reuse_v1_1_20260930_analysis.json)
