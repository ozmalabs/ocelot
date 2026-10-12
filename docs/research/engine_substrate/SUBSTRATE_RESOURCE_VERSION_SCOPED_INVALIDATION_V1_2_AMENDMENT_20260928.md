# v1.2 amendment: phase-local state capture

The v1.1 runner completed all 18 cells and preserved the raw capture. Its analyzer incorrectly tested the final frame projection when checking that the initial and resource-only phases had no accepted target. The runner had recorded those phases' progress and callback counts but not their graph projections, so the initial/external-only gate failed and could not be independently reconstructed from the capture. The remaining v1.1 gates—including lock integrity, final parity, and scoped callback-work reduction—passed; v1.1 is retained as analyzer-failed, not discarded.

Before confirmatory v1.2 capture, the runner was amended to store frame revision/acceptance projections after every phase, and the analyzer was corrected to use those snapshots. Inputs, fixture design, execution arms, frame sizes, and acceptance thresholds did not change. v1.2 ran under a new lock and raw path; only its analysis is treated as confirmatory.
