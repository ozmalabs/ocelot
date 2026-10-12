# Describe-rule full-seed candidate scaling v1

Date: 2026-09-27

## Question

Does the linear candidate-work result for the three source-derived Scene recognition rules survive when they run against the loaded full-seed graph, and how does work change with Scene count and vocabulary membership?

## Method

Eight fresh workers were assigned to a preregistered 2×2 factorial: 1 or 4 Scenes and 0 or 4,096 added distractor Concepts, with two workers per cell. Each worker cold-booted the full seed, built the real `arc_self_report.py::build_describe_faculty`, then tombstoned all active rules except the three measured recognition rules. Every synthetic Scene had three Percepts. Distractor Concepts were attached to a dedicated noise Microtheory. Candidate/Term work was counted during closure, and output labels and fixed-point status were checked. The full-seed graph remained loaded, but only the target rules were active during timed closure.

## Result

All eight workers passed the independent gates: unique processes, matching source locks, 731 loaded seeds and 11 reported load failures per boot, one target Concept per label, exactly three active rules, fixed point, exact expected classifications, and no distractor classifications. The background graph was constant at 10,792 Concept nodes, 509 Microtheories, and 6,320 `has_concept` memberships before synthetic additions.

| Scenes | Added Concepts | Memberships M | Candidate pairs, all 3 rules | Term evaluations, all 3 rules | Audited closure wall median |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 6,320 | 18,969 | 75,901 | 8.72 ms |
| 1 | 4,096 | 10,416 | 31,257 | 125,053 | 14.33 ms |
| 4 | 0 | 6,320 | 75,876 | 303,604 | 33.37 ms |
| 4 | 4,096 | 10,416 | 125,028 | 500,212 | 57.95 ms |

For every rule and cell, observed candidate pairs satisfy `S × (M + 3)`, where S is the Scene count and each Scene has three Percepts. Term evaluations are also proportional to Scene count and membership size, with small rule-specific offsets. These are exact descriptive identities for these fixtures, not a general complexity theorem. The scene multiplier and membership growth therefore reproduce the earlier isolated linear-work pattern in a full-seed graph.

## Interpretation and limits

This is source-grounded evidence that these three matcher motifs have linear measured candidate work over the tested membership and Scene ranges. It does not establish that the live route or full active-rule closure is linear: 2,334 other active rules were tombstoned for the timed closure, and the added scenes and memberships are synthetic. It also does not measure learned frames, separator width, complete inference cost, ordinary uninstrumented latency, or natural task distributions. Faculty construction and full boot dominate the total worker setup and are not part of the audited closure timings.

The next measurement should activate the full rule set on a controlled live route, preserve exact request and whole-graph parity, and attribute repeated work to rules and candidate domains. Compare that total with the isolated three-rule lower bound before making claims about operational cost or frame locality.

## Artifacts

- [Preregistration](SUBSTRATE_DESCRIBE_RULE_FULL_SEED_CANDIDATE_SCALE_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_describe_rule_full_seed_candidate_scale_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_describe_rule_full_seed_candidate_scale_v1.py)
- [Analysis](../../../evaluation/reports/describe_rule_full_seed_candidate_scale_v1_analysis_20260927.json)
- [Raw report](../../../evaluation/reports/describe_rule_full_seed_candidate_scale_v1_20260927.json)
- [Source lock](../../../evaluation/substrate_capability/describe_rule_full_seed_candidate_scale_v1_lock_20260927.json)
