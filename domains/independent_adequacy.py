"""Provenance-bound requests and adjudication for independent model audits.

This module never produces oracle labels. Callers nominate an admissible input
domain, route the returned request to a label provider, and submit the labeled
evidence for deterministic residual adjudication.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable


_REQUEST_SCHEMA = "IndependentAdequacyProbeRequestV1"
_RECEIPT_SCHEMA = "IndependentAdequacyReceiptV1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def candidate_id_for_write_shape(source: str, name: str, args: list,
                                 term: dict, request_text: str | None = None,
                                 lesson_source: str | None = None) -> str:
    """Stable identity for one write-shape candidate and its provenance."""
    if not isinstance(source, str) or not isinstance(name, str) or not isinstance(args, list) or not isinstance(term, dict):
        raise ValueError("source, name, args, and Term are required")
    return _digest({"kind": "code_write_shape", "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                    "name": name, "args": args, "term_sha256": _digest(term),
                    "request_text": request_text, "lesson_source": lesson_source})


def verify_accepted_receipt(receipt: dict, candidate_id: str, term: dict) -> bool:
    """Verify receipt integrity and binding before a candidate is adopted.

    This checks consistency, not the identity or honesty of the label provider.
    """
    if not isinstance(receipt, dict) or receipt.get("schema") != _RECEIPT_SCHEMA:
        return False
    if receipt.get("status") != "accepted" or receipt.get("candidate_id") != candidate_id:
        return False
    if not isinstance(term, dict) or receipt.get("term_sha256") != _digest(term):
        return False
    core = {key: receipt.get(key) for key in
            ("request_id", "candidate_id", "term_sha256", "status", "evidence_sha256", "residuals", "invalid_reasons")}
    try:
        return receipt.get("receipt_sha256") == _digest(core)
    except (TypeError, ValueError):
        return False


def propose_audit_request(
    candidate_id: str,
    term: dict,
    acquisition_rows: list[dict],
    admissible_inputs: list[dict],
    *,
    acquisition_source_ids: list[str],
    count: int = 1,
    seed: str = "independent-adequacy-v1",
) -> dict:
    """Choose fresh descriptors and return a hash-bound request for labels.

    Selection is deterministic and target-blind: a seeded hash ordering spreads
    requests across the caller's admissible finite domain. It is a sampling
    policy, not a guarantee of semantic identifiability or model adequacy.
    """
    if not _valid_id(candidate_id) or not isinstance(term, dict):
        raise ValueError("candidate_id and Term are required")
    if not isinstance(acquisition_rows, list) or not isinstance(admissible_inputs, list):
        raise TypeError("acquisition_rows and admissible_inputs must be lists")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer")
    if not _valid_id(seed):
        raise ValueError("seed must be a non-empty string")
    if not isinstance(acquisition_source_ids, list) or any(not _valid_id(item) for item in acquisition_source_ids):
        raise ValueError("acquisition_source_ids must contain non-empty identifiers")

    acquired: dict[str, dict] = {}
    for row in acquisition_rows:
        if not isinstance(row, dict) or not isinstance(row.get("inputs"), dict):
            raise ValueError("each acquisition row must contain an inputs mapping")
        token = _digest(row["inputs"])
        acquired[token] = row["inputs"]

    candidates: dict[str, dict] = {}
    for inputs in admissible_inputs:
        if not isinstance(inputs, dict) or not inputs:
            raise ValueError("admissible inputs must be non-empty mappings")
        token = _digest(inputs)
        if token in candidates:
            raise ValueError("admissible input descriptors must be unique")
        candidates[token] = inputs

    fresh = [(token, inputs) for token, inputs in candidates.items() if token not in acquired]
    fresh.sort(key=lambda pair: hashlib.sha256(f"{seed}:{pair[0]}".encode()).hexdigest())
    selected = fresh[:count]
    if len(selected) < count:
        raise ValueError("admissible input domain has too few fresh descriptors")

    term_hash = _digest(term)
    acquisition_hash = _digest({"rows": acquisition_rows,
                                "source_ids": sorted(set(acquisition_source_ids))})
    domain_hash = _digest(admissible_inputs)
    probes = [{"probe_id": f"probe-{index + 1}", "inputs": inputs,
               "input_sha256": token}
              for index, (token, inputs) in enumerate(selected)]
    identity = {"candidate_id": candidate_id, "term_sha256": term_hash,
                "acquisition_sha256": acquisition_hash, "domain_sha256": domain_hash,
                "seed": seed, "probes": probes}
    return {"schema": _REQUEST_SCHEMA, "request_id": _digest(identity),
            **identity, "probes": probes, "status": "requested"}


def adjudicate_audit_receipt(
    request: dict,
    candidate_id: str,
    term: dict,
    audit_rows: list[dict],
    evaluate: Callable[[dict, dict], Any],
    *,
    acquisition_source_ids: list[str],
) -> dict:
    """Bind labeled independent evidence to a request and report residuals.

    Each audit row has `probe_id`, `inputs`, and one or more labels of the form
    `{source_id, label_id, expected}`. Conflicting independent labels produce
    `ambiguous`; missing requested probes produce `incomplete`; contaminated
    provenance produces `invalid`; a residual produces `rejected`.
    """
    if not isinstance(request, dict) or request.get("schema") != _REQUEST_SCHEMA:
        raise ValueError("invalid audit request")
    if request.get("status") != "requested" or not _valid_id(candidate_id):
        raise ValueError("request is not pending or candidate id is invalid")
    identity = {key: request.get(key) for key in
                ("candidate_id", "term_sha256", "acquisition_sha256", "domain_sha256", "seed", "probes")}
    if request.get("request_id") != _digest(identity):
        raise ValueError("request contents do not match request_id")
    if not isinstance(term, dict) or _digest(term) != request.get("term_sha256"):
        raise ValueError("candidate Term does not match request")
    if candidate_id != request.get("candidate_id"):
        raise ValueError("candidate id does not match request")
    if not isinstance(audit_rows, list):
        raise TypeError("audit_rows must be a list")
    if not isinstance(acquisition_source_ids, list) or any(not _valid_id(item) for item in acquisition_source_ids):
        raise ValueError("acquisition_source_ids must contain non-empty identifiers")
    acquisition_source_ids = set(acquisition_source_ids)
    requested = {probe["probe_id"]: probe for probe in request.get("probes", [])}
    seen: set[str] = set()
    normalized: dict[str, dict] = {}
    invalid_reasons: list[str] = []

    for row in audit_rows:
        if not isinstance(row, dict) or not _valid_id(row.get("probe_id")):
            invalid_reasons.append("malformed audit row")
            continue
        probe_id = row["probe_id"]
        if probe_id in seen:
            invalid_reasons.append(f"duplicate probe row: {probe_id}")
            continue
        seen.add(probe_id)
        probe = requested.get(probe_id)
        if probe is None or row.get("inputs") != probe["inputs"]:
            invalid_reasons.append(f"unrequested or altered descriptor: {probe_id}")
            continue
        if _digest(row["inputs"]) != probe["input_sha256"]:
            invalid_reasons.append(f"descriptor hash mismatch: {probe_id}")
            continue
        labels = row.get("labels")
        if not isinstance(labels, list) or not labels:
            invalid_reasons.append(f"missing provenance-bound label: {probe_id}")
            continue
        label_ids: set[tuple[str, str]] = set()
        for label in labels:
            if not isinstance(label, dict) or not _valid_id(label.get("source_id")) or not _valid_id(label.get("label_id")) or "expected" not in label:
                invalid_reasons.append(f"malformed label provenance: {probe_id}")
                continue
            identity = (label["source_id"], label["label_id"])
            if identity in label_ids:
                invalid_reasons.append(f"duplicate label provenance: {probe_id}")
            label_ids.add(identity)
            if label["source_id"] in acquisition_source_ids:
                invalid_reasons.append(f"audit label source reused from acquisition: {probe_id}")
            try:
                _canonical(label["expected"])
            except (TypeError, ValueError):
                invalid_reasons.append(f"non-canonical label value: {probe_id}")
        normalized[probe_id] = {"inputs": row["inputs"], "labels": labels}

    if invalid_reasons:
        status = "invalid"
    elif set(normalized) != set(requested):
        status = "incomplete"
    else:
        status = "accepted"

    residuals = []
    if status not in ("invalid", "incomplete"):
        for probe_id, probe in requested.items():
            row = normalized[probe_id]
            try:
                prediction = evaluate(term, row["inputs"])
            except Exception as exc:
                residuals.append({"probe_id": probe_id, "input_sha256": probe["input_sha256"],
                                  "error": type(exc).__name__, "labels": row["labels"]})
                continue
            try:
                _canonical(prediction)
            except (TypeError, ValueError):
                residuals.append({"probe_id": probe_id, "input_sha256": probe["input_sha256"],
                                  "error": "NonCanonicalPrediction", "labels": row["labels"]})
                continue
            values = [label["expected"] for label in row["labels"]]
            try:
                distinct = {_canonical(value) for value in values}
            except (TypeError, ValueError):
                distinct = set()
            if len(distinct) != 1:
                residuals.append({"probe_id": probe_id, "input_sha256": probe["input_sha256"],
                                  "prediction": prediction, "labels": row["labels"], "kind": "ambiguous_label"})
            elif prediction != values[0]:
                residuals.append({"probe_id": probe_id, "input_sha256": probe["input_sha256"],
                                  "prediction": prediction, "labels": row["labels"], "kind": "prediction_residual"})
        if any(row.get("kind") == "ambiguous_label" for row in residuals):
            status = "ambiguous"
        elif residuals:
            status = "rejected"
        else:
            status = "accepted"

    try:
        evidence_hash = _digest(audit_rows)
    except (TypeError, ValueError):
        evidence_hash = None
    receipt_core = {"request_id": request["request_id"], "candidate_id": candidate_id,
                    "term_sha256": request["term_sha256"], "status": status,
                    "evidence_sha256": evidence_hash, "residuals": residuals,
                    "invalid_reasons": invalid_reasons}
    return {"schema": _RECEIPT_SCHEMA, **receipt_core,
            "receipt_sha256": _digest(receipt_core)}
