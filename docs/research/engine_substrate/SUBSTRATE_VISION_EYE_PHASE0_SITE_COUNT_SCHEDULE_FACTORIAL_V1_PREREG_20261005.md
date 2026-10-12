# Phase-0 site-count × schedule factorial v1 preregistration

**Question.** Does four-site localization fail because of site count, one-step interleaving, or both, relative to a paired two-site control?

**Design.** Cross site count (2, 4) with schedule (one-step interleaved, blocked) on seeds 15, 16, and 17. Every site receives 4,000 presentations at `ph0_eta=0.005`; total steps are 8,000 for two sites and 16,000 for four. Two-site centers are `(5,5)` and `(12,12)`. Four-site centers are `(3,3)`, `(3,12)`, `(12,3)`, and `(12,12)`. Each stimulus is an identical filled 3×3 square. For each seed/cell, rotate the site order by `seed mod site_count`; interleaved cycles through that order every step, while blocked presents each site for 4,000 consecutive steps. Thus all cells are paired by seed and matched on per-site exposure, with schedule transition count measured directly.

**Frozen probes.** Freeze through `EyeParams.frozen=1.0`; test each trained location and a fixed set of held-out locations for that site count, three repetitions each. Verify unique native winners, exact weight preservation, and compute activation vectors independently from captured weights.

**Scoring.** Exact localization requires the winning unit center within <1 cell of the presented center and spread <3 cells. Separately report whether the winning field maps to the nearest trained site's region. Keep site-count, schedule, and trained/held-out results separate. Coarse region assignment is not continuous interpolation.

**Gates and limits.** Require all 12 workers, exact per-site exposure and total-step schedules, exact switch/write counts, complete probe matrices, positive progress, source-lock stability, and activation/winner parity. This is one authored retinotopy mechanism and cannot establish a general capacity law or natural vision result.
