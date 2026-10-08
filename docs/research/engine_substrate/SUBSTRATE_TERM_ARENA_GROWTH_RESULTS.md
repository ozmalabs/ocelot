# Reflected Term arena growth results

**Status:** ownership-aware graph cleanup reclaims reflected Term graph nodes but does not reclaim the Rust `TermArena` AST nodes used to create them.

## Measured lifecycle

A source-locked Rust evaluation ran 1,000 parses of the same four-node `Cat(Lit, Reverse(Var))` Term, reflected each into graph nodes, and cleaned each root. With ownership-aware cleanup, graph-node delta stayed 0 at 1/10/100/1,000 cycles, while `TermArena.len()` grew by 4/40/400/4,000. A root-only deletion control retained 3 graph nodes per cycle (+3,000 at 1,000) and showed the same arena growth. Thus graph ownership cleanup fixes graph retention but cannot bound arena growth under repeated parsing.

At 1,000 cycles, one run took 29.32 ms for ownership-aware cleanup and 20.73 ms for root-only deletion. This is descriptive and unreplicated; it does not establish a stable overhead estimate. Arena length measures live logical vector entries, not allocated capacity or RSS.

## Implications and limits

A follow-up source audit identified persistent TermIdx owners in grammar productions, ConceptResolver, and the TermIdx-keyed ShapeCache. Accordingly, rollback was limited to graph-materialization conversions whose TermIdx does not escape. The P4 follow-up confirms zero arena growth around two temporary evaluation helpers and 1/10/100 repeated IR materializations, while graph cleanup independently controls retained graph nodes ([P4 results](SUBSTRATE_P4_TERM_ARENA_RETENTION_RESULTS.md)). Truncation cannot be applied indiscriminately: shape_of_term and add_shape_node_for_term still retain cache entries keyed by their parsed TermIdx.

The probe uses one small fixed tree and Rust-level parse/reflect/remove operations. It does not model the complete P4 Python call path, term evaluation, rule/concept references, varied AST sizes, allocator/RSS effects, or any reclamation implementation. See [protocol](SUBSTRATE_TERM_ARENA_GROWTH_PREREG_20260925.md), [Rust harness](../../../runners/dsl/examples/term_arena_growth_probe.rs), [orchestrator](../../../scripts/substrate_term_arena_growth_probe.py), [lock](../../../evaluation/substrate_capability/term_arena_growth_lock_20260925.json), and [raw report](../../../evaluation/reports/substrate_term_arena_growth_20260925.json).
