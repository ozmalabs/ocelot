# Current-source P6 synthesis recheck (2026-09-25)

## Scope and run state

This is a current-source recheck of the repository's fixed 125-task natural-language program-synthesis battery, a broader path than direct PBE: requests pass through recognition, graph-authored codebook/lattice/descent rules, enumeration fallback, and ProgEval with held-out rows. The set has six strata and 3–5 revealed plus 2–3 held-out examples per task. Its prior outcomes are known, so this is a replication/recheck, not a new confirmatory split. The original [`results/prog_synthesis_battery.json`](../../../results/prog_synthesis_battery.json) was read for paired historical analysis and left unchanged.

The current run used two full main-arm passes to check deterministic outcomes and one frozen learned-layer ablation pass. It also ran the frozen 26-item continuity control and the existing deterministic cross-renderer/toolchain subsample. The primary output is the [raw current-run report](../../../evaluation/reports/substrate_p6_current_recheck_20260925.json); the task-transition analysis is in a separate [derived report](../../../evaluation/reports/substrate_p6_recheck_analysis_20260925.json). Reproduction commands and hashes are recorded there; the runner and analyzer are [`substrate_p6_current_recheck.py`](../../../scripts/substrate_p6_current_recheck.py) and [`analyze_substrate_p6_current_recheck.py`](../../../scripts/analyze_substrate_p6_current_recheck.py).

## Current paired result

| Arm | Held-out passes | Accepted, including held-out failures | Gaps | Not recognized |
|---|---:|---:|---:|---:|
| Current main | 83/125 (66.4%; Wilson 95% CI 57.7–74.1%) | 108 | 14 | 3 |
| Frozen layer | 82/125 (65.6%; Wilson 95% CI 56.9–73.4%) | 107 | 15 | 3 |

Task-ID alignment gives 82 tasks passing in both arms, 42 failing in both, one main-only pass (`la_17_fact_of`), and no frozen-only pass. The fixed-set paired difference is **one task** (+0.8 percentage points); the exact two-sided McNemar test on the single discordant pair gives p=1.0. The earlier reported −10.8 to +12.4 percentage-point Newcombe interval is formed from marginal arm intervals and is not a paired confidence interval. The corrected paired analysis is reproducible from the saved task rows ([analysis report](../../../evaluation/reports/substrate_paired_battery_rechecks_analysis_20260930.json), [analyzer](../../../scripts/analyze_substrate_paired_battery_rechecks.py)). This recheck shows no measured capability gain from the added learned layer; neither the discordance test nor this fixed known suite establishes a natural-task population effect.

Among current main-arm held-out passes, the last successful rung is enumeration for 60, codebook for 11, descent for 5, lattice for 4, and exact for 3. Twenty-five additional accepted programs fail held-out evaluation. Thus answer generation is active across the ladder, while the independent held-out verdict rejects a material number of example-fitting programs. This is bounded task-family capability, not general learning evidence.

Main twin-run outcomes are identical (SHA-256 `5c3fb707837ffbb1df64d698e415ee6f02df41af34d7a618164afb4df43ccea9`). The frozen arm is a paired ablation on the same tasks, but was run once. The live continuity control remains 7/26 with zero frozen-success regressions or improvements.

## Cross-version drift and resource envelope

Compared with the historical July `main_postfix` artifact, current main changes strict pass identity on 28 tasks: 17 previously non-passing tasks become held-out passes and 11 previous passes are lost. Main rises from 77/125 to 83/125. Frozen changes 41 pass identities: 31 gains and 10 losses, rising from 61/125 to 82/125. The historical postfix artifact names seed `program_synthesis.json` v1.1.0; the current run records v1.14.0. These counts show substantial version drift and cannot be attributed to the engine, learned layer, or any single source change. They make the source and seed versions essential parts of any capability claim.

End-to-end wall time was 48.7 s. The two main passes took 10.7 s and 10.5 s; the frozen arm and auxiliary checks account for the remainder. Parent peak RSS was 1,774,824 KiB; subprocess maximum RSS was also reported as 1,774,824 KiB, with child CPU/RSS including toolchain checks and not decomposable per arm. Python rendering succeeded for 57/108 accepted outputs; 50/57 rendered outputs agreed on execution. On the deterministic 15-task subsample, Rust agreed on 8, had 6 render gaps and one compile error; Lua was unavailable; LLVM-to-x86 agreed on 7, refused 4, and marked 4 out of scope. ProgEval pass rates therefore do not equal cross-language deployable output rates.

## E2 interpretation and next gate

This P6 battery supplies broad fixed-suite, held-out task evidence for the full synthesis path. Alongside the prompt-free string PBE recheck, it shows a functioning bounded enumerative/symbolic synthesis capability and no measured advantage from the current learned-layer ablation. It does not measure residual-triggered minting economics, generalization to a newly frozen family, task-distribution prevalence, retention, or cross-domain transfer. The next confirmatory E2 study must freeze a genuinely new task family and splits before outcomes, include recurring and one-off novelty plus adversarial/null controls, and record rung transitions, candidate/search costs, false acceptance/mint, and reuse. This recheck is not that study.
