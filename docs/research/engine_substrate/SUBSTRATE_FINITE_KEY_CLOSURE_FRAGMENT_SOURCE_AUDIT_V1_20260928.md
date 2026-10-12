# Finite-key closure fragment source audit v1

Date: 2026-09-28  
Evidence grade: source audit of the checked-in analyzer and native rule path; no runtime execution or theorem prover was used.  
Question: do the existing finite-key checker assumptions describe a real native sublanguage, and does the engine enforce admission to that sublanguage?

## Finding

The existing checker describes a defensible **finite-key insertion-only fragment**, but it is not weak acyclicity and it is not an engine-enforced restriction. It is a sufficient syntactic envelope over JSON rule specifications. The native rule loader accepts a materially broader language, and the checked-in checker is not called from the native rule-loading or closure entrypoints. Therefore no general termination guarantee currently follows for production rules merely because the checker accepts its input format.

## Fragment for which a finite-state argument works

For a fixed finite rule set and finite initial graph, the checker admits nonempty positive edge-pattern matches; its v0 implementation rejects every rule field except `name`, `match`, and `effects`. Its admitted mutations are:

1. `add_node_if_absent` with one literal node type and a fixed map of finite scalar JSON attributes (`null`, boolean, integer, or string); and
2. `add_edge` between variables already bound by the positive match or by an earlier admitted mint effect, with an empty edge-attribute map.

It refuses fresh `add_node`, computed key values, conditions, attribute writes, deletions, and other effect forms. The initial node-ID list and edge-fact list must be complete, endpoint-closed, and duplicate-free. These restrictions give the graph a finite universe of possible node signatures and typed endpoint pairs.

Let `N₀` be the initial node count, `S` the number of unique admitted `(type, literal key map)` mint signatures, `T` the number of initial or rule-added edge types, and `M₀` the number of initial edge facts. A coarse upper bound on graph facts is `N* = N₀ + S`, `E* = T · (N*)²`, and `P* = S + E* − M₀`.

Each progressing pass must insert at least one previously absent node signature or one previously absent, empty-attribute typed edge. Thus there are at most `P*` progressing passes before a no-progress pass. With a fixed rule set and fixed maximum match-pattern size, ordinary positive matching and the finite-key existence scan have polynomial data complexity in graph size, although the exponent and constants can be poor. This is a finite-universe argument, not a weak-acyclicity proof. It does not by itself bound wall time when patterns/rules grow with the input, external callbacks run, or system resources are capped.

## Source crosswalk

