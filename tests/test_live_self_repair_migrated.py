"""The default dual-process cycle retains the known graph-native repair reflex."""
from __future__ import annotations

from scripts.jabberwock_live_self_repair import main

# OPTIONAL DEPENDENCY (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason, never a red. See tests/optional_deps.py.
from optional_deps import importorskip as _optional_importorskip  # noqa: E402
_optional_importorskip('cv2')



def test_live_perception_regression_repairs_and_keeps_clause():
    assert main() == 0
