"""Spectral forward model: a *photon source* upstream of the GraphEye.

Phase 2 of the Mary's Room empirical paper plan
(``docs/research/spectral-forward-model-spec.md``, incl. Amendment A0).

This module turns a scene description (illuminant SPD x surface reflectance x
optional pre-receptoral filter) into the ``{column, wavelength_nm, count}``
photon packets that ``domains.photon_eye.GraphEye.submit_photons`` already
consumes.  It is graph-external, pure Python/NumPy, and **changes nothing in
the eye**: it does not import the eye, the substrate, or any seed.  The same
at-retina SPD feeds both consumers:

* Arm A (theory): ``lms_from_spd`` integrates the SPD against the CIE 2006
  cone fundamentals (energy units) -> ``opponent`` -> (L-M, S-0.5(L+M)).
* Arm B (eye): ``quantize`` converts the SPD to integer quanta packets.

``eye_capture_model`` is an *analytic replica* of the eye's documented capture
+ Naka-Rushton formula, provided only for reporting operating points (e.g.
that the reference white does not saturate).  It is not the eye and is never
a substitute for running it.

Units
-----
SPDs are arrays on ``grid(step)`` (390-780 nm).  Absolute SPDs are spectral
radiance x pupil area (W sr^-1 m^-2 nm^-1 mm^2), so that
``retinal_illuminance_td(spd) = K_m,F * sum(spd * V_F * dlambda)`` is in
trolands.  Relative SPDs (illuminants normalised to 100 at 560 nm) are made
absolute with ``scale_to_td``.

Quanta (Amendment A0-b,d)
-------------------------
Expected model quanta per bin: ``q_i = QUANTA_SCALE * spd_i * dlambda *
(lambda_i / LAMBDA_REF_NM)`` (energy -> photon number is proportional to
lambda).  ``QUANTA_SCALE`` is the single declared constant: an equal-energy
white at ``REFERENCE_WHITE_TD`` = 100 td gives ``REFERENCE_WHITE_QUANTA`` =
1000 expected model quanta per column on the 1 nm grid -- the pilot's
per-column budget.  Model quanta are model units, not calibrated
isomerisations.
"""
from __future__ import annotations

import csv
import functools
import math
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "colour"
RAW_DIR = DATA_DIR / "raw"

LAMBDA_MIN_NM = 390
LAMBDA_MAX_NM = 780
LAMBDA_REF_NM = 560.0          # wavelength at which quantal weight == 1

# K_m for the CIE cone-fundamental-based V_F(lambda) (2 deg): the SI candela
# definition fixes 683 lm/W at 540 THz (555.016 nm, std air), so
# K_m,F = 683 / V_F(555.016 nm) (linear interpolation of CIE 170-2 table 10.2).
K_M_F_2DEG = 683.3626501713336

# Declared quanta anchor (Amendment A0-b).  Derivation: equal-energy E scaled
# to 100 td on the 1 nm grid, sum(QUANTA_SCALE * spd * 1 nm * lambda/560) = 1000.
REFERENCE_WHITE_TD = 100.0
REFERENCE_WHITE_QUANTA = 1000.0
QUANTA_SCALE = 1891.2408486093182  # model quanta per (W sr^-1 m^-2 mm^2) at 560 nm

# Eyelid parameters (spec, frozen pre-run).
EYELID_OD_SHORT = 3.0
EYELID_OD_LONG = 1.3

# Analytic replica of domains/photon_eye.py::_RECEPTORS (centre nm, bandwidth
# nm, half saturation, dark current).  Used only by eye_capture_model.
EYE_RECEPTORS = {
    "rod": (498.0, 42.0, 1024.0, 0.15),
    "l": (564.0, 42.0, 512.0, 0.0),
    "m": (534.0, 36.0, 512.0, 0.0),
    "s": (420.0, 28.0, 512.0, 0.0),
}

QUANTIZE_METHODS = ("cumulative", "per_bin", "poisson")


# --------------------------------------------------------------------------
# grid helpers
# --------------------------------------------------------------------------

