# Runtime-generated exact-inference scale v1 (2026-09-29)

## Result

All 48 fresh workers passed all nine gates: coverage, expected graph counts, closure completion and terminal probe, width at most 2, exact live extraction, independent variable-elimination and direct-energy parity, valid states/no mutation, and stable source/native locks. The benchmark constructs the model in native graph storage, settles it with current native CAN rules, extracts the post-closure network, and compares min-fill JT MAP with independently coded table-based VE in natural node order.

| N | Topology | Mode | Pairs | Width | Native closure (ms) | Extract (ms) | JT MAP (ms) | VE oracle (ms) | JT traced Python peak (KiB) | Worker RSS high-water (MiB) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | Path | 2-state | 31 | 1 | 15 | 0.51 | 2.91 | 0.41 | 41 | 38 |
| 32 | Path | 3-state | 31 | 1 | 15 | 0.47 | 4.37 | 0.90 | 50 | 37 |
| 32 | Banded-2 | 2-state | 61 | 2 | 24 | 0.68 | 4.79 | 0.99 | 49 | 38 |
| 32 | Banded-2 | 3-state | 61 | 2 | 19 | 0.71 | 11.66 | 2.11 | 85 | 38 |
| 64 | Path | 2-state | 63 | 1 | 130 | 0.96 | 5.27 | 1.11 | 76 | 39 |
| 64 | Path | 3-state | 63 | 1 | 110 | 0.90 | 8.78 | 1.55 | 96 | 39 |
| 64 | Banded-2 | 2-state | 125 | 2 | 127 | 1.35 | 9.85 | 1.90 | 92 | 39 |
| 64 | Banded-2 | 3-state | 125 | 2 | 150 | 1.37 | 24.26 | 4.52 | 167 | 39 |
| 128 | Path | 2-state | 127 | 1 | 1,975 | 1.71 | 10.70 | 2.39 | 151 | 43 |
| 128 | Path | 3-state | 127 | 1 | 972 | 1.82 | 18.45 | 3.67 | 191 | 41 |
| 128 | Banded-2 | 2-state | 253 | 2 | 1,508 | 2.65 | 18.76 | 4.44 | 183 | 43 |
| 128 | Banded-2 | 3-state | 253 | 2 | 1,817 | 2.63 | 48.46 | 9.78 | 338 | 42 |
| 256 | Path | 2-state | 255 | 1 | 14,661 | 3.48 | 22.37 | 7.05 | 301 | 62 |
| 256 | Path | 3-state | 255 | 1 | 8,753 | 3.47 | 36.80 | 8.78 | 380 | 49 |
| 256 | Banded-2 | 2-state | 509 | 2 | 21,519 | 5.47 | 38.73 | 11.76 | 365 | 59 |
| 256 | Banded-2 | 3-state | 509 | 2 | 16,519 | 5.44 | 100.72 | 22.70 | 665 | 54 |

Each value is the median of three fresh workers. Wall times vary across cells; the raw JSON retains all worker-level values. RSS is a whole-worker high-water mark, while the traced peak applies only to the JT call.

## Interpretation

Exact inference scales close to linearly over this fixed-width interval: from N=32 to 256, the 2-state path JT median rises about 7.7x for 8x as many nodes; the banded-2 3-state median rises about 8.6x. The per-call Python allocation grows by a similar factor. Width remains 1 or 2, and all returned energies match the independent oracle. This is positive evidence for the bounded-width operating regime through N=256 in these fixtures.

The same run exposes a larger engine cost. Median native closure grows from about 15–24 ms at N=32 to 8.8–21.5 seconds at N=256, while the reported progress count stays in the single digits to low teens. Therefore closure wall time, not exact MAP, dominates this end-to-end path and grows far faster than the node count in the measured range. The benchmark does not collect matcher/evaluation counters, so the source of that growth is not yet identified. The next engine gate should pair uninstrumented timing with a separate identical scale-audit run and per-rule attribution; optimize only after that attribution is verified against state parity.

## Limits

The workloads are authored synthetic path and bandwidth-2 graphs, with random quantized factors. They are stored and settled in the current native graph engine, but the topology is fixture-generated rather than learned or sampled from natural tasks. The panel supports fixed-width exact inference scaling through 256 nodes; it does not show natural frame prevalence, learned partition quality, larger-scale memory behavior, or general end-to-end tractability. Process RSS includes Python/native imports and VE oracle work, so it is not an isolated native graph-memory measure.

## Reproducibility

- [Preregistration](CAN_RUNTIME_GENERATED_EXACT_INFERENCE_SCALE_V1_PREREG_20260929.md)
- [Runner](../../../evaluation/substrate_capability/can_runtime_generated_exact_inference_scale_v1.py)
- [Input lock](../../../evaluation/substrate_capability/can_runtime_generated_exact_inference_scale_v1_lock_20260929.json)
- [Raw capture](../../../evaluation/reports/can_runtime_generated_exact_inference_scale_v1_20260929.json)
