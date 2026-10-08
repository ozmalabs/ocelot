# Native primitive-family selection transfer v1 preregistration

## Question

Can the substrate's graph-native validation-score and unique-selection mechanism transfer from visual readouts to a separate numeric-relation family, choosing between supplied additive and multiplicative relation candidates and applying that choice to sealed inputs?

This is a cross-domain replication built from an existing locked numeric panel; it is not a novel-task or open-ended discovery claim. The task menu, candidate formulas, panel construction, and target examples are supplied by the harness.

## Panels and split

Use the ten locked additive/product panels in `numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json`, five per target family. Preserve each panel's 32-row `selection_pool` as labeled validation data. Use the full 1,296-row Cartesian grid over `(-2.5,-1.5,-0.5,0.5,1.5,2.5)^4` as sealed evaluation. Before capture, verify that no evaluation row appears in the validation pool. Labels are the boolean relation `ax + ay == ex + ey` or `ax * ay == ex * ey` according to the harness-held task; graph nodes receive validation labels only. Evaluation labels are not inserted until all candidate and selected predictions are captured.

## Supplied candidates and native responsibility

The candidate menu contains exactly two externally authored relations: additive equality and multiplicative equality. Graph-native rules evaluate each candidate on every validation row, count candidate agreement with validation labels in the graph, and use `ArgminUnique` over negative scores to select a unique candidate or explicitly refuse on a tie. The host may install rows, candidate formulas, and task labels, but may not compare candidate scores or set the selected candidate. After selection, the host adds the sealed grid without labels; native rules produce both candidate predictions and publish the selected candidate's prediction. Only after all predictions are read back may the scorer add evaluation labels.

Candidate formulas and the small operator menu are supplied, so this measures native model selection and transfer, not primitive invention. Both candidate outputs are retained as fixed-candidate controls.

## Gates and reporting

Require source lock over runner, analyzer, protocol, numeric-panel lock, runtime sources/build, and engine fingerprint; exact panel and grid reconstruction; validation/evaluation disjointness; no target-task identifier in graph attributes; one native prediction per candidate per validation/evaluation row; native validation-score reconstruction; native unique selection or tie refusal; label-after-prediction receipts; and independent test-grid rescore. Report task-family selection accuracy, tie/abstention rate, selected prediction accuracy and coverage, both fixed-candidate accuracies, per-panel confusion, closure/CPU/RSS cost, and synthesis/panel provenance costs where available. Keep the ten panels as the unit of task variation; 1,296 input rows per panel are not 1,296 independent tasks.

## Interpretation boundary

Success would transfer bounded supervised candidate selection to numeric relations using substrate-native graph rules. It would not demonstrate broad cross-domain cognition, autonomous candidate generation, objective discovery, or self-improvement. The panel was previously used in numeric synthesis studies; results are a new locked mechanism replication, not an untouched benchmark family.

## Reproduction

Use the source-locked runner and independent analyzer under `evaluation/substrate_capability`. Preserve partial captures if any gate fails; amend versioned artifacts rather than replacing results.
