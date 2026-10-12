# Omniglot graph-Term recognition scaling v1.2 results (2026-09-29)

## Integrity and design

The confirmatory 2,700-cell factorial reuses the exact 100 episodes from the locked Omniglot v1.2 recognition panel. It crosses 5/10/20 nested candidate classes, 16/32/64 trajectory points, and three graph-Term recognizers. The same query classes, alphabet, and exemplar/query writers are paired across all methods within each condition. All six independent gates pass: complete matrix; capture/lock match; current source, runtime, dataset, and previous-panel hashes; pre/post source stability; episode/writer/prediction integrity; and independent score and candidate-work reconstruction.

Each episode asks one query for every candidate class. The recognition Terms select the best candidate with `Argmax`; the source-derived expected distance-operation count is therefore k² per episode (25/100/400 for k=5/10/20), or 2,500/10,000/40,000 per 100-episode condition. These are counts implied by the Term structure, not measured native operation counters.

## Accuracy and cost

Point-set distance remains well above the corresponding chance baseline in all nine conditions:

| Candidates | Trajectory points | Accuracy | 95% alphabet-cluster interval | Chance | Median worker wall time | p95 |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 16 | 80.4% | 75.4–85.1% | 20% | 0.56 ms | 0.63 ms |
| 5 | 32 | 86.0% | 82.0–89.3% | 20% | 1.06 ms | 1.21 ms |
| 5 | 64 | 85.4% | 82.1–88.4% | 20% | 2.26 ms | 3.44 ms |
| 10 | 16 | 69.9% | 64.1–75.0% | 10% | 1.23 ms | 1.36 ms |
| 10 | 32 | 75.4% | 70.9–79.6% | 10% | 2.47 ms | 3.73 ms |
| 10 | 64 | 76.0% | 72.0–79.7% | 10% | 5.78 ms | 8.56 ms |
| 20 | 16 | 60.5% | 54.2–66.3% | 5% | 2.92 ms | 3.66 ms |
| 20 | 32 | 66.7% | 62.0–71.4% | 5% | 6.25 ms | 9.37 ms |
| 20 | 64 | 66.8% | 62.5–70.9% | 5% | 16.27 ms | 18.73 ms |

The alphabet is the bootstrap unit (20 clusters); within-alphabet episodes and queries are not treated as independent. At 20-way/64-point resolution, ordered DTW reaches 52.75% (48.94–56.80%) and deformable fit reaches 54.25% (48.95–59.89%), versus 66.8% for point-set distance. Point-set's paired advantage is 14.05 percentage points over DTW and 12.55 points over deformable fit; their 95% alphabet-cluster intervals are 9.01–19.65 and 9.67–14.95 points respectively.

At fixed 64-point resolution, raising k from 5 to 20 increases the implied pairwise distance count 16× and the point-set median worker time 7.2× (2.26→16.27 ms); the k=10→20 segment is 4× more comparisons and 2.8× worker time. At fixed k=20, raising trajectory length from 16 to 64 points leaves pair count at 400 but raises point-set median worker time 5.6× (2.92→16.27 ms). These are finite measurements for this adapter/Term implementation and execution environment, not asymptotic complexity results.

Median worker timing includes building the candidate graph, adding queries, and graph-Term evaluation. Shared feature preparation for 10,542 trajectories took 4.48 s; the full append-only capture took 12.24 s wall / 12.23 s CPU, including source stability hashing. Peak RSS was about 55 MB. The prior 20-way/64-point point-set result reproduces exactly at 66.8% on the same episodes.

## Interpretation and next gates

The panel establishes a task-level quality/cost envelope for selected held-structure recognizers. Point-set distance has a clear accuracy advantage on this workload; increasing candidate count and trajectory resolution increases cost while keeping substantial accuracy above chance. The first two captures are preserved as exploratory because their offline analyzers failed before analysis; v1.2 corrects analyzer scope, locks the exact runner/analyzer pair, and repeats all cells.

This does not prove a general polynomial scaling bound or measure native Term operations directly. It covers 20 alphabets, one existing evaluation split, nested candidate prefixes, one stroke adapter, and the three pre-existing Terms. Next run a disjoint alphabet/writer transfer design and vary exemplar count with a held-out task split; then instrument native Term/operator work and test an independently sourced task family.

## Reproduction artifacts

- [v1.2 preregistration and amendments](SUBSTRATE_OMNIGLOT_TERM_COST_SCALE_V1_2_PREREG_20260929.md)
- [Capture runner](../../../scripts/substrate_omniglot_term_cost_scale_v1_2.py)
- [Independent analyzer](../../../scripts/analyze_substrate_omniglot_term_cost_scale_v1_2.py)
- [Raw 2,700-cell JSONL capture](../../../evaluation/reports/omniglot_term_cost_scale_v1_2_20260929_raw.jsonl)
- [Analysis, all condition intervals and paired contrasts](../../../evaluation/reports/omniglot_term_cost_scale_v1_2_20260929_analysis.json)
- [Source, runtime, dataset, and base-panel lock](../../../evaluation/substrate_capability/omniglot_term_cost_scale_v1_2_20260929_lock.json)
- Exploratory captures: [v1](../../../evaluation/reports/omniglot_term_cost_scale_v1_20260929_raw.jsonl), [v1.1](../../../evaluation/reports/omniglot_term_cost_scale_v1_1_20260929_raw.jsonl)
