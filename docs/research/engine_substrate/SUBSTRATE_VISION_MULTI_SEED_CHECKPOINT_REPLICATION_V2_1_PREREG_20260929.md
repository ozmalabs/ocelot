# Vision substrate multi-seed checkpoint replication v2.1 preregistration (2026-09-29)

## Question

Do independently adapted root-scoped visual graph states reproduce the checkpoint construction and validation contract used by v2.0 on three new initial seeds?

## Fixed procedure

- New seeds: `20260938`, `20260939`, `20260940`. Do not replace a seed that fails.
- For each seed, call the same locked `build_pair(seed, root_scoped=True)` builder. Develop each Retina for exactly 3,000 calls, igniting one cell every fifth call; restore the configured ON/OFF plasticity rate; calibrate the lateral pathway and require nonzero gain; adapt with exactly 2,000 paired `grating_ensemble` presentations from `default_rng(seed+701)`, using identical frames for both sheets; then freeze all learning parameters.
- Require each adaptation presentation to settle to `fixed_point` or `repeated_graph_state` within 1,600,000 cumulative progress. Preserve complete per-presentation progress, passes, and termination class.
- Save each checkpoint immediately with source, topology, calibration, channel activity, schedule, and exact prepared graph digest. Use a new v2.1 checkpoint directory and output manifest; v2.0 artifacts remain unchanged.

## Integrity and interpretation

Lock the protocol, builder, analyzer, v1.4 substrate inputs, engine provenance, and runtime platform. Require a 20-second source-stability interval before building, verify each saved graph digest, and retain invalid seeds as failed replications. This expands seed sensitivity from three to six checkpoints when joined with v2.0; it does not establish population representativeness, natural-task recognition, frame discovery, or scaling.

