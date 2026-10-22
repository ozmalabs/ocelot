"""P12.01 source/interface fixtures, not a runtime imitation claim.

P12.02 will replace these boundary fixtures with native graph-rule lifecycle
tests. For now they make attribution, missingness, body mapping and the
non-teacher observation route explicit at the world-event boundary.
"""
from __future__ import annotations


def _episode(*, source_kind="witnessed_interaction", actor="peer",
             learner="agent-root", actor_body="peer-body",
             learner_body="agent-body", observed_actions=None,
             coverage=None, body_map=None):
    return {
        "schema_version": 1,
        "episode_id": "episode-1",
        "source_epoch": 4,
        "owner_id": learner,
        "observer_id": learner,
        "actor_id": actor,
        "actor_body_id": actor_body,
        "learner_body_id": learner_body,
        "source_kind": source_kind,
        "observed_actions": observed_actions or [],
        "coverage": coverage or {"status": "complete", "visible_orders": [0]},
        "body_map": body_map,
    }


def test_observed_actor_not_self():
    episode = _episode(observed_actions=[{"order": 0, "actor_id": "peer",
                                          "action": "press", "event_id": "event-0"}])
    event = episode["observed_actions"][0]
    assert event["actor_id"] == episode["actor_id"]
    assert event["actor_id"] != episode["owner_id"]
    assert episode["source_kind"] == "witnessed_interaction"


def test_missing_step_unknown():
    episode = _episode(
        observed_actions=[{"order": 0, "actor_id": "peer", "action": "open"}],
        coverage={"status": "partial", "visible_orders": [0],
                  "missing_orders": [1], "missing_means": "unknown"})
    assert episode["coverage"]["missing_means"] == "unknown"
    assert [row["order"] for row in episode["observed_actions"]] == [0]


def test_body_mismatch_blocks_trial():
    episode = _episode(body_map={"source_body_id": "other-body",
                                 "target_body_id": "agent-body",
                                 "source_epoch": 4, "target_epoch": 2,
                                 "status": "mismatch"})
    mapping = episode["body_map"]
    assert mapping["source_body_id"] != episode["actor_body_id"]
    assert mapping["status"] != "verified"


def test_no_directed_teaching_required():
    episode = _episode(source_kind="witnessed_interaction")
    assert episode["source_kind"] == "witnessed_interaction"
    assert "teacher_id" not in episode
    assert "teaching_intent" not in episode


def _agent(*, enabled=True):
    from evaluation.process_mastery.harness import Agent
    agent = Agent(extra_seeds=("imitation",),
                  policy_overrides={"ImitationPolicy": {"enabled": 1.0 if enabled else 0.0}})
    return agent


def _observed_candidate(agent, episode_id, binding_id, *, map_status="verified",
                        observation_status="complete", actor_id="peer-1"):
    s, ag = agent.s, agent.ag
    episode = s.add_node("SocialEpisode", {
        "episode_id": episode_id, "status": "observed",
        "observation_status": observation_status, "source_kind": "directed_demonstration",
        "owner_id": "agent-root", "actor_id": actor_id,
        "actor_body_id": "peer-body", "learner_body_id": "learner-body",
        "source_epoch": 4, "model_epoch": 7, "target_frame_epoch": 9,
        "binding_id": binding_id, "template_key": "press-button",
        "action_sequence": ["seq", ["add", [1]]],
    })
    body_map = s.add_node("SocialBodyFrameMap", {
        "status": map_status, "source_body_id": "peer-body",
        "target_body_id": "learner-body", "source_epoch": 4,
        "target_frame_epoch": 9, "map_id": f"map:{episode_id}"})
    s.add_edge(ag, "has_social_episode", episode, {})
    s.add_edge(episode, "uses_body_frame_map", body_map, {})
    requests = list(s.neighbours(ag, "has_thinking_budget"))
    assert requests
    request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "imitation", "episode_id": episode_id,
        "status": "approved", "source_epoch": 4,
        "source_key": f"imitation:{episode_id}"})
    s.add_edge(ag, "has_imitation_request", request, {})
    s.add_edge(request, "draws_on_thinking_budget", requests[0], {})
    _tick(agent)
    candidates = [n for n in s.nodes("DemonstratedProcessCandidate")
                  if s.node(n)["attrs"].get("episode_id") == episode_id]
    expected = int(map_status == "verified" and observation_status == "complete"
                   and actor_id != "agent-root"
                   and agent.s.node(agent.s.nodes("ImitationPolicy")[0])["attrs"]["enabled"] == 1.0)
    assert len(candidates) == expected
    return candidates[0] if candidates else None


