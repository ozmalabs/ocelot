"""Compatibility alias for migrated native research projection."""
import sys
from ozagia.research import native as _implementation

sys.modules[__name__] = _implementation
