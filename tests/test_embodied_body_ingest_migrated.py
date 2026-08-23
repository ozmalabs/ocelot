"""Focused gates for mechanical body ingestion and graph recognition."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from domains.pybullet_humanoid_trial_transducer import (  # noqa: E402
    PyBulletHumanoidTrialTransducer,
)
from domains.pybullet_humanoid_world import HumanoidBodyConfiguration  # noqa: E402
import jabberwock_daemon as daemon  # noqa: E402
from scripts.gen_embodied_body_ingest_seed import manifest  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


SEED = ROOT / "seeds" / "embodied_body_ingest.json"


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"float crossed into cognitive graph: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_integer_native(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_integer_native(nested)


class _MechanicalHumanoidWorld:
    """An I/O fixture, intentionally free of policy or graph inspection."""

    def body_shape_signature(self):
        return (
            ("body", 7, 3, 2),
            ("link", 0, -1, 0),
            ("link", 1, 0, 0),
            ("link", 2, 1, 0),
            ("actuator", 0, 0, 1, 1, 0, 1, 0, 1),
            ("actuator", 1, 1, 1, 1, 0, 1, 0, 1),
            ("actuator", 2, 2, 1, 1, 0, 1, 0, 1),
        )

    def body_capability_signature(self):
        return (
            ("articulated_body", 1), ("link_count", 8),
            ("actuator_count", 3), ("distal_support_channel_count", 2),
        )

    def actuator_options(self):
        return (
            {"token": "opaque_000", "actuator_group": -1.0, "tonic_default": 1.0},
            {"token": "opaque_001", "actuator_group": 0.0, "tonic_default": 0.0},
            {"token": "opaque_002", "actuator_group": 1.0, "tonic_default": 0.0},
        )


def _mechanical_transducer():
    """Install a fake simulator resource without constructing cognition."""
    transducer = object.__new__(PyBulletHumanoidTrialTransducer)
    object.__setattr__(
        transducer, "configuration",
        SimpleNamespace(
            asset="opaque://fixture", maximum_joint_force=50.0,
            settling_frames=17,
            initial_base_quarter_turns=(1, -1, 0),
        ),
    )
    object.__setattr__(transducer, "seed", 11)
    object.__setattr__(transducer, "world", _MechanicalHumanoidWorld())
    return transducer


def _agent():
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def _development_agent():
    """Load existing graph faculties; no Python episode/goal construction."""
    agent = WorldAdapter(seeds=())
    for seed_id in (
        "cognitive_pareto", "embodied_development", "embodied_motor_bootstrap",
    ):
        agent.inner.load_seed_manifest(manifest_for(seed_id), agent.agent)
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def test_seed_is_reproducible_integer_native_and_only_recognizes_situation():
    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    _assert_integer_native(generated)
    assert generated["depends_on"] == ["embodied_learning_session"]
    serialized = json.dumps(generated)
    for forbidden in ("EmbodiedMotorProgram", "EmbodiedExternalTrialRequest", "Goal"):
        assert forbidden not in serialized
    for required in (
        "EmbodiedRawBodyObservation", "EmbodiedOpaqueActuatorAffordance",
        "EmbodiedWorldCapability", "EmbodiedSimulatorConnection",
        "EmbodiedDevelopmentEpisode",
    ):
        assert required in serialized


def test_raw_mechanical_facts_become_one_situated_environment_in_the_graph():
    agent = _agent()
    _mechanical_transducer().publish_body_world_capabilities(agent)

    raw_bodies = list(agent.s.nodes("EmbodiedRawBodyObservation"))
    connections = list(agent.s.nodes("EmbodiedSimulatorConnection"))
    capabilities = list(agent.s.nodes("EmbodiedWorldCapability"))
    affordances = list(agent.s.nodes("EmbodiedOpaqueActuatorAffordance"))
    assert len(raw_bodies) == len(connections) == 1
    assert len(capabilities) == 3
    raw_interface = list(agent.s.nodes("EmbodiedRawMotorInterface"))
    raw_projections = list(agent.s.nodes("EmbodiedRawMeasurementProjection"))
    assert len(raw_interface) == 1
    assert {(agent.s.node(node)["attrs"]["axis"],
             agent.s.node(node)["attrs"]["sign"])
            for node in raw_projections} == {
        (axis, sign) for axis in range(3) for sign in (-1, 1)
    }
    interface_attrs = agent.s.node(raw_interface[0])["attrs"]
    assert interface_attrs["minimum_actuation_frames"] == 1
    assert interface_attrs["maximum_observation_horizon_frames"] == 17
    assert interface_attrs["simulator_weight_scale_units"] == 1
    assert interface_attrs["minimum_nonzero_weight_units"] == 1
    assert interface_attrs["maximum_joint_force_units"] == 50
    assert [agent.s.node(node)["attrs"]["opaque_token"] for node in affordances] == [
        "opaque_000", "opaque_001", "opaque_002",
    ]
    for node in (*raw_bodies, *connections, *capabilities, *affordances):
        attrs = agent.s.node(node)["attrs"]
        assert attrs["grounded"] == 1
        assert attrs["integer_native"] == 1
        _assert_integer_native(attrs)

    agent.tick()
    body = list(agent.s.nodes("EmbodiedBodySchema"))
    world = list(agent.s.nodes("EmbodiedLearningWorld"))
    pose = list(agent.s.nodes("EmbodiedPoseAffordance"))
    episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))
    contract = list(agent.s.nodes("EmbodiedMotorBootstrapContract"))
    assert len(body) == len(world) == len(pose) == len(episode) == len(contract) == 1
    assert agent.s.node(episode[0])["attrs"]["status"] == "situated_ready"
    assert agent.s.node(episode[0])["attrs"]["development_learning_active"] == 1
    assert agent.s.node(episode[0])["attrs"]["embodiment_reset_available"] == 1
    assert agent.s.node(body[0])["attrs"]["morphology_epoch"] == 1
    assert agent.s.node(body[0])["attrs"]["observation_event_ordinal"] == 1
    assert agent.s.node(raw_bodies[0])["attrs"]["observation_event_ordinal"] == 1
    assert agent.s.node(connections[0])["attrs"]["attachment_event_ordinal"] == 1
    assert agent.inner.neighbours(
        body[0], "has_opaque_embodied_actuator_affordance"
    ) == affordances
    raw_topology = list(agent.s.nodes("EmbodiedRawEffectorTopologyRelation"))
    assert [(agent.s.node(node)["attrs"]["source_group_ordinal"],
             agent.s.node(node)["attrs"]["target_group_ordinal"])
            for node in raw_topology] == [(0, 1), (1, 0)]
    assert agent.inner.neighbours(
        body[0], "has_opaque_embodied_effector_topology_relation"
    ) == raw_topology
    assert agent.inner.neighbours(episode[0], "has_embodied_body_schema") == body
    assert agent.inner.neighbours(episode[0], "has_embodied_learning_world") == world
    assert agent.inner.neighbours(world[0], "has_embodied_pose_affordance") == pose
    scenarios = agent.inner.neighbours(episode[0], "has_embodied_reset_scenario")
    assert len(scenarios) == 1
    scenario_attrs = agent.s.node(scenarios[0])["attrs"]
    assert scenario_attrs["target_goal"] == "any"
    assert tuple(scenario_attrs[f"fixture_quarter_turn_{axis}"]
                 for axis in ("x", "y", "z")) == (1, -1, 0)
    assert agent.inner.neighbours(world[0], "has_embodied_motor_bootstrap_contract") == contract
    projections = agent.inner.neighbours(
        contract[0], "has_embodied_measurement_projection"
    )
    assert {(agent.s.node(node)["attrs"]["axis"],
             agent.s.node(node)["attrs"]["sign"])
            for node in projections} == {
        (axis, sign) for axis in range(3) for sign in (-1, 1)
    }
    assert not list(agent.s.nodes("Goal"))
    assert not list(agent.s.nodes("EmbodiedMotorProgram"))
    assert not list(agent.s.nodes("EmbodiedExternalTrialRequest"))


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional external body adapter",
)
def test_real_pybullet_attachment_publishes_integer_only_body_and_world_facts():
    configuration = HumanoidBodyConfiguration(
        time_step=1.0 / 240.0,
        gravity_acceleration=9.81,
        action_frames=1,
        settling_frames=1,
        joint_twitch_radians=0.085,
        maximum_joint_force=50.0,
        position_gain=0.3,
        velocity_gain=1.0,
    )
    agent = _agent()
    transducer = PyBulletHumanoidTrialTransducer(configuration, seed=5)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        raw_body = list(agent.s.nodes("EmbodiedRawBodyObservation"))
        assert len(raw_body) == 1
        raw_attrs = agent.s.node(raw_body[0])["attrs"]
        _assert_integer_native(raw_attrs)
        assert raw_attrs["actuator_count"] == len(list(agent.s.nodes(
            "EmbodiedOpaqueActuatorAffordance"
        )))
        assert len(list(agent.s.nodes("EmbodiedDevelopmentEpisode"))) == 1
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional external body adapter",
)
def test_opt_in_daemon_attachment_ingests_before_the_graph_recognizes_the_body():
    agent = _agent()
    state = daemon.DaemonState(agent, "test")
    try:
        daemon.attach_pybullet_humanoid_trial_world(
            state,
            protocol_path=ROOT / "protocols" / "humanoid_developmental_smoke_v1.json",
            seed=9,
        )
        assert len(list(agent.s.nodes("EmbodiedSimulatorConnection"))) == 1
        assert len(list(agent.s.nodes("EmbodiedRawBodyObservation"))) == 1
        assert len(list(agent.s.nodes("EmbodiedOpaqueActuatorAffordance"))) > 0
        # The daemon has only ingested world observations. The ordinary Rust
        # graph tick decides that those observations are an environment.
        assert not list(agent.s.nodes("EmbodiedDevelopmentEpisode"))
        agent.tick()
        assert len(list(agent.s.nodes("EmbodiedDevelopmentEpisode"))) == 1
    finally:
        if state.embodied_trial_closer is not None:
            state.embodied_trial_closer()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional external body adapter",
)
def test_real_attached_body_activates_existing_development_and_graph_selects_reset():
    """The body adapter contributes only observed mechanics.

    Existing developmental and motor-bootstrap rules create/select the active
    capability and author/select the reset request.  This test intentionally
    adds no Goal, plan, capability, program, scenario or request itself.
    """
    configuration = HumanoidBodyConfiguration(
        time_step=1.0 / 240.0,
        gravity_acceleration=9.81,
        action_frames=1,
        settling_frames=1,
        joint_twitch_radians=0.085,
        maximum_joint_force=50.0,
        position_gain=0.3,
        velocity_gain=1.0,
        initial_base_quarter_turns=(1, 0, 0),
    )
    agent = _development_agent()
    transducer = PyBulletHumanoidTrialTransducer(configuration, seed=13)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episodes = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))
        assert len(episodes) == 1
        episode = episodes[0]
        assert agent.s.node(episode)["attrs"]["development_learning_active"] == 1
        assert agent.s.node(episode)["attrs"]["embodiment_reset_available"] == 1
        assert len(agent.inner.neighbours(
            episode, "has_embodied_developmental_capability"
        )) == 27
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")
        active = agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )
        scenarios = agent.inner.neighbours(episode, "has_embodied_reset_scenario")
        active_requests = agent.inner.neighbours(
            episode, "has_active_embodied_reset_request"
        )
        requests = agent.inner.neighbours(
            episode, "has_embodied_reset_request"
        )
        assert len(plan) == len(active) == len(scenarios) == len(requests) == 1
        assert active_requests == []
        selected_step = agent.inner.neighbours(
            plan[0], "has_selected_learning_plan_step"
        )
        assert len(selected_step) == 1
        request_attrs = agent.s.node(requests[0])["attrs"]
        assert request_attrs["cause"] == "initial_situated_experiment"
        assert request_attrs["reinstantiation_spec_ready"] == 1
        assert request_attrs["status"] == "initial_fixture_established"
        assert agent.s.node(episode)["attrs"][
            "initial_situated_experiment_established"
        ] == 1
        assert agent.inner.neighbours(
            requests[0], "selects_embodied_reset_scenario"
        ) == scenarios
        scenario_attrs = agent.s.node(scenarios[0])["attrs"]
        assert scenario_attrs["target_goal"] == "any"
        assert scenario_attrs["fixture_quarter_turn_x"] == 1
    finally:
        transducer.close()
