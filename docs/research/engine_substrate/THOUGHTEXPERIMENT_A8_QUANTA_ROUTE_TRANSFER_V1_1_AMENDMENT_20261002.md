# Thoughtexperiment A8 quantum-route transfer v1.1 — integer fixture values and setup preflight

**Date:** 2026-10-02  
**Reason:** v1's order capture passed all graph-attribution and no-cue gates, but its score process failed before task evaluation because `space_quantize`'s `passable_values` argument is an integer set and the runner supplied a float.

Change the fixture to use integer `4` for passable floor values, matching the production quanta navigation test contract. Add a lock-time preflight that builds both held-out world structures, runs `space_quantize`, and verifies that each fixture has passable quanta and its intended wall/portal split before freezing the source lock. The preflight must not run navigation outcomes or expose candidate utility. Then capture new order workers, recheck the graph-route, target-preservation, and no-cue abstention gates, and only then run held-out scores. Keep the v1 lock/orders unchanged.

This amendment repairs harness setup only. All portal-route utility, candidate controls, receipt, isolation, and cost claims remain unmeasured until a valid v1.1 score capture and analyzer pass.
