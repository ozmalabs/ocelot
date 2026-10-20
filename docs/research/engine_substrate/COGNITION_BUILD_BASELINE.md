# Cognition Build — Phase 0 Baseline & Decisions

Generated for `docs/research/engine_substrate/COGNITION_BUILD_P0_BASELINE_PLAN.md` (§P0.H1.5, §P0.G1.1).

- **Base commit:** `0ec3a2576b9e2c11258e96da74681834e7b57c5e`
- **Gate suite file list:** `scripts/cognition_gate_suite.txt` (20 test files)
- **Baseline artifact:** `results/cognition_gate_baseline.json`

## 1. Commands

### Per-file gate sweep and baseline construction

Because `tests/test_capability_control_fabric_migrated.py::test_channel_practice_expands_only_evidenced_dimension_and_failure_revokes` enters a 60,000-step rule loop on its fourth `agent.tick()`, running all 20 files in a single unguarded pytest process stalls on that file. Use the repo's per-file subprocess sweep tool (`scripts/failure_baseline_sweep.py`) followed by `scripts/failure_baseline.py`:

```bash
.venv/bin/python scripts/failure_baseline_sweep.py \
  --files-from scripts/cognition_gate_suite.txt \
  --out /tmp/cog_gate_sweep_raw.json \
  --workers 2

.venv/bin/python scripts/failure_baseline.py build \
  --raw /tmp/cog_gate_sweep_raw.json \
  --out results/cognition_gate_baseline.json \
  --condition "cognition_gate_suite.txt at HEAD 0ec3a257; per-file subprocess via failure_baseline_sweep.py"

.venv/bin/python scripts/failure_baseline.py verify \
  --list results/cognition_gate_baseline.json
```

### Rust unit test baseline

```bash
scripts/engine_cargo_test.sh --lib -- --test-threads=4
```

## 2. Targeted Gate Suite File Summary (20 files)

| File | Status | Passed | Failed | Skipped | Duration (s) |
|---|---|---|---|---|---|
| `tests/test_frozen_core_invariant.py` | `RED` | 8 | 3 | 0 | 2.6 |
| `tests/test_cognitive_architecture_integration_migrated.py` | `GREEN` | 3 | 0 | 0 | 4.8 |
| `tests/test_dual_process_core_migrated.py` | `RED` | 4 | 1 | 0 | 3.5 |
| `tests/test_default_mode_core_migrated.py` | `GREEN` | 3 | 0 | 0 | 3.7 |
| `tests/test_generative_world_model_migrated.py` | `GREEN` | 4 | 0 | 0 | 5.2 |
| `tests/test_episodic_working_memory_migrated.py` | `GREEN` | 5 | 0 | 0 | 4.9 |
| `tests/test_capability_collapse_migrated.py` | `GREEN` | 15 | 0 | 0 | 12.1 |
| `tests/test_capability_control_fabric_migrated.py` | `NOT_ESTABLISHED` | — | — | — | 420.1 (timeout) |
| `tests/test_counterfactual_experiment_migrated.py` | `GREEN` | 7 | 0 | 0 | 6.4 |
| `tests/test_capkey_backfill_migrated.py` | `GREEN` | 4 | 0 | 0 | 2.9 |
| `tests/test_arc_decompose_migrated.py` | `GREEN` | 21 | 0 | 0 | 8.3 |
| `tests/test_cognitive_supervision_migrated.py` | `GREEN` | 7 | 0 | 0 | 4.4 |
| `tests/test_aperture_frame_migrated.py` | `GREEN` | 6 | 0 | 0 | 3.8 |
| `tests/test_learning_aperture_migrated.py` | `GREEN` | 6 | 0 | 0 | 3.9 |
| `tests/test_cognitive_pareto_migrated.py` | `GREEN` | 7 | 0 | 0 | 4.1 |
| `tests/test_arousal_horizon_migrated.py` | `GREEN` | 5 | 0 | 0 | 3.6 |
| `tests/test_staleness_decay_migrated.py` | `ALL_SKIPPED` | 0 | 0 | 5 | 1.9 |
| `tests/test_demotion_hierarchy_migrated.py` | `GREEN` | 6 | 0 | 0 | 3.8 |
| `tests/test_core_emotions_migrated.py` | `GREEN` | 15 | 0 | 0 | 6.2 |
| `tests/test_engine_provenance_migrated.py` | `GREEN` | 8 | 0 | 0 | 2.4 |

- **Totals:** 16 `GREEN`, 2 `RED` (4 failing node IDs), 1 `ALL_SKIPPED`, 1 `NOT_ESTABLISHED`.
- **`failure_baseline.py verify --list results/cognition_gate_baseline.json`:** `held (still red): 4`, `STALE: 0`, `NEW: 0`.

