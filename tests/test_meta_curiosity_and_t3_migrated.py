"""Meta-curiosity, migrated — boundary-asymmetry weighting of the action score
runs through the SEEDED `action_score_term` + `meta_curiosity_weight` policy in
the WorldAdapter (no CuriousAgent).

Covers the *migratable* half of tests/test_meta_curiosity_and_t3:

  (a) seeded-Term decision — the meta-curiosity bonus IS `asym_count * meta_w`
      inside the seeded `action_score_term`; evaluated via EvalSubgraph. The
      weight is a graph-data Lit policy the agent reads (editing it changes
      behaviour), not a Python parameter.
  (b) mechanical bookkeeping — the adapter tracks the boundary relations
      (senses / models / acts_on) as graph edges and computes the asymmetry
      frontier by set arithmetic, then stamps each ActionCandidate's
      `asym_count`. The Argmax over the seeded term decides which action wins.

The τ₃ (theorem) tests and the chess live-loop meta-curiosity tests are NOT
migrated here — see the module docstring of the ORIGINAL file and the burn
report: theorem seeding/checking and the live game loop are CuriousAgent
reasoning (no theorem seed exists; checking needs the live grow/discover
cycle). Those stay in the original until a theorem seed + Rust tick exist.
"""
from __future__ import annotations

import substrate_rs as srs
from domains.worlds import chess_world
from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


def _world(nodes):
    g = TypedGraph()
    for (t, a) in nodes:
        g._insert_node(t, a)
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _read_named(inner, ag, name, env):
    env = dict(env)
    env["a"] = ag
    return inner.evaluate(
        {"type": "EvalSubgraph", "node": {"type": "Pick", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": "a"},
            "edge_type": name}}}, env)


# --- (a) the meta-curiosity DECISION is the seeded action_score_term ----------


def test_action_score_includes_meta_curiosity_bonus_from_seed():
    """asym_count is weighted by meta_curiosity_weight (0.15) inside the seeded
    action_score_term: score = -q + asym_count*0.15 + novelty*0.02."""
    s = srs.Substrate()
    inner = s._inner
    ag = s.add_node("Agent", {})
    inner.load_seed_manifest(manifest_for("decision_core"), ag)
    c = s.add_node("ActionCandidate", {"q": 0.2, "asym_count": 3, "novelty": 2})
    sc = _read_named(inner, ag, "action_score_term", {"c": c})
    assert abs(float(sc) - 0.29) < 1e-9   # -0.2 + 3*0.15 + 2*0.02

    # The bonus is monotone in asym_count: a candidate touching MORE boundary-
    # asymmetric types scores higher (all else equal). The seed decides this.
    lo = s.add_node("ActionCandidate", {"q": 0.0, "asym_count": 0, "novelty": 0})
    hi = s.add_node("ActionCandidate", {"q": 0.0, "asym_count": 2, "novelty": 0})
    s_lo = float(_read_named(inner, ag, "action_score_term", {"c": lo}))
    s_hi = float(_read_named(inner, ag, "action_score_term", {"c": hi}))
    assert s_hi > s_lo
    assert abs(s_hi - s_lo - 2 * 0.15) < 1e-9   # exactly 2 * meta_curiosity_weight


def test_meta_curiosity_weight_is_an_editable_lit_policy():
    """meta_curiosity_weight lives as a graph-data Term.Lit the agent reads;
    editing it re-weights the bonus (it is policy, not a Python constant)."""
    wa = WorldAdapter()
    assert wa.get_scalar_policy("meta_curiosity_weight") == 0.15
    wa.set_scalar_policy("meta_curiosity_weight", 0.5)
    assert wa.get_scalar_policy("meta_curiosity_weight") == 0.5


# --- (b) boundary-asymmetry bookkeeping: senses / models / acts_on ------------


def test_boundary_relations_are_graph_edges():
    """senses (perceived on ingest), acts_on / models (registered by the world)
    live as edges off the agent node; the sets are read back from the graph."""
    wa = WorldAdapter()
    wa.ingest(_world([("Pawn", {"id": "p1"}), ("Rook", {"id": "r1"})]))
    assert wa.senses() == {"Pawn", "Rook"}
    assert wa.acts_on_set() == set() and wa.models_set() == set()
    wa.register_relation("Pawn", "acts_on")
    wa.register_relation("Pawn", "models")
    assert wa.acts_on_set() == {"Pawn"}
    assert wa.models_set() == {"Pawn"}
    # idempotent — re-registering the same relation adds no duplicate edge.
    wa.register_relation("Pawn", "acts_on")
    assert wa.acts_on_set() == {"Pawn"}


