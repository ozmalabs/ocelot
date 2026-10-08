"""Fail-closed, digest-only RFC 3161 timing evidence.

This module deliberately does not implement ``P5R0IndependentTimingAttestationV2``
or ``P5R0IndependentTimingAttestationV3``. An RFC 3161 token proves that a TSA
signed a digest at ``genTime``; it does not provide the evaluator's Ed25519
ledger signature or its independent V2/V3 chain. Consumers must keep
``bridge_required`` true until a separately operated bridge produces and
validates a V3 record.

The default verifier uses the system OpenSSL CLI.  Tests may inject a verifier,
but production construction requires both a pinned CA bundle and a pinned TSA
signer certificate fingerprint.  No raw request, response, or token is emitted
in an evidence record; only their SHA-256 digests are retained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .canonical import b64decode, b64encode, digest


RFC3161_ENDPOINT = "http://timestamp.digicert.com"
FREETSA_ENDPOINT = "https://freetsa.org/tsr"
FREETSA_POLICY_OID = "1.2.3.4.1"
FREETSA_CA_PEM_SHA256 = "sha256:2151b61137ffa86bf664691ba67e7da0b19f98c758e3d228d5d8ebf27e044438"
FREETSA_TSA_CERTIFICATE_SHA256 = "sha256:32e841a95cc1164101ffde41298ef2fc75c1c4372ef095e88a6bbd47dfb191fc"
RFC3161_ENDPOINTS = frozenset({RFC3161_ENDPOINT, FREETSA_ENDPOINT})
SHA256_OID = "2.16.840.1.101.3.4.2.1"
TST_INFO_OID = "1.2.840.113549.1.9.16.1.4"
DEFAULT_POLICY_OID = "2.16.840.1.114412.7.1"
MAX_TIMESTAMP_QUERY_BYTES = 4096
MAX_TIMESTAMP_RESPONSE_BYTES = 256 * 1024
RFC3161_PROOF_SCHEMA = "P5R0RFC3161ProofV1"
MAX_RFC3161_PROOF_BYTES = MAX_TIMESTAMP_RESPONSE_BYTES
MAX_RFC3161_PROOF_B64_BYTES = 4 * ((MAX_RFC3161_PROOF_BYTES + 2) // 3)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class RFC3161EvidenceError(ValueError):
    """An RFC 3161 response or configuration failed closed."""


@dataclass(frozen=True)
class RFC3161Config:
    """Reviewed, immutable TSA policy and trust configuration.

    ``tsa_ca_pem`` is the complete pinned trust-anchor file.  Its digest is
    pinned separately so replacing the PEM file cannot silently change trust.
    ``tsa_certificate_sha256`` pins the TSA signer certificate extracted by
    OpenSSL from the CMS response.  The endpoint is intentionally fixed to
    the documented DigiCert endpoint and cannot be caller-selected.
    """

    endpoint: str = RFC3161_ENDPOINT
    tsa_ca_pem: bytes = b""
    tsa_ca_pem_sha256: str = ""
    tsa_certificate_sha256: str = ""
    policy_oid: str = DEFAULT_POLICY_OID
    timeout_seconds: float = 5.0
    max_response_bytes: int = MAX_TIMESTAMP_RESPONSE_BYTES
    max_gen_time_age_seconds: int = 86_400
    max_gen_time_future_seconds: int = 300
    openssl_path: str = "openssl"

    def __post_init__(self) -> None:
        if self.endpoint not in RFC3161_ENDPOINTS:
            raise RFC3161EvidenceError("RFC3161 endpoint is not allowlisted")
        if not isinstance(self.tsa_ca_pem, (bytes, bytearray)) or not self.tsa_ca_pem:
            raise RFC3161EvidenceError("RFC3161 TSA CA pin is required")
        _require_digest(self.tsa_ca_pem_sha256, "TSA CA pin")
        if digest(bytes(self.tsa_ca_pem)) != self.tsa_ca_pem_sha256:
            raise RFC3161EvidenceError("RFC3161 TSA CA pin mismatch")
        _require_digest(self.tsa_certificate_sha256, "TSA certificate pin")
        if not isinstance(self.policy_oid, str) or not _valid_oid(self.policy_oid):
            raise RFC3161EvidenceError("RFC3161 policy OID")
        if not isinstance(self.timeout_seconds, (int, float)) or not 0 < self.timeout_seconds <= 10:
            raise RFC3161EvidenceError("RFC3161 timeout")
        if type(self.max_response_bytes) is not int or not 0 < self.max_response_bytes <= MAX_TIMESTAMP_RESPONSE_BYTES:
            raise RFC3161EvidenceError("RFC3161 response bound")
        if type(self.max_gen_time_age_seconds) is not int or self.max_gen_time_age_seconds <= 0:
            raise RFC3161EvidenceError("RFC3161 gen_time age bound")
        if type(self.max_gen_time_future_seconds) is not int or self.max_gen_time_future_seconds < 0:
            raise RFC3161EvidenceError("RFC3161 gen_time future bound")
        if not isinstance(self.openssl_path, str) or not self.openssl_path:
            raise RFC3161EvidenceError("OpenSSL path")


@dataclass(frozen=True)
class RFC3161RecordedProof:
    """Verified digest-only evidence and its bounded internal proof envelope."""

    evidence: dict[str, Any]
    proof: dict[str, Any]


@dataclass(frozen=True)
class _DER:
    tag: int
    value: bytes
    encoded: bytes


def _require_digest(value: Any, name: str) -> None:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise RFC3161EvidenceError(name)


def _valid_oid(value: str) -> bool:
    try:
        parts = value.split(".")
        if len(parts) < 2 or any(not part.isdigit() or (len(part) > 1 and part[0] == "0") for part in parts):
            return False
        first, second = int(parts[0]), int(parts[1])
        return (first in (0, 1) and second < 40) or first == 2
    except Exception:
        return False


def _der_length(size: int) -> bytes:
    if size < 0:
        raise RFC3161EvidenceError("DER length")
    if size < 128:
        return bytes([size])
    raw = size.to_bytes((size.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def _der(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _der_length(len(value)) + value


def _der_integer(value: int) -> bytes:
    if value < 0:
        raise RFC3161EvidenceError("DER integer")
    raw = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    if raw[0] & 0x80:
        raw = b"\x00" + raw
    return _der(0x02, raw)


def _der_oid(value: str) -> bytes:
    if not _valid_oid(value):
        raise RFC3161EvidenceError("DER OID")
    parts = [int(part) for part in value.split(".")]
    raw = bytearray()
    first_number = 40 * parts[0] + parts[1]
    encoded = [first_number & 0x7F]
    first_number >>= 7
    while first_number:
        encoded.append(0x80 | (first_number & 0x7F))
        first_number >>= 7
    raw.extend(reversed(encoded))
    for number in parts[2:]:
        encoded = [number & 0x7F]
        number >>= 7
        while number:
            encoded.append(0x80 | (number & 0x7F))
            number >>= 7
        raw.extend(reversed(encoded))
    return _der(0x06, bytes(raw))


def build_timestamp_query(payload_digest: str) -> bytes:
    """Build a DER RFC 3161 request whose only message is ``payload_digest``.

    The evaluator has no raw payload at this boundary.  The already committed
    SHA-256 digest is therefore used directly as the RFC 3161 MessageImprint;
    the payload itself is never sent to the TSA.  The request is deterministic,
    contains no caller timestamp, and asks the TSA to include its certificate.
    """
    _require_digest(payload_digest, "payload digest")
    imprint = bytes.fromhex(payload_digest[7:])
    algorithm = _der(0x30, _der_oid(SHA256_OID) + _der(0x05, b""))
    message_imprint = _der(0x30, algorithm + _der(0x04, imprint))
    request = _der(0x30, _der_integer(1) + message_imprint + _der(0x01, b"\xff"))
    if len(request) > MAX_TIMESTAMP_QUERY_BYTES:
        raise RFC3161EvidenceError("RFC3161 query too large")
    return request


def _read_der(raw: bytes, offset: int = 0) -> tuple[_DER, int]:
    if offset >= len(raw):
        raise RFC3161EvidenceError("RFC3161 DER truncated")
    start = offset
    tag = raw[offset]
    offset += 1
    if offset >= len(raw):
        raise RFC3161EvidenceError("RFC3161 DER length")
    first = raw[offset]
    offset += 1
    if first & 0x80:
        count = first & 0x7F
        if count == 0 or count > 4 or offset + count > len(raw):
            raise RFC3161EvidenceError("RFC3161 DER length")
        if raw[offset] == 0:
            raise RFC3161EvidenceError("RFC3161 non-minimal DER")
        size = int.from_bytes(raw[offset:offset + count], "big")
        offset += count
        if size < 128:
            raise RFC3161EvidenceError("RFC3161 non-minimal DER")
    else:
        size = first
    end = offset + size
    if end > len(raw):
        raise RFC3161EvidenceError("RFC3161 DER truncated")
    return _DER(tag, raw[offset:end], raw[start:end]), end


def _only_der(raw: bytes) -> _DER:
    node, end = _read_der(raw)
    if end != len(raw):
        raise RFC3161EvidenceError("RFC3161 trailing response data")
    return node


def _children(node: _DER) -> list[_DER]:
    if not node.tag & 0x20:
        raise RFC3161EvidenceError("RFC3161 DER constructed value")
    result: list[_DER] = []
    offset = 0
    while offset < len(node.value):
        child, offset = _read_der(node.value, offset)
        result.append(child)
    return result


def _integer(node: _DER, name: str) -> int:
    if node.tag != 0x02 or not node.value or node.value[0] & 0x80 or (len(node.value) > 1 and node.value[0] == 0 and not node.value[1] & 0x80):
        raise RFC3161EvidenceError(name)
    return int.from_bytes(node.value, "big")


def _oid(node: _DER, name: str) -> str:
    if node.tag != 0x06 or not node.value:
        raise RFC3161EvidenceError(name)
    first = node.value[0]
    first_a, first_b = (first // 40, first % 40) if first < 80 else (2, first - 80)
    parts = [first_a, first_b]
    number = 0
    for byte in node.value[1:]:
        number = (number << 7) | (byte & 0x7F)
        if not byte & 0x80:
            parts.append(number)
            number = 0
    if number or first_a > 2:
        raise RFC3161EvidenceError(name)
    return ".".join(str(part) for part in parts)


def _generalized_time(node: _DER) -> tuple[str, datetime]:
    if node.tag != 0x18:
        raise RFC3161EvidenceError("RFC3161 gen_time")
    try:
        text = node.value.decode("ascii")
        if len(text) > 24 or not text.endswith("Z") or not re.fullmatch(r"\d{14}(?:\.\d{1,6})?Z", text):
            raise ValueError
        base, _, fraction = text[:-1].partition(".")
        parsed = datetime.strptime(base, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        if fraction:
            parsed = parsed.replace(microsecond=int((fraction + "000000")[:6]))
        return text, parsed
    except Exception as exc:
        raise RFC3161EvidenceError("RFC3161 gen_time") from exc


def _parse_status(status: _DER) -> int:
    children = _children(status)
    if not 1 <= len(children) <= 3 or children[0].tag != 0x02:
        raise RFC3161EvidenceError("RFC3161 status")
    code = _integer(children[0], "RFC3161 status")
    if code != 0:
        raise RFC3161EvidenceError("RFC3161 status is not granted")
    if len(children) >= 2:
        if children[1].tag != 0x30 or any(item.tag != 0x0C for item in _children(children[1])):
            raise RFC3161EvidenceError("RFC3161 status string")
    if len(children) == 3:
        if children[2].tag != 0x03 or not children[2].value or children[2].value[0] > 7 or any(children[2].value[1:]):
            raise RFC3161EvidenceError("RFC3161 failure info")
        raise RFC3161EvidenceError("RFC3161 granted failure info")
    return code


def _parse_token(token: bytes, expected_imprint: bytes, expected_policy: str) -> tuple[str, str, datetime, bytes, bytes]:
    content_info = _only_der(token)
    content = _children(content_info)
    if content_info.tag != 0x30 or len(content) != 2 or _oid(content[0], "CMS content type") != "1.2.840.113549.1.7.2" or content[1].tag != 0xA0:
        raise RFC3161EvidenceError("RFC3161 CMS token")
    signed_data_parts = _children(content[1])
    if len(signed_data_parts) != 1 or signed_data_parts[0].tag != 0x30:
        raise RFC3161EvidenceError("RFC3161 SignedData")
    signed_data = _children(signed_data_parts[0])
    if len(signed_data) < 4 or _integer(signed_data[0], "CMS version") not in (1, 3):
        raise RFC3161EvidenceError("RFC3161 SignedData version")
    encap = signed_data[2]
    encap_parts = _children(encap)
    if encap.tag != 0x30 or len(encap_parts) != 2 or _oid(encap_parts[0], "TSTInfo content type") != TST_INFO_OID or encap_parts[1].tag != 0xA0:
        raise RFC3161EvidenceError("RFC3161 encapsulated content")
    econtent = _children(encap_parts[1])
    if len(econtent) != 1 or econtent[0].tag != 0x04:
        raise RFC3161EvidenceError("RFC3161 TSTInfo content")
    tst_info = _children(_only_der(econtent[0].value))
    if len(tst_info) < 5 or _integer(tst_info[0], "TSTInfo version") != 1:
        raise RFC3161EvidenceError("RFC3161 TSTInfo")
    policy = _oid(tst_info[1], "RFC3161 policy")
    if policy != expected_policy:
        raise RFC3161EvidenceError("RFC3161 policy mismatch")
    imprint = _children(tst_info[2])
    if len(imprint) != 2 or imprint[0].tag != 0x30 or imprint[1].tag != 0x04:
        raise RFC3161EvidenceError("RFC3161 message imprint")
    algorithm = _children(imprint[0])
    if len(algorithm) not in (1, 2) or _oid(algorithm[0], "RFC3161 hash algorithm") != SHA256_OID:
        raise RFC3161EvidenceError("RFC3161 hash algorithm")
    if (len(algorithm) == 2 and (algorithm[1].tag != 0x05 or algorithm[1].value != b"")) or len(imprint[1].value) != 32:
        raise RFC3161EvidenceError("RFC3161 hash algorithm parameters")
    if imprint[1].value != expected_imprint:
        raise RFC3161EvidenceError("RFC3161 message imprint mismatch")
    if _integer(tst_info[3], "RFC3161 serial") < 1:
        raise RFC3161EvidenceError("RFC3161 serial")
    gen_text, gen_time = _generalized_time(tst_info[4])
    for optional in tst_info[5:]:
        if optional.tag not in (0x30, 0x01, 0xA0, 0xA1):
            raise RFC3161EvidenceError("RFC3161 TSTInfo extension")
    return policy, gen_text, gen_time, econtent[0].value, token


def parse_timestamp_response(response: bytes, *, expected_imprint: bytes, expected_policy: str, now: float, max_age_seconds: int, max_future_seconds: int) -> dict[str, Any]:
    """Parse strict status/policy/imprint/gen_time metadata from a response."""
    if not isinstance(response, bytes) or not response or len(response) > MAX_TIMESTAMP_RESPONSE_BYTES:
        raise RFC3161EvidenceError("RFC3161 response bound")
    root = _only_der(response)
    parts = _children(root)
    if root.tag != 0x30 or len(parts) != 2 or parts[0].tag != 0x30 or parts[1].tag != 0x30:
        raise RFC3161EvidenceError("RFC3161 response schema")
    _parse_status(parts[0])
    policy, gen_text, gen_time, token_content, token_bytes = _parse_token(parts[1].encoded, expected_imprint, expected_policy)
    current = datetime.fromtimestamp(now, timezone.utc)
    age = (current - gen_time).total_seconds()
    if age > max_age_seconds or age < -max_future_seconds:
        raise RFC3161EvidenceError("RFC3161 gen_time outside bound")
    return {"policy_oid": policy, "status": "granted", "gen_time": gen_text, "token_content": token_content, "token_bytes": token_bytes}


def validate_rfc3161_proof(value: Any) -> bytes:
    """Decode the bounded canonical proof carried only inside the bridge envelope."""
    if not isinstance(value, dict) or set(value) != {"schema", "response_b64"} or value.get("schema") != RFC3161_PROOF_SCHEMA:
        raise RFC3161EvidenceError("RFC3161 proof schema")
    encoded = value.get("response_b64")
    if not isinstance(encoded, str) or not encoded or len(encoded) > MAX_RFC3161_PROOF_B64_BYTES:
        raise RFC3161EvidenceError("RFC3161 proof bound")
    try:
        response = b64decode(encoded)
    except Exception as exc:
        raise RFC3161EvidenceError("RFC3161 proof encoding") from exc
    if not response or len(response) > MAX_RFC3161_PROOF_BYTES or b64encode(response) != encoded:
        raise RFC3161EvidenceError("RFC3161 proof encoding")
    return response


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        raise RFC3161EvidenceError("RFC3161 redirects are forbidden")


def _openssl_verify(token: bytes, config: RFC3161Config) -> str:
    """Verify CMS signature/chain and return the pinned signer fingerprint."""
    try:
        with tempfile.TemporaryDirectory(prefix="p5-rfc3161-") as directory:
            token_path = f"{directory}/response.tsr"
            ca_path = f"{directory}/tsa-ca.pem"
            signer_path = f"{directory}/signer.pem"
            content_path = f"{directory}/content.der"
            with open(token_path, "wb") as handle:
                handle.write(token)
            with open(ca_path, "wb") as handle:
                handle.write(bytes(config.tsa_ca_pem))
            result = subprocess.run(
                [config.openssl_path, "cms", "-verify", "-inform", "DER", "-in", token_path,
                 "-CAfile", ca_path, "-purpose", "any", "-signer", signer_path,
                 "-out", content_path, "-binary"],
                check=False, capture_output=True, timeout=config.timeout_seconds,
            )
            if result.returncode != 0:
                raise RFC3161EvidenceError("RFC3161 CMS verification failed")
            purpose_result = subprocess.run(
                [config.openssl_path, "x509", "-in", signer_path, "-purpose", "-noout"],
                check=False, capture_output=True, timeout=config.timeout_seconds,
            )
            purpose = purpose_result.stdout.decode("ascii", "ignore")
            if purpose_result.returncode != 0 or not re.search(r"Time Stamp signing\s*:\s*Yes", purpose):
                raise RFC3161EvidenceError("RFC3161 TSA certificate purpose")
            cert_result = subprocess.run(
                [config.openssl_path, "x509", "-in", signer_path, "-outform", "DER"],
                check=False, capture_output=True, timeout=config.timeout_seconds,
            )
            if cert_result.returncode != 0 or not cert_result.stdout:
                raise RFC3161EvidenceError("RFC3161 TSA certificate unavailable")
            fingerprint = "sha256:" + hashlib.sha256(cert_result.stdout).hexdigest()
            if fingerprint != config.tsa_certificate_sha256:
                raise RFC3161EvidenceError("RFC3161 TSA certificate pin mismatch")
            return fingerprint
    except RFC3161EvidenceError:
        raise
    except Exception as exc:
        raise RFC3161EvidenceError("RFC3161 CMS verification failed") from exc


def validate_rfc3161_evidence(value: dict[str, Any], *, run_id: str, task_id: str, event: str, payload_digest: str, previous_digest: str | None, last_sequence: int) -> dict[str, Any]:
    fields = {"schema", "run_id", "task_id", "event", "sequence", "ledger_id", "previous_digest", "payload_digest", "message_imprint", "status", "policy_oid", "gen_time", "token_digest", "response_digest", "tsa_certificate_sha256", "bridge_required", "bridge_target"}
    if not isinstance(value, dict) or set(value) != fields or value.get("schema") != "P5R0RFC3161TimingEvidenceV1":
        raise RFC3161EvidenceError("RFC3161 evidence schema")
    if value.get("run_id") != run_id or value.get("task_id") != task_id or value.get("event") != event:
        raise RFC3161EvidenceError("RFC3161 evidence binding")
    if event not in {"task_issued", "result_received", "task_completed"} or type(value.get("sequence")) is not int or value["sequence"] != last_sequence + 1:
        raise RFC3161EvidenceError("RFC3161 evidence sequence")
    if value.get("previous_digest") != previous_digest:
        raise RFC3161EvidenceError("RFC3161 evidence chain")
    for key in ("payload_digest", "message_imprint", "token_digest", "response_digest", "tsa_certificate_sha256"):
        _require_digest(value.get(key), key)
    if value["payload_digest"] != payload_digest or value["message_imprint"] != payload_digest:
        raise RFC3161EvidenceError("RFC3161 evidence imprint binding")
    if value.get("status") != "granted" or not _valid_oid(value.get("policy_oid", "")) or not isinstance(value.get("gen_time"), str):
        raise RFC3161EvidenceError("RFC3161 evidence metadata")
    if value.get("bridge_required") is not True or value.get("bridge_target") != "P5R0IndependentTimingAttestationV2":
        raise RFC3161EvidenceError("RFC3161 V2 bridge requirement")
    return value


class RFC3161TimingEvidenceAdapter:
    """Fetch and verify digest-only RFC3161 evidence.

    ``independent`` is intentionally false: this adapter produces evidence,
    not the existing Ed25519 V2 attestation.  Consequently passing it to the
    current ``EvaluatorService`` cannot set ``timing_certified``.  A remote
    Ed25519 timing bridge remains required.
    """

    independent = False
    bridge_required = True

    def __init__(self, config: RFC3161Config, *, opener: Any | None = None, verifier: Callable[[bytes, RFC3161Config], str] | None = None, clock: Callable[[], float] | None = None):
        self.config = config
        self._opener = opener or build_opener(_NoRedirect())
        self._verifier = verifier or _openssl_verify
        self._clock = clock or time.time
        self._chains: dict[str, tuple[int, str | None]] = {}
        self._lock = threading.Lock()

    def _post(self, query: bytes) -> bytes:
        request = Request(self.config.endpoint, data=query, method="POST", headers={"Content-Type": "application/timestamp-query", "Accept": "application/timestamp-reply"})
        try:
            response = self._opener.open(request, timeout=self.config.timeout_seconds)
            status = getattr(response, "status", 200)
            if status != 200:
                raise RFC3161EvidenceError("RFC3161 HTTP status")
            geturl = getattr(response, "geturl", None)
            if callable(geturl) and geturl() != self.config.endpoint:
                raise RFC3161EvidenceError("RFC3161 redirect")
            content_type = getattr(response, "headers", {}).get("Content-Type") if getattr(response, "headers", None) is not None else None
            if content_type is not None and not content_type.lower().split(";", 1)[0].strip() == "application/timestamp-reply":
                raise RFC3161EvidenceError("RFC3161 content type")
            raw = response.read(self.config.max_response_bytes + 1)
            if not isinstance(raw, bytes) or len(raw) > self.config.max_response_bytes:
                raise RFC3161EvidenceError("RFC3161 response too large")
            return raw
        except RFC3161EvidenceError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise RFC3161EvidenceError("RFC3161 request failed") from exc
        except Exception as exc:
            raise RFC3161EvidenceError("RFC3161 request failed") from exc

    def _verify_response(self, response: bytes, payload_digest: str) -> tuple[dict[str, Any], str]:
        if not isinstance(response, bytes) or not response or len(response) > self.config.max_response_bytes:
            raise RFC3161EvidenceError("RFC3161 response bound")
        parsed = parse_timestamp_response(
            response,
            expected_imprint=bytes.fromhex(payload_digest[7:]),
            expected_policy=self.config.policy_oid,
            now=self._clock(),
            max_age_seconds=self.config.max_gen_time_age_seconds,
            max_future_seconds=self.config.max_gen_time_future_seconds,
        )
        try:
            signer_fingerprint = self._verifier(parsed["token_bytes"], self.config)
        except RFC3161EvidenceError:
            raise
        except Exception as exc:
            raise RFC3161EvidenceError("RFC3161 CMS verification failed") from exc
        if signer_fingerprint != self.config.tsa_certificate_sha256:
            raise RFC3161EvidenceError("RFC3161 TSA certificate pin mismatch")
        return parsed, signer_fingerprint

    @staticmethod
    def _evidence(
        *, run_id: str, task_id: str, event: str, payload_digest: str,
        sequence: int, previous: str | None, response: bytes,
        parsed: dict[str, Any], signer_fingerprint: str,
    ) -> dict[str, Any]:
        value = {
            "schema": "P5R0RFC3161TimingEvidenceV1", "run_id": run_id, "task_id": task_id, "event": event,
            "sequence": sequence, "ledger_id": "digicert-rfc3161", "previous_digest": previous,
            "payload_digest": payload_digest, "message_imprint": payload_digest, "status": parsed["status"],
            "policy_oid": parsed["policy_oid"], "gen_time": parsed["gen_time"], "token_digest": digest(parsed["token_bytes"]),
            "response_digest": digest(response), "tsa_certificate_sha256": signer_fingerprint,
            "bridge_required": True, "bridge_target": "P5R0IndependentTimingAttestationV2",
        }
        validate_rfc3161_evidence(
            value, run_id=run_id, task_id=task_id, event=event,
            payload_digest=payload_digest, previous_digest=previous,
            last_sequence=sequence - 1,
        )
        return value

    def verify_proof(
        self, proof: dict[str, Any], *, run_id: str, task_id: str, event: str,
        payload_digest: str, sequence: int, previous_digest: str | None,
    ) -> dict[str, Any]:
        """Verify bridge proof using this pinned TSA configuration without network access."""
        if not all(isinstance(value, str) and value for value in (run_id, task_id, event)) or event not in {"task_issued", "result_received", "task_completed"}:
            raise RFC3161EvidenceError("RFC3161 event metadata")
        _require_digest(payload_digest, "payload digest")
        if type(sequence) is not int or sequence < 1:
            raise RFC3161EvidenceError("RFC3161 evidence sequence")
        response = validate_rfc3161_proof(proof)
        parsed, signer_fingerprint = self._verify_response(response, payload_digest)
        return self._evidence(
            run_id=run_id, task_id=task_id, event=event, payload_digest=payload_digest,
            sequence=sequence, previous=previous_digest, response=response,
            parsed=parsed, signer_fingerprint=signer_fingerprint,
        )

    def record_with_proof(
        self, *, run_id: str, task_id: str, event: str, payload_digest: str,
        sequence: int | None = None, previous_digest: str | None = None,
    ) -> RFC3161RecordedProof:
        """Record verified evidence and retain the exact RFC response proof.

        The bridge service supplies the durable ledger position in production;
        direct diagnostic callers retain the historical process-local chain.
        """
        if not all(isinstance(value, str) and value for value in (run_id, task_id, event)) or event not in {"task_issued", "result_received", "task_completed"}:
            raise RFC3161EvidenceError("RFC3161 event metadata")
        _require_digest(payload_digest, "payload digest")
        with self._lock:
            last_sequence, local_previous = self._chains.get(run_id, (0, None))
            evidence_sequence = last_sequence + 1 if sequence is None else sequence
            evidence_previous = local_previous if sequence is None and previous_digest is None else previous_digest
            if type(evidence_sequence) is not int or evidence_sequence < 1:
                raise RFC3161EvidenceError("RFC3161 evidence sequence")
            response = self._post(build_timestamp_query(payload_digest))
            parsed, signer_fingerprint = self._verify_response(response, payload_digest)
            evidence = self._evidence(
                run_id=run_id, task_id=task_id, event=event, payload_digest=payload_digest,
                sequence=evidence_sequence, previous=evidence_previous, response=response,
                parsed=parsed, signer_fingerprint=signer_fingerprint,
            )
            proof = {"schema": RFC3161_PROOF_SCHEMA, "response_b64": b64encode(response)}
            # Validate before publishing so record_with_proof has one strict output shape.
            validate_rfc3161_proof(proof)
            self._chains[run_id] = (evidence["sequence"], digest(evidence))
            return RFC3161RecordedProof(evidence=evidence, proof=proof)

    def record(self, *, run_id: str, task_id: str, event: str, payload_digest: str) -> dict[str, Any]:
        """Return the existing digest-only evidence contract."""
        return self.record_with_proof(
            run_id=run_id, task_id=task_id, event=event, payload_digest=payload_digest,
        ).evidence


__all__ = [
    "DEFAULT_POLICY_OID", "FREETSA_CA_PEM_SHA256", "FREETSA_ENDPOINT", "FREETSA_POLICY_OID", "FREETSA_TSA_CERTIFICATE_SHA256", "RFC3161_ENDPOINT", "RFC3161_ENDPOINTS", "RFC3161Config", "RFC3161EvidenceError", "RFC3161RecordedProof", "RFC3161_PROOF_SCHEMA", "MAX_RFC3161_PROOF_BYTES", "MAX_RFC3161_PROOF_B64_BYTES",
    "RFC3161TimingEvidenceAdapter", "build_timestamp_query", "parse_timestamp_response", "validate_rfc3161_proof",
    "validate_rfc3161_evidence",
]
