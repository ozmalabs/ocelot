# Shared-substrate multi-sheet fixed-frame diagnostic v1.5 preregistration

## Question
Does the exact B phase-zero, orientation-zero grating produce B SUnit activity when A is blank, and does simultaneous A stimulation change B's endpoint activity?

## Fixture and controls
Rebuild the v1.4 two-sheet fixture with seed 20260934 in root-scoped mode. Repeat its 3,000-step retinal development per sheet and 2,000 paired random-grating adaptation presentations. Freeze the same learning parameters and capture one prepared graph snapshot. Restore that snapshot before each of four conditions: (1) A blank/B blank, (2) A blank/B exact v1.4 grating, (3) A exact v1.4 A grating/B blank, and (4) both exact gratings. The B grating is `binarize(grating((16,16), 0°, 0, period=4))`; A is `binarize(grating((16,16),45°,0.3,period=4))`.

## Measurements
For each condition, record exact stimulus pixel/burst counts, per-unit B `rate` and `act`, closure terminal status and cumulative progress, and prepared-state hash. Save partial results after each condition. Do not update weights between conditions. Lock protocol, runner, v1.4 runner/analyzer, seed manifests, Python source closure, native extension/build manifest, and engine provenance before execution; verify source stability afterward.

## Decision rule
If B's exact grating yields positive B SUnit activity with A blank and lower/zero activity with A active, this supports an A/B interaction in this fixture. If B is silent in both B-grating conditions, v1.4's broad tuning sweep does not validate this exact frame; investigate stimulus/readout alignment before claiming cross-sheet suppression. This four-condition, one-seed test does not establish prevalence, general scope safety, or tractability at scale.
