"""Broker-owned ingress for untrusted native graph action proposals.

Graph code may only serialize a ``GraphActionProposalV1`` candidate and call
``EvaluationActionClient.submit_native_graph_proposal``. This module owns the
catalogue, request identity allocation, provenance/causal checks, and any
access to evaluator grants; proposal bytes never select a host callable.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable

from .canonical import ProtocolError, canonical_bytes, object_hash, parse_canonical, sha256
from .provenance import NativeGraphProvenanceVerifier, VerifiedGraphProposal
from .simulator import METHOD, normalized_args

_GRAPH_FIELDS = frozenset({
    "schema", "proposal_id", "kind", "args", "input_refs", "source",
    "causal_parent_receipt_hash", "requested_budget", "graph_logical_time",
    "proposal_digest",
})
_SOURCE_FIELDS = frozenset({
    "origin_rule_digest", "source_node_type", "source_content_digest",
    "graph_snapshot_digest",
})
_BUDGET_FIELDS = frozenset({"wall_ms", "cpu_ms", "memory_bytes", "writes", "network_bytes"})
CATALOG = {"GraphCounterAdvanceV1": METHOD}


@dataclass(frozen=True)
class ObservedGraphActionOutcomeV1:
    """Non-authoritative graph mirror of a broker receipt."""
    proposal_digest: str | None
    phase: str
    reason_code: str | None
    request_hash: str | None
    signed_receipt_hash: str | None
    receipt_sequence: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "ObservedGraphActionOutcomeV1",
            "proposal_digest": self.proposal_digest,
            "phase": self.phase,
            "reason_code": self.reason_code,
            "request_hash": self.request_hash,
            "signed_receipt_hash": self.signed_receipt_hash,
            "receipt_sequence": self.receipt_sequence,
        }


class GraphProposalAdapter:
    """A deliberately narrow graph reader: it only freezes attributes to bytes."""

    @staticmethod
    def serialize(attrs: dict[str, Any]) -> bytes:
        # ``canonical_bytes`` is intentionally the entire adapter capability.
        # It has no broker, grant, handler registry, simulator, or manifest.
        return canonical_bytes(attrs)


class GraphProposalProjector:
    """Trusted projection of verified native graph candidates into ActionRequestV2."""

    def __init__(self, broker, *, grant_resolver: Callable[[dict[str, Any]], bytes | None] | None = None,
                 provenance_verifier: NativeGraphProvenanceVerifier | None = None):
        self._broker = broker
        self._grant_resolver = grant_resolver
        self._provenance_verifier = provenance_verifier
        if provenance_verifier is not None and broker._graph_binding_verifier is None:
            broker.install_graph_binding_verifier(provenance_verifier.validates_binding)
        self._used_proposals = set(broker.graph_proposal_replays())

    def submit(self, proposal_bytes: bytes):
        """Trusted compatibility ingress; public evaluation code never uses it."""
        proposal: dict[str, Any] | None = None
        proposal_id: str | None = None
        try:
            proposal = parse_canonical(proposal_bytes)
            proposal_id = proposal.get("proposal_id") if isinstance(proposal.get("proposal_id"), str) else None
            if "method" in proposal:
                return self._deny(proposal, "method_substitution")
            self._validate_proposal(proposal)
            evidence = self._verified_provenance(proposal)
            if isinstance(evidence, str):
                return self._deny(proposal, evidence)
        except (ProtocolError, TypeError, KeyError, ValueError):
            return self._broker._deny(proposal_id, "invalid_graph_proposal")
        return self._submit_verified(evidence)

    def submit_native_proposal(self, proposal: dict[str, Any]):
        """Worker ingress: require a complete candidate and attested provenance.

        This deliberately does not accept an ID-only route. The candidate is
        untrusted until it exactly matches an evaluator-attested export; a
        valid-looking forged or mismatched candidate receives a signed denial.
        """
        if not isinstance(proposal, dict):
            return self._broker._deny(None, "invalid_graph_proposal")
        return self.submit(canonical_bytes(proposal))

    def _submit_verified(self, evidence: VerifiedGraphProposal):
        proposal = evidence.proposal
        graph_fields = self._graph_fields(proposal)
        replay_key = (proposal["proposal_id"], proposal["proposal_digest"])
        if replay_key in self._used_proposals:
            return self._broker._deny(None, "replay", **graph_fields)
        try:
            # This validation is over the evaluator-owned record, not client bytes.
            self._validate_proposal(proposal)
            method = CATALOG.get(proposal["kind"])
            if method is None:
                return self._deny(proposal, "graph_action_not_catalogued")
            if not self._valid_parent(proposal, method):
                return self._deny(proposal, "invalid_causal_predecessor")
            request = self._project(proposal, method)
            binding = self._provenance_verifier.bind_request(evidence, request)
            grant_bytes = None
            # Do not request a grant for a manifest-denied method.  This keeps
            # P0-A's empty enablement set the first authorization boundary.
            if method in self._broker.manifest.enabled_methods:
                if self._grant_resolver is None:
                    return self._deny(proposal, "grant_required", request=request)
                grant_bytes = self._grant_resolver(dict(request))
                if grant_bytes is None:
                    return self._deny(proposal, "grant_required", request=request)
            return self._broker.submit_verified_graph_request(
                canonical_bytes(request), grant_bytes, binding=binding,
            )
        except ProtocolError:
            return self._deny(proposal, "invalid_graph_proposal")
        finally:
            # Only a durable receipt consumes a proposal.  An impasse is not a
            # retry/fallback path and the broker remains terminally impassed.
            receipt = self._broker.receipt_log.last_receipt
            if receipt is not None and receipt.get("graph_proposal_id") == proposal["proposal_id"]:
                self._used_proposals.add(replay_key)

    def _deny(self, proposal: dict[str, Any], reason: str, *, request: dict[str, Any] | None = None):
        fields = self._graph_fields(proposal)
        if request is not None:
            fields.update({"request_hash": request["request_hash"], "method": request["method"]})
        return self._broker._deny(None, reason, **fields)

    def _validate_proposal(self, proposal: dict[str, Any]) -> None:
        if set(proposal) != _GRAPH_FIELDS or proposal.get("schema") != "GraphActionProposalV1":
            raise ProtocolError("graph proposal schema")
        try:
            uuid.UUID(proposal["proposal_id"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise ProtocolError("proposal id") from exc
        if not isinstance(proposal["kind"], str) or type(proposal["graph_logical_time"]) is not int:
            raise ProtocolError("proposal kind/time")
        if proposal["graph_logical_time"] < 0 or not isinstance(proposal["args"], dict):
            raise ProtocolError("proposal args")
        if not isinstance(proposal["input_refs"], list) or any(
                not isinstance(ref, str) or not ref.startswith("sha256:") for ref in proposal["input_refs"]):
            raise ProtocolError("proposal inputs")
        source = proposal["source"]
        if not isinstance(source, dict) or set(source) != _SOURCE_FIELDS:
            raise ProtocolError("proposal source")
        if (not isinstance(source["source_node_type"], str) or not source["source_node_type"] or
                any(not isinstance(source[name], str) or not source[name].startswith("sha256:")
                    for name in _SOURCE_FIELDS - {"source_node_type"})):
            raise ProtocolError("proposal source")
        budget = proposal["requested_budget"]
        if not isinstance(budget, dict) or set(budget) != _BUDGET_FIELDS or any(
                type(value) is not int or value < 0 for value in budget.values()):
            raise ProtocolError("proposal budget")
        parent = proposal["causal_parent_receipt_hash"]
        if parent is not None and (not isinstance(parent, str) or not parent.startswith("sha256:")):
            raise ProtocolError("proposal parent")
        if proposal["proposal_digest"] != object_hash(proposal, "proposal_digest"):
            raise ProtocolError("proposal digest")

    def _verified_provenance(self, proposal: dict[str, Any]) -> VerifiedGraphProposal | str:
        if self._provenance_verifier is None:
            return "missing_graph_provenance"
        return self._provenance_verifier.verify(proposal)

    def _valid_parent(self, proposal: dict[str, Any], method: str) -> bool:
        parent = proposal["causal_parent_receipt_hash"]
        # The sole P0 catalogue entry is evaluator-root eligible.
        if parent is None:
            return method == METHOD
        return self._broker.has_causal_receipt(parent)

    def _project(self, proposal: dict[str, Any], method: str) -> dict[str, Any]:
        args = normalized_args(proposal["args"])
        budget = proposal["requested_budget"]
        limits = self._broker.manifest.body["limits"]
        bounded = {"wall_ms", "cpu_ms", "memory_bytes"}
        if (any(budget[name] > limits[name] for name in bounded) or
                budget["writes"] != 0 or budget["network_bytes"] != 0):
            raise ProtocolError("proposal budget exceeds catalog or manifest")
        sequence = self._broker.allocate_graph_sequence()
        request_id = str(uuid.uuid5(uuid.UUID(self._broker.manifest.run_id),
                                     proposal["proposal_id"] + proposal["proposal_digest"]))
        nonce = sha256((proposal["proposal_id"] + proposal["proposal_digest"]).encode("ascii"))[7:]
        request = {
            "schema": "ActionRequestV2", "request_id": request_id,
            "run_id": self._broker.manifest.run_id, "sequence": sequence, "nonce": nonce,
            "created_at_unix_ms": self._broker.now_ms(),
            "expires_at_unix_ms": self._broker.manifest.body["expires_at_unix_ms"],
            "method": method, "args": args,
            "input_refs": sorted(set(proposal["input_refs"] + [proposal["proposal_digest"]])),
            "input_snapshot_digest": self._broker.manifest.body["input_snapshot_digest"],
            "causal_parent_receipt_hash": proposal["causal_parent_receipt_hash"],
            "requested_budget": dict(budget),
            "graph_provenance": {
                "proposal_id": proposal["proposal_id"], "proposal_digest": proposal["proposal_digest"],
                "causal_parent_receipt_hash": proposal["causal_parent_receipt_hash"],
            },
        }
        request["request_hash"] = object_hash(request)
        return request

    @staticmethod
    def _graph_fields(proposal: dict[str, Any]) -> dict[str, Any]:
        return {
            "graph_proposal_id": proposal["proposal_id"],
            "graph_proposal_digest": proposal["proposal_digest"],
            "causal_parent_receipt_hash": proposal["causal_parent_receipt_hash"],
        }


def observed_outcome(receipt: dict[str, Any] | None, reply) -> ObservedGraphActionOutcomeV1:
    return ObservedGraphActionOutcomeV1(
        proposal_digest=None if receipt is None else receipt.get("graph_proposal_digest"),
        phase=reply.phase,
        reason_code=None if receipt is None else receipt.get("reason_code"),
        request_hash=None if receipt is None else receipt.get("request_hash"),
        signed_receipt_hash=None if receipt is None else receipt.get("receipt_hash"),
        receipt_sequence=reply.receipt_sequence_or_null,
    )


def execute_evaluation_graph_proposals(adapter, action_client, *, logical_time: int = 0) -> int:
    """Pump native proposal nodes without constructing legacy host handlers.

    The substrate adapter is intentionally used only to enumerate immutable
    candidate attributes and write an observed (non-causal) outcome node.
    ``logical_time`` is deliberately not used to fill candidate data.
    """
    sub, native = adapter.s, adapter.inner
    completed = 0
    for proposal_node in list(sub.nodes("GraphActionProposalV1")):
        if not native.has_node(proposal_node):
            continue
        attrs = dict(sub.node(proposal_node)["attrs"])
        # The evaluated client submits the complete native candidate. The
        # evaluator alone verifies it against its attested canonical export.
        reply = action_client.submit_native_graph_proposal(attrs)
        outcome = action_client.observed_outcome(reply).as_dict()
        outcome_node = sub.add_node("ObservedGraphActionOutcomeV1", outcome)
        native.add_edge_unchecked(proposal_node, "observed_outcome", outcome_node)
        completed += 1
    return completed
