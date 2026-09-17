"""Default-deny local P0-A action broker; it accepts canonical bytes, never callbacks."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from .canonical import ProtocolError, object_hash, parse_canonical, sha256, verify_signature
from .simulator import METHOD, invoke, normalized_args, preview


@dataclass(frozen=True)
class BrokerReply:
    run_id: str
    request_id_or_null: str | None
    phase: str
    receipt_sequence_or_null: int | None

    def as_dict(self) -> dict[str, Any]:
        return {"schema": "BrokerReplyV1", "run_id": self.run_id,
                "request_id_or_null": self.request_id_or_null, "phase": self.phase,
                "receipt_sequence_or_null": self.receipt_sequence_or_null}


class ActionBroker:
    """P0's sole effect boundary; V2 requests require sealed projector evidence."""
    def __init__(self, manifest, *, grant_keys: dict[str, Any], receipt_log, now_ms=None,
                 fixture_registry: bool = False, control=None, runtime_failure_record=None,
                 graph_binding_verifier: Callable[[object, dict[str, Any]], bool] | None = None):
        self.manifest = manifest
        self.grant_keys = dict(grant_keys)
        self.receipt_log = receipt_log
        self.now_ms = now_ms or (lambda: int(time.time() * 1000))
        self.registry = {METHOD: invoke} if fixture_registry else {}
        self.state: dict[str, Any] = {"counter": 0}
        self.used_requests: set[str] = set()
        self.used_nonces: set[str] = set()
        self.used_grants: set[str] = set()
        self.used_sequences: set[int] = set()
        self.impasse = False
        self.killed = False
        self.control = control
        self.runtime_failure_record = runtime_failure_record
        self._graph_binding_verifier = graph_binding_verifier
        self._restore_v2_reservations()

    def install_graph_binding_verifier(self, verifier: Callable[[object, dict[str, Any]], bool]) -> None:
        """Fixture-only setup hook; an evaluation launcher installs this at construction."""
        if self._graph_binding_verifier is not None and self._graph_binding_verifier is not verifier:
            raise ProtocolError("graph binding verifier already installed")
        self._graph_binding_verifier = verifier

    def _restore_v2_reservations(self) -> None:
        """Recover graph reservations from the signed receipt chain at startup."""
        for receipt in self.receipt_log.records:
            if receipt.get("schema") not in {"ActionReceiptV2", "ActionReceiptV3"} or receipt.get("run_id") != self.manifest.run_id:
                continue
            if receipt.get("request_id") is not None:
                self.used_requests.add(receipt["request_id"])
            if receipt.get("nonce_digest") is not None:
                self.used_nonces.add(receipt["nonce_digest"])
            if receipt.get("grant_id") is not None:
                self.used_grants.add(receipt["grant_id"])
            if type(receipt.get("request_sequence")) is int:
                self.used_sequences.add(receipt["request_sequence"])

    def graph_proposal_replays(self) -> set[tuple[str, str]]:
        return {
            (receipt["graph_proposal_id"], receipt["graph_proposal_digest"])
            for receipt in self.receipt_log.records
            if receipt.get("schema") in {"ActionReceiptV2", "ActionReceiptV3"} and receipt.get("run_id") == self.manifest.run_id
        }

    def allocate_graph_sequence(self) -> int:
        return max(self.used_sequences, default=0) + 1

    def has_causal_receipt(self, receipt_hash: str) -> bool:
        return any(receipt.get("receipt_hash") == receipt_hash and
                   receipt.get("run_id") == self.manifest.run_id and
                   receipt.get("outcome") == "accepted"
                   for receipt in self.receipt_log.records)

    def kill(self) -> None:
        self.killed = True
        if self.control is not None:
            self.control.kill("broker_kill")

    def _is_killed(self) -> bool:
        return self.killed or (self.control is not None and self.control.state != "running")

    def _record_runtime_failure(self, reason_code: str, error: Exception) -> None:
        """Publish active-run terminal evidence without reopening the receipt path."""
        if self.runtime_failure_record is None:
            return
        try:
            self.runtime_failure_record.record(
                run_id=self.manifest.run_id, verified_manifest_hash=self.manifest.manifest_hash,
                last_valid_receipt_sequence=self.receipt_log.sequence,
                last_valid_receipt_hash=self.receipt_log.previous,
                reason_code=reason_code, error=error,
            )
        except Exception:
            # Receipt acknowledgement remains fail-closed even if independent
            # control-plane publication is unavailable.
            pass

    def _reply(self, request_id_or_null: str | None, phase: str, **receipt_fields) -> BrokerReply:
        if self.impasse:
            return BrokerReply(self.manifest.run_id, request_id_or_null, "impasse", None)
        try:
            receipt = self.receipt_log.append(run_id=self.manifest.run_id, outcome=phase,
                                              **receipt_fields)
        except Exception as exc:
            self._record_runtime_failure("receipt_append_failed", exc)
            self.impasse = True
            if self.control is not None:
                self.control.kill("receipt_append_failed")
            return BrokerReply(self.manifest.run_id, request_id_or_null, "impasse", None)
        return BrokerReply(self.manifest.run_id, request_id_or_null, phase, receipt["receipt_sequence"])

    def _deny(self, request_id_or_null: str | None, reason: str, **fields) -> BrokerReply:
        return self._reply(request_id_or_null, "denied", reason_code=reason, **fields)

    def submit_action(self, request_bytes: bytes, grant_bytes: bytes | None) -> BrokerReply:
        """Compatibility ingress for ActionRequestV1 only.

        A V2 object is always a graph projection and cannot be injected through
        this public method.  The projector uses ``submit_verified_graph_request``
        with a sealed provenance binding instead.
        """
        request_id = None
        try:
            candidate = parse_canonical(request_bytes)
            request_id = candidate.get("request_id")
            if candidate.get("schema") == "ActionRequestV2":
                return self._deny(request_id, "verified_graph_proposal_required")
        except (ProtocolError, TypeError):
            pass
        return self._submit(request_bytes, grant_bytes, binding=None)

    def submit_verified_graph_request(self, request_bytes: bytes, grant_bytes: bytes | None,
                                      *, binding: object) -> BrokerReply:
        """Projector-only V2 ingress, guarded by the native evidence capability."""
        return self._submit(request_bytes, grant_bytes, binding=binding)

    def _submit(self, request_bytes: bytes, grant_bytes: bytes | None, *, binding: object | None) -> BrokerReply:
        request_id = None
        if self.impasse:
            return BrokerReply(self.manifest.run_id, None, "impasse", None)
        try:
            request = parse_canonical(request_bytes)
            request_id = request.get("request_id")
            self._validate_request(request)
        except (ProtocolError, KeyError, TypeError):
            return self._deny(request_id, "invalid_request")
        is_v2 = request["schema"] == "ActionRequestV2"
        if is_v2:
            if not self._valid_graph_binding(binding, request):
                return self._deny(request_id, "verified_graph_proposal_required")
            fields = self._request_fields(request, binding)
        else:
            if binding is not None:
                return self._deny(request_id, "invalid_request")
            fields = self._request_fields(request, None)
        if self._is_killed():
            return self._reply(request_id, "killed", reason_code="run_killed", **fields)
        try:
            args_hash = sha256(normalized_args(request["args"])) if request["method"] == METHOD else None
        except (ProtocolError, KeyError, TypeError):
            return self._deny(request_id, "invalid_request", **fields)
        fields["normalized_args_hash"] = args_hash
        nonce_key = fields.get("nonce_digest") if is_v2 else request["nonce"]
        if (request["request_id"] in self.used_requests or nonce_key in self.used_nonces or
                (is_v2 and request["sequence"] in self.used_sequences)):
            return self._deny(request_id, "replay", **fields)
        if request["expires_at_unix_ms"] < self.now_ms():
            return self._deny(request_id, "request_expired", **fields)
        if request["method"] not in self.manifest.enabled_methods or request["method"] not in self.registry:
            return self._deny(request_id, "method_not_enabled", **fields)
        try:
            grant = parse_canonical(grant_bytes or b"")
            grant_hash = self._validate_grant(grant, request, args_hash)
            fields.update({"grant_hash": grant_hash, "grant_id": grant["grant_id"]})
        except (ProtocolError, KeyError, TypeError):
            return self._deny(request_id, "invalid_grant", **fields)
        if grant["grant_id"] in self.used_grants:
            return self._deny(request_id, "replay", **fields)
        # Reserve before receipt preparation.  A failed durable acknowledgement
        # terminates the run; it never enables a retry or legacy fallback.
        self.used_requests.add(request["request_id"])
        self.used_nonces.add(nonce_key)
        self.used_grants.add(grant["grant_id"])
        if is_v2:
            self.used_sequences.add(request["sequence"])
        try:
            _result, result_hash = preview(self.state, request["args"])
        except Exception:
            return self._reply(request_id, "impasse", reason_code="fixture_preview_failed", **fields)
        reply = self._reply(request_id, "accepted", reason_code=None, result_blob_hash=result_hash, **fields)
        if reply.phase != "accepted":
            return reply
        if self._is_killed():
            return self._reply(request_id, "killed", reason_code="run_killed", **fields)
        self.registry[request["method"]](self.state, request["args"])
        return reply

    def _valid_graph_binding(self, binding: object | None, request: dict[str, Any]) -> bool:
        if binding is None or self._graph_binding_verifier is None:
            return False
        try:
            return self._graph_binding_verifier(binding, request) is True
        except Exception:
            return False

    @staticmethod
    def _request_fields(request: dict[str, Any], binding: object | None) -> dict[str, Any]:
        fields = {"request_hash": request["request_hash"], "method": request["method"]}
        if request["schema"] == "ActionRequestV2":
            # The binding is checked before this method is reached; receipt
            # provenance cannot be supplied by an adapter or raw caller.
            fields.update(binding.receipt_fields())
        return fields

    def _validate_request(self, request: dict[str, Any]) -> None:
        common = {"schema", "request_id", "run_id", "sequence", "nonce", "created_at_unix_ms",
                  "expires_at_unix_ms", "method", "args", "input_refs", "input_snapshot_digest",
                  "causal_parent_receipt_hash", "requested_budget", "request_hash"}
        if request.get("schema") == "ActionRequestV1":
            required = common
        elif request.get("schema") == "ActionRequestV2":
            required = common | {"graph_provenance"}
        else:
            raise ProtocolError("request schema")
        if set(request) != required:
            raise ProtocolError("request fields")
        if request["run_id"] != self.manifest.run_id or request["input_snapshot_digest"] != self.manifest.body["input_snapshot_digest"]:
            raise ProtocolError("request binding")
        if (type(request["sequence"]) is not int or type(request["created_at_unix_ms"]) is not int or
                type(request["expires_at_unix_ms"]) is not int or not isinstance(request["request_id"], str) or
                not isinstance(request["nonce"], str)):
            raise ProtocolError("request times")
        if not isinstance(request["input_refs"], list) or any(not isinstance(ref, str) or not ref.startswith("sha256:") for ref in request["input_refs"]):
            raise ProtocolError("input refs")
        if not isinstance(request["requested_budget"], dict) or set(request["requested_budget"]) != {"wall_ms", "cpu_ms", "memory_bytes", "writes", "network_bytes"}:
            raise ProtocolError("budget")
        if any(type(value) is not int or value < 0 for value in request["requested_budget"].values()):
            raise ProtocolError("budget")
        if request["schema"] == "ActionRequestV2":
            provenance = request["graph_provenance"]
            required_provenance = {"proposal_id", "proposal_digest", "causal_parent_receipt_hash"}
            if (not isinstance(provenance, dict) or set(provenance) != required_provenance or
                    provenance["causal_parent_receipt_hash"] != request["causal_parent_receipt_hash"] or
                    provenance["proposal_digest"] not in request["input_refs"]):
                raise ProtocolError("graph provenance")
        if request["request_hash"] != object_hash(request, "request_hash"):
            raise ProtocolError("request hash")

    def _validate_grant(self, grant: dict[str, Any], request: dict[str, Any], args_hash: str | None) -> str:
        required = {"schema", "grant_id", "run_id", "issuer", "key_id", "request_hash", "method",
                    "normalized_args_hash", "input_snapshot_digest", "not_before_unix_ms", "expires_at_unix_ms",
                    "quota", "revocation_generation", "signature"}
        if set(grant) != required or grant["schema"] != "CapabilityGrantV1":
            raise ProtocolError("grant schema")
        key = self.grant_keys.get(grant["key_id"])
        if key is None:
            raise ProtocolError("grant key")
        verify_signature(grant, key)
        if (grant["run_id"] != self.manifest.run_id or grant["request_hash"] != request["request_hash"] or
                grant["method"] != request["method"] or grant["normalized_args_hash"] != args_hash or
                grant["input_snapshot_digest"] != request["input_snapshot_digest"]):
            raise ProtocolError("grant binding")
        if not grant["not_before_unix_ms"] <= self.now_ms() <= grant["expires_at_unix_ms"]:
            raise ProtocolError("grant time")
        if grant["revocation_generation"] != self.manifest.body["revocation_generation"]:
            raise ProtocolError("grant revoked")
        if not isinstance(grant["quota"], dict) or grant["quota"].get("uses") != 1:
            raise ProtocolError("grant quota")
        return object_hash(grant)
