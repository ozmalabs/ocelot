"""P20 observational acquisition preserves source and uncertainty boundaries."""
from evaluation.process_mastery.harness import Agent


def _agent():
    return Agent(extra_seeds=("thinking_budget", "social_process"), track_i=False,
                 policy_overrides={"SocialProcessPolicy": {"enabled": 1.0}},
                 budget={"enabled": 1.0, "remaining": 20.0,
                         "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})


def _episode(agent, *, coverage="complete", teacher=False):
    s, ag = agent.s, agent.ag
    model = s.add_node("ProcessSchema", {
        "name": "held-request-repair", "kind": "sequence", "domain": "social",
        "operator": "request", "binding": "repair", "params": ["seq", ["add", [1]]],
        "status": "active", "source_epoch": 4, "model_epoch": 7})
    s.add_edge(ag, "has_process_schema", model, {})
    attrs = {"episode_id": "observed-peer-1", "status": "observed",
             "source_kind": "witnessed_interaction", "observation_status": coverage,
             "interaction_kind": "request_repair", "owner_id": "learner",
             "actor_id": "peer", "source_epoch": 4, "model_epoch": 7,
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


def test_no_teacher_flag_needed():
    agent = _agent()
    _episode(agent, teacher=False)
    _tick(agent)
    assert len(agent.s.nodes("SocialProcessCandidate")) == 1


def test_hidden_step_not_invented():
    agent = _agent()
    _episode(agent, coverage="partial")
    _tick(agent)
    assert not agent.s.nodes("SocialProcessCandidate")


def test_other_success_is_not_own_receipt_or_grounding():
    agent = _agent()
    _episode(agent)
    _tick(agent)
    candidate = agent.s.nodes("SocialProcessCandidate")[0]
    assert not agent.s.nodes("OwnTrialReceipt")
    assert not agent.s.nodes("ActionAuthorization")
    assert not agent.s.nodes("SocialProcessSchema")
    assert agent.s.node(candidate)["attrs"]["status"] == "unverified_candidate"
