# Generated hypothesis-pool stress scale v1.2 — results

## Result

The parent-capped, source-locked panel completed all 12 fresh-process runs: size caps 7 and 9, batch and streaming modes, three paired replicates, and 12 fixed unlabeled probes. The corrected independent analyzer passes all 10 checks. Every worker completed the bounded search at `max_size`; no worker hit the 10-second internal limit, 15-second parent timeout, or 10,000-fitting-hypothesis cap. Completed batch/stream pairs have identical hypothesis digests, exploration counts, stop reasons, and finite held-out coverage.

| Size cap | Terms explored | Fitting hypotheses | Median synthesis wall, batch / stream | Median peak RSS, batch / stream | Exact on all four held-outs |
|---:|---:|---:|---:|---:|---:|
| 7 | 8,709 | 147 | 576 / 586 ms | 30,192 / 28,748 KiB | 1 hypothesis in each replicate |
| 9 | 88,069 | 1,306 | 7,143 / 7,036 ms | 71,956 / 53,948 KiB | 2 hypotheses in each replicate |

Moving from size 7 to 9 increases explored terms about 10.1× and wall time about 12.4×. At size 9, streaming lowers process peak RSS by about 25% (approximately 18 MiB) while median wall time is about 1.5% lower. With only three replicates, that small wall difference does not establish a speedup. Process RSS includes interpreter and native setup; the 25% difference is a process-level measurement, not a Rust allocation profile. Both modes preserve exact ordered hypothesis-pool digests, training agreement, and held-out exact-hypothesis counts.

## Interpretation

This strengthens the size-7 result: streaming remains semantically identical through an 88,069-term bounded search and has a measurable memory advantage at that scale, while wall time remains dominated by hypothesis evaluation/registration. The fixed 10-second internal and 15-second external caps were not reached, so this panel identifies no actual incomplete-pool boundary. It measures one arithmetic family, one training anchor, one probe domain, and two odd size caps; it does not establish a general scaling exponent, nor show what happens at the first timeout or memory limit. The next gate should extend the same paired design to size 11 with a stricter parent resource limit and explicit retention of any timeout/error outcomes, then vary anchors/task families before judging the general utility of streaming.

## Reproduction artifacts

- [v1.2 preregistration](SUBSTRATE_GENERATOR_STREAM_SCALE_V1_2_PREREG_20261002.md)
- [runner](../../../evaluation/substrate_capability/substrate_generator_stream_scale_v1_2.py)
- [source lock](../../../evaluation/substrate_capability/substrate_generator_stream_scale_v1_2_lock_20261002.json)
- [raw capture](../../../evaluation/reports/substrate_generator_stream_scale_v1_2_raw_20261002.json)
- [analysis](../../../evaluation/reports/substrate_generator_stream_scale_v1_3_analysis_20261002.json)
- [analyzer](../../../evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_3.py)
