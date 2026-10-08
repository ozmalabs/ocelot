# Scheduler checkpoint transfer v1 preregistration

## Question

Does `RuleSchedulerCheckpointV1` reproduce closure work outside the captured conversation route, on two independently authored substrate workload families: productive CAN coactivation closure and retinal percept synthesis?

## Method

Use the existing CAN and retinal source seed definitions, with fixed small workload fixtures (CAN: N=32, Q=128; retina: 12 columns, uniform receptor counts). In each family, capture the full graph, exported ordered rule store, and scheduler checkpoint immediately before a productive `run_rules` call, then capture again after that call at the next fixed-point invocation. For each of the four states, create a fresh substrate, import graph and rules, restore scheduler state, verify round-trip, and run once at the same 100,000-step cap. Map per-rule counters by local rule index; compare graph, rules, scheduler state, global counters (excluding timing fields), and per-rule metrics against the corresponding live call. Lock source, seed, protocol, runner, analyzer, and engine before execution.

## Acceptance and limits

Report each family and state independently. Exact round-trip and exact measured outcomes pass only when all non-timing aggregate and per-rule values agree, and final graph/rule/scheduler states match. Retain all failures. This is a two-family transfer check on small synthetic fixtures, not natural-task prevalence, scaling, automatic frame discovery, or learning of new dimensions. It does not broaden the scheduler checkpoint beyond its current fields.
