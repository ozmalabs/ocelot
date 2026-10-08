# Live describe-scene Percept × distractor factorial v1 preregistration

## Question

Does the measured cost of the full-seed `describe_scene` route depend on Percept count, irrelevant Concept-membership count, or their interaction? The prior one-factor captures show separate affine trends; this crosses the factors directly to test whether added global vocabulary multiplies the work per task-owned Percept.

## Factors and workload

Cross request-view Percept counts 3, 6, 12, and 24 with 0, 1,024, and 4,096 irrelevant Concepts in a dedicated Microtheory. Each larger Scene cycles the same three known percept descriptions evenly. Noise Concepts have unique names, `kind=noise`, and no target names or `Holds` facts. Every input Percept must receive exactly its expected single `is_a` relation; noise receives none. The semantic reply oracle requires all three known propositions; exact wording and graph-visible outbound-message alignment are separate outcomes.

Keep full-seed boot, prompt, speaker, active rules, source state and request path fixed. Noise creation and Scene attachment are outside the timed request. Use two fresh-process replicates for each of the 12 factor cells and paired audited/uninstrumented arms: 48 workers total. The audited arm records scale-audit candidate/Term totals with per-rule/per-clause attribution, selected native access events, and scheduler/deferred operation-work counters. Every worker records wall/CPU, peak RSS, graph counts and semantic digest, Goal lifecycle, reply, classification, and source fingerprints.

## Gates

1. Exactly 48 workers, two pairs in every cell, unique PIDs, and source/native lock equality at worker start/end/post-run.
2. Each worker receives exactly its factor values; loaded base Concept and membership counts remain invariant; noise has no class edges.
3. Percept, semantic reply, and resolved Goal oracles pass in every worker. Preserve failures and report them by cell.
4. Each audited/control pair matches reply, Goal, graph counts/digest, and classifications exactly.
5. Candidate/Term totals reconcile with attributed/unattributed/per-rule/per-clause/Term-variant counts; ambiguous rule IDs have no attribution. Access/work counters reconcile, have no dropped rows, and are empty in controls.
6. Discrete profiles and graph digests reproduce across two replicates within each cell. Timing and RSS remain descriptive.

## Analysis

Report all 12 cell values without pooling wall time with operation counts. Fit the four-term discrete model `y = β₀ + βP(P−3) + βD D + βPD(P−3)D` separately to candidate tests, Term evaluations, and selected access events; report all cell residuals. The interaction coefficient is descriptive over these finite tested points, not an asymptotic theorem. Scheduler/deferred counter units are separate and heterogeneous.

## Claim boundary

This is one authored full-seed route, one balanced known-class multiset, and one synthetic global distractor family. It measures selected route scaling only. It does not establish natural prevalence, learned cheap cuts, novel concept acquisition, complete operation cost, scoped-execution safety, or general capability.

## Reproduction

Use `PYTHONPATH=runners/dsl/python:.`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Generate the source lock using `scripts/substrate_live_describe_scene_percept_noise_factorial_v1.py --lock`, then run that script. The terminal worker check is derived from the 48 declared jobs. The runner refuses to overwrite locked outputs.
