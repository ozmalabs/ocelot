# Omniglot graph-Term one-shot recognition v1.2 results (2026-09-29)

## Integrity and task

A source- and dataset-locked run completed 100 deterministic 20-way episodes on 20 alphabets from the local Omniglot evaluation split. Each episode uses one writer's exemplar for 20 character classes and a different writer's query for each class: 2,000 labeled queries per recognizer. All three graph-Term systems used identical episode keys and fresh Substrates. Feature preparation was shared. The independent analyzer passes 6/6 gates, including exact current-source/data/runtime lock match, complete paired episode matrix, writer separation, prediction and accuracy reconstruction, and stability across the run.

The run is training-free: it compares a query against the one available exemplar per candidate using an existing substrate Term. It does not learn weights or mint a task concept. Recognition uses the graph-resident Term evaluator with the host-side Omniglot trajectory adapter.

## Accuracy

| Recognizer | Correct | Accuracy | 95% alphabet-cluster bootstrap interval | Median per-episode wall time |
|---|---:|---:|---:|---:|
| Ordered DTW (`DtwTo`) | 1,055 / 2,000 | 52.75% | 48.95–56.77% | 12.46 ms |
| Point-set distance (`PointSetDist`) | 1,336 / 2,000 | 66.80% | 62.55–71.10% | 18.40 ms |
| Deformable fit (`DeformDist`) | 1,085 / 2,000 | 54.25% | 49.04–59.88% | 18.11 ms |
| Uniform random control | 88–111 / 2,000 | 4.40–5.55% | chance = 5% | — |

The point-set recognizer exceeds ordered DTW by 14.05 percentage points (paired alphabet-cluster bootstrap 95% interval: 8.89–19.66 points) and deformable fit by 12.55 points (9.71–15.00 points). The intervals resample the 20 alphabets, not individual queries or episodes. This establishes meaningful above-chance performance for this task and the relative advantage of the point-set Term on this fixed panel.

## Cost and limits

Median episode wall/CPU times include construction of the candidate graph and all 20 graph-Term queries; trajectory parsing/resampling is timed separately at 1.51 s for 3,514 unique trajectories. The append-only capture completed in 6.01 s wall / 5.98 s process CPU including source-stability hashing. Peak RSS was about 56 MB. An earlier recorder rewrote the growing JSON capture after every episode; its 249.7 s end-to-end time was dominated by capture serialization. That v1 result is retained as exploratory; do not compare its total wall time to v1.2. Its per-episode scores match exactly, and its method timing excluded recorder writes.

The outcome is specific to one existing adapter, three pre-existing Terms, 20-way one-shot matching, and one Omniglot evaluation split. Twenty alphabets are the resampling units; repeated episodes within an alphabet do not create new task families. This does not establish semantic scene recognition, robust transfer to other alphabets/corpora, concept acquisition, the rate at which induction is invoked, or broad learning economics. The pre-existing Omniglot contrastive-verdict task is a counterexample: its focused host-side classifier lost to its global control (64.0% vs 80.5%). The two outcomes concern different algorithms and must remain separate.

## Next evaluation

Freeze the current Terms and test a preregistered transfer matrix across disjoint alphabet subsets and writer pairs, then a distinct independently sourced task family. Add controlled exemplar-count and trajectory-length scaling with exact prediction parity, per-Term operation counts, and memory/latency costs. Do not use these results to claim the substrate learns new visual concepts; they measure application of held structure.

## Reproduction artifacts

- [v1.2 preregistration and recorder amendment](SUBSTRATE_OMNIGLOT_ONE_SHOT_CURRENT_V1_2_PREREG_20260929.md)
- [Capture program](../../../scripts/substrate_omniglot_one_shot_current_v1_2.py)
- [Independent analyzer](../../../scripts/analyze_substrate_omniglot_one_shot_current_v1_2.py)
- [Append-only capture](../../../evaluation/reports/omniglot_one_shot_current_v1_2_20260929_raw.jsonl)
- [Analysis and per-alphabet outcomes](../../../evaluation/reports/omniglot_one_shot_current_v1_2_20260929_analysis.json)
- [Source, runtime, and dataset lock](../../../evaluation/substrate_capability/omniglot_one_shot_current_v1_2_20260929_lock.json)
- [Exploratory v1 capture](../../../evaluation/reports/omniglot_one_shot_current_v1_20260929_raw.json) and [failed lock recheck](../../../evaluation/reports/omniglot_one_shot_current_v1_1_20260929_analysis.json)
- [Separate negative contrastive-verdict result](SUBSTRATE_OMNIGLOT_CONTRASTIVE_CURRENT_V1_RESULTS_20260928.md)
