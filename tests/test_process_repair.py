"""P9.04 supported native repair boundary and explicit unsupported states."""
from evaluation.process_mastery.harness import Agent


def _apply(agent, process, state):
    return agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": process, "state": state})


def test_repair_candidate_reverified_on_fresh_states():
    agent = Agent(track_i=False)
    add_one = ["add", [1]]
    fresh = [[0], [4]]
    goals = [[1], [5]]
    receipts = [_apply(agent, add_one, state) for state in fresh]
    assert receipts == goals
    # Native transition evaluation is available; graph-level candidate
    # adoption and epoch invalidation remain unimplemented in this phase.
    assert _apply(agent, add_one, [8]) == [9]


def test_no_repair_does_not_invent_inverse():
    agent = Agent(track_i=False)
    many_to_one = [[1, 0], [0, 0]]
    assert _apply(agent, many_to_one, [0, 1]) == [0, 0]
    inverse = agent.native.evaluate(
        {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}},
        {"p": many_to_one})
    assert inverse is None


def test_distribution_support_retained():
    agent = Agent(track_i=False)
    # No distribution DSL term or graph adapter exists yet. Unknown remains
    # unknown instead of being collapsed into a deterministic process.
    assert agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": ["stochastic", [["outcome-a", 0.25], ["outcome-b", 0.5]]],
         "state": [0]}) is None


def test_model_epoch_invalidates_repair():
    agent = Agent(track_i=False)
    stale_process = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "params": [1, 0], "effect_evaluation": "opaque:stale_model",
        "model_epoch": 8, "verified_model_epoch": 7,
    })
    assert agent.attrs(stale_process)["model_epoch"] != agent.attrs(stale_process)["verified_model_epoch"]
    assert agent.attrs(stale_process)["effect_evaluation"] == "opaque:stale_model"
