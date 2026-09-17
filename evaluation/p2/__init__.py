"""P2-B1 bounded native counterfactual-planning evaluation surface.

This package is deliberately separate from :mod:`evaluation.p0a`: P2 workers
run only as a sealed native Podman process and evaluator authority remains
outside the worker.
"""
from .protocol import P2ProtocolError, validate_envelope, validate_proposal
from .lock import validate_lock

__all__ = ["P2ProtocolError", "validate_envelope", "validate_proposal", "validate_lock"]
