"""Compatibility alias for migrated formula-context resolution."""
import sys
from ozagia.research import formula_resolution as _implementation

sys.modules[__name__] = _implementation
