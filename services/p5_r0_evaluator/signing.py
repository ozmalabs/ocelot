from __future__ import annotations

import base64
from typing import Any

from .canonical import b64decode, b64encode, digest, signing_digest
from .interfaces import Signer


class KMSConfigurationError(ValueError):
    pass


class VerifierIssuedKMSCapability:
    """Opaque, verifier-issued permission to use a non-exportable KMS key.

    The capability is intentionally not represented by a caller-controlled
    boolean or mapping.  A verifier-owned adapter obtains it only after the
    attested transport and key binding have been established.  The test-only
    factory is useful for structural adapter tests but is not evidence of a
    live KMS boundary.
    """
    __slots__ = ("_commitment", "_token")
    _TOKEN = object()

    def __init__(self, commitment: dict[str, Any], token: object):
        if token is not self._TOKEN:
            raise KMSConfigurationError("verifier-issued KMS capability required")
        self._commitment = dict(commitment)
        self._token = token

    @property
    def commitment(self) -> dict[str, Any]:
        return dict(self._commitment)

    def matches(self, *, key_version: str, authority: dict[str, Any]) -> bool:
        return (
            self._commitment.get("schema") == "P5R0VerifierKMSCapabilityV1"
            and self._commitment.get("key_version") == key_version
            and self._commitment.get("authority_id") == authority.get("authority_id")
            and self._commitment.get("key_id") == authority.get("key_id")
            and self._commitment.get("public_key_digest") == authority.get("public_key_digest")
            and self._commitment.get("transport_digest") == digest(authority.get("transport_attestation"))
            and self._commitment.get("capability_digest") == digest({
                key: value for key, value in self._commitment.items() if key != "capability_digest"
            })
        )


def issue_verifier_kms_capability(*, issuer: str, key_version: str, authority: dict[str, Any]) -> VerifierIssuedKMSCapability:
    """Create a capability at an adapter boundary after external verification.

    Production callers must invoke this only from the verifier-owned signed
    environment.  It deliberately carries commitments, never private key
    material or a promotion flag.
    """
    if not issuer or not key_version or not isinstance(authority, dict):
        raise KMSConfigurationError("KMS capability inputs")
    commitment = {
        "schema": "P5R0VerifierKMSCapabilityV1",
        "issuer": issuer,
        "authority_id": authority.get("authority_id"),
        "key_id": authority.get("key_id"),
        "key_version": key_version,
        "public_key_digest": authority.get("public_key_digest"),
        "transport_digest": digest(authority.get("transport_attestation")),
    }
    commitment["capability_digest"] = digest(commitment)
    return VerifierIssuedKMSCapability(commitment, VerifierIssuedKMSCapability._TOKEN)


