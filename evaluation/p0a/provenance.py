"""Evaluator-owned verification of canonical native graph-proposal exports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical import (canonical_bytes, ProtocolError, object_hash, parse_canonical, sha256,
                        sign, verify_signature)

_EXPORT_FIELDS = frozenset({
    "schema", "run_id", "input_snapshot_digest", "issued_at_unix_ms",
    "expires_at_unix_ms", "evidence", "export_digest",
})
_EVIDENCE_FIELDS = frozenset({
    "proposal_id", "proposal_digest", "proposal", "source", "causal_parent_receipt_hash",
    "graph_logical_time",
})
_ATTESTATION_FIELDS = frozenset({
    "schema", "run_id", "export_digest", "agent_build_digest", "control_plane_digest",
    "input_snapshot_digest", "capture_sequence", "captured_at_unix_ms", "key_id", "signature",
})
_DIGEST_FIELDS = ("export_digest", "agent_build_digest", "control_plane_digest",
                  "input_snapshot_digest")


class NativeGraphExportAttestationVerifier:
    """Verify evaluator/supervisor custody of one canonical native export.

    This is intentionally separate from native-export structural validation: an
    internally consistent export is not evaluator evidence without this
    authority signature.  Local test signers exercise the protocol only and do
    not establish custody across users or processes.
    """

    def __init__(self, keys: dict[str, Any], *, now_ms):
        self._keys = dict(keys)
        self._now_ms = now_ms

    def verify(self, native_export: bytes, attestation: dict[str, Any] | None, *,
               run_id: str, agent_build_digest: str, control_plane_digest: str,
               input_snapshot_digest: str) -> None:
        if not isinstance(attestation, dict) or set(attestation) != _ATTESTATION_FIELDS:
            raise ProtocolError("missing native graph export attestation")
        if attestation.get("schema") != "NativeGraphExportAttestationV1":
            raise ProtocolError("native graph export attestation schema")
        key = self._keys.get(attestation.get("key_id"))
        if key is None:
            raise ProtocolError("unknown native graph export attestation key")
        verify_signature(attestation, key)
        if any(not isinstance(attestation.get(name), str) or
               not attestation[name].startswith("sha256:") or len(attestation[name]) != 71
               for name in _DIGEST_FIELDS):
            raise ProtocolError("native graph export attestation digest")
        if (attestation["run_id"] != run_id or
                attestation["agent_build_digest"] != agent_build_digest or
                attestation["control_plane_digest"] != control_plane_digest or
                attestation["input_snapshot_digest"] != input_snapshot_digest or
                type(attestation["capture_sequence"]) is not int or
                attestation["capture_sequence"] < 0 or
                type(attestation["captured_at_unix_ms"]) is not int or
                attestation["captured_at_unix_ms"] > self._now_ms()):
            raise ProtocolError("native graph export attestation binding")
        export = parse_canonical(native_export)
        if export.get("export_digest") != attestation["export_digest"]:
            raise ProtocolError("native graph export attestation digest mismatch")


def make_native_graph_export_attestation(native_export: bytes, *, run_id: str,
                                          agent_build_digest: str, control_plane_digest: str,
                                          input_snapshot_digest: str, capture_sequence: int,
                                          captured_at_unix_ms: int, signer, key_id: str) -> dict[str, Any]:
    """Create the evaluator/supervisor signature after canonical export capture."""
    export = parse_canonical(native_export)
    export_digest = export.get("export_digest")
    if not isinstance(export_digest, str) or not export_digest.startswith("sha256:"):
        raise ProtocolError("native graph export capture digest")
    body = {
        "schema": "NativeGraphExportAttestationV1", "run_id": run_id,
        "export_digest": export_digest, "agent_build_digest": agent_build_digest,
        "control_plane_digest": control_plane_digest,
        "input_snapshot_digest": input_snapshot_digest,
        "capture_sequence": capture_sequence, "captured_at_unix_ms": captured_at_unix_ms,
        "key_id": key_id,
    }
    body["signature"] = sign(body, signer)
    return body


def _copy(value: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical detached copy of evaluator-owned export data."""
    return parse_canonical(canonical_bytes(value))


