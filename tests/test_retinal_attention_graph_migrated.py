"""Graph-native attention over main-graph RetinalSalience projections."""
from __future__ import annotations

import json
import math
import shutil

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import reflective_faculty as rf  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
from substrate.seed_loader import SEED_DIR, manifest_for  # noqa: E402

# OPTIONAL DEPENDENCIES (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason on the tests that need it, never a red. See tests/optional_deps.py.
from optional_deps import requires as _requires_optional  # noqa: E402



def _boot(epoch: int = 7, my_angle: float = 90.0):
    """Mechanical minimal boot: the decisions are the two loaded seed rules."""
    substrate, agent = boot_core(seeds=())
    native = rf._native_eval2(substrate)
    native.load_seed_manifest(manifest_for("fovea_salience_bridge"), agent)
    native.load_seed_manifest(manifest_for("retinal_attention_graph"), agent)
    native.set_attr(agent, "vision_settled_epoch", epoch)
    native.set_attr(agent, "my_angle", my_angle)
    return substrate, agent, native


def _project(
    substrate,
    agent,
    *,
    epoch: int,
    col: int,
    row: int = 5,
    gaze_az: float = 0.0,
    gaze_el: float = 0.0,
    raw: float = 0.0,
    residual: float = 0.0,
):
    """Mechanical projection with the exact live photon-sheet attribute contract."""
    salience = substrate.add_node(
        "RetinalSalience",
        {
            "column_index": col,
            "row_index": row,
            "n_az": 16,
            "n_el": 12,
            "gaze_az": gaze_az,
            "gaze_el": gaze_el,
            "sensor_epoch": epoch,
            "raw_salience": raw,
            "residual_salience": residual,
        },
    )
    substrate.add_edge(agent, "perceives_salience", salience)
    return salience


def _candidate_attrs(substrate):
    return [
        substrate.node(node)["attrs"]
        for node in substrate.nodes("FoveaCandidate")
        if substrate.node(node)["attrs"].get("purpose") == "retinal_attention"
    ]


def test_seed_composes_the_existing_tie_refusing_weighted_bridge():
    manifest = manifest_for("retinal_attention_graph")
    assert manifest["depends_on"] == ["fovea_salience_bridge"]
    assert not manifest.get("self_load_only", False)
    text = json.dumps(manifest)
    assert '"residual_salience"' in text
    assert '"Cos"' in text and '"Sin"' in text and '"my_angle"' in text
    assert "doom" not in text.lower()

    bridge = manifest_for("fovea_salience_bridge")
    resolve = next(
        rule for rule in bridge["rules"] if rule["name"] == "fovea_resolve"
    )
    decision = json.dumps(resolve["where"])
    assert '"ArgminUnique"' in decision
    assert '"Filter"' in decision and '"on_valid"' in decision
    assert '"Log"' in decision and '"goal_logweight"' in decision


def test_every_projection_is_consumed_and_top_residual_updates_motor_attention():
    substrate, agent, native = _boot(epoch=7, my_angle=90.0)
    weaker = _project(
        substrate,
        agent,
        epoch=7,
        col=2,
        gaze_az=math.radians(-20.0),
        gaze_el=math.radians(-3.0),
        raw=20.0,
        residual=3.0,
    )
    winner = _project(
        substrate,
        agent,
        epoch=7,
        col=8,
        gaze_az=math.radians(30.0),
        gaze_el=math.radians(4.0),
        raw=12.0,
        residual=9.0,
    )

    native.run_rules()

    # Every Agent -perceives_salience-> projection was consumed, including the
    # losing one; no Python preselection reduced the candidate set.
    assert substrate.node(weaker)["attrs"]["attention_candidate_epoch"] == 7
    assert substrate.node(winner)["attrs"]["attention_candidate_epoch"] == 7
    candidates = _candidate_attrs(substrate)
    assert len(candidates) == 2
    assert sorted(c["residual_salience"] for c in candidates) == [3.0, 9.0]
    assert sum(c.get("is_fovea", 0.0) == 1.0 for c in candidates) == 1

    attrs = substrate.node(agent)["attrs"]
    assert attrs["attention_refused"] == 0.0
    assert attrs["attention_sensor_epoch"] == 7
    # motor_core consumes dimensionless residual/field-mean contrast.
    assert attrs["attention_salience"] == pytest.approx(9.0 / 6.0)
    assert attrs["attention_residual_salience"] == 9.0
    assert attrs["attention_raw_salience"] == 12.0
    assert attrs["attention_column_index"] == 8
    assert attrs["attention_row_index"] == 5
    assert attrs["attention_az"] == pytest.approx(math.radians(30.0))
    assert attrs["attention_el"] == pytest.approx(math.radians(4.0))
    # Absolute direction = my_angle 90 deg + retinal gaze 30 deg = 120 deg.
    assert attrs["attention_x"] == pytest.approx(math.cos(math.radians(120.0)))
    assert attrs["attention_y"] == pytest.approx(math.sin(math.radians(120.0)))


