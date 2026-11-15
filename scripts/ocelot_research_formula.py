"""Compatibility alias for migrated formula translation."""
import sys
from ozagia.research import formula as _implementation

sys.modules[__name__] = _implementation
