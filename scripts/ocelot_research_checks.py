"""Compatibility alias for migrated research checks."""
import sys
from ozagia.research import checks as _implementation

sys.modules[__name__] = _implementation