def test_boundary_asymmetry_frontier_is_set_arithmetic():
    """frontier = (senses ∖ acts_on) ∪ (senses ∖ models) — what's been sensed
    but not yet acted on / modeled. Pure mechanical set difference."""
    wa = WorldAdapter()
    wa.ingest(_world([("Pawn", {"id": "p1"}), ("Rook", {"id": "r1"})]))
    # nothing acted/modeled yet -> everything sensed is on the frontier.
    assert wa.boundary_asymmetry() == {"Pawn", "Rook"}
    wa.register_relation("Pawn", "acts_on")
    wa.register_relation("Pawn", "models")
    # Pawn is now both acted-on and modeled -> off the frontier; Rook remains.
    assert wa.boundary_asymmetry() == {"Rook"}
    assert wa.asymmetry_count(["Rook"]) == 1      # touches the frontier
    assert wa.asymmetry_count(["Pawn"]) == 0      # complete -> no bonus
    assert wa.asymmetry_count(["Pawn", "Rook"]) == 1


def test_meta_curiosity_prefers_the_asymmetric_action():
    """End-to-end through the seed: with the bonus, the action touching a
    body-type still on the asymmetry frontier wins the Argmax — regardless of
    list order. The adapter stamps asym_count; the seeded term decides."""
    touches = {"move_rook": ["Rook"], "move_pawn": ["Pawn"]}
    preview = lambda a: _world([])   # equal (zero) novelty + quality both ways

    for order in (["move_pawn", "move_rook"], ["move_rook", "move_pawn"]):
        wa = WorldAdapter()
        wa.ingest(_world([("Pawn", {"id": "p1"}), ("Rook", {"id": "r1"})]))
        # Pawn is complete (acted-on + modeled); Rook is still on the frontier.
        wa.register_relation("Pawn", "acts_on")
        wa.register_relation("Pawn", "models")
        chosen = wa.choose_action_meta_curious(order, preview, lambda a: touches[a])
        assert chosen == "move_rook", f"frontier action should win (order={order})"


def test_meta_curiosity_stamps_asym_count_on_candidates():
    """The chooser stamps each ActionCandidate's asym_count from the action's
    touched types ∩ frontier — the input the seeded term reads."""
    wa = WorldAdapter()
    wa.ingest(_world([("Pawn", {"id": "p1"}), ("Rook", {"id": "r1"})]))
    wa.register_relation("Pawn", "acts_on")
    wa.register_relation("Pawn", "models")
    touches = {"move_rook": ["Rook"], "move_pawn": ["Pawn"]}
    wa.choose_action_meta_curious(["move_rook", "move_pawn"], lambda a: _world([]),
                                  lambda a: touches[a])
    stamped = {}
    for c in wa.s.nodes():
        n = wa.s.node(c)
        if n["type"] == "ActionCandidate":
            stamped[n["attrs"]["idx"]] = n["attrs"]["asym_count"]
    assert stamped[0] == 1   # move_rook touches the frontier
    assert stamped[1] == 0   # move_pawn is complete


def test_unknown_boundary_relation_rejected():
    """register_relation only admits the three boundary relations — a guard on
    the I/O surface, not a decision over graph state."""
    wa = WorldAdapter()
    import pytest
    with pytest.raises(ValueError):
        wa.register_relation("Pawn", "befriends")


# --- composed boot: the seeded term is present + reads asym_count -------------


def test_composed_boot_has_action_score_term():
    """A fully seed-booted agent carries exactly one action_score_term faculty
    (the meta-curiosity decision), readable as graph data."""
    s, ag = boot_core()
    assert len(s._inner.neighbours(ag, "action_score_term")) == 1


# === MIGRATED from tests/test_meta_curiosity_and_t3.py ========================
#
# Both prior blockers are now resolved on the seed-booted WorldAdapter:
#   • τ₃ — the `theorem_core` seed (in CORE_SEEDS) installs the three Theorem
#     nodes, each with a predicate Term-tree the DSL evaluates. The adapter's
#     check_theorems() runs each predicate via EvalSubgraph and records held /
#     check_count as graph state on the Theorem node. The DECISION is the seeded
#     Term; the adapter only stamps the temporal scalars it reads and counts.
#   • the chess-live meta-curiosity tests — live_examined(chess_world()) drives
#     the seeded action_score_term per ply (choose_action_meta_curious), registers
#     the senses/acts_on/models boundary edges mechanically, and checks the
#     theorems each game. No CuriousAgent.
#
# Mapping from the original CuriousAgent surface to the adapter:
#   agent.theorem_state()          -> wa.theorem_state()
#   agent.mind_graph.nodes("X")    -> [n for n in wa.s.nodes() if type==X]
#   agent.agent_root               -> wa.agent  /  agent.mind_graph -> wa.s
#   agent.live(...)                -> wa.live_examined(...)
#   agent._discovered_relations    -> wa._discovered_relations
#   agent.gamma_dynamic.productions-> wa.meta_productions()  (grown Γ edge types)


def _theorem_nodes(wa):
    return [n for n in wa.s.nodes() if wa.s.node(n)["type"] == "Theorem"]


# --- τ₃: theorems in the substrate (graph data) ------------------------------


