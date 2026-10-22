"""P20 observational acquisition preserves source and uncertainty boundaries."""
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.observed_sequence_execution import (
    execute_verified_observed_sequence, verify_observed_sequence_candidate,
)
from evaluation.process_mastery.target_learning_worlds import RequestRepairWorld


def _agent():
    return Agent(extra_seeds=("thinking_budget", "social_process", "process_schema",
                              "observed_sequence_learning"), track_i=False,
                 policy_overrides={"SocialProcessPolicy": {"enabled": 1.0},
                                   "ObservedSequenceLearningPolicy": {"enabled": 1.0}},
                 budget={"enabled": 1.0, "remaining": 20.0,
                         "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})


def _episode(agent, *, coverage="complete", teacher=False):
    s, ag = agent.s, agent.ag
    model = s.add_node("ProcessSchema", {
        "name": "held-request-repair", "kind": "sequence", "domain": "social",
        "operator": "request", "binding": "repair", "params": ["seq", ["add", [1]]],
        "status": "active", "source_epoch": 4, "model_epoch": 7, "frame_epoch": 9})
    s.add_edge(ag, "has_process_schema", model, {})
    repair = s.add_node("ProcessSchema", {
        "name": "held-repair", "kind": "sequence", "domain": "social",
        "operator": "repair", "params": ["seq", ["add", [1]]],
        "status": "active", "source_epoch": 4, "model_epoch": 7, "frame_epoch": 9})
    s.add_edge(ag, "has_process_schema", repair, {})
    attrs = {"episode_id": "observed-peer-1", "status": "observed",
             "source_kind": "witnessed_interaction", "observation_status": coverage,
             "interaction_kind": "request_repair", "owner_id": "learner",
             "actor_id": "peer", "source_epoch": 4, "model_epoch": 7,
             "frame_epoch": 9,
             "request_action": "request", "repair_action": "repair",
             "action_sequence": ["seq", ["request", "repair"]]}
    if teacher:
        attrs["teacher_id"] = "teacher"
    episode = s.add_node("SocialEpisode", attrs)
    s.add_edge(ag, "has_social_episode", episode, {})
    request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "social_process_observation", "episode_id": attrs["episode_id"],
        "source_key": attrs["episode_id"], "source_epoch": 4,
        "operation_id": "observe:peer:1", "status": "pending", "cost": 1.0})
    s.add_edge(ag, "has_social_process_request", request, {})
    s.add_edge(request, "draws_on_thinking_budget", s.nodes("ThinkingBudget")[0], {})
    seq_request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "observed_sequence_learning", "episode_id": attrs["episode_id"],
        "source_key": f"sequence:{attrs['episode_id']}", "source_epoch": 4,
        "operation_id": "observe-sequence:peer:1", "status": "approved",
        "debited_epoch": 10.0, "cost": 1.0})
    s.add_edge(ag, "has_thinking_budget_request", seq_request, {})
    s.add_edge(seq_request, "draws_on_thinking_budget", s.nodes("ThinkingBudget")[0], {})
    return episode, request


def _tick(agent):
    for _ in range(24):
        if not agent.s.tick(1000):
            return


def test_incidental_interaction_teaches_multistep_process_without_teacher_flag():
    agent = _agent()
    episode, _request = _episode(agent)
    _tick(agent)
    candidates = agent.s.nodes("SocialProcessCandidate")
    assert len(candidates) == 1
    attrs = agent.s.node(candidates[0])["attrs"]
    assert attrs["provenance"] == "incidental_witnessed_interaction"
    assert attrs["constraints"] == ["seq", ["request", "repair"]]
    assert "teacher_id" not in agent.s.node(episode)["attrs"]
    sequence_candidates = agent.s.nodes("ObservedProcessSequenceCandidate")
    assert len(sequence_candidates) == 1
    sequence_attrs = agent.s.node(sequence_candidates[0])["attrs"]
    assert sequence_attrs["action_sequence"] == ["seq", ["request", "repair"]]
    assert sequence_attrs["status"] == "unverified_candidate"
    assert sequence_attrs["source_ast_included"] is False


