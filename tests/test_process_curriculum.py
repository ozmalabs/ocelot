"""P15.03 graph-owned curriculum from source-verified learning residuals."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")

from evaluation.process_mastery.harness import Agent  # noqa: E402


def _agent(*, max_evidence=512, max_tasks=256, budget=32.0):
    agent = Agent(
        extra_seeds=("process_curriculum",),
        policy_overrides={"ProcessCurriculumPolicy": {
            "enabled": 1.0, "max_evidence": float(max_evidence),
            "max_tasks": float(max_tasks),
        }},
        budget={"enabled": 1.0, "capacity": budget, "remaining": budget,
                "refill_per_epoch": 0.0, "last_refill_epoch": -100.0},
    )
    return agent


def _tick(agent, count=12):
    for _ in range(count):
        agent.s.tick(4000)


def _counterexample(agent, event_id, *, split="training", source_epoch=3):
    hyp = agent.s.add_node("ProcessInductionHypothesis", {
        "owner_id": "owner-a", "action_kind": "press", "object_type": "switch",
        "feature_key": "light", "before_value": "off", "after_value": "on",
        "source_epoch": source_epoch, "model_epoch": 2, "frame_epoch": 5,
        "status": "disputed", "counterexample_count": 1,
    })
    ce = agent.s.add_node("ProcessCounterexample", {
        "event_id": event_id, "status": "observed",
        "observed_after_value": "on",
    })
    obs = agent.s.add_node("TransitionObservation", {
        "owner_id": "owner-a", "event_id": event_id,
        "action_kind": "press", "object_type": "switch",
        "feature_key": "light", "before_value": "off",
        "after_value": "on", "split": split,
        "source_epoch": source_epoch, "model_epoch": 2, "frame_epoch": 5,
    })
    agent.s.add_edge(agent.ag, "has_process_induction_hypothesis", hyp, {})
    agent.s.add_edge(hyp, "has_counterexample", ce, {})
    agent.s.add_edge(ce, "counterexample_transition", obs, {})
    return hyp, ce, obs


def _curriculum_nodes(agent, type_):
    return [n for n in agent.s.nodes() if agent.s.node(n)["type"] == type_]


def test_curriculum_targets_real_residual_without_exposing_answer():
    agent = _agent()
    _counterexample(agent, "observed-event-1")
    _tick(agent)
    evidence = _curriculum_nodes(agent, "ProcessCurriculumEvidence")
    tasks = _curriculum_nodes(agent, "ProcessCurriculumTask")
    assert len(evidence) == len(tasks) == 1
    ea = agent.s.node(evidence[0])["attrs"]
    ta = agent.s.node(tasks[0])["attrs"]
    assert ea["source_kind"] == "verified_counterexample"
    assert ta["task_kind"] == "counterexample_discrimination"
    assert ta["split"] == "training"
    assert ta["expected_outcome"] == "unknown"
    assert ta["before_value"] == "off"
    assert "observed_after_value" not in ta
    assert ta["answer_fields_absent"] is True


def test_unlearnable_task_is_retired_without_repetition():
    agent = _agent()
    _counterexample(agent, "unlearnable-event")
    _tick(agent)
    task = _curriculum_nodes(agent, "ProcessCurriculumTask")[0]
    evidence = agent.s.neighbours(task, "from_evidence")[0]
    outcome = agent.s.add_node("ProcessCurriculumOutcome", {
        "status": "observed", "evidence_status": "observed",
        "assessment": "unlearnable", "source_epoch": 3,
    })
    agent.s.add_edge(task, "has_outcome", outcome, {})
    agent.s.add_edge(outcome, "outcome_for", task, {})
    _tick(agent, 20)
    assert agent.s.node(task)["attrs"]["status"] == "retired_unlearnable"
    assert agent.s.node(evidence)["attrs"]["status"] == "suppressed"
    _tick(agent, 20)
    assert len(_curriculum_nodes(agent, "ProcessCurriculumTask")) == 1


def test_stale_success_recheck_requires_a_fresh_training_task():
    agent = _agent()
    domain = agent.add_domain("curriculum-domain", "curriculum_only", [[0, 1]], {})
    task = agent.add_solve_task("curriculum-domain", [0, 1], [1, 0],
                                task_id="fresh-training", split="training",
                                source_epoch=0, model_epoch=0, frame_epoch=0)
    entry = agent.s.add_node("StrategyLibraryEntry", {
        "status": "stale", "source_task": "old-success", "kind": "curriculum_only",
        "state_size": 2, "goal_size": 2, "source_epoch": -1,
        "model_epoch": -1, "frame_epoch": -1,
    })
    agent.s.add_edge(agent.ag, "has_strategy_library_entry", entry, {})
    agent.s.add_edge(entry, "about_domain", domain, {})
    _tick(agent)
    assert len(_curriculum_nodes(agent, "ProcessCurriculumEvidence")) == 1
    task_node = _curriculum_nodes(agent, "ProcessCurriculumTask")[0]
    attrs = agent.s.node(task_node)["attrs"]
    assert attrs["task_kind"] == "stale_strategy_recheck"
    assert attrs["split"] == "training"
    assert agent.s.neighbours(task_node, "from_evidence")
    assert agent.s.node(task)["attrs"]["steps"] == 0


def test_sealed_holdout_never_becomes_curriculum_input():
    agent = _agent()
    _counterexample(agent, "heldout-event", split="heldout")
    agent.s.add_node("SealedPmbEvaluation", {
        "task_id": "sealed-42", "answer_label": "secret-label",
        "hidden_strategy": ["secret-process"],
    })
    agent.add_domain("curriculum-domain", "permutation", [[0, 1]],
                     {"swap": [1, 0]})
    heldout = agent.add_solve_task("curriculum-domain", [1, 0], [0, 1],
                                   task_id="heldout-task", split="heldout",
                                   source_epoch=0, model_epoch=0, frame_epoch=0)
    _tick(agent, 20)
    assert _curriculum_nodes(agent, "ProcessCurriculumEvidence") == []
    assert _curriculum_nodes(agent, "ProcessCurriculumTask") == []
    assert agent.s.node(heldout)["attrs"]["split"] == "heldout"
    seed = json.loads((ROOT / "seeds/process_curriculum.json").read_text())
    serialized = json.dumps(seed)
    assert "SealedPmbEvaluation" not in serialized
    assert "answer_label" not in serialized
    assert "hidden_strategy" not in serialized


def test_growth_and_cost_are_bounded():
    agent = _agent(max_evidence=2, max_tasks=1, budget=8.0)
    for i in range(8):
        _counterexample(agent, f"bounded-event-{i}")
    _tick(agent, 30)
    assert len(_curriculum_nodes(agent, "ProcessCurriculumEvidence")) <= 2
    assert len(_curriculum_nodes(agent, "ProcessCurriculumTask")) <= 1
    assert agent.s.node(_curriculum_nodes(agent, "ProcessCurriculumPolicy")[0])["attrs"]["scheduler_status"] in {
        "active", "ready",
    }
    assert agent.s.node(_curriculum_nodes(agent, "ThinkingBudget")[0])["attrs"]["remaining"] >= 7.0


def test_curriculum_generator_matches_committed_seed():
    from scripts.gen_process_curriculum_seed import OUT, build

    expected = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    assert OUT.read_text(encoding="utf-8") == expected
