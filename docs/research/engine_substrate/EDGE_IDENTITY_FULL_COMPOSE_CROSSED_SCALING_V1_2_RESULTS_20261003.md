# Edge identity full-compose crossed scaling — results

Date: 2026-10-03

## Result

The current-source capture covers 2/4/8/16/32 eligible identity fields crossed
with 0/1,000/10,000 unrelated nodes: 15 cells, one warmup and three measured
trials per cell. The independent analyzer passes all 45 trials. The composer
selects the exact `actor+verb` identity guard in every trial, preserves the
active primary rule store, and the target rule materializer creates exactly
the enumerated candidate-site count. At 32 fields this is 530 total sites
(529 singleton/pair/full-set attribute signatures plus one relation site).
The 600-site cap is not reached.

Median composition time by field count across 0/1,000/10,000 noise nodes:

| Fields | Candidate sites | 0 nodes | 1,000 nodes | 10,000 nodes |
|---:|---:|---:|---:|---:|
| 2 | 4 | 16.46 ms | 15.39 ms | 16.68 ms |
| 4 | 12 | 15.66 ms | 15.63 ms | 16.15 ms |
| 8 | 38 | 16.98 ms | 16.94 ms | 17.89 ms |
| 16 | 138 | 16.36 ms | 24.86 ms | 16.84 ms |
| 32 | 530 | 18.93 ms | 18.02 ms | 17.77 ms |

Within this synthetic workload, increasing field count increases materialized
candidate sites quadratically, while compose latency stays in the same broad
15–25 ms band. The single 24.86 ms median cell at 16 fields has substantial
trial variation; three replicates do not resolve a subtle trend. Unrelated
node count has no consistent directional effect in this 0–10,000 range.
Measured RSS before/after composition is recorded per trial, but it is
process-level and page-granular, not a peak or candidate-attributed memory
measurement. Graph setup and explicit site-materializer timings are separate
from compose latency.

## Scope

This closes the previously missing crossed, current-source full-composer
microbenchmark for supplied rules and cues, including enumeration,
`EditSite` materialization, native overlap selection, and variant creation.
The input is synthetic; extra fields are bound copies of the actor attribute.
It does not measure residual-to-cue grounding, autonomous candidate
generation, natural-task prevalence, frame locality, memory-capped refusal,
or scaling above 10,000 unrelated nodes. It therefore strengthens the bounded
execution-cost envelope but does not demonstrate autonomous self-improvement
or broad tractability.

The first v1 and v1.1 captures remain preserved as diagnostics: v1 counted
nodes on the caller graph although the composer works on a private copy; v1.1
fixed that instrumentation but included an unaccounted preexisting `object`
identity field. Neither diagnostic capture is used in the result above.

## Artifacts

- [Base preregistration](EDGE_IDENTITY_FULL_COMPOSE_CROSSED_SCALING_PREREG_20261003.md), [v1.1 instrumentation amendment](EDGE_IDENTITY_FULL_COMPOSE_CROSSED_SCALING_V1_1_AMENDMENT_20261003.md), and [v1.2 field-count amendment](EDGE_IDENTITY_FULL_COMPOSE_CROSSED_SCALING_V1_2_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_edge_identity_full_compose_crossed_scaling_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_edge_identity_full_compose_crossed_scaling_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/edge_identity_full_compose_crossed_scaling_v1_2_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/edge_identity_full_compose_crossed_scaling_v1_2_20261003.json)
- Preserved [v1 diagnostic](../../../evaluation/reports/edge_identity_full_compose_crossed_scaling_v1_20261003.json) and [v1.1 diagnostic](../../../evaluation/reports/edge_identity_full_compose_crossed_scaling_v1_1_20261003.json)
