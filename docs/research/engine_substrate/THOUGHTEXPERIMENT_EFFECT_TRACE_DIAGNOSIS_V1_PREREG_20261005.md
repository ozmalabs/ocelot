# Thoughtexperiment effect-trace diagnosis v1 preregistration

## Question and scope

Does the native effect-value report expose enough firing-time binding information to localize which rule effect changed a known failing node, when the caller has the rule event report but has not rerun matching or reconstructed the firing environment?

## Held-out cases

Generate 80 deterministic cases in four strata with 4, 8, 16, and 32 target nodes/effects (20 each). Each case has one anchor connected to all targets with typed slot edges. One rule firing binds a variable to each target and applies one `set_attr` per variable. Clause order, node insertion order, and effect order are separately shuffled from a fixed case-specific seed. Exactly one randomly selected target is assigned health 999; the remaining effects assign health 1. The diagnosis query supplies the event report and failing target node ID. Oracle truth is the effect index associated with that target variable.

Three independent workers replay all cases through endpoint-only and effect-level observer APIs. The endpoint baseline has only the aggregate rule event and touched-node set, so its candidate set is all effect indices in the firing; its fixed top-1 prediction is the smallest index. The effect observer predicts the index whose effect snapshot contains the target node's transition to health 999. The analyzer recomputes predictions from raw snapshots and does not trust reported candidates.

## Gates and interpretation

Require 80/80 cases, three distinct workers, exact source/native lock stability, matching final behavior, one progressed firing per arm, endpoint reports without effect snapshots, complete untruncated per-effect values, exact effect-index localization, and worker replication. Report endpoint top-1 accuracy and candidate count by stratum, alongside effect-trace exact accuracy and candidate reduction.

This is an API-level observability test under a deliberately constrained input: event report plus failing node ID. It does not compare against a stronger baseline that rematches the graph or inspects the complete rule body, and does not show that a downstream learner repairs tasks or that the case distribution is natural. Positive results justify testing trace utility in a realistic held-out task route, not a general diagnosis claim.
