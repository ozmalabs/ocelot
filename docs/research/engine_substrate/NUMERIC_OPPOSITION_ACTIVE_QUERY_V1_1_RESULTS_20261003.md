# Numeric opposition active query v1.1 results

Date: 2026-10-03

## Question and design

V1 compared maximum-entropy selection with a fixed-first list whose deliberately
separating probes appeared near the front. This order can favor the control.
V1.1 keeps the same five sparse training panels, source-current synthesizer,
32-input candidate pools, six-label limit, and held-out tests, then freezes 30
seeded permutations per worker. For every worker/permutation, maximum entropy
and sequential querying receive the identical candidate order and initial
version space. The 150 paired blocks are repeated orders nested within five
training panels, not 150 independent tasks.

## Results

All five version spaces completed at `max_size`, retained the exact target,
and contained 9 or 10 hypotheses. The maximum-entropy selector identified a
unique exact survivor in 150/150 paired blocks. Sequential random-order query
identified a unique exact survivor in 111/150. Across paired order blocks,
maximum entropy used fewer labels in 102 cases, tied in 32, and used more in 16.
Median calls were 3 for maximum entropy and 4.5 for sequential random order.
Worker-level median paired differences (active minus sequential calls) were
−1.5, −2, −2, −2, and 0; the median across the five worker medians was −2.

Every selected singleton scored exactly on all 1,296 fractional vector pairs
and the locked 13-case navigation proposal/abstention panel. Sequential-query
failures were non-identification within the six-call budget, not incorrect
oracle labels. Median synthesis time was about 5.8 s per worker. Median
maximum-entropy selection time was 3.74 ms per order block, versus 0.40 ms for
sequential querying. The active policy trades this selector cost for fewer
labels and more reliable identification in this bounded version space. Since
labels were computed locally from a known relation, the experiment does not
show that this trade is favorable for a real or expensive oracle.

## Integrity and interpretation

Independent analysis passes with no errors. It regenerates each bounded version
space from the locked examples and unlabeled pool, reproducing all five exact
hypothesis lists and their `max_size` completion. It also verifies current
source/build hashes, lock/capture identity, all 30 exact pool permutations per worker,
paired order equality, native entropy choices, sequential choices, strict
typed prediction filtering, labels, stopping conditions, survivor identities,
and independent held-out rescoring. All query calls are unique pool members
within budget. Worker-cluster results are reported separately to avoid
treating the 150 order blocks as independent task samples.

The result shows a narrow selection benefit for a generated 9–10-member
version space when candidate ordering is balanced. It does not establish
general active learning, model-adequacy detection, open-ended grammar search,
or autonomous self-improvement. The numeric target, operator grammar, training
examples, query pool, and local oracle remain harness-defined. The next gate
should increase hypothesis ambiguity, include observational aliases and
out-of-grammar targets, and repeat across unrelated task families. See the
[preregistration](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_PREREG_20261003.md),
[runner](../../../evaluation/substrate_capability/measure_numeric_opposition_active_query_v1_1.py),
[analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_active_query_v1_1.py),
[source lock](../../../evaluation/substrate_capability/numeric_opposition_active_query_v1_1_lock_20261003.json),
[capture](../../../evaluation/reports/numeric_opposition_active_query_v1_1_20261003.json),
and [analysis](../../../evaluation/reports/numeric_opposition_active_query_v1_1_analysis_20261003.json).
