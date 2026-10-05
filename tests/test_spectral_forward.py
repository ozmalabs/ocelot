"""Unit tests for the spectral forward model (photon source).

These test forward-model properties only.  The eyelid's *eye-response* sign is
a preregistered prediction measured in Arm B, not a unit test (Amendment A0-c).
The single eye test below is a pilot-regression anchor: forward-model packets
for 1000 quanta at 610/530 nm must reproduce the known pilot/smoke outputs.
"""
from __future__ import annotations

import time

import numpy as np
import pytest

from domains import spectral_forward as sf

PILOT_LMS = {610: (0.7057161, 0.2052721, 8.034895e-06),
             530: (0.7706373, 0.9356857, 0.01260114)}
SMOKE = {610: (0.3436120168296669, -0.3456013062040921),
         530: (-0.07537232767138446, -0.6214367610772381)}


# -- data / grid ------------------------------------------------------------

def test_grid_shapes():
    assert sf.grid(1).shape == (391,) and sf.grid(1)[[0, -1]].tolist() == [390, 780]
    assert sf.grid(5).shape == (79,) and sf.step_for(np.zeros(79)) == 5
    for step in (1, 5):
        n = len(sf.grid(step))
        assert sf.load_lms("2deg", step).shape == (n, 3)
        assert sf.load_lms("10deg", step).shape == (n, 3)
        assert sf.load_xyz(step).shape == (n, 3)
        assert sf.v_star(step).shape == (n,)
        for ill in ("E", "D65", "A"):
            assert sf.illuminant(ill, step).shape == (n,)
        assert sf.reflectance("red", step).shape == (n,)
    assert len(sf.reflectance_names()) == 24


def test_illuminant_normalisation_and_a_matches_cie_table():
    wl = sf.grid(1)
    i560 = int(np.where(wl == 560)[0][0])
    for ill in ("E", "D65", "A"):
        assert sf.illuminant(ill)[i560] == pytest.approx(100.0, rel=1e-6)
    tab = sf._read_numeric_csv(sf.RAW_DIR / "CIE_std_illum_A_1nm.csv", 2)
    tab = tab[(tab[:, 0] >= 390) & (tab[:, 0] <= 780)]
    np.testing.assert_allclose(sf.illuminant_a_planck(tab[:, 0]), tab[:, 1], rtol=1e-5)


def test_vstar_is_cvrl_lm_combination_and_km():
    lms = sf.load_lms("2deg")
    np.testing.assert_allclose(sf.v_star(), 0.68990272 * lms[:, 0] + 0.34832189 * lms[:, 1],
                               atol=1e-6)
    assert sf.K_M_F_2DEG == pytest.approx(sf.derive_k_m_f(), rel=1e-12)


def test_reflectance_interpolation_and_end_hold():
    names, wl_src, refl = sf._colorchecker()
    r = sf.reflectance(1)
    wl = sf.grid(1)
    assert r[wl == 400][0] == pytest.approx(refl[0][wl_src == 400][0])
    assert np.all(r[wl >= 730] == refl[0][-1])
    assert np.all((sf.reflectance("white 9.5") > 0) & (sf.reflectance("white 9.5") < 1))


# -- 1. CIE recovery --------------------------------------------------------

