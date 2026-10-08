# Resource-version and scoped invalidation comparison v1.2

This capture repeats the v1.1 design with per-phase graph snapshots added so initial and resource-only effects are directly verified. All other protocol elements are unchanged: three fresh workers, N=4/16/64, independent per-Microtheory frames, paired global/scoped settlement, external file values keyed by graph revision, and the same four preregistered behavioral gates. The exploratory four-frame pilot and analyzer-failed v1.1 capture are retained separately; only v1.2 will be treated as the corrected capture.

The v1.2 analyzer must check the stored frame projection from each phase, not infer earlier graph state from progress counts or inspect only the final graph. The acceptance gates remain: initial and external-only states reject every target; revision update accepts only frame zero; global and scoped final projections match; and scoped callback work is lower at N≥16. Timings remain descriptive.
