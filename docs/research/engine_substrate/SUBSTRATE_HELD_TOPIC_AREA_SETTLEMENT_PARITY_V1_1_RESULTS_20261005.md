# Held-topic area-settlement structural parity v1.1: results

Date: 2026-10-05  
Status: v1.1 raw fingerprint gate failed; **superseded by v1.2 semantic parity**. The v1.1 fingerprint did not normalize serialized graph references and included execution-time metadata.

## Findings

All nine fresh workers completed seven turns and retained stable source fingerprints. The ID-independent fingerprint fixture checks passed: ID permutation preserved the fingerprint, while node attribute, edge direction, type, attribute, or multiplicity changes altered it.

The original v1.1 analyzer failed structural parity from turn two onward. Follow-up inspection identified two fingerprint defects: `__nid__` and numeric ID references embedded in attributes were treated as ordinary values, and `SystemModel.ts` / `SystemModel.runtime_s` were included despite varying across executions. The captured node and edge counts and replies matched. A read-only foreign-snapshot trace found identical inputs, reconstructed enumeration labels, and model outputs under hash seeds 0, 1, 2, and 3. The uninstrumented fixed-seed capture retained raw-digest differences, but reference-aware final fingerprints matched after timing-field exclusion. The decisive per-turn confirmation is the source-locked v1.2 comparison.

## Interpretation

The v1.1 raw digest did not establish a semantic graph difference. The v1.2 reference-aware per-turn fingerprint passes across arms and repeated workers. Retain the v1.1 capture as evidence that serialized-ID references and runtime metadata must be normalized; use v1.2 as the current parity result.

## Next gate

The baseline repeatability and full-settlement semantic parity gates have passed for this workload. Proceed to the finite response-priority/residual-continuation gate described in [v1.2 results](SUBSTRATE_HELD_TOPIC_AREA_SETTLEMENT_PARITY_V1_2_RESULTS_20261006.md).

Artifacts: [v1.1 protocol](SUBSTRATE_HELD_TOPIC_AREA_SETTLEMENT_PARITY_V1_1_PREREG_20261005.md), [capture](../../../evaluation/reports/held_topic_area_settlement_parity_v1_1_20261005/capture.json.gz), [analysis](../../../evaluation/reports/held_topic_area_settlement_parity_v1_1_analysis_20261005.json), [v1 results](SUBSTRATE_HELD_TOPIC_AREA_SETTLEMENT_PARITY_V1_RESULTS_20261005.md).
