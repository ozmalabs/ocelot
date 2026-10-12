# Shape-decoding Thoughtexperiment scale v1 — preregistration

**Question:** Do the observed branch setup and concurrent-throughput gains persist as unrelated graph size grows, and does the native rule patch preserve both positive and negative candidate outcomes?

Test unrelated-node sizes 0/10k/50k/100k/200k × scoped full-copy/shared graph pages × sequential/concurrent fanout 8 × 3 fresh workers per cell (60 total). Each fresh worker constructs one graph fixture, computes baseline once, and runs both `dedup_identity_fix` and `add_match_guard(control)` as eight-branch waves, alternating candidate order across repeats. The current default native rule patch and native branch summary are enabled. Record true graph node/edge counts, per-candidate wave wall and summed branch CPU, CPU/wall, phase medians, all branch outcomes, and primary graph/rule invariants. The 100k cells compare to the locked 100k profile v3 and concurrency v3 captures as replication anchors.

**Gates:** 60 unique processes; all size/backend/mode cells present; positive arm all converges and applies the intended repair; negative arm does not converge and remains non-inert; exact semantic signatures match across modes and backends at each size; primary isolation and source/native lock pass; nonnegative timings and internally consistent graph sizes.

**Limits:** One synthetic graph family, one positive and one negative candidate, one host, three repeats per cell. This is a finite size curve, not an asymptotic complexity proof or natural-task distribution estimate. CPU/wall is process-thread CPU divided by wave wall, not a CPU utilization counter.
