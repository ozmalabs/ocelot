# Current-source connected discourse task census v2

## Question

Does the source-locked current Goal-identity rule path preserve the task/frame structure and closure semantics of the earlier ten-event connected-dialogue capture, and what graph/candidate/Term work does it record?

## Design

Replay the existing ten-event fixture incrementally through the current `conversation_discourse_state` seed in three fresh processes: plain, runtime-access trace, and repeat. Materialize and settle after each event, preserving the original runner's sequencing. Record whole final graph, task event/Goal frame ownership, direct cross-frame edges, frame-to-global boundary incidences, exact width of the declared frame interaction graph, per-checkpoint closure counters, per-rule counters, and trace rows.

The current seed's explicit event-to-Goal identity relation is part of the run. The analyzer independently checks the fixture frame assignment, terminal Goal lifecycle and event provenance, graph equality across processes, counter conservation, graph structure, boundary counts, and interaction width. All source inputs, including this runner, analyzer, protocol, fixture, seed, materializer, native extension/build manifest, Cargo lock, and relevant Rust files, are frozen in a content-hash lock before capture.

## Limits

This is a source-locked replication on the same authored fixture, not an independent task sample. The prior v1 capture had incomplete recoverable source identity; v2 is a new evidence record and does not overwrite v1. Frame labels remain fixture-derived. Runtime trace coverage is partial and does not prove dependency completeness. Timing values are descriptive for this machine and fixture only; no locality speedup or asymptotic conclusion is claimed.

## Reproduction

Generate the lock with `PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/substrate_discourse_connected_task_census_v2.py --lock`, review it, then run the script with the same environment. Analyze with `python3 scripts/analyze_substrate_discourse_connected_task_census_v2.py`.
