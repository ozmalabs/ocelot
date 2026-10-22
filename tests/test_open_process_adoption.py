"""P19 candidate-specific approval, adoption and revocation gates."""
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate, execute_open_process_candidate,
)
from tests.test_open_process_search import _apply, _compose


def _agent():
    return Agent(track_i=False,
        extra_seeds=("open_process_search", "open_process_adoption"),
        policy_overrides={
            "OpenProcessSearchPolicy": {"enabled": 1.0, "max_attempts": 64.0},
            "OpenProcessAdoptionPolicy": {"enabled": 1.0},
            "ProcessSchemaPolicy": {"enabled": 1.0},
        },
        budget={"enabled": 1.0, "remaining": 100.0, "capacity": 100.0,
                "last_refill_epoch": 0.0, "refill_per_epoch": 0.0})


def _tick(agent, count=16):
    for _ in range(count):
        agent.s.tick(4000)


def _candidate(agent):
    for policy in agent.nodes("ProcessSchemaPolicy"):
        agent.s.set_attr(policy, "enabled", 1.0)
    held = {"p": [1, 0, 2, 3], "q": [0, 2, 1, 3]}
    agent.add_domain("search", "permutation", [[0, 1, 2, 3]], held)
    goal = _apply(agent, _compose(agent, *held.values()), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal)
    agent.s.set_attr(task, "status", "stuck")
    _tick(agent)
    candidates = agent.nodes("OpenProcessCandidate")
    assert candidates
    return candidates[0]


def _approve(agent, candidate, **changes):
    if agent.attrs(candidate).get("expression_digest_status") != "verified":
        attest_open_process_candidate(agent, candidate)
    attrs = agent.attrs(candidate)
    values = {
        "status": "approved", "approval_kind": "human",
        "expression_digest": attrs["expression_digest"],
        "expression_key": attrs["expression_key"],
        "expression_tree": attrs["expression_tree"],
        "effect_digest": attrs["effect_digest"], "params": attrs["params"],
        "guard_state": attrs["guard_state"], "domain": attrs["domain"],
        "source_epoch": attrs["source_epoch"], "model_epoch": attrs["model_epoch"],
        "frame_epoch": attrs["frame_epoch"], **changes,
    }
    approval = agent.s.add_node("OpenProcessAdoptionApproval", values)
    agent.s.add_edge(agent.ag, "has_open_process_adoption_approval", approval, {})
    agent.s.add_edge(approval, "approves_open_process_candidate", candidate, {})
    return approval


def test_expression_digest_not_candidate_name():
    agent = _agent()
    candidate = _candidate(agent)
    original_digest = attest_open_process_candidate(agent, candidate)
    agent.s.set_attr(candidate, "name", "arbitrary-display-label")
    approval = _approve(agent, candidate, expression_digest=original_digest)
    _tick(agent)
    assert agent.attrs(approval)["status"] == "consumed"
    assert agent.attrs(candidate)["status"] == "adopted_candidate"
    assert agent.attrs(candidate)["adopted_expression_digest"] == original_digest


def test_new_candidate_not_preapproved():
    agent = _agent()
    candidate = _candidate(agent)
    assert agent.attrs(candidate)["status"] == "unapproved_candidate"
    assert not agent.nodes("OpenProcessAdoptionApproval")
    assert agent.attrs(candidate).get("adoption_status") is None


def test_effect_proof_binds_new_expression():
    agent = _agent()
    candidate = _candidate(agent)
    _approve(agent, candidate)
    # A human approval of one native finite effect cannot be transferred to a
    # changed expression, even if the candidate's display name is untouched.
    params = list(agent.attrs(candidate)["params"])
    params[0], params[1] = params[1], params[0]
    agent.s.set_attr(candidate, "params", params)
    _tick(agent)
    assert agent.attrs(candidate)["status"] == "unapproved_candidate"
    assert agent.attrs(candidate).get("adoption_status") is None


def test_invalidated_process_stops_next_action():
    agent = _agent()
    candidate = _candidate(agent)
    _approve(agent, candidate)
    task = agent.add_solve_task("search", [0, 1, 2, 3], [3, 2, 1, 0])
    agent.s.set_attr(task, "status", "executing")
    agent.s.add_edge(candidate, "has_dependent_task", task, {})
    _tick(agent)
    assert agent.attrs(candidate)["status"] == "adopted_candidate"

    agent.s.set_attr(candidate, "params", [3, 2, 1, 0])
    calls = []
    blocked = execute_open_process_candidate(agent, candidate,
        state=agent.attrs(candidate)["guard_state"], authorize=lambda proposal: True,
        world_transition=lambda action: calls.append(action) or {"observed_state": action})
    assert blocked["status"] == "ABSTAIN"
    assert calls == []
    _tick(agent)
    assert agent.attrs(candidate)["status"] == "invalidated"
    assert agent.attrs(task)["status"] == "aborted"
    assert agent.attrs(task)["abort_reason"] == "adopted_process_invalidated"


def test_unapproved_candidate_cannot_reach_world_and_receipt_binds_strategy():
    agent = _agent()
    candidate = _candidate(agent)
    calls = []
    rejected = execute_open_process_candidate(agent, candidate,
        state=[0, 1, 2, 3], authorize=lambda proposal: True,
        world_transition=lambda action: calls.append(action) or {"observed_state": action})
    assert rejected["status"] == "ABSTAIN"
    assert calls == []

    _approve(agent, candidate)
    _tick(agent)
    initial = agent.attrs(candidate)["guard_state"]
    def simulate_world(action):
        observed = [None] * len(initial)
        for source, destination in enumerate(action):
            observed[destination] = initial[source]
        return {"observed_state": observed}
    result = execute_open_process_candidate(agent, candidate, state=initial,
        authorize=lambda proposal: proposal["expression_digest"] ==
            agent.attrs(candidate)["expression_digest"],
                world_transition=lambda action: calls.append(action) or simulate_world(action))
    assert result["status"] == "COMPLETED"
    assert result["receipt"]["observed_state"] == result["proposal"]["predicted_state"]
    receipt_nodes = agent.native.neighbours(candidate, "has_world_execution_receipt")
    assert len(receipt_nodes) == 1
    assert agent.attrs(receipt_nodes[0])["status"] == "verified"
    assert agent.attrs(receipt_nodes[0])["expression_digest"] == result["proposal"]["expression_digest"]
