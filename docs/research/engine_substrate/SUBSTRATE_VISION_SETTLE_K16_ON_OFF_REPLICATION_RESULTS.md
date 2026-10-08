# K=16 settling on/off replication results

**Run:** 2026-09-25. Two new seeds, counterbalanced order, four independently prepared arms. The earlier seed 20260928 remains a separate observation.

## Result

Both new within-seed pairs produced exactly equal full tuning matrices and mean OSI between settling-on and settling-off arms. Seed 20260929 had mean OSI 0.328720; seed 20260930 had 0.307224. No readout weight drift occurred. Independent OSI recomputation and all provenance checks passed.

Over 480 `cell_stats` presentations, settling-on used 90,978 and 90,963 native progress applications; settling-off used 2,848 and 2,849. This is a 96.87% reduction in reported progress applications in each pair. Adaptation counts matched within each seed (2,000 presentations per arm); all tick counts were positive and below the configured budget. The order was on→off for seed 20260929 and off→on for seed 20260930.

The single paired readout timings were 13.15 s versus 3.91 s and 13.35 s versus 3.83 s (on versus off). These four measurements are descriptive only and do not establish a stable speedup. Tick integers report progress counts, not fixed-point or cycle termination reasons.

## Claim boundary

This replicates an exact response-parity/high-settling-work observation across two more initial seeds for one 4×4 lateral-sheet preparation and one orientation-rate readout. Together with the earlier seed, it is three observations, not a prevalence estimate. It does not test learned cortical weights, a task-level objective, other sheet sizes, or other domains. In particular, equal rates here do not establish that settling is unnecessary for every downstream capability.

## Evidence

- [preregistration](SUBSTRATE_VISION_SETTLE_K16_ON_OFF_REPLICATION_PREREG_20260925.md)
- [runner](../../../scripts/substrate_vision_settle_k16_on_off_replication.py)
- [independent analyzer](../../../scripts/analyze_substrate_vision_settle_k16_on_off_replication.py)
- [raw report](../../../evaluation/reports/substrate_vision_settle_k16_on_off_replication_20260925.json)
- [analysis](../../../evaluation/reports/substrate_vision_settle_k16_on_off_replication_analysis_20260925.json)
- [provenance lock](../../../evaluation/substrate_capability/vision_settle_k16_on_off_replication_lock_20260925.json)
