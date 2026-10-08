# CAN grid boundary-width scaling v1 preregistration (2026-09-29)

## Question

On a synthetic family with known narrow separators, how do graph extraction, min-fill ordering, and exact junction-tree MAP vary with vertex count and separator width? This extends the fixed-width ladder result by varying both axes.

## Workload and independent oracle

Generate binary pairwise CAN models on `q × m` rectangular grids, with column-major node ids, deterministic seeded quarter-step unary and pair weights, vertical within-column edges, and horizontal same-row edges. Use `q ∈ {1,2,3,4,5,6}`, `m ∈ {32,128,512}`, and three fixed replicates per cell (54 fresh workers). The declared column interface has q variables; the expected path-decomposition width is q (bag size q+1) for this family.

The oracle is a separately coded min-sum dynamic program over the `2^q` assignments to each column, enumerating predecessor/current pairs. Require exact runtime graph extraction parity and energy agreement for junction-tree inference under both generic min-fill and a fixed column-major elimination order. Measure graph extraction, min-fill ordering, both exact inference calls, oracle operations, Python traced peak allocation, and process peak RSS separately. No timing claim is inferred from a correctness gate.

## Lock and gates

Lock this protocol, runner, `can_junction_tree.py`, `graph_treewidth.py`, native library, and native build record before running. Reject stale native builds. Require 54 complete workers; three replicates in every cell; expected width/bag size; exact extraction; and both MAP energies within `1e-8` of the independent oracle. Keep all raw workers and environment/provenance in JSON. No source changes are made for the measurement.

## Claim boundary

This estimates the exact-inference envelope on one synthetic grid family with an exposed q-variable separator. It does not measure whether natural task graphs admit these cuts, frame discovery cost, other factor arities, or general cognitive capability. The expected state-space dependence is exponential in q and linear in m for the independent oracle; any observed engine timing is descriptive finite-range evidence, not a complexity proof.

The first runner invocation failed before starting any workers because an absolute-path launch omitted the repository root from Python imports. The failure and path-only correction are documented in the [v1.1 harness amendment](CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_1_AMENDMENT_20260929.md); the original v1 lock is retained and no v1 capture exists. The complete v1.1 run found that the min-fill heuristic overestimates known grid width at q=5/6; the correction is documented in the [v1.2 gate amendment](CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_2_AMENDMENT_20260929.md). V1.2 uses a fresh lock, checks the known-width column order, and records min-fill overestimation as an outcome.

```sh
python3 evaluation/substrate_capability/can_grid_boundary_width_scale_v1.py --lock
python3 evaluation/substrate_capability/can_grid_boundary_width_scale_v1.py
python3 evaluation/substrate_capability/analyze_can_grid_boundary_width_scale_v1.py
```
