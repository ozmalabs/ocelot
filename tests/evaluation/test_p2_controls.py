from __future__ import annotations

import pytest

from evaluation.p0a.canonical import canonical_bytes, object_hash, sha256
from evaluation.p2.protocol import P2ProtocolError, validate_proposal
from test_p2_protocol import envelope, proposal


def rehash(value):
    value["proposal_digest"] = object_hash({key: item for key, item in value.items() if key != "proposal_digest"})
    return value


def selected(action_id: str):
    return {"selected_action_id": action_id, "classification": "selected",
            "selection_path": "P2BoundedFutureManifoldV1", "feasible_action_ids": [action_id],
            "minimal_action_ids": [action_id], "native_tie_set": [action_id]}


def abstention():
    return {"selected_action_id": None, "classification": "no_goal_satisfying_candidate",
            "selection_path": "P2BoundedFutureManifoldV1", "feasible_action_ids": [],
            "minimal_action_ids": [], "native_tie_set": []}


def test_unavailable_action_cannot_be_predicted_or_selected():
    env = envelope()
    env["legal_action_ids"] = ["a"]
    candidate = proposal(env)
    candidate["predictions"] = [candidate["predictions"][0]]
    candidate["selection"] = selected("a")
    rehash(candidate)

    validated = validate_proposal(candidate, env)
    assert [record["action_id"] for record in validated["predictions"]] == ["a"]
    assert validated["selection"]["selected_action_id"] == "a"


def test_transition_mismatch_and_false_causal_witness_fail_closed():
    env = envelope()
    candidate = proposal(env)
    candidate["predictions"][0]["transition_witness_digests"] = []
    rehash(candidate)

    with pytest.raises(P2ProtocolError, match="transition witnesses"):
        validate_proposal(candidate, env)


def test_over_budget_predictions_must_be_infeasible_and_never_selected():
    env = envelope()
    env["cost_bounds"] = {"maximum_intervention": 0}
    candidate = proposal(env)
    rehash(candidate)
    with pytest.raises(P2ProtocolError, match="over-budget prediction"):
        validate_proposal(candidate, env)

    for item in candidate["predictions"]:
        item["terminal_status"] = "infeasible"
        item["manifold"] = {"support": False, "resolved": False, "loss": 1,
                            "information_loss": 1, "earliest_decisive_tick": 1}
        item["confidence_bp"] = 0
        item["uncertainty_bp"] = 10_000
        item["predicted_goal_atoms"] = []
    candidate["selection"] = abstention()
    rehash(candidate)

    assert validate_proposal(candidate, env)["selection"]["selected_action_id"] is None


def test_scrambled_labels_are_structurally_invariant():
    env = envelope()
    env["legal_action_ids"] = ["z", "q"]
    candidate = proposal(env)
    labels = {"a": "z", "b": "q"}
    for record in candidate["predictions"]:
        record["action_id"] = labels[record["action_id"]]
    selection = candidate["selection"]
    for field in ("feasible_action_ids", "minimal_action_ids", "native_tie_set"):
        selection[field] = [labels[item] for item in selection[field]]
    selection["feasible_action_ids"].sort()
    selection["minimal_action_ids"].sort()
    selection["selected_action_id"] = labels[selection["selected_action_id"]]
    candidate["envelope_digest"] = sha256(canonical_bytes(env))
    candidate["verified_input_digest"] = candidate["envelope_digest"]
    rehash(candidate)

    validated = validate_proposal(candidate, env)
    assert validated["selection"]["selected_action_id"] == "z"
    assert validated["selection"]["feasible_action_ids"] == ["q", "z"]
    assert set(validated["selection"]["native_tie_set"]) == {"q", "z"}
