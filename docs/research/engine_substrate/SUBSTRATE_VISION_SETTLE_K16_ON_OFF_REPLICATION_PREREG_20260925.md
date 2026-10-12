# K=16 settling on/off replication preregistration

Date: 2026-09-25. Two new seeds, four arms, paired within seed. The original 20260928 result remains a separate first observation.

## Question
Does the previously observed response parity and large progress-count reduction when settling is disabled recur on two independently seeded developed/adapted 4×4 lateral sheets?

## Design
Use seeds 20260929 and 20260930. Each seed gets independent settle-on and settle-off worlds. All four arms use the same five benchmark-only `hard_realtime` manifest tags, 3,000 retinal-development steps, 2,000 theta-adaptation presentations, frozen learning during readout, and `cell_stats(key="rate", period=4, K=16)`. The only within-seed intervention is `SettleParams.settle` (1.0 or 0.0), applied immediately before readout. Counterbalance execution order: seed 20260929 on→off; seed 20260930 off→on.

`cell_stats` is expected to call `present` 480 times: 192 orientation/phase tuning presentations, 32 baseline presentations, and 256 F1/F0 phase presentations. Capture every native tick integer return for both adaptation and readout. Treat these as progress counts, not termination labels. Persist a partial record after each completed arm.

## Outcomes and gates
Record full tuning matrices, per-unit OSI, alive counts, weight hashes/drift, adaptation and readout progress values, per-arm timings, and source/native provenance. Independently recompute OSI and paired tuning deltas by seed. Require 2,000 adaptation calls and 480 readout calls per arm; all counts must be positive and below the 200,000 budget. Verify no readout weight drift and exact within-seed adaptation-work parity. Report response parity descriptively; do not reinterpret a nonzero difference post hoc as equivalence. Report timing descriptively only.

This is a two-seed replication, not a prevalence estimate. It tests only this readout and preparation protocol; it does not test trained cortical weights, task-level behavior, or whether settling benefits another objective. Do not change production parameters based on this run alone.
