# Cognition Build Phase 1 — Pre-Registration (`P1.H9`)

**Date:** 2026-10-20  
**Plan Reference:** `docs/research/engine_substrate/COGNITION_BUILD_P1_WIRING_PLAN.md` §P1.H9

---

## 1. Research Question

Do the four Phase 1 graph bridges (`capability_synthesis_bridge`, `decomposition_consumer`, `impasse_simulation_bridge`, `consolidation_scheduler`) change functional cognitive outcomes under `boot_cognition_on()`, rather than merely minting inert bookkeeping nodes?

---

## 2. Experimental Arms

Both arms boot the identical profile via `boot_cognition_on()` (`CORE_SEEDS + COGNITION_ON_SEEDS`) and receive the identical seeded task stream (`N = 10` deterministic trials per task family, seeds `1000..1009`):

1. **Arm A (`bridges_enabled`):** The four P1 bridge policies remain at `enabled = 1` / `1.0` (as installed by `seeds/cognition_on_params.json`).
2. **Arm B (`bridges_disabled`):** All `CapabilitySynthesisBridgePolicy`, `DecompositionConsumerPolicy`, `ImpasseSimulationPolicy`, and `ConsolidationSchedulePolicy` nodes in the graph have `enabled` set to `0` (`0.0`) before the task stream runs.

---

## 3. Pre-Registered Measures

1. **M1 — Unresolved Capability Collapse Settlement Rate within `K = 2` Cycles (A1):**
   - *Protocol:* Trigger an order-0 capability collapse with no higher-order continuation (`status == "unresolved_capability_collapse"`, `synthesis_requested == 1`), then attach a higher-order `CapabilityProgram` (`order: 1`, `holds_default_capability_outcome`) via `continues_to_higher_order_capability_program` and run at most `K = 2` cognitive cycles (`tick()`).
   - *Metric:* Fraction of trials (`N = 10`) in which `CapabilityCollapseState.status == "settled"` and `CapabilitySynthesisRequest.status == "fulfilled"` within `K = 2` cycles without any host poke to `CapabilityCollapseState.status` or `CapabilityResidualChannel.pending`.
   - *Falsification threshold:* Arm A settlement fraction `== 1.0`; Arm B settlement fraction `== 0.0`.

2. **M2 — Dual-Process Tie Imagined Candidate Ground-Truth Match Rate (A4):**
   - *Protocol:* Present a `DecisionEpisode` with two tied `DecisionCandidate`s (`"act_high"`, `"act_low"`) so `dual_process_core` escalates with `EscalationContext{status: "escalated", reason: "tie"}`, in a fixture world with known `WorldModelTransition`s where `"act_high"` leads to a higher-utility state (`predicted_utility_mean`) than `"act_low"`. Run 2 cognitive cycles (`tick()`).
   - *Metric:* Fraction of trials (`N = 10`) in which an `ImaginedCandidate` is minted on the `DecisionEpisode` and its `action` attribute equals `"act_high"`.
   - *Falsification threshold:* Arm A match rate `== 1.0`; Arm B match rate `== 0.0` (0 `ImaginedCandidate` nodes minted).

3. **M3 — Order-3 Impasse Partitioning & Child Progress Rollup Rate (A2):**
   - *Protocol:* Escalate a persistent `Fault` through `impasse_escalation` (`order3_reframe`, `needs_decomposition = 1.0`) with `PartitionKey` nodes (`k_a`, `k_b`) and `CandidateOperator`s, tick once to mint `child_fault`s, then resolve one child (`saturation = 0.0`) while leaving the other saturated (`saturation = 1.0`), and tick once more.
   - *Metric:* Fraction of trials (`N = 10`) in which `parent.decomposition_handled == 1.0`, `count(child_fault) == 2`, and `parent.child_mean_saturation == 0.5`.
   - *Falsification threshold:* Arm A rate `== 1.0`; Arm B rate `== 0.0`.

4. **M4 — Offline Replay `SemanticSupport` Accrual vs Step Cost (B1):**
   - *Protocol:* Record 2 episodic traces on the agent (`EpisodeTrace` nodes linked to concepts and an unmaintained `WorkingMemorySlot{maintenance_demand: 0.1, decay_tau: 2.0}`), then deliver 16 idle `NetworkModeSample`s (`epoch = 1..16`, `task_demand = 0.05`, `salience = 0.05`).
   - *Metric:* Count of completed `MemoryCycle`s, `ReplayTrace`s, `SemanticSupport` nodes (`support_count`), expired `WorkingMemorySlot`s (`status == "expired"`), and mean rule firings (`steps`) per `tick()`.
   - *Falsification threshold:* Arm A produces `4` completed `MemoryCycle`s, `4` `ReplayTrace`s, `>= 1` `SemanticSupport` node with `support_count >= 4.0`, and expires the unmaintained working-memory slot; Arm B produces `0` `MemoryCycle`s, `0` `ReplayTrace`s, `0` `SemanticSupport` nodes, and `0` expired slots.

5. **M5 — Byte-Identical Default Boot & Regression Gate:**
   - *Metric:*
     - `WorldAdapter()` default boot contains none of the P1 seeds in `installed_seeds(w.s)` and none of the P1 rule names in `w.inner.export_rules()`.
     - `scripts/failure_baseline.py verify --list results/cognition_gate_baseline.json` reports `0` new failures.

---

## 4. Open Questions to Answer Empirically in `COGNITION_BUILD_P1_RESULTS.md`

1. **Q1:** Does minting `ImaginedCandidate` via `has_imagined_candidate` automatically alter `dual_process_core`'s `chosen_action`, or does `ImaginedCandidate` remain advisory until a downstream arbitration rule consumes `has_imagined_candidate`? Should `ImaginedCandidate` become System-1/System-2 arbitration-eligible in Phase 2/3?
2. **Q2:** Does `child_mean_saturation` on the parent `Fault` automatically clear `parent.saturation`, or does `parent.saturation` remain at its prior value until an explicit parent-clearance rule acts on `child_mean_saturation`? Should `child_mean_saturation` drive `parent.saturation` directly?
