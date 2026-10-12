# MBPP Arc 3 current-source recheck results (2026-09-25)

**Run state:** current-source replication of a previously registered, previously measured benchmark. Protocol and scope note: [`SUBSTRATE_MBPP_ARC3_CURRENT_RECHECK_NOTE_20260925.md`](SUBSTRATE_MBPP_ARC3_CURRENT_RECHECK_NOTE_20260925.md). **Pre-run lock:** [`mbpp_arc3_current_recheck_lock_20260925.json`](../../../evaluation/substrate_capability/mbpp_arc3_current_recheck_lock_20260925.json). **Raw current report:** [`substrate_mbpp_arc3_current_recheck_20260925.json`](../../../evaluation/reports/substrate_mbpp_arc3_current_recheck_20260925.json). **Version-drift analysis:** [`substrate_mbpp_arc3_recheck_analysis_20260925.json`](../../../evaluation/reports/substrate_mbpp_arc3_recheck_analysis_20260925.json).

## Current registered-split result

The unchanged Arc 3 runner processed the full 257-task MBPP sanitized test split. Its splitter reported 7 few-shot, 257 test, 43 validation, and 120 train tasks (427 total); all 257 test tasks were runnable under the registered primary protocol. No test task's reference `code` is passed into the solver; the runner imports the registered split/parse path and uses assertion rows for revealed and held-out evaluation.

| Arm | Exact passes | Accepted, including holdout failures | Gaps / other failures | Determinism |
|---|---:|---:|---:|---|
| Full R3 | 88/257 (34.2%; Wilson 95% CI 28.7–40.2%) | 147, including 59 holdout failures | 107 gaps, 1 unrecognized, 2 runner exceptions | Identical outcome hash |
| No retrieval | 85/257 (33.1%; 27.6–39.0%) | 150, including 65 holdout failures | 104 gaps, 1 unrecognized, 2 runner exceptions | Identical outcome hash |
| Official R3 | 114/257 (44.4%; 38.4–50.5%) | 119, including 5 holdout failures | 135 gaps, 1 unrecognized, 2 runner exceptions | Identical outcome hash |

Official R3 reveals all parseable assertions and scores against those same rows. Its 114/257 is a protocol-distinct comparability result; it is not an improvement over the held-out primary arms.

Task-ID alignment gives 83 tasks passing in both primary arms, 167 failing in both, five full-R3-only passes, and two no-retrieval-only passes: net +3 tasks (+1.17 percentage points). The exact two-sided McNemar test on the seven discordant pairs gives p=0.453. The earlier reported −6.97 to +9.28 percentage-point Newcombe interval is formed from marginal arm intervals and is not a paired confidence interval. The corrected paired analysis is reproducible from the saved task rows ([analysis report](../../../evaluation/reports/substrate_paired_battery_rechecks_analysis_20260930.json), [analyzer](../../../scripts/analyze_substrate_paired_battery_rechecks.py)). On this fixed recheck there is **no established retrieval gain**; task-level exchangeability is not enough to claim generalization across task families. The full arm still has 59 accepted programs that fail held-out assertions. Full-arm gaps include 66 enumeration failures, 17 structural rejections, 16 property rejections, 5 exhausted cases, and 3 no-shape cases; the two runner exceptions are ValueError on task 124 and TypeError on task 237. These remain in the denominator.

## Source-generation drift

The current full-R3 result is 88/257 versus 21/257 in the historical Arc 3 artifact measured 2026-08-01; no-retrieval is 85 versus 19; official is 114 versus 47. Pass identities changed materially: current full has 70 gains and 3 losses relative to the historical artifact; no-retrieval has 71 gains and 5 losses; official has 86 gains and 19 losses. The current synthesis seed is v1.14.0, while the historical report describes the v1.5.1 stack. This is evidence of a changed system generation, not a causal estimate of any one source change. Both current primary arms and official arm reproduce identical outcomes across their two runs.

## Cost and reproducibility

The three-arm run took 236.67 s wall (full R3 two passes 71.46 s; no retrieval 52.11 s; official 112.99 s), with process peak RSS 345,456 KiB. Python is 3.13.5 on Linux x86-64. The native extension SHA-256 is `ca49e588a9787dad9b957f3e18718d0f0cd72cde85091d2b9edca350965cd4d9`. The pre-run lock freezes the fixture, runner, parser, synthesis adapter/seed, training diet/chunk inputs, historical comparator artifacts, native build, and benchmark protocol. The raw report records per-task results, twin-run hashes, environment, and current source hashes.

This adds broad externally sourced Python-program task evidence to the capability inventory, but it is a replication on a familiar benchmark and a substantially updated source/seed generation. It does not establish fresh-domain transfer, general learning, minting economics, or natural task prevalence. The retrieval ablation only isolates exemplar retrieval in the registered boot; it does not isolate every learned or structural component.
