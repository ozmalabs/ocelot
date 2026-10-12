# Thoughtexperiment selector calibration v1 preregistration

## Question

Does the current open-gap selector distinguish source-audited implemented mechanisms from source-audited absent mechanisms on the current full substrate?

## Audited cases and labels

Labels are fixed from the implementation surface before this panel:

| Case | Expected | Source evidence / audit scope |
|---|---|---|
| Speaker scale normalization | covered | `domains/sound_graph.py` exposes speaker-normalized formant-ratio structure; `domains/speaker_norm.py` implements normalization. |
| Reliability-weighted cue fusion | covered | `domains/combinatorial_recognizer.py` defines `reliability_weighted_score_term` and `predict_reliability_weighted_term`. The earlier VLM synthesis retained this mechanism directionally, so this is a confirmatory diagnostic, not a blind test. |
| Denoising diffusion image generation | open | No denoising-diffusion image-generation mechanism was identified in the current `domains/*.py` implementation surface. Generic feature composition and unrelated diffusion equations do not satisfy this label. |
| Variational autoencoder latent image reconstruction | open | No VAE encoder/decoder, variational posterior, or latent-image reconstruction mechanism was identified in the current `domains/*.py` implementation surface. |

The labels concern executable mechanisms, not whether the concept names or background theory occur in seeds/docs. The absent labels are scoped to current Python domain implementations and are not a claim about every untracked external capability.

## Procedure

Run three fresh full-seed workers. Each computes `_covered_keywords` once and calls `is_gap(..., prune=True)` for the four fixed `name_keys`. Record complete verdict/reason/covered-by fields, worker identity, boot status, and source fingerprints. Fingerprint `domains/order_n_postulates.py`, the two positive implementation modules, boot sources, native extension, and every top-level `domains/*.py` implementation file before and after.

## Primary outcomes

Report the 2×2 table of expected implementation status versus selector verdict. False-open is an implemented case returned as a gap. False-covered is an absent case rejected as already realized. Require three distinct workers, stable boot identities and source hashes, and identical verdicts across workers. This is a small calibration panel, not an estimate of corpus-wide precision/recall. It does not establish utility or learning capability.

## Artifact locations

See the [results](THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_selector_calibration_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_selector_calibration_v1_raw_20261001.json).
