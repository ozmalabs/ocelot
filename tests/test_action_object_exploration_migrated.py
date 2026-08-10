"""Per-(observed_type, action_kind) exploration, migrated — "what can I do with
this?" runs in the WorldAdapter (no CuriousAgent).

ActionTypeStat nodes in the agent's substrate track how many times each (type,
action) pair has been tried, plus a freshening EMA of whether the combo produced
learning. The scorer (seeded) awards a UCB-style bonus to low-attempt pairs,
driving the agent to systematically try each action with each thing it observes
— adventure-game inquisitiveness. The mechanism is map-agnostic.

Covers tests/test_action_object_exploration: lazy ActionTypeStat creation +
agent edge, attempt increments, distinct pairs, untracked→0, choose_action
recording attempts for observed types, exploration-bonus decay, the per-(type,
action) freshening EMA, and type-agnostic application.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world_with(types):
    """One node per requested type, no edges (id-less — types only)."""
    g = TypedGraph()
    for typ in types:
        g._insert_node(typ, {})
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_action_type_stat_created_lazily():
    """The ActionTypeStat node is created on first reference and attached to the
    agent via tracks_action_type — graph data."""
    wa = WorldAdapter()
    nid = wa._ensure_action_type_stat("Door", "use")
    n = wa.s.node(nid)
    assert n["type"] == "ActionTypeStat"
    assert n["attrs"]["type_name"] == "Door"
    assert n["attrs"]["action_kind"] == "use"
    assert n["attrs"]["attempts"] == 0
    # Edge from the agent.
    assert nid in list(wa.inner.neighbours(wa.agent, "tracks_action_type"))


def test_record_action_type_attempt_increments():
    wa = WorldAdapter()
    wa._record_action_type_attempt("Door", "use")
    wa._record_action_type_attempt("Door", "use")
    wa._record_action_type_attempt("Door", "use")
    assert wa._action_type_attempts("Door", "use") == 3


def test_distinct_type_action_pairs_are_separate():
    wa = WorldAdapter()
    wa._record_action_type_attempt("Door", "use")
    wa._record_action_type_attempt("Enemy", "attack")
    assert wa._action_type_attempts("Door", "use") == 1
    assert wa._action_type_attempts("Enemy", "attack") == 1
    assert wa._action_type_attempts("Door", "attack") == 0
    assert wa._action_type_attempts("Enemy", "use") == 0


def test_untracked_pair_returns_zero():
    wa = WorldAdapter()
    assert wa._action_type_attempts("never", "seen") == 0


def test_choose_action_records_attempts_for_observed_types():
    """When the agent picks an action while observing things of certain types,
    the (type, action) attempts counter increments — the agent is logging 'I
    tried action X while seeing things of type Y'."""
    wa = WorldAdapter()
    sub = _world_with(["AgentMarker", "Apple"])
    wa.ingest(sub)
    actions = [("use",), ("attack",)]
    chosen = wa.choose_action_exploring(
        actions, lambda a: _world_with(["AgentMarker", "Apple"]))
    # Whichever action was picked, both observed types got attempts++.
    assert wa._action_type_attempts("AgentMarker", chosen[0]) == 1
    assert wa._action_type_attempts("Apple", chosen[0]) == 1


def test_attempts_decay_exploration_bonus():
    """Repeated attempts of the same (type, action) pair drive the bonus down —
    the agent stops being pushed to retry exhaustively once it has tried
    enough."""
    wa = WorldAdapter()
    for _ in range(50):
        wa._record_action_type_attempt("Door", "use")
    n = wa._action_type_attempts("Door", "use")
    assert n == 50
    # Bonus per the formula exploration_w / (1 + n) for weight 0.05:
    # at n=50, bonus ≈ 0.05 / 51 ≈ 0.001 — small.
    bonus = 0.05 / (1 + n)
    assert bonus < 0.002


def test_freshening_ema_records_per_type_action_outcome():
    """The freshening EMA on each ActionTypeStat node captures whether the
    (type, action) combo produced learning. Many attempts with no freshening
    keeps the EMA near zero — the substrate-native expression of 'I can't use
    these things together'."""
    wa = WorldAdapter()
    # 1000 zero-freshening attempts → EMA stays near zero.
    for _ in range(1000):
        wa._record_action_type_outcome("Wall", "use", 0)
    no_work_ema = wa._action_type_freshening_ema("Wall", "use")
    assert no_work_ema < 0.01
    # 1000 high-freshening attempts → EMA climbs.
    for _ in range(1000):
        wa._record_action_type_outcome("Door", "use", 3)
    works_ema = wa._action_type_freshening_ema("Door", "use")
    assert works_ema > 2.5
    # The differential is what drives the agent toward what works.


def test_pair_with_no_freshening_after_many_tries_loses_priority():
    """A (type, action) pair tried many times with no freshening accumulates
    near-zero ema. Combined with a decaying 1/(1+attempts) UCB term, the total
    bonus drops to near-zero — the agent stops repeating the combination."""
    wa = WorldAdapter()
    for _ in range(200):
        wa._record_action_type_attempt("Wall", "use")
        wa._record_action_type_outcome("Wall", "use", 0)
    n = wa._action_type_attempts("Wall", "use")
    ema = wa._action_type_freshening_ema("Wall", "use")
    # bonus formula: exploration_w * (1/(1+n) + 5*ema)
    # with weight 0.05: 0.05 * (1/201 + ~0) ≈ 0.00025 — negligible.
    bonus = 0.05 * (1.0 / (1 + n) + 5.0 * ema)
    assert bonus < 0.005


def test_pair_with_high_freshening_keeps_priority_after_many_tries():
    """A combo that consistently produces freshening keeps its bonus high even
    after many attempts — the ema-amplifier dominates the decaying UCB term."""
    wa = WorldAdapter()
    for _ in range(200):
        wa._record_action_type_attempt("Door", "use")
        wa._record_action_type_outcome("Door", "use", 2)
    n = wa._action_type_attempts("Door", "use")
    ema = wa._action_type_freshening_ema("Door", "use")
    # Even with n=200, 5*ema ≈ 8.7 → bonus = 0.05*(0.005+8.7) ≈ 0.44.
    bonus = 0.05 * (1.0 / (1 + n) + 5.0 * ema)
    assert bonus > 0.1


def test_exploration_works_for_arbitrary_types():
    """The mechanism is type-agnostic: a brand-new type the agent has never
    observed has 0 attempts for any action, so all candidate actions get the
    full bonus when observing it. Adventure-game instinct: try everything with
    anything new."""
    wa = WorldAdapter()
    sub = _world_with(["AlienDevice"])
    wa.ingest(sub)
    for action in ("use", "attack", "noop"):
        assert wa._action_type_attempts("AlienDevice", action) == 0
