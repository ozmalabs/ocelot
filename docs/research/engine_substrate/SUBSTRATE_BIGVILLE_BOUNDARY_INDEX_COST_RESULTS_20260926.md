# Bigville Boundary-Index Cost Probe Results (2026-09-26)

## Result

Nine fresh worker processes measured the authored Bigville graph with 100 runtime-derived frames of five Concepts each. Three replicates covered ring, star, and random-connected inter-frame link topologies. Across seven lifecycle checkpoints, all workers confirmed their live `has_concept` owner map and directed causal-edge projection, then compared the incrementally updated boundary index with a full rebuild. Workers fail closed on any mismatch. The independent supplementary analyzer passes 16 integrity checks, including the locked worker schedule, exact owner sizes, expected edge transitions, 31 timing samples per operation, and the registered source/native hashes.

| Topology | Full graph build + initial partition (median) | Owner discovery (median) | Live edge extraction at baseline (median) | Boundary rebuild at baseline / 100 links (median) | Incremental update for insert / delete 1/3 (median) |
|---|---:|---:|---:|---:|---:|
| Ring | 56.0 ms | 0.320 ms | 0.340 ms | 0.292 / 0.555 ms | 0.260 / 0.184 ms |
| Star | 55.7 ms | 0.325 ms | 0.344 ms | 0.287 / 0.541 ms | 0.253 / 0.164 ms |
| Random connected | 55.3 ms | 0.325 ms | 0.337 ms | 0.291 / 0.557 ms | 0.256 / 0.173 ms |

Incremental delete-all takes about 0.060 ms median; reinserting the deleted links takes 0.228–0.233 ms. Reweighting changes graph data but not topology: the boundary index update is a no-op, while a full rebuild still costs about 0.47 ms at 66 links. The boundary-rebuild timer covers index/profile construction over a previously extracted flat edge list; live-edge extraction is timed separately. An end-to-end rebuild estimate is their sum (about 0.63 ms at baseline and 0.93–0.95 ms with 100 links), though the two medians are combined descriptively rather than paired at sample level. The timings are micro-measures on a single host and fixed 500-Concept fixture, not scaling curves or whole-application latency.

Boundary profiles reproduce the prior secondary audit: after insertion all 100 frames carry boundary Concepts; maximum fan-out is 2 (ring), 99 (star), and 6 (random connected). After deletion, 99, 67, and 84 frames remain active. The three topologies therefore have similar index timings despite very different fan-out in this small fixture, but this cannot establish asymptotic independence from topology or graph size.

## Interpretation and limits

This closes the missing measurement of owner discovery and boundary-index construction/update cost for one authored graph. The index update itself is sub-millisecond at this scale and cheaper than reconstructing the full index. However, both methods operate on a captured 500-node owner projection; the reported incremental timer does not include mutation event delivery, production queueing, rule closure, or concurrent frame execution. Initial graph construction and initial partition discovery are combined in the 55 ms timing. No partition-learning algorithm is measured, and no scaling beyond 100 frames is established. The fixture's frames are derived from disconnected baseline causal components, then cross-links are injected; it is not evidence that natural task graphs have cheap cuts.

## Artifacts

- Preregistered protocol: [`SUBSTRATE_BIGVILLE_BOUNDARY_INDEX_COST_PREREG_20260926.md`](SUBSTRATE_BIGVILLE_BOUNDARY_INDEX_COST_PREREG_20260926.md)
- Runner: [`substrate_bigville_boundary_index_cost_v1.py`](../../../scripts/substrate_bigville_boundary_index_cost_v1.py)
- Locked raw capture: [`substrate_bigville_boundary_index_cost_v1_20260926.json`](../../../evaluation/reports/substrate_bigville_boundary_index_cost_v1_20260926.json)
- Original registered analyzer (expects an un-emitted convenience field; retained unchanged): [`analyze_substrate_bigville_boundary_index_cost_v1.py`](../../../scripts/analyze_substrate_bigville_boundary_index_cost_v1.py)
- Supplementary analyzer: [`analyze_substrate_bigville_boundary_index_cost_v1a.py`](../../../scripts/analyze_substrate_bigville_boundary_index_cost_v1a.py)
- Supplementary analysis: [`substrate_bigville_boundary_index_cost_v1a_analysis_20260926.json`](../../../evaluation/reports/substrate_bigville_boundary_index_cost_v1a_analysis_20260926.json)
- Source lock: [`bigville_boundary_index_cost_lock_20260926.json`](../../../evaluation/substrate_capability/bigville_boundary_index_cost_lock_20260926.json)
