# Native readout selection gate v1.1 amendment

This is a reporting and outcome-accounting amendment to the prospective [v1 protocol](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_PREREG_20261005.md). It does not change the task, fit/validation/corner partition, candidate set, native scoring rule, selector, seeds, or labels.

## Reason for amendment

The first six-seed capture completed all workers but failed its aggregate gate because three seeds had exactly tied validation scores. Native `ArgminUnique` returned no candidate, as designed. The v1 runner incorrectly treated these valid refusals as missing predictions and did not reveal corner labels after recording the refusals. The raw failed capture is preserved at [v1 capture](../../../evaluation/reports/vision_eye_native_reader_selection_v1_20261005.json); its six score pairs are in that record. The failure is a gate/reporting defect, not a change to the selection policy.

## Amended accounting

Treat a unique validation maximum as a selected candidate and a tied maximum as a native abstention. On selected seeds, require exactly one selected-reader prediction on every corner query. On tied seeds, require no selected-reader corner prediction, explicitly record abstention, and then reveal labels only after this refusal is recorded. Candidate-specific corner predictions may still be captured as diagnostics, but they do not count as selected-reader outputs. The analyzer independently reconstructs each candidate prediction and validation score, verifies that native selection equals the unique best candidate or refuses on a tie, and scores abstentions separately from accuracy.

## Reproduction

Use the v1.1 source-locked runner and independent analyzer named in the capability programme. The amended capture is separately versioned and does not overwrite the v1 failed capture. All experiment conditions remain those in the v1 protocol.
