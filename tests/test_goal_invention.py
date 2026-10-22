"""P10 contract acceptance; later P10 tasks add graph policies and behavior."""
import pytest

from evaluation.process_mastery.harness import Agent


WILD = "·?·"


def test_lift_preserves_bindings():
    agent = Agent(track_i=False)
    witness = agent.native.evaluate(
        {"type": "AntiUnifyWitness", "values": {"type": "Var", "name": "values"},
         "wild": WILD},
        {"values": [
            {"op": "swap", "i": 0, "size": 3},
            {"op": "swap", "i": 2, "size": 5},
        ]})
    template, substitutions = witness
    substitute = {"type": "Substitute", "template": {"type": "Var", "name": "template"},
                  "sigma": {"type": "Var", "name": "sigma"}, "wild": WILD}
    rebuilt = [agent.native.evaluate(substitute, {
        "template": template, "sigma": sigma}) for sigma in substitutions]
    assert rebuilt == [
        {"op": "swap", "i": 0, "size": 3},
        {"op": "swap", "i": 2, "size": 5},
    ]


def test_unseen_size_preconditions():
    agent = Agent(track_i=False)
    constraint = {"type": "Lt", "a": {"type": "Var", "name": "index"},
                  "b": {"type": "Var", "name": "size"}}
    assert agent.native.evaluate(constraint, {"index": 4, "size": 5}) is True
    assert agent.native.evaluate(constraint, {"index": 5, "size": 5}) is False
    assert agent.native.evaluate(constraint, {"index": 5, "size": 6}) is True


def test_goal_gap_mints_interface():
    pytest.skip("P10.03 adds the GoalInventionPolicy graph producer")


def test_no_handwritten_strategy_input():
    agent = Agent(track_i=False)
    agent.add_domain("plain", "permutation", [[0, 1, 2]], {"held": [1, 2, 0]})
    task = agent.add_solve_task("plain", [0, 1, 2], [1, 2, 0])
    attrs = agent.attrs(task)
    assert "strategy" not in attrs and "solution_trace" not in attrs
    assert not agent.nodes("StrategyRecord")
    assert not agent.nodes("ImaginedPlanCandidate")
