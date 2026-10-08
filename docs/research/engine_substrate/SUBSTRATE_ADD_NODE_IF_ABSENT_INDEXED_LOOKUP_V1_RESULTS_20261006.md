# Indexed `AddNodeIfAbsent` lookup v1 results

Date: 2026-10-06  
Status: synthetic mechanism gate passes for the measured cases; no general or live-route speedup claim.

## Result

The fast path preserves the reference graph and closure progress across all 72 synthetic workers, all five timing replicates per cell, all separate trace workers, and the authored semantic controls that were run. The analyzer's 19 integrity checks pass. The controlled ladder varies candidate population `N ∈ {512, 4,096, 7,164, 16,384}` and lookup count `M ∈ {1, 15, 64}`. Across the 12 cells, median paired warm-closure reductions range from 44.9% to 98.5%. For the route-shaped `N=7,164, M=15` cell, reference closure is 1.472 ms, indexed warm closure is 0.095 ms, and index build plus closure is 0.645 ms. The reference diagnostic records 107,397 typed candidates and attribute comparisons; the indexed diagnostic records zero of each and 15 index queries. For `N=16,384, M=64`, reference closure is 13.362 ms, warm indexed closure 0.230 ms, and build plus closure 2.023 ms. These are native measurements on the locked host and controlled graph shape, not a complexity proof.

## Branch cost and applicability

The current attribute-index state makes Thoughtexperiment forks much slower after index construction. At `N=7,164, M=15`, median fork time is 0.102 ms for the reference graph and 0.320 ms for the indexed graph. At `N=16,384, M=64`, it is 0.220 ms versus 3.007 ms. This is consistent with eager cloning of the index map, rather than COW sharing. Thus the warm lookup gain is real for this synthetic path, but the current representation is a poor fit for frequent forks. First-use costs also dominate a single lookup in several cells: at `N=4,096, M=1`, build plus closure is 0.379 ms versus 0.130 ms reference.

The full-seed unknown-word route has exact graph, reply, and task-oracle parity in all five pairs, but its timing contrast is invalid. A separate source-matched boot probe confirms `Concept.name` is absent immediately after `WorldAdapter(seeds=())` and present after loading the same 731 seeds used by the route; the post-boot graph contains 10,794 Concepts. Therefore the nominal reference and indexed arms both already use the fast path. The observed live medians (190.678 ms reference versus 209.979 ms nominal indexed) are reported only as a confounded observation and must not be attributed to the implementation. See the [presence probe protocol and result record](SUBSTRATE_ADD_NODE_IF_ABSENT_LIVE_INDEX_PRESENCE_V1_PREREG_20261006.md) and [probe output](../../../evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006/live_index_presence_probe.json).

## Measurement boundaries

- The semantic controls that passed cover first-witness behavior after deletion and NodeID reuse, indexed-attribute mutation, subset matching, case-varied values, and empty-attribute fallback. Heterogeneous values, retyping, and all duplicate-request combinations remain unmeasured.
- The capture records graph and progress parity and fork parent isolation. It does not establish index lifecycle correctness for every graph mutation.
- RSS deltas are too coarse to estimate index memory at the smaller sizes; process high-water RSS is dominated by the interpreter and fixture. Treat memory as unmeasured.
- The live task route is one authored workload. Its timing cannot estimate natural-task prevalence or general operating cost.

## Decision and next steps

Keep this implementation as an experimental mechanism, not a default optimization for branch-heavy sessions. The next engine gate should make index state COW-friendly or otherwise avoid cloning it on fork, then repeat the fork/build/mutation/closure panel with a precise memory measure. Add the remaining semantic controls before broadening the fast-path claim. For live applicability, construct a source-locked reference arm that genuinely lacks the index while preserving the same seed graph and task semantics; otherwise report only post-boot mechanism counters and parity. Then replicate across another production-derived `AddNodeIfAbsent` family. This result addresses one scan hotspot; it does not show that learned frames have cheap cuts, that frame locality is prevalent, or that rung 3–4 induction is tractable.

## Artifacts

- [Preregistration](SUBSTRATE_ADD_NODE_IF_ABSENT_INDEXED_LOOKUP_V1_PREREG_20261006.md)
- [Amendment](SUBSTRATE_ADD_NODE_IF_ABSENT_INDEXED_LOOKUP_V1_AMENDMENT_20261006.md)
- [Runner](../../../scripts/substrate_add_node_if_absent_indexed_lookup_v1_20261006.py)
- [Analyzer](../../../scripts/analyze_substrate_add_node_if_absent_indexed_lookup_v1_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/add_node_if_absent_indexed_lookup_v1_20261006_lock.json)
- [Capture](../../../evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006/capture.json.gz)
- [Analysis](../../../evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006/analysis.json)
- [Live index presence probe runner](../../../scripts/probe_substrate_add_node_if_absent_live_index_presence_v1_20261006.py)
- [Probe source lock](../../../evaluation/substrate_capability/add_node_if_absent_live_index_presence_v1_20261006_lock.json)