def test_late_exact_top_residual_tie_clears_old_mark_and_is_refused():
    substrate, agent, native = _boot(epoch=11, my_angle=45.0)
    _project(
        substrate,
        agent,
        epoch=11,
        col=3,
        gaze_az=math.radians(-15.0),
        raw=10.0,
        residual=6.0,
    )
    native.run_rules()
    assert substrate.node(agent)["attrs"]["attention_refused"] == 0.0

    # A second, exactly equal candidate arrives in the SAME epoch. This is the
    # hard lifecycle case: the old monotone fovea mark and published direction
    # must both be cleared, not retained as an arbitrary tie-break.
    _project(
        substrate,
        agent,
        epoch=11,
        col=12,
        gaze_az=math.radians(20.0),
        raw=10.0,
        residual=6.0,
    )

    native.run_rules()

    candidates = _candidate_attrs(substrate)
    assert len(candidates) == 2
    assert all(c.get("is_fovea", 0.0) != 1.0 for c in candidates)
    attrs = substrate.node(agent)["attrs"]
    assert attrs["attention_refused"] == 1.0
    assert attrs["attention_sensor_epoch"] == 11
    assert attrs["attention_salience"] == 0.0
    assert attrs["attention_x"] == 0.0
    assert attrs["attention_y"] == 0.0
    assert attrs["attention_column_index"] == -1
    assert attrs["attention_row_index"] == -1


def test_stale_candidates_retire_and_new_epoch_replaces_attention_attrs():
    substrate, agent, native = _boot(epoch=3, my_angle=0.0)
    _project(
        substrate,
        agent,
        epoch=3,
        col=2,
        gaze_az=math.radians(-40.0),
        raw=8.0,
        residual=7.0,
    )
    native.run_rules()
    old_candidates = list(substrate.nodes("FoveaCandidate"))
    assert len(old_candidates) == 1
    assert substrate.node(agent)["attrs"]["attention_az"] == pytest.approx(
        math.radians(-40.0)
    )

    native.set_attr(agent, "vision_settled_epoch", 4)
    _project(
        substrate,
        agent,
        epoch=4,
        col=13,
        row=7,
        gaze_az=math.radians(25.0),
        gaze_el=math.radians(6.0),
        raw=5.0,
        residual=4.0,
    )
    native.run_rules()

    current = _candidate_attrs(substrate)
    assert len(current) == 1
    assert current[0]["candidate_epoch"] == 4
    assert all(old not in list(substrate.nodes("FoveaCandidate")) for old in old_candidates)
    attrs = substrate.node(agent)["attrs"]
    assert attrs["attention_refused"] == 0.0
    assert attrs["attention_sensor_epoch"] == 4
    assert attrs["attention_salience"] == 1.0
    assert attrs["attention_residual_salience"] == 4.0
    assert attrs["attention_column_index"] == 13
    assert attrs["attention_row_index"] == 7
    assert attrs["attention_az"] == pytest.approx(math.radians(25.0))
    assert attrs["attention_el"] == pytest.approx(math.radians(6.0))
    assert attrs["attention_x"] == pytest.approx(math.cos(math.radians(25.0)))
    assert attrs["attention_y"] == pytest.approx(math.sin(math.radians(25.0)))


