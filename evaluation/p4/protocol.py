"""Closed P4-R0 transport schemas; no callable, simulator, or host-control fields."""
from __future__ import annotations
from typing import Any, Mapping
from evaluation.p0a.canonical import object_hash

MAX_FRAME_BYTES = 64 * 1024
ARMS = ("graph_planner", "reactive_no_plan", "no_causal_model", "reset_memory", "search_budget_matched")
SUPPORTED_ACTION_KINDS = frozenset({"inspect", "reverse", "advance"})
ARM_CATALOG_SCHEMA = "P4R0ArmCatalogV1"
ARM_SCHEMA = "P4R0MechanicsArmV1"
SELECTION_SCHEMA = "P4R0RuntimeSelectionV1"


def arm_digest(arm: Mapping[str, Any]) -> str:
    """Hash the locked mechanics and trace contract, never the mutable label."""
    return object_hash(dict(arm), "arm_digest")


def validate_arm(arm: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(arm)
    if (set(value) != {"arm_id", "mechanics", "trace_contract", "arm_digest"}
            or value.get("arm_id") not in ARMS
            or not isinstance(value.get("mechanics"), dict)
            or not isinstance(value.get("trace_contract"), dict)
            or not is_digest(value.get("arm_digest"))
            or value["arm_digest"] != arm_digest(value)):
        raise P4ProtocolError("mechanics arm")
    mechanics = value["mechanics"]
    if (set(mechanics) != {"causal_model", "memory_epoch", "planner", "replan_policy", "search_budget"}
            or mechanics["causal_model"] not in {"persistent", "absent"}
            or mechanics["memory_epoch"] not in {"persistent", "reset_after_intervention"}
            or mechanics["planner"] not in {"graph", "absent"}
            or mechanics["replan_policy"] not in {"required", "forbidden"}
            or type(mechanics["search_budget"]) is not int or mechanics["search_budget"] < 0):
        raise P4ProtocolError("mechanics arm")
    contract = value["trace_contract"]
    if (set(contract) != {"expected_replan_count", "required_edges", "terminal_status"}
            or type(contract["expected_replan_count"]) is not int or contract["expected_replan_count"] < 0
            or not isinstance(contract["required_edges"], list)
            or any(not isinstance(edge, str) or ">" not in edge for edge in contract["required_edges"])
            or contract["terminal_status"] not in {"complete", "impasse"}):
        raise P4ProtocolError("trace contract")
    return value

class P4ProtocolError(ValueError):
    pass

def is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 71 and value.startswith("sha256:") and all(c in "0123456789abcdef" for c in value[7:])

def require_closed(value: Mapping[str, Any], fields: set[str], schema: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields or value.get("schema") != schema:
        raise P4ProtocolError("closed schema")
    return dict(value)

def validate_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    fields = {"schema", "run_id", "sequence", "fixture_id", "logical_time", "observation", "parent_receipt", "envelope_digest"}
    v = require_closed(value, fields, "P4R0TaskEnvelopeV1")
    if (not all(isinstance(v[x], str) and v[x] for x in ("run_id", "fixture_id"))
            or type(v["sequence"]) is not int or v["sequence"] < 0
            or type(v["logical_time"]) is not int or v["logical_time"] < 0
            or type(v["observation"]) is not dict
            or (v["parent_receipt"] is not None and not is_digest(v["parent_receipt"]))
            or v["envelope_digest"] != object_hash(v, "envelope_digest")):
        raise P4ProtocolError("envelope")
    if any(any(word in k.lower() for word in ("world", "domain", "fixture", "hidden", "mechanism", "evaluator")) for k in v["observation"]):
        raise P4ProtocolError("label leak")
    return v

def validate_proposal(value: Mapping[str, Any]) -> dict[str, Any]:
    base_fields = {"schema", "proposal_id", "run_id", "sequence", "kind", "causal_parent_receipt_hash", "reservation", "graph_digest", "proposal_digest"}
    bound_fields = base_fields | {"selection_digest", "arm_digest"}
    if not isinstance(value, Mapping) or set(value) not in (base_fields, bound_fields) or value.get("schema") != "GraphActionProposalV1":
        raise P4ProtocolError("closed schema")
    v = dict(value)
    if (not all(isinstance(v[x], str) and v[x] for x in ("proposal_id", "run_id", "kind"))
            or type(v["sequence"]) is not int or v["sequence"] < 0
            or not is_digest(v["graph_digest"])
            or (set(v) == bound_fields and (not is_digest(v["selection_digest"]) or not is_digest(v["arm_digest"])))
            or not isinstance(v["reservation"], dict) or set(v["reservation"]) != {"actions", "risk", "transactions"}
            or any(type(n) is not int or n < 0 for n in v["reservation"].values())
            or (v["causal_parent_receipt_hash"] is not None and not is_digest(v["causal_parent_receipt_hash"]))
            or v["proposal_digest"] != object_hash(v, "proposal_digest")):
        raise P4ProtocolError("proposal")
    return v

def reservation_digest(*, run_id: str, proposal_digest: str, proposal_sequence: int,
                       snapshot_digest: str, reservation: Mapping[str, Any]) -> str:
    """Commit a reservation to its exact action context using canonical JSON."""
    commitment = {
        "schema": "P4R0ActionReservationV1",
        "run_id": run_id,
        "proposal_digest": proposal_digest,
        "proposal_sequence": proposal_sequence,
        "snapshot_digest": snapshot_digest,
        "reservation": dict(reservation),
    }
    return object_hash(commitment)


def validate_sealed_action_outcome(value: Mapping[str, Any]) -> dict[str, Any]:
    fields = {"schema", "run_id", "fixture_id", "fixture_selection_id", "fixture_digest", "fixture_record_digest", "arm_id", "arm_digest", "selection_digest", "proposal_digest", "proposal_receipt_digest", "grant_receipt_digest", "broker_receipt_digest", "replan_receipt_digest", "sequence", "snapshot_digest", "reservation", "reservation_digest", "success", "trace_digest", "outcome_digest", "receipt"}
    v = require_closed(value, fields, "P4R0SealedActionOutcomeV1")
    if (not isinstance(v["run_id"], str) or not v["run_id"]
            or not isinstance(v["fixture_id"], str) or not isinstance(v["fixture_selection_id"], str)
            or not isinstance(v["arm_id"], str) or not is_digest(v["arm_digest"]) or not is_digest(v["selection_digest"]) or not is_digest(v["trace_digest"])
            or not all(is_digest(v[x]) for x in ("fixture_digest", "fixture_record_digest", "proposal_digest", "proposal_receipt_digest", "grant_receipt_digest", "broker_receipt_digest", "replan_receipt_digest", "snapshot_digest", "reservation_digest"))
            or type(v["sequence"]) is not int or v["sequence"] < 1
            or not isinstance(v["reservation"], dict) or set(v["reservation"]) != {"actions", "risk", "transactions"}
            or any(type(n) is not int or n <= 0 for n in v["reservation"].values())
            or v["reservation_digest"] != reservation_digest(run_id=v["run_id"], proposal_digest=v["proposal_digest"], proposal_sequence=v["sequence"] - 1, snapshot_digest=v["snapshot_digest"], reservation=v["reservation"])
            or type(v["success"]) is not bool
            or not isinstance(v["receipt"], dict)
            or v["outcome_digest"] != object_hash(v, "outcome_digest", "receipt")):
        raise P4ProtocolError("sealed action outcome")
    return v
