# Scheduler dirty-density and positive-join v1 preregistration

Date: 2026-09-26

## Question

How does monolithic scheduler work change with rule count, the number of dirty rules, and the position of those rules in scheduler order when each dirty rule has one positive match and performs one graph write?

## Design

Use `R={8,32,128}` active rules and selected dirty counts `k={1,R/4,R}`. For each `(R,k)`, select either the first `k` rule slots (prefix) or last `k` slots (suffix). Run three fresh-process replications of every cell. Each native substrate contains two nodes and one rule per distinct trigger/derived edge type. First settle with no trigger edges, then insert one trigger edge per selected rule. Capture counters only around the second closure. Run plain and audit-enabled twins from independently reconstructed identical states.

Each selected rule has a one-edge positive pattern and adds a corresponding derived edge. The independent semantic gate requires fixed-point status, exactly `k` progress steps, exactly `k` derived edges, and exact whole-graph/report parity between audit-on and plain arms.

## Exact scheduler predictions

All `R` rules are external-poll slots per pass; no workload rule reads external state. A selected prefix has its first dirty bit at slot 0, so the short-circuit probe visits 1 slot regardless of `k`. A selected suffix has its first dirty bit at slot `R-k`, so the probe visits `R-k+1` slots. The probe then visits all `R` slots on the clean terminal pass. Therefore:

- passes: 2;
- external poll slots: `2R`;
- fixed-point probe slots: `R + 1` for prefix; `2R-k+1` for suffix;
- dirty-vector scan slots: `R`;
- selected rules: `k`;
- rule enumerations: `k`.

The timing counter is descriptive only. It includes enabled counter overhead and excludes initial setup, trigger insertion, queue drains, matching/application, and other pass work.

## Limits

This is an authored one-edge positive family, not a general matcher or real-task benchmark. It measures one dirty-set transition, not repeated mutation dynamics. It does not characterize scoped/event schedulers, deferred queue populations, frame construction, inferred cuts, natural workload distributions, or useful commodity-scale throughput. Exact work counters and semantic parity are the primary outcomes; report latency only descriptively.
