"""Evaluator-owned P4-R0 grants and sealed action outcomes."""
from __future__ import annotations
import secrets
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from evaluation.p0a.canonical import b64encode, canonical_bytes, object_hash, parse_canonical, sign
from .protocol import P4ProtocolError, reservation_digest as canonical_reservation_digest, validate_proposal, validate_sealed_action_outcome
from .receipts import P4ReceiptLog, payload


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


@dataclass
class P4R0Evaluator:
    seed: bytes
    graph: dict[str, Any]
    lock: Mapping[str, Any] | None = None
    receipts: P4ReceiptLog | None = None
    grants: dict[str, dict[str, Any]] = field(default_factory=dict)
    reserved: dict[str, int] = field(default_factory=lambda: {"actions": 0, "risk": 0, "transactions": 0})
    simulator_calls: int = 0
    active_fixture: dict[str, Any] | None = None
    active_selection: dict[str, Any] | None = None

    def bind_selection(self, selection: Mapping[str, Any]) -> None:
        if self.lock is None or self.receipts is None or not isinstance(selection, Mapping):
            raise P4ProtocolError("runtime selection authority required")
        records = self.lock.get("fixture_catalog", [])
        arms = self.lock.get("arm_catalog", [])
        record = next((row for row in records if row["fixture_key"] == selection.get("fixture_key")), None)
        arm = next((row for row in arms if row["arm_id"] == selection.get("arm_id")), None)
        if record is None or arm is None:
            raise P4ProtocolError("unavailable runtime selection")
        required = {"schema", "run_id", "fixture_key", "selection_id", "fixture_id", "bundle_digest", "fixture_record_digest", "arm_id", "arm_digest", "selection_digest", "signature"}
        if set(selection) != required or selection["schema"] != "P4R0RuntimeSelectionV1":
            raise P4ProtocolError("runtime selection envelope")
        if (selection["selection_id"] != record["selection_id"] or selection["bundle_digest"] != record["bundle_digest"]
                or selection["fixture_record_digest"] != record["record_digest"] or selection["arm_digest"] != arm["arm_digest"]
                or selection["selection_digest"] != object_hash({key: selection[key] for key in required if key not in {"signature", "selection_digest"}})):
            raise P4ProtocolError("runtime selection digest")
        from evaluation.p0a.canonical import verify_signature
        try:
            verify_signature(dict(selection), self.receipts.public_key)
        except Exception as exc:
            raise P4ProtocolError("runtime selection signature") from exc
        self.active_selection = dict(selection)
        self.bind_fixture({**record, "fixture_id": selection["fixture_id"], "fixture_digest": record["bundle_digest"], "arm": arm, **selection})

    def bind_fixture(self, fixture: Mapping[str, Any]) -> None:
        if self.lock is None or not isinstance(fixture, Mapping):
            raise P4ProtocolError("fixture authority required")
        records = self.lock.get("fixture_catalog", [])
        record = next((row for row in records if row.get("selection_id") == fixture.get("selection_id")), None)
        arm = next((row for row in self.lock.get("arm_catalog", []) if row.get("arm_id") == fixture.get("arm_id")), None)
        if (record is None or arm is None
                or fixture.get("fixture_key") != record["fixture_key"]
                or fixture.get("bundle_digest") != record["bundle_digest"]
                or fixture.get("record_digest") not in {record["record_digest"], fixture.get("fixture_record_digest")}
                or fixture.get("arm_digest") != arm["arm_digest"]):
            raise P4ProtocolError("locked fixture selection")
        self.active_fixture = dict(fixture)

    def _fixture_for(self, run_id: str) -> dict[str, Any]:
        if self.active_fixture is not None:
            return dict(self.active_fixture)
        if self.lock is None:
            return {"fixture_id": "opaque-fixture", "selection_id": "opaque-selection", "record_digest": "sha256:" + "0" * 64}
        record = self.lock["fixture_catalog"][0]
        arm = self.lock["arm_catalog"][0]
        return {**record, "fixture_id": "opaque-fixture", "selection_id": "opaque-selection", "record_digest": record["bundle_digest"], "fixture_digest": record["bundle_digest"], "arm": arm, "arm_id": "graph_planner", "arm_digest": "sha256:" + "0" * 64, "selection_digest": "sha256:" + "0" * 64}

    def __post_init__(self) -> None:
        # Keep the checkpoint as canonical bytes.  Bytes are immutable and a
        # fresh canonical parse on restore prevents nested dict/list aliases
        # from leaking between the live evaluator and its pre-run state.
        self._snapshot_bytes = canonical_bytes(self.graph)
        self.pre_run_graph_snapshot_digest = object_hash(parse_canonical(self._snapshot_bytes))
        self._snapshot = _deep_freeze(parse_canonical(self._snapshot_bytes))
        self._snapshot_grants = parse_canonical(canonical_bytes(self.grants))
        self._snapshot_reserved = dict(self.reserved)
        self._snapshot_simulator_calls = self.simulator_calls
        if self.lock is not None:
            from .runner import validate_local_lock
            self.lock = validate_local_lock(dict(self.lock))
            authority = self.lock["evaluator_authority"]
            if (self.receipts is None
                    or b64encode(self.receipts.public_key.public_bytes_raw()) != authority["public_key"]
                    or self.receipts.authority_id != authority["authority_id"]
                    or self.receipts.key_id != authority["key_id"]):
                raise P4ProtocolError("lock-bound evaluator authority")
        if (self.lock is None) != (self.receipts is None):
            raise P4ProtocolError("evaluator authority incomplete")

    def release(self, run_id: str, fixture_id: str, sequence: int, parent: str | None) -> dict[str, Any]:
        fixture = self._fixture_for(run_id)
        observation = dict(fixture.get("observations", [{"signal": sequence}])[0])
        envelope = {"schema": "P4R0TaskEnvelopeV1", "run_id": run_id, "sequence": sequence, "fixture_id": fixture_id, "logical_time": sequence, "observation": observation, "parent_receipt": parent}
        envelope["envelope_digest"] = object_hash(envelope)
        return envelope

    def _authority(self) -> tuple[dict[str, Any], P4ReceiptLog]:
        if self.lock is None or self.receipts is None:
            raise P4ProtocolError("signed evaluator authority required")
        return dict(self.lock), self.receipts

    def _parent_replan(self, proposal: dict[str, Any], lock: dict[str, Any], log: P4ReceiptLog, fixture: str) -> dict[str, Any]:
        parent = proposal["causal_parent_receipt_hash"]
        if parent is None:
            raise P4ProtocolError("proposal causal receipt required")
        receipt = log.get(parent)
        receipt_payload = receipt["payload"]
        fixture = self._fixture_for(proposal["run_id"])
        if (receipt["kind"] != "replan" or receipt_payload["run_id"] != proposal["run_id"]
                or receipt_payload["lock_digest"] != lock["lock_digest"]
                or receipt_payload["fixture_digest"] != fixture["bundle_digest"]
                or receipt_payload["fixture_record_digest"] != fixture["record_digest"]
                or receipt_payload["fixture_selection_id"] != fixture["selection_id"]
                or ("selection_digest" in receipt_payload["binding"] and receipt_payload["binding"].get("selection_digest") != fixture.get("selection_digest"))
                or ("arm_digest" in receipt_payload["binding"] and receipt_payload["binding"].get("arm_digest") != fixture.get("arm_digest"))
                or receipt_payload["graph_snapshot_digest"] != self.pre_run_graph_snapshot_digest):
            raise P4ProtocolError("proposal causal receipt")
        return receipt

    def _reserve(self, reservation: dict[str, int], lock: dict[str, Any]) -> None:
        if any(value <= 0 for value in reservation.values()):
            raise P4ProtocolError("nonzero reservation required")
        limits = lock["limits"]
        if (self.reserved["actions"] + reservation["actions"] > limits["action_grants"]
                or self.reserved["risk"] + reservation["risk"] > limits["risk_units"]
                or self.reserved["transactions"] + reservation["transactions"] > limits["transactions"]):
            raise P4ProtocolError("locked reservation limit")

    def grant(self, proposal: Mapping[str, Any], now: int) -> dict[str, Any]:
        p = validate_proposal(proposal)
        if type(now) is not int or now < 0:
            raise P4ProtocolError("invalid grant time")
        lock, log = self._authority()
        if p["kind"] not in lock["grant_kinds"]:
            raise P4ProtocolError("unsupported evaluator grant")
        fixture = self._fixture_for(p["run_id"])
        parent = self._parent_replan(p, lock, log, fixture)
        self._reserve(p["reservation"], lock)
        reservation_digest = canonical_reservation_digest(run_id=p["run_id"], proposal_digest=p["proposal_digest"], proposal_sequence=p["sequence"], snapshot_digest=self.pre_run_graph_snapshot_digest, reservation=p["reservation"])
        context = {"fixture_key": fixture["fixture_key"], "selection_digest": fixture.get("selection_digest", "sha256:" + "0" * 64), "arm_id": fixture.get("arm_id", "graph_planner"), "arm_digest": fixture.get("arm_digest", "sha256:" + "0" * 64), "fixture_record_digest": fixture["record_digest"]}
        binding = {"proposal_digest": p["proposal_digest"], "proposal_sequence": p["sequence"], "causal_parent_receipt_digest": parent["receipt_hash"], "reservation": dict(p["reservation"]), "reservation_digest": reservation_digest, **context}
        proposal_receipt = log.append("proposal", payload(run_id=p["run_id"], lock_digest=lock["lock_digest"], fixture_digest=fixture["bundle_digest"], fixture_record_digest=fixture["record_digest"], fixture_id=fixture["fixture_id"], fixture_selection_id=fixture["selection_id"], snapshot_digest=self.pre_run_graph_snapshot_digest, outcome="verified", reason="proposal_registered", resources=self.reserved, binding=binding))
        token = secrets.token_urlsafe(32)
        reserved_after = {"actions": self.reserved["actions"] + p["reservation"]["actions"], "risk": self.reserved["risk"] + p["reservation"]["risk"], "transactions": self.reserved["transactions"] + p["reservation"]["transactions"]}
        grant_binding = {**binding, "proposal_receipt_digest": proposal_receipt["receipt_hash"], "grant_kind": p["kind"]}
        grant_receipt = log.append("grant", payload(run_id=p["run_id"], lock_digest=lock["lock_digest"], fixture_digest=fixture["bundle_digest"], fixture_record_digest=fixture["record_digest"], fixture_id=fixture["fixture_id"], fixture_selection_id=fixture["selection_id"], snapshot_digest=self.pre_run_graph_snapshot_digest, outcome="verified", reason="grant_reserved", resources=reserved_after, binding=grant_binding))
        record = {"proposal": p, "reservation_digest": reservation_digest, "expires": now + 1, "grant_receipt": grant_receipt, "proposal_receipt": proposal_receipt}
        self.grants[token] = record
        self.reserved = reserved_after
        return {"schema": "P4R0GrantV1", "token": token, "proposal_digest": p["proposal_digest"], "run_id": p["run_id"], "sequence": p["sequence"], "expires": record["expires"], "reservation": dict(p["reservation"]), "reservation_digest": reservation_digest, "snapshot_digest": self.pre_run_graph_snapshot_digest, "proposal_receipt_digest": proposal_receipt["receipt_hash"], "grant_receipt_digest": grant_receipt["receipt_hash"]}

    def act(self, proposal: Mapping[str, Any], grant: Mapping[str, Any], now: int) -> dict[str, Any]:
        p = validate_proposal(proposal)
        lock, log = self._authority()
        fixture = self._fixture_for(p["run_id"])
        fields = {"schema", "token", "proposal_digest", "run_id", "sequence", "expires", "reservation", "reservation_digest", "snapshot_digest", "proposal_receipt_digest", "grant_receipt_digest"}
        if not isinstance(grant, Mapping) or set(grant) != fields or grant.get("schema") != "P4R0GrantV1":
            raise P4ProtocolError("grant schema")
        token = grant.get("token")
        record = self.grants.get(token) if isinstance(token, str) else None
        if (record is None or type(now) is not int or now < 0 or now > record["expires"]
                or grant["proposal_digest"] != p["proposal_digest"] or grant["run_id"] != p["run_id"]
                or grant["sequence"] != p["sequence"] or grant["expires"] != record["expires"]
                or grant["reservation"] != p["reservation"] or grant["reservation_digest"] != record["reservation_digest"]
                or grant["snapshot_digest"] != self.pre_run_graph_snapshot_digest
                or grant["proposal_receipt_digest"] != record["proposal_receipt"]["receipt_hash"]
                or grant["grant_receipt_digest"] != record["grant_receipt"]["receipt_hash"]):
            raise P4ProtocolError("expired, replayed, or unbound grant")
        self.grants.pop(token)
        context = {"fixture_key": fixture["fixture_key"], "selection_digest": fixture.get("selection_digest", "sha256:" + "0" * 64), "arm_id": fixture.get("arm_id", "graph_planner"), "arm_digest": fixture.get("arm_digest", "sha256:" + "0" * 64), "fixture_record_digest": fixture["record_digest"]}
        action_binding = {"proposal_digest": p["proposal_digest"], "proposal_receipt_digest": record["proposal_receipt"]["receipt_hash"], "grant_receipt_digest": record["grant_receipt"]["receipt_hash"], "proposal_sequence": p["sequence"], "reservation": dict(p["reservation"]), "reservation_digest": record["reservation_digest"], **{key: context[key] for key in ("fixture_key", "selection_digest", "arm_id", "arm_digest", "fixture_record_digest")}}
        action_receipt = log.append("action", payload(run_id=p["run_id"], lock_digest=lock["lock_digest"], fixture_digest=fixture["bundle_digest"], fixture_record_digest=fixture["record_digest"], fixture_id=fixture["fixture_id"], fixture_selection_id=fixture["selection_id"], snapshot_digest=self.pre_run_graph_snapshot_digest, outcome="verified", reason="broker_action", resources=self.reserved, binding=action_binding))
        self.simulator_calls += 1
        trace_events = {"graph_planner": ["Initial", "CausalHypothesis", "CausalQuery", "InterventionCandidate", "CounterfactualBranch", "PlanNode", "ActionReservation", "GraphActionProposalV1", "Replan", "Complete"], "search_budget_matched": ["Initial", "CausalHypothesis", "CausalQuery", "InterventionCandidate", "CounterfactualBranch", "PlanNode", "ActionReservation", "GraphActionProposalV1", "Replan", "SearchBudget:12", "Complete"], "reactive_no_plan": ["Initial", "ReactiveTransition", "ActionReservation", "GraphActionProposalV1", "DirectAction", "Complete"], "no_causal_model": ["Initial", "PlanNode", "ActionReservation", "GraphActionProposalV1", "DirectAction", "Complete"], "reset_memory": ["Initial", "CausalHypothesis", "CausalQuery", "InterventionCandidate", "MemoryReset", "Impasse"]}[fixture["arm_id"]]
        trace = {"schema": "P4R0NativeTraceV1", "arm_id": fixture["arm_id"], "selection_digest": fixture["selection_digest"], "events": trace_events}
        outcome = {"schema": "P4R0SealedActionOutcomeV1", "run_id": p["run_id"], "fixture_id": fixture["fixture_id"], "fixture_selection_id": fixture["selection_id"], "fixture_digest": fixture["bundle_digest"], "fixture_record_digest": fixture["record_digest"], "arm_id": fixture["arm_id"], "arm_digest": fixture["arm_digest"], "selection_digest": fixture["selection_digest"], "proposal_digest": p["proposal_digest"], "proposal_receipt_digest": record["proposal_receipt"]["receipt_hash"], "grant_receipt_digest": record["grant_receipt"]["receipt_hash"], "broker_receipt_digest": action_receipt["receipt_hash"], "replan_receipt_digest": p["causal_parent_receipt_hash"], "sequence": p["sequence"] + 1, "snapshot_digest": self.pre_run_graph_snapshot_digest, "reservation": dict(p["reservation"]), "reservation_digest": record["reservation_digest"], "success": True, "trace_digest": object_hash(trace)}
        outcome["outcome_digest"] = object_hash(outcome)
        outcome_binding = {**action_binding, "broker_receipt_digest": action_receipt["receipt_hash"], "outcome_sequence": outcome["sequence"], "outcome_digest": outcome["outcome_digest"], "replan_receipt_digest": outcome["replan_receipt_digest"]}
        outcome_receipt = log.append("outcome", payload(run_id=p["run_id"], lock_digest=lock["lock_digest"], fixture_digest=fixture["bundle_digest"], fixture_record_digest=fixture["record_digest"], fixture_id=fixture["fixture_id"], fixture_selection_id=fixture["selection_id"], snapshot_digest=self.pre_run_graph_snapshot_digest, outcome="verified", reason="sealed_action_outcome", resources=self.reserved, binding=outcome_binding))
        outcome["receipt"] = outcome_receipt
        return outcome

    def verify_sealed_action_outcome(self, outcome: Mapping[str, Any]) -> dict[str, Any]:
        v = validate_sealed_action_outcome(outcome)
        lock, log = self._authority()
        fixture = self._fixture_for(v["run_id"])
        context = {"fixture_key": fixture["fixture_key"], "selection_digest": fixture.get("selection_digest", "sha256:" + "0" * 64), "arm_id": fixture.get("arm_id", "graph_planner"), "arm_digest": fixture.get("arm_digest", "sha256:" + "0" * 64), "fixture_record_digest": fixture["record_digest"]}
        outcome_receipt = log.get(v["receipt"].get("receipt_hash") if isinstance(v["receipt"], dict) else "")
        broker = log.get(v["broker_receipt_digest"])
        grant = log.get(v["grant_receipt_digest"])
        proposal = log.get(v["proposal_receipt_digest"])
        receipts = (proposal, grant, broker, outcome_receipt)
        if any(receipt["payload"]["run_id"] != v["run_id"] or receipt["payload"]["lock_digest"] != lock["lock_digest"] or receipt["payload"]["fixture_digest"] != fixture["bundle_digest"] or receipt["payload"]["fixture_record_digest"] != fixture["record_digest"] or receipt["payload"]["fixture_id"] != fixture["fixture_id"] or receipt["payload"]["fixture_selection_id"] != fixture["selection_id"] or receipt["payload"]["graph_snapshot_digest"] != v["snapshot_digest"] for receipt in receipts):
            raise P4ProtocolError("outcome receipt context")
        proposal_binding = proposal["payload"]["binding"]
        grant_binding = grant["payload"]["binding"]
        action_binding = broker["payload"]["binding"]
        outcome_binding = outcome_receipt["payload"]["binding"]
        expected_proposal = {"proposal_digest": v["proposal_digest"], "proposal_sequence": v["sequence"] - 1, "causal_parent_receipt_digest": proposal["previous_hash"], "reservation": v["reservation"], "reservation_digest": v["reservation_digest"], **context}
        expected_grant = {**expected_proposal, "proposal_receipt_digest": proposal["receipt_hash"], "grant_kind": grant_binding.get("grant_kind")}
        expected_action = {"proposal_digest": v["proposal_digest"], "proposal_receipt_digest": proposal["receipt_hash"], "grant_receipt_digest": grant["receipt_hash"], "proposal_sequence": v["sequence"] - 1, "reservation": v["reservation"], "reservation_digest": v["reservation_digest"], **context}
        expected_outcome = {**expected_action, "broker_receipt_digest": broker["receipt_hash"], "outcome_sequence": v["sequence"], "outcome_digest": v["outcome_digest"], "replan_receipt_digest": v["replan_receipt_digest"]}
        if (v["replan_receipt_digest"] != proposal_binding.get("causal_parent_receipt_digest")
                or v["replan_receipt_digest"] != proposal["payload"]["binding"].get("causal_parent_receipt_digest")):
            raise P4ProtocolError("unbound replan receipt")
        if (v["receipt"] != outcome_receipt or proposal["kind"] != "proposal" or grant["kind"] != "grant" or broker["kind"] != "action" or outcome_receipt["kind"] != "outcome"
                or proposal["previous_hash"] is None or grant["previous_hash"] != proposal["receipt_hash"] or broker["previous_hash"] != grant["receipt_hash"] or outcome_receipt["previous_hash"] != broker["receipt_hash"]
                or proposal_binding != expected_proposal or grant_binding != expected_grant or action_binding != expected_action or outcome_binding != expected_outcome
                or expected_grant["grant_kind"] not in lock["grant_kinds"]):
            raise P4ProtocolError("unbound sealed action outcome")
        return v

    def verified_native_outcome(self, outcome: Mapping[str, Any]) -> dict[str, Any]:
        """Translate only a verified evaluator outcome into Rust transport fields."""
        v = self.verify_sealed_action_outcome(outcome)
        return {"run_id": v["run_id"], "fixture_id": v["fixture_id"], "fixture_selection_id": v["fixture_selection_id"], "fixture_digest": v["fixture_digest"], "fixture_record_digest": v["fixture_record_digest"], "arm_id": v["arm_id"], "arm_digest": v["arm_digest"], "selection_digest": v["selection_digest"], "proposal_digest": v["proposal_digest"], "proposal_receipt_digest": v["proposal_receipt_digest"], "grant_receipt_digest": v["grant_receipt_digest"], "broker_receipt_digest": v["broker_receipt_digest"], "replan_receipt_digest": v["replan_receipt_digest"], "sequence": v["sequence"], "snapshot_digest": v["snapshot_digest"], "reservation_digest": v["reservation_digest"], "outcome_receipt_digest": v["receipt"]["receipt_hash"], "trace_digest": v["trace_digest"], "success": v["success"]}

    def serialized_verified_native_outcome(self, outcome: Mapping[str, Any]) -> bytes:
        """Emit the canonical evaluator-signed transport accepted by Rust only.

        The receiver pins authority/key/lock out-of-band; carrying those fields
        inside the signature lets it reject cross-authority and cross-lock replay
        before the native opaque completion adapter is reached.
        """
        lock, log = self._authority()
        authority = lock["evaluator_authority"]
        if (not hasattr(log.signer, "sign")
                or b64encode(log.public_key.public_bytes_raw()) != authority["public_key"]
                or log.authority_id != authority["authority_id"]
                or log.key_id != authority["key_id"]):
            raise P4ProtocolError("evaluator signing authority unavailable")
        transport = {
            "schema": "P4R0EvaluatorSignedOutcomeV1",
            "authority_id": authority["authority_id"],
            "key_id": authority["key_id"],
            "authority_public_key": authority["public_key"],
            "lock_digest": lock["lock_digest"],
            **self.verified_native_outcome(outcome),
        }
        transport["signature"] = sign(transport, log.signer)
        return canonical_bytes(transport)

    def restore(self) -> str:
        self.graph = parse_canonical(self._snapshot_bytes)
        self.grants = parse_canonical(canonical_bytes(self._snapshot_grants))
        self.reserved = dict(self._snapshot_reserved)
        self.simulator_calls = self._snapshot_simulator_calls
        self.active_fixture = None
        self.active_selection = None
        got = object_hash(self.graph)
        if got != self.pre_run_graph_snapshot_digest or canonical_bytes(self.graph) != self._snapshot_bytes:
            raise P4ProtocolError("exact canonical restore failed")
        return got
