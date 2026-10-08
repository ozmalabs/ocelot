# LS20 map-navigation current-source scale panel v1.2 preregistration

**Date:** 2026-09-28  
**Question:** Does the graph-native ls20 curiosity planner retain task success when its navigation executor is tested on held-out, walled layouts at two map sizes, and how does quanta routing compare with the greedy executor on the same layouts?

## Scope and claim boundary

This is a source-current replication and scale extension of the offline rung-220000 map-navigation pilot. It tests the integrated `worlds.arc_ls20_scenario.run_episode` path with the existing curiosity planner and either `greedy` or `quanta` execution. It measures synthetic ls20-shaped transformations and maps, not live ls20, natural planning prevalence, general action selection, or an LLM comparison. The policy decision rules and router implementations remain unchanged.

## Fixed panel

Use 30 generated scenarios in each walled cell: 16×16 and 32×32 maps, each with one and three transformation stations, at wall density 0.20. For each generated scenario, run both routers against the identical world. Use NumPy PCG64 seeds `222200`, `222201`, `222202`, and `222203` for the four cells in the order just listed. Counterbalance arm execution order by scenario index (quanta first for even indices; greedy first for odd indices). Also run 30 paired open 16×16, one-station scenarios with seed `222204`; the open control requires exact win and step-count parity.

For each scenario, preserve the full generated world description, a canonical scenario digest, both outcomes (`win`, `reason`, steps, recognized key), per-arm wall and CPU time, and independent graph-grid shortest-path distances from the start to every station and the goal. A separate standard-library oracle must recompute the intended shape transform from the generator's declared family/parameter, check that it equals the goal shape, and confirm exactly one station has the required transform key. Check that a `win` label agrees with a delivered terminal outcome.

## Gates

1. All 150 scenarios pass the independent intended-transform/station oracle.
2. Both routers have exactly the same success and step count in all 30 open controls.
3. In each of the four walled cells, quanta succeeds on at least 27/30 tasks.
4. In each walled cell, quanta's Wilson 95% lower confidence bound exceeds greedy's upper bound. If this fails in any cell, report the result and do not pool cells to claim separation.
5. The pre-run, post-run, and live source/build/input locks are identical; the native extension is fresh for the locked Rust source.

These thresholds test a named offline task family only. Timing is descriptive: report per-arm wall/CPU medians and ranges and process peak RSS, without a speedup claim from one process or one host. Preserve all cases and failures; no scenario exclusion, map resizing, or algorithm tuning after outcome inspection.

## Inputs, resume, and analysis

Lock the benchmark/preregistration/runner; the Python import/runtime file closure loaded by one separate representative paired episode (40 files, enumerated in the lock); the Rust source and Cargo manifests; Python native facade; extension/build manifest; every seed manifest in the recursively resolved `boot_core` + shape-decoder + navigation dependency closure; and the directly loaded `arc3_env.py` module. Hash the measurement script directly. This file-level Python scope follows two pre-run/post-run drift detections in the broader source trees: unrelated `scripts/jabberwock_daemon.py` and `domains/construction_grammar.py` edits. Non-loaded Python files are outside this simulation path. Rust, facade, build artifact, and all loaded seed manifests remain fully hashed. Record Git HEAD, runtime/toolchain/hardware, and exact cell parameters. Use a new capture directory and checkpoint after each paired scenario. Resume only under exact lock equality. Independent analysis must read the raw paired rows, re-evaluate the transform/station/route oracle and all gates, and report each cell separately. No benchmark reporting helper may be used by the analyzer.
