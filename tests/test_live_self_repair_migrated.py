"""The default dual-process cycle retains the known graph-native repair reflex."""
from __future__ import annotations

from scripts.jabberwock_live_self_repair import main


def test_live_perception_regression_repairs_and_keeps_clause():
    assert main() == 0