def grid(step: int = 1) -> np.ndarray:
    """Wavelength grid 390..780 nm inclusive (float64). step in {1, 5} (any
    integer divisor of 390 is accepted)."""
    step = int(step)
    if step <= 0 or (LAMBDA_MAX_NM - LAMBDA_MIN_NM) % step:
        raise ValueError(f"step must divide {LAMBDA_MAX_NM - LAMBDA_MIN_NM}: {step}")
    return np.arange(LAMBDA_MIN_NM, LAMBDA_MAX_NM + 1, step, dtype=float)


def step_for(spd) -> int:
    """Infer the grid step from an SPD's length (391 -> 1 nm, 79 -> 5 nm, ...)."""
    n = len(spd)
    span = LAMBDA_MAX_NM - LAMBDA_MIN_NM
    if n < 2 or span % (n - 1):
        raise ValueError(f"SPD length {n} does not match any 390-780 nm grid")
    return span // (n - 1)


def _index(wavelength_nm: float, step: int) -> int:
    wl = grid(step)
    i = int(round((float(wavelength_nm) - LAMBDA_MIN_NM) / step))
    if i < 0 or i >= len(wl) or abs(wl[i] - float(wavelength_nm)) > 1e-9:
        raise ValueError(f"{wavelength_nm} nm is not on the {step} nm grid")
    return i


# --------------------------------------------------------------------------
# tabulated data
# --------------------------------------------------------------------------

def _read_numeric_csv(path: Path, ncols: int) -> np.ndarray:
    rows = []
    with open(path, newline="") as fh:
        for rec in csv.reader(fh):
            rec = [x.strip() for x in rec]
            if not rec or not rec[0]:
                continue
            vals = []
            for x in rec[:ncols]:
                vals.append(float(x) if x and x.lower() != "nan" else 0.0)
            vals += [0.0] * (ncols - len(vals))   # blank S beyond 615 nm -> 0
            rows.append(vals)
    return np.asarray(rows, dtype=float)


def _on_grid(table: np.ndarray, step: int) -> np.ndarray:
    """Select tabulated rows exactly on the grid (no interpolation)."""
    wl = grid(step)
    lut = {int(round(r[0] * 10)): r[1:] for r in table}
    try:
        return np.array([lut[int(round(w * 10))] for w in wl])
    except KeyError as exc:
        raise ValueError(f"table lacks wavelength {int(exc.args[0]) / 10} nm") from None


@functools.lru_cache(maxsize=None)
def _lms_table(observer: str, source: str) -> np.ndarray:
    files = {
        ("2deg", "cvrl"): "linss2_10e_1_8dp.csv",
        ("10deg", "cvrl"): "linss10e_1_8dp.csv",
        ("2deg", "cie_table"): "CIE_lms_cf_2deg.csv",
        ("10deg", "cie_table"): "CIE_lms_cf_10deg.csv",
    }
    if (observer, source) not in files:
        raise ValueError(f"unknown observer/source {(observer, source)}")
    return _read_numeric_csv(RAW_DIR / files[(observer, source)], 4)


def load_lms(observer: str = "2deg", step: int = 1, source: str = "cvrl") -> np.ndarray:
    """CIE 2006 LMS cone fundamentals, energy units, linear, peak-normalised.

    Returns array (N, 3) on ``grid(step)``.  ``source='cvrl'`` (default): the
    CVRL 1 nm 8-decimal tabulation of the CIE 2006 functions (agrees with CIE
    170-1 tables 6.7/6.2 within 1.25e-5 relative).  ``source='cie_table'``: the
    official CIE 5 nm table (exactly the pilot's values; step must be a
    multiple of 5).  S is zero where the tables leave it blank (>615 nm).
    """
    if observer not in ("2deg", "10deg"):
        raise ValueError("observer must be '2deg' or '10deg'")
    return _on_grid(_lms_table(observer, source), step)


@functools.lru_cache(maxsize=None)
def _xyz_table() -> np.ndarray:
    return _read_numeric_csv(RAW_DIR / "CIE_cfb_stv_2deg.csv", 4)


