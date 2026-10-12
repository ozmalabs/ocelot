# Generated hypothesis-pool stress scale v1.3 — results

## Result

The source-locked panel records all 12 scheduled processes: size caps 9 and 11, batch and streaming modes, and three replicates. The corrected independent analyzer passes all 10 provenance, schedule, measurement, and explicit-outcome checks. All six size-9 controls complete within the 12-second internal timeout, 16-second parent timeout, and 2 GiB address-space ceiling. All six size-11 workers return at the 12-second internal timeout; none reaches the parent timeout or address-space limit. Thus the configured search is complete at size 9 and incomplete at size 11 in every replicate.

| Size cap / mode | Search completion | Median terms explored | Median fitting hypotheses returned | Median synthesis wall / CPU | Median peak RSS |
|---|---:|---:|---:|---:|---:|
| 9 batch | 3/3 | 88,069 | 1,306 | 7.21 / 7.20 s | 71,544 KiB |
| 9 stream | 3/3 | 88,069 | 1,306 | 7.04 / 7.04 s | 53,608 KiB |
| 11 batch | 0/3 | 123,158 | 2,834 | 12.10 / 12.10 s | 337,860 KiB |
| 11 stream | 0/3 | 138,486 | 4,019 | 12.03 / 12.03 s | 99,484 KiB |

At size 9, ordered hypothesis digests, candidate counts, and held-out exact coverage match exactly between modes. At size 11, batch and streaming both report an internal timeout, but their incomplete pools differ and cannot be treated as semantically equivalent. Every partial pool nevertheless contains three hypotheses that match all four finite held-out values; because the search is incomplete, this establishes retention in the returned partial pool only, not adequate coverage or identification of the target over the bounded grammar.

Streaming reduced size-11 median process peak RSS by about 71% (approximately 233 MiB) and examined about 12% more terms before the shared timeout. The batch implementation first materializes a whole size cohort and only checks the timeout while registering terms; streaming registers terms as they are generated. This timing/memory behavior is consistent with the observed difference. The result is not a general 71% memory claim: it is one task, one anchor, one grammar, one input family, and a 2 GiB virtual-address-space ceiling. No worker reached that ceiling, so this is a CPU-time/incomplete-cohort boundary, not a memory-limit result.

## Interpretation

This is direct evidence that generated-pool completeness becomes a material resource boundary as the grammar grows: the same bounded search completes at size 9 in about 7 seconds and fails to exhaust size 11 under 12 seconds. Streaming substantially reduces peak process RSS in the incomplete regime and advances farther through generation, but its timed-out pool is different from batch's. This makes `halt_reason`, explored count, and completeness mandatory outputs for any downstream selector; a target-like hypothesis in a partial pool cannot certify the space. The experiment does not estimate natural task prevalence, prove asymptotic complexity, establish incremental continuation across time slices, or show general task-family behavior.

## Reproduction artifacts

- [v1.3 preregistration](SUBSTRATE_GENERATOR_STREAM_SCALE_V1_3_PREREG_20261002.md)
- [runner](../../../evaluation/substrate_capability/substrate_generator_stream_scale_v1_3.py)
- [source lock](../../../evaluation/substrate_capability/substrate_generator_stream_scale_v1_3_lock_20261002.json)
- [raw capture](../../../evaluation/reports/substrate_generator_stream_scale_v1_3_raw_20261002.json)
- [analysis](../../../evaluation/reports/substrate_generator_stream_scale_v1_4_analysis_20261002.json)
- [analyzer](../../../evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_4.py)
