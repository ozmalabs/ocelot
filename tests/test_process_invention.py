"""P9.02 native algebra and budgeted invention acceptance tests."""
from evaluation.process_mastery.harness import Agent


def _term(agent, term, **env):
    return agent.native.evaluate(term, env)


def _compose(a, b):
    return {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
            "b": {"type": "Var", "name": "b"}}, {"a": a, "b": b}


def test_compose_order():
    agent = Agent(track_i=False)
    a, b = [1, 2, 0], [0, 2, 1]
    term, env = _compose(a, b)
    composed = _term(agent, term, **env)
    assert composed == [2, 1, 0]
    applied = agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": composed, "state": [0, 1, 2]})
    assert applied == [2, 1, 0]


def test_noninvertible_no_inverse():
    agent = Agent(track_i=False)
    inverse = {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}}
    assert _term(agent, inverse, p=[0, 0]) is None
    assert _term(agent, inverse, p=[[1, 2], [2, 4]]) is None


def test_repair_not_exact_inverse():
    # The current algebra has no RepairInverse term. A goal-equivalent repair
    # stays a separate record and cannot be routed through ProcessInverse.
    agent = Agent(track_i=False)
    repair = agent.s.add_node("ProcessRepairCandidate", {
        "status": "verified", "goal_predicate": "same-visible-goal",
        "exact_inverse": 0.0, "source_epoch": 1})
    inverse = {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}}
    assert _term(agent, inverse, p=repair) is None
    assert agent.attrs(repair)["exact_inverse"] == 0.0


def test_finite_probe_collision_not_law():
    # An incomplete probe set is not a complete effect certificate. The
    # graph retains both source schemas and labels their equivalence unknown.
    agent = Agent(track_i=False)
    d = agent.add_domain("partial", "permutation", [[0, 1, 2]], {
        "left": [1, 0, 2], "right": [0, 2, 1]})
    schemas = agent.schemas("partial")
    assert len(schemas) == 2
    for node in schemas:
        agent.s.set_attr(node, "effect_evaluation", "probe_relative")
    assert len(agent.schemas("partial")) == 2
    assert not agent.nodes("ProcessLaw")


def test_all_six_operators_execute():
    agent = Agent(track_i=False)
    a, b = [1, 2, 0], [0, 2, 1]
    inv = {"type": "ProcessInverse", "a": {"type": "Var", "name": "a"}}
    compose = lambda x, y: {"type": "ProcessCompose", "a": x, "b": y}
    va, vb = {"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}
    operators = {
        "inverse": inv,
        "compose": compose(va, vb),
        "conjugate": compose(compose(vb, va), {"type": "ProcessInverse", "a": vb}),
        "commutator": compose(compose(compose(va, vb), inv),
                               {"type": "ProcessInverse", "a": vb}),
        "power2": compose(va, va),
        "power3": compose(compose(va, va), va),
    }
    results = {name: _term(agent, term, a=a, b=b) for name, term in operators.items()}
    assert all(value is not None for value in results.values())
    assert results["inverse"] == [2, 0, 1]
    assert results["power3"] == [0, 1, 2]


def test_dihedral_closure():
    agent = Agent(track_i=False)
    generators = [[1, 2, 0], [0, 2, 1]]
    identity = [0, 1, 2]
    seen = {tuple(identity)}
    frontier = [identity]
    while frontier:
        state = frontier.pop()
        for generator in generators:
            term, env = _compose(state, generator)
            nxt = _term(agent, term, **env)
            if tuple(nxt) not in seen:
                seen.add(tuple(nxt)); frontier.append(nxt)
    assert len(seen) == 6
    assert all(sorted(p) == [0, 1, 2] for p in seen)


def test_precise_conjugation_coverage():
    agent = Agent(track_i=False)
    r, s = [1, 2, 0], [0, 2, 1]
    conjugate = {"type": "ProcessCompose",
        "a": {"type": "ProcessCompose", "a": {"type": "Var", "name": "b"},
              "b": {"type": "Var", "name": "a"}},
        "b": {"type": "ProcessInverse", "a": {"type": "Var", "name": "b"}}}
    r_conj = _term(agent, conjugate, a=r, b=s)
    assert r_conj == [2, 0, 1]
    assert sorted(r_conj) == sorted(r)


def _funded_inverse_round():
    agent = Agent(track_i=True,
        policy_overrides={"InventionPolicy": {"enabled": 1.0, "max_invented": 10.0,
                                                 "closure_enabled": 0.0}},
        budget={"enabled": 1.0, "remaining": 10.0, "last_refill_epoch": 0.0})
    for op in agent.nodes("InventionOperator"):
        agent.s.set_attr(op, "enabled", 1.0 if agent.attrs(op)["name"] == "inverse" else 0.0)
    agent.add_domain("cycle", "permutation", [[0, 1, 2]], {"r": [1, 2, 0]})
    task = agent.add_solve_task("cycle", [0, 1, 2], [0, 1, 2])
    agent.s.set_attr(task, "status", "stuck")
    return agent


def test_round_budget_once():
    agent = _funded_inverse_round()
    for _ in range(5):
        agent.s.tick(1000)
    requests = agent.nodes("ThinkingBudgetRequest")
    budget = next(n for n in agent.nodes("ThinkingBudget")
                  if agent.attrs(n).get("enabled") == 1.0)
    assert len(requests) == 1
    assert agent.attrs(requests[0])["status"] == "approved"
    assert agent.attrs(budget)["remaining"] == 6.0
    assert len(agent.invented("cycle")) == 1


def test_restart_bound():
    agent = _funded_inverse_round()
    for _ in range(5):
        agent.s.tick(1000)
    before = agent.attrs(next(n for n in agent.nodes("ThinkingBudget")
                              if agent.attrs(n).get("enabled") == 1.0))["remaining"]
    for _ in range(5):
        agent.s.tick(1000)
    after = agent.attrs(next(n for n in agent.nodes("ThinkingBudget")
                             if agent.attrs(n).get("enabled") == 1.0))["remaining"]
    assert before == after == 6.0
    assert len(agent.nodes("ThinkingBudgetRequest")) == 1
    assert len(agent.invented("cycle")) == 1


def test_round_requires_budget_node():
    agent = _funded_inverse_round()
    for node in agent.nodes("ThinkingBudget"):
        agent.s.remove_node(node)
    for _ in range(5):
        agent.s.tick(1000)
    assert not agent.nodes("InventionRound")
    assert not agent.invented("cycle")
