# Live self-report membership scaling v1

Date: 2026-09-27

## Result

The second full-request topology, `report your organisation`, was run at 0, 1,024, and 4,096 added noise Concepts. Each Concept contributes one `has_concept` edge to a dedicated Microtheory. The full seed and rule set remained active. Two independent fresh-process repetitions per size were run with ordinary execution and with native counters/access tracing enabled (12 workers total).

All 14 independent analysis gates pass. Source fingerprints were stable; all workers used distinct PIDs; every run selected `self_report`, returned the same nonempty organisation-related reply, and resolved exactly one Goal through selection, execution, and action result. The Goal was closed and inactive. Audited/untraced pairs had exact reply, lifecycle, graph digest, and graph-size parity. No synthetic Concept received an `is_a` classification. Candidate and Term counters reconcile; trace rows have zero drops; repeated work profiles and graph output match within each cell.

The exact reply in all workers was: `I am organised into computer_architecture, communication, mathematics, engineering, video_coding_theory, databases_and_storage, art_design_drawing, embedded_iot_realtime, security_and_cryptography, cloud_infrastructure, machine_learning, and philosophy`.

## Measured work

| Added noise Concepts | Total `has_concept` memberships | Candidate tests | Term evaluations | Selected access events | Untraced wall median | Audited wall median | Untraced peak RSS median |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 6,320 | 66,095 | 716,057 | 333,203 | 351 ms | 448 ms | 1.672 GiB |
| 1,024 | 7,344 | 74,287 | 806,169 | 355,731 | 373 ms | 451 ms | 1.672 GiB |
| 4,096 | 10,416 | 98,863 | 1,076,505 | 423,315 | 353 ms | 512 ms | 1.672 GiB |

Across the tested sizes, each added membership contributes exactly 8 candidate tests, 88 Term evaluations, and 22 selected access events. The measured increase is entirely localized to `curiosity_targets_ambivalent_nodes`; this does not imply that other rules never scale with other input axes. The base graph has 10,790 Concepts and 6,320 memberships. Final graph size rises by exactly one node and one edge per added Concept.

Two replicates per arm and cell do not establish a timing law. The untraced medians are nonmonotone; audit overhead is visible in these small request timings. Peak RSS is a process high-water mark dominated by the full seeded substrate and does not resolve the memory increment of each Concept at this scale.

## Interpretation

This is a successful independent-topology replication of the full-request measurement method, plus a second task-specific response to the same synthetic membership axis. The self-report request has far less candidate and Term work than the earlier scene-description request. More importantly, its added vocabulary affects one curiosity rule rather than the four rules that grew in describe-scene. Thus a single task's per-membership slope is not a substrate-wide constant; active rules and topology determine the measured work.

The experiment does not measure whether frames are learned from cheap cuts, whether natural workloads have the same membership distribution, or whether inference factorises across a runtime hierarchy. It tests no new structure induction (rungs 3–4), no large graph beyond 29,085 nodes, and no semantic truth of the self-description. Do not generalize these finite differences to asymptotic complexity or commodity-hardware capability.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_SELF_REPORT_LIVE_SCALE_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_live_self_report_live_scale_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_live_self_report_live_scale_v1.py)
- [Source lock](../../../evaluation/substrate_capability/live_self_report_live_scale_v1_lock_20260927.json)
- [Driver report](../../../evaluation/reports/live_self_report_live_scale_v1_20260927.json)
- [Analysis](../../../evaluation/reports/live_self_report_live_scale_v1_analysis_20260927.json)
- [Raw workers](../../../evaluation/reports/live_self_report_live_scale_v1_workers_raw_20260927.json)
