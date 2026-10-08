# Solver-alternative reusable snapshot consumer v1.1 results

Date: 2026-10-01

## Result

The fresh source/native-locked v1.1 panel passes **8/8 checks** over 20 perturbation × replicate workers, with 20 distinct worker processes and stable pre/post fingerprints. The native CAN `scoped_settle` solver runs on alternatives forked from one shared-graph-pages snapshot. For every cell, reusable-CoW and eager-copy children agree exactly on starting revision, perturbed input, steps, settled Concept states, energy, frustration, coverage, fields, and final graph digest. The primary digest is unchanged, a subsequent snapshot fork retains the baseline digest and fields, and the read-only fork matches the eager base.

Median branch creation is 0.021 ms for reusable CoW and 0.033 ms for eager copy. Median solve time is 0.156 ms and 0.073 ms respectively. These are 20 single-host, sub-millisecond observations on a five-node fixture; they are descriptive and timing noise/setup effects are material. They do not establish a CoW solver speedup. The relevant result is exact consumer compatibility and branch isolation.

## Interpretation and limits

This establishes a solver-alternative consumer for the reusable CoW API, alongside the thoughtexperiment and GenMint candidate-validation consumers. It tests one native CAN solver on a four-concept topology. It does not measure optimality, broad planner behavior, natural task prevalence, concurrent branch behavior, cancellation or reclamation, adoption conflicts, scale, or vLLM-style serving.

The initial v1 capture passed semantic checks but omitted the fork-time observations required by its protocol. It is retained as semantic-only pilot evidence; v1.1 is the complete timing capture and uses separate paths. See [v1.1 preregistration](COW_SOLVER_ALTERNATIVES_SNAPSHOT_V1_1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/cow_solver_alternatives_snapshot_v1_1.py), [analyzer](../../../scripts/analyze_cow_solver_alternatives_snapshot_v1_1.py), [lock](../../../evaluation/substrate_capability/cow_solver_alternatives_snapshot_v1_1_lock_20261001.json), [worker capture](../../../evaluation/reports/cow_solver_alternatives_snapshot_v1_1_workers_20261001.json), and [analysis](../../../evaluation/reports/cow_solver_alternatives_snapshot_v1_1_analysis_20261001.json).
