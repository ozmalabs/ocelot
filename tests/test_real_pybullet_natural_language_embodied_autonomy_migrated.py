"""A real body proves language enters the graph-owned humanoid path."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


pytest.importorskip("substrate_rs")

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import jabberwock_daemon as daemon  # noqa: E402
from domains.imagination_dispatch import scan_and_imagine  # noqa: E402
from domains.pybullet_humanoid_trial_transducer import (  # noqa: E402
    PyBulletHumanoidTrialTransducer,
)
from domains.pybullet_humanoid_world import HumanoidBodyConfiguration  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


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


def _autonomous_agent():
    """Canonical dependency-closed boot; the test authors no cognition."""
    return WorldAdapter(seeds=(
        "embodied_motor_bootstrap",
        "embodied_instruction_goal",
        "comprehend_instruction",
        "learned_lexicon",
    ))


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_local_instruction_reaches_real_humanoid_body_via_autonomous_graph_path():
    """Language adopts a graph-selected goal; only real evidence can confirm it."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=23)
    state = daemon.DaemonState(agent, "test")
    state.embodied_trial_executor = transducer
    state.embodied_trial_closer = transducer.close
    try:
        # Mechanical body attachment is the sole test input besides the utterance.
        transducer.publish_body_world_capabilities(agent)
        agent.tick()

        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))
        assert len(episode) == 1
        episode = episode[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")
        capability = agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )
        motor_episode = agent.inner.neighbours(episode, "has_embodied_motor_episode")
        reset = agent.inner.neighbours(episode, "has_active_embodied_reset_request")
        assert len(plan) == len(capability) == len(motor_episode) == len(reset) == 1
        step = agent.inner.neighbours(plan[0], "has_selected_learning_plan_step")
        selected_goal = agent.inner.neighbours(step[0], "pursues_goal")
        selected_program = agent.inner.neighbours(
            motor_episode[0], "has_embodied_motor_program"
        )
        assert len(step) == len(selected_goal) == len(selected_program) == 1

        # ``walk`` is a held instruction-route concept; conversation is normal
        # mechanical text ingestion, not a Python-authored goal or command.
        reply = agent.converse(
            "Walk forward.", speech_act=agent.classify_speech_act("Walk forward.")
        )

        assert "attached embodied world" in reply.lower()
        assert "no world or faculty" not in reply.lower()

        interpretation = list(agent.s.nodes("InstructionInterpretation"))
        mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(interpretation) == len(mission) == 1
        assert agent.s.node(interpretation[0])["attrs"]["status"] == "verified"
        assert agent.s.node(interpretation[0])["attrs"]["local_grounded"] == 1
        assert agent.s.node(mission[0])["attrs"]["status"] == "accepted"
        assert agent.inner.neighbours(
            mission[0], "requires_embodied_capability"
        ) == capability
        mission_goal = agent.inner.neighbours(mission[0], "proposes_goal")
        assert len(mission_goal) == 1
        assert selected_goal[0] in agent.inner.neighbours(mission_goal[0], "has_subgoal")

        # The session's graph-authored counterfactual must close before it can
        # request the real body.  The dispatcher executes only that request.
        imagined = scan_and_imagine(agent)
        assert imagined
        agent.tick()
        session = agent.inner.neighbours(episode, "has_embodied_learning_session")
        assert len(session) == 1
        external = agent.inner.neighbours(session[0], "has_grounded_external_trial_request")
        assert len(external) == 1
        assert agent.inner.neighbours(external[0], "pursues_goal") == selected_goal
        assert agent.inner.neighbours(
            external[0], "enacts_embodied_motor_program"
        ) == selected_program
        # The request is not merely a contemporaneous episode request: the
        # instruction mission adopts this exact graph-selected request.
        assert agent.inner.neighbours(
            mission[0], "has_embodied_mission_trial_request"
        ) == external
        assert agent.inner.neighbours(
            external[0], "for_embodied_instruction_goal"
        ) == mission_goal

        daemon._ensure_supervisory_scheduler(agent)
        agent.tick()
        hosts = [
            host for host in agent.s.nodes("HostActionRequest")
            if agent.s.node(host)["attrs"].get("action") == "embodied_trial"
            and agent.s.node(host)["attrs"].get("status") == "requested"
        ]
        assert len(hosts) == 1
        assert agent.s.node(hosts[0])["attrs"]["source"] == external[0]
        assert daemon._execute_host_action_requests(state) >= 1
        agent.tick()

        evidence = agent.inner.neighbours(
            external[0], "has_grounded_external_trial_evidence"
        )
        receipt = agent.inner.neighbours(
            external[0], "has_embodied_learning_trial_receipt"
        )
        assert len(evidence) == len(receipt) == 1
        assert agent.inner.neighbours(
            session[0], "has_causal_embodied_learning_receipt"
        ) == receipt
        assert agent.inner.neighbours(
            episode, "has_embodied_development_receipt"
        ) == receipt
        assert agent.inner.neighbours(
            receipt[0], "grounded_in_external_trial_evidence"
        ) == evidence
        assert agent.inner.neighbours(
            receipt[0], "caused_by_embodied_motor_program"
        ) == selected_program
        confirmation = agent.inner.neighbours(
            mission[0], "requires_embodied_goal_confirmation"
        )
        assert len(confirmation) == 1
        assert agent.inner.neighbours(
            confirmation[0], "has_mission_bound_embodied_receipt"
        ) == receipt
        assert agent.inner.neighbours(
            receipt[0], "grounds_embodied_instruction_goal"
        ) == mission

        # Honesty gate: a real non-positive trial stays accepted; confirmation
        # is possible only when its receipt records positive measured progress.
        mission_attrs = agent.s.node(mission[0])["attrs"]
        progress = agent.s.node(receipt[0])["attrs"]["goal_progress_units"]
        assert mission_attrs["status"] in {"accepted", "confirmed"}
        if mission_attrs["status"] == "confirmed":
            assert progress > 0
            assert agent.inner.neighbours(
                confirmation[0], "grounded_in_embodied_receipt"
            ) == receipt
        else:
            assert progress <= 0

        # A receipt may release one graph-authored follow-on (reset/rehearsal
        # bookkeeping). Once that causal consequence settles, the historical
        # receipt must not be re-read as a new observation by every bounded
        # daemon quantum. This guards the episode receipt watermark that
        # prevents unbounded Pareto re-selection/node growth.
        agent.tick(max_steps=100)
        settled_nodes = agent.s.node_count()
        settled_decisions = agent.s.node(plan[0])["attrs"]["decision_count"]
        settled_profiles = len(list(agent.s.nodes("ParetoProfile")))
        for _ in range(3):
            assert agent.tick(max_steps=100) == 0
            assert agent.s.node_count() == settled_nodes
            assert agent.s.node(plan[0])["attrs"]["decision_count"] == settled_decisions
            assert len(list(agent.s.nodes("ParetoProfile"))) == settled_profiles
    finally:
        state.embodied_trial_closer()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_async_ingress_admits_instruction_rules_then_publishes_graph_reply():
    """A transport turn is facts first; graph admission owns its completion."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=47)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        session = agent.inner.neighbours(
            episode, "has_embodied_learning_session"
        )[0]
        baseline_trial_seq = agent.s.node(session)["attrs"]["trial_seq"]

        text = "Walk the humanoid forward."
        mid = agent.ingest_turn(text, speech_act=agent.classify_speech_act(text))

        # Ingress never settles cognition or fabricates a transport reply.
        assert agent.graph_turn_reply(mid) is None
        assert not list(agent.s.nodes("InstructionInterpretation"))
        assert not list(agent.s.nodes("EmbodiedInstructionGoalProposal"))

        # The daemon invokes this same budgeted graph admission for pending
        # turns.  It is not ``converse`` and it does not author a motor route.
        assert agent.comprehend() > 0
        reply = agent.graph_turn_reply(mid)
        assert reply is not None
        assert "attached embodied world" in reply.lower()

        interpretation = list(agent.s.nodes("InstructionInterpretation"))
        mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(interpretation) == len(mission) == 1
        assert agent.s.node(interpretation[0])["attrs"]["status"] == "verified"
        assert agent.s.node(mission[0])["attrs"]["status"] == "accepted"
        assert agent.s.node(mission[0])["attrs"]["baseline_trial_seq"] == baseline_trial_seq
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_verified_instruction_reactivates_lowest_ordinal_ready_capability_once():
    """An instruction repairs withdrawal by selecting the lowest ready step."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=29)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
        capability = agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )[0]
        step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
        higher_steps = [candidate for candidate in agent.inner.neighbours(
            plan, "has_learning_plan_step"
        ) if candidate != step]
        assert higher_steps
        higher_step = min(
            higher_steps,
            key=lambda candidate: agent.s.node(candidate)["attrs"]["ordinal"],
        )
        higher_capability = agent.inner.neighbours(
            higher_step, "plans_learning_capability"
        )[0]

        # This simulates the generic supervisor's evidence-preserving release.
        # No test authors a replacement goal, capability, program, or command.
        agent.inner.remove_edge_unchecked(
            episode, "has_active_embodied_developmental_capability", capability
        )
        agent.inner.remove_edge_unchecked(
            plan, "has_selected_learning_plan_step", step
        )
        agent.inner.set_attr(capability, "status", "available")
        agent.inner.set_attr(step, "status", "ready")
        agent.inner.set_attr(higher_capability, "status", "available")
        agent.inner.set_attr(higher_step, "status", "ready")

        reply = agent.converse(
            "Walk forward.", speech_act=agent.classify_speech_act("Walk forward.")
        )

        assert "attached embodied world" in reply.lower()
        assert agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        ) == [capability]
        assert agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        ) == [step]
        mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(mission) == 1
        assert agent.s.node(mission[0])["attrs"]["status"] == "accepted"
        assert agent.inner.neighbours(
            mission[0], "requires_embodied_capability"
        ) == [capability]

        # ``converse`` settles the instruction fixed point. A further cognitive
        # cycle may independently check in and withdraw the temporary lease,
        # but cannot duplicate the mission.
        agent.tick()
        assert len(list(agent.s.nodes("EmbodiedInstructionGoalProposal"))) == 1
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_verified_instruction_honestly_abstains_when_no_ready_capability_exists():
    """Understanding remains visible when the graph has no motor authority."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=31)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
        capability = agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )[0]
        step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
        agent.inner.remove_edge_unchecked(
            episode, "has_active_embodied_developmental_capability", capability
        )
        agent.inner.remove_edge_unchecked(
            plan, "has_selected_learning_plan_step", step
        )
        agent.inner.set_attr(capability, "status", "unavailable")
        agent.inner.set_attr(step, "status", "blocked")

        reply = agent.converse(
            "Walk forward.", speech_act=agent.classify_speech_act("Walk forward.")
        )
        agent.tick()

        assert "no ready developmental capability" in reply.lower()
        mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(mission) == 1
        attrs = agent.s.node(mission[0])["attrs"]
        assert attrs["status"] == "abstained"
        assert attrs["abstention_reason"] == (
            "no_ready_embodied_developmental_capability"
        )
        assert not agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )
        assert not agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        )
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_existing_active_pair_creates_no_duplicate_instruction_mission_or_edges():
    """An already selected route is adopted once, not multiplied per tick."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=35)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
        capability = agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )[0]
        step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]

        reply = agent.converse(
            "Walk forward.", speech_act=agent.classify_speech_act("Walk forward.")
        )
        assert "attached embodied world" in reply.lower()
        # A second settle cannot recreate the same proposal or parallel edges.
        agent.tick()
        missions = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(missions) == 1
        assert len(agent.inner.neighbours(
            missions[0], "requires_embodied_capability"
        )) == 1
        # The supervisor may subsequently release a lease; if it has not, the
        # sole selected edge remains the original pair, never a duplicate.
        assert len(agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )) <= 1
        assert len(agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        )) <= 1
        assert capability not in agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        ) or step in agent.inner.neighbours(plan, "has_selected_learning_plan_step")
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_verified_instruction_renews_exact_meta_suspended_supervisory_frontier():
    """Top-down intent restarts a held process, without inventing a route."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=41)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
        capability = agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        )[0]
        step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
        process = agent.inner.neighbours(episode, "has_cognitive_process")[0]
        policy = agent.inner.neighbours(
            process, "governed_by_cognitive_supervision_policy"
        )[0]

        agent.inner.remove_edge_unchecked(
            episode, "has_active_embodied_developmental_capability", capability
        )
        agent.inner.remove_edge_unchecked(
            plan, "has_selected_learning_plan_step", step
        )
        agent.inner.set_attr(capability, "status", "meta_suspended")
        agent.inner.set_attr(step, "status", "meta_suspended")
        agent.inner.set_attr(process, "status", "replan_required")
        agent.inner.set_attr(process, "continuation_authority", 0)
        agent.inner.set_attr(policy, "enabled", 0)

        reply = agent.converse(
            "Walk forward.", speech_act=agent.classify_speech_act("Walk forward.")
        )

        assert "attached embodied world" in reply.lower()
        mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(mission) == 1
        assert agent.s.node(mission[0])["attrs"]["status"] == "accepted"
        assert agent.inner.neighbours(
            episode, "has_active_embodied_developmental_capability"
        ) == [capability]
        assert agent.inner.neighbours(
            plan, "has_selected_learning_plan_step"
        ) == [step]
        assert agent.s.node(process)["attrs"]["status"] == "monitoring"
        assert agent.s.node(process)["attrs"]["continuation_authority"] == 1
        assert agent.s.node(policy)["attrs"]["enabled"] == 1
        assert agent.s.node(process)["attrs"]["baseline_effort_units"] == (
            agent.s.node(step)["attrs"]["evidence_spent_units"]
        )
        assert agent.s.node(process)["attrs"]["checkin_count"] >= 1
    finally:
        transducer.close()


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet is an optional real-world transducer dependency",
)
def test_instruction_mission_cannot_adopt_historical_request_or_receipt():
    """The proposal's immutable trial frontier excludes old same-goal work."""
    agent = _autonomous_agent()
    transducer = PyBulletHumanoidTrialTransducer(_configuration(), seed=37)
    try:
        transducer.publish_body_world_capabilities(agent)
        agent.tick()
        episode = list(agent.s.nodes("EmbodiedDevelopmentEpisode"))[0]
        session = agent.inner.neighbours(
            episode, "has_embodied_learning_session"
        )[0]
        plan = agent.inner.neighbours(episode, "has_self_directed_learning_plan")[0]
        step = agent.inner.neighbours(plan, "has_selected_learning_plan_step")[0]
        goal = agent.inner.neighbours(step, "pursues_goal")[0]

        # An already-closed, same-goal trial is deliberately present before
        # language arrives.  It must not become the later mission's evidence.
        historical_request = agent.s.add_node("EmbodiedExternalTrialRequest", {
            "status": "closed", "attempt_ordinal": 1,
            "grounded": 1, "integer_native": 1,
        })
        historical_receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
            "status": "closed", "development_receipt_closed": 1,
            "grounded": 1, "causal_closed": 1, "integer_native": 1,
        })
        agent.inner.add_edge_unchecked(
            session, "has_grounded_external_trial_request", historical_request
        )
        agent.inner.add_edge_unchecked(historical_request, "pursues_goal", goal)
        agent.inner.add_edge_unchecked(
            historical_request, "has_embodied_learning_trial_receipt", historical_receipt
        )
        agent.inner.set_attr(session, "trial_seq", 1)

        agent.converse(
            "Walk forward.", speech_act=agent.classify_speech_act("Walk forward.")
        )
        agent.tick()

        mission = list(agent.s.nodes("EmbodiedInstructionGoalProposal"))
        assert len(mission) == 1
        assert agent.s.node(mission[0])["attrs"]["baseline_trial_seq"] == 1
        assert not agent.inner.neighbours(
            mission[0], "has_embodied_mission_trial_request"
        )
        confirmation = agent.inner.neighbours(
            mission[0], "requires_embodied_goal_confirmation"
        )
        assert len(confirmation) == 1
        assert not agent.inner.neighbours(
            confirmation[0], "has_mission_bound_embodied_receipt"
        )
        assert agent.s.node(mission[0])["attrs"]["status"] == "accepted"

        # A *later* request for the mission's adopted subgoal crosses the
        # immutable baseline and is therefore the only admissible provenance.
        root = agent.inner.neighbours(mission[0], "proposes_goal")[0]
        adopted = [candidate for candidate in agent.inner.neighbours(
            root, "has_subgoal"
        ) if candidate != historical_receipt]
        developmental_goal = next(
            candidate for candidate in adopted
            if agent.s.node(candidate)["attrs"].get("kind")
            not in {"enact_embodied_capability", "verify_embodied_receipt"}
        )
        post_request = agent.s.add_node("EmbodiedExternalTrialRequest", {
            "status": "closed", "attempt_ordinal": 2,
            "grounded": 1, "integer_native": 1,
        })
        post_receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
            "status": "closed", "development_receipt_closed": 1,
            # The mission's confirmation rule requires a later *positive*
            # receipt as well as the new capability success unit.  This
            # fixture is the valid post-baseline confirmation datum, not
            # merely a closed historical receipt.
            "success_delta_units": 1,
            "grounded": 1, "causal_closed": 1, "integer_native": 1,
        })
        agent.inner.add_edge_unchecked(
            session, "has_grounded_external_trial_request", post_request
        )
        agent.inner.add_edge_unchecked(post_request, "pursues_goal", developmental_goal)
        agent.inner.add_edge_unchecked(
            post_request, "has_embodied_learning_trial_receipt", post_receipt
        )
        selected_capability = agent.inner.neighbours(
            mission[0], "requires_embodied_capability"
        )[0]
        # The session rule's write, simulated. Measured progress moved off
        # `success_count` on 2026-08-07 -- that attribute is the developmental
        # CRITERION's, and mission confirmation is a delta test over the
        # world's measured progress.
        agent.inner.set_attr(selected_capability, "positive_progress_count", 1)
        agent.tick()

        assert agent.inner.neighbours(
            mission[0], "has_embodied_mission_trial_request"
        ) == [post_request]
        assert agent.inner.neighbours(
            confirmation[0], "has_mission_bound_embodied_receipt"
        ) == [post_receipt]
        assert agent.s.node(confirmation[0])["attrs"]["status"] == "confirmed"
    finally:
        transducer.close()
