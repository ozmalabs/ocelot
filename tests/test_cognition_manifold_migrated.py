"""Fail-closed GWM manifold candidate bridge (P4.E1.2)."""
import json

from substrate_rs import _native
from scripts.gen_cognition_manifold_seed import OUT, build_seed
from substrate.world_adapter import WorldAdapter
from tests.test_generative_world_model_migrated import _model_fixture, _nodes, _perceive


def _boot(enabled=True):
    a = _native.Substrate()
    ag = a.add_node("Agent", {})
    for seed_id in ("default_mode_core", "generative_world_model", "thinking_budget"):
        manifest = json.loads((OUT.parent / f"{seed_id}.json").read_text())
        assert a.load_seed_manifest(manifest, ag).get("rules_skipped") == []
    assert a.load_seed_manifest(build_seed(), ag).get("rules_skipped") == []
    policy = a.nodes("CognitionManifoldPolicy")[0]
    episode = a.nodes("CognitionManifoldEpisode")[0]
    budget = a.nodes("ThinkingBudget")[0]
    a.set_attr(budget, "enabled", 1.0)
    a.set_attr(budget, "remaining", 4.0)
    a.set_attr(budget, "refill_per_epoch", 0.0)
    a.set_attr(budget, "last_refill_epoch", 1.0)
    modes = a.nodes("NetworkModeState")
    if modes:
        a.set_attr(modes[0], "epoch", 1.0)
    else:
        mode = a.add_node("NetworkModeState", {"epoch": 1.0, "mode": "awake"})
        a.add_edge(ag, "has_network_mode_state", mode)
    a.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    a.set_attr(policy, "future_manifold_projection_budget", 2.0)
    a.set_attr(policy, "future_manifold_physical_horizon", 2.0)
    a.set_attr(episode, "future_manifold_target", [[1.0], [2.0]])
    a.set_attr(episode, "future_manifold_bounds", [[0.5], [0.5]])
    return a, ag, policy, episode


def _tick(a):
    for _ in range(30):
        if not a.run_rules(10000):
            return
    raise AssertionError("cognition manifold did not reach a fixpoint")


def test_dependency_closure_and_generator_reproduction():
    assert json.loads(OUT.read_text()) == build_seed()
    a, _, _, _ = _boot(enabled=False)
    assert len(a.nodes("CognitionManifoldPolicy")) == 1
    assert a.nodes("CognitionManifoldCandidate") == []



def test_missing_model_unresolved():
    a, _, _, episode = _boot()
    _tick(a)
    attrs = a.node(episode)["attrs"]
    assert attrs["status"] == "unresolved"
    assert attrs["unresolved_reason"] == "missing_model_or_request"
    assert a.nodes("CognitionManifoldCandidate") == []



def test_model_owned_numeric_path_is_projected_with_residual_shape():
    a, _, _, episode = _boot()
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.1})
    transition = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-1",
        "model_id": "model-1", "model_epoch": 3,
        "future_manifold_values": [[1.0], [3.0]],
        "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]],
        "future_manifold_effort": [0.0, 0.0],
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    candidate = a.nodes("CognitionManifoldCandidate")[0]
    attrs = a.node(candidate)["attrs"]
    assert attrs["status"] == "audited"
    assert attrs["model_epoch"] == 3
    assert attrs["future_manifold_values"] == [[1.0], [3.0]]
    assert attrs["projection_shape"] is not None
    assert attrs["projection_resolved"] == 1.0
    assert attrs["projection_support"] == 1.0
    assert attrs["projection_loss"] > 0
    assert attrs["projection_horizon"] == 2
    # Candidate projection is evidence only; it never grounds the prediction.
    assert a.node(state)["attrs"].get("observation_status", "not_observed") == "not_observed"
    assert a.nodes("CognitionManifoldFeasibilityReceipt") == []


def test_complete_in_bounds_projection_mints_receipt():
    a, _, _, episode = _boot()
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.1})
    transition = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-feasible",
        "model_id": "model-feasible", "model_epoch": 7,
        "future_manifold_values": [[1.0], [2.0]], "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]], "future_manifold_effort": [0.0, 0.0],
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    candidate = a.nodes("CognitionManifoldCandidate")[0]
    receipt = a.nodes("CognitionManifoldFeasibilityReceipt")[0]
    attrs = a.node(receipt)["attrs"]
    assert attrs["status"] == "verified"
    assert attrs["model_id"] == "model-feasible"
    assert attrs["model_epoch"] == 7
    assert attrs["transition_id"] == "tr-feasible"
    assert attrs["candidate_version"] == attrs["projection_version"] == 1
    assert attrs["horizon"] == 2
    assert attrs["projection_loss"] == attrs["projection_information_loss"] == 0
    assert receipt in a.neighbours(candidate, "has_feasibility_receipt")
    assert candidate in a.neighbours(receipt, "verifies_candidate")
    assert transition in a.neighbours(receipt, "verifies_transition")



