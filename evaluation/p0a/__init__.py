"""Local P0-A harness approximation, not evaluator custody.

Keep the package namespace lightweight. Normal runtime code imports the
standalone legacy-I/O guard from this package, but must not thereby import the
evaluation broker, manifest verifier, or their cryptographic dependencies.
The historical convenience exports remain available on explicit access.
"""

from __future__ import annotations

from typing import Any

__all__ = ["ActionBroker", "BrokerReply", "ManifestVerifier"]


def __getattr__(name: str) -> Any:
    if name in {"ActionBroker", "BrokerReply"}:
        from . import broker
        return getattr(broker, name)
    if name == "ManifestVerifier":
        from .manifest import ManifestVerifier
        return ManifestVerifier
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
