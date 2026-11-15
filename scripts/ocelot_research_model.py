"""Compatibility alias for migrated research models."""
import sys
from ozagia.research import model as _implementation

sys.modules[__name__] = _implementation
