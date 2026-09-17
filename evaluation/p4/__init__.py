"""P4-R0 local-only readiness gate.  It never authorizes adoption or release."""
from .protocol import P4ProtocolError
__all__ = ["P4ProtocolError"]
