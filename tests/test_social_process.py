"""P12.03 instruction and incidental social process evidence lifecycle."""
from __future__ import annotations

from evaluation.process_mastery.harness import Agent


def _agent():
    return Agent(extra_seeds=("social_process",),
                 policy_overrides={"SocialProcessPolicy": {"enabled": 1.0}},
                 budget={"enabled": 1.0, "remaining": 12.0,
                         "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})


def _tick(agent):
    for _ in range(24):
        agent.s.tick(1000)


def _request(agent, *, requester_kind, source_key, source_epoch, identity_key,
             identity, cost=1.0):
    s = agent.s
    budget = list(s.neighbours(agent.ag, "has_thinking_budget"))[0]
    attrs = {"requester_kind": requester_kind, identity_key: identity,
             "source_key": source_key, "source_epoch": source_epoch,
             "operation_id": f"{requester_kind}:{identity}", "status": "pending",
             "cost": cost}
    request = s.add_node("ThinkingBudgetRequest", attrs)
    s.add_edge(agent.ag, "has_social_process_request", request, {})
    s.add_edge(request, "draws_on_thinking_budget", budget, {})
    return request


def _instruction(agent, *, predicate="press", content="lever"):
    s = agent.s
    message = s.add_node("Message", {
        "from": "interlocutor", "text": f"{predicate} {content}",
        "comp_kind": "instruction", "comp_predicate": predicate,
        "comp_content": content})
    # The slim PMB harness omits conversation ingress vocabulary; this is a
    # fixture insertion only. InstructionUnderstanding rules still execute in
    # Rust on the typed graph node and edge.
    agent.native.add_edge_unchecked(agent.ag, "received", message)
    pred = s.add_node("Mention", {"text": predicate})
    pred_concept = s.add_node("Concept", {"name": predicate,
                                           "instruction_route": "world_action"})
    s.add_edge(message, "has_mention", pred, {})
    s.add_edge(pred, "refers_to", pred_concept, {})
    obj = s.add_node("Mention", {"text": content})
    obj_concept = s.add_node("Concept", {"name": content})
    s.add_edge(message, "has_mention", obj, {})
    s.add_edge(obj, "refers_to", obj_concept, {})
    model = s.add_node("ProcessSchema", {
        "name": f"held:{predicate}:{content}", "kind": "sequence",
        "domain": "native-action-model", "operator": predicate, "binding": content,
        "params": ["seq", ["add", [1]]], "status": "active",
        "source_epoch": 4, "model_epoch": 7, "frame_epoch": 9,
        "provenance": "held_native_model"})
    s.add_edge(agent.ag, "has_process_schema", model, {})
    intake = _request(agent, requester_kind="social_process_instruction",
                      source_key=f"{predicate} {content}", source_epoch=4,
                      identity_key="instruction_id", identity=f"{predicate}:{content}")
    return message, model, intake


def _validate_candidate(agent, candidate, model):
    s = agent.s
    cattrs = s.node(candidate)["attrs"]
    mattrs = s.node(model)["attrs"]
    term = {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
            "state": {"type": "Var", "name": "state"}}
    predicted = agent.native.evaluate(term, {"p": mattrs["params"], "state": [0]})
    exact = predicted == [1]
    request = _request(agent, requester_kind="social_process_validation",
                       source_key=f"validate:{cattrs['candidate_id']}",
                       source_epoch=cattrs["source_epoch"], identity_key="candidate_id",
                       identity=cattrs["candidate_id"])
    receipt = s.add_node("SocialProcessVerification", {
        "candidate_id": cattrs["candidate_id"], "verification_kind": "native_process_effect",
        "status": "verified" if exact else "failed", "exact_effect_match": exact,
        "source_epoch": cattrs["source_epoch"], "model_epoch": cattrs["model_epoch"],
        "receipt_id": f"social-process-verification:{cattrs['candidate_id']}"})
    s.add_edge(candidate, "has_verification", receipt, {})
    # Validation funding is a distinct request from candidate acquisition.
    s.add_edge(candidate, "has_validation_request", request, {})
    _tick(agent)
    return receipt


def test_instruction_to_schema_verified():
    agent = _agent()
    _message, model, _intake = _instruction(agent)
    _tick(agent)
    interpretations = list(agent.s.nodes("InstructionInterpretation"))
    assert len(interpretations) == 1
    assert agent.s.node(interpretations[0])["attrs"]["status"] == "verified"
    candidates = list(agent.s.nodes("SocialProcessCandidate"))
    assert len(candidates) == 1
    assert agent.s.node(candidates[0])["attrs"]["source_kind"] == "verified_instruction"
    _validate_candidate(agent, candidates[0], model)
    social_schemas = list(agent.s.nodes("SocialProcessSchema"))
    assert len(social_schemas) == 1
    assert agent.s.node(social_schemas[0])["attrs"]["status"] == "verified"
    assert agent.s.node(social_schemas[0])["attrs"]["effect_evaluation"] == "exact:native_process_effect"


def _witnessed_episode(agent):
    s = agent.s
    model = s.add_node("ProcessSchema", {
        "name": "request-repair-model", "kind": "sequence", "domain": "social",
        "operator": "request", "binding": "repair", "params": ["seq", ["add", [1]]],
        "status": "active", "source_epoch": 4, "model_epoch": 7,
        "provenance": "held_native_model"})
    s.add_edge(agent.ag, "has_process_schema", model, {})
    episode = s.add_node("SocialEpisode", {
        "episode_id": "witnessed-1", "status": "observed",
        "source_kind": "witnessed_interaction", "observation_status": "complete",
        "interaction_kind": "request_repair", "owner_id": "agent-root",
        "actor_id": "peer", "source_epoch": 4, "model_epoch": 7,
        "request_action": "request", "repair_action": "repair",
        "action_sequence": ["seq", ["add", [1]]]})
    s.add_edge(agent.ag, "has_social_episode", episode, {})
    intake = _request(agent, requester_kind="social_process_observation",
                      source_key="witnessed-1", source_epoch=4,
                      identity_key="episode_id", identity="witnessed-1")
    return model, episode, intake


def test_incidental_request_repair_acquired():
    agent = _agent()
    model, _episode, intake = _witnessed_episode(agent)
    _tick(agent)
    candidates = list(agent.s.nodes("SocialProcessCandidate"))
    assert len(candidates) == 1
    attrs = agent.s.node(candidates[0])["attrs"]
    assert attrs["source_kind"] == "witnessed_request_repair"
    assert attrs["provenance"] == "incidental_witnessed_interaction"
    assert "teacher_id" not in attrs
    assert agent.s.node(intake)["attrs"]["terminal_status"] == "completed"
    _validate_candidate(agent, candidates[0], model)
    assert len(agent.s.nodes("SocialProcessSchema")) == 1


def test_no_teacher_marker_needed():
    agent = _agent()
    _model, episode, _intake = _witnessed_episode(agent)
    assert "teacher_id" not in agent.s.node(episode)["attrs"]
    _tick(agent)
    assert len(agent.s.nodes("SocialProcessCandidate")) == 1


def test_own_grounding_requires_owned_authorized_action_and_matching_sink_receipt():
    agent = _agent()
    _message, model, _intake = _instruction(agent)
    _tick(agent)
    candidate = agent.s.nodes("SocialProcessCandidate")[0]
    _validate_candidate(agent, candidate, model)
    schema = agent.s.nodes("SocialProcessSchema")[0]
    assert agent.s.node(schema)["attrs"].get("grounding_status") is None
    request = agent.s.add_node("ActionRequest", {
        "request_id": "social-own-action", "actor_id": "agent-root",
        "source_epoch": 4, "status": "emitted", "sink_receipt_id": "sink:social-own"})
    authorization = agent.s.add_node("ActionAuthorization", {
        "request_id": "social-own-action", "source_epoch": 4, "status": "consumed"})
    agent.s.add_edge(agent.ag, "has_action_request", request, {})
    agent.s.add_edge(request, "has_action_authorization", authorization, {})
    receipt = agent.s.add_node("OwnTrialReceipt", {
        "receipt_id": "social-own", "status": "observed", "actual_own_trial": True,
        "owner_id": "agent-root", "learner_body_owner_id": "agent-root",
        "source_epoch": 4, "model_epoch": 7, "sink_receipt_id": "sink:social-own"})
    agent.s.add_edge(schema, "has_own_trial_receipt", receipt, {})
    agent.s.add_edge(receipt, "binds_action_request", request, {})
    _tick(agent)
    assert agent.s.node(schema)["attrs"]["grounding_status"] == "own_trial_grounded"
    assert agent.s.node(schema)["attrs"]["own_trial_receipt_id"] == "social-own"


def test_reward_only_acquisition_requires_rewarded_owned_trial_and_native_validation():
    agent = _agent()
    s = agent.s
    model = s.add_node("ProcessSchema", {
        "name": "reward-model", "kind": "sequence", "domain": "reward",
        "operator": "apply", "binding": "increment", "params": ["seq", ["add", [1]]],
        "status": "active", "source_epoch": 4, "model_epoch": 7,
        "frame_epoch": 9})
    s.add_edge(agent.ag, "has_process_schema", model, {})
    action = s.add_node("ActionRequest", {
        "request_id": "reward-own-action", "actor_id": "agent-root",
        "source_epoch": 4, "status": "emitted", "action_key": "apply",
        "sink_receipt_id": "sink:reward-own"})
    authorization = s.add_node("ActionAuthorization", {
        "request_id": "reward-own-action", "source_epoch": 4,
        "status": "consumed", "action_key": "apply"})
    s.add_edge(agent.ag, "has_action_request", action, {})
    s.add_edge(action, "has_action_authorization", authorization, {})
    feedback = s.add_node("RewardProcessFeedback", {
        "feedback_id": "reward-feedback-1", "status": "observed",
        "actual_own_trial": True, "outcome": "rewarded", "reward_value": 1.0,
        "owner_id": "agent-root", "source_epoch": 4, "model_epoch": 7,
        "sink_receipt_id": "sink:reward-own"})
    s.add_edge(agent.ag, "has_reward_process_feedback", feedback, {})
    s.add_edge(feedback, "uses_process_model", model, {})
    s.add_edge(feedback, "binds_action_request", action, {})
    intake = _request(agent, requester_kind="reward_process_acquisition",
                      source_key="reward-feedback-1", source_epoch=4,
                      identity_key="feedback_id", identity="reward-feedback-1")
    _tick(agent)
    candidates = s.nodes("RewardProcessCandidate")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert s.node(candidate)["attrs"]["provenance"] == "rewarded_actual_own_trial"
    validation = _request(agent, requester_kind="reward_process_validation",
                          source_key="validate:reward-feedback-1", source_epoch=4,
                          identity_key="candidate_id",
                          identity=s.node(candidate)["attrs"]["candidate_id"])
    s.add_edge(candidate, "has_validation_request", validation, {})
    receipt = s.add_node("RewardProcessVerification", {
        "candidate_id": s.node(candidate)["attrs"]["candidate_id"],
        "verification_kind": "native_process_effect", "status": "verified",
        "exact_effect_match": True, "source_epoch": 4, "model_epoch": 7,
        "receipt_id": "reward-validation-1"})
    s.add_edge(candidate, "has_verification", receipt, {})
    _tick(agent)
    schemas = s.nodes("RewardProcessSchema")
    assert len(schemas) == 1
    assert s.node(schemas[0])["attrs"]["status"] == "verified"
    assert s.node(candidate)["attrs"]["status"] == "adopted"
    assert s.node(intake)["attrs"]["terminal_status"] == "completed"


def test_wrong_interpretation_counterexample_revises():
    agent = _agent()
    _message, model, _intake = _instruction(agent)
    _tick(agent)
    candidate = agent.s.nodes("SocialProcessCandidate")[0]
    _validate_candidate(agent, candidate, model)
    social_schema = agent.s.nodes("SocialProcessSchema")[0]
    counterexample = agent.s.add_node("SocialProcessCounterexample", {
        "counterexample_id": "counterexample-1", "candidate_id": "instruction:press:lever",
        "status": "observed", "source_epoch": 4, "model_epoch": 7,
        "evidence_ref": "observed:press-without-lever-effect"})
    agent.s.add_edge(social_schema, "has_counterexample", counterexample, {})
    _tick(agent)
    revisions = list(agent.s.nodes("SocialProcessRevision"))
    assert len(revisions) == 1
    assert agent.s.node(revisions[0])["attrs"]["status"] == "pending_verification"
    assert agent.s.node(revisions[0])["attrs"]["counterexample_evidence"] == "observed:press-without-lever-effect"
    assert agent.s.node(candidate)["attrs"]["status"] == "revision_pending"
    assert agent.s.node(social_schema)["attrs"]["status"] == "stale_counterexample"
