"""Focused gates for the generic live allocentric world-view faculty."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from domains.allocentric_world_view_ingest import (
    ingest_current_optic_evidence,
)
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


def _fresh():
    world = WorldAdapter(seeds=())
    result = world.inner.load_seed_manifest(
        manifest_for("allocentric_world_view"), world.agent)
    assert result["rules_skipped"] == []
    return world


def _params(world, *, enabled=1.0, max_age=32):
    (params,) = list(
        world.s.nodes("AllocentricWorldViewParams"))
    world.inner.set_attr(params, "enabled", enabled)
    world.inner.set_attr(params, "max_cell_age_epochs", max_age)
    return params


def _evidence(
        world,
        *,
        epoch,
        x=120.0,
        y=50.0,
        sigma=4.0,
        confidence=0.8,
        topology="visible_surface_support",
        occupancy_commit=0.0,
):
    evidence = world.s.add_node(
        "OpticRangeEvidence",
        {
            "sensor_epoch": epoch,
            "column_index": 5,
            "row_index": 4,
            "bearing_rad": 0.0,
            "range_world": 20.0,
            "x_world": x,
            "y_world": y,
            "range_sigma_world": sigma,
            "confidence": confidence,
            "topology_kind": topology,
            "occupancy_commit": occupancy_commit,
            "oracle_free": 1.0,
        },
    )
    world.inner.add_edge_unchecked(
        world.agent, "holds_spatial_evidence", evidence)
    return evidence


def _set_epoch(world, epoch):
    world.inner.set_attr(world.agent, "vision_settled_epoch", epoch)


def _visual_tile(
        world, *, epoch, x=120.0, y=50.0, sigma=2.0,
        observed_quanta=None, feature_unit="photon_count_quanta"):
    attrs = {
        "world_x": x,
        "world_y": y,
        "registration_uncertainty_world": sigma,
        "last_observed_epoch": epoch,
        "world_relative": 1.0,
        "occupancy_commit": 0.0,
    }
    if observed_quanta is not None:
        attrs["observed_quanta"] = observed_quanta
        attrs["feature_unit"] = feature_unit
    tile = world.s.add_node("VisualTile", attrs)
    world.inner.add_edge_unchecked(
        world.agent, "holds_visual_tile", tile)
    return tile


def _held_photometry(
        world, evidence, *, epoch, observed_quanta,
        unit="photon_count_quanta"):
    held = world.s.add_node(
        "HeldPredictionResidual",
        {
            "sensor_epoch": epoch,
            "observed_quanta": observed_quanta,
        },
    )
    world.inner.set_attr(evidence, "photometry_unit", unit)
    world.inner.add_edge_unchecked(
        evidence, "supported_by_photometry", held)
    return held


def _assessment_for(world, ingress):
    for assessment in world.inner.neighbours(
            world.agent, "assesses_world_view_ingress"):
        if ingress in world.inner.neighbours(
                assessment, "based_on_world_view_ingress"):
            return world.s.node(assessment)["attrs"]
    raise AssertionError("no assessment for ingress")


def test_default_off_bridge_is_cognitively_inert():
    world = _fresh()
    _set_epoch(world, 7)
    evidence = _evidence(world, epoch=7)

    assert ingest_current_optic_evidence(world) == 1
    assert list(world.s.nodes("AllocentricWorldViewCell")) == []
    assert list(world.s.nodes("WorldViewAssessment")) == []
    (ingress,) = list(world.s.nodes("WorldViewIngress"))
    assert world.inner.neighbours(
        ingress, "based_on_spatial_evidence") == [evidence]


def test_current_graph_admitted_evidence_mints_persistent_surface_support():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    evidence = _evidence(world, epoch=7)

    assert ingest_current_optic_evidence(world) == 1
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    attrs = world.s.node(cell)["attrs"]
    assert attrs["world_x"] == 120.0
    assert attrs["world_y"] == 50.0
    assert attrs["registration_uncertainty_world"] == 4.0
    assert attrs["confidence"] == 0.8
    assert attrs["observation_count"] == 1
    assert attrs["freshness"] == 1
    assert attrs["topology_kind"] == "visible_surface_support"
    assert attrs["occupancy_commit"] == 0
    assert attrs["world_relative"] == 1
    assert "surface_value" not in attrs
    assert world.inner.neighbours(cell, "grounded_by") == [evidence]

    (ingress,) = list(world.s.nodes("WorldViewIngress"))
    assessment = _assessment_for(world, ingress)
    assert assessment["status"] == "supported"
    assert assessment["result"] == "minted_novel_surface_support"


def test_uncertainty_supported_revisit_updates_unique_existing_cell():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    _evidence(world, epoch=7, x=120.0, y=50.0, sigma=4.0)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))

    _set_epoch(world, 8)
    world.inner.run_rules()
    evidence = _evidence(
        world, epoch=8, x=122.0, y=51.0, sigma=2.0, confidence=0.9)
    assert ingest_current_optic_evidence(world) == 1

    assert list(world.s.nodes("AllocentricWorldViewCell")) == [cell]
    attrs = world.s.node(cell)["attrs"]
    assert attrs["world_x"] == 120.0 and attrs["world_y"] == 50.0
    assert attrs["latest_world_x"] == 122.0
    assert attrs["latest_world_y"] == 51.0
    assert attrs["last_observed_epoch"] == 8
    assert attrs["observation_count"] == 2
    assert attrs["registration_uncertainty_world"] == 2.0
    assert attrs["confidence"] == 0.9
    assert evidence in world.inner.neighbours(cell, "grounded_by")


def test_nonoverlapping_uncertainty_support_grows_world_view():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    _evidence(world, epoch=7, x=0.0, y=0.0, sigma=2.0)
    _evidence(world, epoch=7, x=20.0, y=20.0, sigma=2.0)

    assert ingest_current_optic_evidence(world) == 2
    cells = list(world.s.nodes("AllocentricWorldViewCell"))
    assert len(cells) == 2
    assert {
        (world.s.node(cell)["attrs"]["world_x"],
         world.s.node(cell)["attrs"]["world_y"])
        for cell in cells
    } == {(0.0, 0.0), (20.0, 20.0)}


def test_exact_nearest_distance_tie_refuses_association():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    for x in (-1.0, 1.0):
        cell = world.s.add_node(
            "AllocentricWorldViewCell",
            {
                "world_x": x,
                "world_y": 0.0,
                "range_world": 10.0,
                "registration_uncertainty_world": 3.0,
                "confidence": 0.5,
                "first_observed_epoch": 6,
                "last_observed_epoch": 6,
                "observation_count": 1,
                "freshness": 1.0,
                "status": "fresh",
                "topology_kind": "visible_surface_support",
                "world_relative": 1.0,
                "occupancy_commit": 0.0,
                "oracle_free": 1.0,
            },
        )
        world.inner.add_edge_unchecked(
            world.agent, "holds_world_view_cell", cell)
    _evidence(world, epoch=7, x=0.0, y=0.0, sigma=3.0)

    assert ingest_current_optic_evidence(world) == 1
    cells = list(world.s.nodes("AllocentricWorldViewCell"))
    assert len(cells) == 2
    assert all(
        world.s.node(cell)["attrs"]["observation_count"] == 1
        for cell in cells
    )
    (ingress,) = list(world.s.nodes("WorldViewIngress"))
    assessment = _assessment_for(world, ingress)
    assert assessment["status"] == "refused"
    assert assessment["reason"] == "ambiguous_world_cell_association"


def test_bridge_rejects_stale_evidence_without_host_thresholds():
    world = _fresh()
    _params(world)
    _set_epoch(world, 8)
    _evidence(world, epoch=7)

    assert ingest_current_optic_evidence(world) == 0
    assert list(world.s.nodes("WorldViewIngress")) == []
    assert list(world.s.nodes("AllocentricWorldViewCell")) == []


def test_world_view_decays_stales_and_accepts_transsaccadic_enrichment():
    world = _fresh()
    _params(world, max_age=2)
    _set_epoch(world, 7)
    _evidence(world, epoch=7, sigma=4.0)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))

    tile = _visual_tile(world, epoch=7, x=122.0, y=51.0)
    world.inner.run_rules()
    assert world.inner.neighbours(
        cell, "enriched_by_visual_tile") == [tile]

    _set_epoch(world, 10)
    world.inner.run_rules()
    attrs = world.s.node(cell)["attrs"]
    assert attrs["freshness"] == pytest.approx(0.25)
    assert attrs["status"] == "stale"
    assert list(world.s.nodes("AllocentricWorldViewCell")) == [cell]


def test_unique_current_enriched_tile_publishes_surface_photometry():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    _evidence(world, epoch=7)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))

    tile = _visual_tile(world, epoch=7, observed_quanta=37.0)
    world.inner.run_rules()

    attrs = world.s.node(cell)["attrs"]
    assert attrs["surface_value"] == 37.0
    assert attrs["surface_value_unit"] == "photon_count_quanta"
    assert attrs["surface_value_epoch"] == 7
    assert attrs["surface_value_status"] == "supported"
    assert attrs["surface_value_source"] == "unique_current_visual_tile"
    assert world.inner.neighbours(
        cell, "surface_value_grounded_by") == [tile]


def test_unique_current_held_photometry_publishes_without_fixation_tile():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    evidence = _evidence(world, epoch=7)
    held = _held_photometry(
        world, evidence, epoch=7, observed_quanta=41.0)
    ingest_current_optic_evidence(world)

    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    attrs = world.s.node(cell)["attrs"]
    assert attrs["surface_value"] == 41.0
    assert attrs["surface_value_unit"] == "photon_count_quanta"
    assert attrs["surface_value_epoch"] == 7
    assert attrs["surface_value_status"] == "supported"
    assert attrs["surface_value_source"] == "unique_current_held_photometry"
    assert world.inner.neighbours(
        cell, "surface_value_grounded_by_evidence") == [evidence]
    assert world.inner.neighbours(
        cell, "surface_value_grounded_by_held") == [held]


def test_current_direct_photometry_precedes_longer_lived_visual_tile():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    evidence = _evidence(world, epoch=7)
    _held_photometry(world, evidence, epoch=7, observed_quanta=41.0)
    _visual_tile(world, epoch=7, observed_quanta=99.0)
    ingest_current_optic_evidence(world)

    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    attrs = world.s.node(cell)["attrs"]
    assert attrs["surface_value"] == 41.0
    assert attrs["surface_value_source"] == "unique_current_held_photometry"


def test_ambiguous_direct_photometry_blocks_visual_tile_fallback():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    evidence = _evidence(world, epoch=7)
    _held_photometry(world, evidence, epoch=7, observed_quanta=20.0)
    _held_photometry(world, evidence, epoch=7, observed_quanta=30.0)
    _visual_tile(world, epoch=7, observed_quanta=99.0)
    ingest_current_optic_evidence(world)

    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    attrs = world.s.node(cell)["attrs"]
    assert "surface_value" not in attrs
    assert "surface_value_source" not in attrs


def test_published_direct_photometry_is_revoked_on_late_ambiguity():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    evidence = _evidence(world, epoch=7)
    _held_photometry(world, evidence, epoch=7, observed_quanta=20.0)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    assert (
        world.s.node(cell)["attrs"]["surface_value_source"]
        == "unique_current_held_photometry"
    )

    _held_photometry(world, evidence, epoch=7, observed_quanta=30.0)
    world.inner.run_rules()
    attrs = world.s.node(cell)["attrs"]
    assert attrs["surface_value"] is None
    assert attrs["surface_value_epoch"] == -1
    assert (
        attrs["surface_value_status"]
        == "refused_no_unique_current_held_photometry"
    )


@pytest.mark.parametrize(
    "tiles",
    [
        [],
        [
            {"epoch": 6, "observed_quanta": 20.0},
        ],
        [
            {"epoch": 7, "observed_quanta": 20.0},
            {"epoch": 7, "observed_quanta": 30.0},
        ],
        [
            {"epoch": 7, "observed_quanta": None},
        ],
    ],
)
def test_zero_stale_missing_or_ambiguous_tiles_leave_surface_absent(tiles):
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    _evidence(world, epoch=7)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    for tile in tiles:
        _visual_tile(world, **tile)
    world.inner.run_rules()

    attrs = world.s.node(cell)["attrs"]
    assert "surface_value" not in attrs
    assert "surface_value_unit" not in attrs
    assert "surface_value_epoch" not in attrs


def test_published_surface_is_revoked_when_current_tile_becomes_ambiguous():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    _evidence(world, epoch=7)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))

    _visual_tile(world, epoch=7, observed_quanta=20.0)
    world.inner.run_rules()
    assert world.s.node(cell)["attrs"]["surface_value_status"] == "supported"

    _visual_tile(world, epoch=7, observed_quanta=30.0)
    world.inner.run_rules()
    attrs = world.s.node(cell)["attrs"]
    assert attrs["surface_value"] is None
    assert attrs["surface_value_unit"] is None
    assert attrs["surface_value_epoch"] == -1
    assert (
        attrs["surface_value_status"]
        == "refused_no_unique_current_visual_tile"
    )


def test_published_surface_is_revoked_after_its_sensor_epoch():
    world = _fresh()
    _params(world)
    _set_epoch(world, 7)
    _evidence(world, epoch=7)
    ingest_current_optic_evidence(world)
    (cell,) = list(world.s.nodes("AllocentricWorldViewCell"))
    _visual_tile(world, epoch=7, observed_quanta=20.0)
    world.inner.run_rules()

    _set_epoch(world, 8)
    world.inner.run_rules()
    attrs = world.s.node(cell)["attrs"]
    assert attrs["surface_value"] is None
    assert attrs["surface_value_epoch"] == -1
    assert (
        attrs["surface_value_status"]
        == "refused_no_unique_current_visual_tile"
    )


def test_source_audit_is_generic_and_bridge_contains_no_cognition():
    manifest = manifest_for("allocentric_world_view")
    text = json.dumps(manifest).lower()
    assert manifest["nodes"][0]["attrs"]["enabled"] == 0.0
    assert "map_mode" not in text
    assert '"doom"' not in text
    assert "depth_buffer" not in text and "labels_buffer" not in text
    assert "screen_buffer" not in text and "raw_pixel" not in text
    assert '"occupancy_commit": 1' not in text
    assert '"type": "argminunique"' in text

    source = (
        __import__(
            "domains.allocentric_world_view_ingest",
            fromlist=["unused"],
        )
        .__file__
    )
    bridge = open(source, encoding="utf-8").read()
    assert 'add_node("AllocentricWorldViewCell"' not in bridge
    assert "range_sigma_world" not in bridge
    assert "x_world" not in bridge and "y_world" not in bridge
    assert "sorted(" not in bridge and ".sort(" not in bridge
