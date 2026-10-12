# LS20 decision under station ambiguity and recognition noise v1

**Question.** With navigation held to the quanta router, how do distractor station count and visual recognition noise affect the existing graph-native LS20 planner's task success?

## Scope

This is an offline synthetic task evaluation. Each paired comparison reuses one generated map and changes only the visual recognizer: a clean image path versus Gaussian pixel noise at sigma 8 or 12 before the existing grid-recovery function. The graph-native planning rules, quanta route executor, world physics, action budget, and generated world are fixed within each pair. No planner or router parameters are tuned. The result measures integrated response to recognition errors in the presence of distractor stations; it does not estimate natural task frequency or general planning ability.

## Design

Use 20 scenarios per cell on 16x16 maps with 20% walls. Cross station count {1, 6} with recognition sigma {0, 8, 12}, for six cells and 120 paired worlds. Exactly one station is correct; remaining stations are distractors under the existing scenario generator. Seeds are fixed as 928001 through 928006 in cell order (station count outer, sigma inner). For each world, run the clean arm and the noisy arm using `router="quanta"`, 200-step budget, and fixed arm order alternating by episode index. Sigma 0 is the clean-vs-clean repeatability control: use the same deterministic recognizer in both arms.

For noisy episodes, a local PCG64 generator seeded from the cell seed and episode index adds independent Gaussian noise to the rendered symbol and goal images, clips to uint8, and passes them through the production `recover_grid_from_render` and graph-native transform recognizer. Preserve both the recognition key and the full episode outcome. World scoring remains exact and noiseless, as in the existing adapter.

## Measures and gates

Record paired success, route steps, terminal reason, recognized key, recognition exact-match, wall/CPU time, plus process wall/CPU and peak RSS. Independently reconstruct every scenario's intended transformed shape, verify exactly one matching station, hash each scenario, and BFS-check reachability to the goal and all stations. Check that win labels agree with delivered terminal outcomes.

Integrity gates: all 120 scenarios are unique and pass the independent world oracle; every pair has identical scenario hashes; sigma-0 arm outcomes and recognized keys match exactly; source/build/input locks match pre-run, post-run, and live recomputation; native extension is fresh. Efficacy is descriptive by cell: give exact counts, Wilson intervals, recognition errors, paired fixed/broken counts and exact McNemar p-values. Do not pool station counts or noise conditions. This first panel has 20 per cell and is a screening estimate, not a confirmatory threshold test.

## Reproducibility

Hash this preregistration, runner, scenario and measurement sources, loaded Python runtime closure, Rust source/manifests, native facade/extension/build manifest, recursively loaded core and LS20 seed closure, and direct environment script. Store a new lock and checkpoint each completed pair. Resume only under exact lock equality. The independent analyzer must reconstruct task truth and score from raw captures without importing the benchmark's scoring/reporting code. Preserve censored captures and do not change seeds or thresholds after observing outcomes.
