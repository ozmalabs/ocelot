"""Execution gates for the domain-neutral graph-native decision collapse."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[1]
SEED = ROOT / "seeds" / "motor_decision_collapse.json"
GENERATOR = ROOT / "scripts" / "gen_motor_decision_collapse_seed.py"

for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _fresh():
    return WorldAdapter(seeds=("motor_decision_collapse",))


def _state(agent, *, tolerance=0.15, deepen=1.0, gain=0.35):
    state = agent.s.add_node("MotorDecisionState", {
        "stage": "ready",
        "collapse_armed": 0.0,
        "settle_tolerance": float(tolerance),
        "deeper_enabled": float(deepen),
        "internalization_gain": float(gain),
        "rationalise_gain": 0.0,
        "decision_epoch": 0.0,
        "done": 0.0,
    })
    _edge(agent, agent.agent, "has_motor_decision", state)
    return state


def _option(
    agent,
    state,
    token,
    ordinal,
    default,
    grounded,
    *,
    edge="in_scene",
    learned=0.0,
    count=0.0,
    available=1.0,
):
    option = agent.s.add_node("DecisionOption", {
        "token": token,
        "ordinal": float(ordinal),
        "default_value": float(default),
        "learned_value": float(learned),
        "grounded_value": float(grounded),
        "decision_experience_count": float(count),
        "available": float(available),
        "internalized_epoch": -1.0,
    })
    _edge(agent, state, edge, option)
    return option


def _arm(agent, state, epoch):
    agent.s.set_attr(state, "stage", "ready")
    agent.s.set_attr(state, "collapse_armed", 1.0)
    agent.s.set_attr(state, "decision_epoch", float(epoch))
    agent.s.set_attr(state, "done", 0.0)
    assert agent.tick() > 0
    return agent.s.node(state)["attrs"]


def test_seed_is_generated_domain_neutral_graph_data():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    assert seed["id"] == "motor_decision_collapse"
    assert seed["self_load_only"] is True
    assert seed["version"] == "1.1.0"
    assert len(seed["rules"]) == 12
    names = {rule["name"] for rule in seed["rules"]}
    assert {
        "mdc_fast_propose",
        "mdc_shallow_settle",
        "mdc_residual_authorized_deepen",
        "mdc_internalize_scene_option",
        "mdc_internalize_episode_option",
        "mdc_finish_internalization",
        "mdc_episode_provision_state",
        "mdc_episode_open_state",
        "mdc_episode_unscope_removed_option",
        "mdc_episode_refuse_empty",
        "mdc_episode_disarm_stale_request",
        "mdc_episode_publish_once",
    } == names

    serialized = json.dumps(seed).lower()
    assert '"type": "union"' in serialized
    assert '"edge_type": "in_scene"' in serialized
    assert '"edge_type": "in_episode"' in serialized
    for body_term in (
        "wheel", "steer", "throttle", "quaternion", "pybullet",
        "r2d2", "husky", "racecar",
    ):
        assert body_term not in serialized


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert SEED.read_bytes() == before


def test_two_states_collapse_only_over_their_scene_or_episode():
    agent = _fresh()
    first = _state(agent)
    second = _state(agent)
    _option(agent, first, "first_low", 0, 0.2, 0.2, edge="in_scene")
    _option(agent, first, "first_high", 1, 0.8, 0.8, edge="in_scene")
    _option(agent, second, "second_low", 0, 0.1, 0.1, edge="in_episode")
    _option(agent, second, "second_high", 1, 0.6, 0.6, edge="in_episode")
    # A globally visible but unscoped node must be cognitively nonexistent.
    agent.s.add_node("DecisionOption", {
        "token": "outsider",
        "ordinal": 0.0,
        "default_value": 100.0,
        "learned_value": 100.0,
        "grounded_value": 100.0,
        "decision_experience_count": 1.0,
        "available": 1.0,
        "internalized_epoch": -1.0,
    })

    agent.s.set_attr(first, "collapse_armed", 1.0)
    agent.s.set_attr(first, "decision_epoch", 1.0)
    agent.s.set_attr(second, "collapse_armed", 1.0)
    agent.s.set_attr(second, "decision_epoch", 1.0)
    agent.tick()

    assert agent.s.node(first)["attrs"]["chosen_token"] == "first_high"
    assert agent.s.node(second)["attrs"]["chosen_token"] == "second_high"


def test_novel_options_use_defaults_and_experienced_options_use_learning():
    agent = _fresh()
    state = _state(agent, tolerance=10.0)
    # The novel option's unsupported learned=0.95 must be ignored; its default
    # 0.20 still beats the experienced option's learned 0.10.
    novel = _option(
        agent, state, "novel", 0, 0.2, 0.2, learned=0.95, count=0.0,
    )
    _option(
        agent, state, "experienced", 1, 0.9, 0.1, learned=0.1, count=3.0,
    )
    first = _arm(agent, state, 1)
    assert first["proposed_token"] == "novel"
    assert first["proposed_fast_value"] == pytest.approx(0.2)

    # Once experience backs the learned value, the same graph row proposes it.
    agent.s.set_attr(novel, "decision_experience_count", 1.0)
    second = _arm(agent, state, 2)
    assert second["proposed_token"] == "novel"
    assert second["proposed_fast_value"] == pytest.approx(0.95)


def test_residual_alone_authorizes_deeper_collapse_and_settle_back():
    agent = _fresh()
    state = _state(agent)
    options = [
        _option(agent, state, "impulse", 0, 0.9, -0.5),
        _option(agent, state, "grounded", 1, 0.2, 0.5),
    ]

    rows = [_arm(agent, state, epoch) for epoch in range(1, 5)]
    assert rows[0]["proposed_token"] == "impulse"
    assert rows[0]["residual"] == pytest.approx(1.4)
    assert rows[0]["deeper_authorized"] == 1.0
    assert rows[0]["deepened"] == 1.0
    assert rows[0]["chosen_token"] == "grounded"
    assert rows[0]["chosen_via"] == "orderN"

    # Grounded values settle back into every scoped option, then the corrected
    # choice becomes an automatic learned/default proposal.
    assert all(
        agent.s.node(option)["attrs"]["decision_experience_count"] == 2.0
        for option in options
    )
    assert rows[1]["deepened"] == 1.0
    assert rows[2]["proposed_token"] == "grounded"
    assert rows[2]["deepened"] == 0.0
    assert rows[2]["chosen_via"] == "order0"
    assert rows[3]["deepened"] == 0.0


def test_union_deduplicates_an_option_for_internalization():
    agent = _fresh()
    state = _state(agent)
    shared = _option(agent, state, "shared", 0, 0.9, -0.5, edge="in_scene")
    _edge(agent, state, "in_episode", shared)
    _option(agent, state, "other", 1, 0.2, 0.5, edge="in_episode")

    row = _arm(agent, state, 1)
    assert row["deepened"] == 1.0
    assert (
        agent.s.node(shared)["attrs"]["decision_experience_count"] == 1.0
    )
    assert agent.s.node(shared)["attrs"]["internalized_epoch"] == 1.0


def test_exact_value_ties_collapse_by_stable_ordinal():
    agent = _fresh()
    state = _state(agent, tolerance=10.0)
    _option(agent, state, "later", 8, 0.5, 0.5)
    _option(agent, state, "earlier", 2, 0.5, 0.5)
    row = _arm(agent, state, 1)
    assert row["proposed_token"] == "earlier"
    assert row["chosen_token"] == "earlier"


def test_depth_cap_cannot_run_grounded_valuation():
    agent = _fresh()
    state = _state(agent, deepen=0.0)
    _option(agent, state, "impulse", 0, 0.9, -0.5)
    _option(agent, state, "grounded", 1, 0.2, 0.5)
    row = _arm(agent, state, 1)
    assert row["residual"] > row["settle_tolerance"]
    assert row["deeper_authorized"] == 0.0
    assert row["deepened"] == 0.0
    assert row["chosen_token"] == "impulse"
    assert row["chosen_via"] == "order0"


def _episode(agent):
    episode = agent.s.add_node("EmbodiedMotorEpisode", {
        "decision_armed": 0.0,
        "decision_request_epoch": 0.0,
        "last_opened_decision_epoch": 0.0,
        "last_published_decision_epoch": 0.0,
    })
    _edge(agent, agent.agent, "has_embodied_motor_episode", episode)
    return episode


def _episode_option(agent, episode, *args, **kwargs):
    # Reuse the direct-state option constructor, then replace its scope edge
    # with the episode exposure edge.
    holder = agent.s.add_node("MotorDecisionState", {})
    option = _option(agent, holder, *args, **kwargs)
    agent.inner.remove_node(holder)
    _edge(agent, episode, "has_motor_decision_option", option)
    return option


def _request(agent, episode, epoch):
    agent.s.set_attr(episode, "decision_request_epoch", float(epoch))
    agent.s.set_attr(episode, "decision_armed", 1.0)
    assert agent.tick() > 0
    return agent.s.node(episode)["attrs"]


def test_episode_bridge_keeps_multiple_episodes_independent():
    agent = _fresh()
    first = _episode(agent)
    second = _episode(agent)
    _episode_option(agent, first, "first_low", 0, 0.1, 0.1)
    _episode_option(agent, first, "first_high", 1, 0.7, 0.7)
    _episode_option(agent, second, "second_low", 0, 0.2, 0.2)
    _episode_option(agent, second, "second_high", 1, 0.8, 0.8)

    # Exposure provisions one dormant graph slot per episode before requests.
    assert agent.tick() > 0
    first_states = list(agent.inner.neighbours(first, "has_motor_decision_state"))
    second_states = list(agent.inner.neighbours(second, "has_motor_decision_state"))
    assert len(first_states) == len(second_states) == 1
    assert set(agent.inner.neighbours(first_states[0], "in_episode")) == set(
        agent.inner.neighbours(first, "has_motor_decision_option")
    )
    assert set(agent.inner.neighbours(second_states[0], "in_episode")) == set(
        agent.inner.neighbours(second, "has_motor_decision_option")
    )

    agent.s.set_attr(first, "decision_request_epoch", 1.0)
    agent.s.set_attr(first, "decision_armed", 1.0)
    agent.s.set_attr(second, "decision_request_epoch", 1.0)
    agent.s.set_attr(second, "decision_armed", 1.0)
    agent.tick()

    assert agent.s.node(first)["attrs"]["selected_token"] == "first_high"
    assert agent.s.node(second)["attrs"]["selected_token"] == "second_high"
    assert agent.s.node(first)["attrs"]["decision_status"] == "published"
    assert agent.s.node(second)["attrs"]["decision_status"] == "published"


def test_episode_publication_waits_for_internalization_and_fires_once():
    agent = _fresh()
    episode = _episode(agent)
    options = [
        _episode_option(agent, episode, "impulse", 0, 0.9, -0.5),
        _episode_option(agent, episode, "grounded", 1, 0.2, 0.5),
    ]
    agent.tick()  # provision + fully scope the reusable state

    row = _request(agent, episode, 1)
    assert row["decision_status"] == "published"
    assert row["selected_token"] == "grounded"
    assert row["selected_via"] == "orderN"
    assert row["last_published_decision_epoch"] == 1.0
    state = list(agent.inner.neighbours(
        episode, "has_motor_decision_state"
    ))[0]
    state_attrs = agent.s.node(state)["attrs"]
    assert state_attrs["internalization_required"] == 1.0
    assert state_attrs["internalization_complete"] == 1.0
    assert state_attrs["publication_status"] == "published"
    assert all(
        agent.s.node(option)["attrs"]["internalized_epoch"] == 1.0
        and agent.s.node(option)["attrs"]["decision_experience_count"] == 1.0
        for option in options
    )

    # No graph mutation means no second publication. Re-arming the same epoch
    # is consumed as stale and does not update learning or mint another state.
    assert agent.tick() == 0
    counts = [
        agent.s.node(option)["attrs"]["decision_experience_count"]
        for option in options
    ]
    duplicate = _request(agent, episode, 1)
    assert duplicate["decision_status"] == "stale_request_ignored"
    assert duplicate["last_published_decision_epoch"] == 1.0
    assert len(list(agent.inner.neighbours(
        episode, "has_motor_decision_state"
    ))) == 1
    assert [
        agent.s.node(option)["attrs"]["decision_experience_count"]
        for option in options
    ] == counts


def test_episode_publication_gate_refuses_a_half_internalized_state():
    agent = _fresh()
    episode = _episode(agent)
    option = _episode_option(agent, episode, "opaque", 0, 0.4, 0.4)
    agent.tick()
    state = list(agent.inner.neighbours(
        episode, "has_motor_decision_state"
    ))[0]
    for key, value in {
        "stage": "settled",
        "done": 1.0,
        "internalization_required": 1.0,
        "internalization_complete": 0.0,
        "publication_status": "pending",
        "decision_epoch": 1.0,
        "chosen_option_ref": option,
        # Deliberately inconsistent denormalized caches: publication must use
        # the authoritative winner reference, not stale values from a reused
        # decision slot.
        "chosen_token": "stale_cached_token",
        "chosen_ordinal": 99.0,
        "chosen_via": "orderN",
        "residual": 0.4,
        "order": 1.0,
        "deepened": 1.0,
    }.items():
        agent.s.set_attr(state, key, value)

    assert agent.tick() == 0
    assert "selected_token" not in agent.s.node(episode)["attrs"]
    agent.s.set_attr(state, "internalization_complete", 1.0)
    assert agent.tick() > 0
    published = agent.s.node(episode)["attrs"]
    assert published["selected_option_ref"] == option
    assert published["selected_token"] == "opaque"
    assert published["selected_ordinal"] == 0.0


def test_episode_rearm_reuses_one_bounded_state_and_automates():
    agent = _fresh()
    episode = _episode(agent)
    _episode_option(agent, episode, "impulse", 0, 0.9, -0.5)
    _episode_option(agent, episode, "grounded", 1, 0.2, 0.5)
    agent.tick()

    rows = [_request(agent, episode, epoch) for epoch in (1, 2, 3)]
    assert [row["selected_token"] for row in rows] == [
        "grounded", "grounded", "grounded",
    ]
    assert [row["decision_deepened"] for row in rows] == [1.0, 1.0, 0.0]
    assert rows[-1]["selected_via"] == "order0"
    assert rows[-1]["last_published_decision_epoch"] == 3.0
    assert len(list(agent.inner.neighbours(
        episode, "has_motor_decision_state"
    ))) == 1


def test_episode_empty_request_refuses_without_minting_a_choice():
    agent = _fresh()
    episode = _episode(agent)
    row = _request(agent, episode, 1)
    assert row["decision_status"] == "refused_no_options"
    assert row["decision_armed"] == 0.0
    assert row["last_opened_decision_epoch"] == 1.0
    assert "selected_token" not in row
    assert list(agent.inner.neighbours(
        episode, "has_motor_decision_state"
    )) == []


def test_episode_bridge_co_loads_with_embodied_sensorimotor_core():
    agent = WorldAdapter(seeds=(
        "embodied_sensorimotor_core",
        "motor_decision_collapse",
    ))
    assert len(list(agent.s.nodes("MotorDecisionPolicy"))) == 1


def test_bigville_decision_core_remains_compatible():
    from worlds.bigville_decision_world import BigvilleDecisionWorld

    world = BigvilleDecisionWorld([
        ("walk_away", 0.2, 0.5, 0),
        ("strike", 0.9, -0.5, 1),
    ])
    try:
        row = world.decide()
        assert row["cand"] == "strike"
        assert row["chosen"] == "walk_away"
        assert row["deepened"] == 1
    finally:
        world.close()
