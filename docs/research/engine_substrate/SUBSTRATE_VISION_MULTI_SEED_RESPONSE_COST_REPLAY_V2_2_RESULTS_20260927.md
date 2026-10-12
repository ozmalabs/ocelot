# Vision multi-seed response cost replay v2.2 results

## Result

All 75 timed trials pass the seven registered gates. Every condition matches the v2.1 record exactly on post-input graph digest, rate-write vectors, termination class, pass count, progress, and cycle indices; there are zero parity failures. Input delivery and the `rate=max(act-theta,0)` equation remain valid, all trials terminate by fixed point or exact repeated state, and all bounds hold.

The native `run_rules_report(1, False)` calls are fast on this small fixture. Across three seed workers, median accumulated closure-call wall time per stimulus is 60.4, 61.4, and 61.6 ms; summed over each seed's 25 trials, closure-call wall time is 1.50–1.56 s. Median process CPU time inside closure calls is within measurement noise of those values, so these samples show no large parallel CPU amplification at this size.

| Seed | Median closure-call wall / stimulus | Median full audit condition / stimulus | Total closure-call wall (25 trials) | Full audit wall (25 trials) | Peak RSS |
|---|---:|---:|---:|---:|---:|
| 20260935 | 60.4 ms | 16.9 s | 1.563 s | 444.9 s | 236.8 MiB |
| 20260936 | 61.4 ms | 17.5 s | 1.546 s | 445.9 s | 228.3 MiB |
| 20260937 | 61.6 ms | 17.4 s | 1.499 s | 426.5 s | 229.3 MiB |

The full audit loop is about 280 times the closure-call wall time in aggregate. It repeatedly materializes and hashes the entire graph to detect exact cycles, and also performs state extraction and fixture restoration. The replay did not separately time those components, so the excess cannot be assigned to graph hashing alone. It is a cost of this exact-cycle measurement harness, not a runtime estimate for ordinary substrate operation. The per-seed RSS is a process high-water mark for all 25 trials and likewise cannot be attributed to one condition or engine routine.

This evidence narrows one uncertainty from the tractability report: closure calls on the small 4×4-per-sheet vision fixture consume little measured CPU time, and process memory remains below 240 MiB in this harness. It does not show that native calls remain cheap as graph size, rule count, or separator width grows. A current-source size sweep with call-level CPU time, peak RSS, and exact semantic parity is still needed before making a commodity-hardware scaling claim.

## Reproduction artifacts

- Protocol: [v2.2 preregistration](SUBSTRATE_VISION_MULTI_SEED_RESPONSE_COST_REPLAY_V2_2_PREREG_20260927.md)
- Runner and analyzer: [timed replay](../../../scripts/substrate_vision_multiseed_response_cost_replay_v2_2.py), [independent analysis](../../../scripts/analyze_substrate_vision_multiseed_response_cost_replay_v2_2.py)
- Raw data: [aggregate](../../../evaluation/reports/vision_multiseed_response_cost_replay_v2_2_20260927.json) and isolated per-seed worker reports under `evaluation/reports/vision_multiseed_response_cost_replay_v2_2_20260927_seed_*.json`
- Analysis and source lock: [analysis](../../../evaluation/reports/vision_multiseed_response_cost_replay_v2_2_analysis_20260927.json), [lock](../../../evaluation/substrate_capability/vision_multiseed_response_cost_replay_v2_2_lock_20260927.json)
- Matched response baseline: [v2.1 results](SUBSTRATE_VISION_MULTI_SEED_RESPONSE_REPLICATION_V2_1_RESULTS_20260927.md)
