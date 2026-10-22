"""Source-specific P20 adapters preserve evidence into native learning."""
import pytest

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.observed_sequence_inputs import (
    demonstrated_episode, instructed_episode, reward_only_episode,
    witnessed_episode,
)
from evaluation.process_mastery.target_learning_worlds import RequestRepairWorld
from domains.language_production import LanguageProduction
from domains.language_world import LanguageWorld, make_stub_teacher
from domains.process_explanation_language import (parse_ordered_explanation,
                                                   produce_ordered_explanation)
from scripts.language_test import training_bank


def _agent():
    agent = Agent(extra_seeds=("thinking_budget", "social_process", "process_schema",
                               "observed_sequence_learning"), track_i=False,
                  policy_overrides={"SocialProcessPolicy": {"enabled": 1.0},
                                    "ObservedSequenceLearningPolicy": {"enabled": 1.0}},
                  budget={"enabled": 1.0, "remaining": 20.0,
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    for operator in ("request", "repair"):
        model = agent.s.add_node("ProcessSchema", {
            "name": operator, "kind": "sequence", "domain": "social",
            "operator": operator, "params": ["seq", ["add", [1]]],
            "status": "active", "source_epoch": 4, "model_epoch": 7,
            "frame_epoch": 9})
        agent.s.add_edge(agent.ag, "has_process_schema", model, {})
    return agent


def _run(agent):
    for _ in range(24):
        if not agent.s.tick(1000):
            break


def _receipts(world_id):
    world = RequestRepairWorld(world_id=world_id)
    return [world.apply("request"), world.apply("repair")]


def _candidate(agent):
    _run(agent)
    candidates = agent.s.nodes("ObservedProcessSequenceCandidate")
    return agent.s.node(candidates[0])["attrs"] if candidates else None


def test_observation_adapter_requires_actual_ordered_world_receipts():
    agent = _agent()
    budget = agent.s.node(agent.s.nodes("ThinkingBudget")[0])["attrs"]["remaining"]
    witnessed_episode(agent, episode_id="witness", receipts=_receipts("witness-world"))
    attrs = _candidate(agent)
    assert attrs["source_kind"] == "witnessed_interaction"
    assert attrs["action_sequence"] == ["seq", ["request", "repair"]]
    assert attrs["actor_outcome_is_own_trial"] is False
    assert len(agent.s.nodes("ObservedInteractionTrace")) == 1
    request = next(node for node in agent.s.nodes("ThinkingBudgetRequest")
                   if agent.s.node(node)["attrs"].get("requester_kind")
                   == "observed_sequence_learning")
    assert agent.s.node(request)["attrs"]["status"] == "approved"
    assert agent.s.node(request)["attrs"].get("debited_epoch") is not None
    assert agent.s.node(agent.s.nodes("ThinkingBudget")[0])["attrs"]["remaining"] < budget


def test_demonstration_adapter_keeps_the_other_actor_and_receipt_ids():
    agent = _agent()
    demonstrated_episode(agent, episode_id="demo", demonstration={
        "status": "complete", "actor_id": "demonstrator",
        "receipts": _receipts("demo-world")})
    attrs = _candidate(agent)
    assert attrs["source_kind"] == "demonstration"
    assert attrs["actor_id"] == "demonstrator"
    assert len(agent.s.nodes("ProcessDemonstration")) == 1


def test_instruction_adapter_requires_a_successful_public_parse():
    agent = _agent()
    domain_bank = training_bank() + [
        {"text": "The peer requests the case.", "language": "en",
         "expected_meaning": {"event": "request", "agent": "peer",
                              "patient": "case", "tense": "present"}},
        {"text": "The peer repaired the case.", "language": "en",
         "expected_meaning": {"event": "repair", "agent": "peer",
                              "patient": "case", "tense": "past"}},
    ]
    teacher = make_stub_teacher({"en": {"peer": "peer", "requests": ("request", "present"),
                                          "repaired": ("repair", "past"), "case": "case"}})
    parser_world = LanguageWorld(agent.native, domain_bank, teacher)
    parser_world.run()
    production = LanguageProduction(parser_world)
    authored = produce_ordered_explanation("en", [
        {"precondition": "idle", "frame": {"event": "request", "agent": "peer",
                                                  "patient": "case", "tense": "present",
                                                  "speech_act": "inform"}},
        {"precondition": "requested", "frame": {"event": "repair", "agent": "peer",
                                                      "patient": "case", "tense": "past",
                                                      "speech_act": "inform"}},
    ], production)
    assert authored["status"] == "produced"
    parsed = parse_ordered_explanation(authored["text"], "en", production)
    instructed_episode(agent, episode_id="instruction", text=authored["text"],
                       parsed=parsed)
    attrs = _candidate(agent)
    assert attrs["source_kind"] == "parsed_instruction"
    assert agent.s.node(agent.s.nodes("ParsedProcessInstruction")[0])["attrs"][
        "source_ast_included"] is False
    with pytest.raises(ValueError, match="did not parse"):
        instructed_episode(agent, episode_id="bad", text="unparsed", parsed={
            "parse_status": "failed"})


def test_reward_adapter_records_feedback_but_native_learner_abstains():
    agent = _agent()
    reward_only_episode(agent, episode_id="reward", feedback={
        "status": "observed", "outcome": "rewarded", "reward_value": 1.0})
    assert _candidate(agent) is None
    results = agent.s.nodes("ObservedSequenceInferenceResult")
    assert len(results) == 1
    assert agent.s.node(results[0])["attrs"]["status"] == "abstained_underidentified"
    assert "action_sequence" not in agent.s.node(agent.s.nodes("SocialEpisode")[0])["attrs"]


def test_adapters_reject_mislabeled_or_incomplete_evidence():
    agent = _agent()
    with pytest.raises(ValueError, match="does not show"):
        witnessed_episode(agent, episode_id="wrong", receipts=[
            _receipts("wrong-world")[1], _receipts("wrong-world-2")[0]])
    with pytest.raises(ValueError, match="demonstration required"):
        demonstrated_episode(agent, episode_id="self", demonstration={
            "status": "complete", "actor_id": "learner", "receipts": _receipts("self")})
