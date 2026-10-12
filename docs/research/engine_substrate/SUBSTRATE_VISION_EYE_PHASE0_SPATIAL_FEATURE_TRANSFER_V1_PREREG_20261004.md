# Phase-0 spatial feature geometry transfer v1

**Question.** Does the phase-0 learner localize two sites when their spatial activity geometry differs, under rapid interleaving and the empirically supported `ph0_eta=0.005` setting?

**Design.** Three fresh seeds (6, 7, 8) each run two arms for 8,000 steps: a positive control with 5×5 solid patches at `(5,5)` and `(12,12)`, and a mixed-geometry arm with a filled 3×3 square at `(5,5)` and a five-cell plus/cross at `(12,12)`. Alternate the two stimuli every step, giving each exactly 4,000 presentations. Keep the 16×16 retina, four units, native rules, and eta fixed. Capture each receptive field at steps 4,000 and 8,000. Record active counts, transition writes, input-update timing, closure timing, and progress separately.

**Scoring.** Independently recompute weighted receptive-field center and RMS spread from all captured weights. A target is localized if any unit has center distance <1 cell and spread <3 cells. The primary outcome is both targets localized per seed, reported separately for control and mixed geometry. This measures location-centered learning across geometry variation; it does not measure explicit shape classification. Input activity counts differ within the mixed arm (9 versus 5), and that limitation is recorded rather than hidden.

**Gates and limits.** Require source stability, exact six-worker schedule, equal exposures, expected active pattern sizes/write counts, nonzero progress, and nonempty Argmax occupancy. Three seeds per arm are exploratory. Results apply to this authored two-site spatial task, not natural images, semantic categories, or general induction. Lock source/protocol, run capture, then independent analysis.
