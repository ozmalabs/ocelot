"""Compatibility alias for migrated research traces."""
import sys
from ozagia.research import trace as _implementation

sys.modules[__name__] = _implementation
