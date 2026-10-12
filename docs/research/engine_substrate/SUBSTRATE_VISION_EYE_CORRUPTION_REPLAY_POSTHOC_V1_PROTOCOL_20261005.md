# Vision-eye corruption replay — post-hoc protocol

This is a diagnostic on the completed v2.1 phase-0 capture, not a preregistered confirmatory experiment. It uses the captured learned WUnit weights and applies the readout independently. The clean activation and argmax equation was already reconstructed for every captured probe; this replay does not rerun the Rust scheduler or alter weights.

For every held-out probe in the 12 captured workers, construct four deterministic perturbation conditions: random removal of 25%, 50%, and 75% of active mask pixels, and random addition of background pixels at 25% and 50% of the original mask area (rounded up). A SHA-256-derived per-probe/per-condition seed selects pixels. Use the same corrupted mask for all three scorers: (1) learned WUnit weight-sum argmax using captured weights; (2) active-pixel centroid mapped to nearest training-site region; and (3) nearest training exemplar under Hamming distance, scored as a set when templates tie.

Retain the uncorrupted result as a parity baseline. Report region accuracy, tie/ambiguity rates, coordinate error, and counts at each corruption dose, separated by morphology and scorer. Keep the six seed pairs descriptive; do not pool trained probes or infer natural-image robustness.

The fixed captures, analyzer source, and this protocol are hash-recorded in the report. Required gates: both source-locked captures and independent analyses pass; all six seed workers per morphology and all 48 held-out probes per worker are present; every clean learned prediction reproduces the existing activation/argmax result; every perturbation is deterministic and uses one identical input mask across scorers; all grouped denominators reconcile to 288 per morphology/condition.

Claim boundary: synthetic binary retinotopy masks only. This evaluates frozen-weight readout robustness under these pixel perturbations; it says nothing about online adaptation, scheduler overhead, semantic vision, or natural images.