@_requires_optional('cv2')
def test_world_adapter_photon_projection_drives_attention_in_live_gaze_units():
    """Actual GraphEye projection -> main graph -> master cycle -> motor attrs."""
    from substrate.world_adapter import WorldAdapter

    calibration = {
        "retina_2d": True,
        "retina_n_az": 16,
        "retina_n_el": 12,
        "synchronous": True,
        "retina_accel": True,
        "event_native": True,
        "visual_motion": True,
        "visual_salience": True,
        "event_window_epochs": 8,
        "adapt_rate": 0.4,
        "onset_threshold_db": 6.0,
        "onset_refractory_epochs": 0.0,
    }
    adapter = WorldAdapter(seeds=())
    try:
        adapter.inner.load_seed_manifest(
            manifest_for("fovea_salience_bridge"), adapter.agent
        )
        adapter.inner.load_seed_manifest(
            manifest_for("retinal_attention_graph"), adapter.agent
        )
        adapter.inner.set_attr(adapter.agent, "my_angle", 90.0)

        # The canonical photon-sheet sequence creates a coherent retinal sweep.
        for epoch in range(1, 5):
            counts = np.zeros((12, 16), dtype=np.int64)
            adapter.update_vision(
                calibration=calibration,
                photon_packets=[],
                photon_counts=counts,
                photon_epoch=epoch,
            )
        for col in range(2, 10):
            epoch = col + 3
            counts = np.zeros((12, 16), dtype=np.int64)
            counts[5, col] = 4096
            adapter.update_vision(
                calibration=calibration,
                photon_packets=[
                    {
                        "col": col,
                        "row": 5,
                        "wavelength_nm": 498.0,
                        "count": 4096,
                    }
                ],
                photon_counts=counts,
                photon_epoch=epoch,
            )

        projected = adapter.inner.neighbours(
            adapter.agent, "perceives_salience"
        )
        assert len(projected) == 8
        target = projected[-1]
        gaze_rad = adapter.s.node(target)["attrs"]["gaze_az"]
        assert gaze_rad == pytest.approx(adapter._eye._column_az(9))
        assert abs(gaze_rad) < math.pi

        # The coherent sweep itself is fully explained (zero residual). Make one
        # projected cell unexplained so this integration gate exercises the
        # general residual-attention join, while retaining GraphEye's real gaze.
        adapter.inner.set_attr(target, "residual_salience", 2.0)
        adapter.inner.set_attr(adapter.agent, "attention_x", 99.0)
        adapter.inner.set_attr(adapter.agent, "attention_salience", 99.0)
        adapter.master_tick()
        adapter.inner.run_rules()

        attrs = adapter.s.node(adapter.agent)["attrs"]
        assert all(
            adapter.s.node(node)["attrs"]["attention_candidate_epoch"] == 12
            for node in projected
        )
        assert attrs["attention_sensor_epoch"] == 12
        assert attrs["attention_refused"] == 0.0
        assert attrs["attention_residual_salience"] == 2.0
        # One nonzero residual among eight cells: contrast=2/(2/8)=8, which
        # crosses motor_core's established attention_salience > 2 admission.
        assert attrs["attention_salience"] == pytest.approx(8.0)
        assert attrs["attention_salience"] > 2.0
        heading = math.radians(90.0) + gaze_rad
        assert attrs["attention_x"] == pytest.approx(math.cos(heading))
        assert attrs["attention_y"] == pytest.approx(math.sin(heading))
    finally:
        adapter.close()


def test_load_all_seeds_discovers_and_installs_attention_seed(tmp_path):
    """A normal glob boot installs the seed and its dependency automatically."""
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    for name in ("fovea_salience_bridge.json", "retinal_attention_graph.json"):
        shutil.copyfile(SEED_DIR / name, tmp_path / name)

    adapter = WorldAdapter(seeds=())
    try:
        report = load_all_seeds(adapter, seed_dir=tmp_path)
        assert report["failed"] == []
        assert report["order"] == [
            "fovea_salience_bridge",
            "retinal_attention_graph",
        ]
        assert report["loaded"] == 2
        assert len(
            adapter.inner.neighbours(
                adapter.agent, "has_retinal_attention_resolver"
            )
        ) == 1
    finally:
        adapter.close()