@dataclass(frozen=True)
class VerifiedGraphProposal:
    """An evaluator-private match to one canonical native-export record."""
    proposal_id: str
    proposal_digest: str
    causal_parent_receipt_hash: str | None
    proposal: dict[str, Any] = field(repr=False, compare=False)
    _capability: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class GraphRequestBinding:
    """Seal exactly the V2 projection derived from native export evidence."""
    proposal_id: str
    proposal_digest: str
    run_id: str
    request_id: str
    request_hash: str
    sequence: int
    nonce_digest: str
    causal_parent_receipt_hash: str | None
    native_export_digest: str
    native_attestation_digest: str | None
    request_bytes: bytes = field(repr=False, compare=False)
    _capability: object = field(repr=False, compare=False)

    def receipt_fields(self) -> dict[str, Any]:
        return {
            "graph_proposal_id": self.proposal_id,
            "graph_proposal_digest": self.proposal_digest,
            "causal_parent_receipt_hash": self.causal_parent_receipt_hash,
            "request_id": self.request_id,
            "nonce_digest": self.nonce_digest,
            "request_sequence": self.sequence,
            "native_export_digest": self.native_export_digest,
            "native_attestation_digest": self.native_attestation_digest,
        }


class NativeGraphProvenanceVerifier:
    """Verify complete bounded candidates against evaluator-attested exports.

    The worker submits a complete ``GraphActionProposalV1`` candidate. The
    evaluator admits it only when it exactly equals the matching ``proposal``
    in an evaluator-attested canonical native export, then seals the trusted
    ``ActionRequestV2`` projection derived from that verified evidence.
    """

    def __init__(self, native_export: bytes, *, run_id: str, input_snapshot_digest: str, now_ms,
                 native_attestation_digest: str | None = None):
        self._capability = object()
        self._run_id = run_id
        self._input_snapshot_digest = input_snapshot_digest
        self._now_ms = now_ms
        export = parse_canonical(native_export)
        self._validate_export(export)
        if export["run_id"] != run_id or export["input_snapshot_digest"] != input_snapshot_digest:
            raise ProtocolError("native graph export binding")
        self._export = export
        self._export_digest = export["export_digest"]
        if native_attestation_digest is not None and (not isinstance(native_attestation_digest, str) or
                                                       not native_attestation_digest.startswith("sha256:")):
            raise ProtocolError("native graph attestation digest")
        self._native_attestation_digest = native_attestation_digest
        self._evidence = tuple(export["evidence"])

    def _validate_export(self, export: dict[str, Any]) -> None:
        if set(export) != _EXPORT_FIELDS or export.get("schema") != "NativeGraphEvidenceExportV1":
            raise ProtocolError("native graph export schema")
        if (not isinstance(export.get("run_id"), str) or
                not isinstance(export.get("input_snapshot_digest"), str) or
                not export["input_snapshot_digest"].startswith("sha256:") or
                type(export.get("issued_at_unix_ms")) is not int or
                type(export.get("expires_at_unix_ms")) is not int or
                export["expires_at_unix_ms"] < export["issued_at_unix_ms"] or
                not isinstance(export.get("evidence"), list) or
                export.get("export_digest") != object_hash(export, "export_digest")):
            raise ProtocolError("native graph export fields")
        seen_ids: set[str] = set()
        for evidence in export["evidence"]:
            if not isinstance(evidence, dict) or set(evidence) != _EVIDENCE_FIELDS:
                raise ProtocolError("native graph evidence fields")
            proposal = evidence["proposal"]
            if (not isinstance(evidence["proposal_id"], str) or
                    evidence["proposal_id"] in seen_ids or
                    not isinstance(evidence["proposal_digest"], str) or
                    not evidence["proposal_digest"].startswith("sha256:") or
                    not isinstance(proposal, dict) or
                    type(evidence["graph_logical_time"]) is not int or
                    evidence["graph_logical_time"] < 0):
                raise ProtocolError("native graph evidence values")
            if (proposal.get("proposal_id") != evidence["proposal_id"] or
                    proposal.get("proposal_digest") != evidence["proposal_digest"] or
                    proposal.get("proposal_digest") != object_hash(proposal, "proposal_digest") or
                    proposal.get("source") != evidence["source"] or
                    proposal.get("causal_parent_receipt_hash") != evidence["causal_parent_receipt_hash"] or
                    proposal.get("graph_logical_time") != evidence["graph_logical_time"]):
                raise ProtocolError("native graph evidence proposal mismatch")
            seen_ids.add(evidence["proposal_id"])

    def _find(self, proposal_id: str) -> dict[str, Any] | str:
        if not self._export["issued_at_unix_ms"] <= self._now_ms() <= self._export["expires_at_unix_ms"]:
            return "stale_graph_provenance"
        matches = [record for record in self._evidence if record["proposal_id"] == proposal_id]
        if not matches:
            return "missing_graph_provenance"
        if len(matches) != 1:
            return "ambiguous_graph_provenance"
        return matches[0]

    def proposal_for_identity(self, proposal_id: str) -> VerifiedGraphProposal | str:
        """Resolve an evaluator-private ID to its sealed canonical proposal."""
        if not isinstance(proposal_id, str):
            return "missing_graph_provenance"
        record = self._find(proposal_id)
        if isinstance(record, str):
            return record
        return VerifiedGraphProposal(record["proposal_id"], record["proposal_digest"],
                                     record["causal_parent_receipt_hash"],
                                     _copy(record["proposal"]), self._capability)

    def verify(self, proposal: dict[str, Any]) -> VerifiedGraphProposal | str:
        """Trusted compatibility check: supplied data must equal the export record."""
        if not isinstance(proposal, dict):
            return "missing_graph_provenance"
        record = self._find(proposal.get("proposal_id"))
        if isinstance(record, str):
            return record
        if proposal != record["proposal"]:
            return "forged_graph_provenance"
        return self.proposal_for_identity(record["proposal_id"])

    def bind_request(self, evidence: VerifiedGraphProposal, request: dict[str, Any]) -> GraphRequestBinding:
        if evidence._capability is not self._capability:
            raise ProtocolError("unverified native graph evidence")
        provenance = request.get("graph_provenance")
        if (request.get("schema") != "ActionRequestV2" or not isinstance(provenance, dict) or
                provenance.get("proposal_id") != evidence.proposal_id or
                provenance.get("proposal_digest") != evidence.proposal_digest or
                provenance.get("causal_parent_receipt_hash") != evidence.causal_parent_receipt_hash or
                request.get("run_id") != self._run_id or
                request.get("causal_parent_receipt_hash") != evidence.causal_parent_receipt_hash):
            raise ProtocolError("graph request binding")
        request_bytes = canonical_bytes(request)
        return GraphRequestBinding(
            evidence.proposal_id, evidence.proposal_digest, self._run_id,
            request["request_id"], request["request_hash"], request["sequence"],
            sha256(request["nonce"].encode("utf-8")), evidence.causal_parent_receipt_hash,
            self._export_digest, self._native_attestation_digest, request_bytes, self._capability,
        )

    def validates_binding(self, binding: object, request: dict[str, Any]) -> bool:
        if not isinstance(binding, GraphRequestBinding) or binding._capability is not self._capability:
            return False
        provenance = request.get("graph_provenance")
        return bool(
            canonical_bytes(request) == binding.request_bytes and
            request.get("schema") == "ActionRequestV2" and
            binding.run_id == self._run_id == request.get("run_id") and
            binding.request_id == request.get("request_id") and
            binding.request_hash == request.get("request_hash") and
            binding.sequence == request.get("sequence") and
            binding.nonce_digest == sha256(request.get("nonce", "").encode("utf-8")) and
            isinstance(provenance, dict) and
            provenance.get("proposal_id") == binding.proposal_id and
            provenance.get("proposal_digest") == binding.proposal_digest and
            provenance.get("causal_parent_receipt_hash") == binding.causal_parent_receipt_hash and
            request.get("causal_parent_receipt_hash") == binding.causal_parent_receipt_hash and
            binding.proposal_digest in request.get("input_refs", [])
        )
