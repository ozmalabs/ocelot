# GenMint process-restart persistence and reuse v1 preregistration

## Question

Does a training-acquired `DimensionGenerator` remain available and useful after the substrate graph, grammar, and native rule store are saved and loaded in a separate process, and what extra cost does that durable reuse add? This isolates checkpoint durability and downstream selection in the already measured 2-D integer-linear family. In this division-of-labor stage, the LLM/meta-controller chooses the task family and budget; GenMint measures object-level substrate improvement. This is a persistence gate, not substrate meta-learning and not a new-family generalization estimate.

## Fixed task cells and arms

Use the v3 matrix reuse fixtures and held-out generator, with six fixed matrix/layout cells:

| Matrix | Predicate layout |
|---|---|
| `prior_matrix` | `adjacent_01`, `opposite_03` |
| `shearA` | `adjacent_01`, `opposite_03` |
| `shearB` | `adjacent_01`, `opposite_03` |

For every cell run three arms, five fresh-process replicates per arm, and the same 16 held-out bases (K=16):

1. GenInfer enabled, train and apply in one process (`continuous_enabled`).
2. GenInfer enabled, train in one process, checkpoint, load in a second process, and apply (`restart_enabled`).
3. GenInfer disabled, train in one process, checkpoint, load in a second process, and apply (`restart_disabled`).

This is 90 sequences. Repeat counts estimate source/runtime reproducibility and timing variation only; the six matrix/layout cells are the task diversity. Randomize the full worker schedule from the locked seed. Reuse the exact matrix/layout/replicate/heldout inputs across matched arms.

## Checkpoint contract

Checkpoint the complete native graph (`graph_to_dict`), dynamic grammar (`grammar_to_json`), native rule store (`export_rules`), agent node ID, and source/task provenance. In the restart arm, construct a fresh native `Substrate` in a distinct child process, restore the graph, replay grammar productions with the mirror-free loader, import rules, and verify graph/grammar/rule parity before applying held-out observations. A checkpoint round-trip that merely preserves the generator node but fails to execute the production selection route is a failure. Do not re-seed or retrain in the application process.

## Measures and gates

For every sequence record training acquisition status, exact intended-matrix presence, selected generator and residual on each held-out call, independent exact output score, graph/grammar/rule parity, checkpoint bytes and write/read cost, train/application/boot wall and CPU time, peak RSS, and per-call closure time. Retain all misses and worker errors in the denominator.

Primary persistence gate: every enabled restart worker must restore exact graph/grammar/rule state, and every held-out call routed through the training-acquired generator must exactly match the independently reconstructed target. Report acquisition failures separately; do not count a restart as successful acquisition merely because `recognized_transformed` is returned. Compare paired end-to-end training-plus-application cost by matrix/layout and total K=16, including checkpoint and reload time in the restart arm. Report medians and all worker values; do not claim population-level amortization from this fixed panel.

Integrity gates: locked source/native/task hashes; unique child PIDs; exact 90-cell randomized schedule; balanced matched arms; independent input/target reconstruction; checkpoint file hash/byte reconciliation; stable semantic outcomes within each repeated cell; complete status and cost fields. Any invalid cell remains reported and blocks the corresponding claim.

## Claim boundary and stop rule

Passing establishes only that selected trained 2-D generators survive this explicit graph/grammar/rule checkpoint and are reused by the selected held-out route on this source revision. It does not establish persistence for every graph-resident concept, natural-task acquisition frequency, general transfer, stable economic crossover, or Rung 3/4 primitive invention. If graph parity passes but route use fails, stop and diagnose missing runtime/index state before expanding matrices. If the checkpoint adds cost with no matched held-out benefit over `restart_disabled`, report durable state without demonstrated economic value.

## Reproduction artifacts

The runner, analyzer, frozen input lock, and raw report are listed in the result document after capture. The prior controlled baselines are [GenMint v2 extended-horizon reuse](SUBSTRATE_GENMINT_MATRIX_REUSE_V2_RESULTS_20260926.md) and [GenMint v3 matrix-family reuse](SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3_RESULTS_20260926.md).
