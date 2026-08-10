"""Gates for the price of not knowing a member.

MEASURED, and the term exists because of the number rather than the theory: on
damaged_wing the loop spends 319 of 1000 actions commanding one effector alone
-- a large attribution budget -- and after action 250 all 231 of those go to a
SINGLE member. 36 of 37 effector models sit frozen at `experience_count` 201
for the last 750 actions, which is the entire departure. The budget was never
missing; it was spent on the member that already knew the most.

The cause is convergence, not scheduling: the singleton open picks whichever
member minimises `singleton_cost`, the state barely moves, so the same member
wins every time. Pricing staleness in the cost rotates the primary, which is
also the composition variation the learners need — one term, both halves.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter


REFERENCE = 50.0
ATTRIBUTION_WEIGHT = 0.05


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _bench(*, declare=True, request_seq=500.0, fresh_seq=490.0, stale_seq=10.0):
    """Two members, near-identical on every state term.

    `settled` was exercised alone ten actions ago; `starved` four hundred and
    ninety. Nothing else distinguishes them, which is exactly the degenerate
    case that produced 100% concentration in flight.
    """
    try:
        agent = WorldAdapter(seeds=("embodied_motor_program",))
    except RuntimeError as exc:  # pragma: no cover - optional native dep
        pytest.skip(f"native substrate unavailable: {exc}")

    root = agent.agent
    policy = agent.inner.neighbours(
        root, "has_embodied_motor_program_policy")[0]
    if declare:
        agent.s.set_attr(policy, "attribution_reference_actions", REFERENCE)
        agent.s.set_attr(policy, "attribution_weight", ATTRIBUTION_WEIGHT)

    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "target_forward": 1.0, "target_lateral": 0.0, "target_vertical": 0.0,
        "target_roll": 0.0, "target_pitch": 0.0, "target_turn": 0.0,
        "target_normal_load": 0.0,
        "program_request_seq": float(request_seq),
    })
    _edge(agent, root, "has_embodied_motor_program_episode", episode)

    for token, group, seq in (
        ("settled", 0.0, fresh_seq), ("starved", 1.0, stale_seq),
    ):
        model = agent.s.add_node("EmbodiedEffectorModel", {
            "token": token, "actuator_group": group, "ordinal": 1.0,
            "experience_count": 9.0, "available": 1.0,
            "log_authority": 0.0, "activation_magnitude": 0.0,
            "mean_forward": 1.0, "mean_vertical": 0.0,
            "last_singleton_exercise_seq": float(seq),
        })
        _edge(agent, episode, "has_embodied_effector_model", model)
    return agent, episode, policy


def _chosen(agent, episode, policy) -> set:
    chosen = set()
    for model in agent.inner.neighbours(
        episode, "has_embodied_effector_model"
    ):
        verdict = agent.inner.evaluate({
            "type": "MotorCompose",
            "episode": {"type": "Var", "name": "ep"},
            "policy": {"type": "Var", "name": "po"},
            "candidate": {"type": "Var", "name": "cand"},
        }, {"ep": episode, "po": policy, "cand": model})
        if verdict:
            chosen.add(str(agent.s.node(model)["attrs"].get("token")))
    return chosen


def test_the_starved_member_is_preferred_when_all_else_is_equal():
    """The headline: identical on every state term, so staleness decides."""
    agent, episode, policy = _bench()
    assert "starved" in _chosen(agent, episode, policy), (
        "a member unexercised for ~10 windows must outrank one exercised a "
        "fifth of a window ago when nothing else separates them"
    )


def test_an_undeclared_policy_prices_no_attribution():
    """Absent-inert: without the policy asking, the tie breaks as before."""
    agent, episode, policy = _bench(declare=False)
    chosen = _chosen(agent, episode, policy)
    assert "settled" in chosen, (
        "with no attribution policy the composer must decide exactly as it did"
    )


def test_a_never_exercised_member_is_maximally_stale():
    """Absence is the right polarity: never measured is most worth measuring.

    `last_singleton_exercise_seq` absent reads 0 through the attr default, so a
    member that has never been commanded alone prices as maximally stale rather
    than as freshly known.
    """
    agent, episode, policy = _bench(stale_seq=0.0)
    assert "starved" in _chosen(agent, episode, policy)


def test_equal_staleness_does_not_shift_the_choice():
    """The term must break ties on STALENESS, not add a constant offset.

    If both members are equally stale the attribution price is identical and
    cancels, so the decision returns to the state terms. A linear offset that
    failed to cancel here would bias every composition.
    """
    agent, episode, policy = _bench(fresh_seq=100.0, stale_seq=100.0)
    baseline_agent, baseline_episode, baseline_policy = _bench(
        declare=False, fresh_seq=100.0, stale_seq=100.0)
    assert _chosen(agent, episode, policy) == _chosen(
        baseline_agent, baseline_episode, baseline_policy)
