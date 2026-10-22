"""P13.04 observed-yield, structure-conditioned strategy recall tests."""
from evaluation.process_mastery.harness import Agent


def _agent(*, solve=True):
    agent = Agent(
        track_i=True, extra_seeds=("strategy_library",),
        policy_overrides={"StrategyLibraryPolicy": {"enabled": 1.0},
                          "InventionPolicy": {"enabled": 0.0}},
        budget={"enabled": 1.0, "remaining": 100.0,
                "last_refill_epoch": 0.0, "refill_per_epoch": 0.0},
    )
    if not solve:
        agent.s.set_attr(agent.nodes("SolverPolicy")[0], "enabled", 0.0)
    return agent


def _tick(agent, n=12):
    for _ in range(n):
        agent.s.tick(4000)


def _cycle_and_distractor(agent, name="domain"):
    cycle = [1, 2, 0]
    swap = [1, 0, 2]
    domain = agent.add_domain(name, "permutation", [[0, 1, 2]], {
        "cycle": cycle, "swap": swap,
    })
    return domain


def _apply(agent, process, state):
    return agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": agent.attrs(process)["params"], "state": state},
    )


def _learn_cycle(agent, name="domain"):
    domain = _cycle_and_distractor(agent, name)
    task = agent.add_solve_task(name, [0, 1, 2], [2, 0, 1])
    _tick(agent)
    assert agent.attrs(task)["status"] == "solved"
    agent.s.set_attr(agent.nodes("SolverPolicy")[0], "enabled", 0.0)
    entry = next(e for e in agent.nodes("StrategyLibraryEntry")
                 if agent.attrs(e).get("source_task") == task)
    return domain, task, entry


def test_recall_reduces_candidate_work():
    agent = _agent()
    domain, source, entry = _learn_cycle(agent)
    budget = next(n for n in agent.nodes("ThinkingBudget")
                  if agent.attrs(n).get("enabled") == 1.0)
    remaining_before = agent.attrs(budget)["remaining"]
    cycle = next(p for p in agent.schemas("domain") if agent.attrs(p)["name"] == "cycle")
    initial = [2, 1, 0]
    goal = _apply(agent, cycle, initial)
    unseen = agent.add_solve_task("domain", initial, goal)
    _tick(agent)
    assert agent.attrs(unseen)["status"] == "solved"
    attempts = agent.s.neighbours(unseen, "has_strategy_recall_attempt")
    assert len(attempts) == 1
    attrs = agent.attrs(attempts[0])
    assert attrs["candidate_count"] == 1
    assert attrs["cold_start_process_count"] == 2
    assert attrs["candidate_count"] < attrs["cold_start_process_count"]
    assert agent.attrs(unseen)["steps"] == 1
    assert agent.s.neighbours(unseen, "recalls_strategy_entry") == [entry]
    requests = agent.s.neighbours(unseen, "has_strategy_recall_request")
    assert len(requests) == 1
    assert agent.attrs(requests[0])["status"] == "approved"
    assert agent.attrs(requests[0])["debited_epoch"] == agent.attrs(requests[0])["requested_epoch"]
    assert agent.attrs(budget)["remaining"] == remaining_before - 1
    assert agent.attrs(domain)["kind"] == agent.attrs(entry)["kind"]
    assert agent.attrs(source)["status"] == "solved"


def test_bad_recall_falls_back_to_bounded_solver():
    agent = _agent()
    _domain, _source, entry = _learn_cycle(agent)
    task = agent.add_solve_task("domain", [1, 0, 2], [1, 2, 0])
    _tick(agent)
    assert agent.attrs(task)["status"] == "solved"
    assert agent.attrs(task)["strategy_fallback_started"] == 1
    assert agent.s.neighbours(task, "rejected_strategy_recall") == [entry]
    assert agent.attrs(task)["steps"] == 2  # one rejected recall step plus one cold-start solver step
    assert agent.attrs(entry)["observed_attempts"] == 2
    assert agent.attrs(entry)["observed_successes"] == 1
    assert agent.attrs(entry)["observed_yield"] == 0.5
    observations = agent.s.neighbours(entry, "has_yield_observation")
    assert len(observations) == 1
    assert agent.attrs(observations[0])["result"] == "observed_failure"


