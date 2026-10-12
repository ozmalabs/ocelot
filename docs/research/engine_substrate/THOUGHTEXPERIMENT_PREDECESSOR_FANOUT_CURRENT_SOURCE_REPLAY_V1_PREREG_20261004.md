# Thoughtexperiment predecessor fanout current-source replay v1

Date: 2026-10-04

## Question

Does the archived 100,000-noise-node predecessor-dependent thoughtexperiment
case reproduce on the current native engine, and how much lifecycle time is
accounted for by the measurement's named phase timers?

## Fixed design

This is a source-current replication of one earlier exploratory workload, not a
new scale sweep. Use four frames with independent discourse states, four
candidate branches, 100,000 unrelated noise nodes, three replicates, and both
`full_copy` and `shared_graph_pages` snapshot backends. The six backend/replicate
pairs are the entire panel. Reuse the v1.1 workload and semantic checks without
changing candidate construction, task result, closure, residual return, or
stale-revision controls.

Each configuration runs in a fresh worker process. Preserve candidate
correctness, branch/primary isolation, selected-branch versus direct-monolithic
oracle parity, stale-return rejection, graph/rule revision outcomes, node/edge
counts, allocator and RSS samples, lifecycle time, and the existing named
phase timers. Define named-phase coverage as the sum of recorded phase times
divided by lifecycle time. The remainder is lifecycle time outside those
recorded timers; do not attribute it to hashing or another operation without a
timer that measures that operation directly.

## Gates

1. A pre-run source lock covers this protocol, runner, independent analyzer,
   imported v1.1 runner/analyzer, engine and seed sources, native extension,
   build manifest, Cargo lock, and repository commit.
2. Capture exactly six unique worker PIDs matching the fixed matrix; record
   worker failures rather than silently omitting them.
3. Require one selected candidate at the locked correct position in every
   successful row; every decoy must fail target grounding.
4. Require branch and primary graph parity with the direct monolithic oracle,
   primary isolation before return, preserved rules, stale revision rejection,
   and stale retry non-mutation.
5. Require stable source lock before and after capture. Independent analysis
   recomputes all structural, semantic, and timing gates from raw rows.

## Interpretation limits

This confirms one authored 100k-node workload on one host if all gates pass. It
does not estimate natural graph distributions, candidate-generation ability,
general speedup, or a scaling law. The named-phase remainder is diagnostic. A
follow-up must instrument graph export, digesting, and other audit work
separately before claiming which operation dominates. No parameter may be
changed after source lock; a changed design requires a new version and lock.

## Artifacts

- Runner: `evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_current_source_replay_v1.py`
- Lock and capture: corresponding `evaluation/substrate_capability/*lock*` and `evaluation/reports/*20261004.json`
