"""Committed real-Doom oracle for attention-directed retinal settlement."""
from __future__ import annotations

from scripts.retinal_focus_fixture_measure import measure


def test_real_doom_focus_preserves_live_coarse_outputs_with_less_settlement():
    result = measure(20, 15)
    command = result["command"]
    whole = result["whole"]
    focused = result["focused"]

    # This is a graph verdict, including the held-prediction fallback route,
    # not a label/depth-selected fixture crop.
    assert command["active"] == 1.0
    assert command["refused"] == 0.0

    # On the real low-resolution fixture there is one live event and it lies in
    # the graph-commanded window. The focused arm preserves every externally
    # visible event product, while the mint rules enumerate only the bounded
    # settlement relation instead of all 300 receptor columns.
    assert focused["event_counts"] == whole["event_counts"] == [1, 1, 1]
    assert (
        focused["polygons"], focused["motion"], focused["salience"]
    ) == (
        whole["polygons"], whole["motion"], whole["salience"]
    ) == (0, 0, 1)
    assert whole["settlement_columns"] == 300
    assert focused["settlement_columns"] <= 81
    assert focused["settlement_columns"] < whole["settlement_columns"]
