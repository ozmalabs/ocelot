"""P19 bounded generic expression search over graph-held process evidence."""
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.native_process_execution import open_process_candidate_digest


def _agent(*, attempts=64, held=None):
    agent = Agent(track_i=False, extra_seeds=("open_process_search",),
        policy_overrides={"OpenProcessSearchPolicy": {
            "enabled": 1.0, "max_attempts": float(attempts), "max_candidates": 16.0},
            "ProcessSchemaPolicy": {"enabled": 1.0}},
        budget={"enabled": 1.0, "remaining": 100.0, "capacity": 100.0,
                "last_refill_epoch": 0.0, "refill_per_epoch": 0.0})
    for policy in agent.nodes("ProcessSchemaPolicy"):
        agent.s.set_attr(policy, "enabled", 1.0)
    held = held or {"source-a": [1, 0, 2, 3], "source-b": [0, 2, 1, 3]}
    domain = agent.add_domain("search", "permutation", [[0, 1, 2, 3]], held)
    return agent, domain


def _apply(agent, process, state):
    return agent.native.evaluate({"type": "ProcessApply",
        "p": {"type": "Var", "name": "p"},
        "state": {"type": "Var", "name": "state"}},
        {"p": process, "state": state})


def _compose(agent, a, b):
    return agent.native.evaluate({"type": "ProcessCompose",
        "a": {"type": "Var", "name": "a"},
        "b": {"type": "Var", "name": "b"}}, {"a": a, "b": b})


def _tick(agent):
    for _ in range(12):
        agent.s.tick(4000)


