"""Compatibility alias for migrated finite formula translation."""
import sys
from ozagia.research import finite_formula as _implementation

sys.modules[__name__] = _implementation