class KMSEd25519Signer(Signer):
    """KMS signer. The private key never enters this process."""
    def __init__(self, key_version: str, authority: dict[str, Any], client: Any | None = None,
                 verifier_capability: VerifierIssuedKMSCapability | None = None):
        if not key_version or set(authority) != {"schema", "authority_id", "key_id", "public_key", "public_key_digest", "transport_attestation"}:
            raise KMSConfigurationError("closed signer authority metadata")
        # A signer is an exported capability boundary.  It must never create a
        # default-credential KMS client on behalf of an untrusted caller.
        if client is None:
            raise KMSConfigurationError("explicit federated KMS client is required")
        if authority["schema"] not in {"P5R0AuthorityV3", "P5R0PublicAuthorityV4"} or authority["public_key_digest"] != digest(authority["public_key"]):
            raise KMSConfigurationError("authority metadata")
        transport = authority.get("transport_attestation")
        if authority["schema"] == "P5R0PublicAuthorityV4" and (not isinstance(transport, dict) or set(transport) != {"schema", "provider", "audience", "event"} or transport.get("schema") != "P5R0AuthorityTransportV1"):
            raise KMSConfigurationError("closed authority transport metadata")
        self.authority = dict(authority)
        self.key_version = key_version
        self.client = client
        self.verifier_capability = verifier_capability
        try:
            public = client.get_public_key(request={"name": key_version})
            algorithm = getattr(public, "algorithm", None)
            algorithm_name = getattr(algorithm, "name", None) or str(algorithm)
            if not algorithm_name or "EC_SIGN_ED25519" not in algorithm_name:
                raise KMSConfigurationError("KMS key is not EC_SIGN_ED25519")
            pem = public.pem
            if isinstance(pem, bytes):
                pem_text = pem.decode("ascii")
            elif isinstance(pem, str):
                pem_text = str(pem)
            else:
                raise KMSConfigurationError("KMS public key encoding")
            pem_body = "".join(
                line.strip() for line in pem_text.splitlines()
                if line.strip() and not line.startswith("-----")
            )
            raw_bytes = b64decode(self.authority["public_key"])
            if len(raw_bytes) != 32:
                raise KMSConfigurationError("KMS authority public key length")
            expected_der = bytes.fromhex("302a300506032b6570032100") + raw_bytes
            expected_body = base64.b64encode(expected_der).decode("ascii")
            if pem_body != expected_body:
                raise KMSConfigurationError("KMS public key does not match authority")
        except KMSConfigurationError:
            raise
        except Exception as exc:
            # Preserve a bounded diagnostic category without exposing API
            # response bodies, token material, or resource details.
            error_type = type(exc).__name__.lower()
            error_text = str(exc).lower()
            if (
                "permission" in error_type or "forbidden" in error_type or
                "permission" in error_text or "forbidden" in error_text or
                "unauthorized" in error_text or "statuscode=403" in error_text or
                "status code 403" in error_text
            ):
                raise KMSConfigurationError("KMS public key permission denied") from exc
            if "unauthenticated" in error_type or "invalid_grant" in error_text:
                raise KMSConfigurationError("KMS public key authentication failed") from exc
            if "unavailable" in error_type or "deadline" in error_type or "timeout" in error_text or "connection" in error_text:
                raise KMSConfigurationError("KMS public key transport failed") from exc
            if "notfound" in error_type or "not found" in error_text:
                raise KMSConfigurationError("KMS public key resource unavailable") from exc
            if error_type == "typeerror":
                traceback = __import__("traceback")
                frame = traceback.extract_tb(exc.__traceback__)[-1]
                filename = frame.filename.rsplit("/", 1)[-1]
                raise KMSConfigurationError(f"KMS public key type error line {frame.lineno} file {filename}") from exc
            known_types = {
                "attributeerror": "attribute_error",
                "typeerror": "type_error",
                "valueerror": "value_error",
                "invalidargument": "invalid_argument",
                "unauthenticated": "authentication_failed",
                "permissiondenied": "permission_denied",
                "serviceunavailable": "transport_failed",
                "deadlineexceeded": "deadline_exceeded",
                "refresherror": "authentication_failed",
            }
            category = known_types.get(error_type, "unknown client error")
            raise KMSConfigurationError(f"KMS public key {category}") from exc
        if isinstance(raw_bytes, str):
            raw_text = str(raw_bytes)
            try:
                raw_bytes = raw_text.encode("latin-1")
            except UnicodeEncodeError:
                raw_bytes = raw_text.encode("utf-8")
        elif not isinstance(raw_bytes, bytes):
            raw_bytes = bytes(raw_bytes)
        encoded = b64encode(raw_bytes)
        if encoded != authority["public_key"]:
            raise KMSConfigurationError("KMS public key does not match authority")
        self._public_key = raw_bytes

    def sign_digest(self, message_digest: bytes) -> str:
        if len(message_digest) != 32:
            raise KMSConfigurationError("signing input must be one SHA-256 digest")
        try:
            response = self.client.asymmetric_sign(
                # Ed25519 is a raw signing algorithm in Cloud KMS: the
                # already-computed protocol SHA-256 digest is supplied as data,
                # not as a second-level digest.sha256 request.
                request={"name": self.key_version, "data": message_digest}
            )
            signature = bytes(response.signature)
        except Exception as exc:
            raise KMSConfigurationError("KMS signing failed") from exc
        if len(signature) != 64:
            raise KMSConfigurationError("unexpected Ed25519 signature")
        encoded = b64encode(signature)
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            Ed25519PublicKey.from_public_bytes(self._public_key).verify(signature, message_digest)
        except Exception as exc:
            raise KMSConfigurationError("KMS returned an invalid Ed25519 signature") from exc
        return encoded


def sign_object(obj: dict[str, Any], signer: Signer, *excluded: str) -> str:
    return signer.sign_digest(signing_digest(obj, *excluded))


def verify_task_signature(obj: dict[str, Any], authority: dict[str, Any]) -> None:
    """Signature verification is intentionally available without private material."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from .canonical import signing_digest
    try:
        Ed25519PublicKey.from_public_bytes(b64decode(authority["public_key"])).verify(
            b64decode(obj["signature"]), signing_digest(obj)
        )
    except Exception as exc:
        raise KMSConfigurationError("invalid service signature") from exc