def _verify_new_effect_drives_search():
    agent, _ = _agent()
    left, right = [1, 0, 2, 3], [0, 2, 1, 3]
    goal = _apply(agent, _compose(agent, left, right), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    candidates = agent.nodes("OpenProcessCandidate")
    assert candidates
    candidate = agent.attrs(candidates[0])
    assert candidate["status"] == "unapproved_candidate"
    assert candidate["approval_required"] == 1.0
    assert candidate["expression_tree"][0] == "guard"
    assert candidate["expression_tree"][2][0] == "subgoal"
    assert candidate["expression_tree"][2][2][0] == "compose"
    assert candidate["guard_state"] == [0, 1, 2, 3]
    assert candidate["subgoal_state"] == _apply(agent, left, [0, 1, 2, 3])
    assert candidate["params"] == _compose(agent, left, right)
    assert _apply(agent, candidate["params"], [0, 1, 2, 3]) == goal
    # The full expression is retained on the graph candidate; the host only
    # reads and verifies the graph-authored term, never rebuilds it by name.
    attempt = agent.native.neighbours(candidates[0], "derived_from_attempt")[0]
    assert agent.attrs(attempt)["predicted_state"] == goal
    assert agent.attrs(attempt)["status"] == "verified"
    assert agent.attrs(attempt)["rank_score"] == agent.attrs(attempt)["work_cost"]


def test_new_candidate_executed_not_host_rebuilt():
    _verify_new_effect_drives_search()


def test_new_effect_drives_search():
    _verify_new_effect_drives_search()


def test_renaming_parents_does_not_change_expression_choice():
    results = []
    for held in ({"source-a": [1, 0, 2, 3], "source-b": [0, 2, 1, 3]},
                 {"renamed-x": [1, 0, 2, 3], "renamed-y": [0, 2, 1, 3]}):
        agent, _ = _agent(held=held)
        goal = _apply(agent, _compose(agent, *held.values()), [0, 1, 2, 3])
        task = agent.add_solve_task("search", [0, 1, 2, 3], goal)
        agent.s.set_attr(task, "status", "stuck")
        _tick(agent)
        results.append([agent.attrs(n)["params"] for n in agent.nodes("OpenProcessCandidate")])
    assert results[0] == results[1]


def test_candidate_name_does_not_choose_recipe():
    agent, _ = _agent()
    left, right = [1, 0, 2, 3], [0, 2, 1, 3]
    goal = _apply(agent, _compose(agent, left, right), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal,
                                candidate_name="power3_candidate")
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    candidates = agent.nodes("OpenProcessCandidate")
    assert any(agent.attrs(candidate)["expression_tree"][2][2][0] == "compose"
               and agent.attrs(candidate)["params"] == _compose(agent, left, right)
               for candidate in candidates)


def test_unseen_operator_expression_generated():
    agent, _ = _agent(held={"turn": [1, 2, 3, 0]})
    initial = [0, 1, 2, 3]
    inverse = agent.native.evaluate(
        {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}},
        {"p": [1, 2, 3, 0]})
    goal = _apply(agent, inverse, initial)
    task = agent.add_solve_task("search", initial, goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    candidates = [agent.attrs(node) for node in agent.nodes("OpenProcessCandidate")]
    assert any(attrs["expression_tree"][2][0] == "inverse"
               and attrs["params"] == inverse for attrs in candidates)


def test_both_subgoal_orders_are_evaluated_within_budget():
    held = {"p": [1, 0, 2, 3], "q": [0, 2, 1, 3]}
    agent, _ = _agent(held=held)
    initial = [0, 1, 2, 3]
    reverse = _compose(agent, held["q"], held["p"])
    goal = _apply(agent, reverse, initial)
    task = agent.add_solve_task("search", initial, goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    attempts = [agent.attrs(n) for n in agent.nodes("OpenProcessSearchAttempt")]
    assert any(attempt["expression_key"] == "compose:q:p"
               and attempt["status"] == "verified" for attempt in attempts)
    candidates = [agent.attrs(n) for n in agent.nodes("OpenProcessCandidate")]
    assert any(candidate["params"] == reverse for candidate in candidates)


def test_residual_expression_expands_recursively_with_depth_bound():
    held = {"p": [1, 0, 2, 3], "q": [0, 2, 1, 3], "r": [0, 1, 3, 2]}
    agent, _ = _agent(held=held)
    initial = [0, 1, 2, 3]
    expected = _compose(agent, _compose(agent, held["p"], held["q"]), held["r"])
    goal = _apply(agent, expected, initial)
    task = agent.add_solve_task("search", initial, goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    attempts = [agent.attrs(node) for node in agent.nodes("OpenProcessSearchAttempt")]
    expanded = [attrs for attrs in attempts if attrs.get("depth", 0) == 2]
    assert expanded
    assert any(attrs["status"] == "verified" and attrs["params"] == expected
               for attrs in expanded)
    assert all(attrs["depth"] <= 4 for attrs in attempts)
    assert any(agent.native.neighbours(node, "extends_search_attempt")
               for node in agent.nodes("OpenProcessSearchAttempt"))
    candidates = [node for node in agent.nodes("OpenProcessCandidate")
                  if agent.attrs(node)["params"] == expected]
    assert candidates
    candidate = candidates[0]
    before = open_process_candidate_digest(agent, candidate)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    ancestors = agent.native.neighbours(attempt, "extends_search_attempt")
    assert ancestors
    ancestor_parent = agent.native.neighbours(ancestors[0], "uses_parent_process")[0]
    agent.s.set_attr(ancestor_parent, "source_digest", "mutated-parent-source")
    assert open_process_candidate_digest(agent, candidate) != before


def test_changed_goal_changes_proposal():
    agent, _ = _agent()
    task = agent.add_solve_task("search", [0, 1, 2, 3], [3, 2, 1, 0])
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    candidates = agent.nodes("OpenProcessCandidate")
    assert not any(agent.attrs(n)["params"] == [3, 2, 1, 0] for n in candidates)
    attempts = agent.nodes("OpenProcessSearchAttempt")
    assert attempts
    assert all(agent.attrs(n)["goal_state"] == [3, 2, 1, 0] for n in attempts)


def test_invalid_composition_unknown():
    agent, _ = _agent(held={"short": [1, 0, 2], "long": [1, 0, 2, 3]})
    task = agent.add_solve_task("search", [0, 1, 2, 3], [3, 2, 1, 0])
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    attempts = agent.nodes("OpenProcessSearchAttempt")
    assert attempts
    assert any(agent.attrs(n)["status"] == "unknown" for n in attempts)
    assert all(agent.attrs(n)["rank_score"] >= 2_000_000 for n in attempts
               if agent.attrs(n)["status"] == "unknown")
    assert not [n for n in agent.nodes("OpenProcessCandidate")
                if agent.attrs(n)["status"] == "promoted"]


def test_proposal_budget_includes_failures():
    agent, _ = _agent(attempts=1)
    task = agent.add_solve_task("search", [0, 1, 2, 3], [3, 2, 1, 0])
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    requests = agent.nodes("OpenProcessSearchRequest")
    assert len(requests) == 1
    assert len(agent.native.neighbours(requests[0], "has_search_attempt")) == 1
    budget_requests = [n for n in agent.nodes("ThinkingBudgetRequest")
        if agent.attrs(n).get("requester_kind") == "open_process_search"]
    assert len(budget_requests) == 1
    assert agent.attrs(budget_requests[0])["status"] == "approved"
