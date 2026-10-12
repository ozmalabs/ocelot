# Generated hypothesis-pool streaming scale v1.1 — results

## Result

The source-locked paired panel completed all 54 fresh-process rows: three replicates across expression-size caps 5/6/7, probe counts 4/8/12, and batch/streaming collection modes. The corrected independent analysis passes all 10 preregistered integrity and semantic gates. No worker timed out or hit the 10,000-hypothesis cap. Batch and streaming modes had identical stop reasons, explored/distinct counts, ordered hypothesis digests, training-consistent pool sizes, and held-out exact-hypothesis coverage in all 27 pairs.

| Expression size | Probe environments | Explored terms | Training-consistent pool | Median synthesis wall (batch → stream) | Peak RSS ratio (stream / batch) | Held-out-exact hypothesis |
|---|---:|---:|---:|---:|---:|---|
| 5 | 4 / 8 / 12 | 945 | 19 / 20 / 20 | 19.8 / 35.7 / 50.3 ms → 19.9 / 34.7 / 48.2 ms | 0.99 / 1.02 / 0.98 | absent in all pools |
| 6 | 4 / 8 / 12 | 945 | 19 / 20 / 20 | 20.1 / 36.1 / 49.2 ms → 21.4 / 33.9 / 49.5 ms | 0.97 / 0.98 / 1.01 | absent in all pools |
| 7 | 4 / 8 / 12 | 8,629 / 8,709 / 8,709 | 120 / 140 / 147 | 224 / 392 / 583 ms → 254 / 396 / 582 ms | 0.92 / 0.93 / 0.96 | one per pool in all 9 replicates |

Sizes 5 and 6 explore the same 945 terms because this grammar's binary expression trees add odd node counts; raising the ceiling from 5 to 6 introduces no additional expression cohort. At size 7, exploration rises about 9.2× and median synthesis wall rises to 0.22–0.58 s. Expanding the unlabeled probe prefix from 4 to 12 increases the size-7 distinct pool from 120 to 147 behaviors, while the tested held-out-exact behavior remains present in every replicate. The exact held-out expression in the captured pool is `(n * ((n + 1) / 2))`; this is finite held-out agreement, not proof of equivalence on all inputs.

Streaming does not show a stable end-to-end wall-time advantage here: paired median ratios range from 0.94× to 1.13× across the size-7 probe cells. Process peak RSS is lower for the size-7 streaming arms by about 4–8%, but remains a coarse high-water measurement; interpreter/native startup is included and no Rust allocation attribution is available. The small size-5/6 RSS differences change sign across probe counts.

## Interpretation

The useful new evidence is a same-semantics batch/stream comparison at a single-anchor version space: streaming preserved every hypothesis and target-coverage result, while slightly reducing process peak RSS at the largest measured size. It did not produce a reliable wall-time gain. This is an approximately 9,000-term, subsecond, single-family result. It does not establish scaling beyond size 7, prevent the larger eager-cohort memory spike, establish incremental search, or show that the substrate can choose or invent a grammar. The previous three-family scale ladder reached triangular ceiling 8, so v1.1 adds the controlled representation comparison at a different one-anchor training regime rather than extending that earlier ladder.

The v1 attempt failed before producing a capture because its audit code read tagged numeric signatures as scalars; partial worker outputs were not retained. In v1.1, the locked analyzer initially failed because it expected a different native-path provenance field. The post-capture v1.2 analyzer uses the actual `native_path` field, passes 10/10 checks, and preserves the raw capture and source lock. See the [analysis amendment](SUBSTRATE_GENERATOR_STREAM_SCALE_V1_2_ANALYSIS_AMENDMENT_20261002.md).

## Reproduction artifacts

- [v1.1 preregistration](SUBSTRATE_GENERATOR_STREAM_SCALE_V1_1_PREREG_20261002.md)
- [runner](../../../evaluation/substrate_capability/substrate_generator_stream_scale_v1_1.py)
- [source lock](../../../evaluation/substrate_capability/substrate_generator_stream_scale_v1_1_lock_20261002.json)
- [raw capture](../../../evaluation/reports/substrate_generator_stream_scale_v1_1_raw_20261002.json)
- [corrected analysis](../../../evaluation/reports/substrate_generator_stream_scale_v1_2_analysis_20261002.json)
- [corrected analyzer](../../../evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_2.py)
