# Native readout selection validation breadth v1 results

## Measurement integrity

The six-seed fresh-cohort capture and independent analyzer pass. Seeds 46–51 use the unchanged eight-site, 6,400-presentation fit set, 16 validation examples across eight distinct positions, and eight corner probes. The analyzer reconstructs the schedule and learned association counts, replays both native reader predictions and validation scores, verifies `ArgminUnique` selection/refusal, and checks that corner labels are revealed only after selected predictions or abstentions are recorded.

## Outcome

The wider validation panel reduces ties from 3/6 seeds in the earlier seeds 40–45 cohort to 1/6 here. This is descriptive across independent cohorts, not a paired causal estimate. The new cohort selects a unique reader in five seeds: prototype distance in two and dot product in three. It abstains on the one tie.

Selected outputs are correct on 24/40 covered corner cases (60% conditional accuracy, 83.3% coverage). Counting abstained corners as no answer, the selector yields 24/48 correct. Fixed prototype distance scores 32/48 (66.7%), fixed dot product 29/48 (60.4%), external nearest-mean 32/48, initial projection and centroid/count 27/48 and 24/48 respectively, and the translation-aware template 48/48. Thus more validation positions improve selection coverage in this cohort but do not improve corner transfer over the fixed distance reader. The validation choices are not a substitute for task utility.

Median fit closure cost is 11.29 ms per training step. Candidate-score closure, selection CPU, and peak RSS are reported in the raw [capture](../../../evaluation/reports/vision_eye_native_reader_selection_v1_2_20261005.json). Full per-seed validation scores and corner outcomes are in the [analysis](../../../evaluation/reports/vision_eye_native_reader_selection_v1_2_analysis_20261005.json).

## Interpretation and next gate

The substrate can evaluate the supplied readers on disjoint labeled examples and uniquely select or abstain using native graph rules. This follow-up shows validation breadth affects refusal rate, but does not show the chosen reader is better on unseen outcomes. Candidate invention, objective selection, independent feature families, and self-directed repair remain unmeasured. Next test the bounded selector on a prospectively specified independent feature family or transfer benchmark, preserving the same separation between fit, validation, and sealed evaluation; keep candidate development and selection costs visible.

## Reproduction

See the [preregistration](SUBSTRATE_NATIVE_READOUT_SELECTION_VALIDATION_BREADTH_V1_PREREG_20261005.md), [source-locked runner](../../../evaluation/substrate_capability/vision_eye_native_reader_selection_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_native_reader_selection_v1_2.py), [source lock](../../../evaluation/substrate_capability/vision_eye_native_reader_selection_v1_2_lock_20261005.json), raw capture, and analysis linked above. Earlier v1 and v1.1 artifacts remain separate.
