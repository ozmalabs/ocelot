# Phase-0 eta-rescue replication on held-out positions v1

**Question.** Does the 10× `ph0_eta` rescue observed under stepwise switching replicate on new initializations and different retinal coordinates?

**Design.** Run fresh graphs for seeds 3, 4, and 5, two fixed location pairs (original `(5,5)/(12,12)` and held-out `(3,12)/(12,4)`), and two eta values (0.0005 baseline and 0.005 rescue), for 12 workers. Every worker receives 8,000 alternating one-step presentations, exactly 4,000 per location, with the initial site balanced by `seed mod 2`. Keep four WUnits, 16×16 retina, 5×5 patches, and all other settings fixed. Capture all four receptive fields after 4,000 and 8,000 steps; record identical schedule/work counts and input/closure times separately.

**Scoring.** Independently compute weighted center and RMS spread from raw weights. A location is localized if at least one unit has spread <3 cells and center distance <1 cell. Report both-location retention out of three separately for each pair and eta. No outcome threshold is used to alter the capture or scoring.

**Gates and limits.** Require source stability, exact 12-cell factorial, 8,000-step horizon, equal exposure/write schedules, progress, active count 25, and nonempty Argmax cache. Three new seeds give an out-of-sample initialization check; the second pair tests spatial transfer within the same authored learner, not a new feature class. The experiment does not establish general vision or autonomous self-improvement. Lock, capture, and run the independent analyzer as separate steps.
