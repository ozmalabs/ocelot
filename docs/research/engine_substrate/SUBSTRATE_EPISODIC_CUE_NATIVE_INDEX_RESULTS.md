# Native exact-cue attribute index: results

**Run:** `substrate-episodic-cue-native-index-20260925-v2`, with its [frozen lock](SUBSTRATE_EPISODIC_CUE_NATIVE_INDEX_LOCK_V2_20260925.json). V1 was rejected during development because its manifest dropped a required Argmax iterator variable; it loaded no retrieval rule and produced no scored result. V2 retained that variable, replaced only the predicate and source, and passed all checks. No checked-in seed or engine implementation changed.

## What was compared

Three isolated runtime variants were run on exact-key unique and two-event collision workloads at N=6/24/78/192, with two independent writer/checkpoint replicates per cell and fresh control/audit readers (48 cells total): checked-in baseline; request-time `Count(Filter(...))` after omitting the global pair rule; and request-time native `NodesWhere(Episode,cue_key,request.cue_key)` for both ambiguity count and Argmax retrieval, with the attribute index redeclared after checkpoint load.

All variants returned the expected event identity, one recalled candidate, recalled provenance, `not_observed`, and expected confidence (0.85 unique, 0.5 collision). The index was active only in the indexed variant, including after load. The experiment preserves the earlier caveat: both prototypes omit persistent baseline collision marks and establish response-level parity only.

## Results at N=192

| Workload | Variant | Median query tick | Candidate tests | Where evaluations | Total term evaluations | Retrieval-rule term evaluations |
|---|---:|---:|---:|---:|---:|---:|
| Unique | Baseline | 12.26 ms | 75,278 | 73,729 | 380,833 | 1,972 |
| Unique | Request count | 0.762 ms | 1,166 | 385 | 14,127 | 3,906 |
| Unique | Native index | 0.674 ms | 1,166 | 385 | 11,247 | 1,026 |
| Collision | Baseline | 11.67 ms | 74,511 | 72,966 | 377,050 | 2,009 |
| Collision | Request count | 0.738 ms | 1,167 | 386 | 14,162 | 3,941 |
| Collision | Native index | 0.696 ms | 1,167 | 386 | 11,284 | 1,063 |

Compared with request-count, the index left candidate tests and where evaluations exactly unchanged. It removed Filter-term evaluations, reduced retrieval-rule term evaluations by about 73% and total term evaluations by about 20%, while median wall time improved by about 12% (unique) and 6% (collision). The indexed exact lookup therefore works, but it does not remove the remaining rule-matcher traversal. At N=192 that traversal is 196–197 retrieval-rule candidate tests per query, consistent with enumerating the whole Episode population.

## Tractability and capability implications

The graph already has a maintained `(node_type, attr_key, value)` index, and `NodesWhere` uses it when declared. The index is derived in-memory state: this experiment explicitly redeclared it after `WorldAdapter.load`, which rebuilt it from the restored Episode attributes. The general adapter does not currently declare this memory-specific index automatically, and no seed-level declaration contract was added.

This is concrete support for one capability claim: exact keyed retrieval can use native indexed attribute lookup with correct fresh-process reconstruction on the measured synthetic cases. It also exposes the next engine gap: index use in the Term evaluator does not prune the rule's match-edge candidate enumeration. A follow-up should add or evaluate an indexed join path for the retrieval match itself, with the request cue bound before episode enumeration, then measure matching candidates and graph update semantics. It must account for duplicate cue values, Episode insertion/deletion/attribute changes, checkpoint rebuild, multiple agents/substrates, and all current closure/error paths.

This evidence is local to exact episodic retrieval, N≤192, two replicates. It does not demonstrate cheap cuts on natural tasks, general inference, scaling to millions of nodes, or tractability of rung 3/4 learning.

## Artifacts

- [Preregistration and amendment](SUBSTRATE_EPISODIC_CUE_NATIVE_INDEX_PREREG_20260925.md)
- [Raw run](../../../evaluation/reports/substrate_episodic_cue_native_index_20260925.json)
- [Independent analysis](../../../evaluation/reports/substrate_episodic_cue_native_index_analysis_20260925.json)
- [Harness](../../../scripts/substrate_episodic_cue_native_index.py) and [analyzer](../../../scripts/analyze_substrate_episodic_cue_native_index.py)
- Previous pair-scan optimization evidence: [results](SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_RESULTS.md)
