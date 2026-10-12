# Bigville connected-frame stress preregistration

**Question.** On the current runtime CAN rule path, does a shared-graph frame wakeup schedule preserve full-graph fixed-point validity when controlled inter-frame edges connect otherwise independent authored resident CANs? How do boundary incidence and operation counts change across sparse frame topologies?

**Scope.** This is a controlled stress experiment on the 100 authored Bigville residents. Cross-resident links are injected only for this benchmark; they are not part of the authored Bigville model and no prevalence claim follows. It tests the existing native scoped settlement plus a Python static dependency queue, not generic native GALS or exact monolithic basin selection.

## Locked design

- Use all 100 residents from `seeds/bigville_cast100.json`, the current `can_native_update_3state` rule, and the current native extension.
- For each condition, construct the authored resident CANs, then add symmetric `causal_influence` pairs between each frame's `world_safe` Concept and selected other frames' `world_safe` Concept. Each added pair has weight `0.2` in both directions.
- Conditions: disconnected (0 pairs), ring (one pair per adjacent frame, including wraparound), and star (resident 0 linked to residents 1–99). The ring has at most two neighboring frames per frame; the star exposes degree 99 at its hub.
- For each condition, run full round-robin scoped settlement and event-queue settlement from the same built graph, then apply the ten authored scenario evidence updates at resident positions 0, 10, …, 90. The event arm starts each update by waking its target frame and wakes adjacent frames when a frame's state changes.
- Record exact state parity, independently recomputed full-graph residuals, terminal status, candidate/Term counters, queue turns/enqueues, cut edge count, and per-frame cross-edge degree. Include setup and settlement wall time as descriptive data; no timing gate.
- Each arm runs in a fresh process. A separate analyzer checks the locked input/source hashes, topology arithmetic, checkpoint counts, counter nonnegativity, terminal statuses, and residual recomputation from stored states/fields/weights.

## Decision rules and limits

The primary semantic gate is that both policies terminate and every returned state has zero residual under the full graph. Exact monolithic state equality is reported separately because update order can change the selected fixed point. Operation-count differences are descriptive for these three injected topologies. A failure is retained in raw output and is not repaired by changing thresholds or topology after execution.

This experiment cannot establish natural boundary-width prevalence, separator discovery, boundary-message completeness for arbitrary rules, native scheduling, or a general scaling law. A passing result supports only this CAN update rule and these controlled graph perturbations. A failing result identifies a wakeup or scheduling counterexample for follow-up.

## Reproduction

The runner and lock will be recorded alongside the raw report. Run `python3 scripts/substrate_bigville_connected_frame_stress.py`; it verifies locked inputs and native build freshness before starting workers.
