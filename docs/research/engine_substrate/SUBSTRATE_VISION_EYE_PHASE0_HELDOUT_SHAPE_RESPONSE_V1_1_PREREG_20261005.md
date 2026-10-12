# Phase-0 held-out shape response v1.1 preregistration

**Question.** After learning two spatial receptive fields from a 3×3 square and a five-cell plus, does a unit centered on each trained location still win when presented with a never-trained five-cell X at that location?

**Training.** Use fresh source-locked workers for seeds 6, 7, and 8. On a 16×16 retina, alternate a filled 3×3 square centered at `(5,5)` and a five-cell plus centered at `(12,12)` one step at a time for 8,000 steps, 4,000 exposures each. Use four WUnits, `ph0_eta=0.005`, and the same phase-0 authored rules. Capture learned weights after training.

**Probe.** Set the authored `frozen` parameter to 1.0, then present five repetitions each of the seen square at site A, seen plus at site B, and held-out five-cell diagonal X at both sites. There are 20 probes per worker. Learning remains frozen; phase-0 activation and WTA rules continue to run. Capture all four unit activations and the unique current-step winner for every probe, then verify weights are unchanged after probing.

**Primary scoring.** Independently recompute each unit's center and RMS spread from saved weights. A probe is location-correct when its native winner's field has center distance <1 cell from the presented site and spread <3 cells. Report seen and held-out probe outcomes separately (10 probes each across three workers). Also recompute each unit's input-mask dot product and require its argmax to match the native winner; this is a consistency check, not an outcome gate.

**Limits.** This tests morphology tolerance at two trained spatial locations for three seeds. X is unseen during training, but both its locations are trained locations. It is not semantic shape classification, new-location transfer, natural-image recognition, or general concept learning. Failures remain in the report; no thresholds are tuned after capture.

**Version note.** The initial v1 runner completed training for its first worker but stopped before probes because it indexed probe labels directly into the training-mask table. It wrote no capture. V1.1 adds an explicit label-to-mask mapping; the schedule, masks, scoring, and conditions are unchanged. The v1 lock and failed execution are preserved.
