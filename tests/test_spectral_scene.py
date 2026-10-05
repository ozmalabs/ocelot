"""Stage 4.2: mechanical 2-D photon scene generator (domains/spectral_scene.py)."""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import spectral_forward as sf  # noqa: E402
from domains import spectral_scene as ss  # noqa: E402


def _by_cell(packets):
    out = {}
    for p in packets:
        out.setdefault((p["col"], p["row"]), []).append((p["wavelength_nm"], p["count"]))
    return out


def _sf_cell(spd):
    return [(p["wavelength_nm"], p["count"]) for p in sf.quantize(spd)]


@pytest.fixture(scope="module")
def std():
    return ss.standard_mondrian()


def test_packet_keys_and_bounds(std):
    pk = ss.render(std)
    assert pk and all(set(p) == {"col", "row", "wavelength_nm", "count"} for p in pk)
    assert all(0 <= p["col"] < 24 and 0 <= p["row"] < 16 and p["count"] > 0 for p in pk)
    assert len(_by_cell(pk)) == 24 * 16


@pytest.mark.parametrize("ill", ["E", "D65", "A"])
@pytest.mark.parametrize("filt", [None, "eyelid"])
def test_packets_per_cell_equal_sf_quantize(std, ill, filt):
    cells = _by_cell(ss.render(std, ill, 100.0, filt))
    lab = std.label_map()
    illum = sf.scale_to_td(sf.illuminant(ill), 100.0)
    T = np.ones(391) if filt is None else sf.eyelid_transmittance()
    for row in range(16):
        for col in range(24):
            refl = sf.reflectance(std.reflectance_of(int(lab[row, col])))
            assert cells.get((col, row), []) == _sf_cell(illum * refl * T)


def test_render_matches_spd_from_recipe(std):
    from scripts.marys_room_broad_theory import spd_from_recipe
    spds = ss.cell_spds(std, "D65", 50.0)
    lab = std.label_map()
    for row, col in [(0, 0), (2, 2), (7, 7), (7, 11)]:
        ref = spd_from_recipe({"kind": "scene", "illuminant": "D65", "scene_td": 50.0,
                               "reflectance": std.reflectance_of(int(lab[row, col]))})
        np.testing.assert_allclose(spds[row, col], ref, rtol=1e-12)


def test_label_map_geometry(std):
    lab = std.label_map()
    assert lab.shape == (16, 24)
    for pid, _r, c0, r0, w, h in std.rects:
        assert w >= 3 and h >= 3
        assert (lab[r0:r0 + h, c0:c0 + w] == pid).all()
        assert (lab == pid).sum() == w * h
    assert (lab == 0).sum() == 24 * 16 - sum(r[4] * r[5] for r in std.rects)
    # later rects overwrite earlier ones
    m = ss.Mondrian(6, 5, [(1, "red", 0, 0, 4, 4), (2, "blue", 2, 2, 4, 4)])
    lm = m.label_map()
    assert lm[3, 3] == 2 and lm[1, 1] == 1 and lm[4, 5] == 2 and lm[0, 5] == 0
    assert (lm == 1).sum() == 16 - 4


def test_swap_preserves_geometry_and_exchanges_reflectances(std):
    sw = ss.swap_patches(std, 2, 8)
    np.testing.assert_array_equal(sw.label_map(), std.label_map())
    assert sw.reflectance_of(2) == std.reflectance_of(8)
    assert sw.reflectance_of(8) == std.reflectance_of(2)
    for pid in std.patch_ids():
        if pid not in (2, 8):
            assert sw.reflectance_of(pid) == std.reflectance_of(pid)
    a, b = _by_cell(ss.render(std)), _by_cell(ss.render(sw))
    assert b[(7, 2)] == a[(17, 7)] and b[(17, 7)] == a[(7, 2)]   # red <-> orange cells
    assert ss.swap_patches(sw, 2, 8) == std
    assert std.reflectance_of(2) == "red"   # original untouched


def test_translate_patch(std):
    tr = ss.translate_patch(std, 10, 3, 1)
    lab0, lab1 = std.label_map(), tr.label_map()
    assert tr.rect(10)[2:4] == (11, 12)
    assert (lab1[12:16, 11:15] == 10).all() and (lab1 == 10).sum() == 16
    vac = (lab0 == 10) & (lab1 != 10)
    assert vac.sum() == 4 * 4 - 1 * 3 and (lab1[vac] == 0).all()   # background fills
    others = (lab0 != 10) & (lab1 != 10)
    np.testing.assert_array_equal(lab0[others], lab1[others])
    cells = _by_cell(ss.render(tr))
    bg = _sf_cell(sf.scale_to_td(sf.illuminant("E"), 100) * sf.reflectance(ss.DEFAULT_BACKGROUND))
    assert cells[(8, 11)] == bg
    # off-sheet clipping
    assert (ss.translate_patch(std, 10, 20, 0).label_map() == 10).sum() == 0


def test_isoluminant_pair_and_chromatic_difference(std):
    a, b = ss.ISOLUMINANT_PAIR
    ra, rb = std.rect(a), std.rect(b)
    assert ra[2] + ra[4] == rb[2] and ra[3] == rb[3] and ra[5] == rb[5]   # adjacent
    ill = sf.scale_to_td(sf.illuminant("E"), 100.0)
    sa, sb = ill * sf.reflectance(ra[1]), ill * sf.reflectance(rb[1])
    la, lb = ss.catches_of_spd(sa)["lm"], ss.catches_of_spd(sb)["lm"]
    assert abs(la - lb) / max(la, lb) < ss.ISOLUMINANCE_TOL
    rga = sf.eye_capture_model(sf.quantize(sa))["red_green"]
    rgb = sf.eye_capture_model(sf.quantize(sb))["red_green"]
    assert abs(rga - rgb) > 0.02
    # every other patch-vs-background pair is NOT isoluminant
    bg = ss.catches_of_spd(ill * sf.reflectance(ss.DEFAULT_BACKGROUND))["lm"]
    for pid in std.patch_ids():
        lm = ss.catches_of_spd(ill * sf.reflectance(std.reflectance_of(pid)))["lm"]
        assert abs(lm - bg) / max(lm, bg) >= ss.ISOLUMINANCE_TOL
    assert std.reflectance_of(ss.STANDARD_WHITE_ID).startswith("white 9.5")