def test_yield_requires_observed_result():
    agent = _agent(solve=False)
    agent.s.set_attr(agent.nodes("StrategyLibraryPolicy")[0], "enabled", 0.0)
    _cycle_and_distractor(agent)
    active = agent.add_solve_task("domain", [0, 1, 2], [2, 0, 1])
    _tick(agent)
    assert not agent.nodes("StrategyLibraryEntry")
    assert not agent.nodes("StrategyYieldObservation")
    assert agent.attrs(active)["status"] == "active"
    agent.s.set_attr(agent.nodes("StrategyLibraryPolicy")[0], "enabled", 1.0)
    agent.s.set_attr(agent.nodes("SolverPolicy")[0], "enabled", 1.0)
    _tick(agent)
    assert agent.attrs(active)["status"] == "solved"
    entry = agent.nodes("StrategyLibraryEntry")[0]
    assert agent.attrs(entry)["yield_source"] == "observed_solved_task"
    assert agent.attrs(entry)["observed_yield"] == 1.0


def test_distribution_change_invalidates():
    agent = _agent()
    domain, _source, entry = _learn_cycle(agent)
    agent.s.set_attr(domain, "model_epoch", 1.0)
    _tick(agent)
    assert agent.attrs(entry)["status"] == "stale"
    task = agent.add_solve_task("domain", [2, 1, 0], [1, 0, 2])
    _tick(agent)
    assert not agent.s.neighbours(task, "has_strategy_recall_attempt")
    assert len(agent.s.neighbours(task, "has_strategy_recall_fallback")) == 1


def test_denied_recall_funding_falls_back_without_retry():
    agent = _agent()
    _domain, _source, _entry = _learn_cycle(agent)
    budget = next(n for n in agent.nodes("ThinkingBudget")
                  if agent.attrs(n).get("enabled") == 1.0)
    agent.s.set_attr(budget, "remaining", 0.0)
    cycle = next(p for p in agent.schemas("domain") if agent.attrs(p)["name"] == "cycle")
    initial = [2, 1, 0]
    task = agent.add_solve_task("domain", initial, _apply(agent, cycle, initial))
    _tick(agent)
    request = agent.s.neighbours(task, "has_strategy_recall_request")[0]
    assert agent.attrs(request)["status"] == "denied"
    assert agent.attrs(task)["strategy_funding_fallback"] == 1
    assert not agent.s.neighbours(task, "has_strategy_recall_attempt")
    assert agent.attrs(task)["status"] == "solved"


def test_disabled_duplicate_budget_does_not_override_approved_recall():
    agent = _agent()
    _domain, _source, _entry = _learn_cycle(agent)
    disabled = agent.s.add_node("ThinkingBudget", {
        "enabled": 0.0, "remaining": 0.0, "capacity": 0.0,
        "last_refill_epoch": 0.0, "refill_per_epoch": 0.0,
    })
    agent.s.add_edge(agent.ag, "has_thinking_budget", disabled, {})
    cycle = next(p for p in agent.schemas("domain") if agent.attrs(p)["name"] == "cycle")
    initial = [2, 1, 0]
    task = agent.add_solve_task("domain", initial, _apply(agent, cycle, initial))
    _tick(agent)
    request = agent.s.neighbours(task, "has_strategy_recall_request")[0]
    assert agent.attrs(request)["status"] == "approved"
    assert len(agent.s.neighbours(task, "has_strategy_recall_attempt")) == 1
    assert not agent.s.neighbours(task, "has_strategy_recall_fallback")
    assert agent.attrs(task)["status"] == "solved"
