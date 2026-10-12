# Thoughtexperiment all-domain selector surface v1 preregistration

## Question

Does scanning every `domains/*.py` implementation module instead of the current speech-oriented surface correct the known reliability-weighted-fusion false-open without falsely closing the two absent generative mechanisms?

## Procedure

Repeat the four source-audited cases and three fresh full-seed workers from [selector calibration v1](THOUGHTEXPERIMENT_SELECTOR_CALIBRATION_V1_PREREG_20261001.md). In each worker, explicitly set `_SPEECH_GLOBS_OVERRIDE` to the sorted complete set of top-level `domains/*.py` modules, then call the same `is_gap` operator for the fixed capability keys. This override is a measurement arm; it does not change production defaults. Record full verdicts, files scanned, boot status, and fingerprints for all top-level domain source files before and after.

## Decision criteria

The proposed surface passes this panel if it closes both implemented cases and leaves both absent cases open in all workers, with identical verdicts across workers, three distinct PIDs, stable boot identities, and stable source hashes. Any false-covered or remaining false-open case means this surface is not sufficient by itself. The four-item panel is selected, not representative; it cannot estimate general selector precision/recall or establish that scanning all domains is the right production policy.

No capability changes are made in this experiment. It evaluates selector coverage policy only, and makes no utility claim. See the [results](THOUGHTEXPERIMENT_SELECTOR_DOMAIN_SURFACE_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_selector_domain_surface_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_selector_domain_surface_v1_raw_20261001.json).
