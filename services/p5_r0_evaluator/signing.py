from __future__ import annotations

from typing import Any

from .canonical import b64decode, b64encode, digest, signing_digest
from .interfaces import Signer


class KMSConfigurationError(ValueError):
    pass


class KMSEd25519Signer(Signer):
    """KMS signer. The private key never enters this process."""
    def __init__(self, key_version: str, authority: dict[str, Any], client: Any | None = None):
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
        try:
            public = client.get_public_key(request={"name": key_version})
            algorithm = getattr(public, "algorithm", None)
            algorithm_name = getattr(algorithm, "name", None) or str(algorithm)
            if not algorithm_name or "EC_SIGN_ED25519" not in algorithm_name:
                raise KMSConfigurationError("KMS key is not EC_SIGN_ED25519")
            pem = public.pem
            from cryptography.hazmat.primitives import serialization
            key = serialization.load_pem_public_key(pem.encode("utf-8"))
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            if not isinstance(key, Ed25519PublicKey):
                raise KMSConfigurationError("KMS public key is not Ed25519")
            raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        except KMSConfigurationError:
            raise
        except Exception as exc:
            raise KMSConfigurationError("KMS public key unavailable") from exc
        encoded = b64encode(raw)
        if encoded != authority["public_key"]:
            raise KMSConfigurationError("KMS public key does not match authority")
        self._public_key = raw

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
