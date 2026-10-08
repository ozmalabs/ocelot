# Phase-0 novel-shape, novel-location response v1 preregistration

**Question.** After learning two spatial fields from a square and plus at two sites, can the frozen substrate preserve location-specific WUnit winners for a never-seen X shape at those sites, and does that behavior transfer to locations never used during training?

**Training.** Use fresh workers on seeds 9, 10, and 11. Train 8,000 one-step alternating presentations of a filled 3×3 square at `(5,5)` and a five-cell plus at `(12,12)`, 4,000 exposures each, with four WUnits and `ph0_eta=0.005`. Keep the same phase-0 rules and 16×16 retina.

**Frozen probes.** Set and read back `EyeParams.frozen=1.0` through `domains.eye_world.set_params`. Present five repetitions each of the seen square at `(5,5)`, the seen plus at `(12,12)`, and the held-out five-cell diagonal X at each of four sites: the two trained sites plus novel sites `(5,12)` and `(12,5)`. This yields 30 probes per worker and 90 total. Verify learned receptive-field weights are exactly unchanged after the probes.

**Scoring.** The native WUnit winner is location-correct if its independently recomputed field center is within <1 cell of the presented location and RMS spread is <3 cells. Report four cells separately: each seen shape at its trained site, X at trained sites, and X at novel sites. Recompute the weight/input-mask dot products and check all native activation values and winners; those are execution-integrity checks rather than capability outcomes.

**Limits.** The unseen locations are tested zero-shot with a two-site map; a failure there means the measured representation does not interpolate under this setup, not that the substrate lacks all spatial generalization. This is not a natural-image task, semantic shape classification, or broad capability score. Preserve all outcomes and do not change thresholds after capture.