@pytest.mark.parametrize("lam", [610, 530])
def test_cie_recovery_monochromatic(lam):
    for step in (1, 5):
        spd = np.zeros(len(sf.grid(step)))
        spd[(lam - 390) // step] = 1.0 / step          # unit energy in one bin
        lms = sf.lms_from_spd(spd)
        # CVRL 8dp vs CIE 170-1 table 6.7: tabulation difference < 1e-5 abs
        np.testing.assert_allclose(lms, PILOT_LMS[lam], atol=1e-5, rtol=0)
    spd5 = np.zeros(79)
    spd5[(lam - 390) // 5] = 0.2
    np.testing.assert_allclose(sf.lms_from_spd(spd5, source="cie_table"),
                               PILOT_LMS[lam], rtol=1e-12, atol=0)


# -- 2. pilot packet reproduction ------------------------------------------

@pytest.mark.parametrize("lam", [610, 530])
@pytest.mark.parametrize("method", ["cumulative", "per_bin"])
def test_pilot_packets(lam, method):
    want = [{"column": 3, "wavelength_nm": float(lam), "count": 1000}]
    assert sf.monochromatic(lam, 1000, column=3) == want
    for step in (1, 5):
        spd = sf.monochromatic_spd(lam, 1000, step=step)
        assert sf.quantize(spd, column=3, method=method) == want


def test_capture_replica_matches_smoke_values():
    for lam, (rg, by) in SMOKE.items():
        c = sf.eye_capture_model(sf.monochromatic(lam, 1000))
        assert c["red_green"] == pytest.approx(rg, abs=1e-12)
        assert c["blue_yellow"] == pytest.approx(by, abs=1e-12)


def test_pilot_eye_regression_through_forward_model():
    from domains.engine_provenance import engine_preamble, provenance_line
    engine_preamble(strict=False)
    from domains.photon_eye import GraphEye, _RECEPTORS
    assert _RECEPTORS == sf.EYE_RECEPTORS
    packets = (sf.quantize(sf.monochromatic_spd(610, 1000), column=0)
               + sf.quantize(sf.monochromatic_spd(530, 1000), column=1))
    eye = GraphEye(n_az=2, context={"worker_capacity": 1}).build()
    try:
        eye.submit_photons(packets)
        deadline = time.monotonic() + 10.0
        while eye.processed_count() < 1 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert eye.processed_count() >= 1, provenance_line()
        got = [(float(p["red_green"]), float(p["blue_yellow"]))
               for p in eye.latest()["percepts"]]
    finally:
        eye.stop()
    assert got == [SMOKE[610], SMOKE[530]]


# -- 3. metamers ------------------------------------------------------------

@pytest.mark.parametrize("illum", ["E", "D65", "A"])
@pytest.mark.parametrize("cycles,phase", [(2.0, 0.0), (3.0, 1.0), (5.0, 2.0)])
def test_metamer_identity_under_cie(illum, cycles, phase):
    base = sf.scale_to_td(sf.at_retina_spd("neutral 6.5", illum), 100.0)
    m = sf.metamer(base, amplitude=0.8, cycles=cycles, phase=phase)
    np.testing.assert_allclose(sf.lms_from_spd(m), sf.lms_from_spd(base), rtol=1e-10, atol=1e-15)
    assert np.all(m > 0)
    assert np.max(np.abs(m - base)) / np.max(base) > 0.05          # spectrally distinct
    assert sf.quantize(m) != sf.quantize(base)                      # distinct packet lists


def test_metamer_5nm_and_10deg_not_identity():
    base = sf.scale_to_td(sf.illuminant("E", 5), 100.0)
    m = sf.metamer(base)
    np.testing.assert_allclose(sf.lms_from_spd(m), sf.lms_from_spd(base), rtol=1e-10)
    b1 = sf.scale_to_td(sf.illuminant("E"), 100.0)
    m1 = sf.metamer(b1, amplitude=0.9)
    gap = np.abs(sf.lms_from_spd(m1, "10deg") - sf.lms_from_spd(b1, "10deg"))
    assert gap.max() > 1e-6     # null space is observer-specific


# -- 4. determinism and count scaling --------------------------------------

def test_determinism_and_scaling():
    spd = sf.scale_to_td(sf.at_retina_spd("orange", "D65"), 100.0)
    a = sf.quantize(spd, column=2)
    assert a == sf.quantize(spd.copy(), column=2)
    totals = [sf.packets_total(sf.quantize(spd, quanta_scale=sf.QUANTA_SCALE * f)) for f in (0.5, 1, 2, 4)]
    assert totals == sorted(totals) and totals[-1] > 7 * totals[0]
    assert sf.packets_total(sf.quantize(spd * 10)) == int(np.floor(10 * sf.expected_quanta(spd).sum() + 0.5))


def test_poisson_requires_seed_and_is_seeded():
    spd = sf.scale_to_td(sf.illuminant("E"), 100.0)
    with pytest.raises(ValueError):
        sf.quantize(spd, method="poisson")
    assert sf.quantize(spd, method="poisson", seed=7) == sf.quantize(spd, method="poisson", seed=7)
    assert sf.quantize(spd, method="poisson", seed=7) != sf.quantize(spd, method="poisson", seed=8)


def test_quanta_anchor():
    assert sf.QUANTA_SCALE == pytest.approx(sf.derive_quanta_scale(1), rel=1e-12)
    white = sf.scale_to_td(sf.illuminant("E"), sf.REFERENCE_WHITE_TD)
    assert sf.retinal_illuminance_td(white) == pytest.approx(100.0)
    assert sf.expected_quanta(white).sum() == pytest.approx(1000.0)
    c = sf.eye_capture_expected(white)
    assert all(c[k]["activation"] < 0.5 for k in ("l", "m", "s", "rod"))


# -- cumulative rounding ----------------------------------------------------

@pytest.mark.parametrize("td", [0.1, 1.0, 100.0, 1e4])
@pytest.mark.parametrize("step", [1, 5])
def test_cumulative_rounding_conserves_total(td, step):
    for spd in (sf.scale_to_td(sf.illuminant("E", step), td),
                sf.scale_to_td(sf.illuminant("D65", step), td) * sf.eyelid_transmittance(step=step),
                sf.scale_to_td(sf.at_retina_spd("blue", "A", step=step), td)):
        q = sf.expected_quanta(spd)
        pk = sf.quantize(spd, method="cumulative")
        assert sf.packets_total(pk) == int(np.floor(q.sum() + 0.5))
        assert all(p["count"] > 0 and isinstance(p["count"], int) for p in pk)
        # running total never deviates from the continuous one by >= 1 quantum
        wl = sf.grid(step)
        cum = np.zeros(len(wl))
        for p in pk:
            cum[int(round((p["wavelength_nm"] - 390) / step))] = p["count"]
        assert np.max(np.abs(np.cumsum(cum) - np.cumsum(q))) <= 0.5 + 1e-9


def test_per_bin_rounding_loses_dim_broadband():
    dim = sf.scale_to_td(sf.illuminant("E"), 100.0) * sf.eyelid_transmittance()
    assert sf.packets_total(sf.quantize(dim, method="per_bin")) == 0
    assert sf.packets_total(sf.quantize(dim, method="cumulative")) > 10


# -- 5. eyelid (forward-model properties only; A0-c) ------------------------

def test_eyelid_forward_model_properties():
    wl = sf.grid(1)
    T = sf.eyelid_transmittance()
    band = (wl >= 600) & (wl <= 700)
    assert np.all(np.diff(T[band]) > 0)                      # monotone long-pass rise
    assert np.all(T[wl <= 600] == pytest.approx(10 ** -3.0))
    assert np.all(T[wl >= 700] == pytest.approx(10 ** -1.3))
    assert T[wl == 450][0] < T[wl == 650][0] < T[wl == 700][0]
    for od_long in (1.0, 1.3, 1.6):
        for ill in ("E", "D65", "A"):
            spd = sf.at_retina_spd(None, ill, sf.eyelid_transmittance(od_long=od_long))
            rg, _ = sf.opponent(sf.lms_from_spd(spd))
            assert rg > 0
    assert np.array_equal(sf.at_retina_spd(None, "D65", "eyelid"),
                          sf.illuminant("D65") * T)


def test_filter_off_by_default():
    assert np.array_equal(sf.at_retina_spd("red", "D65"),
                          sf.illuminant("D65") * sf.reflectance("red"))


# -- colorimetry helpers ----------------------------------------------------

def test_dominant_wavelength_monochromatic_and_white():
    for lam in (480, 530, 580, 610):
        spd = np.zeros(391)
        spd[lam - 390] = 1.0
        d, purity = sf.dominant_wavelength(spd)
        assert d == pytest.approx(lam, abs=0.5) and purity == pytest.approx(1.0, abs=1e-3)
    d, purity = sf.dominant_wavelength(sf.illuminant("E"))
    assert purity == 0.0
    assert sf.dominant_wavelength(sf.at_retina_spd("magenta", "E"))[0] < 0   # purple: complementary


def test_five_nm_grid_end_to_end():
    spd = sf.scale_to_td(sf.at_retina_spd("red", "D65", step=5), 100.0)
    pk = sf.quantize(spd, column=1)
    assert all(p["wavelength_nm"] % 5 == 0 for p in pk) and sf.packets_total(pk) > 0
    s1 = sf.scale_to_td(sf.at_retina_spd("red", "D65", step=1), 100.0)
    o1, o5 = sf.opponent(sf.lms_from_spd(s1)), sf.opponent(sf.lms_from_spd(spd))
    assert o5 == pytest.approx(o1, rel=0.02)
