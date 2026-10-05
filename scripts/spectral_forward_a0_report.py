"""Amendment A0 numbers for the spectral forward model (no eye run).

Computes, from the forward model and the documented capture formula only:
quanta anchor operating points, quantisation-error table, eyelid td levels,
CIE opponent zero-crossings.  Writes results/spectral_forward_a0.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from domains import spectral_forward as sf  # noqa: E402

AMBIENT_TD = (100.0, 1000.0, 10000.0)        # declared open-eye ambient levels
ILLUMS = ("E", "D65", "A")


def capture_summary(spd):
    e = sf.eye_capture_expected(spd)
    return {k: {"caught": e[k]["caught"], "activation": e[k]["activation"]}
            for k in ("l", "m", "s", "rod")}


def quant_errors(spd):
    ref = sf.eye_capture_expected(spd)
    out = {"td": sf.retinal_illuminance_td(spd),
           "expected_quanta": float(sf.expected_quanta(spd).sum()),
           "continuous_caught": {k: ref[k]["caught"] for k in "lms"}}
    for m, kw in (("cumulative", {}), ("per_bin", {}), ("poisson_seed0", {"seed": 0})):
        pk = sf.quantize(spd, method=m.split("_seed")[0], **kw)
        c = sf.eye_capture_model(pk)
        out[m] = {"total": sf.packets_total(pk), "n_packets": len(pk),
                  "caught_error": {k: c[k]["caught"] - ref[k]["caught"] for k in "lms"}}
    return out


def main():
    wl = sf.grid(1)
    res = {"experiment": "spectral_forward_amendment_A0", "provenance": provenance_line(),
           "quanta_scale": sf.QUANTA_SCALE, "k_m_f_2deg": sf.K_M_F_2DEG,
           "reference_white": {"illuminant": "E", "td": sf.REFERENCE_WHITE_TD,
                               "expected_quanta_1nm": sf.REFERENCE_WHITE_QUANTA}}
    res["pilot_td"] = {str(l): sf.retinal_illuminance_td(sf.monochromatic_spd(l, 1000))
                       for l in (610, 530)}
    res["pilot_capture"] = {str(l): sf.eye_capture_model(sf.monochromatic(l, 1000))
                            for l in (610, 530)}
    res["white_operating_points"] = {
        f"{ill}@{td:g}td": capture_summary(sf.scale_to_td(sf.illuminant(ill), td))
        for ill in ILLUMS for td in (10.0, 100.0, 1000.0)}
    eyelid = {}
    for od_long in (1.0, 1.3, 1.6):
        T = sf.eyelid_transmittance(od_long=od_long)
        for ill in ILLUMS:
            for td in AMBIENT_TD:
                spd = sf.scale_to_td(sf.illuminant(ill), td) * T
                lms = sf.lms_from_spd(spd)
                rg, by = sf.opponent(lms)
                eyelid[f"OD_long={od_long}|{ill}|{td:g}td"] = {
                    "td_behind_lid": sf.retinal_illuminance_td(spd),
                    "expected_quanta": float(sf.expected_quanta(spd).sum()),
                    "cie_lms": lms.tolist(), "cie_rg": rg, "cie_by": by,
                    "cie_rg_over_lplusm": rg / (lms[0] + lms[1]),
                    "dominant_wavelength_nm": sf.dominant_wavelength(spd, white=ill)[0],
                    "capture_expected": capture_summary(spd)}
    res["eyelid"] = eyelid
    res["eyelid_mean_od_450_650"] = float(sf.eyelid_od()[(wl >= 450) & (wl <= 650)].mean())
    q = {}
    for step in (1, 5):
        q[f"white_E_100td_{step}nm"] = quant_errors(sf.scale_to_td(sf.illuminant("E", step), 100.0))
        for ill in ("E", "D65"):
            for td in AMBIENT_TD:
                spd = sf.scale_to_td(sf.illuminant(ill, step), td) * sf.eyelid_transmittance(step=step)
                q[f"eyelid_{ill}_{td:g}td_{step}nm"] = quant_errors(spd)
    res["quantisation_error"] = q
    zc = {}
    for obs, src, step in (("2deg", "cvrl", 1), ("10deg", "cvrl", 1), ("2deg", "cie_table", 5)):
        lms = sf.load_lms(obs, step, src)
        g = sf.grid(step)
        zc[f"{obs}_{src}_{step}nm"] = {
            "L-M": sf.zero_crossings(lms[:, 0] - lms[:, 1], g),
            "S-0.5(L+M)": sf.zero_crossings(lms[:, 2] - 0.5 * (lms[:, 0] + lms[:, 1]), g)}
    res["cie_opponent_zero_crossings_nm"] = zc
    out = Path(__file__).parents[1] / "results" / "spectral_forward_a0.json"
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
