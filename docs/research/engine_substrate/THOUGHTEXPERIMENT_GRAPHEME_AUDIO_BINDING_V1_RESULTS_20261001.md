# Thoughtexperiment grapheme–audio binding v1 results

**Outcome:** the graph-native co-presentation task bound all 10 grapheme–digit pairs and reproduced 32/40 read-aloud (80%) and 28/40 dictation (70%) outcomes in each of three fresh workers.

The panel uses held-out Omniglot writers for symbol queries and held-out FSDD speakers for audio queries. It uses the 3,000-WAV repository release at `data/fsdd-current/.../recordings`; four sorted speakers supply the audio gallery and the remaining speakers supply queries. Ten of ten co-presented grapheme/audio identities produce a `sounds_like` binding. Each worker returns 40 read-aloud and 40 dictation queries. Outcomes match exactly across workers, PIDs are distinct, and source plus all selected Omniglot/FSDD file hashes are stable.

This is measured narrow cross-modal association and recall between handwritten digit symbols and spoken digits. The results are above the nominal 10-way chance rate, but no shuffled-pair or permuted-binding control was included, so do not assign the full score to the association rules or claim their causal benefit. End-to-end accuracy also includes each modality's recognition errors. The task is not image-caption alignment, joint semantic embedding, general VLM behavior, or a Thoughtexperiment improvement.

The follow-up [permuted-binding control](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_PERMUTED_BINDING_V1_RESULTS_20261001.md) reproduces this correct-map outcome and compares it to a shifted association.

See [preregistration](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_grapheme_audio_binding_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_grapheme_audio_binding_v1_raw_20261001.json).
