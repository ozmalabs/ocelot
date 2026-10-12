# Phase-0 four-site map and held-out interpolation v1 preregistration

**Question.** Does increasing the learned map from two sites to four improve frozen localization at unseen positions between them?

**Training.** Three fresh workers (seeds 12, 13, 14) use four WUnits and a 16×16 retina. Train on identical filled 3×3 masks centered at the four corners `(3,3)`, `(3,12)`, `(12,3)`, `(12,12)`. Cycle sites one step at a time for 16,000 steps at `ph0_eta=0.005`, giving 4,000 exposures per site. Balance the first site by seed modulo four. Capture all four receptive fields after training.

**Frozen probes.** Set and verify `EyeParams.frozen=1.0`. Present the same 3×3 mask at each of the four trained centers and twelve held-out centers: edge-interior points `(3,6)`, `(3,9)`, `(6,3)`, `(9,3)`, `(6,12)`, `(9,12)`, `(12,6)`, `(12,9)` and interior points `(6,6)`, `(6,9)`, `(9,6)`, `(9,9)`. Repeat each location five times, for 80 probes per worker. Require exact learned-weight preservation through probing.

**Scoring.** Independently recompute each receptive-field center/spread, the native activation vector from captured weights, and its WTA result. A probe is exactly localized when its winning unit is within <1 cell of the presented center and has spread <3. Separately score whether the winning unit's learned field maps to the nearest trained site's Voronoi region. Report trained and held-out results independently. The nearest-region measure is coarse classification, not continuous interpolation.

**Gates and limits.** Require source-lock stability, three complete 16,000-step workers, exactly 4,000 exposures per training site, exact switch/write schedule, all 80 probes/site repetitions, unique winners, activation/weight parity, frozen weights, and nonzero progress. A four-unit/four-site result does not establish larger-map capacity or natural vision. No outcome thresholds will be tuned after capture.
