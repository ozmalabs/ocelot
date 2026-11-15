"""Compatibility alias for migrated finite membership translation."""
import sys
from ozagia.research import membership as _implementation

sys.modules[__name__] = _implementation
