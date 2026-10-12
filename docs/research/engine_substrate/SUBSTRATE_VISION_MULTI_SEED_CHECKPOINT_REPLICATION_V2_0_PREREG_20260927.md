# Vision substrate multi-seed checkpoint replication v2.0 preregistration

## Question
Do the prepared-state response and termination patterns from v1.9/v1.9.1 recur across independently initialized and adapted graph states?

## Design
Create prepared checkpoints for seeds `20260935`, `20260936`, and `20260937`, each under the v1.7/v1.9 root-scoped adaptation schedule. Per seed: build the same two-sheet fixture; independently develop each Retina for exactly 3,000 calls using `ignite_k=1` every fifth call; restore the initial plasticity rates; calibrate and freeze lateral weights; perform exactly 2,000 paired presentations from `grating_ensemble(wA, rng)` with `rng=default_rng(seed+701)` and identical frames on A and B; then freeze all learning parameters as in v1.7. Each presentation must settle to `fixed_point` or `repeated_graph_state` within the cumulative progress cap of 1,600,000. Record development clocks, calibration gains, ON/OFF channel activity, adaptation closure counts/work, topology, source lock, and exact prepared graph digest.

The response panel will be run later from each saved checkpoint using the v1.9 contract and stimulus schedule. Each checkpoint is an independent adapted state; root-scoped adaptation is held constant, so this study measures seed sensitivity rather than scope sensitivity.

## Integrity and analysis
Lock this protocol, runner, v1.4 substrate inputs, native engine provenance, and platform before adaptation. Save a checkpoint per seed immediately after validation so interrupted runs can resume without repeating completed seeds. Verify checkpoint digest on load. Report any invalid seed as a failed replication; do not silently replace it. Compare seeds on calibration, channel activity, adaptation work, and subsequent phase/orientation response and termination classes. Three seeds are a pilot estimate of variability, not a population guarantee.

## Claim boundary
This is a small 4x4-per-sheet vision fixture. It tests repeatability across initial conditions, not natural-task frame locality, large-graph scaling, or general tractability.
