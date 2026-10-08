# Numeric opposition active query v1 results

Date: 2026-10-03

## Question and design

This experiment asks whether the native-Term maximum-entropy selector can
identify a numeric opposition rule with fewer oracle calls than fixed-first
or seeded-random querying. Five fresh workers received four sparse labeled
integer examples (axis-aligned positive x/y cases, one same-direction negative,
one orthogonal negative), then synthesized a bounded version space under
`Neg`, `Eq`, and `And`, with no constants, size cap 9, a 12-second limit, and a
32-input unlabeled query pool. All policies replayed the same generated pool
with a six-call cap. The relation and simulated oracle are harness-defined;
no external human oracle was queried. Survivor sets were frozen before the
fractional grid and navigation transfer panel were scored.

## Results

The bounded search completed at `max_size` in all five workers and retained
the exact target Term in every version space. Pools contained 9 or 10 distinct
hypotheses (median 9). Maximum entropy used a median of 2 labels; fixed-first
used 1; seeded-random used 4. Every policy reduced to one survivor in all
workers, and each final survivor was exact on all 1,296 disjoint fractional
vector pairs and all 13 navigation proposal/abstention cases.

Maximum entropy therefore did **not** reduce query count on this design. It
spent more calls than the fixed-order policy and its selector stage was slower:
median selector time was 3.13 ms for maximum entropy, 0.066 ms for fixed-first,
and 0.14 ms for seeded-random. Median version-space synthesis took 5.83 s
(5.83 s CPU). Those synthesis costs dominate selection. This is a negative
result for an active-query efficiency advantage on this five-panel task, even
though all policies eventually identify a correct rule.

## Integrity and limits

The final independent analyzer passes with no integrity errors. It recomputes
the source/build lock, current source hashes, exact typed prediction
partitions, query-policy choices, oracle labels, stopping conditions, survivor
sets, and held-out scores. All five pools completed the bounded grammar rather
than hitting the solution or time cap. This does not establish performance on
larger or richer version spaces: the grammar, task, examples, unlabeled inputs,
and oracle relation were supplied by the harness, and the measured pools had
only 9–10 members. Query labels were computed locally from the known relation,
so the run measures logical query count rather than the cost or availability of
a real oracle. Navigation transfer is one authored action-vector panel.

During pilot analysis, the replay harness briefly coerced numeric outputs to
booleans while the selector preserves type distinctions (for example,
`True` versus `1.0`). That capture failed independent replay and was discarded.
The final runner uses the selector's exact typed-label semantics; the final
runner, analyzer, source files, native binary, training sets, and query pools
are bound by the lock. See the [preregistration](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_PREREG_20261003.md), [implementation amendment](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_AMENDMENT_20261003.md), [runner](../../../evaluation/substrate_capability/measure_numeric_opposition_active_query_v1.py), [analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_active_query_v1.py), [source lock](../../../evaluation/substrate_capability/numeric_opposition_active_query_v1_lock_20261003.json), [capture](../../../evaluation/reports/numeric_opposition_active_query_v1_20261003.json), and [analysis](../../../evaluation/reports/numeric_opposition_active_query_v1_analysis_20261003.json).


## Follow-up on candidate-order effects

The fixed-first candidate list in v1 put deliberately selected separating probes first, so its one-call median depended on a favorable order. V1.1 replaces that comparison with 30 paired, randomized pool orders per worker. Its independent analyzer re-runs version-space synthesis from locked inputs and reproduces each of the five generated pools before replaying query outcomes. Use the v1.1 order-balanced result for conclusions about selection versus randomized sequential querying ([results](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_RESULTS_20261003.md)).