def test_expected_catches_oracle(std):
    ec = ss.expected_catches(std, "D65", 100.0)
    assert ec["l"].shape == (16, 24)
    cells = _by_cell(ss.render(std, "D65"))
    for (col, row) in [(0, 0), (3, 3), (7, 7), (12, 8)]:
        pk = [{"wavelength_nm": w, "count": n} for w, n in cells[(col, row)]]
        m = sf.eye_capture_model(pk)
        for r in ("l", "m", "s", "rod"):
            dark = sf.EYE_RECEPTORS[r][3]
            # quantisation moves at most ~1 quantum per bin boundary; check 1%
            assert math.isclose(m[r]["caught"] - dark, ec[r][row, col], rel_tol=0.01, abs_tol=1.0)
    np.testing.assert_allclose(ec["lm"], ec["l"] + ec["m"])


def test_eyelid_diffuse_identical_per_cell():
    pk = ss.diffuse(10, 7, "E", 100.0, "eyelid")
    cells = _by_cell(pk)
    assert len(cells) == 70
    first = cells[(0, 0)]
    assert all(v == first for v in cells.values())
    assert first == _sf_cell(sf.scale_to_td(sf.illuminant("E"), 100.0) * sf.eyelid_transmittance())


def test_adapting_field():
    pk = ss.adapting_field((5, 3), 610.0, 4000)
    assert len(pk) == 15 and all(p["wavelength_nm"] == 610.0 and p["count"] == 4000 for p in pk)
    assert len(ss.adapting_field(ss.standard_mondrian(), 610.0, 10)) == 24 * 16


def test_gain_and_illuminant_maps(std):
    gain = np.ones((16, 24)); gain[:, 12:] = 0.25
    ec0 = ss.expected_catches(std)
    ec1 = ss.expected_catches(std, illum_gain_map=gain)
    np.testing.assert_allclose(ec1["l"][:, 12:], 0.25 * ec0["l"][:, 12:])
    np.testing.assert_allclose(ec1["l"][:, :12], ec0["l"][:, :12])
    idx = np.zeros((16, 24), dtype=int); idx[:, 12:] = 1
    spds = ss.cell_spds(std, illuminant_map=(idx, ["E", "A"]))
    np.testing.assert_allclose(spds[:, :12], ss.cell_spds(std, "E")[:, :12])
    np.testing.assert_allclose(spds[:, 12:], ss.cell_spds(std, "A")[:, 12:])


def test_schedules(std):
    seq = ss.illuminant_change(std, ["E", "D65", "A"])
    assert len(seq) == 3 and seq[1] == ss.render(std, "D65")
    mv = ss.motion(std, 10, [(1, 0), (1, 0)])
    assert mv[0] == ss.render(std) and mv[2] == ss.render(ss.translate_patch(std, 10, 2, 0))


def test_determinism(std):
    assert ss.render(std, "A") == ss.render(std, "A")
    assert ss.standard_mondrian(seed=7) == ss.standard_mondrian(seed=7)
    p1 = ss.render(std, method="poisson", seed=3)
    assert p1 == ss.render(std, method="poisson", seed=3)
    assert p1 != ss.render(std, method="poisson", seed=4)
    with pytest.raises(ValueError):
        ss.render(std, method="poisson")
    sh = ss.standard_mondrian(seed=7)
    assert sh.reflectance_of(1) == std.reflectance_of(1)
    for pid in ss.ISOLUMINANT_PAIR:
        assert sh.reflectance_of(pid) == std.reflectance_of(pid)
    assert sorted(map(str, (sh.reflectance_of(i) for i in sh.patch_ids()))) == \
        sorted(map(str, (std.reflectance_of(i) for i in std.patch_ids())))


def test_graph_eye_2d_accepts_packets():
    """Smoke: packets drive the (rod-only) 2-D sheet; each cell's rod catch
    equals the analytic capture of that cell's packets."""
    from domains.engine_provenance import engine_preamble
    engine_preamble()
    pytest.importorskip("substrate_rs")
    from domains.photon_eye import GraphEye
    scene = ss.Mondrian(6, 4, [(1, "white 9.5 (.05 D)", 0, 0, 3, 4), (2, "red", 3, 0, 3, 4)])
    eye = GraphEye(n_az=6, n_el=4, context={"synchronous": True, "worker_capacity": 1,
                                            "retina_2d": True}).build()
    pk = ss.render(scene)
    eye.submit_photons_2d(pk)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    cells = _by_cell(pk)
    for flat, (col, row) in enumerate((c, r) for r in range(4) for c in range(6)):
        rod = eye._receptors[(row * 6 + col, "rod")]
        got = float(eye.substrate.node(rod)["attrs"]["caught_quanta"])
        m = sf.eye_capture_model([{"wavelength_nm": w, "count": n} for w, n in cells[(col, row)]])
        assert math.isclose(got, m["rod"]["caught"], rel_tol=1e-6), (col, row, got)
