# Single-rule native closure scale v1 preregistration

Date: 2026-09-28

## Question

How do native candidate work, closure CPU/wall time, and process memory scale when one monotone rule settles a sparse attributed graph from N=10k through 10M nodes? Does every seeded node reach the independent terminal-state oracle at each size?

## Workload

Each fresh process builds a directed ring of N `WorkItem` nodes and N `next` edges, with attrs `status="pending"`, integer `ordinal=i`, and integer `bucket=i mod 64`. It declares the `(WorkItem,status)` attribute index so the final oracle can check all N nodes without exporting or copying the graph. One rule matches `x -next→ y`, requires `x.status == "pending"`, and sets `x.status = "done"`. This monotone transition should settle exactly N WorkItems and preserve all nodes/edges. Sizes are 10k/100k/1M/10M, with two fresh-process replicates per size and audit mode. Audit-on/off are crossed as separate workers (16 total); graph sizes, construction, and rule are identical.

Record source/native provenance, node and edge construction time, index declaration time, rule install time, closure wall/CPU time, closure report, exact native per-rule/global candidate and effect counters when auditing is on, RSS before/after each stage, index-backed counts for pending and done states, and graph node/edge counts. Compare audit-on/off semantics and counts within every `(N,replicate)` pair. Keep setup and validation time separate from closure time; report total build+index+install+closure separately.

## Gates

- Sixteen unique worker processes; two replicates for each N × audit setting.
- Stable parent, worker-start/end source and native fingerprints; nonstale native build.
- Exactly N nodes and N ring edges; all sampled ring neighbors are correct.
- Closure reaches fixed point without budget overshoot; exact N done, zero pending, and exact N node/N edge counts.
- Audit-on/off graph projection, terminal index counts, closure status, progress, and passes agree for each pair.
- Positive construction/index/install/closure timers and source-linked per-rule candidate/effect counter conservation on audit-on workers.
- Preserve all raw records, including resource failure; do not substitute smaller sizes after observing outcomes.

## Claim limits

This is one favorable, single-rule, one-edge monotone workload over a ring. It does not measure interacting rules, arbitrary attribute selection, fresh-name minting, dynamic boundaries, deletions/reuse, representative seed boot, inference, or realistic task distributions. Audit counters are opt-in and timing is paired with audit off. The maintained index is part of the measured memory and the final oracle; its overhead must be reported. Four sizes and two replicates do not prove asymptotic complexity.
