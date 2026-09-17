"""Canonical, fail-closed P2-B1 protocol validation.

The worker receives a signed public observation envelope and may return one
bounded native plan proposal.  This module intentionally has no action grant,
callback, world-state, or simulator interface.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from evaluation.p0a.canonical import ProtocolError, canonical_bytes, object_hash, sha256, verify_signature

SCHEMA_ENVELOPE = "P2ObservationEnvelopeV1"
SCHEMA_PROPOSAL = "P2NativePlanProposalV1"
MAX_ACTIONS, MAX_NODES, MAX_FRAME_BYTES = 4, 8, 64 * 1024
BASIS_POINTS = 10_000
VALID_CLASSIFICATIONS = frozenset({"unestablished", "infeasible", "budget_exhausted", "protocol_error"})
FORBIDDEN_AUTHORITY_FIELDS = frozenset({
    "authoritative_world_state", "hidden_state", "hidden_parameters", "fixture_path",
    "fixture_paths", "callback", "callbacks", "simulator", "simulator_interface",
    "action_grant", "grant", "capability", "host_handle", "socket", "mount_path",
    "transition_table", "secret_seed", "enactment_rank",
})

class P2ProtocolError(ProtocolError):
    """The P2 worker message is untrusted, malformed, or authority-bearing."""

def _exact(value: Mapping[str, Any], fields: set[str], label: str) -> None:
    if set(value) != fields:
        raise P2ProtocolError(f"{label} fields")

def _text(value: Any, label: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > max_len or "\x00" in value:
        raise P2ProtocolError(f"{label} invalid")
    return value

def _digest(value: Any, label: str) -> str:
    value = _text(value, label, max_len=71)
    if len(value) != 71 or not value.startswith("sha256:") or any(c not in "0123456789abcdef" for c in value[7:]):
        raise P2ProtocolError(f"{label} invalid")
    return value

def _integer(value: Any, label: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise P2ProtocolError(f"{label} invalid")
    return value

def _no_authority(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise P2ProtocolError("non-string key")
            if key in FORBIDDEN_AUTHORITY_FIELDS:
                raise P2ProtocolError("forbidden authority field")
            _no_authority(child)
    elif isinstance(value, list):
        for child in value: _no_authority(child)
    elif value is not None and not isinstance(value, (str, bool, int)):
        raise P2ProtocolError("non-canonical protocol value")

def _identifier_list(value: Any, label: str, maximum: int) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise P2ProtocolError(f"{label} invalid")
    result = [_text(item, label) for item in value]
    if len(set(result)) != len(result): raise P2ProtocolError(f"{label} duplicate")
    return result

def validate_envelope(value: Mapping[str, Any], *, signing_key=None) -> dict[str, Any]:
    """Validate the sealed input before a native worker is launched.

    Signing is optional only for structural fixture tests; production callers
    supply the evaluator public key.  The result is a canonical detached copy.
    """
    if not isinstance(value, Mapping): raise P2ProtocolError("envelope object")
    _exact(value, {"schema", "run_id", "episode_id", "step", "observation_atoms", "legal_action_ids",
                   "goal_atoms", "cost_bounds", "budget", "training_bundle", "signature"}, "envelope")
    if value["schema"] != SCHEMA_ENVELOPE: raise P2ProtocolError("envelope schema")
    _text(value["run_id"], "run id"); _text(value["episode_id"], "episode id")
    _integer(value["step"], "step", 0, 1)
    _identifier_list(value["observation_atoms"], "observation atoms", MAX_NODES)
    _identifier_list(value["legal_action_ids"], "legal actions", MAX_ACTIONS)
    _identifier_list(value["goal_atoms"], "goal atoms", MAX_NODES)
    if not isinstance(value["cost_bounds"], Mapping) or set(value["cost_bounds"]) != {"maximum_intervention"}:
        raise P2ProtocolError("cost bounds")
    _integer(value["cost_bounds"]["maximum_intervention"], "maximum intervention", 0, 1_000_000)
    if not isinstance(value["budget"], Mapping): raise P2ProtocolError("budget")
    _exact(value["budget"], {"cpu_ms", "wall_ms", "memory_bytes", "pids", "stdout_bytes", "network_bytes", "horizon", "branching", "nodes_per_action"}, "budget")
    expected = {"cpu_ms": 2000, "wall_ms": 3000, "memory_bytes": 512 * 1024 * 1024, "pids": 32,
                "stdout_bytes": MAX_FRAME_BYTES, "network_bytes": 0, "horizon": 1, "branching": 1,
                "nodes_per_action": MAX_NODES}
    if value["budget"] != expected: raise P2ProtocolError("unlocked budget")
    if not isinstance(value["training_bundle"], Mapping): raise P2ProtocolError("training bundle")
    _no_authority(value["training_bundle"])
    _text(value["signature"], "signature", max_len=128)
    canonical_bytes(dict(value))
    if signing_key is not None: verify_signature(dict(value), signing_key)
    return dict(value)

def _distribution(value: Any, atoms: set[str]) -> dict[str, int]:
    if not isinstance(value, Mapping) or set(value) != atoms: raise P2ProtocolError("outcome distribution domain")
    result = {str(atom): _integer(bp, "outcome basis points", 0, BASIS_POINTS) for atom, bp in value.items()}
    if sum(result.values()) != BASIS_POINTS: raise P2ProtocolError("outcome distribution total")
    return result

def _manifold(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping): raise P2ProtocolError("manifold")
    _exact(value, {"support", "resolved", "loss", "information_loss", "earliest_decisive_tick"}, "manifold")
    for key in ("support", "resolved"):
        if type(value[key]) is not bool: raise P2ProtocolError("manifold boolean")
    for key in ("loss", "information_loss", "earliest_decisive_tick"):
        _integer(value[key], key, 0, MAX_NODES)
    if value["resolved"] and not value["support"]: raise P2ProtocolError("resolved without support")
    return dict(value)

def _prediction(value: Any, legal: set[str], outcomes: set[str], goals: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping): raise P2ProtocolError("prediction object")
    _exact(value, {"action_id", "source_belief_digest", "transition_witness_digests", "trajectory_export",
                   "outcome_basis_points", "predicted_goal_atoms", "intervention_cost", "manifold",
                   "goal_probability_bp", "confidence_bp", "uncertainty_bp", "terminal_status"}, "prediction")
    action_id = _text(value["action_id"], "prediction action")
    if action_id not in legal: raise P2ProtocolError("nonlegal prediction")
    _digest(value["source_belief_digest"], "source belief digest")
    witnesses = value["transition_witness_digests"]
    if not isinstance(witnesses, list) or not witnesses or len(witnesses) > MAX_NODES: raise P2ProtocolError("transition witnesses")
    for witness in witnesses: _digest(witness, "transition witness digest")
    if len(set(witnesses)) != len(witnesses): raise P2ProtocolError("duplicate transition witness")
    if not isinstance(value["trajectory_export"], Mapping): raise P2ProtocolError("trajectory export")
    _no_authority(value["trajectory_export"])
    nodes = value["trajectory_export"].get("nodes")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES: raise P2ProtocolError("trajectory node bound")
    _distribution(value["outcome_basis_points"], outcomes)
    raw_goals = value["predicted_goal_atoms"]
    if not isinstance(raw_goals, list) or len(raw_goals) > MAX_NODES:
        raise P2ProtocolError("predicted goals invalid")
    predicted_goals = [_text(item, "predicted goals") for item in raw_goals]
    if len(set(predicted_goals)) != len(predicted_goals): raise P2ProtocolError("predicted goals duplicate")
    if not set(predicted_goals).issubset(goals): raise P2ProtocolError("unknown predicted goal")
    _integer(value["intervention_cost"], "intervention cost", 0, 1_000_000)
    _manifold(value["manifold"])
    _integer(value["goal_probability_bp"], "goal probability", 0, BASIS_POINTS)
    _integer(value["confidence_bp"], "confidence", 0, BASIS_POINTS)
    _integer(value["uncertainty_bp"], "uncertainty", 0, BASIS_POINTS)
    if value["confidence_bp"] + value["uncertainty_bp"] != BASIS_POINTS: raise P2ProtocolError("confidence uncertainty")
    if value["terminal_status"] not in {"predicted", *VALID_CLASSIFICATIONS}: raise P2ProtocolError("terminal status")
    return dict(value)

def validate_proposal(value: Mapping[str, Any], envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a pre-action all-legal-actions native proposal exactly once."""
    envelope = validate_envelope(envelope)
    if not isinstance(value, Mapping): raise P2ProtocolError("proposal object")
    _exact(value, {"schema", "run_id", "episode_id", "envelope_digest", "verified_input_digest", "predictions", "selection", "proposal_digest"}, "proposal")
    if value["schema"] != SCHEMA_PROPOSAL: raise P2ProtocolError("proposal schema")
    if value["run_id"] != envelope["run_id"] or value["episode_id"] != envelope["episode_id"]: raise P2ProtocolError("proposal binding")
    _digest(value["envelope_digest"], "proposal envelope digest")
    _digest(value["verified_input_digest"], "proposal sealed digest")
    if value["envelope_digest"] != sha256(canonical_bytes(dict(envelope))): raise P2ProtocolError("proposal envelope digest")
    if value["verified_input_digest"] != value["envelope_digest"]: raise P2ProtocolError("proposal sealed digest")
    legal, outcomes, goals = set(envelope["legal_action_ids"]), set(envelope["observation_atoms"]), set(envelope["goal_atoms"])
    predictions = value["predictions"]
    if not isinstance(predictions, list) or len(predictions) != len(legal): raise P2ProtocolError("prediction completeness")
    parsed = [_prediction(prediction, legal, outcomes, goals) for prediction in predictions]
    if {prediction["action_id"] for prediction in parsed} != legal: raise P2ProtocolError("prediction action set")
    maximum_intervention = envelope["cost_bounds"]["maximum_intervention"]
    for prediction in parsed:
        if prediction["intervention_cost"] > maximum_intervention and prediction["terminal_status"] != "infeasible":
            raise P2ProtocolError("over-budget prediction must be infeasible")
    selection = value["selection"]
    if not isinstance(selection, Mapping): raise P2ProtocolError("selection")
    _exact(selection, {"selected_action_id", "classification", "selection_path", "feasible_action_ids", "minimal_action_ids", "native_tie_set"}, "selection")
    if selection["selection_path"] != "P2BoundedFutureManifoldV1":
        raise P2ProtocolError("selection path")
    classification = selection["classification"]
    if classification not in {"selected", "sealed_enactment_rank_required", *VALID_CLASSIFICATIONS, "no_goal_satisfying_candidate"}: raise P2ProtocolError("selection classification")
    for field in ("feasible_action_ids", "minimal_action_ids"):
        items = selection[field]
        if not isinstance(items, list) or len(items) > MAX_ACTIONS:
            raise P2ProtocolError("selection derivation")
        parsed_items = [_text(item, "selection derivation") for item in items]
        if parsed_items != sorted(parsed_items) or len(set(parsed_items)) != len(parsed_items) or not set(parsed_items).issubset(legal):
            raise P2ProtocolError("selection derivation")
    selected = selection["selected_action_id"]
    raw_tie_set = selection["native_tie_set"]
    if not isinstance(raw_tie_set, list) or len(raw_tie_set) > MAX_ACTIONS:
        raise P2ProtocolError("native tie set")
    tie_set = [_text(item, "native tie set") for item in raw_tie_set]
    if len(set(tie_set)) != len(tie_set): raise P2ProtocolError("duplicate native tie")
    if not set(tie_set).issubset(legal): raise P2ProtocolError("nonlegal tie")
    if classification == "selected":
        if selected not in legal or selected not in tie_set: raise P2ProtocolError("selection reference")
        if any(prediction["action_id"] == selected and prediction["intervention_cost"] > maximum_intervention for prediction in parsed):
            raise P2ProtocolError("over-budget selection")
        if any(prediction["action_id"] in tie_set and prediction["intervention_cost"] > maximum_intervention for prediction in parsed):
            raise P2ProtocolError("over-budget tie")
    elif classification == "sealed_enactment_rank_required":
        if selected is not None or len(tie_set) < 2:
            raise P2ProtocolError("sealed enactment selection")
    elif selected is not None or tie_set: raise P2ProtocolError("abstention selection")
    proposal_without_digest = {key: value[key] for key in value if key != "proposal_digest"}
    if value["proposal_digest"] != object_hash(proposal_without_digest): raise P2ProtocolError("proposal digest")
    canonical = canonical_bytes(dict(value))
    if len(canonical) > MAX_FRAME_BYTES: raise P2ProtocolError("proposal frame bound")
    _no_authority(value)
    return dict(value)
