"""P26.02 tests for bounded native search repair and visible failures."""
from test_open_process_search import _agent, _apply, _compose, _tick


def test_known_feasible_expression_reachable_by_native_search():
    agent, _ = _agent(attempts=64)
    left, right = [1, 0, 2, 3], [0, 2, 1, 3]
    goal = _apply(agent, _compose(agent, left, right), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal,
                                training_trial_key="p26-known-feasible")
    agent.s.set_attr(task, "split", "training")
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    assert any(agent.attrs(candidate)["params"] == _compose(agent, left, right)
               for candidate in agent.nodes("OpenProcessCandidate"))


def test_exhausted_set_stops_with_reason():
    agent, _ = _agent(attempts=1)
    task = agent.add_solve_task("search", [0, 1, 2, 3], [3, 2, 1, 0],
                                training_trial_key="p26-exhausted")
    agent.s.set_attr(task, "split", "training")
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    request, = agent.nodes("OpenProcessSearchRequest")
    assert agent.attrs(request)["status"] == "global_attempt_ceiling"
    assert len(agent.native.neighbours(request, "has_search_attempt")) == 1


def test_oracle_witness_not_input():
    agent, _ = _agent()
    task = agent.add_solve_task("search", [0, 1, 2, 3], [2, 0, 1, 3],
                                training_trial_key="p26-no-oracle")
    agent.s.set_attr(task, "split", "training")
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    attrs = agent.attrs(task)
    assert attrs["split"] == "training"
    assert not ({"expression_tree", "candidate_expression", "heldout_label",
                 "expected_operator"} & set(attrs))
    assert all(agent.native.neighbours(candidate, "derived_from_attempt")
               for candidate in agent.nodes("OpenProcessCandidate"))
