"""P21 generated tasks are delivered as real events to native learning."""
from __future__ import annotations

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.target_learner import NativeTargetLearner
from evaluation.process_mastery.target_learning_worlds import ThermalWorld


def _agent():
    return Agent(
        extra_seeds=("curriculum_learning_bridge",), track_i=False,
        policy_overrides={
            "ProcessCurriculumPolicy": {"enabled": 1.0},
            "CurriculumLearningBridgePolicy": {"enabled": 1.0},
            "ModelLearningPolicy": {"enabled": 1.0},
            "TargetLearningPolicy": {"enabled": 0.0},
        },
        budget={"enabled": 1.0, "capacity": 32.0, "remaining": 32.0,
                "refill_per_epoch": 0.0, "last_refill_epoch": -100.0})


def _disputed_training_residual(agent):
    hyp = agent.s.add_node("ProcessInductionHypothesis", {
        "hypothesis_key": "owner:warm:ThermalSample:temperature:cold->cold:3:2",
        "owner_id": "owner-a", "action_kind": "warm", "object_type": "ThermalSample",
        "feature_key": "temperature", "before_value": "cold", "after_value": "cold",
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
        "status": "disputed", "counterexample_count": 1})
    ce = agent.s.add_node("ProcessCounterexample", {
        "event_id": "residual-thermal-1", "status": "observed",
        "observed_after_value": "warm"})
    obs = agent.s.add_node("TransitionObservation", {
        "owner_id": "owner-a", "event_id": "residual-thermal-1",
        "action_kind": "warm", "object_type": "ThermalSample",
        "feature_key": "temperature", "before_value": "cold",
        "after_value": "warm", "split": "training", "source_epoch": 3,
        "model_epoch": 2, "frame_epoch": 5})
    agent.s.add_edge(agent.ag, "has_process_induction_hypothesis", hyp, {})
    agent.s.add_edge(hyp, "has_counterexample", ce, {})
    agent.s.add_edge(ce, "counterexample_transition", obs, {})


def _tick(agent, count=12):
    for _ in range(count):
        agent.s.tick(4000)


def test_generated_task_reaches_learner_and_result_changes_native_state():
    agent = _agent()
    budgets = [n for n in agent.s.nodes("ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    budget = budgets[0]
    starting_budget = agent.s.node(budget)["attrs"]["remaining"]
    _disputed_training_residual(agent)
    _tick(agent)
    assert agent.s.node(budget)["attrs"]["remaining"] < starting_budget
    tasks = agent.s.nodes("ProcessCurriculumTask")
    requests = agent.s.nodes("CurriculumTrainingRequest")
    assert len(tasks) == len(requests) == 1
    request = requests[0]
    attrs = agent.s.node(request)["attrs"]
    assert attrs["split"] == "training" and attrs["status"] == "authorized"
    assert "after_value" not in attrs and "expected_after_value" not in attrs

    learner = NativeTargetLearner(agent=agent, owner_id="owner-a")
    world = ThermalWorld(object_ids=("curriculum-a", "curriculum-b"))
    observations = []
    for object_id in ("curriculum-a", "curriculum-b"):
        receipt = world.apply(object_id, "warm")
        observations.append(learner.observe_world_receipt(
            receipt, source_epoch=int(attrs["source_epoch"]),
            model_epoch=int(attrs["model_epoch"]), frame_epoch=int(attrs["frame_epoch"])))
    learner.settle()
    for observation in observations:
        agent.s.add_edge(request, "has_training_receipt", observation, {})
    agent.s.set_attr(request, "status", "executed")
    _tick(agent)

    assert len(agent.s.nodes("ProcessInductionHypothesis")) >= 2
    outcomes = agent.s.nodes("ProcessCurriculumOutcome")
    assert len(outcomes) == 1
    assert agent.s.node(outcomes[0])["attrs"]["assessment"] == "tractable_progress"
    assert agent.s.node(tasks[0])["attrs"]["status"] == "completed"


def test_generated_training_task_does_not_receive_sealed_eval_identity():
    agent = _agent()
    _disputed_training_residual(agent)
    _tick(agent)
    task = agent.s.node(agent.s.nodes("ProcessCurriculumTask")[0])["attrs"]
    request = agent.s.node(agent.s.nodes("CurriculumTrainingRequest")[0])["attrs"]
    for attrs in (task, request):
        assert attrs["split"] == "training"
        assert attrs["expected_outcome"] == "unknown"
        assert not {"sealed_eval_id", "answer", "expected_answer",
                    "expected_after_value"}.intersection(attrs)


def test_empty_or_failed_delivery_does_not_create_learning_outcome():
    agent = _agent()
    _disputed_training_residual(agent)
    _tick(agent)
    request = agent.s.nodes("CurriculumTrainingRequest")[0]
    agent.s.set_attr(request, "status", "executed")
    _tick(agent)
    assert agent.s.nodes("ProcessCurriculumOutcome") == []


def test_state_perturbation_changes_world_execution_and_abstains():
    agent = _agent()
    _disputed_training_residual(agent)
    _tick(agent)
    request = agent.s.nodes("CurriculumTrainingRequest")[0]
    agent.s.set_attr(request, "action_kind", "cool")
    world = ThermalWorld(object_ids=("perturbed-a", "perturbed-b"))
    try:
        world.apply("perturbed-a", agent.s.node(request)["attrs"]["action_kind"])
    except ValueError:
        pass
    else:
        raise AssertionError("perturbed task unexpectedly executed in the target world")
    assert world.receipts == []
    assert agent.s.nodes("ProcessCurriculumOutcome") == []
