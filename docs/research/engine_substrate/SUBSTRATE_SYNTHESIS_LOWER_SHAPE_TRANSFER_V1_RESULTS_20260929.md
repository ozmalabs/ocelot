# Lower-than operator-shape transfer v1 — results

**Date:** 2026-09-29. **Question:** does the graph-authored lower-threshold shape select an executable grammar on unseen scalar piecewise-scaling instances, and how does that compare with a matched neutral wording?

## Protocol and integrity

The panel tests `4*x if x<4 else 2*x` and `5*x if x<6 else 3*x`, each with six training values, six disjoint holdouts, trigger wording, and lexical-ablation wording. Five fresh processes run per task/wording cell through `ensure_program_synthesis` → `ingest_spec` → standard `pump`; no operator inventory is injected. Accepted graph-reflected Programs are evaluated on all holdouts.

The preregistered pilot disclosure records one exploratory threshold-4 worker; it is not pooled. The confirmatory analyzer passes all eight capture-integrity gates: exact locked schedule, complete unique 20-cell matrix, no worker failures, current source/native hashes, stable workers, terminal Rung 3 status, and complete holdout readbacks for every accepted Program. Nine of ten behavioral gates pass. One misses its registered threshold: threshold-6 median candidate work falls 1.44× under trigger wording, below the preregistered 1.5× requirement. That gate is retained as failed ([protocol](SUBSTRATE_SYNTHESIS_LOWER_SHAPE_TRANSFER_V1_PREREG_20260929.md)).

## Results

| Task | Wording | Selected shape/operators | Accepted / exact transfer | Median candidates | Median pump wall time |
|---|---|---|---:|---:|---:|
| Threshold 4, factors 4/2 | Trigger | `thresholded_lower_branch`; `Times/Lt/IfThenElse` | 5/5; 30/30 points | 50,515 | 156.5 ms |
| Threshold 4, factors 4/2 | Lexical ablation | No shape | 0/5; no candidate | 200,000 cap | 282.2 ms |
| Threshold 6, factors 5/3 | Trigger | `thresholded_lower_branch`; `Times/Lt/IfThenElse` | 5/5; 30/30 points | 138,506 | 201.4 ms |
| Threshold 6, factors 5/3 | Lexical ablation | No shape | 0/5; no candidate | 200,000 cap | 213.8 ms |

Both trigger tasks accept and transfer exactly in every worker with no false accepts. Both lexical ablations exhaust the cap and gap in all five workers. Candidate reduction is 3.96× at threshold 4 and 1.44× at threshold 6. Full `pump` median wall time is lower under trigger wording in both cases, but the threshold-6 difference is small; the preregistered candidate-work criterion still fails for that task. This demonstrates parameter-dependent search cost even under a fixed selected grammar.

Full gates and per-cell metrics are in the [analysis](../../../evaluation/reports/synthesis_lower_shape_transfer_v1_20260929_analysis.json), per-worker data in the [raw capture](../../../evaluation/reports/synthesis_lower_shape_transfer_v1_20260929_raw.jsonl), and source/task provenance in the [lock](../../../evaluation/substrate_capability/synthesis_lower_shape_transfer_v1_20260929_lock.json). The [runner](../../../scripts/substrate_synthesis_lower_shape_transfer_v1.py) and [analyzer](../../../scripts/analyze_substrate_synthesis_lower_shape_transfer_v1.py) are source-locked.

## Interpretation and next measurement

Together with the greater-than transfer panel, this shows that two pre-authored, token-triggered selector shapes can select distinct branch operators and correctly synthesize scalar piecewise functions on these small examples. It does not establish general grammar learning: the selector chooses between two explicitly encoded shapes using distinctive words, and operator families outside those shapes remain untested. Both lexical-ablation suites fail under the broad default budget, which makes the supported capability conditional on a helpful prompt and fixed ontology.

The lower-shape behavioral gate is only partially passed because the threshold-6 work reduction misses the preregistered margin. Do not tune budgets or thresholds post hoc. Next test an unsupported third family under both trigger-like and neutral wording to measure honest refusal and broad-search costs, then test any proposed new shape on tasks held out from its construction. No broad operator-selection claim follows from these two panels.
