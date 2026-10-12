# Live describe-scene Percept-count scaling v1 preregistration

## Question

How do end-to-end candidate tests, Term evaluations, scheduler/deferred work, native selected accesses, time, and peak RSS change as task-owned Scene/Percept input grows on the full-seed `describe_scene` route, with an irrelevant Concept population held fixed?

## Factors and workload

Use Percept counts 3, 6, 12, and 24. Cycle the same three known Percept descriptions (grey static, yellow meter, blue mover) to make each larger scene a balanced multiset. Every input Percept must receive exactly its expected single `is_a` relation; no Percept may receive an incorrect class. The semantic reply oracle requires all three supported propositions at least once, so duplicate scene entries do not require duplicate wording. Preserve exact text and outbound graph alignment as separate observations.

Add exactly 4,096 `kind=noise` Concepts in one dedicated Microtheory to every worker before measuring the request. They have no target names or `Holds` facts; none may receive an `is_a` edge. Keep the same full seed profile, prompt, speaker, active/authored rules, and production request path. Noise construction and Scene attachment occur outside the timed request and are reported separately.

Use two fresh-process replicates per Percept count and paired audited/uninstrumented arms (16 workers). The audited arm captures scale-audit global/per-rule/per-clause candidate and Term counts, selected access events, and operation-work rows. Capture request wall/process CPU, peak RSS, full graph counts/digest, response and Goal lifecycle, per-Percept classification, and outbound-message alignment.

## Gates

1. Sixteen unique fresh worker PIDs, complete factorial, source/native hashes unchanged at worker start/end/post-run.
2. Every worker uses the assigned Scene count and fixed 4,096 noise concepts; base seeds/rules stay invariant and noise gains no `is_a` edges.
3. Every Percept is classified exactly once to its expected concept, with no wrong class; one request Goal resolves with `selection → execution → action_result`; the semantic reply contains all three expected propositions.
4. Audited and uninstrumented workers match within each pair on response, Goal projection, graph node/edge counts, and semantic whole-graph digest.
5. Candidate/Term counters reconcile with per-rule, per-clause, unattributed, and Term-variant totals; ambiguous rule IDs have no per-rule rows. Access and operation-work streams conserve counts, have zero drops, and remain empty in uninstrumented arms.
6. Discrete work profile and semantic graph repeat exactly between replicates at each size. Wall time and RSS remain descriptive, not pass/fail criteria.

If a size fails the task oracle, preserve the raw worker and report the failure for that size; do not silently exclude it or infer successful scaling.

## Claim boundary

This is one authored live route with repeated known semantic classes and one fixed synthetic distractor population. It measures data-size sensitivity, not novel concept learning, natural input prevalence, learned frame discovery, safe partition execution, or general AI capability. Candidate tests, Term evaluations, scheduler slots, native accesses, elapsed time, and RSS are different measures; do not pool them into a single cost number.

## Reproduction

Use `PYTHONPATH=runners/dsl/python:.`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Generate the source lock with `scripts/substrate_live_describe_scene_percept_scale_v1.py --lock`, then run the same script. It refuses to overwrite existing lock or report files.
