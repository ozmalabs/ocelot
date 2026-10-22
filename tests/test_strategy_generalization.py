"""P19 lifted ordered strategies retain native preconditions and provenance."""
from evaluation.process_mastery.harness import Agent
from tests.test_open_process_search import _agent as _open_agent
from tests.test_open_process_search import _apply as _apply_native
from tests.test_open_process_search import _compose


def _agent():
    return Agent(track_i=True, extra_seeds=("strategy_discovery",),
        policy_overrides={"StrategyDiscoveryPolicy": {"enabled": 1.0, "allow_lift": 1.0}})


def _tick(agent, count=16):
    for _ in range(count):
        agent.s.tick(4000)


def _new_binding_transfer():
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


def test_new_binding_uses_discovered_strategy():
    _new_binding_transfer()


def test_strategy_not_exact_trace_lookup():
    _new_binding_transfer()


def test_failed_constraint_not_replayed():
    agent = _agent()
    domain = agent.add_domain("lift", "permutation", [[0, 1, 2]], {
        "turn": [1, 2, 0]})
    source = agent.add_solve_task("lift", [0, 1, 2], [1, 2, 0])
    _tick(agent)
    assert agent.attrs(source)["status"] == "solved"
    for policy in agent.nodes("SolverPolicy"):
        agent.s.set_attr(policy, "enabled", 0.0)

    failed_initial = [2, 1, 0]
    failed = agent.add_solve_task("lift", failed_initial, failed_initial)
    _tick(agent)
    assert agent.attrs(failed)["status"] == "strategy_failed"
    strategy = agent.nodes("DiscoveredStrategy")[0]
    failures = agent.native.neighbours(strategy, "has_strategy_failure_constraint")
    assert len(failures) == 1
    assert agent.attrs(failures[0])["source"] == "native_strategy_replay"

    retry = agent.add_solve_task("lift", failed_initial, failed_initial)
    _tick(agent)
    assert "strategy_started" not in agent.attrs(retry)

    process = agent.attrs(strategy)["trace"][0]
    process_params = agent.attrs(process)["params"]
    transferable_initial = [2, 0, 1]
    transferable_goal = _apply_native(agent, process_params, transferable_initial)
    transfer = agent.add_solve_task("lift", transferable_initial, transferable_goal)
    _tick(agent)
    assert agent.attrs(transfer)["status"] == "solved"

    larger = agent.add_solve_task("lift", [0, 1, 2, 3], [1, 2, 0, 3])
    agent.s.set_attr(domain, "frame_epoch", 1.0)
    stale = agent.add_solve_task("lift", [2, 0, 1], [0, 1, 2])
    _tick(agent)
    assert "strategy_started" not in agent.attrs(larger)
    assert "strategy_started" not in agent.attrs(stale)


def test_new_object_count_uses_witnessed_lifted_strategy():
    from tests.test_process_lifting import _commutator

    agent = Agent(extra_seeds=("strategy_discovery", "process_lifting"),
        policy_overrides={
            "StrategyDiscoveryPolicy": {"enabled": 1.0, "allow_lift": 1.0},
            "ProcessLiftingPolicy": {"enabled": 1.0, "unseen_size_enabled": 1.0},
        })
    for size in (3, 5):
        domain_name = f"train-{size}"
        agent.add_domain(domain_name, "permutation", [list(range(size))],
                         {f"commutator-{size}": _commutator(size)}, size=size)
        process = agent.schemas(domain_name)[0]
        agent.s.set_attr(process, "operator", "commutator")
        agent.s.set_attr(process, "expr_tree", [
            "commutator", ["cycle", size, 0, size], ["swap", size, 0, 1]])
    _tick(agent, 8)
    families = agent.nodes("LiftedProcessFamily")
    assert len(families) == 1

    source_state = [0, 1, 2]
    source_process = agent.schemas("train-3")[0]
    source_goal = _apply_native(agent, agent.attrs(source_process)["params"], source_state)
    source_task = agent.add_solve_task("train-3", source_state, source_goal)
    _tick(agent)
    assert agent.attrs(source_task)["status"] == "solved"
    assert len(agent.nodes("DiscoveredStrategy")) == 1
    for policy in agent.nodes("SolverPolicy"):
        agent.s.set_attr(policy, "enabled", 0.0)

    target_size = 6
    target_domain = agent.add_domain("target-6", "permutation", [list(range(target_size))],
        {"identity": list(range(target_size))}, size=target_size)
    _tick(agent, 8)
    lifted = [schema for schema in agent.schemas("target-6")
              if agent.attrs(schema).get("provenance") == "lifted_from_witness"]
    assert len(lifted) == 1
    initial = list(range(target_size))
    goal = _apply_native(agent, agent.attrs(lifted[0])["params"], initial)
    task = agent.add_solve_task("target-6", initial, goal)
    _tick(agent)
    assert agent.attrs(task)["strategy_started"] == 1
    assert agent.attrs(task)["strategy_size_lifted"] == 1
    assert agent.attrs(task)["status"] == "solved"
    used = agent.native.neighbours(task, "uses_lifted_strategy_instance")
    assert used == lifted
    assert len(agent.attrs(used[0])["params"]) == target_size


