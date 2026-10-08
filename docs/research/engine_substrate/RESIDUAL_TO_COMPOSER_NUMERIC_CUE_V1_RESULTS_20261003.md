# Numeric residual-to-composer cue — results

Date: 2026-10-03

## Result

The locked 13-case panel passed independent analysis. A native rule reads
numeric observed/expected displacement components from each raw residual,
without an action-name or opposite-action-pair ontology in the candidate
branch. It derives the fixed held cue for all four opposite-direction cases;
the composer chooses `flip_comparison` for `hop_descend_gradient`, and all
four fresh held-out scores pass. The target-absent control derives the cue but
does not emit a proposal. Eight ordinary controls produce no cue or false
proposal. All 13 cases preserve branch isolation and compact result return.

The corrected independent analysis reports medians of 0.247 ms for the two
snapshot forks, 6.23 ms for concern induction with native rule execution, and
0.377 ms for composer grounding. The first analyzer omitted captured fork
timings from its summary; the v1.1 analysis rechecks behavior and computes that
metric from raw `fork_ms`. The initial analysis file is retained as generated.

## Interpretation

This closes a narrow data-path gate: numeric outcome residuals can drive an
authored native relation rule, produce a held cue, and reach a useful
composer repair without symbolic action-pair facts. No action labels occur on
the residual nodes or in the observation passed to concern induction. The
evaluation harness still translates the navigation task's action labels into
vectors, and the rule itself hardcodes the opposition test and output cue.
Therefore this does not show that the substrate learns the relation, invents
the cue vocabulary, or autonomously chooses a repair family. It is stronger
than the prior action-pair lookup result, but remains substrate execution of
an authored mapping.

## Artifacts

- [Preregistration](RESIDUAL_TO_COMPOSER_NUMERIC_CUE_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_residual_to_composer_numeric_cue_v1.py), [initial analyzer](../../../evaluation/substrate_capability/analyze_residual_to_composer_numeric_cue_v1.py), and [corrected independent analyzer](../../../evaluation/substrate_capability/analyze_residual_to_composer_numeric_cue_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/residual_to_composer_numeric_cue_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/residual_to_composer_numeric_cue_v1_20261003.json), [initial analysis](../../../evaluation/reports/residual_to_composer_numeric_cue_v1_analysis_20261003.json), and [corrected analysis](../../../evaluation/reports/residual_to_composer_numeric_cue_v1_1_analysis_20261003.json)
- Prior action-relation [cue study](RESIDUAL_TO_COMPOSER_NATIVE_CUE_V1_PREREG_20261003.md) and [corrected analysis](../../../evaluation/reports/residual_to_composer_native_cue_v1_1_analysis_20261003.json)
