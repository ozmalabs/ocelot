"""Compatibility alias for migrated research sources."""
import sys
from ozagia.research import sources as _implementation

sys.modules[__name__] = _implementation
