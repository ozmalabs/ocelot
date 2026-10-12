# Task-generated residual transfer v1.1 timing amendment

**Date:** 2026-10-01, after completing the v1 semantic panel and before the v1.1 capture.

## Reason

The v1 analyzer found that module import time was included in each episode's measured route total, but Python imports were cached after the first episode in a worker. The arm-order schedule was counterbalanced, yet only eight workers were used and the actual cold-import cost was large enough to distort the per-arm median. The v1 task-semantic and receipt-parity gates remain valid; v1 timing totals are retained as diagnostic and are not used for the v1.1 timing comparison.

## Amendment

Use a new source lock and new raw/analysis output paths. Before any arm starts, import the common-ground task dependencies once in each worker process and report that cold import interval at worker level. Keep per-episode measured route time as the sum of adapter/seed setup, event construction, branch setup, ordinary rule closure, journal readout, receipt adoption, and terminal probe. Do not charge worker-level cold import time to whichever arm happens to run first. Continue to report oracle graph serialization separately from the route stages. The task schedule, arm implementations, semantic/parity gates, and eight-worker count do not change.

This amendment corrects timing attribution only. Do not overwrite or pool v1 measurements with v1.1. Both captures remain available, with v1 serving as the completed semantic pilot and v1.1 as the confirmatory stage-timing capture.