def test_no_teacher_flag_needed():
    agent = _agent()
    _episode(agent, teacher=False)
    _tick(agent)
    assert len(agent.s.nodes("SocialProcessCandidate")) == 1
    assert len(agent.s.nodes("ObservedProcessSequenceCandidate")) == 1


def test_hidden_step_not_invented():
    agent = _agent()
    _episode(agent, coverage="partial")
    _tick(agent)
    assert not agent.s.nodes("SocialProcessCandidate")
    assert not agent.s.nodes("ObservedProcessSequenceCandidate")


def test_other_success_is_not_own_receipt_or_grounding():
    agent = _agent()
    _episode(agent)
    _tick(agent)
    candidate = agent.s.nodes("SocialProcessCandidate")[0]
    assert not agent.s.nodes("OwnTrialReceipt")
    assert not agent.s.nodes("ActionAuthorization")
    assert not agent.s.nodes("SocialProcessSchema")
    assert agent.s.node(candidate)["attrs"]["status"] == "unverified_candidate"
    sequence_candidate = agent.s.nodes("ObservedProcessSequenceCandidate")[0]
    assert agent.s.node(sequence_candidate)["attrs"]["actor_outcome_is_own_trial"] is False
    assert agent.s.node(sequence_candidate)["attrs"]["status"] == "unverified_candidate"


def _verified_sequence_candidate(agent):
    _episode(agent)
    _tick(agent)
    candidate = agent.s.nodes("ObservedProcessSequenceCandidate")[0]
    request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "observed_sequence_validation",
        "candidate_id": agent.s.node(candidate)["attrs"]["candidate_id"],
        "source_key": "fresh-world-verification", "source_epoch": 4,
        "operation_id": "verify-observed-sequence", "status": "approved",
        "debited_epoch": 10.0, "cost": 2.0})
    agent.s.add_edge(agent.ag, "has_thinking_budget_request", request, {})
    agent.s.add_edge(request, "draws_on_thinking_budget",
                     agent.s.nodes("ThinkingBudget")[0], {})
    agent.s.add_edge(candidate, "has_verification_request", request, {})
    result = verify_observed_sequence_candidate(agent, candidate)
    assert result["status"] == "VERIFIED"
    assert agent.s.node(candidate)["attrs"]["status"] == "verified"
    return candidate


def test_sequence_candidate_requires_fresh_world_verification_then_own_trial():
    agent = _agent()
    candidate = _verified_sequence_candidate(agent)
    world = RequestRepairWorld(world_id="own-world", case_id="new-case")
    authorized = []
    result = execute_verified_observed_sequence(
        agent, candidate, world=world,
        authorize=lambda proposal: authorized.append(proposal["action"]) or True)
    assert result["status"] == "COMPLETED"
    assert world.solved and authorized == ["request", "repair"]
    own_receipts = agent.native.neighbours(candidate, "has_own_trial_receipt")
    assert len(own_receipts) == 2
    assert all(agent.s.node(node)["attrs"]["actual_own_trial"] for node in own_receipts)
    assert len(agent.s.nodes("ActionAuthorization")) == 2


def test_denied_sequence_step_stops_before_world_action():
    agent = _agent()
    candidate = _verified_sequence_candidate(agent)
    world = RequestRepairWorld(world_id="denied-world", case_id="case-denied")
    result = execute_verified_observed_sequence(
        agent, candidate, world=world,
        authorize=lambda proposal: proposal["action"] != "repair")
    assert result["status"] == "ABSTAIN"
    assert result["reason"] == "action_not_authorized"
    assert world.state == "requested"
    assert len(world.receipts) == 1
    assert len(agent.native.neighbours(candidate, "has_own_trial_receipt")) == 1
