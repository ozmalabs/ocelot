"""P3-R0 local-only evaluator readiness protocol.

This package deliberately provides no adoption authority.  Missing trusted release
or containment evidence is terminal and is sealed as an impasse/no-go.
"""
from .protocol import P3ProtocolError, validate_learning_proposal
from .lock import P3ReleaseLockV1, validate_lock

__all__ = ["P3ProtocolError", "P3ReleaseLockV1", "validate_learning_proposal", "validate_lock"]
