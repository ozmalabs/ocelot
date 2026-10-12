# Thoughtexperiment computer-vision open-gap discovery v1 results

**Outcome:** the exploratory screen retained one order-1 open gap for three of 33 computer-vision postulates. This is candidate discovery only; none of the three is established as a capability gain.

## Run

The fresh full-boot worker loaded 731 seeds and recorded 11 failed seed loads. It resolved the exact default `harvested` shape mode once (24 shapes), computed the covered-keyword index once, then scanned all 33 postulates with `max_order=1`, normal pruning enabled, and graph recording disabled. Source and top-level seed fingerprints were stable. The full retained-gap payloads are in the [raw capture](../../../evaluation/reports/thoughtexperiment_open_gap_discovery_cv_v1_raw_20261001.json); the reproducible [runner](../../../evaluation/substrate_capability/thoughtexperiment_open_gap_discovery_cv_v1.py) and [discovery procedure](THOUGHTEXPERIMENT_OPEN_GAP_DISCOVERY_CV_V1_20261001.md) define the scope.

| Postulate | Retained keys | Donor shape | Current assessment |
|---|---|---|---|
| `diffusion_model_vision` | compositional generation; production-space search; compose-under-selection generator | `compositional_generativity__from__grammar` | Generic derivation. No specific denoising/image-generation implementation or task oracle has been shown. |
| `variational_autoencoder` | same compositional-generation keys | same grammar shape | Same generic derivation; not evidence of latent-variable encoding or reconstruction. |
| `vision_language_model` | reliability-weighted cue fusion; multi-cue integration; audiovisual fusion estimate | `reliability_weighted_fusion__from__Kalman_filter` | Likely selector false positive for the fusion subclaim: `domains/combinatorial_recognizer.py` already represents and predicts with reliability-weighted channel fusion. The broader visual modality remains a separate known acquisition gap. |

The VLM finding is particularly informative about measurement quality. The openness selector matches distinctive tokens, and the open result does not entail the corresponding mechanism is absent. Earlier substrate documentation also records that reliability-weighted fusion machinery exists while a general visual front end does not ([self-introspection audit](self_introspection_wiring.md)). Thus this scan improves candidate discovery but cannot substitute for semantic source audit.

## Interpretation and next gate

The three retained gaps should not be promoted directly to capability proposals. First audit derivation claims against source-level mechanisms and narrow each claim to an executable capability. Then select a candidate whose task oracle is independent of the derivation and whose required modality/data path exists. The next useful experiment is a selector calibration panel pairing known implemented capabilities with genuinely absent capabilities, measuring false-open and false-covered rates. A later utility experiment must separate substrate-generated proposal quality from any manually supplied implementation.

The covered-keyword cache added for batch discovery preserves the default recompute path for all existing callers. A direct default-versus-cached semantic parity panel remains required before relying on it in confirmatory work.
