# Phase-0 four-site schedule replication v1 preregistration

**Question.** Does the blocked-training rescue for a four-site, four-unit map replicate across six new seeds, relative to one-step interleaving?

**Design.** Use seeds 18–23, crossing each across blocked and interleaved schedules (12 fresh workers). Train identical filled 3×3 patterns at `(3,3)`, `(3,12)`, `(12,3)`, `(12,12)`, with four WUnits, a 16×16 retina, and `ph0_eta=0.005`. Every site receives 4,000 presentations (16,000 steps total). Rotate the site order by seed modulo four. Interleaved presentation cycles through the rotated order every step; blocked presentation gives each site a contiguous 4,000-step block. The paired conditions match per-site exposure and differ in transition frequency.

**Frozen probes.** Set and verify `EyeParams.frozen=1.0`. Probe each of four trained sites and the same twelve untrained edge/interior sites from the prior four-site map evaluation three times each, for 48 probes per worker. Confirm learned weights remain exactly unchanged.

**Scoring.** Independently recompute field centers/spreads, unit activations, winners, and nearest trained-site region. Exact localization requires winner center distance <1 cell and spread <3. Report per-seed distinct trained sites covered, exact localization for trained/held-out probes, and coarse nearest-region accuracy separately.

**Gates and limits.** Require source stability, 12 complete workers, six paired seeds, exact site exposure/transition/write counts, all 48 probes, unique winners, weight/activation parity, frozen weights, and positive progress. This is a replication of one authored learning regime, not a universal capacity claim or natural-vision benchmark.
