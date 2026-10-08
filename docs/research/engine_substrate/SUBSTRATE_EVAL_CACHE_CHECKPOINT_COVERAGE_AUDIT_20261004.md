# EvalCache checkpoint coverage audit — 2026-10-04

## Scope and evidence

This is a source audit of the six `EvalCache` maps declared in [`term.rs`](../../../runners/dsl/src/term.rs), their invalidation path, and native scheduler checkpoint behavior in [`py.rs`](../../../runners/dsl/src/py.rs). Dynamic evidence includes the source-locked primary routes in [closure-entry replay v7](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V7_RESULTS_20261004.md) and [v8](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V8_RESULTS_20261004.md). It does not establish complete checkpoint coverage for every cache family or workload.

| Cache family | Key and value shape | Invalidation | Checkpoint status |
|---|---|---|---|
| `reachable` | start node, edge symbol, any-type flag → result plus inspected-node footprint | graph-dependent clear; counters/payload telemetry retained | Occupancy/configuration/telemetry recorded; entries not serialized |
| `neighbours` | node, edge symbol, direction → frozen set of values | traversal clear | Entries serialized/restored; primary-route full-checkpoint parity passed |
| `filter` | term index, free-variable bindings → set value | traversal clear | Entries serialized/restored; primary-route full-checkpoint parity passed |
| `argmax` | term index, free-variable bindings → winner value | traversal clear | Schema V6 direct codec and evaluator-generated two-binding replay pass |
| `holds` | concept symbol and optional node arguments → value | traversal clear on substrate mutation, with graph-dependent clear at the next rule-pass boundary | Schema V6 direct codec and evaluator-generated two-node/multi-binding replay pass; stale value does not affect the post-mutation pass |
| `sd_ops` | tagged operation key with values, scalars, typed fingerprints → report value | graph-dependent clear | Occupancy only; entries not serialized |

The shared clear path is `clear_traversal` / `clear_graph_dependent` in [`term.rs`](../../../runners/dsl/src/term.rs); substrate mutation sites call the latter (see [`substrate.rs`](../../../runners/dsl/src/substrate.rs)). The checkpoint implementation emits entry counts for all six families and serializes neighbour, filter, argmax, and holds payloads. Restore rejects any nonempty reachable or SD-operation cache. This is an explicit, conservative boundary rather than silent cache loss.

## Dynamic evidence

The V7/V8 route captures observed neighbour occupancy up to 73 and filter occupancy of 6 in several states; the other families remained empty there. V8 replay under schema V6 passes full scheduler-checkpoint equality and independent counter analysis for 15 call-entry states and 13,376/13,376 per-rule metric cells. This dynamically supports nonempty neighbour/filter entries on the captured route. The direct source-locked [codec probe v1.1](SUBSTRATE_SCHEDULER_CACHE_CODEC_V1_1_RESULTS_20261004.md) covers representative wire forms. The confirmatory [live argmax/holds V2.5 fixture](SUBSTRATE_SCHEDULER_CACHE_LIVE_ARGMAX_HOLDS_V2_5_RESULTS_20261004.md) naturally populates two outer Argmax keys and two-node Holds keys, checks exact restored work, and verifies pass-boundary invalidation prevents a stale Holds value from refiring an effect. Reachable/SD-operation entries remain unsupported.

### Source-authored vision Argmax diagnostic

A focused exploratory run loaded `vision_growth`, ingested four one-patch images, and invoked the installed Rust `run_rules` path. It produced 13 rule applications and four `term_eval:Argmax` evaluations, confirming that the source-authored `vg_learn_kernel_oja` rule reaches Argmax. The final checkpoint nevertheless had zero Argmax entries. Source inspection explains why this is not evidence of a checkpoint defect: `cached_argmax_key` only memoizes a restricted stable graph-query subset, and the vision rule's ranking expression contains `Dot`, which `is_stable_graph_query` does not admit. Successful Oja applications also write kernel weights and a patch marker, while substrate mutations clear graph-dependent cache entries. The run therefore does not create a nonempty Argmax checkpoint at a quiescent boundary. This is exploratory diagnosis on synthetic patches, not a locked transfer result or a natural-image evaluation. A valid transfer gate must either exercise an existing source rule whose Argmax expression is cache-eligible, or deliberately broaden the stable-query subset and prove mutation, output, and replay parity before claiming coverage.

The source-locked [eligibility census](SUBSTRATE_ARGMAX_ELIGIBILITY_CENSUS_V1_RESULTS_20261004.md) narrows the candidate search: 204/327 seed Argmax sites are structurally eligible under today's whitelist, spanning 52 seed/rule pairs. `vision_eye.ph0_wunit_winner` is one eligible source-authored candidate; static eligibility does not prove runtime cache occupancy.

The source-locked [vision-eye replay](SUBSTRATE_SCHEDULER_CACHE_VISION_EYE_ARGMAX_V1_RESULTS_20261004.md) closes this first source-authored transfer gate. Four fixed-patch phase-0 steps reach the production seed rule and leave one evaluator-generated Argmax entry. Two restores match the captured checkpoint, and subsequent dirty no-op closure matches aggregate/per-rule work, graph, and scheduler state exactly. This establishes a narrow source-rule cache replay, not speedup or natural workload prevalence. The separate `vision_growth` diagnostic remains ineligible because its ranking term uses `Dot`.

The follow-on [WUnit scale panel](SUBSTRATE_VISION_EYE_WUNIT_SCALE_V1_RESULTS_20261004.md) measures the same source family at 4/16/64/256 units. Candidate and Term work grow about 51×/49× for a 64× population increase, and median closure latency grows about 42×. This is bounded one-host scaling evidence; construction/input costs and cache-disabled comparison are outside scope.

## Next gates

1. Expand evaluator-generated argmax/holds coverage to heterogeneous binding values, both optional-node combinations, and repeated mutations; compare cold/warm work and output. V2.5 covers two outer bindings, two-node Holds, and one mutation but is still a tiny fixture. For source-authored transfer, first classify Argmax ranking expressions by memoization eligibility: the live vision-growth WTA expression is reached but currently ineligible because it uses `Dot`.
2. Serialize `reachable` entries only after validating that every footprint node and result value can be restored against the target graph; assert retained-payload and hit/miss telemetry parity.
3. Decide whether `sd_ops` is durable checkpoint state or a safely recomputable cache. If recomputed, prove that checkpoint restore invalidates it before any dependent work and measure the resulting cost.
4. Repeat dynamic transfer on independent workload families with nonempty caches; keep cache family, entry count, bytes, restore time, and exact downstream work as separate metrics.

A passing cache round-trip gate establishes replay fidelity, not tractability, natural frequency, or scaling. The separate structural and learning gates in the [measurement plan](SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md) remain necessary.

The source-locked [executable seed census](SUBSTRATE_CACHE_OPERATOR_SEED_CENSUS_V1_RESULTS_20261004.md) finds Argmax and Holds in disjoint authored rules: 327 Argmax occurrences in 126 rules versus 33 Holds occurrences in 10 rules, with no rule containing both. Runtime transfer should therefore exercise them in separate representative rules or subsystems, not require a single rule to co-populate both cache families.
