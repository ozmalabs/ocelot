# CAN rule execution across graph structures — 2026-09-24

## Question and protocol

Does the authored native CAN asynchronous update settle to a mathematically valid fixed point as graph size, coupling sparsity, mode, and weight granularity vary?

[`scripts/substrate_can_structure_envelope.py`](../../../scripts/substrate_can_structure_envelope.py) replayed the seeded CAN rules for 180 draws: sizes 8, 16, and 32; path, bandwidth-2, and complete symmetric coupling graphs; 2-state and 3-state rules; coarse (1.0) and fine (0.25) weight quantization; five deterministic draws per cell. A fixed contiguous frame size of four was used only to count crossing edges; execution was still monolithic. Timings cover `run_rules` only, excluding seed loading and graph construction. For every draw, the same workload was also run on a fresh identical substrate with the existing native `scale_audit` enabled. The instrumentation run matched the uninstrumented progress count and final state; timings reported below remain from the uninstrumented run.

The independent reference does not assume a particular basin. It recomputes every concept’s next state from the generated fields, weights, and native final state using a Python implementation of the seed’s thresholds. A zero-residual state is a fixed point. This is an independent stationarity check, not an energy-optimality or task-quality oracle. The native one-step terminal probe is a separate engine-level quiescence check.

Raw per-draw records, summaries, hashes, command, and runtime environment: [`evaluation/reports/substrate_can_structure_envelope_20260924.json`](../../../evaluation/reports/substrate_can_structure_envelope_20260924.json).

## Results

All 180 runs stayed below the 100,000 progress cap, had zero terminal-probe progress, stayed in the declared state vocabulary, and had zero independent fixed-point residuals.

| Concepts | Graph | Directed coupling edges | Directed edges crossing contiguous 4-node frames | Range of cell median wall time across mode/weight settings |
|---:|---|---:|---:|---:|
| 8 | Path | 14 | 2 | 0.26–0.49 ms |
| 8 | Banded (width 2) | 26 | 6 | 0.28–0.43 ms |
| 8 | Complete | 56 | 32 | 0.20–0.50 ms |
| 16 | Path | 30 | 6 | 1.36–2.21 ms |
| 16 | Banded (width 2) | 58 | 18 | 1.82–2.14 ms |
| 16 | Complete | 240 | 192 | 1.32–1.92 ms |
| 32 | Path | 62 | 14 | 9.99–20.64 ms |
| 32 | Banded (width 2) | 122 | 42 | 11.19–22.03 ms |
| 32 | Complete | 992 | 896 | 8.34–15.61 ms |

Native audit counters, pooled over mode, quantization, and the five draws (median per topology/size group):

| Concepts | Graph | Edge candidates enumerated/tested | Where evaluations | Binding leaves/clones | Effect attr-set attempts | Effect edge-insert attempts |
|---:|---|---:|---:|---:|---:|---:|
| 8 | Path | 940 | 380 | 26 | 8 | 36 |
| 8 | Banded (width 2) | 925 | 450 | 24 | 8 | 30 |
| 8 | Complete | 696 | 486 | 9 | 9 | 0 |
| 16 | Path | 6,552 | 1,555 | 118 | 16 | 202 |
| 16 | Banded (width 2) | 8,334 | 2,154 | 103 | 17 | 172 |
| 16 | Complete | 2,944 | 2,139 | 19 | 19 | 0 |
| 32 | Path | 59,821 | 9,005 | 469 | 32 | 876 |
| 32 | Banded (width 2) | 78,557 | 9,142 | 466 | 34 | 864 |
| 32 | Complete | 14,640 | 11,301 | 37 | 37 | 0 |

The global candidate-enumeration/test and binding-leaf/clone identities reconcile on every draw. These counters cover all active rules loaded from the CAN manifest, not only the two update rules. `effect_edge_insert_attempts` counts attempts across effects and is not a successful-mint count; `effect_attr_set_attempts` is likewise an aggregate and is not a unique-concept count. The rows are operation counts, not wall-time attribution or per-rule traces.

Cell medians use five observations; their ranges above span the four mode/weight cells for each topology and size. These are exploratory timings, not fitted complexity estimates or confidence bounds. The dense cases are not consistently slower in this small run, so edge count alone does not explain the observed runtime; progress counts, binding enumeration, update order, and native indexing need attribution before drawing a scaling conclusion.

## Interpretation and next gate

This supplies stronger evidence than the earlier N=8 replay: correctness is checked against a separate local-update predicate; topology, size, and a simple frame boundary measure are varied; and existing native counters expose some search and effect work. Candidate counts do not align monotonically with graph density in this small suite (the dense topology has fewer enumerated candidates than sparse topologies), so candidate generation, rule guards, and effect paths need per-rule attribution before structural cost can be explained. The audit counters are collected in a separate run and state parity is checked; their instrumentation overhead itself is not measured here.

The experiment still does not execute a partitioned frame hierarchy, test inference factorization, or establish cheap-cut locality. The contiguous partition is a diagnostic counter only; the boundary measure is not treewidth.

Next, add native counters or trace attribution for candidate visits, rule matches, and state writes; repeat sizes and draws in fresh processes with memory measurements; then compare monolithic execution against a partitioned implementation/reference on the sparse cases while injecting omitted cross-frame edges as a negative control. Extend beyond N=32 only after the cost attribution and process-level resource harness are stable.
