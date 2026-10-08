# Recurrence repair parallel thoughtexperiment wave v2 — preregistration

**Question:** After releasing the GIL around experimental forks, does the recurrence-repair task retain its shared-page concurrency gain and gain full-copy CPU overlap?

Repeat the existing 100k-noise, 64-recurrence-candidate repair workload with eager full-copy and shared graph pages, fanouts 1/2/4/8, three fresh processes per cell (24 total), and paired sequential/concurrent waves. Keep the authored rule repair, five closure rounds, per-candidate exactly-one-offer oracle, graph/rule revision checks, and 10 ms RSS/PSS sampler unchanged. Record wave wall, experiments/s, branch thread CPU sum/CPU-wall, and peak memory deltas. Compare directly with v1, whose source/native lock predates the GIL-release fork bindings.

**Gates:** 24 unique processes; all fanout/backend cells and both modes; every branch restores the authored idempotence guard, yields exactly one offer for each of 64 candidates, and reaches fixed point; sequential/concurrent signatures match; primary graph/rule revision remains unchanged; memory/timing values valid; current source/native build lock matches.

**Limits:** One synthetic recurrence task with duplicated candidates and linked noise, one host, three repeats. This is an independent thoughtexperiment workload family, not natural task prevalence or autonomous candidate discovery.
