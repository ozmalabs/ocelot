# Thoughtexperiment graph-native grapheme recognition v1 preregistration

## Question

What held-writer visual grapheme-recognition accuracy does the current substrate-backed recognition Term attain on the local Omniglot evaluation corpus under the existing reading runner?

## Procedure

- Run three fresh Python workers.
- Use the exact `run_grapheme` procedure with 8 episodes and 10 candidate graphemes per episode. That runner uses the first sorted evaluation alphabet, one writer's drawing as each class exemplar, held-out drawing indices from writers 1–11, the fixed local RNG seed, and the substrate's `PointSetDist`/Argmax Term.
- Capture alphabet, class count, query count, scalar accuracy, worker PID, and full hashes for the selected alphabet's evaluation drawing files.
- Fingerprint the runner, recognition/operator/adapter sources, native extension, selected data files, and source files before/after.

## Measures and interpretation

Primary measure: fraction correct over the runner's 8×10 held-out writer queries. Require exact accuracy agreement across workers, the expected query count, distinct PIDs, and stable source/data hashes. This is a single-alphabet, seen-class/new-writer visual recognition result. It does not measure cross-modal binding, image-text alignment, zero-shot classes, broad visual generalization, or thoughtexperiment learning.

The `run_cross_modal` name is not used as the outcome: source inspection shows it delegates directly to this grapheme-only runner. A separate graph-native grapheme↔audio panel uses the repository-local FSDD release and is reported independently. Keep the modalities and claims separate. See the [visual results](THOUGHTEXPERIMENT_OMNIGLOT_GRAPH_RECOGNITION_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_omniglot_graph_recognition_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_omniglot_graph_recognition_v1_raw_20261001.json).
