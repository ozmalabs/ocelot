"""P9.03 conformance for witnessed walls and verified breakers."""
from evaluation.process_mastery.harness import Agent


def _wall_case(*, breaker=True, partial=False):
    agent = Agent(track_i=True,
                  policy_overrides={
                      "InvariantMinerPolicy": {"enabled": 1.0},
                      "InventionPolicy": {"enabled": 0.0},
                      "SolverPolicy": {"enabled": 0.0},
                  })
    for node in agent.nodes("ThinkingBudget"):
        agent.s.set_attr(node, "enabled", 0.0)
    probes = [[0, 1, 2]] if not partial else [[0, 1, 2]]
    agent.add_domain("wall", "permutation", probes, {
        "even_cycle": [1, 2, 0],
        **({"odd_breaker": [1, 0, 2]} if breaker else {}),
    })
    invented = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": "wall", "domain_kind": "permutation",
        "name": "invented_even", "params": [1, 2, 0], "cost": 1.0,
        "provenance": "invented_by:compose", "status": "active", "invented": 1,
    })
    agent.s.add_edge(agent.ag, "has_process_schema", invented, {})
    agent.s.add_edge(agent.domains["wall"], "has_invented_process", invented, {})
    task = agent.add_solve_task("wall", [0, 1, 2], [1, 0, 2])
    agent.s.set_attr(task, "status", "stuck")
    return agent, task


def test_even_tools_cannot_reach_odd_target():
    agent, task = _wall_case()
    for _ in range(5):
        agent.s.tick(1000)
    walls = agent.nodes("WallExplanation")
    assert len(walls) == 1
    wall = agent.attrs(walls[0])
    assert wall["invariant"] == "perm_parity"
    assert wall["state_parity"] != wall["goal_parity"]
    assert agent.attrs(task)["status"] == "active"
    assert agent.attrs(walls[0])["status"] == "broken"
    assert agent.attrs(walls[0])["breaking_process"] == "odd_breaker"


def test_breaker_changes_required_invariant():
    agent, _ = _wall_case()
    for _ in range(5):
        agent.s.tick(1000)
    assert agent.attrs(agent.nodes("WallExplanation")[0])["breaking_process"] == "odd_breaker"


def test_partial_probe_not_proof():
    agent, _ = _wall_case(partial=True)
    # A finite probe fingerprint is not an invariant proof or a ProcessLaw.
    for _ in range(5):
        agent.s.tick(1000)
    assert not [n for n in agent.nodes("ProcessLaw")
                if agent.attrs(n).get("proof_kind") != "structural_induction"]


def test_no_breaker_honest_impasse():
    agent, _ = _wall_case(breaker=False)
    for _ in range(5):
        agent.s.tick(1000)
    walls = agent.nodes("WallExplanation")
    assert len(walls) == 1
    assert agent.attrs(walls[0])["status"] == "unbreakable"
