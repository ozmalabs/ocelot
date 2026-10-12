# Prospective finite behavior-class return policy v1 results

Date: 2026-10-03

## Design and integrity

The source-locked capture contains 25 fresh panels: five seeded draws each from the additive, product, ordering, opposition, and inequality relations. All use the same per-panel candidate pool and 16 training labels across three paired policies. Independent replay passed source binding, panel reconstruction, query selection and label transitions, class partitions, class membership, and full 6,560-case returned-program scoring. The task relation is accessed through the simulated label oracle and the separately gated help callback; policy logic receives no task identifier or heldout labels.

The initial analysis implementation did not correctly normalize class ordering and model a terminal selector-abstention check; its diagnostic output was rejected. The v1.1 independent replay fixes those checks against the unchanged capture and passes. Each policy can evaluate an unlabeled pool of 64 rows. The zero-aware pool has fixed quotas of eight zero-containing, eight boundary, and sixteen general rows in each selection and challenge set. The nonzero control excludes zero. A class result is correct only if every returned member matches the target on the full finite fractional holdout grid.

## Outcomes

| Policy | Safe returned set | Contains an exact candidate | Help calls | Labels | Class partition cost |
|---|---:|---:|---:|---:|---:|
| Zero-aware query, then help | 19/25 | 25/25 | 6 | 56 | — |
| Zero-aware query and finite-class return | 24/25 | 25/25 | 1 | 18 | 81.0 ms total; 2.08 ms median/panel |
| Nonzero-only query and finite-class return | 20/25 | 25/25 | 0 | 15 | 76.4 ms total; 1.27 ms median/panel |

The nonzero control returned one finite class on all 25 panels, but all five inequality classes contained both a false Plus candidate and a correct Lt candidate. Zero-aware probes separated those candidates; the zero-aware class policy returned heldout-safe classes on 24 panels. Its remaining inequality panel had two distinct classes, requested the Not hint, and received a set with one exact candidate plus ten false candidates. Thus a help hint can recover an exact candidate without resolving which candidate is safe to return.

The query-help policy produced at least one exact candidate on all panels, but returned an all-exact set on only 19/25. Five opposition panels triggered Base help even though the zero-aware class policy safely returned four behaviorally equivalent, exact candidates. These five hint syntheses cost 6.02 seconds combined. The zero-aware class policy spent one Not hint on the unresolved inequality panel, taking 2.42 seconds; the returned set remained mixed. Class partitioning on the zero-aware policy evaluated 8,448 candidate-probe pairs. These costs are small beside candidate acquisition: four grammar searches across the 25 fresh panels consumed 209.3 seconds aggregate measured wall time. Synthesis dominates this bounded run.

## Interpretation and limits

Fresh panels replicate the core coverage result: a zero-aware finite class can safely replace syntactic-ambiguity help on opposition, while nonzero-only classes produce harmful returns on inequality. The result also exposes a remaining selection gap: the help callback often supplies a set containing both exact and false hypotheses. Class return lowers labels and avoids five unnecessary hints here, but is only safe relative to declared probes and the scored finite domain.

This is evidence from five authored relations, five panels each, one host, and finite query/holdout grids. The task-relevant hint is harness supplied; no primitive was discovered and no persistent rule was adopted. It is not a natural-task capability or universal equivalence result. Synthesis and class costs are measured wall times, not CPU-time or energy measurements.

## Reproduction artifacts

- [Preregistration](BEHAVIOR_CLASS_RETURN_PROSPECTIVE_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/behavior_class_return_prospective_v1.py) and [source lock](../../../evaluation/substrate_capability/behavior_class_return_prospective_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/behavior_class_return_prospective_v1_20261003.json)
- [Independent replay analyzer](../../../evaluation/substrate_capability/analyze_behavior_class_return_prospective_v1_1.py) and [analysis](../../../evaluation/reports/behavior_class_return_prospective_v1_1_analysis_20261003.json)