def test_symbolic_gwm_transition_does_not_claim_a_manifold_projection():
    a, _, _, episode = _boot()
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 1.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.2})
    transition = a.add_node("TransitionHypothesis", {
        "source_state_kind": "room", "action_kind": "turn",
        "successor_state_kind": "hall", "uncertainty": 0.2,
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    assert a.node(episode)["attrs"]["status"] == "unresolved"
    assert a.node(episode)["attrs"]["unresolved_reason"] == "no_resolved_numeric_gwm_candidate"
    candidate = a.nodes("CognitionManifoldCandidate")[0]
    assert a.node(candidate)["attrs"]["status"] == "unresolved_numeric_path"
    assert "projection_resolved" not in a.node(candidate)["attrs"]


def test_no_supplied_moves_uses_gwm_actions_and_records_unresolved_candidates():
    agent = WorldAdapter(seeds=("generative_world_model", "thinking_budget",
                                "cognition_manifold"))
    _, belief = _perceive(agent)
    request, _, _ = _model_fixture(agent, belief)
    policy = _nodes(agent, "CognitionManifoldPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    agent.tick()
    assert agent.s.node(request)["attrs"]["status"] == "completed"
    candidates = [agent.s.node(n)["attrs"] for n in _nodes(agent, "CognitionManifoldCandidate")]
    assert len(candidates) >= 2, "GWM model actions should produce multiple branch candidates"
    assert all(c["candidate_kind"] == "gwm_transition" for c in candidates)
    assert all(c["status"] == "unresolved_numeric_path" for c in candidates)
    assert all("future_manifold_values" not in c for c in candidates)
    episode = _nodes(agent, "CognitionManifoldEpisode")[0]
    assert agent.s.node(episode)["attrs"]["status"] == "unresolved"
    agent.close()


def test_refinement_request_debited_once_and_waits_for_model_response():
    a, ag, _, episode = _boot()
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.1})
    transition = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-refine",
        "model_id": "model-refine", "model_epoch": 4,
        "future_manifold_values": [[1.0], [3.0]],
        "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]],
        "future_manifold_effort": [0.0, 0.0],
        "refinement_requested": True,
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    candidate = a.nodes("CognitionManifoldCandidate")[0]
    request = a.nodes("ThinkingBudgetRequest")[0]
    budget = a.nodes("ThinkingBudget")[0]
    attrs = a.node(candidate)["attrs"]
    assert a.node(request)["attrs"]["status"] == "approved"
    assert a.node(request)["attrs"]["debited_epoch"] == 1.0
    assert attrs["status"] == "awaiting_model_refinement"
    assert a.node(budget)["attrs"]["remaining"] == 3.0
    _tick(a)
    assert len(a.nodes("ThinkingBudgetRequest")) == 1
    assert a.node(budget)["attrs"]["remaining"] == 3.0


def test_funded_model_response_creates_a_new_projection_version():
    a, _, _, episode = _boot()
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.1})
    source_transition = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-parent",
        "model_id": "model-versioned", "model_epoch": 4,
        "future_manifold_values": [[1.0], [3.0]], "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]], "future_manifold_effort": [0.0, 0.0],
        "refinement_requested": True,
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", source_transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    parent = a.nodes("CognitionManifoldCandidate")[0]
    assert a.node(parent)["attrs"]["status"] == "awaiting_model_refinement"
    response = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-refined",
        "model_id": "model-versioned", "model_epoch": 4, "uncertainty": 0.05,
        "future_manifold_values": [[1.0], [2.5]], "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]], "future_manifold_effort": [0.0, 0.0],
    })
    a.add_edge(parent, "has_refinement_transition", response)
    _tick(a)
    versions = sorted((a.node(n)["attrs"] for n in a.nodes("CognitionManifoldCandidate")),
                      key=lambda attrs: attrs["projection_version"])
    assert len(versions) == 2
    assert versions[0]["status"] == "refined"
    assert versions[1]["projection_version"] == 2
    assert versions[1]["parent_projection_version"] == 1
    assert versions[1]["status"] == "audited"
    assert versions[1]["projection_resolved"] == 1.0
    request = a.nodes("ThinkingBudgetRequest")[0]
    assert a.node(request)["attrs"]["status"] == "consumed"


def test_model_change_invalidates_cached_projection():
    a, _, _, episode = _boot()
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.1})
    transition = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-epoch",
        "model_id": "model-epoch", "model_epoch": 4,
        "future_manifold_values": [[1.0], [3.0]], "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]], "future_manifold_effort": [0.0, 0.0],
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    candidate = a.nodes("CognitionManifoldCandidate")[0]
    assert a.node(candidate)["attrs"]["status"] == "audited"
    a.set_attr(transition, "model_epoch", 5)
    _tick(a)
    assert a.node(candidate)["attrs"]["status"] == "stale"
    assert a.node(episode)["attrs"]["unresolved_reason"] == "model_epoch_changed"


def test_denied_refinement_is_terminal_and_cannot_retry():
    a, _, _, episode = _boot()
    budget = a.nodes("ThinkingBudget")[0]
    a.set_attr(budget, "remaining", 0.0)
    req = a.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    traj = a.add_node("PredictionTrajectory", {})
    state = a.add_node("PredictedBeliefState", {"uncertainty": 0.1})
    transition = a.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "tr-denied",
        "model_id": "model-denied", "model_epoch": 1,
        "future_manifold_values": [[1.0], [3.0]], "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]], "future_manifold_effort": [0.0, 0.0],
        "refinement_requested": True,
    })
    for src, edge, tgt in ((episode, "has_gwm_request", req),
                           (req, "has_prediction_trajectory", traj),
                           (traj, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        a.add_edge(src, edge, tgt)
    _tick(a)
    candidate = a.nodes("CognitionManifoldCandidate")[0]
    request = a.nodes("ThinkingBudgetRequest")[0]
    assert a.node(request)["attrs"]["status"] == "denied"
    assert a.node(candidate)["attrs"]["status"] == "refinement_denied"
    _tick(a)
    assert len(a.nodes("ThinkingBudgetRequest")) == 1
    assert a.node(budget)["attrs"]["remaining"] == 0.0
