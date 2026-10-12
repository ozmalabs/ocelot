# Phase-0 visual switching-dose v1 preregistration

**Question.** Does two-location receptive-field retention vary with the interval between switches, when total exposure to each location is held at 4,000 steps?

**Design.** Use fresh phase-0 `vision_eye` graphs for three paired initialization seeds (0, 1, 2) and five fixed block lengths (1, 10, 100, 1,000, and 4,000 steps), for 15 workers total. Present the two fixed 5×5 patches at `(5,5)` and `(12,12)` for 8,000 steps on a 16×16 retina. Every schedule alternates locations at the assigned block length; each location receives exactly 4,000 exposures. Start location is `seed mod 2`, balancing the initial location across seeds. Capture all four 256-weight receptive fields at steps 4,000 and 8,000. Record switches, host-side input writes and update time, native closure time, progress, and Argmax cache occupancy separately.

**Scoring.** An independent analyzer recomputes weighted centers and RMS spread from raw weights. A location is localized if at least one unit has spread <3 cells and center distance <1 cell. Report retained-both count out of three for each switching interval, without pooling across intervals.

**Gates and interpretation.** Capture gates require source stability, exact schedules/exposures, 15 complete workers, 25 active cells, nonzero closure progress, and nonempty Argmax occupancy. The capability outcome is descriptive; no required dose is assumed to pass. Input-update counts are an explicit covariate: switching itself requires changed cell facts, so time/cost comparisons do not isolate a purely neural-memory effect. The seed-level pairing and balanced starting location reduce, but do not eliminate, initialization variability.

**Limits.** This is one authored two-location visual rule family with four units and three seeds. It does not measure larger codebooks, natural images, feature transfer, or autonomous structural induction. Lock sources with `vision_eye_phase0_switching_dose_v1.py --lock`, run the capture, then the independent analyzer. Preserve all artifacts immutably.
