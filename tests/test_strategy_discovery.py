"""P10.04 graph strategy discovery and trace provenance gates."""
from evaluation.process_mastery.harness import Agent


def _agent(*, budget=30.0, policies=None):
    overrides = {"StrategyDiscoveryPolicy": {"enabled": 1.0}}
    overrides.update(policies or {})
    return Agent(track_i=True, extra_seeds=("strategy_discovery",),
                 policy_overrides=overrides,
                 budget={"enabled": 1.0, "remaining": budget,
                         "last_refill_epoch": 0.0, "refill_per_epoch": 0.0})


def _tick(agent, n=12):
    for _ in range(n):
        agent.s.tick(4000)


def _replay(agent, state, trace):
    for process in trace:
        state = agent.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": agent.attrs(process)["params"], "state": state})
    return state


def test_agent_finds_constraint_preserving_strategy():
    agent = _agent()
    agent.add_domain("pair", "permutation", [[0, 1, 2]], {"cycle": [1, 2, 0]})
    task = agent.add_solve_task("pair", [0, 1, 2], [2, 0, 1])
    _tick(agent)
    strategies = agent.nodes("DiscoveredStrategy")
    assert len(strategies) == 1
    strategy = agent.attrs(strategies[0])
    assert strategy["source"] == "observed_graph_trace"
    assert strategy["status"] == "verified"
    assert _replay(agent, [0, 1, 2], strategy["trace"]) == agent.attrs(task)["goal"]


def test_found_strategy_replays_through_native_process_view():
    agent = _agent()
    agent.add_domain("reuse", "permutation", [[0, 1, 2]], {"cycle": [1, 2, 0]})
    source = agent.add_solve_task("reuse", [0, 1, 2], [2, 0, 1])
    _tick(agent)
    assert agent.attrs(source)["status"] == "solved"
    for policy in agent.nodes("SolverPolicy"):
        agent.s.set_attr(policy, "enabled", 0.0)
    replay = agent.add_solve_task("reuse", [0, 1, 2], [2, 0, 1])
    _tick(agent)
    assert agent.attrs(replay)["status"] == "solved"
    assert agent.attrs(replay)["strategy_started"] == 1
    assert _replay(agent, [0, 1, 2], agent.attrs(replay)["trace"]) == [2, 0, 1]


def test_delayed_progress_not_greedy_trap():
    agent = _agent()
    agent.add_domain("delayed", "permutation", [[0, 1, 2, 3]], {
        "a": [1, 0, 2, 3], "b": [0, 2, 1, 3]})
    task = agent.add_solve_task("delayed", [0, 1, 2, 3], [2, 0, 1, 3])
    _tick(agent)
    trace = agent.attrs(task)["trace"]
    assert agent.attrs(task)["status"] == "solved"
    assert any(agent.attrs(p)["provenance"].startswith("invented_by:") for p in trace)
    assert _replay(agent, [0, 1, 2, 3], trace) == [2, 0, 1, 3]


def test_odd_wall_uses_verified_breaker():
    agent = _agent(policies={"InvariantMinerPolicy": {"enabled": 1.0},
                             "SolverPolicy": {"enabled": 0.0},
                             "InventionPolicy": {"enabled": 0.0}})
    for node in agent.nodes("ThinkingBudget"):
        agent.s.set_attr(node, "enabled", 0.0)
    agent.add_domain("wall", "permutation", [[0, 1, 2]], {
        "even_cycle": [1, 2, 0], "odd_breaker": [1, 0, 2]})
    even = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": "wall", "domain_kind": "permutation",
        "name": "invented_even", "params": [1, 2, 0], "cost": 1.0,
        "provenance": "invented_by:commutator", "status": "active", "invented": 1,
    })
    agent.s.add_edge(agent.ag, "has_process_schema", even, {})
    agent.s.add_edge(agent.domains["wall"], "has_invented_process", even, {})
    task = agent.add_solve_task("wall", [0, 1, 2], [1, 0, 2])
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent, 5)
    trace = agent.attrs(task)["trace"]
    assert trace
    assert agent.attrs(trace[0])["name"] == "odd_breaker"
    assert agent.attrs(trace[0])["fingerprint_checked"] == 1


def test_trace_contains_only_graph_decisions():
    agent = _agent()
    agent.add_domain("trace", "permutation", [[0, 1, 2]], {"r": [1, 2, 0]})
    task = agent.add_solve_task("trace", [0, 1, 2], [2, 0, 1])
    assert "strategy" not in agent.attrs(task) and "solution_trace" not in agent.attrs(task)
    _tick(agent)
    trace = agent.attrs(task)["trace"]
    assert trace
    schemas = set(agent.nodes("ProcessSchema"))
    assert set(trace) <= schemas
    assert _replay(agent, [0, 1, 2], trace) == agent.attrs(task)["goal"]
