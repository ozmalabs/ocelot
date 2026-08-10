import math

import numpy as np
import substrate_rs as srs

from domains import doom_photon_world as dpw
from domains.photon_eye import (
    GraphEye,
    fovea_logpolar_receptor_layout,
    receptor_layout_from_calibration,
    uniform_receptor_layout,
)


def test_explicit_uniform_layout_is_exact_legacy_block_mean():
    rng = np.random.default_rng(204000)
    rgb = rng.integers(0, 256, size=(24, 32, 3), dtype=np.uint8)
    layout = uniform_receptor_layout(8, 6, fov_h_deg=90, fov_v_deg=60)
    got = dpw.luma_layout(rgb, layout, 6, 8)
    expected = dpw.luma_grid(rgb, 6, 8)
    assert np.array_equal(got, expected)


def test_114_square_fovea_maps_one_to_one_to_114_square_native_pixels():
    # 90/320 != 60/240: independent foveal FOV axes are necessary.
    rgb = np.arange(240 * 320, dtype=np.uint32).reshape(240, 320)
    rgb = np.repeat((rgb % 251).astype(np.uint8)[..., None], 3, axis=2)
    cal = {
        "retinal_layout": "foveated",
        "fovea_width": 114,
        "fovea_height": 114,
        "source_width": 320,
        "source_height": 240,
        "peripheral_rings": 8,
    }
    layout = receptor_layout_from_calibration(cal, 128, 128)
    fovea = layout[:114 * 114]
    assert all(
        math.isclose(r["angular_width"], math.radians(90 / 320))
        for r in fovea)
    assert all(
        math.isclose(r["angular_height"], math.radians(60 / 240))
        for r in fovea)

    sampled = dpw.luma_layout(rgb, layout, 128, 128).reshape(-1)[:114 * 114]
    native = dpw.luma_grid(rgb, 240, 320)[63:177, 103:217].reshape(-1)
    assert np.array_equal(sampled, native)


def test_foveated_layout_keeps_dense_and_peripheral_scout_paths_connected():
    layout = fovea_logpolar_receptor_layout(
        12, 8, fovea_width=4, fovea_height=3, peripheral_rings=4,
        fovea_fov_h_deg=12, fovea_fov_v_deg=9)
    assert len(layout) == 96
    assert [r["cell_index"] for r in layout] == list(range(96))
    assert sum(r["pathway"] == "fovea" for r in layout) == 12
    assert sum(
        r["pathway"] == "log_polar_periphery" for r in layout) == 84
    for record in layout:
        for other in record["adjacent"]:
            assert record["cell_index"] in layout[other]["adjacent"]

    seen = {0}
    pending = [0]
    while pending:
        for other in layout[pending.pop()]["adjacent"]:
            if other not in seen:
                seen.add(other)
                pending.append(other)
    assert len(seen) == len(layout)
    assert max(r["angular_width"] for r in layout[12:]) > max(
        r["angular_width"] for r in layout[:12])


def test_graph_eye_installs_and_updates_explicit_physical_optics():
    context = {
        "retina_2d": True,
        "synchronous": True,
        "retinal_layout": "foveated",
        "fovea_width": 3,
        "fovea_height": 2,
        "peripheral_rings": 2,
        "fovea_fov_h_deg": 10,
        "fovea_fov_v_deg": 8,
    }
    eye = GraphEye(n_az=5, n_el=4, context=context).build()
    assert eye.receptor_pathway_counts_2d() == {
        "fovea": 6, "log_polar_periphery": 14}
    assert eye.substrate.node(eye._retina)["attrs"]["peripheral_receptors"] == 14
    assert eye._layout_adjacency_edges
    assert eye.substrate.edge_count() >= len(eye._layout_adjacency_edges)
    for flat, cell in enumerate(eye._cells):
        attrs = eye.substrate.node(cell)["attrs"]
        rod_attrs = eye.substrate.node(
            eye._receptors[(flat, "rod")])["attrs"]
        assert attrs["cell_index"] == flat
        assert attrs["pathway"] == rod_attrs["pathway"]
        assert attrs["gaze_az"] == rod_attrs["gaze_az"]

    before_nodes = eye.substrate.node_count()
    before_edges = eye.substrate.edge_count()
    moved = dict(context, gaze_az_deg=7.5, gaze_el_deg=-3.0)
    eye.update_receptor_layout_2d(calibration=moved)
    assert eye.substrate.node_count() == before_nodes
    assert eye.substrate.edge_count() == before_edges
    for flat, record in enumerate(eye._receptor_layout):
        col, row = record["col"], record["row"]
        assert eye._cell_gaze(col, row) == (
            record["gaze_az"], record["gaze_el"])
        attrs = eye.substrate.node(eye._cells[flat])["attrs"]
        assert attrs["gaze_az"] == record["gaze_az"]
        assert attrs["gaze_el"] == record["gaze_el"]


