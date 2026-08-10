from __future__ import annotations

import json

import pytest

from domains.graph_snapshot_io import (
    load_graph_snapshot,
    save_graph_snapshot,
)


class _SnapshotSubstrate:
    def __init__(self, graph=None) -> None:
        self.graph = graph or {"nodes": [{"id": "n0"}], "edges": []}

    def graph_to_dict(self):
        return self.graph

    def graph_from_dict(self, graph):
        self.graph = graph


def test_graph_snapshot_io_has_no_cortex_rehydration(tmp_path):
    path = tmp_path / "graph.json"
    source = _SnapshotSubstrate()
    info = save_graph_snapshot(source, str(path))
    target = _SnapshotSubstrate({"nodes": [], "edges": []})
    loaded = load_graph_snapshot(target, str(path))

    assert info["graph_path"] == str(path)
    assert target.graph == source.graph == loaded


def test_motor_cortex_is_explicitly_quarantined():
    from domains.motor_cortex import (
        LEGACY_COMPATIBILITY_ONLY,
        MotorCortex,
    )

    assert LEGACY_COMPATIBILITY_ONLY is True
    assert MotorCortex.LEGACY_COMPATIBILITY_ONLY is True
    with pytest.warns(DeprecationWarning, match="legacy Python"):
        MotorCortex(object())


def test_legacy_session_api_remains_compatible_but_warns(tmp_path):
    from domains.cortex_persistence import (
        LEGACY_COMPATIBILITY_ONLY,
        save_session,
    )

    base = str(tmp_path / "session")
    with pytest.warns(DeprecationWarning, match="legacy Python"):
        info = save_session(_SnapshotSubstrate(), base, [])

    assert LEGACY_COMPATIBILITY_ONLY is True
    assert info["n_cortices"] == 0
    assert json.loads(
        (tmp_path / "session.session.json").read_text(encoding="utf-8")
    ) == {"cortices": []}