def load_xyz(step: int = 1) -> np.ndarray:
    """CIE 2012 (CIE 170-2:2015 table 10.7a) 2-deg cone-fundamental-based XYZ
    colour-matching functions, energy, 1 nm source.  Array (N, 3)."""
    return _on_grid(_xyz_table(), step)


@functools.lru_cache(maxsize=None)
def _vstar_table() -> np.ndarray:
    return _read_numeric_csv(RAW_DIR / "CIE_cfb_sle_2deg.csv", 2)


def v_star(step: int = 1) -> np.ndarray:
    """CIE 2008/2015 physiologically relevant luminous efficiency V*(lambda)
    = V_F(lambda), 2 deg, energy (CIE 170-2:2015 table 10.2; equal to
    0.68990272 L + 0.34832189 M of the CIE 2006 2-deg fundamentals)."""
    return _on_grid(_vstar_table(), step)[:, 0]


@functools.lru_cache(maxsize=None)
def _d65_table() -> np.ndarray:
    return _read_numeric_csv(RAW_DIR / "CIE_std_illum_D65.csv", 2)


def illuminant_a_planck(wavelengths_nm) -> np.ndarray:
    """CIE illuminant A by the CIE 15 / ISO/CIE 11664-2 formula:
    S_A = 100 (560/l)^5 (exp(c2/(2848*560)) - 1)/(exp(c2/(2848*l)) - 1),
    c2 = 1.435e7 nm K (this is the 2856 K Planckian on the ITS-90 c2=1.4388e7)."""
    lam = np.asarray(wavelengths_nm, dtype=float)
    c2, T = 1.435e7, 2848.0
    return 100.0 * (560.0 / lam) ** 5 * np.expm1(c2 / (T * 560.0)) / np.expm1(c2 / (T * lam))


def illuminant(name: str = "E", step: int = 1) -> np.ndarray:
    """Relative illuminant SPD on grid(step), normalised 100 at 560 nm.
    name in {'E', 'D65', 'A'}.  D65: CIE 1 nm table (ISO/CIE 11664-2:2022
    B.1).  A: computed from the CIE Planck formula.  E: flat 100."""
    wl = grid(step)
    key = name.upper()
    if key == "E":
        return np.full(len(wl), 100.0)
    if key == "D65":
        return _on_grid(_d65_table(), step)[:, 0].copy()
    if key == "A":
        return illuminant_a_planck(wl)
    raise ValueError(f"unknown illuminant {name!r}")


@functools.lru_cache(maxsize=None)
def _colorchecker() -> tuple[tuple[str, ...], np.ndarray, np.ndarray]:
    path = DATA_DIR / "colorchecker24_babelcolor_avg_10nm.csv"
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    wl = np.array([float(x) for x in rows[0][2:]])
    names = tuple(r[1] for r in rows[1:])
    refl = np.array([[float(x) for x in r[2:]] for r in rows[1:]])
    return names, wl, refl


