# Seed Argmax memoization-eligibility census v1

**Question.** How many source-authored executable seed Argmax sites are structurally eligible for the current `cached_argmax_key` policy, and which term operators most often prevent memoization?

**Procedure.** Scan each JSON seed manifest, apply `engine_rules_only`, and inspect every `Argmax` in each executable rule's match, where, and effect terms. Classify its source, ranking value, and non-null default with the same recursive stable-term whitelist as `is_stable_graph_query` in `runners/dsl/src/term.rs`. Report sites and distinct affected seed/rule pairs, plus unsupported term types. Hash the runner, this protocol, seed loader, Rust Term evaluator, and every seed manifest before and after execution.

**Limits.** This is a static syntactic eligibility census. It does not establish that any site fires, that all free variables are bound on every runtime path, that caching produces a speedup, or that graph mutations leave a cache entry at a checkpoint boundary. The classifier mirrors the current whitelist and must be updated if that policy changes.

**Execution.** `python3 evaluation/substrate_capability/cache_argmax_eligibility_census_v1.py --lock` creates an immutable source lock; execute the same runner without arguments for the capture. Do not overwrite either artifact; create a new version for changed sources or procedure.
