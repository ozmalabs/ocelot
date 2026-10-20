# Cognition Build Phase 2 — Results

**Execution date:** 2026-10-21
**P2 implementation commit:** `1d5e63f9` (as recorded by the parent plan)
**P3 start commit:** `ff689b30`

This document records the Phase 2 gate on the P3 starting checkout. The plan said the P2 results doc and gate evidence had not been committed; the commands below were rerun for this record. Results describe this checkout, which also contains subsequent repository changes.

## Gate commands

| Command | Result |
|---|---|
| `OZMA_SEED_PERSIST_DISABLED=1 scripts/engine_cargo_test.sh --lib -- --test-threads=4` | **Failed with 2 tests / 840 passed / 4 ignored.** `substrate::tests::graph_rule_patch_node_receives_durable_commit_receipt` is the known baseline failure. `substrate::tests::independent_substrates_keep_overlapping_rule_indices_distinct_in_audit` also failed (`left: 3`, `right: 2`). |
| `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_engine_provenance_migrated.py -q -p no:cacheprovider` | **Passed:** 10 tests. |
| `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_geninfer_grain_migrated.py tests/test_gen_infer_migrated.py tests/test_soft_weights_term.py tests/test_cognitive_pareto_migrated.py tests/test_aperture_frame_migrated.py tests/test_thinking_budget_migrated.py tests/test_tolerance_registry_migrated.py tests/test_default_mode_core_migrated.py tests/test_impasse_simulation_bridge_migrated.py tests/test_consolidation_scheduler_migrated.py tests/test_cognition_profile_integration.py tests/test_lint_orphan_signals.py tests/test_engine_provenance_migrated.py tests/test_dimension_inference_migrated.py -q -p no:cacheprovider` | **Passed:** 104 tests. This is the 14-file P0–P2 task test set used for this rerun. |
| `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest $(cat scripts/cognition_gate_suite.txt) -q -p no:cacheprovider` | **Stopped without a final result after 14 minutes** while executing `tests/test_capability_control_fabric_migrated.py`; it continued consuming CPU past the baseline's 420-second per-file unestablished threshold. No aggregate pass/fail count can be claimed from this run. The pinned baseline lists four known failures and records that file as NOT_ESTABLISHED, not red. The Phase 3 gate uses the repository's per-file baseline protocol to avoid letting this one file prevent the remaining comparisons. |

## As-built deviations relevant to P3

- `tolerance_registry` is data only: its five `Tolerance` records are not read or written by rules. P3 therefore writes the `Agent` attributes consumed by DimInfer and GenInfer directly.
- `thinking_budget` supplies the generic pending-request contract. P1 bridges debit inline; P3 is the first producer of a generic request node.
- `SoftWeights` is available and documented in `SOFT_ADMISSIBILITY_RECIPES.md`, but the P3 executor does not need it.
- Graded aperture relaxation and the non-residual questioning trigger are implemented; the aperture pathology test passes.
- `ImaginedCandidate` remains advisory with no consumer. P3 does not consume it.
- The P2 gate evidence was missing from the committed history; this document records a fresh gate run from the P3 start checkout rather than attributing that run to commit `1d5e63f9`.
