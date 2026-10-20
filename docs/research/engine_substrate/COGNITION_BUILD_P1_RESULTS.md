# Cognition Build Phase 1 — Evaluation Results (`P1.H9`)

**Date:** 2026-10-20  
**Pre-Registration Reference:** `docs/research/engine_substrate/COGNITION_BUILD_P1_PREREG.md` (`0978fb24`)  
**Plan Reference:** `docs/research/engine_substrate/COGNITION_BUILD_P1_WIRING_PLAN.md` §P1.H9

---

## 1. Two-Arm Evaluation Summary (`N = 10` trials per arm, seeds `1000..1009`)

Both arms boot `boot_cognition_on()` (`CORE_SEEDS + COGNITION_ON_SEEDS`, mean boot latency `44.7 ms` in Arm A, `47.9 ms` in Arm B) and execute the identical task stream.

| Measure | Pre-Registered Target (Arm A vs Arm B) | Arm A (`bridges_enabled`) | Arm B (`bridges_disabled`) | Verdict |
|---|---|---|---|---|
| **M1 (A1):** Unresolved capability collapse settlement rate within `K = 2` cycles after higher program supply | `1.000` vs `0.000` | **`1.000`** (`10/10`) | **`0.000`** (`0/10`) | **PASS** |
| **M2 (A4):** Dual-process `instinct_conflict` tie `ImaginedCandidate` ground-truth match rate (`root_action_kind == "forward"`) | `1.000` vs `0.000` | **`1.000`** (`10/10`) | **`0.000`** (`0/10`) | **PASS** |
| **M3 (A2):** Order-3 impasse (`needs_decomposition`) partitioning + `child_mean_saturation` rollup rate | `1.000` vs `0.000` | **`1.000`** (`10/10`) | **`0.000`** (`0/10`) | **PASS** |
| **M4a (B1):** Completed offline `MemoryCycle`s / `ReplayTrace`s across 16 idle epochs (`cooldown_epochs = 4.0`) | `4.0` vs `0.0` | **`4.000`** (`epochs 1, 5, 9, 13`) | **`0.000`** | **PASS** |
| **M4b (B1):** Replay-driven `SemanticSupport.support_count` accrued across 16 idle epochs | `>= 4.0` vs `0.0` | **`4.000`** | **`0.000`** | **PASS** |
| **M4c (B1):** Unmaintained `WorkingMemorySlot` expiry rate via bound `has_memory_clock` | `1.000` vs `0.000` | **`1.000`** (`10/10`) | **`0.000`** (`0/10`) | **PASS** |
| **M4d (Cost):** Mean rule-firing steps per idle epoch (`tick()`) | Recorded | **`6.250` steps/epoch** | **`1.938` steps/epoch** | **`+4.312` steps/epoch** (`+17.25` steps per consolidated replay cycle) |
| **M5 (Gate):** Default `WorldAdapter()` isolation & 20-file cognition gate baseline verification | `0` new seeds/rules; `0` new test failures | `0` new seeds/rules in default boot; `0` new failures | — | **PASS** |

---

## 2. Empirical Answers to Pre-Registered Open Questions

1. **Q1 — Should an `ImaginedCandidate` become System-1 eligible (or feed System-2 arbitration directly)?**
   - *Observation:* In both Arm A and Arm B, `DualProcessContext.status` remains `"escalated"` after `isb_propose_imagined_candidate` mints `ImaginedCandidate{status: "proposal", provenance_kind: "imagined", observation_status: "not_observed", root_action_kind: "forward", expected_value: 0.576}` on `SystemTwoEscalation`.
   - *Finding:* Keeping `ImaginedCandidate` distinct from `SystemOneCandidate` preserves the provenance invariant that unexecuted counterfactual rollouts (`provenance_kind: "imagined"`, `observation_status: "not_observed"`) are never confused with grounded System-1 habits (`grounded: 1`). However, because no downstream rule in `dual_process_core` currently reads `has_imagined_candidate` to resolve `DualProcessContext`, the proposal is advisory unless a System-2 arbitration rule consumes `has_imagined_candidate` (without promoting it to System-1 until an action is actually executed and observed).

2. **Q2 — Should `child_mean_saturation` drive parent `saturation` directly?**
   - *Observation:* In Arm A, `dc_parent_progress_from_children` computes `ax.child_mean_saturation == 0.5` when the two partitioned child `CapabilityAxis` nodes reach `saturation = 1.0` and `0.0`, while `ax.saturation` remains at its original `0.2`.
   - *Finding:* Writing `child_mean_saturation` as a separate diagnostic attribute prevents circular feedback with `impasse_escalation`'s order-1/2/3 saturation guards on the parent axis while decomposition is still in progress. A separate completion rule (e.g., when all `decomposes_into` children exceed the saturation threshold) is the clean mechanism to resolve the parent `Impasse` and update parent `saturation` without premature de-escalation.

## 3. Deferred work carried forward

- The `ImaginedCandidate` consumer is deferred to P5.E4 (multi-step planning) or Track I5. P1 established that the proposal remains advisory until a grounded arbitration consumer exists.
- The parent-completion rule that converts `child_mean_saturation` into parent `saturation` is deferred to Phase 5. P1 keeps the child rollup diagnostic to avoid premature de-escalation during decomposition.
- The P1 bridges' inline budget debit remains as implemented. P3 is the first consumer of the generic pending-request contract in `thinking_budget`; the bridges are not migrated in this phase.