def _tick(agent):
    for _ in range(20):
        agent.s.tick(1000)


def _verify_candidate(agent, candidate, *, expected_state=None):
    """Mechanical scorer creates a receipt from native detached ProcessApply."""
    s = agent.s
    attrs = s.node(candidate)["attrs"]
    expected_state = [1] if expected_state is None else expected_state
    term = {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
            "state": {"type": "Var", "name": "state"}}
    predicted = agent.native.evaluate(term, {"p": attrs["action_sequence"], "state": [0]})
    status = "verified" if predicted == expected_state else "failed"
    budget = list(s.neighbours(agent.ag, "has_thinking_budget"))[0]
    request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "imitation_validation", "candidate_id": attrs["candidate_id"],
        "status": "approved", "source_epoch": attrs["source_epoch"],
        "source_key": f"validation:{attrs['candidate_id']}"})
    s.add_edge(candidate, "has_validation_request", request, {})
    s.add_edge(request, "draws_on_thinking_budget", budget, {})
    receipt = s.add_node("DetachedOwnModelVerification", {
        "candidate_id": attrs["candidate_id"], "verification_kind": "detached_own_model_rollout",
        "status": status, "owner_id": attrs["owner_id"], "source_epoch": attrs["source_epoch"],
        "model_epoch": attrs["model_epoch"], "frame_epoch": attrs["target_frame_epoch"],
        "receipt_id": f"rollout:{attrs['candidate_id']}"})
    s.add_edge(candidate, "has_own_model_verification", receipt, {})
    _tick(agent)
    return receipt


def test_demo_candidate_graph_resident():
    agent = _agent()
    candidate = _observed_candidate(agent, "episode-a", "object-red")
    attrs = agent.s.node(candidate)["attrs"]
    assert attrs["status"] == "unverified_candidate"
    assert attrs["provenance"] == "ordered_directed_observation"
    assert attrs["action_sequence"] == ["seq", ["add", [1]]]
    assert list(agent.s.neighbours(candidate, "from_episode"))


def test_imitation_seed_is_disabled_by_default():
    agent = _agent(enabled=False)
    assert agent.s.node(agent.s.nodes("ImitationPolicy")[0])["attrs"]["enabled"] == 0.0
    assert _observed_candidate(agent, "disabled", "object-red") is None


def test_failed_own_rollout_rejects():
    agent = _agent()
    candidate = _observed_candidate(agent, "episode-fail", "object-red")
    _verify_candidate(agent, candidate, expected_state=[9])
    assert agent.s.node(candidate)["attrs"]["status"] == "rejected"
    assert not agent.s.nodes("ProcessSchema")


def test_incomplete_observation_and_body_mismatch_do_not_mint_candidates():
    agent = _agent()
    assert _observed_candidate(agent, "partial", "object-red",
                               observation_status="partial") is None
    assert _observed_candidate(agent, "wrong-body", "object-blue",
                               map_status="mismatch") is None
    assert _observed_candidate(agent, "self-observed", "object-green",
                               actor_id="agent-root") is None


def test_demo_candidate_adoption_is_model_verified_but_not_own_grounded():
    agent = _agent()
    candidate = _observed_candidate(agent, "episode-a", "object-red")
    _verify_candidate(agent, candidate)
    schemas = [n for n in agent.s.nodes("ProcessSchema")
               if agent.s.node(n)["attrs"].get("provenance") == "own_model_verified_demonstration"]
    assert len(schemas) == 1
    schema = schemas[0]
    assert agent.s.node(schema)["attrs"]["grounding_status"] == "model_verified_not_own_trial"