def test_failed_subgoal_order_guides_open_search():
    p = [1, 0, 2, 3]
    q = [0, 1, 3, 2]
    agent = Agent(track_i=True,
        extra_seeds=("strategy_discovery", "open_process_search"),
        policy_overrides={
            "ProcessSchemaPolicy": {"enabled": 1.0},
            "InventionPolicy": {"enabled": 0.0},
            "InvariantMinerPolicy": {"enabled": 0.0},
            "StrategyDiscoveryPolicy": {"enabled": 1.0, "allow_lift": 1.0},
            "OpenProcessSearchPolicy": {"enabled": 1.0, "max_attempts": 16.0},
            "SolverPolicy": {"enabled": 1.0},
        }, budget={"enabled": 1.0, "remaining": 100.0, "capacity": 100.0,
                   "last_refill_epoch": 0.0, "refill_per_epoch": 0.0})
    agent.add_domain("search", "permutation", [[0, 1, 2, 3]], {"p": p, "q": q})
    schemas = {agent.attrs(node)["name"]: node for node in agent.schemas("search")}
    agent.s.set_attr(schemas["q"], "cost", 2.0)
    training_initial = [1, 0, 2, 3]
    training_goal = _apply_native(agent, p, training_initial)
    training = agent.add_solve_task("search", training_initial, training_goal)
    _tick(agent)
    assert agent.attrs(training)["status"] == "solved"
    strategy = agent.nodes("DiscoveredStrategy")[0]
    learned_process = agent.attrs(strategy)["trace"][0]
    assert agent.attrs(learned_process)["params"] == p
    for policy in agent.nodes("SolverPolicy"):
        agent.s.set_attr(policy, "enabled", 0.0)

    initial = [0, 1, 2, 3]
    failed_subgoal = _apply_native(agent, p, initial)
    goal = _apply_native(agent, q, failed_subgoal)
    failed_replay = agent.add_solve_task("search", initial, goal)
    _tick(agent)
    assert agent.attrs(failed_replay)["status"] == "strategy_failed"
    constraint = agent.native.neighbours(strategy, "has_strategy_failure_constraint")[0]
    assert agent.attrs(constraint)["failed_state"] == failed_subgoal

    task = agent.add_solve_task("search", initial, goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    attempts = [agent.attrs(node) for node in agent.nodes("OpenProcessSearchAttempt")
                if agent.native.neighbours(node, "about_task") == [task]]
    failed_order = _compose(agent, p, q)
    assert any(attrs["params"] == failed_order
               and attrs["subgoal_state"] == failed_subgoal
               and attrs["status"] == "constraint_failed" for attrs in attempts)
    expected = _compose(agent, q, p)
    assert any(attrs["params"] == expected and attrs["status"] == "verified"
               for attrs in attempts)
    candidates = [agent.attrs(node) for node in agent.nodes("OpenProcessCandidate")]
    assert any(attrs["params"] == expected for attrs in candidates)
    assert all(attrs.get("subgoal_state") != failed_subgoal
               for attrs in candidates if attrs["params"] == failed_order)


def test_temporary_regression_allowed():
    agent, _ = _open_agent(held={"p": [3, 2, 0, 1], "q": [0, 3, 1, 2]})
    initial = [2, 0, 3, 1]
    intermediate = _apply_native(agent, [3, 2, 0, 1], initial)
    goal = _apply_native(agent, [0, 3, 1, 2], intermediate)
    distance = lambda left, right: sum(a != b for a, b in zip(left, right))
    assert distance(intermediate, goal) > distance(initial, goal)

    task = agent.add_solve_task("search", initial, goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    candidates = [candidate for candidate in agent.nodes("OpenProcessCandidate")
                  if agent.attrs(candidate)["expression_tree"][2][2][0] == "compose"]
    assert len(candidates) == 1
    attrs = agent.attrs(candidates[0])
    assert attrs["status"] == "unapproved_candidate"
    assert attrs["subgoal_state"] == intermediate
    assert attrs["params"] == _compose(agent, [3, 2, 0, 1], [0, 3, 1, 2])
    assert _apply_native(agent, attrs["params"], initial) == goal
