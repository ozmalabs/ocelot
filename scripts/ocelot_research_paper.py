"""Compatibility alias for migrated paper ingestion."""
import sys
from ozagia.research import paper as _implementation

sys.modules[__name__] = _implementation
