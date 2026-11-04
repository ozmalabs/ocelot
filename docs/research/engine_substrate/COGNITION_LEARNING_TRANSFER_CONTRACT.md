# Fresh target learning and transfer contract

**Status:** P20 implementation contract. The supported first target learner is the existing native, receipt-bound categorical transition inducer. It learns only a repeated `(action, object type, feature, before value) → after value` effect. It does not claim general process, language, or representation learning. `TargetLearningPolicy` remains disabled by default.

## Common target learner

Every comparison arm starts with the same empty target graph, learner rules, primitive affordances, target frame, model epoch and shared `ThinkingBudget`. The learner consumes `TransitionObservation` records only when matching action and outcome receipts bind owner, episode, event, source/model/frame epochs and status. Native rules create and revise hypotheses; adapters may expose world events and read terminal receipts, but may not infer effects or choose a winning hypothesis.

Fresh, source-exposed and mismatched-source arms use the same target probes, action choices, target-side learner, verification rules and caps. Source evidence can propose a prior only after a declared source/target map and exact source provenance are supplied. It cannot count as target evidence, bypass target verification, or be inserted as a verified target effect. Mismatched, stale, incomplete and contradictory sources stay explicit and must not be silently discarded.

## Exposure and accounting

Record separately: evidence opportunities, visible observations, missing/occluded observations, target primitive actions, source-information units, native rule/model-query units, elapsed time, graph nodes/bytes and budget debits. All arms receive equal target opportunities and total declared work caps. A source exposure is charged even when it is uninformative. A probe counts as an interaction when the learner causes a target-world action; passive observation does not.

Learning curves use fixed interaction checkpoints and all allocated streams. Unsolved, censored, unsupported and invalid-source outcomes remain in denominators with distinct statuses. Report success-vs-interactions area and interaction-to-success separately. A target transition learned from observations is not a solved task until an independent target test and world receipt confirm it.

## Scope and controls

The initial executable slice supports finite categorical effects with exact receipts and current epochs. Missing outcome, wrong owner, mismatched receipt, changed model/frame epoch and contradictory effects must not create an adopted target model. Demonstration, witnessed observation, instruction and reward evidence retain distinct labels. Own-action receipts remain behind existing authorization and action-safety gates. No hidden source AST, target answer, goal-action field, teacher marker or held-out result may enter learner input.

P20's preregistration must use two independently coded domain pairs, working learner adapters in every arm, fresh-arm development competence, disjoint source/target/held-out allocations, fixed evidence/work limits and the plan's registered efficacy thresholds. If these conditions are absent, freeze is blocked; an inert arm is never scored as zero skill.
