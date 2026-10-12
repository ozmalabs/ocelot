# Cross-family idempotence transfer v1 — protocol amendment

**Date:** 2026-10-01  
**Status:** Amended before the final three-worker confirmatory replay.

## Reason

A single-worker development probe showed that the recurrence task's cold structural-cost policy already ranks `dedup_identity_fix` first and reaches the independent one-offer oracle in one trial. Requiring transferred history to change the order would therefore reject successful evidence consumption whenever the unconditioned structural prior already makes the same choice. The probe was exploratory, not retained as a confirmatory capture.

## Amendment

Replace the original treatment-difference gate with direct evidence-consumption checks: the cold rank trace must show zero cross-family prior successes; the transfer rank trace must show at least one prior success for the `mrl_offer_due_once` candidate, sourced from the shape-axis task class. Keep the independent task oracle, branch-isolation, source-stability, and fresh-worker gates. Candidate-order change and fewer trials are reported as outcomes, not required gates.

## Preserved interpretation

This amendment distinguishes representation transfer from utility gain. If both arms choose the repair on the first attempt, the result can show that the graph-authored policy consumed cross-target evidence, but must report no demonstrated search-cost reduction. The original preregistration remains available to document the initial design.
