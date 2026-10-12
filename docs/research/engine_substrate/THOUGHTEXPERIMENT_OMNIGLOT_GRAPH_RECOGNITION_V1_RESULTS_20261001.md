# Thoughtexperiment graph-native grapheme recognition v1 results

**Outcome:** the substrate-backed grapheme recognizer scores 77/80 (96.25%) on the fixed small held-writer Omniglot panel in each of three fresh workers.

The workers use the `Angelic` evaluation alphabet, 10-way episodes, one gallery drawing per character, and query drawings from held-out writer indices. Accuracy is exactly repeatable across workers; worker PIDs are distinct; each processes 80 queries; and source and selected-alphabet data fingerprints are stable. The operator uses the substrate's `PointSetDist` recognition Term and native graph evaluation through `domains/reading_runners.py::run_grapheme`.

This is evidence for a specific single-modality capability: writer-generalizing recognition among character classes represented in the gallery. It does not establish general visual understanding, unseen-class recognition, image-text alignment, zero-shot image classification, or a Thoughtexperiment-derived improvement. The sample is small and from one alphabet; 77/80 should not be generalized to Omniglot as a whole.

The existing `run_cross_modal` reading runner directly calls `run_grapheme`, so its score is not an independent cross-modal binding result. A separate graph-native grapheme↔audio panel now uses the repository-local FSDD release and measures both held-out read-aloud and dictation. See the [binding results](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_RESULTS_20261001.md); those outcomes remain distinct from this visual-only score.

See the [preregistration](THOUGHTEXPERIMENT_OMNIGLOT_GRAPH_RECOGNITION_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_omniglot_graph_recognition_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_omniglot_graph_recognition_v1_raw_20261001.json).
