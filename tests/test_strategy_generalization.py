"""P19 lifted ordered strategies retain native preconditions and provenance."""
from evaluation.process_mastery.harness import Agent


def _agent():
    return Agent(track_i=True, extra_seeds=("strategy_discovery",),
        policy_overrides={"StrategyDiscoveryPolicy": {"enabled": 1.0, "allow_lift": 1.0}})


def _tick(agent, count=16):
    for _ in range(count):
        agent.s.tick(4000)


def test_new_binding_uses_discovered_strategy():
    agent = _agent()
    domain = agent.add_domain("lift", "permutation", [[0, 1, 2]], {
        "turn": [1, 2, 0]})
    source = agent.add_solve_task("lift", [0, 1, 2], [1, 2, 0])
    _tick(agent)
    assert agent.attrs(source)["status"] == "solved"
    strategy = agent.nodes("DiscoveredStrategy")[0]
    assert agent.attrs(strategy)["source"] == "observed_graph_trace"
    for policy in agent.nodes("SolverPolicy"):
        agent.s.set_attr(policy, "enabled", 0.0)

    initial = [2, 0, 1]
    # This target differs from the source task's goal. The only available
    # route with primitive solving disabled is the acquired strategy.
    goal = [0, 1, 2]
    task = agent.add_solve_task("lift", initial, goal)
    _tick(agent)
    assert agent.attrs(task)["strategy_started"] == 1
    assert agent.attrs(task)["status"] == "solved"
    assert agent.attrs(task)["state"] == goal
    assert agent.attrs(agent.s.neighbours(task, "executes_discovered_strategy")[0])["source"] == "observed_graph_trace"


def test_lift_rejects_different_object_count_and_stale_constraints():
    agent = _agent()
    domain = agent.add_domain("lift", "permutation", [[0, 1, 2]], {
        "turn": [1, 2, 0]})
    source = agent.add_solve_task("lift", [0, 1, 2], [1, 2, 0])
    _tick(agent)
    assert agent.attrs(source)["status"] == "solved"
    for policy in agent.nodes("SolverPolicy"):
        agent.s.set_attr(policy, "enabled", 0.0)

    larger = agent.add_solve_task("lift", [0, 1, 2, 3], [1, 2, 0, 3])
    agent.s.set_attr(domain, "frame_epoch", 1.0)
    stale = agent.add_solve_task("lift", [2, 0, 1], [0, 1, 2])
    _tick(agent)
    assert "strategy_started" not in agent.attrs(larger)
    assert "strategy_started" not in agent.attrs(stale)
