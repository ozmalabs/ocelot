"""Gates for the price of time in `program_cost`.

Every other term in the composer's cost prices the STATE a program produces.
None of them could say "take this one because it buys more time", so a
candidate that was worse on the goal but extended the margin could never win,
however short the margin got. A reflex buys time and the composer had no way to
spend it. These gates hold the term that closes that, and the two boundaries it
must respect:

  * absence is decided by the POLICY, so an agent that declares nothing prices
    exactly what it always priced;
  * THERE IS NO MARGIN OF ZERO. If the margin is zero it is too late, which is
    a different state and not a larger weight -- the escape path answers there,
    not the cost function.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter


REFERENCE = 50.0
MARGIN_WEIGHT = 0.1


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _compose_bench(*, margin_actions, declare_policy=True):
    """Two candidates: one better on the goal, one that climbs.

    The goal is level flight (`target_vertical` 0), so the climbing candidate
    is strictly WORSE on every state term. Only a price on time can select it.
    """
    try:
        agent = WorldAdapter(seeds=("embodied_motor_program",))
    except RuntimeError as exc:  # pragma: no cover - optional native dep
        pytest.skip(f"native substrate unavailable: {exc}")

    root = agent.agent
    policy = agent.inner.neighbours(
        root, "has_embodied_motor_program_policy")[0]
    if declare_policy:
        agent.s.set_attr(policy, "margin_reference_actions", REFERENCE)
        agent.s.set_attr(policy, "margin_weight", MARGIN_WEIGHT)

    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "target_forward": 1.0,
        "target_lateral": 0.0,
        "target_vertical": 0.0,
        "target_roll": 0.0,
        "target_pitch": 0.0,
        "target_turn": 0.0,
        "target_normal_load": 0.0,
        "margin_actions": float(margin_actions),
    })
    _edge(agent, root, "has_embodied_motor_program_episode", episode)

    # On-goal: hits target_forward exactly, no vertical rate.
    on_goal = agent.s.add_node("EmbodiedEffectorModel", {
        "token": "on_goal", "actuator_group": 0.0, "ordinal": 1.0,
        "experience_count": 9.0, "available": 1.0, "log_authority": 0.0,
        "activation_magnitude": 0.0,
        "mean_forward": 1.0, "mean_vertical": 0.0,
    })
    # Buys time: climbs, but misses the goal.
    buys_time = agent.s.add_node("EmbodiedEffectorModel", {
        "token": "buys_time", "actuator_group": 1.0, "ordinal": 1.0,
        "experience_count": 9.0, "available": 1.0, "log_authority": 0.0,
        "activation_magnitude": 0.0,
        "mean_forward": 0.0, "mean_vertical": 1.0,
    })
    for model in (on_goal, buys_time):
        _edge(agent, episode, "has_embodied_effector_model", model)
    return agent, episode, policy


def _chosen(agent, episode, policy) -> set:
    """Which candidates the composer put in the program.

    `MotorCompose` answers PER CANDIDATE -- "is this model a member of the
    composed program" -- so the readout asks it once per model rather than
    expecting a plan back.
    """
    chosen = set()
    for model in agent.inner.neighbours(
        episode, "has_embodied_effector_model"
    ):
        term = {
            "type": "MotorCompose",
            "episode": {"type": "Var", "name": "ep"},
            "policy": {"type": "Var", "name": "po"},
            "candidate": {"type": "Var", "name": "cand"},
        }
        verdict = agent.inner.evaluate(
            term, {"ep": episode, "po": policy, "cand": model})
        if verdict:
            chosen.add(str(agent.s.node(model)["attrs"].get("token")))
    return chosen


def test_a_long_margin_leaves_the_choice_on_the_goal():
    """Urgency ~0: the price of time must not distort a relaxed decision."""
    agent, episode, policy = _compose_bench(margin_actions=1000.0)
    chosen = _chosen(agent, episode, policy)
    assert "on_goal" in chosen, (
        "with 1000 actions of budget the goal term must still decide"
    )


def test_a_short_margin_selects_the_candidate_that_buys_time():
    """The headline: worse on the goal, chosen because it extends the margin.

    This is the sentence `program_cost` could not previously express.
    """
    agent, episode, policy = _compose_bench(margin_actions=2.0)
    chosen = _chosen(agent, episode, policy)
    assert "buys_time" in chosen, (
        "at 2 actions of budget the climbing candidate must be selected even "
        "though it is worse on every state term"
    )


def test_an_undeclared_policy_prices_no_margin():
    """Absent-inert: the faculty is off unless the policy asks for it."""
    agent, episode, policy = _compose_bench(
        margin_actions=2.0, declare_policy=False)
    chosen = _chosen(agent, episode, policy)
    assert "on_goal" in chosen
    assert "buys_time" not in chosen, (
        "an agent that declares no margin policy must decide exactly as before"
    )


def test_a_margin_of_zero_is_not_priced_at_all():
    """THERE IS NO MARGIN OF ZERO -- if it is zero it is too late.

    Zero is not maximum urgency, it is a different state, and the escape path
    answers there. Pricing it would keep the composer choosing between
    programs at the exact moment its job is to stop choosing and go.
    """
    agent, episode, policy = _compose_bench(margin_actions=0.0)
    chosen = _chosen(agent, episode, policy)
    assert "on_goal" in chosen, (
        "a zero margin must fall through to the unpriced decision, not to an "
        "unbounded one"
    )
    assert "buys_time" not in chosen
