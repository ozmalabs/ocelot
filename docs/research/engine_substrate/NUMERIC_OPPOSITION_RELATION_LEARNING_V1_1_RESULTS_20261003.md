# Numeric opposition relation learning v1.1 — coverage-directed results

Date: 2026-10-03

## Result

All five source-locked coverage-directed training panels passed measurement
integrity and generalization gates. Each contains 8 positives and 8 negatives,
including x-axis and y-axis positive examples, two-dimensional positives, and
negative examples where only x or only y satisfies opposition. All five
synthesized the same size-9 rule:

```text
(ax == neg(ex)) and (ay == neg(ey))
```

Independent re-evaluation found zero false positives and zero false negatives
on each worker's 1,296-case held-out fractional grid. Across workers, the
pooled count is 180/180 positive and 6,300/6,300 negative predictions. Median
search time is 1.137 s wall / 1.137 s CPU, with 6,587–10,638 explored terms
(median 8,908).

## Comparison with random panels

| Training design | Exact held-out workers | Pooled false positives | Median search time |
|---|---:|---:|---:|
| Random balanced v1 | 1/5 | 720/6,300 | 5.5 ms |
| Coverage-directed v1.1 | 5/5 | 0/6,300 | 1,137 ms |

The panels are not paired per worker; they differ by design. The v1 random
median hides four underfit, x-only solutions. Coverage-directed examples
consistently force the conjunction and therefore require substantially more
search. This is descriptive evidence on one relation, not a broad causal
sample-efficiency estimate.

## Interpretation and next gate

This provides positive evidence that the substrate's fixed-grammar term
synthesizer can infer and generalize a relation when the supervised examples
distinguish both dimensions. It also measures the cost of finding the complete
rule rather than a cheap underfit. Labels, input schema, grammar, and the
relation's correct example labels remain evaluator supplied. The learned Term
has not yet been installed into the thoughtexperiment residual-to-cue flow.
Next: convert the frozen synthesized AST into the native cue rule in a CoW
branch; test cue precision/recall and held-out task utility, with the cue
association separately identified as authored.

## Artifacts

- [Preregistration](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_numeric_opposition_relation_learning_v1_1.py), [analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_relation_learning_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/numeric_opposition_relation_learning_v1_1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/numeric_opposition_relation_learning_v1_1_20261003.json), [analysis](../../../evaluation/reports/numeric_opposition_relation_learning_v1_1_coverage_analysis_20261003.json)
- Prior [random-panel results](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_RESULTS_20261003.md) and [corrected analysis](../../../evaluation/reports/numeric_opposition_relation_learning_v1_1_analysis_20261003.json)