## 3. Pre-Existing Failing Node IDs (4)

| Node ID | Class | Last Green Commit | Failure Summary |
|---|---|---|---|
| `tests/test_dual_process_core_migrated.py::test_unique_grounded_default_commits_without_system_two` | Pre-existing (`RED`) | `a1f0565c` | `AssertionError: assert ['unlabelled_legacy_settle'] == []` — `run_unlabelled_legacy` in `runners/dsl/src/cognitive_cycle.rs` appends `"unlabelled_legacy_settle"` to `report["trace"]` when unlabelled rules settle. |
| `tests/test_frozen_core_invariant.py::test_frozen_core_set_reports_the_closure_with_no_manifest_drift` | Pre-existing (`RED`) | `efdd2e86` | `AssertionError: Frozen-core manifest drift` — `boot_all._FROZEN_SEED_IDS` vs `CORE_SEEDS` / `OPTIONAL_CORE_SEEDS` closure mismatch. |
| `tests/test_frozen_core_invariant.py::test_frozen_seed_ids_closed_folds_in_enact_and_discourse` | Pre-existing (`RED`) | `efdd2e86` | `AssertionError` — `_FROZEN_SEED_IDS` closure drift on `enact` / `discourse`. |
| `tests/test_frozen_core_invariant.py::test_manifest_matches_live_constants_no_drift` | Pre-existing (`RED`) | `efdd2e86` | `AssertionError` — frozen manifest vs live constants drift. |

### Notes on `NOT_ESTABLISHED` and `ALL_SKIPPED` files

- **`tests/test_capability_control_fabric_migrated.py` (`NOT_ESTABLISHED` — per-file timeout at 420s):**
  - 6 of 7 tests in this file pass in `< 1s` when run individually (`-k "not test_channel_practice_expands_only_evidenced_dimension_and_failure_revokes"`).
  - `tests/test_capability_control_fabric_migrated.py::test_channel_practice_expands_only_evidenced_dimension_and_failure_revokes` stalls on its fourth `agent.tick()` (entering the 60,000-step rule loop): when `cc_reset_failed_compiled_channel_boundary` resets `trained.boundary_quanta` from `8` back to `3`, the earlier settled `CapabilityCollapseState` (at `epoch=1, outcome_verified=1`) satisfies `cc_record_traversed_residual_channels`, whose `add_node_if_absent` matches `credited: 0` while `cc_credit_channel_practice_success` immediately flips `credited` to `1`, minting a new `CapabilityChannelPracticeEvidence` node on every step.
- **`tests/test_staleness_decay_migrated.py` (`ALL_SKIPPED`):**
  - Marked `pytest.importorskip("matplotlib")`; `matplotlib` is not installed in `.venv`.

## 4. Rust Baseline (`P0.H1.4`)

Command: `scripts/engine_cargo_test.sh --lib -- --test-threads=4`

- **Result:** `836 passed; 1 failed; 0 ignored`
- **Failing Rust test:** `substrate::tests::graph_rule_patch_node_receives_durable_commit_receipt` (pre-existing failure at `2cd46a6a` and `0ec3a257`).

## 5. `dual_process_core` Status Decision (`P0.G1.1`)

- **Decision:** Keep `dual_process_core` in `substrate/boot_core.OPTIONAL_CORE_SEEDS` (`opt_in_core_seeds=("dual_process_core",)`). Do **not** promote it to `CORE_SEEDS` in Phase 0.
- **Reason:**
  1. `CyclePlan::select` in `runners/dsl/src/cognitive_cycle.rs` switches the cognitive cycle from `CyclePlan::Legacy` to `CyclePlan::DualProcess` whenever `dual_process_core` rules are loaded in the graph.
  2. Under `CyclePlan::DualProcess`, all unlabelled rules are routed through `run_unlabelled_legacy` after the six dual-process phases, which changes rule-scheduling order for unlabelled rules and appends `"unlabelled_legacy_settle"` to `report["trace"]`.
  3. Ground rule #2 (`COGNITION_BUILD_PLAN_20261010.md` §1) requires default boots to remain byte-identical until Phase 1.8 (`boot_cognition_on()`). Keeping `dual_process_core` in `OPTIONAL_CORE_SEEDS` preserves default boot behaviour, while `boot_cognition_on()` (Phase 1.H8) can opt in explicitly.
  4. The inaccurate doc comment above `run_unlabelled_legacy` in `runners/dsl/src/cognitive_cycle.rs` has been updated (`P0.G1.2`) to state accurately that `dual_process_core` is an optional core seed (`OPTIONAL_CORE_SEEDS`).
