# LS20 map-navigation current-source scale panel v1.2 results

**Status:** complete; all preregistered integrity, world-oracle, open-parity, and walled-cell gates pass.  
**Scope:** current-source task quality and warm per-episode cost on the synthetic offline ls20-shaped planner/navigation task. This is not natural-world planning prevalence or a general planning claim.

## Task outcomes

Thirty paired scenarios were run in each cell; each pair used the identical generated world and the curiosity planner with the greedy or quanta executor. The independent analyzer reconstructed the intended transformation from the scenario's generator fields, verified the goal shape, confirmed one corresponding station, and independently checked reachability of the goal and every station.

| Map and stations | Greedy success | Quanta success | Quanta fixed / broken | Exact paired p |
|---|---:|---:|---:|---:|
| 16×16, one station, 20% walls | 1/30 | 30/30 | 29 / 0 | 3.73e-9 |
| 16×16, three stations, 20% walls | 1/30 | 30/30 | 29 / 0 | 3.73e-9 |
| 32×32, one station, 20% walls | 0/30 | 30/30 | 30 / 0 | 1.86e-9 |
| 32×32, three stations, 20% walls | 1/30 | 30/30 | 29 / 0 | 3.73e-9 |

The open 16×16 control also passes: both routers win all 30 scenarios and match both win/loss and step count exactly. The planner's recognized transform key matched the independent expected key in all 150 scenarios. All four walled cells exceed the preregistered quanta success floor and have non-overlapping Wilson intervals against greedy. These results confirm a strong contribution from the quanta router on these generated blocked-map tasks; they do not isolate the planner's decision quality because both route arms share the curiosity decisions.

## Cost and scale observations

Per-episode wall time includes scenario execution through the planner and route machinery, with model recognition memoized within the process. Quanta median wall time is 1.12–1.23 s on 16×16 walled maps and 3.49–3.65 s on 32×32 maps. The descriptive 32×32/16×16 median ratios are 2.85× (one station) and 3.26× (three stations) for a fourfold increase in grid area. Median route steps increase from 27.5–32 at 16×16 to 66–67 at 32×32. Across the complete worker, wall time is 961.3 s, process CPU time 1,383.4 s, and peak RSS 120,944 KiB. Process CPU may exceed wall time because it aggregates worker-thread CPU. These are one-host descriptive measurements, not a fitted complexity law or a comparison of cold startup costs.

## Integrity and analysis notes

The final source/input lock is identical pre-run, post-run, and on independent live recomputation. It covers the 40 Python files loaded by the representative path, all Rust sources and Cargo manifests, native facade and fresh extension/build identity, the 24 recursively loaded seed manifests, and exact task/configuration inputs. The native extension reports no stale source reasons. A complete scenario record is captured for each episode; canonical scenario SHA-256 digests are derived by the independent analyzer rather than persisted by the runner, so this is disclosed as a capture-format deviation from the original preregistered artifact list.

The first independent analyzer pass exposed an analyzer-only recolour-key formatting bug (missing the `v` prefix on the target colour). The raw task capture did not change. The analyzer was corrected against the source-defined key format, rerun, and all independent gates then passed. The first v1 and v1.1 attempts remain preserved as censored: v1 and the second v1.1 run completed their scenarios but failed source-stability gates; the first v1.1 lock attempt stopped before evaluation. None of their outcome labels were used to tune this panel.

## Claim boundary and next test

This establishes current-source capability on one generated planning/navigation family at 16×16 and 32×32, 20% wall density, and one/three transform stations. It does not measure general planning search, natural task frequency, unknown-map exploration, arbitrary wall topology, or learned transfer. A next planning gate should separate decision quality from navigation by holding route execution fixed while varying transform ambiguity, distractor count, and recognition noise; any larger scaling claim should then vary map area and wall density with fresh, preregistered samples and report tail latency as well as medians.

Artifacts: [v1.2 preregistration](SUBSTRATE_LS20_MAPNAV_CURRENT_SOURCE_SCALE_V1_2_PREREG_20260928.md), [amendment history](SUBSTRATE_LS20_MAPNAV_CURRENT_SOURCE_SCALE_V1_2_AMENDMENT_20260928.md), [runner](../../../evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_ls20_mapnav_current_source_scale_v1_2.py), [source lock](../../../evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2_lock_20260928.json), [raw capture](../../../evaluation/reports/ls20_mapnav_current_source_scale_v1_2/capture.json), [independent analysis](../../../evaluation/reports/ls20_mapnav_current_source_scale_v1_2_independent_analysis.json). Censored runs: [v1 lock and partial](../../../evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_lock_20260928.json), [v1.1 censored partial](../../../evaluation/reports/ls20_mapnav_current_source_scale_v1_1_censored_source_drift/partial.json).
