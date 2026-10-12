# Thoughtexperiment grapheme–audio permuted-binding control v1 preregistration

## Question

Does correct co-presentation improve held-out read-aloud and dictation relative to an otherwise identical one-digit cyclically shifted binding?

## Arms and controls

Use the same Omniglot/FSDD sources, feature extraction, recognition Terms, galleries, query identities, test order, and graph-native rules as the v1 co-presentation panel. Each fresh worker runs two isolated new-substrate arms:

- **Correct:** `pair_shift=0`, binding grapheme digit `d` to audio digit `d`.
- **Permuted:** `pair_shift=1`, binding grapheme digit `d` to audio digit `(d+1) mod 10`.

Both arms use `n_test=40`, hence 40 queries per direction. Run three fresh workers. The v1 correct-map result is already known (32/40 read-aloud, 28/40 dictation); this is a preregistered causal control, not a blind baseline replication. Fingerprint all task sources and all selected Omniglot/FSDD data before and after.

## Primary measure and gates

Per worker, compute the mean of read-aloud and dictation accuracy for each arm and the paired difference (correct minus permuted). Also report both direction-specific differences and exact success counts. Require 10/10 bindings and 40 queries per direction in both arms, three distinct worker PIDs, identical inputs/task identities within each worker, repeatable outcomes across workers, and stable source/data hashes. The directional hypothesis is that correct mapping beats the permuted mapping on the mean end-to-end score; report failures without changing thresholds.

The cyclic shift preserves rule firing and binding count while making the learned relation systematically wrong. A performance drop supports sensitivity to the co-presented mapping, but end-to-end scores still include modality-recognition quality. No claim about image-text alignment, general VLM capability, or thoughtexperiment-driven improvement follows.

See the [results](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_PERMUTED_BINDING_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_grapheme_audio_permuted_binding_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_grapheme_audio_permuted_binding_v1_raw_20261001.json).