def test_layout_is_strictly_opt_in_for_legacy_graph_shape():
    eye = GraphEye(
        n_az=4, n_el=3,
        context={"retina_2d": True, "synchronous": True}).build()
    assert eye._receptor_layout == []
    assert "pathway" not in eye.substrate.node(eye._cells[0])["attrs"]
    assert "angular_width" not in eye.substrate.node(eye._cells[0])["attrs"]


def test_explicit_uniform_graph_transduction_matches_legacy_graph():
    base = {"retina_2d": True, "synchronous": True, "retina_accel": True}
    legacy = GraphEye(n_az=4, n_el=3, context=base).build()
    explicit = GraphEye(
        n_az=4, n_el=3,
        context=dict(base, retinal_layout="uniform")).build()
    packets = [
        {"col": 0, "row": 0, "wavelength_nm": 498.0, "count": 300},
        {"col": 2, "row": 1, "wavelength_nm": 510.0, "count": 900},
        {"col": 3, "row": 2, "wavelength_nm": 480.0, "count": 1200},
    ]
    legacy.submit_photons_2d(packets)
    explicit.submit_photons_2d(packets)
    for flat in range(12):
        a = legacy.substrate.node(legacy._receptors[(flat, "rod")])["attrs"]
        b = explicit.substrate.node(explicit._receptors[(flat, "rod")])["attrs"]
        for key in (
                "activation", "prev_activation", "adaptation",
                "caught_quanta"):
            assert a[key] == b[key]


def test_salience_readout_carries_exact_packed_cell_physical_gaze():
    eye = GraphEye(
        n_az=5, n_el=4,
        context={
            "retina_2d": True, "synchronous": True,
            "retinal_layout": "foveated",
            "fovea_width": 3, "fovea_height": 2,
            "gaze_az_deg": 11, "gaze_el_deg": -4,
        }).build()
    flat = 4
    record = eye._receptor_layout[flat]
    eye.substrate.add_node("RetinalSalience", {
        "column_index": record["col"], "row_index": record["row"],
        "raw_salience": 2.0, "residual_salience": 1.0, "epoch": 3,
    })
    readout = eye.salience_percepts_2d()
    assert readout == [{
        "column_index": record["col"],
        "row_index": record["row"],
        "cell_index": flat,
        "gaze_az": record["gaze_az"],
        "gaze_el": record["gaze_el"],
        "eye_id": record["eye_id"],
        "pathway": record["pathway"],
        "raw_salience": 2.0,
        "residual_salience": 1.0,
        "epoch": 3,
    }]


def test_gaze_contingent_sampling_moves_optics_not_policy():
    rgb = np.zeros((60, 90, 3), dtype=np.uint8)
    rgb[:, 45:, :] = 240
    base = {
        "retinal_layout": "foveated",
        "fovea_width": 3,
        "fovea_height": 3,
        "fovea_fov_h_deg": 3,
        "fovea_fov_v_deg": 3,
        "peripheral_rings": 3,
    }
    layout_a = receptor_layout_from_calibration(base, 8, 6)
    layout_b = receptor_layout_from_calibration(
        dict(base, gaze_az_deg=15), 8, 6)
    a = dpw.luma_layout(rgb, layout_a, 6, 8).reshape(-1)
    b = dpw.luma_layout(rgb, layout_b, 6, 8).reshape(-1)
    assert np.mean(b[:9]) > np.mean(a[:9])
    assert all(
        math.isclose(
            rb["gaze_az"] - ra["gaze_az"], math.radians(15), abs_tol=1e-12)
        for ra, rb in zip(layout_a[:9], layout_b[:9]))
    assert all(
        rb["gaze_az"] == ra["gaze_az"]
        and rb["gaze_el"] == ra["gaze_el"]
        for ra, rb in zip(layout_a[9:], layout_b[9:]))


def test_transient_event_stream_can_be_allocated_to_persistent_periphery():
    eye = GraphEye(
        n_az=6, n_el=4,
        context={
            "retina_2d": True, "synchronous": True, "event_native": True,
            "retinal_layout": "foveated", "event_pathway": "periphery",
            "fovea_width": 3, "fovea_height": 2,
            "peripheral_rings": 3, "peripheral_spokes": 6,
            "fovea_fov_h_deg": 9, "fovea_fov_v_deg": 6,
        }).build()
    eye._epoch = 1
    for record in eye._receptor_layout:
        eye.substrate.add_node("RetinalOnsetEvent", {
            "column_index": record["col"], "row_index": record["row"],
            "magnitude_db": 9.0, "epoch": 1, "logical_time": 1,
        })

    task = eye.settle_carve_2d(since_epoch=1)
    payload = eye.substrate.node(srs.NodeID(task))["attrs"]["payload"]
    assert payload[4] == 18.0
    packed = payload[5:]
    assert len(packed) == 18 * 3
    flats = [
        int(packed[i + 1]) * eye.n_az + int(packed[i])
        for i in range(0, len(packed), 3)
    ]
    assert min(flats) == 6
    assert max(flats) == 23
