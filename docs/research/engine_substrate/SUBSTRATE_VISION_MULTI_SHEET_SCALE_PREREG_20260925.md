# Multi-sheet vision fold coupling scale preregistration

Date: 2026-09-25. Repeated native semantic/work probe extending the minimal two-root result.

## Question

Does the authored global SUnit competition term let one full sheet alter another sheet's computed response as sheet population grows, and does a benchmark-only root-scoped fold remove that cross-root dependency while preserving each sheet's isolated equation?

## Workload and arms

For each of three fixed seeds (4101, 7301, 10703) and side lengths 2, 4, 8, and 16, build one substrate containing two distinct `World` roots. Each owns an n×n SUnit lattice with directed eight-neighbour connectivity. Set every A `act` to 1; set every B `act` to either 0 or 1. Set A afferents deterministically from the seed and B afferents to zero. Initialize `act_next=-1`. Load only `vision_settle.st_settle` plus its singleton `SettleParams`. Compare four fresh-substrate arms: global/B=0, global/B=1, scoped/B=0, scoped/B=1. The scoped clone replaces only the two global `NodesOfType(SUnit)` terms with `Neighbours(r, has_sunit)`. Counterbalance arm order by seed index.

Enable the existing opt-in native scale audit and per-rule counters. Invoke native `run_rules` with a fixed 10,000-application ceiling. Record progress, both output arrays, counters, root membership, graph size, and provenance. Independently recompute the settlement equation from inputs and the selected global or per-root mean. Require residual ≤1e-12, exact root membership, global B=0 versus B=1 to change A, and scoped B=0 versus B=1 to leave A exactly unchanged. Do not interpret the progress return as a termination reason; retain cap status.

## Claim limits

This is a synthetic two-root, one-rule workload through 512 total SUnits. It measures cross-root dependence and attributed work, not natural-workload prevalence, full-cortex quality, learning, or commodity-scale performance. The scoped rule is a benchmark clone; no production seed or scheduler changes.
