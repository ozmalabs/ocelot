# Single-rule native closure scale v1 pilot amendment

Date: 2026-09-28, before the confirmatory lock.

Two 10k-node runner smoke workers were executed before locking: one audit-off and one audit-on. Both reached fixed point with exactly 10k done, zero pending, and N/N ring structure. The audit-on smoke observed 20,000 candidate tests, 10,000 attribute-set attempts, and 80,000 Term evaluations. These runs confirmed rule wire syntax, ring construction, and the indexed terminal-state readback. They are exploratory setup pilots and are excluded from all confirmatory worker counts, estimates, and parity pairs.

The registered panel remains 16 fresh workers over 10k/100k/1M/10M × audit on/off × two replicates. The confirmatory runner, analyzer, pilot disclosure, and base protocol are included in the source lock.

From the pilot's two passes, the confirmatory operation-count prediction is exactly 2N candidate tests, N attribute-set attempts, and zero unattributed candidate tests, with per-clause candidate counts summing to the per-rule total. The audit counters are the evidence for these predictions; audit-off timings remain the primary latency measurement. If larger-size scheduler behavior violates these equations, preserve and report the failure rather than normalizing it away.
