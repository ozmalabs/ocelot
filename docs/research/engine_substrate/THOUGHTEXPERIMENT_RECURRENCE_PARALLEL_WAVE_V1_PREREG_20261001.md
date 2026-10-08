# Recurrence repair parallel thoughtexperiment wave v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does shared-graph-page CoW increase the throughput of concurrent, task-shaped repair rehearsals on a 100k-node substrate?

## Design

Start from the existing recurrence-ledger single-guard fault, expand its task graph to 64 independent recurrence candidates with one supporting segment each, and add a 100k-node linked noise graph. Compare native full-copy and shared-graph-page backends at fanout 1, 2, 4, and 8. In each fresh process, run a sequential control that forks, restores the known authored guard, runs native closure, validates all 64 candidates, and drops each branch before proceeding. Then run an equivalent threaded wave from the same unchanged primary; each thread forks its own branch and executes closure. `run_rules` releases the GIL, so the wave can measure native parallel closure after branch creation. Three fresh processes per backend/fanout cell (24 total); backend and fanout order alternate. Sample Linux `smaps_rollup` every 10 ms through both waves.

## Gates

- Eight backend/fanout cells and 24 unique fresh processes complete with source and native-binary lock parity.
- Every branch restores the original rule, produces exactly one offer for each of 64 candidates, and reaches a zero-progress fixed point.
- Sequential and concurrent outcomes match; all primary graph/rule revisions and counts remain unchanged.
- Report sequential and concurrent wall time, experiments/second, sampled peak ΔPSS/RSS/private-dirty, and per-worker closure progress.

## Interpretation limits

One synthetic task family and host; candidates share a common rule/task structure, and the noise graph is a linked path. This measures concurrent known-repair application, not candidate discovery, independent task diversity, natural workloads, or service isolation. A 10 ms sampler can miss brief peaks. Fork operations are serialized by the Python API lock; the measured native rule-closure phase can overlap across branches.
