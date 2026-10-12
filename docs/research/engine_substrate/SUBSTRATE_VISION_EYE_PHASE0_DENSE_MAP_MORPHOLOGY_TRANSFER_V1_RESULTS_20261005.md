# Vision-eye phase-0 dense-map morphology transfer v1 results

## Result

All 14 capture gates and all 10 independent-analysis gates pass. Six paired seeds compare square and cross receptive-field patches over the same nine-site training grid. Each morphology acquired all nine trained sites in every seed; trained probes are 162/162 nearest-region correct in each condition. On 288 held-out probes per morphology, square patches classify the nearest trained region correctly on 288/288, while cross patches score 33/288 (11.5%). Square is better in all six paired seeds, by 39–45 of 48 probes per seed (81.3–93.8 percentage points). Both morphologies have zero exact held-out coordinate localizations (0/288).

The morphology manipulation has a large effect on held-out region transfer in this fixture. The result is not a general visual-recognition claim: both conditions see the same authored site grid, stimulus construction, update rule, training schedule, and downstream nearest-region readout. Exact coordinate localization remains absent, and held-out success means the winning unit's learned center falls in the correct nearest-site region, not that the network represents the held-out coordinate precisely.

## Integrity and artifacts

The raw capture passes schedule, exposure, write, probe-matrix, activation reconstruction, argmax, frozen-weight, and source-stability checks. The independent analyzer reconstructs all 900 activation vectors and winners and confirms the paired-seed panel. See the [preregistration](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V1_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v1.py), [source lock](../../../evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v1_lock_20261005.json), [raw capture](../../../evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_20261005.json), [independent analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v1.py), and [analysis](../../../evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_analysis_20261005.json).

## Next gate

Replicate the morphology contrast under a second site-grid arrangement and at least one changed patch scale while preserving matched exposure and frozen probes. Keep nearest-region transfer and exact coordinate localization as separate outcomes. Then compare against an explicit coordinate/interpolation baseline and report training/update work and inference cost, not just accuracy. Do not pool this authored map result with production image-ingestion or semantic-recognition evidence.
