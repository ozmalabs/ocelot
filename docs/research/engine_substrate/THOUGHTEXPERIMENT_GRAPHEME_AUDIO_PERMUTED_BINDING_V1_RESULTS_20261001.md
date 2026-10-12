# Thoughtexperiment grapheme–audio permuted-binding v1 results

**Outcome:** the correct co-presentation mapping beats the one-digit cyclic shift by 80 percentage points on read-aloud and 70 points on dictation in every worker.

| Binding arm | Read-aloud | Dictation | Mean accuracy |
|---|---:|---:|---:|
| Correct mapping (`shift=0`) | 32/40 (80%) | 28/40 (70%) | 75% |
| One-digit cyclic shift (`shift=1`) | 0/40 (0%) | 0/40 (0%) | 0% |

All six worker/arm runs create 10/10 graph binding edges and execute 40 queries in each direction. The three workers reproduce the exact arm outcomes. Each worker compares arms in a new substrate and resets the task's deterministic query RNGs; only the co-presented audio identity changes. Source, native extension, Omniglot, and all 3,000 FSDD file fingerprints remain stable.

The result gives causal evidence that held-out symbol-to-speech and speech-to-symbol outputs depend on the correct co-presented mapping in this task. The zero score under the cyclic shift is expected because every taught association is systematically wrong; it is not a general chance estimate. This supports the narrow graph-native grapheme↔spoken-digit capability, with modality-recognition quality still part of the end-to-end score. It does not establish image-text alignment, general multimodal reasoning, VLM behavior, or Thoughtexperiment-driven learning.

The standalone task now accepts an optional `pair_shift` argument, defaulting to zero so existing invocations retain the original mapping. See the [preregistration](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_PERMUTED_BINDING_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_grapheme_audio_permuted_binding_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_grapheme_audio_permuted_binding_v1_raw_20261001.json).
