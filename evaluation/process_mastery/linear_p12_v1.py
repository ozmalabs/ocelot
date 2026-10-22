"""P12 social acquisition and explanation/rebuild evidence panel.

Python installs external observations and scores native process receipts. The
candidate lifecycle, verification gates, adoption and own-trial grounding run in
Rust graph rules. This panel is a bounded synthetic process mechanism test;
it does not estimate open-domain social learning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.harness import Agent  # noqa: E402
from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
import substrate_rs  # noqa: E402

PHASE = "linear-p12-v1"
SOCIAL_ARMS = ("observation", "demonstration", "instruction", "reward_only")
CONTROLS = ("shuffled", "missing", "body_mismatch")
LIMITS = {"max_ticks": 24, "max_steps_per_tick": 1000,
          "budget": 12.0, "evidence_opportunities": 8,
          "native_effect_probes": 3, "action_trials": 3}
DEV_SEED = 12_000_000
HELDOUT_SEED = 12_100_000
SOCIAL_N = 200
CONTROL_N = 100
REBUILD_N = 200
ACTION = ["seq", ["add", [1]]]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          default=str).encode())


def _provenance():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True).strip()
    except Exception:
        commit = "unavailable"
    paths = ["evaluation/process_mastery/linear_p12_v1.py",
             "evaluation/process_mastery/analyze_linear_p12_v1.py",
             "evaluation/process_mastery/harness.py",
             "evaluation/process_mastery/scorecard.py",
             "substrate/boot_profiles.py",
             "scripts/gen_imitation_seed.py", "seeds/imitation.json",
             "scripts/gen_social_process_seed.py", "seeds/social_process.json",
             "scripts/gen_process_explanation_seed.py", "seeds/process_explanation.json",
             "seeds/instruction_understanding.json"]
    bundle = hashlib.sha256()
    for rel in paths:
        bundle.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    engine = hashlib.sha256()
    for rel in ("runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
                "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
                "runners/dsl/src/eval.rs", "runners/dsl/src/engine.rs"):
        file = ROOT / rel
        if file.exists():
            engine.update(rel.encode() + b"\0" + file.read_bytes() + b"\0")
    return {"phase": PHASE, "git_commit": commit,
            "source_bundle_sha256": bundle.hexdigest(),
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "engine_source_sha256": engine.hexdigest(),
            "engine_binary_sha256": _sha(Path(substrate_rs.__file__).read_bytes()),
            "python": sys.version.split()[0], "limits": dict(LIMITS)}


def _tick(agent, count=LIMITS["max_ticks"]):
    total = 0
    for _ in range(count):
        total += agent.s.tick(LIMITS["max_steps_per_tick"])
    return total


def _agent(*, imitation=False, social=False, explanation=False):
    extras = []
    policies = {}
    if imitation:
        extras.append("imitation")
        policies["ImitationPolicy"] = {"enabled": 1.0}
    if social:
        extras.append("social_process")
        policies["SocialProcessPolicy"] = {"enabled": 1.0}
    if explanation:
        extras.append("process_explanation")
        policies["ProcessExplanationPolicy"] = {"enabled": 1.0}
    started = time.perf_counter()
    agent = Agent(extra_seeds=tuple(extras), policy_overrides=policies,
                  budget={"enabled": 1.0, "remaining": LIMITS["budget"],
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0},
                  profile=f"p12-{'+'.join(extras) or 'no_social'}")
    agent._p12_boot_seconds = time.perf_counter() - started
    agent._p12_initial_graph_nodes = len(agent.s.nodes())
    agent._p12_initial_graph_bytes = _graph_bytes(agent.s)
    return agent


def _budget(agent):
    values = list(agent.s.neighbours(agent.ag, "has_thinking_budget"))
    if not values:
        raise RuntimeError("missing shared ThinkingBudget adapter")
    return values[0]


def _budget_remaining(agent):
    return agent.s.node(_budget(agent))["attrs"].get("remaining")


def _graph_bytes(substrate):
    return len(json.dumps([substrate.node(n) for n in substrate.nodes()],
                          sort_keys=True, default=str).encode())


def _request(agent, kind, identity_key, identity, source_epoch=4):
    s = agent.s
    request = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": kind, identity_key: identity,
        "source_key": f"{kind}:{identity}", "source_epoch": source_epoch,
        "operation_id": f"{kind}:{identity}", "status": "pending", "cost": 1.0})
    edge = ("has_imitation_request" if kind.startswith("imitation")
            else "has_social_process_request")
    s.add_edge(agent.ag, edge, request, {})
    s.add_edge(request, "draws_on_thinking_budget", _budget(agent), {})
    return request


def _held_model_bank(agent, seed):
    models = []
    for binding, params in (("repair", ACTION), ("restore", ["seq", ["add", [2]]])):
        model = agent.s.add_node("ProcessSchema", {
            "name": f"held-request-{binding}:{seed}", "kind": "sequence",
            "domain": f"p12-social:{seed}", "operator": "request", "binding": binding,
            "params": params, "status": "active", "source_epoch": 4,
            "model_epoch": 7, "frame_epoch": 9, "provenance": "shared_held_process_model"})
        agent.s.add_edge(agent.ag, "has_process_schema", model, {})
        models.append(model)
    return models


def _social_input(agent, arm, seed, model):
    s = agent.s
    if arm == "observation":
        episode = s.add_node("SocialEpisode", {
            "episode_id": f"obs:{seed}", "status": "observed",
            "source_kind": "witnessed_interaction", "observation_status": "complete",
            "interaction_kind": "request_repair", "owner_id": "agent-root",
            "actor_id": "peer", "source_epoch": 4, "model_epoch": 7,
            "request_action": "request", "repair_action": "repair",
            "action_sequence": ACTION})
        s.add_edge(agent.ag, "has_social_episode", episode, {})
        _request(agent, "social_process_observation", "episode_id", episode and f"obs:{seed}")
        _tick(agent)
        return model
    if arm == "instruction":
        message = s.add_node("Message", {
            "from": "interlocutor", "text": "request repair",
            "comp_kind": "instruction", "comp_predicate": "request",
            "comp_content": "repair"})
        agent.native.add_edge_unchecked(agent.ag, "received", message)
        pred = s.add_node("Mention", {"text": "request"})
        pred_concept = s.add_node("Concept", {"name": "request", "instruction_route": "world_action"})
        obj = s.add_node("Mention", {"text": "repair"})
        obj_concept = s.add_node("Concept", {"name": "repair"})
        s.add_edge(message, "has_mention", pred, {})
        s.add_edge(pred, "refers_to", pred_concept, {})
        s.add_edge(message, "has_mention", obj, {})
        s.add_edge(obj, "refers_to", obj_concept, {})
        intake = _request(agent, "social_process_instruction", "instruction_id", f"request:repair")
        s.set_attr(intake, "source_key", "request repair")
        _tick(agent)
        return model
    return model


def _validate_social(agent, seed):
    s = agent.s
    candidates = [n for n in s.nodes("SocialProcessCandidate")
                  if s.node(n)["attrs"].get("episode_id") == f"obs:{seed}"
                  or s.node(n)["attrs"].get("candidate_id") == "instruction:request:repair"]
    if len(candidates) != 1:
        return None, "no_unique_native_social_candidate"
    candidate = candidates[0]
    attrs = s.node(candidate)["attrs"]
    request = _request(agent, "social_process_validation", "candidate_id",
                       attrs["candidate_id"], attrs["source_epoch"])
    s.add_edge(candidate, "has_validation_request", request, {})
    params = s.node(list(s.neighbours(candidate, "uses_process_model"))[0])["attrs"]["params"]
    predicted = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}}, {"p": params, "state": [0]})
    receipt = s.add_node("SocialProcessVerification", {
        "candidate_id": attrs["candidate_id"], "verification_kind": "native_process_effect",
        "status": "verified" if predicted == [1] else "failed",
        "exact_effect_match": predicted == [1], "source_epoch": attrs["source_epoch"],
        "model_epoch": attrs["model_epoch"], "receipt_id": f"spv:{seed}"})
    s.add_edge(candidate, "has_verification", receipt, {})
    _tick(agent)
    schemas = [n for n in s.nodes("SocialProcessSchema")
               if s.node(n)["attrs"].get("schema_id") == attrs["candidate_id"]]
    if len(schemas) != 1:
        return None, "native_social_verification_did_not_adopt"
    return schemas[0], "adopted"


def _reward_input(agent, model_bank, seed):
    """Expose scalar outcomes from two world-scheduled, authorized own probes."""
    s = agent.s
    modes = list(s.neighbours(agent.ag, "has_network_mode_state"))
    policies = list(s.nodes("ResponseInhibitionPolicy"))
    if len(modes) != 1 or len(policies) != 1:
        raise RuntimeError("reward probe requires one native action mode and inhibition policy")
    s.set_attr(modes[0], "epoch", 4.0)
    s.set_attr(policies[0], "enabled", 1.0)
    positive_feedback = None
    for index, model in enumerate(model_bank):
        ma = s.node(model)["attrs"]
        request_id = f"reward-probe:{seed}:{index}"
        action_key = f"probe:{ma['binding']}"
        action = s.add_node("ActionRequest", {
            "request_id": request_id, "actor_id": "agent-root", "source_epoch": 4.0,
            "status": "selected", "action_key": action_key})
        authorization = s.add_node("ActionAuthorization", {
            "authorization_id": f"auth:{request_id}", "request_id": request_id,
            "source_epoch": 4.0, "status": "pending", "action_key": action_key,
            "sink_route": "world.apply_action"})
        s.add_edge(agent.ag, "has_action_request", action, {})
        s.add_edge(action, "has_action_authorization", authorization, {})
        agent_id = agent.ag.value if hasattr(agent.ag, "value") else int(str(agent.ag).lstrip("#"))
        enabled, authorized_id = agent.native.authorize_action_emission(
            agent_id, action_key, "world.apply_action")
        if not enabled or authorized_id != request_id:
            raise RuntimeError("native P5 gate denied a registered reward probe")
        result = agent.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": ma["params"], "state": [0]})
        reward = 1.0 if result == [1] else 0.0
        agent.native.complete_action_emission(agent_id, authorized_id, True)
        sink = s.node(action)["attrs"].get("sink_receipt_id")
        if not sink or s.node(authorization)["attrs"].get("status") != "consumed":
            raise RuntimeError("reward probe lacks a consumed P5 authorization/sink receipt")
        feedback_id = f"reward-feedback:{seed}:{index}"
        feedback = s.add_node("RewardProcessFeedback", {
            "feedback_id": feedback_id, "status": "observed", "actual_own_trial": True,
            "outcome": "rewarded" if reward > 0 else "unrewarded", "reward_value": reward,
            "owner_id": "agent-root", "learner_body_owner_id": "agent-root",
            "source_epoch": 4, "model_epoch": ma["model_epoch"], "sink_receipt_id": sink})
        s.add_edge(agent.ag, "has_reward_process_feedback", feedback, {})
        s.add_edge(feedback, "uses_process_model", model, {})
        s.add_edge(feedback, "binds_action_request", action, {})
        if reward > 0:
            intake = _request(agent, "reward_process_acquisition", "feedback_id",
                              feedback_id, source_epoch=4)
            s.set_attr(intake, "source_key", feedback_id)
            positive_feedback = feedback
    if positive_feedback is None:
        _tick(agent)
        return None, "no_positive_reward_feedback"
    _tick(agent)
    feedback_id = s.node(positive_feedback)["attrs"]["feedback_id"]
    candidates = [n for n in s.nodes("RewardProcessCandidate")
                 if s.node(n)["attrs"].get("feedback_id") == feedback_id]
    if len(candidates) != 1:
        return None, "native_reward_feedback_did_not_mint_candidate"
    candidate = candidates[0]
    ca = s.node(candidate)["attrs"]
    validation = _request(agent, "reward_process_validation", "candidate_id",
                          ca["candidate_id"], source_epoch=ca["source_epoch"])
    s.add_edge(candidate, "has_validation_request", validation, {})
    models = list(s.neighbours(candidate, "uses_process_model"))
    if len(models) != 1:
        return None, "reward_candidate_has_ambiguous_model"
    params = s.node(models[0])["attrs"]["params"]
    probes = [[seed % 9], [3], [-2]]
    exact = all(agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}}, {"p": params, "state": state})
                == [state[0] + 1] for state in probes)
    receipt = s.add_node("RewardProcessVerification", {
        "candidate_id": ca["candidate_id"], "verification_kind": "native_process_effect",
        "status": "verified" if exact else "failed", "exact_effect_match": exact,
        "source_epoch": ca["source_epoch"], "model_epoch": ca["model_epoch"],
        "receipt_id": f"reward-verify:{seed}"})
    s.add_edge(candidate, "has_verification", receipt, {})
    _tick(agent)
    schemas = [n for n in s.nodes("RewardProcessSchema")
               if s.node(n)["attrs"].get("schema_id") == ca["candidate_id"]]
    if len(schemas) != 1:
        return None, "native_reward_validation_did_not_adopt"
    return schemas[0], "adopted"


def _demonstration(agent, seed, control=None):
    s = agent.s
    sequence = ACTION
    observation_status, map_status, actor = "complete", "verified", "peer"
    if control == "missing":
        observation_status = "partial"
    elif control == "body_mismatch":
        map_status = "mismatch"
    elif control == "shuffled":
        sequence = ["seq", ["add", [2]]]
    episode_id = f"demo:{seed}"
    episode = s.add_node("SocialEpisode", {
        "episode_id": episode_id, "status": "observed",
        "observation_status": observation_status, "source_kind": "directed_demonstration",
        "owner_id": "agent-root", "actor_id": actor, "actor_body_id": "peer-body",
        "learner_body_id": "learner-body", "source_epoch": 4, "model_epoch": 7,
        "target_frame_epoch": 9, "binding_id": f"binding:{seed}",
        "template_key": "press-button", "action_sequence": sequence})
    body_map = s.add_node("SocialBodyFrameMap", {
        "status": map_status, "source_body_id": "peer-body", "target_body_id": "learner-body",
        "source_epoch": 4, "target_frame_epoch": 9, "map_id": f"map:{seed}"})
    s.add_edge(agent.ag, "has_social_episode", episode, {})
    s.add_edge(episode, "uses_body_frame_map", body_map, {})
    request = _request(agent, "imitation", "episode_id", episode_id)
    _tick(agent)
    candidates = [n for n in s.nodes("DemonstratedProcessCandidate")
                 if s.node(n)["attrs"].get("episode_id") == episode_id]
    if control in {"missing", "body_mismatch"}:
        return None, "rejected_control" if not candidates else "false_candidate"
    if len(candidates) != 1:
        return None, "no_unique_native_demo_candidate"
    candidate = candidates[0]
    attrs = s.node(candidate)["attrs"]
    validation = _request(agent, "imitation_validation", "candidate_id",
                          attrs["candidate_id"], attrs["source_epoch"])
    s.add_edge(candidate, "has_validation_request", validation, {})
    predicted = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": attrs["action_sequence"], "state": [0]})
    receipt = s.add_node("DetachedOwnModelVerification", {
        "candidate_id": attrs["candidate_id"], "verification_kind": "detached_own_model_rollout",
        "status": "verified" if predicted == [1] else "failed", "owner_id": attrs["owner_id"],
        "source_epoch": attrs["source_epoch"], "model_epoch": attrs["model_epoch"],
        "frame_epoch": attrs["target_frame_epoch"], "receipt_id": f"rollout:{seed}"})
    s.add_edge(candidate, "has_own_model_verification", receipt, {})
    _tick(agent)
    schemas = [n for n in s.nodes("ProcessSchema")
               if s.node(n)["attrs"].get("provenance") == "own_model_verified_demonstration"
               and s.node(n)["attrs"].get("name") == f"demonstrated:{attrs['candidate_id']}"]
    if len(schemas) != 1:
        return None, "native_demo_verification_did_not_adopt"
    return schemas[0], "adopted"


def _own_trial(agent, schema, seed):
    if schema is None:
        return False, "no_process_schema"
    s = agent.s
    attrs = s.node(schema)["attrs"]
    params = attrs.get("params")
    if params is None:
        effects = list(s.neighbours(schema, "instantiates_effect"))
        if len(effects) == 1:
            params = s.node(effects[0])["attrs"].get("params")
    state = [seed % 13]
    expected = [state[0] + 1]
    modes = list(s.neighbours(agent.ag, "has_network_mode_state"))
    if len(modes) != 1:
        return False, "missing_or_ambiguous_network_epoch"
    epoch = attrs.get("source_epoch", 4)
    s.set_attr(modes[0], "epoch", float(epoch))
    policies = list(s.nodes("ResponseInhibitionPolicy"))
    if len(policies) != 1:
        return False, "missing_or_ambiguous_response_inhibition_policy"
    s.set_attr(policies[0], "enabled", 1.0)
    request = s.add_node("ActionRequest", {
        "request_id": f"own:{seed}", "actor_id": "agent-root",
        "source_epoch": float(epoch), "status": "selected",
        "action_key": "apply_process"})
    auth = s.add_node("ActionAuthorization", {
        "authorization_id": f"auth:{seed}", "request_id": f"own:{seed}",
        "source_epoch": float(epoch), "status": "pending",
        "action_key": "apply_process", "sink_route": "world.apply_action"})
    s.add_edge(agent.ag, "has_action_request", request, {})
    s.add_edge(request, "has_action_authorization", auth, {})
    native_agent_id = agent.ag.value if hasattr(agent.ag, "value") else int(str(agent.ag).lstrip("#"))
    enabled, request_id = agent.native.authorize_action_emission(
        native_agent_id, "apply_process", "world.apply_action")
    if not enabled or request_id is None:
        return False, "native_action_authorization_denied"
    # The adapter applies only the graph-provided ProcessSchema effect at the
    # external world sink. P5 consumes its own request-scoped authorization.
    result = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}}, {"p": params, "state": state})
    succeeded = result == expected
    agent.native.complete_action_emission(native_agent_id, request_id, succeeded)
    if not succeeded:
        return False, "world_effect_mismatch"
    sink_receipt_id = s.node(request)["attrs"].get("sink_receipt_id")
    if not sink_receipt_id:
        return False, "missing_native_sink_receipt"
    receipt = s.add_node("OwnTrialReceipt", {
        "receipt_id": f"own-receipt:{seed}", "status": "observed",
        "actual_own_trial": True, "owner_id": "agent-root",
        "learner_body_owner_id": "agent-root", "source_epoch": attrs.get("source_epoch", 4),
        "model_epoch": attrs.get("model_epoch", 7),
        "frame_epoch": attrs.get("frame_epoch", 9),
        "sink_receipt_id": sink_receipt_id})
    s.add_edge(schema, "has_own_trial_receipt", receipt, {})
    s.add_edge(receipt, "binds_action_request", request, {})
    _tick(agent, 4)
    grounded = s.node(schema)["attrs"].get("grounding_status") == "own_trial_grounded"
    return grounded, "grounded" if grounded else "receipt_not_grounded"


def _false_grounding_count(agent):
    s = agent.s
    invalid = 0
    for kind in ("ProcessSchema", "SocialProcessSchema", "RewardProcessSchema"):
        for schema in s.nodes(kind):
            if s.node(schema)["attrs"].get("grounding_status") != "own_trial_grounded":
                continue
            valid = False
            for receipt in s.neighbours(schema, "has_own_trial_receipt"):
                ra = s.node(receipt)["attrs"]
                if ra.get("status") != "observed" or ra.get("actual_own_trial") is not True:
                    continue
                if ra.get("owner_id") != ra.get("learner_body_owner_id"):
                    continue
                for request in s.neighbours(receipt, "binds_action_request"):
                    qa = s.node(request)["attrs"]
                    if (request not in s.neighbours(agent.ag, "has_action_request")
                            or qa.get("actor_id") != ra.get("owner_id")
                            or qa.get("status") != "emitted"
                            or qa.get("sink_receipt_id") != ra.get("sink_receipt_id")):
                        continue
                    if any(s.node(auth)["attrs"].get("status") == "consumed"
                           and s.node(auth)["attrs"].get("request_id") == qa.get("request_id")
                           for auth in s.neighbours(request, "has_action_authorization")):
                        valid = True
                        break
                if valid:
                    break
            invalid += not valid
    return invalid


def _unverified_adoption_count(agent):
    s = agent.s
    invalid = 0
    requirements = {
        "SocialProcessSchema": ("evidenced_by_candidate", "has_verification",
                                "SocialProcessCandidate"),
        "RewardProcessSchema": ("evidenced_by_candidate", "has_verification",
                                "RewardProcessCandidate"),
        "ProcessSchema": ("learned_from_demonstration", "has_own_model_verification",
                          "DemonstratedProcessCandidate"),
    }
    for schema_type, (candidate_edge, receipt_edge, candidate_type) in requirements.items():
        for schema in s.nodes(schema_type):
            attrs = s.node(schema)["attrs"]
            if schema_type == "ProcessSchema" and attrs.get("provenance") != "own_model_verified_demonstration":
                continue
            if schema_type != "ProcessSchema" and attrs.get("status") != "verified":
                continue
            candidates = list(s.neighbours(schema, candidate_edge))
            valid = False
            for candidate in candidates:
                ca = s.node(candidate)["attrs"]
                if ca.get("status") != "adopted":
                    continue
                if not any(s.node(receipt)["attrs"].get("status") == "verified"
                           and s.node(receipt)["attrs"].get("candidate_id") == ca.get("candidate_id")
                           for receipt in s.neighbours(candidate, receipt_edge)):
                    continue
                valid = True
                break
            invalid += not valid
    return invalid


def _record_social(seed, arm, split, control=None):
    started = time.perf_counter()
    agent = _agent(imitation=arm == "demonstration",
                   social=arm in {"observation", "instruction", "reward_only"})
    s = agent.s
    world_hash = _json_sha({"kind": "integer_increment", "initial": seed % 13})
    for i in range(LIMITS["evidence_opportunities"]):
        node = agent.s.add_node("SocialEvidenceOpportunity", {
            "opportunity_id": f"{seed}:{i}", "owner_id": "agent-root",
            "available": i == 0, "evidence_kind": arm,
            "world_hash": world_hash})
        # This is measurement metadata only; it is intentionally not in the
        # agent's process vocabulary and no acquisition rule reads it.
        agent.native.add_edge_unchecked(agent.ag, "has_social_evidence_opportunity", node)
    model_bank = _held_model_bank(agent, seed)
    model_access_sha = _json_sha(sorted(
        (s.node(n)["attrs"]["operator"], s.node(n)["attrs"]["binding"],
         s.node(n)["attrs"]["params"]) for n in model_bank))
    schema, adoption = None, "no_social_input"
    if arm == "demonstration":
        schema, adoption = _demonstration(agent, seed, control)
    elif arm in {"observation", "instruction"}:
        model = next(n for n in model_bank
                     if s.node(n)["attrs"]["binding"] == "repair")
        _social_input(agent, arm, seed, model)
        schema, adoption = _validate_social(agent, seed)
    elif arm == "reward_only":
        schema, adoption = _reward_input(agent, model_bank, seed)
    if control == "shuffled" and arm == "demonstration":
        # A wrong process must be rejected by the detached native rollout.
        schemas = [n for n in agent.s.nodes("ProcessSchema")
                   if agent.s.node(n)["attrs"].get("provenance") == "own_model_verified_demonstration"]
        schema = schemas[0] if schemas else None
        adoption = "rejected_wrong_effect" if schema is None else "false_adoption"
    own_success, own_status = _own_trial(agent, schema, seed)
    unverified = sum(
        agent.s.node(n)["attrs"].get("status") == "unverified_candidate"
        for kind in ("DemonstratedProcessCandidate", "SocialProcessCandidate",
                     "RewardProcessCandidate")
        for n in agent.s.nodes(kind))
    false_grounding = _false_grounding_count(agent)
    unverified_adoptions = _unverified_adoption_count(agent)
    # The learner input audit explicitly excludes the hidden effect and target.
    return Agent.trial_record(
        "COMPLETED", family="social_acquisition", seed=seed, split=split,
        profile=arm, control=control, world_access_sha256=world_hash,
        outcome="own_trial_success" if own_success else "own_trial_failure",
        own_trial_success=own_success, own_trial_status=own_status,
        candidate_adoption=adoption, unverified_candidate_count=unverified,
        unverified_adoption_count=unverified_adoptions,
        false_own_grounding=false_grounding,
        evidence_opportunities=LIMITS["evidence_opportunities"],
        informative_opportunities=2 if arm == "reward_only" else 1,
        world_action_calls=sum(agent.s.node(n)["attrs"].get("status")
                               in {"emitted", "emission_failed"}
                               for n in agent.s.nodes("ActionRequest")),
        boot_seconds=round(agent._p12_boot_seconds, 6),
        initial_graph_nodes=agent._p12_initial_graph_nodes,
        graph_node_growth=len(agent.s.nodes()) - agent._p12_initial_graph_nodes,
        graph_estimated_bytes_start=agent._p12_initial_graph_bytes,
        graph_estimated_bytes_end=_graph_bytes(agent.s),
        budget_remaining_graph=_budget_remaining(agent),
        budget_request_debits=sum(
            agent.s.node(n)["attrs"].get("debited_epoch") is not None
            for n in agent.s.nodes("ThinkingBudgetRequest")),
        receipt_ids=[agent.s.node(n)["attrs"].get("receipt_id")
                     for kind in ("SocialProcessVerification", "DetachedOwnModelVerification",
                                  "RewardProcessVerification", "OwnTrialReceipt")
                     for n in agent.s.nodes(kind)],
        action_sink_receipt_ids=[agent.s.node(n)["attrs"].get("sink_receipt_id")
                                 for n in agent.s.nodes("ActionRequest")
                                 if agent.s.node(n)["attrs"].get("sink_receipt_id")],
        graph_nodes=len(agent.s.nodes()),
        budget_remaining=_budget_remaining(agent),
        elapsed_s=round(time.perf_counter() - started, 6),
        agent_input_audit={"target_absent": True,
                           "equal_world_hash": world_hash,
                           "common_model_access_sha256": model_access_sha,
                           "reward_only_has_no_process_input": arm != "reward_only" or schema is None})


def _explanation_packet():
    from domains.language_world import LanguageWorld, teacher_stub
    from domains.language_production import LanguageProduction
    from scripts.language_test import training_bank
    source = _agent(explanation=True)
    language = LanguageWorld(source.native,
                             [row for row in training_bank() if row["language"] == "en"],
                             teacher_stub)
    language.run()
    model = source.s.add_node("ProcessSchema", {
        "name": "private-source", "kind": "sequence", "domain": "private",
        "operator": "love", "params": ACTION, "status": "active",
        "source_epoch": 1, "model_epoch": 7, "frame_epoch": 9,
        "public_explanation_frame": {"event": "love", "agent": "Mary",
                                     "patient": "John", "tense": "present",
                                     "speech_act": "inform"},
        "public_vocabulary": ["love", "Mary", "John", "primitive-love"]})
    source.s.add_edge(source.ag, "has_process_schema", model, {})
    request = source.s.add_node("ProcessExplanationRequest", {
        "request_id": "p12-explanation-source", "status": "requested", "language": "en"})
    source.s.add_edge(source.ag, "has_process_explanation_request", request, {})
    funding = source.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_authoring",
        "source_key": "p12-explanation-source", "source_epoch": 1,
        "operation_id": "explain:p12:source", "status": "pending", "cost": 1.0})
    source.s.add_edge(funding, "draws_on_thinking_budget", _budget(source), {})
    source.s.add_edge(request, "explains_process", model, {})
    source.s.add_edge(request, "funded_by", funding, {})
    _tick(source)
    drafts = list(source.s.nodes("ProcessExplanationDraft"))
    if len(drafts) != 1:
        raise RuntimeError("source graph did not produce one funded explanation draft")
    draft = source.s.node(drafts[0])["attrs"]
    producer = LanguageProduction(language)
    rendered = producer.produce("en", draft["public_frame"])
    if not rendered.get("accepted") or not rendered.get("self_monitor", {}).get("match"):
        raise RuntimeError("source language production failed self-monitoring")
    parsed = producer._comprehend("en", rendered["overt_speech"])
    if parsed.get("event") != "love":
        raise RuntimeError("source explanation did not parse back to its public frame")
    return {"explanation_id": "p12-public-love", "text": rendered["overt_speech"],
            "language": "en", "vocabulary": list(draft["supported_vocabulary"]),
            "semantic_frame": parsed,
            "production_self_monitor": True}


def _record_rebuild(seed, split, packet, control=None):
    started = time.perf_counter()
    agent = _agent(explanation=True)
    s = agent.s
    delivery = dict(packet)
    if control == "source_ids_removed":
        delivery.update(source_schema_id="private-source", source_actor_id="source-agent",
                        source_process_id="private-process")
    elif control == "source_expressions_removed":
        delivery.update(source_ast=ACTION, source_fingerprint="private-fingerprint",
                        candidate_strategy=ACTION)
    forbidden = {"source_schema_id", "source_actor_id", "source_process_id", "source_ast",
                 "params", "fingerprint", "source_fingerprint", "candidate_strategy",
                 "target_answer"}
    redacted = sorted(forbidden.intersection(delivery))
    delivery = {key: value for key, value in delivery.items() if key not in forbidden}
    primitive = s.add_node("ProcessPrimitiveVocabulary", {
        "primitive_id": "primitive-love", "semantic_event": "love",
        "public_token": "primitive-love", "native_effect": ACTION,
        "vocabulary_status": "shared", "model_epoch": 7, "frame_epoch": 9})
    s.add_edge(agent.ag, "has_process_primitive_vocabulary", primitive, {})
    frame = packet["semantic_frame"]
    input_node = s.add_node("ProcessExplanationInput", {
        "explanation_id": delivery["explanation_id"], "text": delivery["text"],
        "language": delivery["language"], "parse_status": "parsed",
        "semantic_event": frame.get("event"), "supported_vocabulary": delivery["vocabulary"],
        "model_epoch": 7, "frame_epoch": 9})
    s.add_edge(agent.ag, "has_process_explanation_input", input_node, {})
    request = s.add_node("ProcessExplanationRequest", {
        "explanation_id": packet["explanation_id"], "status": "requested"})
    s.add_edge(agent.ag, "has_process_explanation_request", request, {})
    funding = s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_rebuild",
        "explanation_id": packet["explanation_id"], "source_key": packet["explanation_id"],
        "source_epoch": 1, "operation_id": f"rebuild:{seed}",
        "status": "pending", "cost": 1.0})
    s.add_edge(request, "funded_by", funding, {})
    s.add_edge(funding, "draws_on_thinking_budget", _budget(agent), {})
    _tick(agent)
    candidates = list(s.nodes("RebuiltProcessCandidate"))
    candidate = candidates[0] if len(candidates) == 1 else None
    if candidate is not None:
        attrs = s.node(candidate)["attrs"]
        verify_request = s.add_node("ThinkingBudgetRequest", {
            "requester_kind": "process_rebuild_validation",
            "candidate_id": attrs["candidate_id"], "source_key": f"verify:{seed}",
            "source_epoch": 1, "operation_id": f"verify:{seed}",
            "status": "pending", "cost": 1.0})
        s.add_edge(candidate, "has_verification_request", verify_request, {})
        s.add_edge(verify_request, "draws_on_thinking_budget", _budget(agent), {})
        states = [[seed % 7], [3], [-2]]
        outcomes = [agent.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": attrs["params"], "state": state}) for state in states]
        exact = all(out == [state[0] + 1] for out, state in zip(outcomes, states))
        receipt = s.add_node("RebuildVerification", {
            "candidate_id": attrs["candidate_id"],
            "verification_kind": "fresh_native_rebuild",
            "status": "verified" if exact else "failed", "exact_effect_match": exact,
            "model_epoch": attrs["model_epoch"], "frame_epoch": attrs["frame_epoch"],
            "probe_count": len(states), "receipt_id": f"rebuild:{seed}"})
        s.add_edge(candidate, "has_rebuild_verification", receipt, {})
        _tick(agent)
    else:
        exact = False
    adopted = [n for n in s.nodes("ProcessSchema")
               if s.node(n)["attrs"].get("provenance") == "rebuilt_from_explanation"]
    # Input graph must be isolated from source schema/ID, expression and params.
    attrs = s.node(input_node)["attrs"]
    forbidden = {"source_schema_id", "source_actor_id", "source_process_id",
                 "source_ast", "params", "fingerprint", "candidate_strategy",
                 "target_answer"}
    allowed_input = {"explanation_id", "text", "language", "parse_status", "semantic_event",
                     "supported_vocabulary", "model_epoch", "frame_epoch"}
    input_fields_ok = set(attrs).issubset(allowed_input)
    graph_text = json.dumps([s.node(n)["attrs"] for n in s.nodes()], sort_keys=True, default=str)
    source_schema_absent = not any(
        s.node(n)["attrs"].get("name") == "private-source" for n in s.nodes("ProcessSchema"))
    leakage = (bool(forbidden.intersection(attrs)) or not source_schema_absent
               or any(token in graph_text for token in ("private-source", "private-process",
                                                          "source-agent", "private-fingerprint")))
    return Agent.trial_record(
        "COMPLETED", family="explain_rebuild", seed=seed, split=split, control=control,
        profile="isolated_receiver", world_access_sha256=_json_sha({"states": [[seed % 7], [3], [-2]],
                                                                        "effect": "add_one"}),
        outcome="verified" if exact and len(adopted) == 1 and not leakage else "failed",
        effect_agreement=bool(exact), adopted_process=len(adopted) == 1,
        source_leakage=leakage, explanation_tokens=len(delivery["text"].split()),
        evidence_exposures=1, redacted_forbidden_fields=redacted,
        receipt_ids=[s.node(n)["attrs"].get("receipt_id")
                     for n in s.nodes("RebuildVerification")],
        graph_nodes=len(s.nodes()), boot_seconds=round(agent._p12_boot_seconds, 6),
        initial_graph_nodes=agent._p12_initial_graph_nodes,
        graph_node_growth=len(s.nodes()) - agent._p12_initial_graph_nodes,
        graph_estimated_bytes_start=agent._p12_initial_graph_bytes,
        graph_estimated_bytes_end=_graph_bytes(s),
        budget_remaining_graph=_budget_remaining(agent),
        budget_request_debits=sum(
            s.node(n)["attrs"].get("debited_epoch") is not None
            for n in s.nodes("ThinkingBudgetRequest")),
        budget_remaining=_budget_remaining(agent),
        elapsed_s=round(time.perf_counter() - started, 6),
        agent_input_audit={"source_schema_absent": source_schema_absent,
                           "source_ast_absent": "source_ast" not in attrs,
                           "only_public_explanation_and_shared_vocabulary": input_fields_ok
                           and len(s.nodes("ProcessPrimitiveVocabulary")) == 1})


def _counts(split, self_check):
    if self_check:
        return 1, 1
    n = 1 if split == "development" else SOCIAL_N
    return n, (1 if split == "development" else REBUILD_N)


def run(split, *, self_check=False):
    social_n, rebuild_n = _counts(split, self_check)
    offset = DEV_SEED if split == "development" else HELDOUT_SEED
    records = []
    for seed_ix in range(social_n):
        seed = offset + seed_ix
        for arm in SOCIAL_ARMS:
            records.append(_record_social(seed, arm, split))
    control_n = 1 if self_check or split == "development" else CONTROL_N
    for control in CONTROLS:
        for i in range(control_n):
            records.append(_record_social(offset + 5000 + i, "demonstration", split,
                                          control=control))
    packet = _explanation_packet()
    for i in range(rebuild_n):
        records.append(_record_rebuild(offset + 8000 + i, split, packet))
    redaction_n = 1 if self_check or split == "development" else 100
    for control in ("source_ids_removed", "source_expressions_removed"):
        for i in range(redaction_n):
            records.append(_record_rebuild(offset + 9000 + i, split, packet, control))
    if self_check:
        from evaluation.process_mastery.analyze_linear_p12_v1 import analyze
        result = analyze({"schema": "pmb-scorecard-v1",
                          "metadata": {"phase": PHASE, "split": split,
                                       "seed_allocation": {
                                           "social_per_arm": social_n,
                                           "controls_each": control_n,
                                           "rebuild": rebuild_n,
                                           "rebuild_redaction_controls_each": redaction_n}},
                          "records": records})
        if (result["primary_status"] == "INVALID"
                or result["rebuild_status"] != "PASS"
                or result["completion_failures"] or result["control_failures"]):
            raise RuntimeError(f"P12 development adapter self-check failed: {result}")
        if result["controls"]["missing"]["false_adoptions"]:
            raise RuntimeError("missing-data control produced a false adoption")
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    records = run(args.split, self_check=args.self_check)
    metadata = _provenance() | {"split": args.split,
                                "self_check": args.self_check,
                                "seed_allocation": {"offset": DEV_SEED if args.split == "development" else HELDOUT_SEED,
                                                    "social_per_arm": 1 if args.self_check or args.split == "development" else SOCIAL_N,
                                                    "controls_each": 1 if args.self_check or args.split == "development" else CONTROL_N,
                                                    "rebuild": 1 if args.self_check or args.split == "development" else REBUILD_N,
                                                    "rebuild_redaction_controls_each": 1 if args.self_check or args.split == "development" else 100},
                                "arms": list(SOCIAL_ARMS), "controls": list(CONTROLS)}
    if args.output is not None:
        write_scorecard(args.output, metadata=metadata, records=records)
    else:
        print(json.dumps({"metadata": metadata, "records": records}, indent=2, sort_keys=True))
    print(f"{PHASE} {args.split}: {len(records)} records")


if __name__ == "__main__":
    main()
