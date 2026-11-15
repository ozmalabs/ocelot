"""Compatibility alias for migrated Lean export."""
import sys
from ozagia.research import lean as _implementation

sys.modules[__name__] = _implementation
