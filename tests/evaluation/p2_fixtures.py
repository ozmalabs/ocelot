from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluation.p0a.canonical import sign
from evaluation.p2.lock import ARTIFACT_NAMES, make_release_lock

PRIVATE = Ed25519PrivateKey.from_private_bytes(bytes([3]) * 32)
PUBLIC = PRIVATE.public_key()
LOCK_PRIVATE = Ed25519PrivateKey.from_private_bytes(bytes([4]) * 32)
LOCK_PUBLIC = LOCK_PRIVATE.public_key()


def release_lock(artifacts=None):
    digest = lambda c: "sha256:" + c * 64
    artifacts = artifacts or {name: digest("abcdef0123456789"[index]) for index, name in enumerate(ARTIFACT_NAMES)}
    return make_release_lock(signing_key=LOCK_PRIVATE, key_id="ed25519:p2-release-test",
        evaluator_key=PUBLIC, evaluator_key_id="ed25519:p2-envelope-test",
        receipt_key=PUBLIC, receipt_key_id="ed25519:p2-receipt-test", artifacts=artifacts)


def signed(value):
    value = dict(value)
    value["signature"] = sign(value, PRIVATE)
    return value
