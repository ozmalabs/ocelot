"""Gates for shapes indexing MODELS.

DF measured why the shape-derived adaptation rate cost three ground contacts,
and the defect was SCOPE, not arithmetic: `stable_run` is regime-local and the
model it moved is global, so one sample in a new regime discarded what the
model knew about every other one.

The resolution is the pattern this line already uses -- shapes index programs,
shapes index reflexes, so shapes index models. A model that meets a regime it
has never seen FORKS: the fork inherits the parent's means and restarts its own
sample count, which makes the plain `1/n` the tree has always used correct by
construction. No floor, no `1/stable_run`, no declared constant.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _bench(*, enabled=True):
    try:
        agent = WorldAdapter(seeds=("embodied_motor_program",))
    except RuntimeError as exc:  # pragma: no cover - optional native dep
        pytest.skip(f"native substrate unavailable: {exc}")
    root = agent.agent
    policy = agent.inner.neighbours(
        root, "has_embodied_motor_program_policy")[0]
    agent.s.set_attr(policy, "motor_surprise_shape_quantum", 1.0)
    if enabled:
        agent.s.set_attr(policy, "regime_local_models_enabled", 1.0)

    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "target_forward": 1.0, "target_lateral": 0.0, "target_vertical": 0.0,
        "target_roll": 0.0, "target_pitch": 0.0, "target_turn": 0.0,
        "target_normal_load": 0.0,
    })
    _edge(agent, root, "has_embodied_motor_program_episode", episode)
    model = agent.s.add_node("EmbodiedEffectorModel", {
        "token": "elevator", "actuator_group": 0.0, "ordinal": 1.0,
        "experience_count": 200.0, "available": 1.0,
        "mean_forward": 1.0, "mean_vertical": 0.25,
    })
    _edge(agent, episode, "has_embodied_effector_model", model)
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "relative_normal_load_error": 3.0, "member_count": 1.0,
        "internalized_epoch": 7.0,
    })
    _edge(agent, episode, "has_default_embodied_motor_program", program)
    _edge(agent, program, "includes_embodied_effector_model", model)
    return agent, episode, policy, model, program


def _action(agent, episode, program, model, seq, *, residual=3.0):
    agent.s.set_attr(episode, "program_request_seq", float(seq))
    agent.s.set_attr(program, "relative_normal_load_error", float(residual))
    trial = agent.s.add_node("EmbodiedMotorProgramTrial", {
        "expected_member_count": 1.0,
    })
    outcome = agent.s.add_node("EmbodiedMotorProgramOutcome", {
        "receipt_verified": 1.0, "request_seq": float(seq), "processed": 1.0,
    })
    _edge(agent, episode, "has_embodied_motor_program_trial", trial)
    _edge(agent, trial, "enacts_embodied_motor_program", program)
    _edge(agent, trial, "commands_embodied_effector_model", model)
    _edge(agent, trial, "has_embodied_motor_program_outcome", outcome)
    agent.inner.run_rules(12)


def _forks(agent, model):
    return agent.inner.neighbours(model, "has_regime_local_model")


def test_a_new_regime_forks_the_model():
    """The headline: a residual bucket never seen before mints a fork."""
    agent, episode, policy, model, program = _bench()
    _action(agent, episode, program, model, 1)
    forks = _forks(agent, model)
    assert len(forks) == 1, "a new regime must fork the commanded model"


def test_the_fork_inherits_rather_than_starting_empty():
    """Starting empty is unusable, and inheriting is the honest prior.

    `eligible` needs `experience_count > 0.5`, so an empty fork could never be
    selected and could therefore never gain a sample.  Inheriting the parent's
    means makes it no worse than the parent on its first action.
    """
    agent, episode, policy, model, program = _bench()
    _action(agent, episode, program, model, 1)
    fork = agent.s.node(_forks(agent, model)[0])["attrs"]
    parent = agent.s.node(model)["attrs"]
    # Compared against the PARENT as it stands, not against the seeded literal:
    # the exact-receipt learner fires in the same fixpoint, so the parent has
    # already taken this action's sample and the fork inherits the updated
    # value.  That is the correct behaviour -- the fork should start from what
    # the parent knows now, not from what it knew before the action.
    assert fork["mean_forward"] == pytest.approx(parent["mean_forward"])
    assert fork["mean_vertical"] == pytest.approx(parent["mean_vertical"])
    assert fork["experience_count"] == pytest.approx(1.0), (
        "the fork restarts its OWN count -- that is the whole point, and it "
        "is what makes plain 1/n the correct rate again"
    )
    # 201, not the seeded 200, for the same reason: the parent took this
    # action's sample before the fork read its count.
    assert fork["forked_from_experience"] == pytest.approx(
        parent["experience_count"])
    assert fork["forked_from_experience"] > 100.0, (
        "the provenance must record the parent's GLOBAL count -- that is the "
        "scope the fork exists to escape"
    )


def test_a_second_action_in_the_same_regime_does_not_fork_again():
    """One fork per regime, not one per action."""
    agent, episode, policy, model, program = _bench()
    for seq in (1, 2, 3):
        _action(agent, episode, program, model, seq)
    assert len(_forks(agent, model)) == 1


def test_a_different_regime_forks_separately():
    """The index has to distinguish regimes, or it is just one extra model."""
    agent, episode, policy, model, program = _bench()
    _action(agent, episode, program, model, 1, residual=3.0)
    _action(agent, episode, program, model, 2, residual=1_000_000.0)
    ordinals = sorted(
        agent.s.node(f)["attrs"]["shape_ordinal"] for f in _forks(agent, model)
    )
    assert len(ordinals) == 2, "a distinct residual bucket is a distinct regime"
    assert ordinals[0] != ordinals[1]


def test_a_fork_never_forks():
    """Forks are one level deep, or the model set grows without bound."""
    agent, episode, policy, model, program = _bench()
    _action(agent, episode, program, model, 1)
    fork = _forks(agent, model)[0]
    assert _forks(agent, fork) == []


def test_the_faculty_is_inert_when_undeclared():
    """Absent-inert: no policy flag, no forks, byte-identical behaviour."""
    agent, episode, policy, model, program = _bench(enabled=False)
    for seq in (1, 2, 3):
        _action(agent, episode, program, model, seq)
    assert _forks(agent, model) == []
