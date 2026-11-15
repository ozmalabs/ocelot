"""Compatibility alias for the migrated Ozagia research graph."""
import sys
from ozagia.research import graph as _implementation

sys.modules[__name__] = _implementation
