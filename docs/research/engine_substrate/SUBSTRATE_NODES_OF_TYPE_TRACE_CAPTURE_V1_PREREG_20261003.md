# `NodesOfType` access-trace capture v1 preregistration

Date: 2026-10-03  
Status: preregistered before the versioned replay.

## Question

Does the current native evaluator emit an explicit typed-population query event for each `NodesOfType` Term evaluation, including empty results, and a candidate event for every returned node, without changing task semantics?

## Workload and capture

Run the established three-worker, two-prompt live frame-interface fixture through a fresh process per replicate. Use the source-built measuring extension. Preserve request-time access/work traces, full graph and semantic digest, task lifecycle, native rule exports before and after each request, and existing semantic controls. Do not overwrite v1 or v1.1 artifacts. The new event codes are the existing `term_typed_population_query` (34) and `term_typed_population_candidate` (35); other emitters of those shared event kinds are retained and reported.

## Gates

1. Three distinct worker processes; stable source lock before/after every worker and after the run; measuring-engine provenance passes.
2. Both prompts, task lifecycle, all existing semantic controls, and stable exported definitions reproduce.
3. Final semantic graph digest equals the accepted v1.1 digest; all three workers agree.
4. Access and work traces report zero dropped rows. New event counts and per-rule/type groupings are retained, including query groups with no candidate rows.
5. For every candidate event, a matching `term_type_read` for the same RuleUID, node, and type is present with at least the candidate count. This is a cross-event consistency check, not a full semantic oracle.
6. Archive hashes and source hashes remain stable; raw capture is losslessly compressed.

## Interpretation boundary

A query marker proves that an instrumented query site ran; it does not prove all graph dependencies are traced. Candidate events expose returned population members but not every host/scheduler dependency. Event kinds 34/35 are shared with other typed-population paths, so the report will not attribute all such rows to `NodesOfType` without rule-syntax/source context. This fixture measures instrumentation coverage and overhead only on one authored prompt pair; it does not establish locality prevalence, exact partitionability, or scaling.

## Runtime cost

Report end-to-end request time and event-row volume for comparability with v1.1. This replay is not an isolated instrumentation-on/off benchmark; interpret timing only as a coarse continuity check because the rebuilt binary and capture instrumentation change.
