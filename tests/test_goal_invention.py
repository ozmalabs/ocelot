"""P10.01 and P10.03 goal regression/invention acceptance tests."""

from evaluation.process_mastery.harness import Agent


WILD = "·?·"


def test_lift_preserves_bindings():
    agent = Agent(track_i=False)
    witness = agent.native.evaluate(
        {"type": "AntiUnifyWitness", "values": {"type": "Var", "name": "values"},
         "wild": WILD},
        {"values": [
            {"op": "swap", "i": 0, "size": 3},
            {"op": "swap", "i": 2, "size": 5},
        ]})
    template, substitutions = witness
    substitute = {"type": "Substitute", "template": {"type": "Var", "name": "template"},
                  "sigma": {"type": "Var", "name": "sigma"}, "wild": WILD}
    rebuilt = [agent.native.evaluate(substitute, {
        "template": template, "sigma": sigma}) for sigma in substitutions]
    assert rebuilt == [
        {"op": "swap", "i": 0, "size": 3},
        {"op": "swap", "i": 2, "size": 5},
    ]


def test_unseen_size_preconditions():
    agent = Agent(track_i=False)
    constraint = {"type": "Lt", "a": {"type": "Var", "name": "index"},
                  "b": {"type": "Var", "name": "size"}}
    assert agent.native.evaluate(constraint, {"index": 4, "size": 5}) is True
    assert agent.native.evaluate(constraint, {"index": 5, "size": 5}) is False
    assert agent.native.evaluate(constraint, {"index": 5, "size": 6}) is True


def test_goal_gap_mints_interface():
    agent = _agent()
    task = _stuck_task(agent, kind="opaque", held={"mystery": [1, 2]})
    _tick(agent)
    gap = agent.nodes("ProcessGap")[0]
    assert agent.attrs(gap)["required_effect_kind"] == "state_transition"
    requests = agent.nodes("SynthesisInterfaceRequest")
    assert len(requests) == 1
    assert agent.attrs(requests[0])["status"] == "needs_tool"
    assert agent.attrs(task)["status"] == "stuck"


def _agent(*, targeted=True, remaining=8.0):
    return Agent(track_i=True, extra_seeds=("goal_invention",),
                 policy_overrides={
                     "GoalInventionPolicy": {"enabled": 1.0,
                                             "targeted_enabled": 1.0 if targeted else 0.0},
                     "InventionPolicy": {"enabled": 0.0},
                 }, budget={"enabled": 1.0, "remaining": remaining,
                            "last_refill_epoch": 0.0, "refill_per_epoch": 0.0})


def _stuck_task(agent, *, kind="permutation", held=None):
    domain = agent.add_domain("goal", kind, [[0, 1, 2]], held or {"r": [1, 2, 0]})
    task = agent.add_solve_task("goal", [0, 1, 2], [1, 2, 0])
    return task


def _tick(agent, count=8):
    for _ in range(count):
        agent.s.tick(2000)


def test_missing_effect_drives_invention():
    agent = _agent()
    task = _stuck_task(agent)
    _tick(agent)
    episodes = agent.nodes("GoalInventionEpisode")
    assert len(episodes) == 1
    assert agent.attrs(episodes[0])["status"] == "found"
    assert agent.nodes("ProcessGap")
    assert agent.attrs(task)["status"] == "solved"
    assert agent.attrs(agent.nodes("InventionPolicy")[0])["enabled"] == 0.0


def test_goal_plan_uses_new_process():
    agent = _agent()
    _stuck_task(agent)
    _tick(agent)
    invented = [n for n in agent.nodes("ProcessSchema")
                if agent.attrs(n).get("provenance") == "goal_targeted_inverse"]
    assert len(invented) == 1
    attrs = agent.attrs(invented[0])
    assert attrs["verification_receipt"] == "native_apply_reduces_current_goal_distance"
    assert attrs["fingerprint_checked"] == attrs["dedup_checked"] == 1


def test_targeted_rung_funded():
    agent = _agent()
    _stuck_task(agent)
    _tick(agent)
    requests = [n for n in agent.nodes("ThinkingBudgetRequest")
                if agent.attrs(n).get("requester_kind") == "goal_invention"]
    assert len(requests) == 1
    assert agent.attrs(requests[0])["status"] == "approved"
    budget = next(n for n in agent.nodes("ThinkingBudget")
                  if agent.attrs(n).get("enabled") == 1.0)
    assert agent.attrs(budget)["remaining"] == 6.0


def test_denied_rung_restores():
    agent = _agent(remaining=0.0)
    _stuck_task(agent)
    _tick(agent)
    episode = agent.nodes("GoalInventionEpisode")[0]
    assert agent.attrs(episode)["status"] == "denied"
    assert agent.attrs(agent.nodes("InventionPolicy")[0])["enabled"] == 0.0
    assert not [n for n in agent.nodes("ProcessSchema")
                if agent.attrs(n).get("provenance") == "goal_targeted_inverse"]


def test_new_program_never_skips_verifier():
    agent = _agent()
    _stuck_task(agent, kind="opaque", held={"mystery": [1, 2]})
    _tick(agent)
    assert agent.nodes("SynthesisInterfaceRequest")
    assert not agent.nodes("Program")
    assert not agent.nodes("ProgramCandidate")


def test_no_handwritten_strategy_input():
    agent = Agent(track_i=False)
    agent.add_domain("plain", "permutation", [[0, 1, 2]], {"held": [1, 2, 0]})
    task = agent.add_solve_task("plain", [0, 1, 2], [1, 2, 0])
    attrs = agent.attrs(task)
    assert "strategy" not in attrs and "solution_trace" not in attrs
    assert not agent.nodes("StrategyRecord")
    assert not agent.nodes("ImaginedPlanCandidate")
