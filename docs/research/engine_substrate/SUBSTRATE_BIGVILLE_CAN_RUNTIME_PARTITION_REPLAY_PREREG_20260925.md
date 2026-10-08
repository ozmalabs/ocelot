# Bigville CAN runtime partition replay — preregistration

**Status:** preregister before execution. This is a project-authored task replay, not an external or natural-world sample. It tests frame settlement under actual Bigville resident CAN graph construction; it does not claim a discovered hierarchy beyond the graph-derived dependency components.

## Question

Do partitions derived from runtime causal-influence access in the authored 100-resident Bigville CAN cast support caller-notified settlement that matches full population rescans after sequential resident-level evidence updates, and how much candidate work does the queue visit?

## Frozen workload and protocol

- Input: all 100 residents, in source order, from `seeds/bigville_cast100.json`.
- Graph construction: `worlds.bigville_can_beliefs.install_productions`, `build_resident_can_mt`, and `apply_scenario_evidence`; one actual `Microtheory` and its five actual Concepts per resident, including the builder's directed causal edges and resident-specific weights/fields.
- Rule: only `can_native_update_3state` from `seeds/can_native_reimplementation.json`; each Microtheory uses 3-state mode, temperature 1.5, tick 0.
- Partition: derive undirected dependency components from the live native graph's `causal_influence` adjacency after construction. Map each component to its owning Microtheory via live `has_concept` membership. Require a bijection of 100 components to 100 Microtheories, five concepts each, and no causal edge crossing components. Do not use the resident index to construct the dependency components.
- Update sequence: residents at source-order positions 0, 10, 20, ..., 90 receive the exact two-item `SCENARIO_EVIDENCE` again, one resident per step, through `concept_apply_evidence`. Both arms start from the same fully settled, paired baseline.
- Event arm: seed only the component/frame containing the two changed concepts, then propagate to source frames that read any state changed in the current frame, using the live directed causal adjacency. Full-rescan arm: run every Microtheory in source order until an entire round has zero progress.
- Cap: 100,000 progress applications per settlement sequence. Enable/reset native scale-audit counters around each scoped call; report API frame turns, progress applications, candidate pairs, tested candidates, where evaluations, leaf visits, and Term evaluations/units.
- Oracles: compare all 500 final concept states after every update. Independently recompute the full-graph 3-state local-equation residual from saved fields and resident-specific weights. Include a no-notification control for the first evidence update; it is required to be sensitive if the event arm changes any state in that resident frame.

## Acceptance

All 100 runtime components must biject with the actual Microtheories and meet the recorded five-concept/zero-cross-edge contract. The initial paired baselines and every one of the ten sequential event/reference states must be identical and independently zero-residual under the local update equation. The run must settle under cap and preserve the exact list of ten evidence events. The no-notification control must show a positive residual if the notified first update changed a state; if it changed no state, report the control as insensitive and fail the negative-control criterion rather than claiming sensitivity. Work reduction is reported only as measured operation counts. No timing or asymptotic extrapolation is registered.

## Claim boundary

This workload has one fixed five-node resident topology repeated across the authored cast and no expected cross-resident causal edges. It can establish that these authored modules are graph-disconnected and that a queue avoids revisiting independent resident frames for local evidence changes. It cannot establish natural-world prevalence, learned partition discovery, cross-frame boundary correctness on connected workload topology, node birth/deletion, mint idempotence, native automatic notifications, or production GALS. Preserve failures and source hashes; do not modify fixture parameters in response to run outcomes.
