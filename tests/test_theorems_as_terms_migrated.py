"""theorems as Term-trees + theorem discovery, migrated — runs the SEEDED theorem
faculty (tau-3) AND the theorem-discovery faculty on the seed-booted agent via
boot_core + the theorem_core seed, with NO CuriousAgent.

Two halves, mirroring tests/test_theorems_as_terms.py:

1. **Theorems as Term-trees** — each seeded Theorem node carries a predicate Term
   subgraph (a `predicate` edge to a Term.* root), asserted by the agent, and the
   predicate evaluates through the DSL (EvalSubgraph), not Python branching.

2. **Theorem discovery** — across a chess `live_examined` run the agent tracks
   stable invariants in its own boundary structure (senses/models/acts_on
   cardinalities) and promotes those that hold for the SEEDED `theorem_hold_threshold`
   to fresh `thm_*` Theorem nodes — same graph shape as the seeded ones (predicate
   Term subgraph + asserts edge), with `discovered_from` provenance, and they accrue
   `check_count` on subsequent checks. The candidate predicates are graph-resident
   DSL Term-trees the substrate evaluates; the adapter only counts holds + reifies.
"""
from __future__ import annotations

from substrate.boot_core import boot_core
from substrate.world_adapter import WorldAdapter


def _booted():
    s, ag = boot_core()
    return s, ag, s._inner


# --- Theorems as Term-trees -------------------------------------------------


def test_every_theorem_has_a_predicate_term():
    """Each seeded Theorem node has a `predicate` edge to a Term.* subgraph
    (mirrors test_every_theorem_has_a_predicate_term_in_mind_graph)."""
    s, ag, inner = _booted()
    theorems = [n for n in s.nodes() if s.node(n)["type"] == "Theorem"]
    assert len(theorems) >= 3
    for t in theorems:
        preds = inner.neighbours(t, "predicate")
        assert len(preds) == 1, f"{s.node(t)['attrs'].get('name')} needs 1 predicate"
        assert s.node(preds[0])["type"].startswith("Term.")


def test_theorems_asserted_by_agent():
    """The Theorem -> predicate -> Term.* graph was admitted by Γ_meta (construction
    succeeded) and the theorems are asserted by the agent. Mirrors
    test_predicate_terms_admitted_by_meta_gamma: the seeded theorems exist and are
    wired by `asserts`, proving the meta-grammar admitted those edges."""
    s, ag, inner = _booted()
    asserted = inner.neighbours(ag, "asserts")
    assert len(asserted) >= 3
    assert {s.node(n)["type"] for n in asserted} == {"Theorem"}
    names = {s.node(n)["attrs"]["name"] for n in asserted}
    assert {"sensed_implies_modeled", "quality_monotone_non_decreasing",
            "discovery_converges"} <= names


def test_theorem_predicate_evaluates_through_dsl():
    """A theorem's predicate Term is graph data the DSL evaluates — read it via
    EvalSubgraph. sensed_implies_modeled = |senses − models| ≤ 2; on the freshly
    booted agent (no senses/models) the difference is 0 ≤ 2 → True. Mirrors
    test_theorem_evaluation_runs_through_dsl (the predicate is a real Term tree)."""
    s, ag, inner = _booted()
    theorem = next(n for n in s.nodes()
                   if s.node(n)["type"] == "Theorem"
                   and s.node(n)["attrs"]["name"] == "sensed_implies_modeled")
    term = {"type": "EvalSubgraph", "node": {"type": "Pick", "source": {
        "type": "Neighbours", "node": {"type": "Var", "name": "t"},
        "edge_type": "predicate"}}}
    held = inner.evaluate(term, {"t": theorem, "agent": ag, "self": ag})
    assert bool(held) is True


# --- Theorem discovery ------------------------------------------------------


