# Learned numeric cue to composer integration — results

Date: 2026-10-03

## Result

All 65 source-locked cells passed independent semantic and lifecycle analysis.
The five frozen ASTs from coverage-directed synthesis were each crossed with
the 13-case task panel. In every cell, the integration runner embedded the
exact learned AST in the native graph rule after binding its four variables to
numeric residual attributes. The candidate branch had no action-pair
codebook.

Across the 20 ordinary positive cells, the learned relation fired, the cue
axis was minted, the composer selected `flip_comparison` for
`hop_descend_gradient`, and every fresh held-out score passed. All 40 ordinary
negative controls produced no cue or proposal. All five target-absent controls
derived the cue but emitted no proposal. Baseline branches made no proposal.
All 65 branches preserved the primary graph/rule/revision during exploration
and returned exactly one compact `ExperimentResidual` receipt.

| Measure | Result |
|---|---:|
| Cue recall on ordinary positives | 20/20 |
| False cues on ordinary negatives | 0/40 |
| Held-out repair passes | 20/20 |
| False proposals, including absent target | 0/45 |
| Primary isolation and compact return | 65/65 |
| Median snapshot fork | 0.258 ms |
| Median native concern induction | 6.245 ms |
| Median composer grounding | 0.241 ms |
| Median held-out task scoring | 71.611 ms |

Prior relation acquisition cost is median 1.137 s per training panel. At 13
measured task uses per term, that is 87.5 ms amortized acquisition per case,
before any subsequent reuse. Scoring is reported separately from acquisition
and branch operation.

## Interpretation

This demonstrates a connected supervised pipeline: fixed-grammar examples
produce a learned Term, the frozen Term executes in a native residual rule,
the result activates a held cue, and the structural composer builds a useful
held-out repair in an isolated branch. It remains a narrow authored task
family. The evaluator supplies relation labels and converts actions to numeric
vectors; the mapping from a true relation to the existing cue vocabulary and
the cue-to-edit path are authored. The experiment therefore demonstrates
learning and application of one relation inside an engineered loop, not
autonomous problem discovery, self-directed query selection, cue invention,
or general self-improvement.

## Artifacts

- [Preregistration](LEARNED_NUMERIC_CUE_COMPOSER_INTEGRATION_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_learned_numeric_cue_composer_integration_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_learned_numeric_cue_composer_integration_v1.py)
- [Source lock](../../../evaluation/substrate_capability/learned_numeric_cue_composer_integration_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/learned_numeric_cue_composer_integration_v1_20261003.json), [analysis](../../../evaluation/reports/learned_numeric_cue_composer_integration_v1_analysis_20261003.json)
- Upstream [coverage-directed relation learning](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_1_RESULTS_20261003.md) and its [capture](../../../evaluation/reports/numeric_opposition_relation_learning_v1_1_20261003.json)
