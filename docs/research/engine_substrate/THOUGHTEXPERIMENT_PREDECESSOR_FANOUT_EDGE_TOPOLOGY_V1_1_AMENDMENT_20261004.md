# Thoughtexperiment predecessor fanout edge-topology v1.1 amendment

Date: 2026-10-04

## Reason for amendment

The preregistered v1 run attempted its complete 24-worker schedule, but all
workers failed before lifecycle measurement because the fixture passed Python
integers to the native edge API, which requires `NodeID` values. The failure is
preserved in `thoughtexperiment_predecessor_fanout_edge_topology_v1_20261004.json`
and its original lock. It is not evidence about candidate or backend behavior.

## Correction and design preservation

Version 1.1 wraps both endpoint IDs with the native `NodeID` constructor. It
retains the exact 24 cells, randomized schedule, four topology generators,
100,000 background nodes, 99,999 background edges, and candidate/task
configuration. It also records the time spent constructing the added topology
on both the primary and direct-oracle workload separately from the lifecycle;
this is an added descriptive measure and does not affect lifecycle timing.
The amended runner, analyzer, this amendment, and the existing source-locked
cost breakdown/baseline artifacts receive a new lock before the rerun.

No other exclusions or schedule changes are introduced. The v1.1 capture must
still satisfy every semantic and provenance gate in the original protocol,
plus the two-call topology setup-time check, before any timing comparison is
reported. The claim limits in v1 remain unchanged.
