# K=16 orientation response under global and Retina-root scope: multi-seed preregistration

Date: 2026-09-27. This is a confirmatory extension of the one-seed K=16 scope gate. It is not a population estimate over vision tasks.

## Question

After identical retinal development and theta adaptation, does replacing the two global `NodesOfType(SUnit)` means in `st_settle` with means over the matched Retina root's `has_sunit` members preserve the complete K=16 orientation response across independent initial seeds?

## Design

Use three independent seeds: 20260931, 20260932, and 20260933. For each seed, construct two fresh 4×4 lateral sheets (`connectivity=8`, `settle=1`, `bubble=0`), one with the authored global rule and one with the benchmark-only root-scoped clone. Tag executable rules in the five vision manifests `hard_realtime` in both arms, but execute every preparation and presentation with unfiltered `run_rules_report(..., detect_cycles=True)`. This holds executor constant and leaves only scope as the intervention.

For each arm, follow the existing preparation: 3,000 retinal-development steps; 2,000 seeded random grating adaptation presentations; pin theta and freeze all learning; then call `cell_stats(key="rate", period=4, K=16)`. Retain complete tuning matrices, per-unit OSI, alive counts, final weights, progress/status counts, root membership, and timings. Run global then scoped for each seed. Save a partial record after each arm.

## Analysis and pass criteria

Independently recompute each unit's OSI from its 12-orientation tuning curve, check all 16 units and exact root membership, and compare global/scoped tuning values within absolute tolerance `1e-10` per seed. Report every seed, not only pooled means. Require all presentations to return a recognized fixed-point or repeated-state status without hitting the native cap, no weight drift during readout, stable source/native fingerprints before and after capture, and complete six-arm records. Exact response parity is a benchmark-specific equivalence result, not proof of equal cost, learned-frame discovery, or general vision capability.

## Claim boundary

This isolates the one-sheet scope substitution under full-rescan semantics. It does not test multi-sheet interactions, settling ablation, default-tick equivalence, natural task success, learned cortical weights, or a scaling advantage. The 4×4 anatomy and three fixed seeds are a small controlled fixture.
