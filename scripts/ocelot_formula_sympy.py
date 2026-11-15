"""Compatibility alias for migrated optional SymPy/Lark candidates."""
import sys
from ozagia.research import formula_sympy as _implementation

sys.modules[__name__] = _implementation