def _lived(n_games=5, max_plies=20):
    """A WorldAdapter that has lived a chess run with boundary edges registered
    and per-game theorem discovery — the graph-native analogue of
    CuriousAgent.live(world=chess_world(), ...). The seeded boundary asymmetry
    (senses ≥ models, senses ≥ acts_on) makes the bootstrap invariants hold across
    games, so they promote to thm_* theorems."""
    from domains.worlds import chess_world
    wa = WorldAdapter()
    wa.live_examined(world=chess_world(), n_games=n_games, max_plies=max_plies,
                     grow_every_game=1)
    return wa


def _discovered(wa):
    return [t for t in wa._theorem_nodes()
            if wa.s.node(t)["attrs"].get("name", "").startswith("thm_")]


def test_theorem_discovery_finds_invariants():
    """After enough life the agent discovers ≥1 stable invariant and promotes it
    to a new thm_* Theorem node (mirrors test_theorem_discovery_finds_invariants)."""
    wa = _lived()
    discovered = _discovered(wa)
    names = [wa.s.node(t)["attrs"].get("name") for t in wa._theorem_nodes()]
    assert len(discovered) > 0, f"agent should have discovered ≥1 theorem; got {names}"


def test_discovered_theorem_has_term_tree_predicate():
    """Discovered theorems have the same shape as seeded ones — a Term-tree
    predicate attached via a `predicate` edge (mirrors
    test_discovered_theorem_has_term_tree_predicate)."""
    wa = _lived()
    discovered = _discovered(wa)
    assert discovered  # precondition; covered by previous test
    for t in discovered:
        preds = wa.inner.neighbours(t, "predicate")
        assert len(preds) == 1
        assert wa.s.node(preds[0])["type"].startswith("Term.")


def test_discovered_theorems_record_provenance():
    """Each discovered theorem stores `discovered_from` — the candidate pattern
    name that yielded it. The agent can trace back the source of its own knowledge.
    Mirrors test_discovered_theorems_record_provenance."""
    wa = _lived()
    discovered = _discovered(wa)
    bootstrap_names = {"senses_ge_models", "senses_ge_acts_on", "models_ge_acts_on"}
    for t in discovered:
        a = wa.s.node(t)["attrs"]
        assert "discovered_from" in a
        prov = a["discovered_from"]
        assert prov in bootstrap_names or prov.startswith("cand_"), (
            f"discovered_from should be a bootstrap name or cand_*; got {prov}")


def test_discovered_theorems_are_checked_thereafter():
    """Once promoted, discovered theorems get the same check cycle as seeded ones —
    they accrue check_count > 0 over subsequent life. The cycle runs check_theorems
    *before* discover_theorems each game, so a theorem promoted in the very last
    cycle wouldn't yet be checked. Force one final check pass to test the
    persistence semantics. Mirrors test_discovered_theorems_are_checked_thereafter."""
    from domains.worlds import chess_world
    wa = WorldAdapter()
    wa.live_examined(world=chess_world(), n_games=4, max_plies=20, grow_every_game=1)
    wa.live_examined(world=chess_world(), n_games=3, max_plies=20, grow_every_game=1)
    wa.check_theorems()  # final pass — covers theorems promoted on the last live
    discovered = _discovered(wa)
    assert discovered
    for t in discovered:
        a = wa.s.node(t)["attrs"]
        assert int(a.get("check_count", 0)) >= 1, \
            f"discovered theorem {a.get('name')} was never checked"


def test_discovered_theorems_appear_in_theorem_state():
    """The theorem_state API surfaces both seeded and discovered theorems (mirrors
    test_discovered_theorems_appear_in_theorem_state)."""
    wa = _lived()
    state = wa.theorem_state()
    seeded_names = {"sensed_implies_modeled", "quality_monotone_non_decreasing",
                    "discovery_converges"}
    discovered_names = {n for n in state if n.startswith("thm_")}
    assert seeded_names.issubset(state.keys())
    assert len(discovered_names) > 0
