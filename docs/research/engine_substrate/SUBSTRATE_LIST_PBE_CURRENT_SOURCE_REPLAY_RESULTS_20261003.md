# List PBE current-source replay results

Date: 2026-10-03

## Result

The source-current replay completed all 30 frozen list tasks under each of three arms. Its independent accepted-IR holdout audit passed, and the task-level comparison to the 2026-09-25 amended capture found zero outcome, status, or construction mismatches in any arm. Main, frozen codebook/bigram ablation, and fresh-substrate main replay each produced 14/30 exact held-out passes, two accepted false programs, and 14 gaps. Thus the previously observed outcome pattern is stable on the current source/build for this suite; the ablation still shows no measurable change on these tasks.

The 90-run capture took 52.8 seconds wall time. Current main-arm route time totaled 15.7 seconds (median 498 ms, p90 1.11 s); the current-source analyzer re-evaluated 48 accepted IRs across arms and found six arm-level held-out failures (the same two task failures repeated in each arm). The old result's task-family limitations remain: integer-list PBE, one generated fixture, and no estimate of natural-task prevalence or broad capability. This is a source-drift replication, not a new confirmatory task sample.

## Artifacts

- [Protocol](SUBSTRATE_LIST_PBE_CURRENT_SOURCE_REPLAY_PREREG_20261003.md)
- [Wrapper](../../../scripts/substrate_list_pbe_current_source_replay.py)
- [Pre-run lock](../../../evaluation/substrate_capability/list_pbe_current_source_replay_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_list_pbe_composition_current_source_20261003.json)
- [Independent accepted-IR analysis](../../../evaluation/reports/substrate_list_pbe_composition_current_source_analysis_20261003.json)
- [Prior amended pilot results](SUBSTRATE_LIST_PBE_COMPOSITION_BENCHMARK_RESULTS.md)
