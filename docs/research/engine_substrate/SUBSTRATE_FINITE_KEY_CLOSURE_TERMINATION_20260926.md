# Restricted closure termination: finite-key monotone insertion fragment

## Result

For the rule fragment admitted by `scripts/analyze_mint_termination_fragment.py`, closure terminates on a fixed finite initial graph, provided the closure call is not interleaved with external graph mutation. This is a finite-universe argument; it is **not** weak acyclicity, a chase theorem for arbitrary existential rules, or a claim about unrestricted Ocelot rules.

The fragment allows only:

- rules with nonempty positive graph-edge triple matches and no extra clauses/conditions;
- `add_node_if_absent` with fixed node type and finite scalar literal attributes (no computed/fresh key values);
- `add_edge` between already-bound or earlier-minted variables, with empty attributes;
- no node deletion, edge deletion, attribute mutation, arbitrary node creation, external predicate, or unsupported rule/effect fields.

The initial node inventory and initial edge facts must be complete and well-formed. Any edge type with existing attributed edges cannot be rewritten through this fragment. The analyzer rejects malformed inventories and unsupported effects instead of assuming termination.

## Bound

Let `N` be the initial node count, `M` the number of syntactically distinct admitted literal mint signatures, and `E` the number of edge types appearing initially or in admitted rules. Runtime equality or subset-key matching may coalesce signatures (for example `Bool(true)` and `Int(1)` compare equal by design), so M is an upper bound on newly minted nodes, not necessarily an exact count. Then at most `N' = N+M` nodes can ever exist. Since edges have finite directed endpoint/type keys and no attributes are changed, there are at most `E(N')²` distinct edge facts. If `e₀` initial edge facts exist, the number of possible newly inserted graph facts is bounded by

`B = M + E(N+M)² − e₀`.

Every progressing firing must insert at least one previously absent node or edge fact. No insertion is later removed. Therefore there can be at most `B` progressing firings. Under the engine's dirty-rule pass scheduler, there are at most `B` progressing passes followed by one no-progress pass before `fixed_point`; the runtime budget must be at least B to observe the full closure rather than an explicit budget exit. This is a loose bound, not a prediction of typical rounds.

For fixed rules, every match has a fixed number `v` of node variables and ranges over a finite graph, so positive triple matching per pass is polynomial in N (a coarse enumeration bound is `O(N^v)`). The finite progress bound is polynomial in N for fixed M/E. Thus closure work for this fragment is polynomial in the initial graph size under fixed-rule data complexity, with the exponent depending on the rule variable count and implementation/index costs. No uniform polynomial in program size is claimed.

## Assumptions requiring care

1. `add_node_if_absent` compares the authored literal attrs as a subset of an existing same-type node's attrs. Once a node satisfying the authored signature exists, that signature cannot mint another node. The native source documents this subset behavior in `runners/dsl/src/rewrite.rs`.
2. Each admitted edge insertion has empty attrs. This excludes attribute replacement and makes the edge fact universe finite over endpoint/type triples.
3. Matching is positive and graph-only. No negation, host callback, mutable external sensor, computed term, or rule patch can create a nonmonotone dependency.
4. The proof is about one closure invocation against a stable substrate. Repeated external events can make the overall system run indefinitely while each closure call terminates.
5. The static analyzer's acceptance is a syntactic sufficient condition. Rejected rules may still terminate; the analyzer makes no converse claim.

## Executed evidence

On 2026-09-26, `python3 scripts/analyze_mint_termination_fragment.py --self-check` passed its accepted/rejected syntax fixtures. `scripts/verify_mint_termination_fragment_native.py` then loaded the admitted recursive finite-key rule through the native loader/scheduler. Its complete logical initial graph had N=2, M=1, E=1, e₀=1, giving B=9. After the trigger mutation, native closure reported `fixed_point`, 2 progressing rule firings, 3 completed passes, and the exact expected three-node/three-edge graph; all six native verifier checks passed. Raw provenance is in [self-check capture](../../../evaluation/reports/mint_termination_fragment_selfcheck_20260926.json) and [native capture](../../../evaluation/reports/mint_termination_fragment_native_20260926.json). The capture is one rule/one fixture and validates the bound's application, not every accepted rule program.

