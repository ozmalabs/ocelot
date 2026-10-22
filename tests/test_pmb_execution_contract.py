from evaluation.process_mastery.harness import Agent, TRACK_I_SEEDS


def test_baseline_has_no_track_i():
    agent = Agent(track_i=False)
    installed = {agent.attrs(n).get("id") for n in agent.s.nodes("Seed")}
    assert installed.isdisjoint(TRACK_I_SEEDS)
    assert not agent.s.nodes("SolverPolicy")


def test_arms_share_world_and_budget():
    budget = {"max_invention_rounds": 2.0}
    arms = [Agent(track_i=enabled, budget=budget) for enabled in (False, True)]
    domains = [a.add_loopover_domain(2) for a in arms]
    for a, d in zip(arms, domains):
        domain = a.attrs(d)
        assert domain["name"] == "loopover_2"
        assert domain["kind"] == "permutation"
        assert len(a.schemas("loopover_2", name="R0")) == 1
        assert a.resource_budget == budget


def test_actions_are_graph_selected():
    agent = Agent(track_i=True)
    domain = agent.add_loopover_domain(2)
    task = agent.add_solve_task("loopover_2", [1, 2, 3, 0], [0, 1, 2, 3])
    assert agent.s.has_edge(agent.ag, "has_solve_task", task)
    assert agent.s.has_edge(task, "about_domain", domain)
    assert "action" not in agent.attrs(task)
    before = list(agent.attrs(task)["state"])
    run = agent.run(max_ticks=100, max_steps=100_000)
    after = agent.attrs(task)
    assert run["ticks"] > 0
    assert after["status"] == "solved"
    assert after["state"] == after["goal"]
    assert after["state"] != before
    assert after["steps"] == len(after["trace"]) > 0
    assert all(agent.s.node(schema)["type"] == "ProcessSchema"
               for schema in after["trace"])


def test_missing_adapter_not_zero_score():
    agent = Agent(track_i=False)
    try:
        agent.request_action(1, "step")
    except RuntimeError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("missing adapters must fail fast")
    assert Agent.trial_record("UNSUPPORTED")["status"] == "UNSUPPORTED"
    assert Agent.trial_record("NOT_RUN")["status"] == "NOT_RUN"