def _norm_name(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def reflectance_names() -> list[str]:
    """The 24 ColorChecker patch names (BabelColor average), patch order 1..24."""
    return list(_colorchecker()[0])


def reflectance(name, step: int = 1) -> np.ndarray:
    """ColorChecker spectral reflectance factor on grid(step).

    ``name``: patch name (case/punctuation-insensitive, e.g. 'red',
    'dark skin', 'white 9.5 (.05 D)') or 1-based patch number.  Source data
    380-730 nm at 10 nm, linearly interpolated; values beyond 730 nm hold the
    730 nm value (np.interp end-hold)."""
    names, wl_src, refl = _colorchecker()
    if isinstance(name, (int, np.integer)):
        idx = int(name) - 1
        if not 0 <= idx < len(names):
            raise ValueError(f"patch number out of range: {name}")
    else:
        key = _norm_name(str(name))
        matches = [i for i, n in enumerate(names) if _norm_name(n) == key]
        if not matches:
            matches = [i for i, n in enumerate(names) if _norm_name(n).startswith(key)]
        if len(matches) != 1:
            raise ValueError(f"unknown/ambiguous reflectance {name!r}")
        idx = matches[0]
    return np.interp(grid(step), wl_src, refl[idx])


# --------------------------------------------------------------------------
# filters and SPD composition
# --------------------------------------------------------------------------

def eyelid_od(od_short: float = EYELID_OD_SHORT, od_long: float = EYELID_OD_LONG,
              step: int = 1) -> np.ndarray:
    """Eyelid optical density, piecewise per the spec: OD_short for l<=600,
    linear to OD_long over 600-700, OD_long for l>=700."""
    wl = grid(step)
    od = np.where(wl <= 600.0, od_short,
                  np.where(wl >= 700.0, od_long,
                           od_short - (od_short - od_long) * (wl - 600.0) / 100.0))
    return od.astype(float)


def eyelid_transmittance(od_short: float = EYELID_OD_SHORT,
                         od_long: float = EYELID_OD_LONG, step: int = 1) -> np.ndarray:
    """T_eyelid(l) = 10^(-OD(l))."""
    return 10.0 ** (-eyelid_od(od_short, od_long, step))


def _as_spectrum(x, step: int, kind: str) -> np.ndarray:
    if x is None:
        return np.ones(len(grid(step)))
    if isinstance(x, (str, int, np.integer)):
        if kind == "illuminant":
            return illuminant(str(x), step)
        if kind == "reflectance":
            return reflectance(x, step)
        if kind == "filter":
            if str(x).lower() == "eyelid":
                return eyelid_transmittance(step=step)
        raise ValueError(f"unknown {kind} {x!r}")
    arr = np.asarray(x, dtype=float)
    if arr.shape != grid(step).shape:
        raise ValueError(f"{kind} array has shape {arr.shape}, grid has {grid(step).shape}")
    return arr


def at_retina_spd(reflectance=None, illuminant="E", filter=None, emission=None,
                  step: int = 1) -> np.ndarray:
    """Relative at-retina SPD  Phi'(l) = E(l) R(l) T(l)  (or emission x T).

    reflectance: None (R==1, i.e. the illuminant itself), patch name/number,
    or array.  illuminant: name or array.  filter: None (T==1, default),
    'eyelid' (default OD params), or an array.  emission: if given (array),
    replaces E*R (emissive stimulus)."""
    if emission is not None:
        phi = _as_spectrum(emission, step, "emission")
    else:
        phi = _as_spectrum(illuminant, step, "illuminant") * _as_spectrum(reflectance, step, "reflectance")
    return phi * _as_spectrum(filter, step, "filter")


# --------------------------------------------------------------------------
# colorimetry (theory arm)
# --------------------------------------------------------------------------

def lms_from_spd(spd, observer: str = "2deg", source: str = "cvrl") -> np.ndarray:
    """(L, M, S) = sum_l spd(l) * lmsbar(l) * dl  (CIE 2006, energy)."""
    spd = np.asarray(spd, dtype=float)
    step = step_for(spd)
    return spd @ load_lms(observer, step, source) * step


def opponent(lms) -> tuple[float, float]:
    """(RG, BY) = (L - M, S - 0.5 (L + M))."""
    L, M, S = (float(v) for v in lms)
    return (L - M, S - 0.5 * (L + M))


def xyz_from_spd(spd) -> np.ndarray:
    spd = np.asarray(spd, dtype=float)
    step = step_for(spd)
    return spd @ load_xyz(step) * step


def chromaticity(spd) -> tuple[float, float]:
    X, Y, Z = xyz_from_spd(spd)
    s = X + Y + Z
    return (float(X / s), float(Y / s))


def dominant_wavelength(spd, white="E") -> tuple[float, float]:
    """Dominant wavelength (nm) and excitation purity in CIE 2012 2-deg xy.

    White point = chromaticity of the named illuminant (or an SPD array).
    For samples in the purple region the complementary wavelength is returned
    as a negative number.  Returns (nan, 0) if the sample is the white point."""
    spd = np.asarray(spd, dtype=float)
    step = step_for(spd)
    w = np.array(chromaticity(_as_spectrum(white, step, "illuminant")))
    p = np.array(chromaticity(spd))
    d = p - w
    if np.hypot(*d) < 1e-12:
        return (float("nan"), 0.0)
    cmf = load_xyz(1)
    loc = cmf[:, :2] / cmf.sum(axis=1, keepdims=True)
    wl = grid(1)

    def hit(direction):
        best = None
        for i in range(len(loc) - 1):
            a, b = loc[i], loc[i + 1]
            e = b - a
            den = direction[0] * (-e[1]) + direction[1] * e[0]
            if abs(den) < 1e-15:
                continue
            r = a - w
            t = (r[0] * (-e[1]) + r[1] * e[0]) / den
            u = (direction[0] * r[1] - direction[1] * r[0]) / den
            if t > 0 and -1e-12 <= u <= 1 + 1e-12 and (best is None or t < best[0]):
                best = (t, wl[i] + u * (wl[i + 1] - wl[i]))
        return best

    h = hit(d)
    if h is not None:
        return (float(h[1]), float(1.0 / h[0]))
    h = hit(-d)
    if h is None:
        return (float("nan"), float("nan"))
    # purity relative to the purple line
    a, b = loc[0], loc[-1]
    e = b - a
    den = d[0] * (-e[1]) + d[1] * e[0]
    r = a - w
    t = (r[0] * (-e[1]) + r[1] * e[0]) / den
    return (-float(h[1]), float(1.0 / t) if t > 0 else float("nan"))


def retinal_illuminance_td(spd) -> float:
    """Retinal illuminance (td) = K_m,F * sum spd * V*(l) * dl (spd absolute)."""
    spd = np.asarray(spd, dtype=float)
    step = step_for(spd)
    return float(K_M_F_2DEG * np.sum(spd * v_star(step)) * step)


def scale_to_td(spd, td: float) -> np.ndarray:
    """Return spd scaled so retinal_illuminance_td(result) == td."""
    spd = np.asarray(spd, dtype=float)
    cur = retinal_illuminance_td(spd)
    if cur <= 0:
        raise ValueError("SPD has zero luminance")
    return spd * (float(td) / cur)


def zero_crossings(values, wavelengths) -> list[float]:
    """Linearly interpolated zero crossings of a sampled function."""
    v = np.asarray(values, dtype=float)
    wl = np.asarray(wavelengths, dtype=float)
    out = []
    for i in range(len(v) - 1):
        if v[i] == 0.0:
            out.append(float(wl[i]))
        elif v[i] * v[i + 1] < 0:
            out.append(float(wl[i] + (wl[i + 1] - wl[i]) * v[i] / (v[i] - v[i + 1])))
    return out


# --------------------------------------------------------------------------
# photons (eye arm)
# --------------------------------------------------------------------------

def _quantal_weight(step: int, photon_conversion: str) -> np.ndarray:
    if photon_conversion == "quantal":
        return grid(step) / LAMBDA_REF_NM
    if photon_conversion == "energy":   # declared ablation: no lambda factor
        return np.ones(len(grid(step)))
    raise ValueError("photon_conversion must be 'quantal' or 'energy'")


def expected_quanta(spd, quanta_scale: float = QUANTA_SCALE,
                    photon_conversion: str = "quantal") -> np.ndarray:
    """Continuous expected model quanta per bin:
    q_i = quanta_scale * spd_i * dl * (l_i / 560 nm)."""
    spd = np.asarray(spd, dtype=float)
    if np.any(spd < 0):
        raise ValueError("SPD must be non-negative")
    step = step_for(spd)
    return float(quanta_scale) * spd * step * _quantal_weight(step, photon_conversion)


def _round_half_up(x: np.ndarray) -> np.ndarray:
    return np.floor(x + 0.5)


def quantize(spd, quanta_scale: float = QUANTA_SCALE, column: int = 0,
             method: str = "cumulative", seed: int | None = None,
             photon_conversion: str = "quantal") -> list[dict]:
    """SPD -> integer photon packets for one retinal column.

    method:
      'cumulative' (default, A0-a): N_i = r(C_i) - r(C_{i-1}), C = cumulative
                   expected count, r = round-half-up.  Deterministic; total
                   count = r(sum q); preserves spectral shape.
      'per_bin'    (declared ablation): N_i = r(q_i).
      'poisson'    (declared noise arm): N_i ~ Poisson(q_i), explicit seed
                   required (numpy default_rng(seed)).
    Bins with N_i == 0 are omitted.  Packet = {column, wavelength_nm, count}.
    """
    q = expected_quanta(spd, quanta_scale, photon_conversion)
    step = step_for(spd)
    if method == "cumulative":
        c = _round_half_up(np.cumsum(q))
        n = np.diff(np.concatenate(([0.0], c)))
    elif method == "per_bin":
        n = _round_half_up(q)
    elif method == "poisson":
        if seed is None:
            raise ValueError("poisson quantisation requires an explicit seed")
        n = np.random.default_rng(int(seed)).poisson(q).astype(float)
    else:
        raise ValueError(f"method must be one of {QUANTIZE_METHODS}")
    wl = grid(step)
    return [{"column": int(column), "wavelength_nm": float(wl[i]), "count": int(n[i])}
            for i in range(len(wl)) if n[i] > 0]


def monochromatic(wavelength_nm: float, quanta: int, column: int = 0) -> list[dict]:
    """Monochromatic stimulus specified directly in model quanta (pilot form):
    one packet {column, wavelength_nm, count=quanta}."""
    return [{"column": int(column), "wavelength_nm": float(wavelength_nm),
             "count": int(quanta)}]


def monochromatic_spd(wavelength_nm: float, quanta: float = REFERENCE_WHITE_QUANTA,
                      step: int = 1, quanta_scale: float = QUANTA_SCALE,
                      photon_conversion: str = "quantal") -> np.ndarray:
    """Absolute single-bin SPD whose expected quanta at ``wavelength_nm`` equal
    ``quanta`` (so ``quantize`` returns the pilot packet).  The wavelength must
    lie on the grid."""
    spd = np.zeros(len(grid(step)))
    i = _index(wavelength_nm, step)
    w = _quantal_weight(step, photon_conversion)[i]
    spd[i] = float(quanta) / (float(quanta_scale) * step * w)
    return spd


def packets_total(packets) -> int:
    return int(sum(p["count"] for p in packets))


def relabel(packets, column: int) -> list[dict]:
    """Copy of packets assigned to another column."""
    return [dict(p, column=int(column)) for p in packets]


# --------------------------------------------------------------------------
# metamers
# --------------------------------------------------------------------------

def lms_matrix(observer: str = "2deg", step: int = 1, source: str = "cvrl") -> np.ndarray:
    """3 x N matrix A with A @ spd == lms_from_spd(spd)."""
    return load_lms(observer, step, source).T * step


def null_space_project(f, observer: str = "2deg", source: str = "cvrl") -> np.ndarray:
    """Project f onto the null space of the 3 x N LMS matrix: f - A+ (A f)."""
    f = np.asarray(f, dtype=float)
    A = lms_matrix(observer, step_for(f), source)
    coef, *_ = np.linalg.lstsq(A @ A.T, A @ f, rcond=None)
    return f - A.T @ coef


def metamer(base_spd, perturbation=None, amplitude: float = 0.5,
            cycles: float = 3.0, phase: float = 0.0,
            observer: str = "2deg", source: str = "cvrl") -> np.ndarray:
    """Build an SPD metameric to ``base_spd`` under the CIE observer.

    perturbation: None -> sin(2 pi cycles (l-390)/390 + phase); or an array.
    It is projected onto the null space of the 3xN CIE LMS matrix, then scaled
    by ``amplitude`` (0 < amplitude < 1) times the largest step that keeps the
    SPD non-negative, so the result is >= 0 (strictly > 0 where base > 0 and
    amplitude < 1) and has identical CIE (L, M, S) to numerical tolerance."""
    base = np.asarray(base_spd, dtype=float)
    step = step_for(base)
    if not 0.0 < amplitude <= 1.0:
        raise ValueError("amplitude must be in (0, 1]")
    if perturbation is None:
        wl = grid(step)
        perturbation = np.sin(2 * np.pi * cycles * (wl - LAMBDA_MIN_NM)
                              / (LAMBDA_MAX_NM - LAMBDA_MIN_NM) + phase)
    p = null_space_project(perturbation, observer, source)
    neg = p < -1e-15
    if not np.any(neg):
        raise ValueError("null-space perturbation has no negative part")
    alpha_max = float(np.min(base[neg] / -p[neg]))
    if alpha_max <= 0:
        raise ValueError("base SPD is zero where the perturbation is negative")
    out = base + amplitude * alpha_max * p
    return np.maximum(out, 0.0) if amplitude == 1.0 else out


# --------------------------------------------------------------------------
# analytic replica of the eye's capture formula (reporting only)
# --------------------------------------------------------------------------

def eye_capture_model(packets, adaptation=None) -> dict:
    """Replica of the documented eye capture: per receptor
    caught = dark + sum count exp(-0.5((l-c)/bw)^2),
    activation = caught/(caught + half_sat + adaptation) (adaptation 0 on a
    fresh eye), plus red_green / blue_yellow on activations.  For reporting
    operating points only -- it is not the eye."""
    adaptation = adaptation or {}
    out = {}
    for r, (c, bw, half, dark) in EYE_RECEPTORS.items():
        caught = dark + sum(p["count"] * math.exp(-0.5 * ((p["wavelength_nm"] - c) / bw) ** 2)
                            for p in packets)
        a = float(adaptation.get(r, 0.0))
        out[r] = {"caught": caught, "activation": caught / (caught + half + a)}
    L, M, S = (out[k]["activation"] for k in ("l", "m", "s"))
    out["red_green"] = L - M
    out["blue_yellow"] = S - 0.5 * (L + M)
    return out


def eye_capture_expected(spd, quanta_scale: float = QUANTA_SCALE,
                         photon_conversion: str = "quantal") -> dict:
    """Same as eye_capture_model but on the continuous (unquantised) expected
    quanta -- the reference for quantisation-error reporting."""
    q = expected_quanta(spd, quanta_scale, photon_conversion)
    wl = grid(step_for(spd))
    pk = [{"wavelength_nm": float(w), "count": float(n)} for w, n in zip(wl, q) if n > 0]
    return eye_capture_model(pk)


def derive_quanta_scale(step: int = 1) -> float:
    """Re-derive QUANTA_SCALE from its declared definition (E at 100 td ->
    1000 expected quanta on the given grid)."""
    white = scale_to_td(illuminant("E", step), REFERENCE_WHITE_TD)
    return REFERENCE_WHITE_QUANTA / float(np.sum(white * step * grid(step) / LAMBDA_REF_NM))


def derive_k_m_f() -> float:
    t = _vstar_table()
    return 683.0 / float(np.interp(555.016, t[:, 0], t[:, 1]))


__all__ = [
    "grid", "step_for", "load_lms", "load_xyz", "v_star", "illuminant",
    "illuminant_a_planck", "reflectance", "reflectance_names", "eyelid_od",
    "eyelid_transmittance", "at_retina_spd", "lms_from_spd", "opponent",
    "xyz_from_spd", "chromaticity", "dominant_wavelength",
    "retinal_illuminance_td", "scale_to_td", "zero_crossings",
    "expected_quanta", "quantize", "monochromatic", "monochromatic_spd",
    "packets_total", "relabel", "lms_matrix", "null_space_project", "metamer",
    "eye_capture_model", "eye_capture_expected", "derive_quanta_scale",
    "derive_k_m_f", "QUANTA_SCALE", "K_M_F_2DEG", "REFERENCE_WHITE_TD",
    "REFERENCE_WHITE_QUANTA", "LAMBDA_REF_NM", "EYE_RECEPTORS",
    "EYELID_OD_SHORT", "EYELID_OD_LONG", "QUANTIZE_METHODS",
]