def test_grounding_requires_own_receipt():
    agent = _agent()
    candidate = _observed_candidate(agent, "episode-a", "object-red")
    _verify_candidate(agent, candidate)
    schema = next(n for n in agent.s.nodes("ProcessSchema")
                  if agent.s.node(n)["attrs"].get("provenance") == "own_model_verified_demonstration")
    attrs = agent.s.node(schema)["attrs"]
    action_request = agent.s.add_node("ActionRequest", {
        "request_id": "own-trial-action", "source_epoch": attrs["source_epoch"],
        "action_key": "press", "status": "emitted", "sink_receipt_id": "sink:own-trial-1"})
    authorization = agent.s.add_node("ActionAuthorization", {
        "authorization_id": "auth-own-trial", "request_id": "own-trial-action",
        "source_epoch": attrs["source_epoch"], "action_key": "press", "status": "consumed"})
    agent.s.add_edge(action_request, "has_action_authorization", authorization, {})
    receipt = agent.s.add_node("OwnTrialReceipt", {
        "status": "observed", "actual_own_trial": True,
        "owner_id": "agent-root", "learner_body_owner_id": "agent-root",
        "sink_receipt_id": "sink:own-trial-1",
        "source_epoch": attrs["source_epoch"], "model_epoch": attrs["model_epoch"],
        "frame_epoch": attrs["frame_epoch"], "receipt_id": "own-trial-1"})
    agent.s.add_edge(schema, "has_own_trial_receipt", receipt, {})
    agent.s.add_edge(receipt, "binds_action_request", action_request, {})
    _tick(agent)
    assert agent.s.node(schema)["attrs"]["grounding_status"] == "own_trial_grounded"
    assert agent.s.node(schema)["attrs"]["own_trial_receipt_id"] == "own-trial-1"


def test_trial_stop_respected_by_native_response_inhibition_gate():
    agent = _agent()
    policy = agent.s.nodes("ResponseInhibitionPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    request = agent.s.add_node("ActionRequest", {
        "request_id": "own-action-1", "source_epoch": 4.0,
        "action_key": "press", "status": "selected"})
    agent.s.add_edge(agent.ag, "has_action_request", request, {})
    auth = agent.s.add_node("ActionAuthorization", {
        "authorization_id": "auth-1", "status": "pending",
        "request_id": "own-action-1", "source_epoch": 4.0,
        "action_key": "press", "sink_route": "count"})
    agent.s.add_edge(request, "has_action_authorization", auth, {})
    stop = agent.s.add_node("ActionStopEvent", {
        "request_id": "own-action-1", "source_epoch": 4.0, "status": "pending"})
    agent.s.add_edge(request, "has_action_stop", stop, {})
    _tick(agent)
    assert agent.s.node(request)["attrs"]["status"] == "withheld"
    assert agent.s.node(auth)["attrs"]["status"] == "revoked"


def test_demo_lifts_to_unseen_binding_only_after_fresh_rollout():
    agent = _agent()
    first = _observed_candidate(agent, "episode-a", "object-red")
    _verify_candidate(agent, first)
    second = _observed_candidate(agent, "episode-b", "object-blue")
    _verify_candidate(agent, second)
    families = list(agent.s.nodes("DemonstratedProcessFamily"))
    assert len(families) == 1
    replay = agent.s.add_node("DemonstratedBindingReplay", {
        "replay_id": "replay-object-green", "template_key": "press-button",
        "binding_id": "object-green", "owner_id": "agent-root",
        "model_epoch": 7, "frame_epoch": 9, "status": "requested"})
    agent.s.add_edge(agent.ag, "has_binding_replay_request", replay, {})
    agent.s.add_edge(replay, "reuses_demonstrated_family", families[0], {})
    budget = list(agent.s.neighbours(agent.ag, "has_thinking_budget"))[0]
    replay_request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "imitation_binding_replay", "replay_id": "replay-object-green",
        "status": "approved", "source_epoch": 4,
        "source_key": "replay:object-green"})
    agent.s.add_edge(replay, "funded_by", replay_request, {})
    agent.s.add_edge(replay_request, "draws_on_thinking_budget", budget, {})
    receipt = agent.s.add_node("DetachedOwnModelVerification", {
        "candidate_id": "replay-object-green", "verification_kind": "detached_own_model_rollout",
        "status": "verified", "owner_id": "agent-root", "source_epoch": 4,
        "model_epoch": 7, "frame_epoch": 9, "receipt_id": "replay-rollout-green"})
    agent.s.add_edge(replay, "has_fresh_verification", receipt, {})
    _tick(agent)
    schemas = [n for n in agent.s.nodes("ProcessSchema")
               if agent.s.node(n)["attrs"].get("provenance") == "verified_unseen_demo_binding"]
    assert len(schemas) == 1
    assert agent.s.node(schemas[0])["attrs"]["binding_id"] == "object-green"
