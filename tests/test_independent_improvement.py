"""P22 generic proposal, split, and candidate-scoped approval checks."""
import json
from pathlib import Path

from evaluation.process_mastery.native_process_execution import attest_open_process_candidate
from substrate.seed_loader import manifest_for
from tests.test_open_process_search import _agent as _p19_agent, _apply, _compose
from tests.test_open_process_adoption import (
    _agent as _adoption_agent, _approve, _candidate as _adoption_candidate, _tick,
)

ROOT = Path(__file__).resolve().parents[1]


def _agent():
    agent, _domain = _p19_agent(attempts=1000)
    return agent


def _install(agent):
    manifest = json.loads((ROOT / "seeds/independent_improvement.json").read_text())
    agent.native.load_seed_manifest(manifest, agent.ag)


def _candidate(agent):
    goal = _apply(agent, _compose(agent, [1, 0, 2, 3], [0, 2, 1, 3]), [0, 1, 2, 3])
    task = agent.add_solve_task("search", [0, 1, 2, 3], goal)
    agent.s.set_attr(task, "status", "stuck")
    for _ in range(12):
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
    source_task = agent.native.neighbours(attempt, "about_task")[0]
    agent.s.set_attr(source_task, "split", "training")
    agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
    attest_open_process_candidate(agent, candidate)
    _install(agent)
    agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
    for _ in range(8):
        agent.s.tick(4000)
    proposals = agent.nodes("IndependentImprovementProposal")
    assert len(proposals) == 1
    assert agent.attrs(proposals[0])["source_split"] == "training"
    assert agent.native.neighbours(proposals[0], "derived_from_trial") == [attempt]
    agent.s.set_attr(agent.nodes("OpenProcessSearchPolicy")[0], "max_attempts", 5000.0)
    second_task = agent.add_solve_task("search", [0, 1, 2, 3],
                                       agent.attrs(source_task)["goal"],
                                       training_trial_key="independent-trial-2")
    agent.s.set_attr(second_task, "split", "training")
    agent.s.set_attr(second_task, "status", "stuck")
    for _ in range(20):
        agent.s.tick(4000)
    proposal = proposals[0]
    qualification = agent.native.neighbours(proposal, "has_native_qualification")
    assert len(qualification) == 1
    assert agent.attrs(qualification[0])["trial_count"] == 2.0
    assert agent.attrs(proposal)["status"] == "qualified_for_candidate_specific_approval"
    supporting_attempts = agent.native.neighbours(qualification[0], "counts_native_trial")
    assert len(supporting_attempts) == 2
    supporting_requests = [request for request in agent.nodes("OpenProcessSearchRequest")
        if any(attempt in agent.native.neighbours(request, "has_search_attempt")
               for attempt in supporting_attempts)]
    assert len(supporting_requests) == 2
    assert all(agent.attrs(request)["status"] == "qualified_terminal"
               for request in supporting_requests)
    attempt_count = len(agent.nodes("OpenProcessSearchAttempt"))
    for _ in range(4):
        agent.s.tick(4000)
    assert len(agent.nodes("OpenProcessSearchAttempt")) == attempt_count


def test_no_holdout_in_proposal():
    agent = _agent()
    candidate = _candidate(agent)
    attempt = agent.native.neighbours(candidate, "derived_from_attempt")[0]
    task = agent.native.neighbours(attempt, "about_task")[0]
    agent.s.set_attr(task, "split", "heldout")
    agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
    attest_open_process_candidate(agent, candidate)
    _install(agent)
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
