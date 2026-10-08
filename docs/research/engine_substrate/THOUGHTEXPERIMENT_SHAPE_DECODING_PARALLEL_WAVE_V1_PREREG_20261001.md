# Shape-decoding correction parallel thoughtexperiment wave v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does the shared-page throughput advantage measured on recurrence-rule repair transfer to an independent shape-axis correction task?

## Design

Use the existing positive `sd_mint_quantum` `dedup_identity_fix` fixture from `thoughtexperiment_self_correction_copy_comparison_v1.py`, at 100k unrelated linked noise nodes. Compute the baseline collapse model once before timing, then repeat the same read-only correction rehearsal from an unchanged primary. Cross native scoped full-copy vs native scoped shared-graph-page backends, sequential vs threaded waves, and fanout 1/2/4/8; three fresh processes per cell (48 processes). Each branch runs `imagine_and_check_convergence` with the production candidate, horizon 3, two imagination steps, three-observation focus, one-hop aperture, and `record_trace=False` to ensure multiple workers do not append to the same primary.

The independent task oracle requires the candidate to be applicable, `dedup_identity_fix` to be evaluated, and the model-after to converge. Every branch must return the same convergence/residual/conclusion signature. Primary graph/rules/revision must remain exactly stable. Run each fanout/mode/backend in an isolated fresh process; alternate sequential/concurrent and backend order across replicates.

## Gates

- 16 backend/fanout/mode cells × three fresh processes = 48 unique PIDs complete with source/native-binary lock parity.
- All branches converge under the independent shape-axis oracle, are non-inert, apply the expected target-rule repair, and agree semantically across modes/backends.
- Primary graph counts/revision/rules remain unchanged; input observations/noise-chain integrity is retained by the source-locked fixture.
- Report median end-to-end rehearsal wall time, experiments/second, sampled peak ΔPSS/RSS/private-dirty, and per-run signatures.

## Interpretation limits

One authored shape-decoding task and one host; repeated branches share one candidate and task shape. The scoped branch API and branch closure are measured, not autonomous proposal generation or ranking. The 10 ms sampler can miss short peaks. CPU quota and serving-level scheduling are reported if available; results are not general throughput guarantees.
