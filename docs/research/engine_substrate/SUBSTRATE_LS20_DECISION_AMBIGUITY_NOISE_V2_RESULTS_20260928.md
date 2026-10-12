# LS20 decision ambiguity/noise multi-seed v2 results

**Status:** complete; final corrected independent analysis passes all eight integrity gates. **Scope:** 640 paired synthetic worlds across eight station/noise strata and four seed blocks, with 1,280 episode executions. Quanta routing and planner rules are held fixed.

## Recognition and task outcomes

Every clean comparator recognized the required transform and completed all 80 tasks in every stratum. The noisy recognition key was either exact or refused: **there were no incorrect non-null transform keys among 640 noisy episodes.** Task success exactly tracked exact recognition in this panel; each refusal produced `no_waypoint`.

| Stations | Sigma | Noisy exact / refusal / wrong key | Clean success | Noisy success (95% Wilson CI) | Noisy breaks / fixes | Holm-adjusted paired p |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 8 | 80 / 0 / 0 | 80/80 | 80/80 (0.954–1.000) | 0 / 0 | 1.000 |
| 1 | 10 | 76 / 4 / 0 | 80/80 | 76/80 (0.878–0.980) | 4 / 0 | 0.375 |
| 1 | 12 | 64 / 16 / 0 | 80/80 | 64/80 (0.700–0.873) | 16 / 0 | 0.000153 |
| 1 | 14 | 1 / 79 / 0 | 80/80 | 1/80 (0.002–0.067) | 79 / 0 | 2.65e-23 |
| 6 | 8 | 80 / 0 / 0 | 80/80 | 80/80 (0.954–1.000) | 0 / 0 | 1.000 |
| 6 | 10 | 71 / 9 / 0 | 80/80 | 71/80 (0.800–0.940) | 9 / 0 | 0.0156 |
| 6 | 12 | 59 / 21 / 0 | 80/80 | 59/80 (0.632–0.821) | 21 / 0 | 5.72e-6 |
| 6 | 14 | 5 / 75 / 0 | 80/80 | 5/80 (0.027–0.138) | 75 / 0 | 3.71e-22 |

Sigma 8 survives this panel with all five distractor operators present. At sigma 10 and 12, six stations yield somewhat more refusals than one station (9 vs 4, and 21 vs 16); this is descriptive, not a tested station-count effect. At sigma 14 almost all cases are refused at either station count. The confidence intervals and paired tests quantify the noisy-versus-clean difference within each stratum; they do not test between-stratum station effects. The v1 screening signal is replicated: degradation leads to conservative abstention rather than wrong transform execution, for these shapes, transforms, renderer, and noise process.

Every 20-world seed block contains all six required operators—three rotations, two reflections, and recolouring—three or four times. Each stratum's four block success counts are preserved in the analysis artifact; sigma-8 is 20/20 in every block. The task-oracle analyzer independently checked exact transform construction, one matching station, route reachability, terminal consistency, and each stored scenario digest.

## Integrity and analysis corrections

The run completed all 640 unique worlds. The final verification confirms stable pre/post/live worker locks, a fresh native extension, all world and route oracles, 32/32 balanced operator blocks, and 80 worlds in each of eight strata. Worker wall time was 1,451.9 s, aggregate process CPU 2,481.3 s, and peak RSS 133,456 KiB.

The initial independent analyzer incorrectly collapsed parameterized transform operators into three broad families; its retained output therefore reports false-negative integrity gates. The first correction counted the six distinct operators but mistakenly expected 16 blocks instead of 32; that output is also retained. The final, separately locked v2.2 correction checks the preregistered 8 conditions × 4 blocks = 32 blocks. It changes no raw data, worker inputs, seeds, scoring, or outcomes. The amendment chain documents both analysis-only corrections; only the final v2.2 report supports the pass claim.

## Interpretation and next work

This gives an empirical noise envelope and a favorable fail-closed profile for one synthetic recognition/planning family. It does not establish a general confidence calibration, performance on unseen shape families, natural visual noise, or broad tractability. The engine currently exposes recognition as an exact key or refusal in this path; a confidence-margin recovery policy was not evaluated. Next inspect whether candidate scores/margins are available without changing the decision rule, then preregister a held-out shape-family transfer panel with an explicit wrong-key cost and compare abstention against any calibrated fallback. Separately continue long-horizon planning and frame-boundary scaling gates.

Artifacts: [preregistration](SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V2_PREREG_20260928.md), [analysis amendments](SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V2_AMENDMENT_20260928.md), [count correction](SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V2_2_AMENDMENT_20260928.md), [runner](../../../evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2.py), [worker lock](../../../evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_lock_20260928.json), [raw capture](../../../evaluation/reports/ls20_decision_ambiguity_noise_v2/capture.json), [initial analysis](../../../evaluation/reports/ls20_decision_ambiguity_noise_v2_independent_analysis.json), [v2.1 analysis](../../../evaluation/reports/ls20_decision_ambiguity_noise_v2_1_analysis.json), [final analysis](../../../evaluation/reports/ls20_decision_ambiguity_noise_v2_2_analysis.json), [final analysis lock](../../../evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_2_analysis_lock_20260928.json), [corrected analyzer](../../../evaluation/substrate_capability/analyze_ls20_decision_ambiguity_noise_v2_2.py).
