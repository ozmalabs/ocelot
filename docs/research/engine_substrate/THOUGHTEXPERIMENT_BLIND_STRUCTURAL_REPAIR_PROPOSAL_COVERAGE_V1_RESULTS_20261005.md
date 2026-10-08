# Blind structural repair proposal coverage v1 results

The source-locked proposal-coverage subgate passes its integrity and
repeatability checks across three fresh workers. Candidate IDs, candidate
counts, and target-in-pool decisions agree across workers for all five cases;
all pools are untruncated and proposal accounting reconciles.

| Sealed fault form | Candidates | Target rule proposed |
|---|---:|:---:|
| Comparison flip | 9 | Yes |
| Numeric constant shift | 9 | No |
| Match edge dropped | 0 | No |
| Guard added | 5 | No |
| Effect value substituted | 2 | No |

Aggregate proposal coverage is 1/5 (20%) on this deliberately small panel.
There are 25 candidates across the five cases; median pool size is 5 and
median enumeration time is 0.677 ms. The zero-candidate row is the dropped
edge case: after deletion, the rule has no applicable comparison flip or
second match edge to drop, and its effects/conditions expose no attributes
from which this enumerator can form a guard. The remaining misses align with
the current operator gaps: no constant editing, match-edge insertion, guard
deletion, or effect replacement.

This is a proposal-language coverage measurement, not a repair success rate.
The fixture contains authored structural pairs; the enumerator receives only
the faulted rule, while the target is consulted afterward by the evaluation
layer. No task examples, oracle labels, branch rehearsals, graph-native
selection, held-out task outcomes, canaries, or commits are involved. The
20% figure must not be generalized beyond this fixture. It identifies the
next engineering need: expand candidate generation to express inverses for
the missing edit families, then evaluate candidate ranking and behavioral
utility separately.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v1.py)
- [Fixture](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_lock_20261005.json)
- [Raw capture](../../../evaluation/reports/blind_structural_repair_proposal_coverage_v1_20261005.json)
- [Analysis](../../../evaluation/reports/blind_structural_repair_proposal_coverage_v1_analysis_20261005.json)

Source-lock SHA-256: `6afebd5392fa584fd3177884ce5afecb9d91f682f68343df3047e480b429b06c`.
