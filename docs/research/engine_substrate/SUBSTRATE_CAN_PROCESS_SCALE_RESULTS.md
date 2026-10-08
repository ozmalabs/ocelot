# CAN fresh-process scale and RSS envelope — 2026-09-24

## Protocol

[`scripts/substrate_can_process_scale.py`](../../../scripts/substrate_can_process_scale.py) launched 66 fresh Python processes over 22 cells, each with three replicates. The shared authored workload builder ran sizes 32/64/128/256 on path and banded-2 graphs, and sizes 32/64/128 on complete graphs; each size/topology was run with both 2-state and 3-state update rules, fixed 0.25 weight granularity, and deterministic seeds. The native audit twin was disabled so peak RSS reflects one workload substrate rather than two. Every worker records exact source/extension/seed hashes, process wall time, engine wall/CPU time, and Linux `ru_maxrss` high-water after import, after setup, and after rule execution.

The engine timing excludes rule/graph construction; RSS is process high-water and therefore includes imports, setup, and execution. This sweep uses **three** fresh-process replicates per cell. These resource readings are high-water marks, not allocator deltas or a component heap profile.

Raw worker records and exact environment: [`evaluation/reports/substrate_can_process_scale_20260924.json`](../../../evaluation/reports/substrate_can_process_scale_20260924.json). Run command:

```bash
PYTHONPATH=/tmp/ocelot-perrule-variants-n4ix6p_4:$PWD python3 scripts/substrate_can_process_scale.py
```

## Results

All 66 workers settled within the 100,000-progress cap, returned zero work on the terminal probe, and had zero independent fixed-point residuals. Per-cell time and RSS ranges below are ranges across the two update modes’ medians; RSS is MiB.

| Concepts | Graph | Directed edges | Engine wall time | RSS after setup | RSS after run |
|---:|---|---:|---:|---:|---:|
| 32 | Path | 62 | 10.04–24.70 ms | 25.1–25.7 | 25.7–26.4 |
| 32 | Banded (width 2) | 122 | 21.40–27.19 ms | 25.3 | 25.9–26.1 |
| 32 | Complete | 992 | 8.43–18.27 ms | 24.9 | 25.5–25.7 |
| 64 | Path | 126 | 86.39–338.46 ms | 25.1–25.3 | 26.2–27.2 |
| 64 | Banded (width 2) | 250 | 162.82–204.44 ms | 24.6–24.9 | 26.2–26.4 |
| 64 | Complete | 4,032 | 125.04–133.02 ms | 25.7–25.9 | 26.2–26.4 |
| 128 | Path | 254 | 1,162.25–1,261.50 ms | 24.8–25.3 | 28.2–31.6 |
| 128 | Banded (width 2) | 506 | 1,354.50–2,129.72 ms | 24.8–25.5 | 29.5–31.3 |
| 128 | Complete | 16,256 | 998.25–2,449.43 ms | 29.1–29.2 | 29.2–29.6 |
| 256 | Path | 510 | 13,720–19,366 ms | 24.6–24.9 | 36.6–45.5 |
| 256 | Banded (width 2) | 1,018 | 19,146–23,171 ms | 25.3–25.7 | 42.5–46.2 |

The refreshed process batch took 267.6 seconds on the recorded Linux/Python environment. In the path family, cell median engine time increases from roughly 1.2 seconds at N=128 to 13.7–19.4 seconds at N=256; banded graphs show a similar increase. The second batch is slower than the first at N=256, especially in 2-state runs, showing substantial host/run variation even with fresh processes. These are measured local curves, not asymptotic fits. Dense cases are only measured to N=128 and again do not show a simple monotone relation between edge count and time. Peak memory rises much less sharply than time over these sizes, but the limited points do not justify extrapolation to 10⁷ nodes or commodity-scale claims.

## Interpretation and next measurement

This establishes an isolated, correctness-checked resource envelope beyond N=32. It also falsifies any casual reading of the earlier sub-millisecond N=8 results as representative of larger graphs. The substantial N=256 runtime jump and inconsistent density ordering make per-rule/per-stage attribution the next priority. RSS has a ~23–24 MiB import-time floor here and is too coarse to isolate graph storage from interpreter/native overhead.

Next: measure memory in a native-only harness or with allocation-level profiling, repeat the high-variance N=128→256 conditions with more seeds, and compare actual partitioned against monolithic execution. No commodity-hardware throughput or cheap-cut claim follows from this sweep.
