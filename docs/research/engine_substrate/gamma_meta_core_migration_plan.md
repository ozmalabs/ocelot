# Γ_meta core migration plan — the last + hardest piece

The final CuriousAgent bench, `test_curious_agent` (18 tests), is the irreducible
self-growing substrate: Γ_dynamic grows from observing a chess world, gated by a
meta-grammar Γ_meta, with boundary relations, where-clause widening, supersede,
and gamma-as-a-view. This is "last by design." Frontier is now ONLY this + the
parity gate; everything else is migrated (654 migrated+parity green).

## KEY ARCHITECTURAL FINDING (de-risks the whole thing)

The Rust `substrate_rs` **already gates admissibility**: its checked `add_edge`
raises `InadmissibleEdge` ("Γ rejects: type … not in vocabulary"), and it exposes
`add_production` + `is_edge_admissible`. CuriousAgent's `mind_substrate` is a
PYTHON `Substrate` + `ConsistencyChecker(meta_grammar())`; the WorldAdapter does
NOT need a parallel Python substrate — the Γ_meta core runs on the agent's own
Rust substrate `self.s` (mind_substrate == self.s, gamma_root == a Grammar node
in self.s, agent_root == self.agent). The Γ-edits use the CHECKED `add_edge`
(gated), not `add_edge_unchecked`.

CAVEAT to resolve in slice A: confirm the exact Rust rejection semantics —
`meta_grammar()` is ~9.6k productions (the full epistemic layer); the Γ-evolution
SUBSET is what's needed (Grammar-production->Production, Production-pattern.src/
tgt->NodePattern, Production-pattern.where->Term.*, Agent-{senses,models,acts_on}
->BodyType). Verify that installing that subset as productions makes the good
edges admissible AND the test's bad edges (Grammar-production->NodePattern,
Agent-secret_relation->BodyType) raise InadmissibleEdge (vocabulary vs
production-triple gating — test it before relying on it).

## What the adapter ALREADY has (reusable)
`senses()` / `models_set()` / `acts_on_set()` (graph-query boundary) ·
`_ensure_body_type` · `quality_of_gamma` (variant — sums relation counts, not
triple counts) · `observe_structure` (triple counting) · `grow_structural_grammar`
(triple-threshold -> Pattern nodes) · `grow_gamma` (dispatcher -> discover_relations).

## What it MUST gain (per the Explore map of domains/curious_agent.py)
- module `meta_grammar()` subset + install onto self.s (gate Γ-edits);
- `gamma_root` (a Grammar node) + `gamma_dynamic` property (VIEW: rebuild
  `Grammar` from Production nodes off gamma_root, incl. pattern.src/tgt NodePattern
  + the `where` Term + edge_type/provenance attrs);
- `_append_production(Production) -> NodeID` — checked, Γ_meta-gated transaction;
- `_supersede_production(idx, Production)` — build new (gated) then detach old
  (orphan left in graph);
- `_term_to_mind(term)` — where-clause Term subgraph (reuse add_term_subgraph);
- `observe(world_substrate)` — tally `triple_counts` (Counter[(src,edge,tgt)]) +
  `attr_values` (dict[(type,attr)]->set) + n_observations++; write boundary edges;
- `grow_gamma()` two-phase — (1) triples >= threshold -> _append_production +
  _register_relation(models); (2) per-type attr WIDENING (where = In(Attr(Var,key),
  SetT(Lit…)) over the UNION of observed values) via _supersede;
- `quality_of_gamma` = sum of triple_counts for triples in Γ_dynamic (monotone);
- the chess world (domains/worlds.chess_world or shared_chess) + `live(n_games,
  max_plies, grow_every_game)` self-play -> observe -> grow loop; `interpret_acts_on`
  drives `acts_on` (Square sensed+modeled but NOT acted_on; pieces acted_on).

## Slices (each a migrated twin; test_curious_agent burns only after all)
- **A — Γ-as-graph + meta-grammar gating** (tests 1, 11, 12, 14, 15, 17):
  gamma_root + meta-grammar subset on self.s + gamma_dynamic view +
  _append_production + _supersede + _term_to_mind. No chess.
- **B — the grow engine** (tests 2, 4, 7, 9, 13, 16, 18): observe (triple_counts +
  attr_values) + grow_gamma two-phase (discovery + where-widening + supersede
  orphans) + quality monotone + boundary _register_relation(models) + the
  inadmissible-boundary gate (test 10).
- **C — the chess world** (tests 3, 5, 8): chess_world + live self-play ->
  discovers all 12 piece types + pawn rank invariants (rank 0/7 excluded) + the
  acts_on gradient (Square not acted_on). Plus test 6 (no-win AST scan — re-point
  it at the world/adapter module; keep the code outcome-free).

## Then the HULL BURN (momentous, irreversible — a deliberate step)
git rm domains/curious_agent.py + tests/test_curious_agent.py +
tests/test_migration_parity.py (the gate — nothing left to compare) + the capture
tooling (tools/capture_intent_rules.py, tools/capture_seed.py); retarget or retire
the 39 experiment scripts + domains/arc3_full_seed.py. This deletes ~13k lines +
the regression bench that gated the entire migration — confirm before doing it.
