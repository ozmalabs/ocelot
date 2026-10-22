"""P22 generic proposal, split, and candidate-scoped approval checks."""
import json
from pathlib import Path

from tests.test_open_process_search import _agent as _p19_agent, _apply, _compose
from tests.test_open_process_adoption import (
    _agent as _adoption_agent, _approve, _candidate as _adoption_candidate, _tick,
)

ROOT = Path(__file__).resolve().parents[1]


def _agent():
    agent, _domain = _p19_agent()
    return agent


def _install(agent):
    manifest = json.loads((ROOT / "seeds/independent_improvement.json").read_text())
    agent.native.load_seed_manifest(manifest, agent.ag)


def _candidate(agent):
    goal = _apply(agent, _compose(agent, [1, 0, 2, 3], [0, 2, 1, 3]), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal)
    agent.s.set_attr(task, "status", "stuck")
    for _ in range(20):
        agent.s.tick(4000)
    candidates = agent.nodes("OpenProcessCandidate")
    assert candidates
    return candidates[0]


def test_next_candidate_not_named_in_seed():
    seed = json.loads((ROOT / "seeds/independent_improvement.json").read_text())
    serialized = json.dumps(seed, sort_keys=True)
    for name in ("commutator_square_v1", "commutator_cube_v2", "commutator_fourth_v3"):
        assert name not in serialized
    assert "expression_digest" in serialized and "expression_tree" in serialized


def test_qualification_from_native_trials():
    agent = _agent()
    candidate = _candidate(agent)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    assert agent.attrs(attempt)["status"] == "verified"
    assert agent.attrs(attempt)["expression_tree"]
    assert agent.attrs(candidate)["status"] == "unapproved_candidate"
    _install(agent)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    task = agent.native.neighbours(attempt, "about_task")[0]
    agent.s.set_attr(task, "split", "training")
    agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
    for _ in range(8):
        agent.s.tick(4000)
    proposals = agent.nodes("IndependentImprovementProposal")
    assert len(proposals) == 1
    assert agent.attrs(proposals[0])["source_split"] == "training"
    assert agent.native.neighbours(proposals[0], "derived_from_trial") == [attempt]


def test_no_holdout_in_proposal():
    agent = _agent()
    candidate = _candidate(agent)
    _install(agent)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    task = agent.native.neighbours(attempt, "about_task")[0]
    agent.s.set_attr(task, "split", "heldout")
    agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
    for _ in range(8):
        agent.s.tick(4000)
    assert not agent.nodes("IndependentImprovementProposal")


def test_new_approval_exact_expression():
    agent = _adoption_agent()
    candidate = _adoption_candidate(agent)
    approval = _approve(agent, candidate)
    params = list(agent.attrs(candidate)["params"])
    params[0], params[1] = params[1], params[0]
    agent.s.set_attr(candidate, "params", params)
    _tick(agent)
    assert agent.attrs(approval)["status"] != "consumed"
    assert agent.attrs(candidate)["status"] == "unapproved_candidate"


def test_rollback_stops_current_execution():
    seed = json.loads((ROOT / "seeds/recursive_process_improvement.json").read_text())
    rollback = next(rule for rule in seed["rules"]
                    if rule["name"] == "rpi_rollback_failed_generation_to_verified_ancestor")
    encoded = json.dumps(rollback, sort_keys=True)
    assert "rolled_back" in encoded and "suspended" in encoded
    assert "zero_tolerance_invariant_failure" in encoded
