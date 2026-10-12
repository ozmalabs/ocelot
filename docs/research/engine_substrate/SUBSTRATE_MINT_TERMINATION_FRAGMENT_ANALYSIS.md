# Finite-key monotone mint fragment: static bound and current limits

**Status:** conservative design analysis and executable syntactic checker; not a reviewed theorem about the complete engine.  
**Checker:** [`analyze_mint_termination_fragment.py`](../../../scripts/analyze_mint_termination_fragment.py)  
**Classifier fixture output:** [`mint_termination_fragment_self_check_20260925.json`](../../../evaluation/reports/mint_termination_fragment_self_check_20260925.json)  
**Runtime probe:** [`SUBSTRATE_MINT_TERMINATION_ENVELOPE_RESULTS.md`](SUBSTRATE_MINT_TERMINATION_ENVELOPE_RESULTS.md)

**Native loader/scheduler probe:** [`verify_mint_termination_fragment_native.py`](../../../scripts/verify_mint_termination_fragment_native.py), [raw report](../../../evaluation/reports/mint_termination_fragment_native_20260925.json)

**Interacting rule probe:** [`SUBSTRATE_MINT_INTERACTING_RULES_RESULTS.md`](SUBSTRATE_MINT_INTERACTING_RULES_RESULTS.md), [raw report](../../../evaluation/reports/substrate_mint_interacting_rules_20260925.json)

## Accepted fragment v0

The checker admits only rules with a nonempty body of positive edge triples over bound variables and effects, in order, from:

1. `add_node_if_absent(new_var, literal_node_type, literal_scalar_attrs)`, where `new_var` is new in that rule binding; and
2. `add_edge(bound_or_previously_minted_src, literal_edge_type, bound_or_previously_minted_tgt, {})`.

All other match forms and effects are rejected. In particular, plain `add_node`, computed or structured dedup keys, attribute writes, deletes, replacements, and edge attributes are outside this fragment. These restrictions are intentionally narrower than the engine API.

## Finite-universe bound

Let `N` be the initial number of nodes, `R` the number of distinct `(node type, literal key map)` mint signatures across the fixed rule set, `E` the number of distinct initial or rule-produced edge types, and `M` the number of initial directed edge triples. `AddNodeIfAbsent` can insert at most one node for each signature, so at most `N+R` nodes can ever exist. Empty-attribute edge insertion can add at most one fact for each ordered node pair and edge type, so at most `E(N+R)^2` edge triples can exist. Therefore the number of graph fact insertions—and hence progressing rule applications—is at most:

`R + E(N+R)^2 - M`.

For a fixed rule set (`R` and `E` constants), this is `O(N²)`. This is a coarse upper bound; it says nothing about the cost of enumerating matches, which can be much larger per insertion, or about a hard wall-time bound. The argument depends on insertion-only monotonicity and finite literal keys; allowing generated values, deletion, or replacement invalidates this finite-state potential argument.

The bound proves finite progress in the abstract graph rewrite relation. It does **not by itself prove** that the production scheduler observes every newly enabled match, that a `fixed_point` report equals the intended logical least fixed point, or that matching/run time is polynomial. Those require separate scheduling/access-recall and complexity results. Thus this is not a weak-acyclicity analyzer and is not yet a closure-termination theorem for A1.

## Finite-progress proposition for fragment v0

**Proposition (bounded progress).** Fix a finite rule set admitted by the checker,
and a finite initial graph whose complete node-ID inventory, edge facts, and
edge attributes are supplied to it. Assume one graph owner mutates the graph
during a closure run. Let `B = R + E(N+R)^2 - M` as above. Under the native
effect semantics described below, the abstract rewrite process can perform at
most `B` progressing rule applications.