**Multi-rule native extension (same date):** an additional 18-cell run crosses one/two/four distinct literal mint signatures with a sparse cycle and a dense directed no-self-loop initial graph, with three repeated substrate constructions per cell. The production classifier accepts all 18; independently recomputed graph fact bounds and exact terminal nodes/edges pass in all 18; native reports fixed point and stay below the bound. For N=4, E=1, observed bounds are 22/34/64 on the cycle and 14/26/56 on the dense graph for M=1/2/4; the engine takes three passes in every cell, with observed progress steps 2/4/8 respectively. See [runner](../../../scripts/verify_mint_termination_families_v1.py), [independent analyzer](../../../scripts/analyze_mint_termination_families_v1.py), [raw](../../../evaluation/reports/mint_termination_families_v1_20260926.json), and [analysis](../../../evaluation/reports/mint_termination_families_v1_analysis_20260926.json). This strengthens finite-rule-family validation but remains synthetic, all-positive, and one initial-node scale; larger N and broader admitted program shapes are still required.

**Scale and key-equality extension (same date):** the 54-case v1.1 matrix adds N=4/16/64 and preserves the initial v1 failures where an exact-node oracle incorrectly assumed `true` and `1` mint separately. Source confirms native equality intentionally coalesces them; v1.1 computes the expected three runtime witnesses for four authored signatures and retains the analyzer's larger syntactic M in its safe bound. All 54 amended graphs/status/bound checks pass. See [scale results](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_1_RESULTS_20260926.md), [raw](../../../evaluation/reports/mint_termination_scale_v1_1_20260926.json), and [independent analysis](../../../evaluation/reports/mint_termination_scale_v1_1_analysis_20260926.json). This validates the same one-schema fragment through N=64; it does not broaden to all analyzer-admitted rule programs.

## Claim boundary and next strengthening

A locked generated grammar panel exercises 15 admitted and 10 refused forms; each accepted native closure matches an independent interpreter and stays under the finite-fact bound. An initial self-loop discrepancy was traced to the oracle omitting the runtime's injective-variable rule, corrected in v1.2, with no engine change retained. See [v1.2 results](SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_2_RESULTS_20260926.md) and [analysis](../../../evaluation/reports/mint_termination_generated_grammar_v1_2_analysis_20260926.json).

The source crosswalk now maps every currently admitted rule/effect wire form to `parse_rule_json` and `parse_effect_json`, and documents the runtime's permissive forms intentionally rejected by the analyzer. It finds no source-level syntax mismatch within the checker-accepted subset, but this remains a source audit plus finite executed fixtures, not exhaustive grammar equivalence; see [parser/admission crosswalk](SUBSTRATE_FINITE_KEY_RUNTIME_PARSER_CROSSWALK_20260926.md).

This result supplies restricted closure-termination content for the tractability report: the finite-key monotone fragment terminates with a polynomial graph-fact/progress bound for fixed rules. It does not establish a polynomial wall-time guarantee for the full engine, unrestricted minting, or weakly acyclic rule behavior. Before treating the checker as a trusted admission gate, extend independent analyzer fixtures to multiple mint signatures, several recursive rules, adversarial initial graphs, and pair every accepted family with a native fixed-point/progress oracle; separately validate all runtime rule forms against the analyzer's admitted syntax.


**Checker input hardening (2026-09-26):** source review found empty non-list top-level `rule_specs` and `initial_edges` containers could be treated as empty collections and accepted. The analyzer now rejects non-list inputs explicitly. A locked v1.1 probe passes all 15 checker fixtures, confirms the positive rule remains admitted and native-loadable, and verifies exact fixed-point state plus all 11 independent provenance/runtime checks ([results](SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_RESULTS_20260926.md), [protocol](SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_PROTOCOL_20260926.md), [analysis](../../../evaluation/reports/mint_termination_checker_hardening_v1_1_analysis_20260926.json)). This closes only a top-level input validation gap; accepted-syntax/runtime equivalence remains unproven.
