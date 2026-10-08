# Native readout selection gate v1

## Question and scope

Can the substrate select between two externally proposed graph-native readouts using labeled validation examples, then apply its selected readout to position-held-out examples whose labels are unavailable during selection? This is a staged responsibility-transfer experiment. It tests supervised model selection inside the substrate; it does not test autonomous proposal generation, task discovery, or self-improvement.

## Prospective split

Use the existing centered five-pixel horizontal/vertical bar task and six paired seeds 40–45. Keep the four corner sites sealed for final evaluation. Partition the 12 interior sites before running: eight sites for fitting association prototypes (6,400 presentations total, 400 per class/site), four fixed interior sites for validation (eight labeled validation queries), and the four corners for final evaluation (eight unlabeled-to-selector queries). Do not present validation or corner examples to the association update rule. Validation labels may be present in the graph only for native candidate scoring. Corner labels must be withheld from the graph until all candidate choices and predictions are frozen and captured.

## Candidate set and substrate responsibility

Provide exactly two externally specified candidate rules: (1) raw activation-by-association dot product, and (2) squared Euclidean distance from the class activation prototype. Both use the same fitted association state, typed graph, native closure, and tie order. Candidate prediction records for fit-validation examples are produced by native rules. Native rules count validation agreements against the provided labels and attach the resulting score to each candidate. A native `Argmax` over candidate score selects one reader per seed. Host code may install the fixed task, labels, candidate definitions, and runner, but must not compare scores, choose the winner, or write the chosen-candidate field. The selected candidate identifier and both scores are captured before corner labels are revealed.

## Gates and reporting

Require source lock, exact fit/validation/corner partitions, schedule reconstruction, reconstruction of learned association counts from fit activations, zero validation/corner updates, native predictions for both candidates on validation, native score reconstruction, unique native candidate selection (or explicit tie/refusal), and exactly one selected-rule prediction per corner query. Record all candidate-generation and evaluation work, closure time, CPU time, memory, predictions, scores, abstentions, and selected candidate. Compare selected-reader corner accuracy with each fixed candidate, the external nearest-mean control, initial projection, centroid/count baseline, and translation-aware template. Report per-seed outcomes and paired uncertainty; do not use aggregate validation performance as a substitute for held-out task utility.

## Interpretation boundary

Selection success would show that a substrate rule can choose between a supplied pair using a disjoint supervised validation set and transfer the choice to four unseen corners on this task. It would not show that the substrate invented either readout, selected its own benchmark, learned without labels, or generalized to independent feature families. Failure modes include candidate ties, validation overfit, no candidate beating the fixed-reader controls, inability to express the selector natively, or excessive selection cost. Preserve raw captures and report each failure without silently changing the split or candidate set.

## Implementation/reproduction status

Implemented and measured under the unchanged task conditions with the [v1.1 amended accounting](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_1_AMENDMENT_20261005.md). The original v1 raw capture failed its aggregate gate because three legitimate native tie refusals were counted as missing predictions; that capture is preserved. The corrected [v1.1 results](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_1_RESULTS_20261005.md) report selections, abstentions, and sealed-corner utility separately. Reproduce using its source-locked runner and independent analyzer.

A fresh-seed [validation-breadth follow-up](SUBSTRATE_NATIVE_READOUT_SELECTION_VALIDATION_BREADTH_V1_RESULTS_20261005.md) adds four validation locations without changing fit sites or training exposure. Ties decrease from three to one among six seeds, but overall selected-reader yield remains below the fixed prototype-distance reader. The cohorts are independent and should not be interpreted as a paired treatment effect.


## Implementation smoke amendment (pre-capture)

The first locked single-worker smoke attempt failed during rule installation, before training or probe presentation: native `add_edge` effects require a bound target variable and do not accept a computed `PickUnique` target. The implementation now binds the candidate prediction in the rule match and publishes that bound node. No task outcomes were observed and no raw capture was produced. The source lock is regenerated after this correction.
