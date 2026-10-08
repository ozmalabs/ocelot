"""Optional HMAC-authenticated audit evidence for trusted provider channels.

The keyring must be provisioned by a trusted service boundary, separately from
the submitted audit rows. HMAC authenticates a configured shared-key holder; it
does not prove that a provider's answer is correct or protect keys exposed to
an untrusted caller in the same process.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping


_SIGNED_LABEL_SCHEMA = "AdequacyProviderSignedLabelV1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _signed_fields(label: dict, request_id: str, probe_id: str, input_sha256: str) -> dict:
    return {"schema": _SIGNED_LABEL_SCHEMA, "source_id": label["source_id"],
            "request_id": request_id, "probe_id": probe_id,
            "input_sha256": input_sha256, "label_id": label["label_id"],
            "expected": label["expected"], "oracle_sha256": label.get("oracle_sha256")}


def sign_label(label: dict, request_id: str, probe_id: str, input_sha256: str,
               provider_key: bytes) -> dict:
    """Return a copy of a label with an HMAC over its request-bound envelope."""
    if not isinstance(provider_key, bytes) or len(provider_key) < 32:
        raise ValueError("provider key must contain at least 32 bytes")
    if not isinstance(label, dict) or not all(isinstance(label.get(k), str) and label[k]
                                              for k in ("source_id", "label_id")):
        raise ValueError("label needs source_id and label_id")
    if "expected" not in label or not request_id or not probe_id or not input_sha256:
        raise ValueError("request, probe, input hash, and expected label are required")
    fields = _signed_fields(label, request_id, probe_id, input_sha256)
    signature = hmac.new(provider_key, _canonical(fields).encode("utf-8"), hashlib.sha256).hexdigest()
    return {**label, "signature_schema": _SIGNED_LABEL_SCHEMA, "signature": signature}


def verify_signed_audit_evidence(request: dict, audit_rows: list[dict], receipt: dict,
                                 trusted_provider_keys: Mapping[str, bytes]) -> dict:
    """Verify request binding, receipt evidence hash, and every provider MAC.

    `trusted_provider_keys` is trust configuration and must not be accepted
    from the same untrusted caller that submits `audit_rows`.
    """
    errors: list[str] = []
    if not isinstance(request, dict) or request.get("schema") != "IndependentAdequacyProbeRequestV1":
        return {"ok": False, "errors": ["invalid request"]}
    request_identity = {key: request.get(key) for key in
                        ("candidate_id", "term_sha256", "acquisition_sha256", "domain_sha256", "seed", "probes")}
    if request.get("request_id") != _digest(request_identity):
        errors.append("request identity mismatch")
    if not isinstance(audit_rows, list) or not isinstance(receipt, dict):
        return {"ok": False, "errors": [*errors, "missing evidence or receipt"]}
    if receipt.get("request_id") != request.get("request_id"):
        errors.append("receipt/request mismatch")
    try:
        evidence_hash = _digest(audit_rows)
    except (TypeError, ValueError):
        evidence_hash = None
        errors.append("non-canonical evidence")
    if evidence_hash != receipt.get("evidence_sha256"):
        errors.append("evidence hash mismatch")

    probes = request.get("probes")
    if not isinstance(probes, list) or not probes:
        errors.append("request has no probes")
        probes = []
    requested = {row.get("probe_id"): row for row in probes
                 if isinstance(row, dict) and isinstance(row.get("probe_id"), str)}
    seen: set[str] = set()
    verified = 0
    for row in audit_rows:
        if not isinstance(row, dict):
            errors.append("malformed audit row"); continue
        probe_id = row.get("probe_id")
        probe = requested.get(probe_id)
        if probe is None or probe_id in seen:
            errors.append("unrequested or duplicate probe row"); continue
        seen.add(probe_id)
        inputs = row.get("inputs")
        try:
            input_hash = _digest(inputs)
        except (TypeError, ValueError):
            errors.append("non-canonical probe input"); continue
        if inputs != probe.get("inputs") or input_hash != probe.get("input_sha256"):
            errors.append("probe descriptor mismatch"); continue
        labels = row.get("labels")
        if not isinstance(labels, list) or not labels:
            errors.append("missing signed labels"); continue
        for label in labels:
            if not isinstance(label, dict) or label.get("signature_schema") != _SIGNED_LABEL_SCHEMA:
                errors.append("unsigned or unsupported label"); continue
            source_id = label.get("source_id")
            key = trusted_provider_keys.get(source_id) if isinstance(source_id, str) else None
            if not isinstance(key, bytes) or len(key) < 32:
                errors.append("unknown trusted provider"); continue
            signature = label.get("signature")
            if not isinstance(signature, str):
                errors.append("missing provider signature"); continue
            try:
                fields = _signed_fields(label, request["request_id"], probe_id, input_hash)
                expected_mac = hmac.new(key, _canonical(fields).encode("utf-8"), hashlib.sha256).hexdigest()
            except (KeyError, TypeError, ValueError):
                errors.append("malformed signed label"); continue
            if not hmac.compare_digest(signature, expected_mac):
                errors.append("provider signature mismatch"); continue
            verified += 1
    if seen != set(requested):
        errors.append("incomplete signed probe set")
    return {"ok": not errors, "errors": errors, "verified_labels": verified,
            "request_id": request.get("request_id"), "evidence_sha256": evidence_hash}


def teach_write_shape_from_example_authenticated(agent, example_source: str, *,
        request: dict, audit_rows: list[dict], receipt: dict,
        trusted_provider_keys: Mapping[str, bytes],
        probe_selection_context: dict | None = None,
        **teach_kwargs) -> dict:
    """Authenticate supplied evidence before invoking the existing teach gate.

    Key configuration is deliberately an explicit service-side argument. This
    wrapper is an opt-in path; legacy callers remain governed by the existing
    receipt-only contract.
    """
    verification = verify_signed_audit_evidence(request, audit_rows, receipt, trusted_provider_keys)
    if not verification["ok"]:
        return {"ok": False, "reason": "provider-authenticated adequacy evidence required",
                "provider_auth": verification}
    from domains.code_write_growth import teach_write_shape_from_example
    result = teach_write_shape_from_example(agent, example_source,
        adequacy_receipt=receipt, require_adequacy_receipt=True,
        provider_evidence={"request": request, "audit_rows": audit_rows,
                           "receipt": receipt,
                           "probe_selection_context": probe_selection_context},
        **teach_kwargs)
    return {**result, "provider_auth": verification}
