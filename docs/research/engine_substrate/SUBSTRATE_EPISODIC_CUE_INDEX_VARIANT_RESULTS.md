# Episodic cue collision query variant: results

**Run:** `substrate-episodic-cue-index-variant-20260925-v3`, frozen in [lock](SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_LOCK_V3_20260925.json). The pre-locked v1/v2 development attempts are retained in the raw artifact directory; v1 applied the prototype transform to both arms, and v2 failed only on strict floating-point equality. V3 changes the confidence assertion to 1e-12 and passes all preregistered gates. No checked-in seed or engine source was changed.

## Design and scope

An isolated runtime manifest variant removes `episodic_mark_overlapping_cues_for_conservative_completion`. At recall time it counts recorded episodes with the requested exact cue and caps emitted confidence at 0.5 when more than one match exists. Baseline and prototype share event data and retrieval ranking. We ran unique-cue and one two-event collision workloads at N=6/24/78/192, two fresh writer/checkpoint replicates per cell, and fresh uninstrumented and instrumented readers (32 cells total).

Both variants returned the exact expected event identity, `recalled` provenance, `not_observed`, and the expected confidence (0.85 unique; 0.5 collision). The baseline persisted collision caps/status on both episodes. The prototype left those episode attributes unchanged and moved collision uncertainty to the recall result. Therefore the result establishes response-level parity for these inputs, not graph-state or persistence semantics parity.

## Cost results

At N=192, the baseline's global pair rule produced 74,112 candidate tests on unique cues and 73,344 on the collision workload. The request-count prototype produced zero pair-rule tests. Total audited candidate tests fell from 75,278 to 1,166 (98.45%) for unique cues and from 74,511 to 1,167 (98.43%) for collisions. Total term-evaluation counts fell 96.29% and 96.24%, respectively.

Uninstrumented median query tick at N=192 fell from 11.98 ms to 0.72 ms on unique cues (0.060× baseline) and from 12.31 ms to 0.80 ms on collisions (0.065×). With only two replicates these are descriptive comparisons, not stable latency estimates. At N=6, latency ratios were 0.97 and 0.96, respectively; the benefit becomes visible as the pair-scan workload grows. Instrumented timing carries substantial overhead and is not used as the speed estimate.

## Interpretation and remaining work

This isolates a concrete avoidable quadratic cost in the current episodic query path. It does not prove the architecture's full operating regime tractable: the prototype's Count/Filter and existing Argmax retrieval still inspect episode records, and the measured upper size is only 192. The next optimization should use an exact cue-to-episode index (with duplicate handling and checkpoint recovery) so both ambiguity lookup and candidate retrieval avoid a full scan. It must preserve the baseline's persistent collision marks or explicitly revise that state contract, then test insertions, removals, duplicate groups, restart, and concurrent query/update semantics.

The experiment says nothing about natural task locality, frame decomposition, general graph inference, rung 3 dimension induction, rung 4 primitive minting, or learning frequency. It sharpens the substrate capability map only for exact-key episodic retrieval and rule-cost attribution. It does not change the tractability assessment's open status for learning new structure.

## Artifacts

- Preregistration and disclosed amendments: [protocol](SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_PREREG_20260925.md)
- Frozen v3 inputs: [lock](SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_LOCK_V3_20260925.json)
- Paired raw measurements: [raw JSON](../../../evaluation/reports/substrate_episodic_cue_index_variant_v3_20260925.json)
- Independent checks and paired analysis: [analysis JSON](../../../evaluation/reports/substrate_episodic_cue_index_variant_v3_analysis_20260925.json)
- Harness: [experiment script](../../../scripts/substrate_episodic_cue_index_variant.py)
- Analyzer: [analysis script](../../../scripts/analyze_substrate_episodic_cue_index_variant.py)
