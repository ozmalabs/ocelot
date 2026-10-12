# Residual-to-composer grounding boundary v1 preregistration

This paired diagnostic tests the current learning handoff between an observed task error and structural proposal generation. Four fresh navigation workers begin from the same faulted `hop_descend_gradient` rule. Each runs one training direction, observes the actual wrong action and expected action, and passes only generic `actual`/`expected` output fields to `induce_concern` without `name_hint`, target name, operator cue, or prebuilt `CapabilityAxis`. The resulting induced axis is sent to `ground_concern`. A separate fresh context in each worker runs the existing authored A8 cue as a positive proposal control.

The preregistered raw-residual outcome is that induction mints an axis with the generic residual predicates, but held-relation grounding refuses and no proposal is emitted. The positive control must build `flip_comparison` on `hop_descend_gradient`. In both branches the primary rule must remain unchanged during proposal construction. The design measures the handoff boundary, not task utility; the authored control's utility was evaluated separately in A8 v1.4. Four workers are isolated repetitions of one task/rule family.

- Runner: [measure_residual_to_composer_grounding_boundary_v1.py](../../../evaluation/substrate_capability/measure_residual_to_composer_grounding_boundary_v1.py)
- Analyzer: [analyze_residual_to_composer_grounding_boundary_v1.py](../../../evaluation/substrate_capability/analyze_residual_to_composer_grounding_boundary_v1.py)
- Lock: [residual_to_composer_grounding_boundary_v1_lock_20261002.json](../../../evaluation/substrate_capability/residual_to_composer_grounding_boundary_v1_lock_20261002.json)
- Results: [residual_to_composer_grounding_boundary_v1_20261002.json](../../../evaluation/reports/residual_to_composer_grounding_boundary_v1_20261002.json)
