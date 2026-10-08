# CAN width-two ladder inference scale results

**Status:** exact junction-tree MAP matches an independent ladder dynamic-programming oracle through 1,024 variables on the measured width-two family.

The preregistered sweep covered 16–512 rungs (32–1,024 Concept nodes), three fresh-process replicates each. Runtime extraction exactly reproduced the generated unary and pair factors in all 18 workers. Every min-fill ordering reported width 2 and bag size 3; junction-tree MAP under both min-fill and an explicit rung elimination order matched the independent four-state rung-DP energy in all workers.

Median exact MAP time using min-fill increased from 4.45 ms at 32 variables to 77.67 ms at 1,024 variables. The independent rung-order MAP was 4.26–76.04 ms over the same endpoints. Generic min-fill ordering increased from 0.62 ms to 439.83 ms and dominated end-to-end cost at the largest size. Median traced Python inference allocation grew from about 60 KB to 937 KB for min-fill, approximately with variable count. RSS includes interpreter/import baseline, and traced allocation excludes native memory.

This extends the synthetic bounded-width inference evidence from paths (width one) to ladders (width two). It does not measure separator discovery, natural-task locality, or general graph scaling.

Protocol: [width-two ladder preregistration](CAN_WIDTH_TWO_LADDER_SCALE_PREREG_20260925.md). Runner: [scale runner](../../../scripts/can_width_two_ladder_scale.py). Lock: [content lock](../../../evaluation/substrate_capability/can_width_two_ladder_scale_lock_20260925.json). Raw report: [18-worker record](../../../evaluation/reports/can_width_two_ladder_scale_20260925.json).