**Argument.** Each `AddNodeIfAbsent` signature can create at most one node:
when no node of its type contains the fixed literal key map, the first firing
inserts one with exactly that map; subsequent firings bind the existing node.
Subset-key reuse can suppress an insertion sooner, but cannot add another
node for the same signature. Thus the graph contains at most `N+R` nodes. The
only other allowed effect adds an empty-attribute edge triple. The graph is a
simple directed typed graph, so for `E` edge types there are at most
`E(N+R)^2` triples. The analyzer rejects any effect edge type that has an
attributed initial edge, because native `AddEdge` replaces attributes on an
existing triple. Attributed initial edges with unrelated types remain fixed;
on every effect edge type, the operation either inserts an empty-attribute
triple or repeats an identical no-op. Thus an allowed effect either adds a
previously absent node or edge fact, or makes no graph change. Since the fragment has no delete,
replacement, computed key, condition, attribute-write, or external effect,
every progressed application consumes at least one of the at most
`R + E(N+R)^2 - M` initially absent facts. No fact can be consumed twice, so
the progress bound follows.

This proposition is about **progress count**, not a claim that the Rust
scheduler discovers every enabled match. For a full native sweep, a finite
graph and finite positive patterns imply finitely many candidate bindings per
rule, so each completed sweep is finite; if the runner completes sweeps, no
more than `B` progress-bearing sweeps plus a terminal no-progress sweep are
needed. The proposition does not establish that a reported `fixed_point` is
the least closure, that dirty/access scheduling is complete, or that time per
candidate is small. Those remain independent Stage 1 correctness and Stage 2
tractability obligations.

## Checker validation performed

The self-check accepts the recursively triggered finite-key fixture and rejects the paired unrestricted fresh-node rule, a computed-key case, an attribute replacement case, and a rule with an unsupported condition clause. A source audit found the binding census also included the match triple's middle edge-label string as if it were a bound node variable. The checker now binds only the source and target positions; a held negative contrast confirms an effect endpoint named `link` is rejected when `link` appears only as the matched edge type. A second audit found that the engine's `AddEdge` overwrites attributes when the triple already exists: an allowed empty-attribute effect can therefore mutate a nonempty initial edge instead of inserting a fact. The analyzer now accepts optional initial-edge attribute maps and rejects any admitted `AddEdge` type that could collide with such a pre-existing attributed edge. A native regression confirms that this case reaches `fixed_point` in one progress step with the same edge count, demonstrating the state-changing collision the static fragment must exclude. The analyzer now takes the complete initial node-ID inventory rather than a claimed node count; it rejects duplicate IDs, omitted edge endpoints, malformed or duplicate edge facts, and its bound includes isolated nodes. Ten self-check fixtures and five tests pass, including a control showing that adding an isolated initial node increases the derived bound. The original finite-key runtime probe still observes two steps in each bounded case, within its static bounds; the unrestricted control remains capped and correctly rejected by the checker.

This validates the checker against five hand-authored syntax fixtures and one small measured rule family only. The single-case native check below establishes an initial schema/access parity point; before using the checker as a construction-time guard, broaden parity coverage, add counterexamples for every rejected effect family, and prove/check variable binding and access-dependency coverage end to end.

## Native path check

The admitted recursive fixture was loaded through PyO3 `Substrate.add_rule`. Its native `rule_access_sets` output exactly matched the declared edge/type reads and edge/type/attribute writes. The rule was initially run on an empty graph, then enabled by inserting a matching edge after installation; the subsequent typed report reached `fixed_point` in two progress steps and the final graph matched the exact three-node/three-edge oracle, within the static bound. A fresh 2026-09-26 replay using explicit initial node IDs passes all six loader/scheduler checks; the two interacting cascade/feedback closures also pass current classifier bounds and independent positive-closure oracles. See [current native report](../../../evaluation/reports/mint_termination_fragment_native_20260926.json) and [current interacting-rule report](../../../evaluation/reports/substrate_mint_interacting_rules_20260926.json).

A follow-up loaded two interacting rule sets through the same native path. A cascade with two mint signatures and three rules, plus a feedback cycle that re-enabled an earlier rule, both reached `fixed_point` and matched all expected edges and node-type counts from an independent positive-closure evaluator. Native reported progress steps 3 and 2 against bounds 100 and 31. The oracle counts effectful binding applications separately, so its counts (4 each) are not interpreted as parity with the engine's progress unit. See the linked results. These cases extend coverage but still do not prove scheduler completeness for all rule sets, all write/read dependencies, imports, or rewrites.
