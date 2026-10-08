# Ternary exact-inference higher-width envelope v1 results (2026-10-02)

## Outcome

All 18 source-locked ternary workers completed without timeout or memory failure. They pass exact extraction, certified width, independent factor-table oracle and returned-state parity, state-domain, no-mutation, and source-lock gates. The current-native binary comparison matches native binary, solver, generator, worker, seed, node count, and edge count. Independent analysis passes 16/16 checks.

| q | Family | Ternary certified JT | Binary certified JT | Ternary / binary | Ternary traced peak | Min-fill width on grid |
|---:|---|---:|---:|---:|---:|---|
| 6 | Grid | 4.52 s | 276 ms | 16.35× | 17.0 MiB | 7 |
| 6 | Sparse partial q-tree | 631 ms | 58.5 ms | 10.79× | 0.89 MiB | 6 |
| 7 | Grid | 14.15 s | 592 ms | 23.92× | 47.3 MiB | 9 |
| 7 | Sparse partial q-tree | 1.74 s | 93.8 ms | 18.60× | 1.53 MiB | 7 |
| 8 | Grid | 44.06 s | 1.24 s | 35.55× | 153 MiB | 10, 11, 12 |
| 8 | Sparse partial q-tree | 2.59 s | 108 ms | 24.02× | 3.17 MiB | 8 |

The q=6 ternary control reproduces the prior domain-cost panel within ordinary runtime variation. Increasing certified width from q=6 to q=8 raises ternary certified JT time 9.75× on the grid and 4.10× on the q-tree. The matched binary-to-ternary penalty also grows with width. At q=8, min-fill's grid width varies from 10 to 12 even though the certificate proves width 8; min-fill-order JT has a 67.0 s median there, versus 44.1 s under the certificate order. Thus conservative width estimation can reject solvable cases, and a poor estimated order can cost more than the exact certified order.

## Limits

This is one host, N=120, three replicates, two synthetic binary-pairwise graph families, and widths up to 8. It measures exact 3-state MAP, not marginal inference, natural task widths, learned frame discovery, or end-to-end application cost. The 44 s q=8 grid time and 153 MiB traced peak mark a practical boundary for this Python JT path on this host; they do not imply a universal cutoff. Ternary q=9 and connected task-derived factors remain open.

## Reproduction artifacts

- [Preregistration](CAN_TERNARY_HIGH_WIDTH_INFERENCE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/can_ternary_high_width_inference_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_can_ternary_high_width_inference_v1.py)
- [Source lock](../../../evaluation/substrate_capability/can_ternary_high_width_inference_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/can_ternary_high_width_inference_v1_20261002.json)
- [Analysis](../../../evaluation/reports/can_ternary_high_width_inference_v1_20261002_analysis.json)