def test_theorems_seeded_on_construction_migrated():
    """A freshly seed-booted agent starts with the three theorem nodes — graph
    data installed by the theorem_core seed, read back via theorem_state()."""
    wa = WorldAdapter()
    theorems = wa.theorem_state()
    assert len(theorems) >= 3
    assert "sensed_implies_modeled" in theorems
    assert "quality_monotone_non_decreasing" in theorems
    assert "discovery_converges" in theorems


def test_theorem_nodes_are_admissible_in_meta_gamma_migrated():
    """The agent's `asserts` edges to Theorem nodes are admissible — boot
    succeeded — and there is exactly one per theorem."""
    wa = WorldAdapter()
    asserts_edges = wa.inner.neighbours(wa.agent, "asserts")
    assert {wa.s.node(n)["type"] for n in asserts_edges} == {"Theorem"}
    assert len(asserts_edges) == len(wa.theorem_state())


def test_theorem_checking_runs_during_life_migrated():
    """check_theorems is woven into live_examined; check counts increase for
    every theorem over a life."""
    wa = WorldAdapter()
    initial = {n: s["checks"] for n, s in wa.theorem_state().items()}
    wa.live_examined(chess_world(), n_games=2, max_plies=20, grow_every_game=1)
    after = {n: s["checks"] for n, s in wa.theorem_state().items()}
    for name in initial:
        assert after[name] > initial[name], f"theorem {name} was never checked"


def test_quality_monotone_theorem_holds_migrated():
    """Theorem A — Γ-quality should be monotone non-decreasing across the life.
    The held flag latches False on the first violation; it stays True here. The
    DECISION is the seeded quality_monotone predicate Term (current ≥ prev),
    evaluated each check over the adapter-stamped quality scalar."""
    wa = WorldAdapter()
    wa.live_examined(chess_world(), n_games=3, max_plies=20, grow_every_game=1)
    assert wa.theorem_state()["quality_monotone_non_decreasing"]["held"], (
        "Theorem A violated: Γ-quality decreased somewhere in the trajectory"
    )


def test_theorem_state_is_graph_state_migrated():
    """Theorem held status + check counter live as attrs on the Theorem nodes in
    the substrate — not Python state, substrate state."""
    wa = WorldAdapter()
    wa.live_examined(chess_world(), n_games=2, max_plies=15, grow_every_game=1)
    theorem_nodes = _theorem_nodes(wa)
    assert len(theorem_nodes) >= 3
    for t in theorem_nodes:
        attrs = wa.s.node(t)["attrs"]
        assert "last_held" in attrs
        assert "check_count" in attrs
        assert attrs["check_count"] > 0


def test_theorem_predicate_is_evaluated_graph_data_migrated():
    """The theorem's held verdict is produced by evaluating its predicate Term
    (graph data) through the DSL — editing the temporal scalars the predicate
    reads flips the verdict, proving the decision is the seeded Term, not Python.
    quality_monotone = current_quality ≥ prev_quality."""
    wa = WorldAdapter()
    th = next(t for t in _theorem_nodes(wa)
              if wa.s.node(t)["attrs"]["name"] == "quality_monotone_non_decreasing")
    term = {"type": "EvalSubgraph", "node": {"type": "Pick", "source": {
        "type": "Neighbours", "node": {"type": "Var", "name": "t"},
        "edge_type": "predicate"}}}
    wa.inner.set_attr(th, "current_quality", 5.0)
    wa.inner.set_attr(th, "prev_quality", 3.0)
    assert bool(wa.inner.evaluate(term, {"t": th, "agent": wa.agent, "self": th})) is True
    wa.inner.set_attr(th, "current_quality", 2.0)   # quality DROPPED
    assert bool(wa.inner.evaluate(term, {"t": th, "agent": wa.agent, "self": th})) is False


# --- Meta-curiosity over chess-live (the seeded action_score_term) ------------


def test_meta_curiosity_does_not_break_chess_migrated():
    """The meta-curiosity bonus coexists with the base curiosity signal — the
    agent still plays legal moves, accumulates activity, and runs discovery in
    chess, all through live_examined."""
    wa = WorldAdapter()
    wa.live_examined(chess_world(), n_games=2, max_plies=20, grow_every_game=1)
    # Discovery still happens (activity accumulates) and boundary edges grow.
    assert wa._n_events > 0
    assert len(wa.acts_on_set()) > 0
    assert len(wa.senses()) > 0


def test_meta_curiosity_expands_acts_on_set_more_eagerly_migrated():
    """With the bonus, the agent prefers moves involving body-types still on the
    asymmetry frontier; over several games acts_on covers many piece kinds. The
    seeded action_score_term decides; the adapter stamps asym_count."""
    wa = WorldAdapter()
    wa.live_examined(chess_world(), n_games=5, max_plies=30, grow_every_game=2)
    piece_types = {"Pawn", "Knight", "Bishop", "Rook", "Queen", "King"}
    acted_kinds = {t.replace("White", "").replace("Black", "")
                   for t in wa.acts_on_set()}
    assert len(acted_kinds & piece_types) >= 4, (
        f"meta-curiosity should diversify acts_on; got {acted_kinds}"
    )
