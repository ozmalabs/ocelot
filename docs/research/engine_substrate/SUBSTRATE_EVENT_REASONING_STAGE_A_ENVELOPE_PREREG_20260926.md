# Event-reasoning Stage A applicability envelope preregistration

## Question

For an authored rule chain with independently matched entities, what share of closure drains is admitted by Stage A, how often does runtime overlap fallback occur, and how do exact outcomes and descriptive runtime scale with entity count?

## Workload and design

Load `seeds/event_reasoning.json` through `engine_rules_only`, retaining its authored `infer_on_floor`, `infer_broken`, and `infer_worthless` rules. For N=1, 4, 16, 64, and 256, create N independent `Entity` nodes with `fell=1`, `fragile=1`, and a self-loop `is_entity` match edge. The authored rule chain should derive `on_floor`, `broken`, and `worthless` plus each corresponding `_inferred` marker. Run six fresh identical substrates per size, one worker for each permutation of ordinary, compare-only, and Stage-A-enabled arm order. This balances warm-up/order effects across six independent workers.

The matched-run admission count is compare-only `compared_drains`; the excluded count comes from the Stage-A-enabled arm. The admitted drain share is `compared / (compared + excluded)`. The overlap fallback rate is `enabled conflict_fallbacks / compared`, undefined if compared is zero. Proposal/write counts measure Stage-A derivation work. Wall/CPU times exclude graph/rule setup and are descriptive; compare-only is deliberately diagnostic and is not the timing arm.

## Gates and provenance

Use six fresh worker processes, each covering all five sizes once in its assigned arm order. Lock the seed manifest, protocol, runner, Python seed loader, relevant Rust sources, native extension/build manifest, and commit at worker start/end. All three arms must settle within budget, reach the independent per-entity oracle, and agree exactly on complete graph state and progress/terminal behavior. Compare-only must show at least one compared drain at every size with zero divergence/unsoundness; enabled fallback counts must be zero or satisfy the rate denominator, with no Stage A exclusions for this one-variable workload. Preserve all raw failures.

## Claim boundary

This measures one authored three-rule implication chain on a synthetic collection of independent entities. It is not evidence that this eligibility profile is common in production workloads, that natural graphs are frame-local, or that Stage A improves performance. The zero-conflict outcome is specific to the workload and does not establish general conflict-guard soundness.
