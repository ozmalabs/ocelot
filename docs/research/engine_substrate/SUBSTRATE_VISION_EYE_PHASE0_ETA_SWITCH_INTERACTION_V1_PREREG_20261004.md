# Phase-0 visual plasticity-rate × switching interaction v1

**Question.** Can increasing `ph0_eta` rescue two-location localization under one-step switching, or does it destabilize learning? A 100-step baseline provides a moderate-switch reference.

**Design.** Fresh graphs cross seeds 0/1/2 with five conditions: one-step switching at `ph0_eta` 0.0005, 0.001, 0.002, or 0.005, and 100-step switching at the baseline 0.0005. There are 15 workers. Each has 8,000 steps, the same two fixed 5×5 patches, 4,000 exposures per location, four units, and a balanced initial location (`seed mod 2`). Capture all 256 weights per unit at steps 4,000 and 8,000; record switch count, host input-update time, native closure time, progress, and cache occupancy.

**Scoring.** Independent analysis recomputes each unit's weighted receptive-field center and RMS spread. A location is localized if any unit has spread <3 cells and center distance <1. Report the number retaining both locations out of three for every condition. No eta is assumed to pass; excessive plasticity may broaden or destabilize receptive fields.

**Gates.** Require source stability, all 15 complete workers, exact exposure/switch/write schedules, nonzero progress, active-count 25 and nonempty Argmax occupancy at both checkpoints. This captures the trade between transition frequency and update magnitude. It cannot hold transition work fixed because all one-step eta arms receive the same sequence and write volume, while the 100-step reference intentionally has fewer transitions.

**Limits.** One authored spatial learner, two locations, four units, one host and three seeds. Results do not establish a general plasticity law, natural-image learning, or general self-improvement. Lock with the runner's `--lock` option; run the capture and independent analyzer without modifying thresholds.
