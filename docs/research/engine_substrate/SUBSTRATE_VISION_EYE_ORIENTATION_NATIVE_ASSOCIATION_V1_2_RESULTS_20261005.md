# Native orientation association v1.2 results

## Result

The source-locked six-seed capture and independent analyzer pass all gates. Training schedules, learned visual weights, and association counts match v1.1 exactly; association counts reconstruct from the recorded native training activations. All 192 worker probes return exactly one native prediction, and associations and visual weights remain frozen during probes.

On 48 position-held-out examples, the Euclidean prototype readout is correct on 34 (19/24 horizontal, 15/24 vertical). The paired v1.1 dot-product readout scores 30/48 (20/24 horizontal, 10/24 vertical). Per-seed v1.2 versus v1.1 correct counts are: seed 40, 5 vs 6; 41, 5 vs 4; 42, 6 vs 4; 43, 7 vs 6; 44, 6 vs 6; 45, 5 vs 4. Thus four seeds improve, one declines, and one ties. Exact reconstructed prototype-distance ties occur on 0/48 held-out probes.

The external nearest-class-mean control scores 31/48 (16/24 per class); the initial random projection scores 29/48 (16 horizontal, 13 vertical); centroid/count scores 24/48; and a translation-aware pixel template scores 48/48. Median closure cost is 8.21 ms per training step. The result is exploratory because this readout was chosen after observing v1.1's class bias. It suggests that prototype-distance calibration can reduce the bias on this fixed synthetic panel; it does not establish a general advantage or autonomous readout invention.

## Interpretation and next gate

This is supervised graph-resident association and prediction under externally authored labels, grammar, and rules. No substrate-selected representation, update rule, or task definition was evaluated. The next capability gate should seal held-out outcomes while allowing substrate-side selection among a bounded set of representations or update/readout rules, and charge all candidate evaluation cost. Replicate that gate on independently generated feature families before making claims about reusable learning.

## Reproduction and artifacts

The post-result protocol is [v1.2 preregistration](SUBSTRATE_VISION_EYE_ORIENTATION_NATIVE_ASSOCIATION_V1_2_PREREG_20261005.md). Reproduce with the [source-locked runner](../../../evaluation/substrate_capability/vision_eye_orientation_native_association_v1_2.py), then run the [independent analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_orientation_native_association_v1_2.py). Raw capture: [JSON](../../../evaluation/reports/vision_eye_orientation_native_association_v1_2_20261005.json). Analyzed results: [JSON](../../../evaluation/reports/vision_eye_orientation_native_association_v1_2_analysis_20261005.json). Source lock: [JSON](../../../evaluation/substrate_capability/vision_eye_orientation_native_association_v1_2_lock_20261005.json).
