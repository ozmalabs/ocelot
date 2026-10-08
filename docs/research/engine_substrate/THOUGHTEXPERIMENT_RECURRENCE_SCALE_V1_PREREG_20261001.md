# Recurrence repair thoughtexperiment scale v1 — preregistration

**Question:** Does the recurrence-repair branch lifecycle retain its semantic behavior and backend performance profile as unrelated graph size grows?

Run the v2 task and oracle at 0, 50k, 100k, and 200k unrelated noise nodes, holding the 64 recurrence candidates and authored repair fixed. Cross eager full-copy and shared graph-page forks with fanout 1 and 8. For every cell, run paired sequential and concurrent waves in alternating order across three fresh processes (48 workers total). Record wave wall time, branch throughput, summed per-branch thread CPU, CPU/wall overlap, and sampled RSS/PSS at 10 ms. Use the existing recurrence candidate-level exactly-one-offer oracle, five closure rounds, fixed-point check, authored rule restoration check, and primary graph/rule isolation check.

**Gates:** 48 distinct worker processes; all size/backend/fanout cells; exact semantic signature parity between sequential and concurrent waves; every branch valid for all 64 candidates; unchanged primary state; stable source hashes and matching native binary; finite positive timings and nonnegative sampled memory deltas.

**Limits:** One authored recurrence-repair family, one host, three repeats per cell, and synthetic unrelated path noise. Candidate count is fixed, so this isolates graph-size effects only. RSS/PSS are sampled at 10 ms and are not allocator or kernel peak measurements. Timing ratios are descriptive for this host and protocol, not asymptotic proofs or natural-task prevalence estimates. No candidate discovery or rule invention is evaluated.
