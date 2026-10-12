# Native candidate-adequacy gate v3 preregistration

## Question

Can a native adequacy policy reject a supplied candidate that has high balanced accuracy but systematically accepts cases from a narrower, different relation?

## Panels

Generate 10 deterministic fresh panels for each of the v2 relations: additive conservation, product conservation, componentwise opposition, and inequality. Use the same complete integer domain `(-3,-2,-1,0,1,2,3)^4`, exactly 16 positive and 16 negative validation examples per panel, and the frozen v2 class-stratified seeded selection algorithm. Use seed IDs `830000 + task_index*100 + worker`. Include zero and boundary examples in each class. Test on each panel's integer-grid complement plus all 1,296 fractional rows from `(-2.5,-1.5,-0.5,0.5,1.5,2.5)^4`. Preserve generated validation rows in the source lock; reveal test labels after candidate predictions and decisions are captured.

## Native policy

The candidate menu remains additive and product equality. For each candidate, graph rules compute true-positive rate and true-negative rate from the 16 examples in each validation class. Candidate score is `min(TPR,TNR)`, so one class cannot be masked by strength on the other. The fixed acceptance threshold is 0.98. Because each class has 16 examples, the threshold requires perfect class-specific validation accuracy in this design. If the best candidate misses the threshold, native rules emit `decision=request_help`. Otherwise native `ArgminUnique` selects a unique best candidate; a score tie emits `decision=abstain_tie`. No help response or new primitive is provided. Candidate ranking and decision remain native graph operations.

## Gates

Require source lock and stable measured sources; 40 expected panels; exact class balance and zero/boundary coverage; disjoint validation and held-out rows; no task identifier in graph attributes; native prediction, raw agreement, and minimum-class score replay; correct threshold, unique-selection, tie, and help outcomes; label-after-prediction receipts; and independent scoring on the complete integer complement and fractional grid. Report per-task false-help and false-accept rates, coverage and selected accuracy, confusion counts, score distributions, and worker cost.

## Interpretation and reproducibility

This is a prospective test of a stringent deterministic-relation gate on a finite authored task family. It does not estimate natural-task calibration or general adequacy. The 0.98 threshold was set as an exact-per-class requirement for these 16-example strata, not fitted to the v2 opposition score. Reproduce with `python3 evaluation/substrate_capability/native_candidate_adequacy_v3.py --lock`, then `--run`, then `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_v3.py`.