| Claim | Current source evidence | Consequence |
|---|---|---|
| The checker admits a narrow insertion-only finite-key syntax and computes a coarse fact/progress bound. | [`analyze_mint_termination_fragment.py`](../../../scripts/analyze_mint_termination_fragment.py), especially `analyze`; prior finite-key checker results ([v1.1](SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_RESULTS_20260926.md), [generated grammar v1.2](SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_2_RESULTS_20260926.md)). | Useful design envelope, but prior evidence covers selected fixtures and generated combinations only. |
| Native `AddNodeIfAbsent` deduplication is type plus subset-attribute comparison; a hit reuses the first matching node and makes no graph progress. | [`rewrite.rs`](../../../runners/dsl/src/rewrite.rs#L115) documents the semantics; the implementation resolves arguments, scans typed nodes, compares every key/value pair, and inserts only on a miss ([implementation](../../../runners/dsl/src/rewrite.rs#L2294)). | A fixed literal signature can create at most one new witness node. Two distinct signatures can overlap under subset semantics, so the checker’s count is an upper bound, not an exact mint count. |
| Native edge insertion is not always a monotone fact insertion. | `AddEdge` replaces attributes when a typed edge already exists ([implementation](../../../runners/dsl/src/rewrite.rs#L1861)); the checker therefore rejects edge types with attributed initial edges and only admits empty attributes. | The analyzer’s edge-type guard is necessary for its insertion-only argument. Any broader fragment must model edge replacement and attribute domains explicitly. |
| The rule loader accepts computed effect arguments and general parsed `where` Terms. | [`graph_rules.rs`](../../../runners/dsl/src/graph_rules.rs#L137) parses `where`; [`parse_effect_arg`](../../../runners/dsl/src/graph_rules.rs#L160) accepts a `__term__` wrapper; [`parse_attrs_dict`](../../../runners/dsl/src/graph_rules.rs#L181) permits computed values in effect attributes. | Runtime syntax is broader than the finite-key checker’s literal-only fragment. |
| The ordinary Python authoring and checkpoint-import paths parse rules, then call `Substrate::add_rule`, without invoking the finite-key checker. | [`PySubstrate.add_rule`](../../../runners/dsl/src/py.rs#L3456) calls `parse_rule_json` then `inner.add_rule`; [`import_rules`](../../../runners/dsl/src/py.rs#L5248) parses every rule then installs them with `inner.add_rule`; [`parse_rule_json`](../../../runners/dsl/src/py.rs#L9719) accepts general `where`, `effects`, and scheduling/metadata fields. `Substrate::add_rule` derives indices/access metadata but has no fragment-admission step ([implementation](../../../runners/dsl/src/substrate.rs#L2974)). | Both new authoring and restored rule stores can contain rules outside the finite-key fragment. |
| Graph-resident rule compilation and self-minting also install without finite-key admission. | [`run_graph_rules_opts`](../../../runners/dsl/src/graph_rules.rs#L455) parses `Rule` nodes through `rule_from_node`; the self-build queue also calls `rule_from_node` followed by `add_rule` ([implementation](../../../runners/dsl/src/substrate.rs#L3944)). | Graph-authored/self-minted rules form additional admission surfaces. |
| Revision paths validate patch shape and revision/hash consistency, but not finite-key membership. | [`stage_rule_patch`](../../../runners/dsl/src/substrate.rs#L2784) parses replacement `where` Terms or effects and recomputes access; `apply_rule_patch` commits after CAS checks ([implementation](../../../runners/dsl/src/substrate.rs#L2952)). The legacy `SetRuleClause` path reaches the same patch API ([implementation](../../../runners/dsl/src/substrate.rs#L3990)). | CAS protects against stale edits; it does not preserve the finite-key termination restriction after a valid revision. |
| The standalone checker has no production callsite in the audited checkout. | Scoped repository search for `analyze_mint_termination_fragment`, `mint_termination_fragment`, and `progress_steps_upper_bound` finds imports in evaluation scripts/tests, while native loader/install callsites route through `parse_rule_json`, `rule_from_node`, `add_rule`, and patch APIs. | This is a source-callsite audit, not proof against dynamic/reflection-based calls; the direct native pathways above already establish that admission is not mandatory. |
| A syntactically positive rule may still contain external reads or callbacks through `where`/computed Terms. | `UseTool` dispatches to a Python callback ([`term.rs`](../../../runners/dsl/src/term.rs#L6904)); `ReadFile` accesses host filesystem state ([implementation](../../../runners/dsl/src/term.rs#L7007)). | A general fixed-point semantics needs a purity/snapshot contract or an explicit external-state version; this audit's fragment excludes `where` and computed Terms. |
| The closure progress budget is not a strict effect-level cancellation bound. | `run_rules_opts_with_audit_ids` checks its pass loop and increments progress within rule processing ([`rewrite.rs`](../../../runners/dsl/src/rewrite.rs#L2865)); see [progress-budget results](SUBSTRATE_RULE_RUN_PROGRESS_BUDGET_OVERSHOOT_V1_1_RESULTS_20260928.md). | The finite-state bound is about total graph-changing progress, not the `max_steps` argument as a strict per-pass work cap. |

## Scope limits and next gate

This audit supports the finite-universe proof sketch only under the fragment above. The checker is not a weak-acyclicity analysis: its central guarantee comes from constant finite dedup signatures and insertion-only finite edge relations. Nor is its bound a cost guarantee for variable-size patterns; general subgraph matching remains hard when the pattern is part of the input.

The next result should either (a) keep this deliberately narrow fragment and integrate fail-closed admission at every native rule install/load/revision boundary, or (b) design a larger, formally specified existential-rule fragment with an actual weak-acyclicity/rank checker. In either branch, verify accepted and rejected programs through the production parser, exercise rule revision/restart paths, and independently check the final graph and termination status. Until then, report termination for arbitrary production rules as unproved.

**Runtime route confirmation (2026-09-28):** the source-level gap was exercised in three fresh workers. The checker refused a fresh-`add_node` rule in all workers, while direct authoring, checkpoint import, revision/hash-CAS patching, and explicit graph-rule self-mint each accepted it in 3/3. The self-minted rule was installed but not executed because its match edge was absent. This confirms the exact route-level admission gap without making a termination claim; see [v1.1 results](SUBSTRATE_MINT_FRAGMENT_ADMISSION_PATH_PROBE_V1_1_RESULTS_20260928.md), [raw capture](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_20260928.json), and [independent analysis](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_analysis_20260928.json). V1's cycle-plan fixture failure and the unscored setup pilot are preserved and disclosed in the amendment.

## Reproducibility note

This is an offline source review. Source file SHA-256 values at review time:

- `runners/dsl/src/graph_rules.rs`: `b0e9c5bf0bbb4bf278fdab03610fa3f6f82d01ad8ee898ec789982ff41812a50`
- `runners/dsl/src/rewrite.rs`: `58cea7eaa595c804f4f0265c4003231105011dc2493bea8ca30dea6bb6246c34`
- `runners/dsl/src/term.rs`: `0b91be836a6a7fe4587fb2ec3a944fdd6fb461838ca25151b1358c2158705fce`
- `scripts/analyze_mint_termination_fragment.py`: hash should be refreshed when this review is converted into a locked executable audit; no code was changed in this source review.
