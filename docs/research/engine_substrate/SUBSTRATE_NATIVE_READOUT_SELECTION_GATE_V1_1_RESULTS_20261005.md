# Native readout selection gate v1.1 results

## Measurement integrity

The amended six-seed capture and independent analyzer pass. The analyzer replays the 6,400-step fit schedule, reconstructs all association counts from training activations, recomputes every candidate prediction and validation score, and verifies native `ArgminUnique` either selected the unique validation winner or refused on a tie. It also verifies that the corner labels were revealed only after selected predictions or refusals were recorded. Visual weights and association counts stay frozen during probes.

## Outcome

Each seed has eight labeled validation examples and eight label-sealed corner examples. Validation scores tie in three of six seeds; `ArgminUnique` abstains in those cases. In the other three seeds, the substrate selects a reader: prototype distance in seeds 40 and 42, dot product in seed 44.

Across all 48 corner cases, the selected-reader output is correct on 21 (43.8%) and is present for 24 (50%) cases. Conditional accuracy among selected outputs is 21/24 (87.5%). The fixed prototype-distance reader scores 37/48 (77.1%); fixed dot product scores 35/48 (72.9%). External nearest-mean scores 37/48, initial projection and centroid/count each score 24/48, and the translation-aware template scores 48/48. The selector therefore demonstrates native validation-based choice with explicit abstention, but its three ties reduce coverage and unconditional task yield below either fixed reader. It does not establish a net capability advantage under ordinary accuracy scoring.

Per-seed validation scores and corner correct counts are in the [analysis JSON](../../../evaluation/reports/vision_eye_native_reader_selection_v1_1_analysis_20261005.json). Median fit closure cost is 11.44 ms per training step. Candidate-score closure has a 4.36 ms median; selection commit CPU has a 4.84 ms median. Peak worker RSS is at most 84,840 KiB. These small-fixture costs are descriptive, not scaling estimates. Per-worker timing and memory values are in the raw [capture](../../../evaluation/reports/vision_eye_native_reader_selection_v1_1_20261005.json).

## Interpretation and next gate

This is evidence that native graph rules can evaluate two supplied readers on disjoint labeled validation examples, select a unique winner, and abstain on ties before sealed-corner evaluation. Task specification, candidate rules, labels, and split are externally authored. The preregistered validation-breadth follow-up has now reduced ties from 3/6 to 1/6 seeds, but the selector still scores 24/48 versus 32/48 for the fixed prototype-distance reader; see [validation-breadth results](SUBSTRATE_NATIVE_READOUT_SELECTION_VALIDATION_BREADTH_V1_RESULTS_20261005.md). Next test the bounded selector on an independent feature family or transfer benchmark before generalizing.

## Reproduction and version history

The original protocol is [v1 preregistration](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_PREREG_20261005.md), and the post-capture accounting correction is [v1.1 amendment](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_1_AMENDMENT_20261005.md). Reproduce using the [v1.1 source-locked runner](../../../evaluation/substrate_capability/vision_eye_native_reader_selection_v1_1.py) and [independent analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_native_reader_selection_v1_1.py). The failed original v1 capture remains preserved separately.
