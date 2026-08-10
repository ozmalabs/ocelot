"""The daemon's PyBullet humanoid body is a mechanical trial transducer."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import jabberwock_daemon as daemon  # noqa: E402
from domains.imagination_dispatch import scan_and_imagine  # noqa: E402
from domains.pybullet_humanoid_trial_transducer import (  # noqa: E402
    PyBulletHumanoidTrialTransducer,
)
from domains.pybullet_humanoid_world import HumanoidBodyConfiguration  # noqa: E402
from scripts.gen_embodied_learning_session_seed import manifest as learning_manifest  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"float crossed into graph evidence: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_integer_native(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_integer_native(nested)


def _selected_trial(agent):
    request = agent.s.add_node("EmbodiedExternalTrialRequest", {
        "status": "requested", "grounded": 1, "integer_native": 1,
        "output_authority": 0,
    })
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "integer_native": 1,
        # These are the body world's exact opaque tokens, not a semantic alias
        # such as "walk" or "tonic".
        "simulator_tokens": ["humanoid_actuator_001"],
        "simulator_weight_units": [1],
        "simulator_weight_scale_units": 1,
        "simulator_frames": 2,
        # The graph retains and projects the complete observed vector; this
        # program intentionally contains no axis/sign policy.
        "displacement_units_per_metre": 1000,
        "energy_units_per_joule": 1000,
        "load_units_per_newton": 1,
    })
    pose = agent.s.add_node("EmbodiedPoseAffordance", {"enabled": 1})
    scenario = agent.s.add_node("EmbodiedResetScenario", {
        "fixture_quarter_turn_x": 1,
        "fixture_quarter_turn_y": 0,
        "fixture_quarter_turn_z": 0,
    })
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 1})
    for source, edge_type, target in (
        (request, "enacts_embodied_motor_program", program),
        (request, "uses_embodied_pose_affordance", pose),
        (request, "uses_embodied_reset_scenario", scenario),
        (request, "pursues_goal", goal),
    ):
        _edge(agent, source, edge_type, target)
    return request, program, pose, scenario, goal


def _configuration():
    return HumanoidBodyConfiguration(
        time_step=1.0 / 240.0,
        gravity_acceleration=9.81,
        action_frames=1,
        settling_frames=1,
        joint_twitch_radians=0.085,
        maximum_joint_force=50.0,
        position_gain=0.3,
        velocity_gain=1.0,
    )


def _learning_session_agent():
    """Load the graph path under test without a Python session controller."""
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(
        manifest_for("counterfactual_experiment"), agent.agent
    )
    agent.inner.load_seed_manifest(learning_manifest(), agent.agent)
    return agent


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_real_pybullet_trial_enacts_exact_graph_program_and_publishes_integer_evidence():
    agent = WorldAdapter(seeds=())
    request, program, pose, scenario, goal = _selected_trial(agent)
    transducer = PyBulletHumanoidTrialTransducer(_configuration())
    try:
        transducer(agent, request)
        evidence = agent.inner.neighbours(
            request, "has_grounded_external_trial_evidence"
        )
        assert len(evidence) == 1
        evidence_node = evidence[0]
        attrs = agent.s.node(evidence_node)["attrs"]
        _assert_integer_native(attrs)
        assert attrs["grounded"] == 1
        assert attrs["measurement_frame_count"] == 2
        assert {"base_displacement_x_units", "base_displacement_y_units",
                "base_displacement_z_units",
                "proprioceptive_configuration_delta_units"} <= set(attrs)
        assert "goal_progress_units" not in attrs
        assert "proprioceptive_configuration_l1_units" not in attrs
        assert "measurement_axis" not in attrs
        assert "measurement_sign" not in attrs
        assert attrs["reset_quarter_turn_x"] == 1
        assert attrs["simulator_step_after"] - attrs["simulator_step_before"] == 2
        assert agent.inner.neighbours(
            evidence_node, "measures_embodied_motor_program"
        ) == [program]
        assert agent.inner.neighbours(
            evidence_node, "under_embodied_pose_affordance"
        ) == [pose]
        assert agent.inner.neighbours(
            evidence_node, "from_embodied_reset_scenario"
        ) == [scenario]
        assert agent.inner.neighbours(evidence_node, "measures_goal") == [goal]
        assert transducer.world.observe()["last_actuator_tokens"] == (
            "humanoid_actuator_001",
        )
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_daemon_passes_the_exact_selected_source_to_real_body_transducer():
    agent = WorldAdapter(seeds=())
    request, _program, _pose, _scenario, _goal = _selected_trial(agent)
    transducer = PyBulletHumanoidTrialTransducer(_configuration())
    state = daemon.DaemonState(agent, "test")
    state.embodied_trial_executor = transducer
    state.embodied_trial_closer = transducer.close
    host_request = agent.s.add_node("HostActionRequest", {
        "action": "embodied_trial", "status": "requested", "source": request,
        "urgency": 1, "residual": 1, "estimated_cost": 1, "deadline": 0,
    })
    try:
        assert daemon._execute_host_action_requests(state) == 1
        assert agent.s.node(host_request)["attrs"]["status"] == "done"
        assert len(agent.inner.neighbours(
            request, "has_grounded_external_trial_evidence"
        )) == 1
    finally:
        state.embodied_trial_closer()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_graph_authored_session_request_rehearses_schedules_and_learns_from_real_body():
    """The graph, not this test, creates the physical trial request.

    This joins the entire intended seam: the session selects an already
    graph-authored integer motor program, detached cognition closes first,
    the graph emits the external request, generic supervision schedules it,
    and the real world returns evidence that the graph retains.
    """
    agent = _learning_session_agent()
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    body = agent.s.add_node("EmbodiedBodySchema", {"morphology_epoch": 1})
    learning_world = agent.s.add_node("EmbodiedLearningWorld", {"world_epoch": 1})
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    goal = agent.s.add_node("Goal", {"status": "active", "order_n": 1})
    frontier = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {})
    profile = agent.s.add_node("ParetoProfile", {"dimension_count": 3})
    motor_episode = agent.s.add_node("EmbodiedMotorEpisode", {})
    hint = agent.s.add_node("EmbodiedMotorPrior", {})
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "integer_native": 1,
        "predicted_forward_units": 2,
        "predicted_vertical_units": 0,
        "predicted_energy_units": 3,
        "predicted_peak_load_units": 1,
        "experience_units": 4,
        # Exact opaque body command. Goal projection is graph-owned.
        "simulator_tokens": ["humanoid_actuator_001"],
        "simulator_weight_units": [1],
        "simulator_weight_scale_units": 1,
        "simulator_frames": 2,
        "displacement_units_per_metre": 1000,
        "energy_units_per_joule": 1000,
        "load_units_per_newton": 1,
    })
    pose = agent.s.add_node("EmbodiedPoseAffordance", {"enabled": 1})
    reset = agent.s.add_node("EmbodiedResetRequest", {"status": "requested"})
    scenario = agent.s.add_node("EmbodiedResetScenario", {
        "fixture_quarter_turn_x": 1,
        "fixture_quarter_turn_y": 0,
        "fixture_quarter_turn_z": 0,
    })
    for source, edge_type, target in (
        (agent.agent, "has_embodied_development_episode", episode),
        (episode, "has_embodied_body_schema", body),
        (episode, "has_embodied_learning_world", learning_world),
        (episode, "has_self_directed_learning_plan", plan),
        (plan, "has_selected_learning_plan_step", step),
        (plan, "has_learning_decision_profile", profile),
        (step, "pursues_goal", goal),
        (episode, "has_active_embodied_developmental_capability", frontier),
        (episode, "has_embodied_motor_episode", motor_episode),
        (motor_episode, "uses_embodied_motor_prior", hint),
        (motor_episode, "has_embodied_motor_program", program),
        (learning_world, "has_embodied_pose_affordance", pose),
        (episode, "has_active_embodied_reset_request", reset),
        (reset, "selects_embodied_reset_scenario", scenario),
    ):
        _edge(agent, source, edge_type, target)

    agent.tick()
    session = list(agent.s.nodes("EmbodiedLearningSession"))
    assert len(session) == 1
    session = session[0]
    rehearsal = agent.inner.neighbours(
        session, "has_counterfactual_embodied_trial"
    )
    assert len(rehearsal) == 1
    assert agent.s.node(rehearsal[0])["attrs"]["status"] == "counterfactual_running"
    assert not list(agent.s.nodes("EmbodiedExternalTrialRequest"))

    imagination_request = list(agent.s.nodes("ImagineRequest"))
    assert scan_and_imagine(agent) == imagination_request
    agent.tick()
    assert agent.s.node(rehearsal[0])["attrs"]["status"] == "counterfactual_done"
    external_requests = agent.inner.neighbours(
        session, "has_grounded_external_trial_request"
    )
    assert len(external_requests) == 1
    external = external_requests[0]
    assert agent.inner.neighbours(external, "enacts_embodied_motor_program") == [program]
    assert agent.inner.neighbours(external, "uses_embodied_pose_affordance") == [pose]
    assert agent.inner.neighbours(external, "uses_embodied_reset_scenario") == [scenario]

    daemon._ensure_supervisory_scheduler(agent)
    agent.tick()
    host = [node for node in agent.s.nodes("HostActionRequest")
            if agent.s.node(node)["attrs"].get("action") == "embodied_trial"]
    assert len(host) == 1
    assert agent.s.node(host[0])["attrs"]["source"] == external

    transducer = PyBulletHumanoidTrialTransducer(_configuration())
    state = daemon.DaemonState(agent, "test")
    state.embodied_trial_executor = transducer
    state.embodied_trial_closer = transducer.close
    try:
        assert daemon._execute_host_action_requests(state) == 1
        agent.tick()
        assert agent.s.node(host[0])["attrs"]["status"] == "done"
        assert agent.s.node(external)["attrs"]["status"] == "evidenced"
        evidence = agent.inner.neighbours(
            session, "has_grounded_external_trial_evidence"
        )
        assert len(evidence) == 1
        evidence_attrs = agent.s.node(evidence[0])["attrs"]
        _assert_integer_native(evidence_attrs)
        assert agent.inner.neighbours(
            evidence[0], "evidence_for_embodied_trial_request"
        ) == [external]
        candidates = agent.inner.neighbours(
            evidence[0], "published_as_pareto_candidate"
        )
        assert len(candidates) == 1
    finally:
        state.embodied_trial_closer()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_daemon_opt_in_attachment_uses_declared_external_mechanics_protocol():
    agent = WorldAdapter(seeds=())
    state = daemon.DaemonState(agent, "test")
    try:
        daemon.attach_pybullet_humanoid_trial_world(
            state,
            protocol_path=ROOT / "protocols" / "humanoid_developmental_smoke_v1.json",
            seed=7,
        )
        assert isinstance(state.embodied_trial_executor, PyBulletHumanoidTrialTransducer)
        assert state.embodied_trial_executor.seed == 7
        assert state.embodied_trial_closer is not None
    finally:
        if state.embodied_trial_closer is not None:
            state.embodied_trial_closer()


def test_semantic_motor_alias_cannot_be_interpreted_by_python():
    agent = WorldAdapter(seeds=())
    request, program, _pose, _scenario, _goal = _selected_trial(agent)
    # The adapter must not turn a semantic name into a hardware token.
    agent.s.set_attr(program, "simulator_tokens", ["tonic"])
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("PyBullet is an optional real-world transducer dependency")
    transducer = PyBulletHumanoidTrialTransducer(_configuration())
    try:
        with pytest.raises(ValueError, match="unknown humanoid actuator token"):
            transducer(agent, request)
        assert not agent.inner.neighbours(
            request, "has_grounded_external_trial_evidence"
        )
    finally:
        transducer.close()


# --- CARRIAGE PASSES THROUGH A WELD ------------------------------------------
#
# `_carried_by_effector_relations` used to map a joint's parent LINK straight to
# a channel and give up when that link was not itself actuated, so a rigidly
# welded intermediate SEVERED the chain. Measured on the MJCF humanoid: 12 of 33
# links are FIXED, costing nine of eighteen carriage edges and leaving five of
# twenty-one joint groups — including both joints standing on their travel stop
# — outside every chain, so they reached no limb and no settle at all.

from domains.pybullet_humanoid_trial_transducer import (  # noqa: E402
    _RIGID_JOINT_TYPE,
    _carried_by_effector_relations,
)

_REVOLUTE, _FIXED = 0, _RIGID_JOINT_TYPE


def _shape(links, actuators):
    return [["link", *row] for row in links] + [
        ["actuator", channel, joint] for channel, joint in actuators
    ]


def test_carriage_walks_through_a_rigid_weld():
    """joint 0 -actuated-, link 1 WELDED to it, joint 2 actuated beyond it.
    Channel 1 is carried by channel 0 even though its parent link is not a
    joint anything can command."""
    relations = _carried_by_effector_relations(_shape(
        links=[(0, -1, _REVOLUTE), (1, 0, _FIXED), (2, 1, _REVOLUTE)],
        actuators=[(0, 0), (1, 2)],
    ))
    assert relations == ((1, 0),)


def test_carriage_stops_at_a_joint_that_is_not_rigid():
    """A free hinge genuinely DECOUPLES. Treating any unactuated joint as
    transparent would claim a carriage relation the mechanism does not
    provide, so the walk must stop rather than reach past it."""
    relations = _carried_by_effector_relations(_shape(
        links=[(0, -1, _REVOLUTE), (1, 0, _REVOLUTE), (2, 1, _REVOLUTE)],
        actuators=[(0, 0), (1, 2)],   # joint 1 present but NOT actuated
    ))
    assert relations == ()


def test_carriage_walks_a_run_of_welds_and_stops_at_the_base():
    """Several welds in series still carry; a joint whose walk reaches the base
    without finding an actuated ancestor is a true root and gets no edge."""
    relations = _carried_by_effector_relations(_shape(
        links=[(0, -1, _REVOLUTE), (1, 0, _FIXED), (2, 1, _FIXED),
               (3, 2, _REVOLUTE), (4, -1, _FIXED), (5, 4, _REVOLUTE)],
        actuators=[(0, 0), (1, 3), (2, 5)],
    ))
    assert relations == ((1, 0),), "channel 2 walks to the base and is a root"


def test_carriage_without_a_published_type_keeps_the_direct_parent_reading():
    """Nothing is assumed rigid when the signature does not carry a type — the
    behaviour collapses to the original lookup rather than inventing carriage
    the host never reported."""
    relations = _carried_by_effector_relations(_shape(
        links=[(0, -1), (1, 0), (2, 1)],
        actuators=[(0, 0), (1, 2)],
    ))
    assert relations == ()


def test_carriage_survives_a_cycle_in_the_declared_parent_table():
    """A malformed signature must not hang the boundary."""
    relations = _carried_by_effector_relations(_shape(
        links=[(0, 1, _FIXED), (1, 0, _FIXED), (2, 0, _REVOLUTE)],
        actuators=[(0, 2)],
    ))
    assert relations == ()
