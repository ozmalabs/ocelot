# Thoughtexperiment selector calibration v1 results

**Outcome:** three of four fixed audit cases match their expected implementation status. The selector misses one known implemented mechanism and returns it as an open gap.

All three fresh workers loaded the same full-boot substrate and returned identical verdicts; source and implementation-surface fingerprints were stable. The selector closes speaker scale normalization, and leaves both audited-absent generative capabilities open. However, it also leaves reliability-weighted cue fusion open despite `domains/combinatorial_recognizer.py` implementing `reliability_weighted_score_term` and `predict_reliability_weighted_term`.

| Source-audited status | Selector says covered | Selector says open |
|---|---:|---:|
| Implemented (2 cases) | 1 | 1 false-open |
| Absent in audited `domains/*.py` surface (2 cases) | 0 false-covered | 2 |

For this small, deliberately selected panel, selector accuracy is 3/4; recall on the two open cases is 2/2; and one of two reported open cases is a known false-open. These are panel counts, not estimates of corpus-wide precision/recall. The previous `vision_language_model` derivation names an already implemented reliability-weighted fusion operation, so that operation itself is not novel. This does not establish that the full VLM capability or visual input path is implemented; the fusion result must be separated from the remaining modality requirement.

## Diagnosed miss

`_live_speech_globs()` includes `domains/abs_learned_fusion.py` and `domains/native_fusion.py`, but omits `domains/combinatorial_recognizer.py`. The latter's stem does not match the speech-module discovery markers even though it implements the exact reliability-weighted fusion mechanism. Direct confirmation gives `combinatorial_recognizer_in_scan=False` and `_codebase_has(...) = None` for the fusion candidate. The selector's speech-scoped source discovery is too narrow for a postulate drawn from the computer-vision / multimodal domain. The immediate engineering target is domain-aware implementation-surface lookup, with a regression panel that retains the absent controls and the covered SIFT case.

This calibration panel does not assess proposal utility or whether missing capabilities can be learned. The absent labels are scoped to the audited Python domain implementation files. See [preregistration](THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_selector_calibration_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_selector_calibration_v1_raw_20261001.json).
