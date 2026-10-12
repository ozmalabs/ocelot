# Thoughtexperiment candidate branch scaling v1 results

## Outcome

The current-source capture and independent analyzer pass across 12 fresh
processes, four sparse-path sizes, and 120 branch episodes. At every size the
live/no-op branch returns `true`, the threshold-edit branch returns `false`,
and the primary graph digest plus active-rule UID, revision, and content hash
remain unchanged. Source hashes match the frozen lock in every worker.

## Phase timings

Medians pool 30 branch episodes per size (three processes × five paired
repetitions × two arms). Values are wall-clock milliseconds; node counts
include the nine-node self-change seed graph.

| Decoy path | Total nodes / edges | Graph construction | Shared-page fork | Rule install | Task input | Rule closure | Targeted read |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 9 / 8 | 0.004 ms | 0.055 ms | 0.050 ms | 0.023 ms | 0.233 ms | 0.004 ms |
| 1,024 | 1,033 / 1,031 | 3.775 ms | 0.046 ms | 0.059 ms | 0.019 ms | 0.189 ms | 0.003 ms |
| 8,192 | 8,201 / 8,199 | 35.004 ms | 0.043 ms | 0.055 ms | 0.024 ms | 0.136 ms | 0.002 ms |
| 32,768 | 32,777 / 32,775 | 154.522 ms | 0.046 ms | 0.054 ms | 0.039 ms | 0.138 ms | 0.003 ms |

From 1,024 to 32,768 decoys (31.8× more nodes), shared-page fork is nearly
flat in these measurements (45.5 to 45.7 μs median), rule closure is 0.189
to 0.138 ms, and targeted read is 2.8 to 2.6 μs. Creating the three task
nodes and two edges rises from 19.2 to 39.1 μs. Building the background path
is the size-dependent cost: 3.78 to 154.52 ms. The 0-node arm has a higher
closure median than larger arms, so the panel does not show monotone closure
growth; these sub-millisecond timings are sensitive to runtime and scheduler
noise. RSS snapshots vary and are retained only in the raw capture, not used
for a memory-scaling claim.

## Interpretation and limits

This is evidence that the measured shared-page fork and a fixed-aperture
candidate rehearsal do not scale with total node count in proportion to a
simple whole-graph copy over this one sparse path topology. It does not
establish asymptotic complexity or prove hyp:cheap-cut: the task is deliberately
isolated from decoys, only one rule family runs, and there are four sizes on
one host. It omits full candidate-pool growth, dense/high-degree graphs,
changing frame apertures, concurrent branch pressure, reclamation, and
real-task distributions. Follow-up should vary separator width and aperture
independently, include decoy edges incident to matched task variables, and
measure uninstrumented RSS/PSS/peak memory on at least one second topology.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_CANDIDATE_BRANCH_SCALING_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_candidate_branch_scaling_v1.py)
- [Fixture](../../../evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1_fixture_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_candidate_branch_scaling_v1_20261005.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_candidate_branch_scaling_v1_analysis_20261005.json)
