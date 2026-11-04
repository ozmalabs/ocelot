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
    verified = agent.native.evaluate(
        {"type": "ProcessRepairVerify", "p": {"type": "Var", "name": "p"},
         "fresh_states": {"type": "Var", "name": "fresh"},
         "goals": {"type": "Var", "name": "goals"}},
        {"p": add_one, "fresh": fresh, "goals": goals})
    assert verified is True
    rejected = agent.native.evaluate(
        {"type": "ProcessRepairVerify", "p": {"type": "Var", "name": "p"},
         "fresh_states": {"type": "Var", "name": "fresh"},
         "goals": {"type": "Var", "name": "goals"}},
        {"p": add_one, "fresh": fresh, "goals": [[1], [4]]})
    assert rejected is False
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
    result = agent.native.evaluate(
        {"type": "ProcessDistribution", "outcomes": {"type": "Var", "name": "outcomes"}},
        {"outcomes": [["outcome-a", 0.25], ["outcome-b", 0.5]]})
    assert result == ((("outcome-a", 0.25), ("outcome-b", 0.5)), 0.25)
    assert agent.native.evaluate(
        {"type": "ProcessDistribution", "outcomes": {"type": "Var", "name": "outcomes"}},
        {"outcomes": [["outcome-a", 0.7], ["outcome-b", 0.4]]}) is None


def test_model_epoch_invalidates_repair():
    agent = Agent(track_i=True, policy_overrides={"InventionPolicy": {"enabled": 1.0, "offline_enabled": 0.0}})
    repair = agent.s.add_node("ProcessRepairCandidate", {
        "status": "candidate", "model_epoch": 7, "source_model_epoch": 7,
        "params": ["add", [1]], "fresh_states": [[0], [4]], "goals": [[1], [5]],
    })
    agent.s.add_edge(agent.ag, "has_repair_candidate", repair, {})
    for _ in range(3):
        agent.s.tick(1000)
    assert agent.attrs(repair)["status"] == "verified"
    assert agent.attrs(repair)["verified_model_epoch"] == 7
    agent.s.set_attr(repair, "model_epoch", 8)
    for _ in range(3):
        agent.s.tick(1000)
    assert agent.attrs(repair)["status"] == "stale"
