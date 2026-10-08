# Blind structural repair proposal coverage v2 results

The v2 source-locked capture and independent analyzer pass across three fresh
workers. Candidate IDs, counts, and target-in-pool decisions agree; candidate
pools are untruncated and accounting reconciles.

| Fault form | V1 candidates / hit | V2 candidates / hit |
|---|---:|---:|
| Comparison flip | 9 / yes | 13 / yes |
| Numeric constant shift | 9 / no | 13 / yes |
| Match edge dropped | 0 / no | 1 / no |
| Guard added | 5 / no | 10 / yes |
| Boolean effect substituted | 2 / no | 3 / yes |

Exact target proposal coverage rises from 1/5 (20%) to 4/5 (80%), a 60
percentage-point paired increase. Total candidates rise from 25 to 40; median
pool size rises from 5 to 10. Median syntax-enumeration time rises from
0.677 ms to 1.040 ms. These times cover only the tiny rule enumerator and are
not representative throughput estimates. The dropped-match-edge case remains
uncovered because a syntax-only candidate generator cannot reconstruct an
absent relation without a candidate relation vocabulary or observed graph
evidence.

The three new operations are numeric literal shifts by exactly ±1, removal of
one child from an existing `where` conjunction, and inversion of an individual
boolean literal in effects. They recovered the three expected cases on this
panel. Since v1 misses informed these operator additions and the same five
authored pairs were reused, this is a transparent engineering iteration, not
independent confirmation, held-out generalization, or a broad proposal-recall
estimate. No task behavior, graph-native selection, branch rehearsal, canary,
or commit was measured.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_PROPOSAL_COVERAGE_V2_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v2.py)
- [Reused v1 fixture](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2_lock_20261005.json)
- [Raw capture](../../../evaluation/reports/blind_structural_repair_proposal_coverage_v2_20261005.json)
- [Analysis](../../../evaluation/reports/blind_structural_repair_proposal_coverage_v2_analysis_20261005.json)
